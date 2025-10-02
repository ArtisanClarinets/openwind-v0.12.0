"""Adapter layer that bridges Pydantic models with the OpenWInD API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from openwind.impedance_computation import ImpedanceComputation
from openwind.impedance_tools import match_freqs_with_notes

from .fingerings_bb import build_fingering_chart, fingering_sequence
from .models import Geometry, IntonationResult, SimulationOptions, ToneHole


MM_TO_M = 1e-3


@dataclass
class SimulationData:
    frequencies: np.ndarray
    impedance: np.ndarray


class OpenWInDAdapter:
    """High-level facade around the OpenWInD primitives."""

    def __init__(self, default_temperature: float = 22.0) -> None:
        self.default_temperature = default_temperature

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def geometry_to_openwind(self, geometry: Geometry) -> Tuple[List[list], List[list], List[list]]:
        """Convert :class:`Geometry` to OpenWInD main bore, holes and fingering lists."""

        length_m = geometry.length_mm * MM_TO_M
        bore_radius = (geometry.bore_mm * MM_TO_M) / 2.0
        barrel_length = (geometry.barrel_length_mm or 65.0) * MM_TO_M

        bell_length = min(0.12, 0.18 * length_m)
        body_length = max(length_m - bell_length - barrel_length, 0.32)

        main_bore: List[list] = [
            [0.0, barrel_length, bore_radius * 0.96, bore_radius, "cone"],
            [barrel_length, barrel_length + body_length, bore_radius, bore_radius, "cone"],
            [barrel_length + body_length, length_m, bore_radius, bore_radius * 2.15, "bessel", 0.7],
        ]

        holes = self._toneholes_to_openwind(geometry.tone_holes)
        fingering = build_fingering_chart(geometry.tone_holes)
        return main_bore, holes, fingering

    def _toneholes_to_openwind(self, holes: Sequence[ToneHole]) -> List[list]:
        formatted: List[list] = [["label", "x", "r", "l"]]
        for hole in sorted(holes, key=lambda h: (h.axial_pos_mm, h.index)):
            x_m = hole.axial_pos_mm * MM_TO_M
            radius_m = hole.radius_m
            chimney_m = hole.chimney_mm * MM_TO_M
            formatted.append([f"H{hole.index+1}", x_m, radius_m, chimney_m])
        return formatted

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------
    def compute_impedance(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> SimulationData:
        main_bore, holes, fingering_chart = self.geometry_to_openwind(geometry)
        if fingering_notes is not None:
            fingering_chart = build_fingering_chart(geometry.tone_holes, notes=fingering_notes)
        freqs = np.linspace(options.freq_min_hz, options.freq_max_hz, options.n_points)
        solver = ImpedanceComputation(
            freqs,
            main_bore,
            holes,
            fingering_chart,
            unit="m",
            diameter=False,
            temperature=options.temp_C,
            losses=True,
        )
        return SimulationData(frequencies=solver.frequencies, impedance=solver.impedance)

    def predict_intonation(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> List[IntonationResult]:
        note_entries = fingering_sequence(fingering_notes)
        main_bore, holes, fingering_chart = self.geometry_to_openwind(geometry)
        requested_notes = [entry["note"] for entry in note_entries]
        if requested_notes:
            fingering_chart = build_fingering_chart(geometry.tone_holes, notes=requested_notes)
        freqs = np.linspace(options.freq_min_hz, options.freq_max_hz, options.n_points)
        solver = ImpedanceComputation(
            freqs,
            main_bore,
            holes,
            fingering_chart,
            unit="m",
            diameter=False,
            temperature=options.temp_C,
            losses=True,
        )

        results: List[IntonationResult] = []
        for entry in note_entries:
            note = str(entry["note"])
            solver.set_note(note)
            resonances = np.asarray(solver.resonance_frequencies(options.modes, display_warning=False))
            if resonances.size == 0:
                continue
            targets, cents, _ = match_freqs_with_notes(
                resonances,
                concert_pitch_A=options.temp_C >= 25.0 and 442.0 or 440.0,
                transposition="Bb",
                simple_name=True,
            )
            results.append(
                IntonationResult(
                    note=note,
                    midi=int(entry["midi"]),
                    target_hz=float(targets[0]),
                    resonance_hz=float(resonances[0]),
                    cents=float(cents[0]),
                )
            )
        return results

    # ------------------------------------------------------------------
    # Optimization helpers
    # ------------------------------------------------------------------
    def optimise_geometry(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        max_iter: int,
        mutate: Callable[[Geometry, int], Geometry],
        callback: Callable[[int, float, Geometry], None],
    ) -> Tuple[Geometry, List[float], List[Dict[str, float]]]:
        best_geom = geometry
        best_score = self._score_geometry(best_geom, options)
        convergence: List[float] = [best_score]
        sensitivities: List[Dict[str, float]] = []

        for iteration in range(1, max_iter + 1):
            candidate = mutate(best_geom, iteration)
            score = self._score_geometry(candidate, options)
            if score < best_score:
                best_geom = candidate
                best_score = score
            convergence.append(best_score)
            callback(iteration, best_score, best_geom)
            sensitivities.append({"iteration": iteration, "score": score})
        return best_geom, convergence, sensitivities

    def _score_geometry(self, geometry: Geometry, options: SimulationOptions) -> float:
        predictions = self.predict_intonation(geometry, options)
        if not predictions:
            return float("inf")
        return sum(abs(item.cents) for item in predictions) / len(predictions)


__all__ = ["OpenWInDAdapter", "SimulationData"]
