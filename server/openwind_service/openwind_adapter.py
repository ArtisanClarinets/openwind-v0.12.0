# -*- coding: utf-8 -*-
"""Adapter layer that bridges Pydantic models with the OpenWInD API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from openwind.impedance_computation import ImpedanceComputation
from openwind.impedance_tools import match_freqs_with_notes

from .fingerings_bb import build_fingering_chart, fingering_sequence
from .models import (
    Geometry,
    IntonationResult,
    ObjectiveWeights,
    SimulationOptions,
    ToneHole,
)

MM_TO_M = 1e-3


@dataclass
class SimulationData:
    frequencies: np.ndarray
    impedance: np.ndarray


@dataclass
class SimulationBundle:
    frequencies: np.ndarray
    impedance: np.ndarray
    intonation: List[IntonationResult]
    fingering_notes: List[str]


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

        # Simple clarinet segmentation: barrel, body, bell (Bessel flare)
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
        # OpenWInD holes table: ["label","x","r","l"] then rows
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
    def _build_solver(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> Tuple[ImpedanceComputation, List[Dict[str, object]]]:
        main_bore, holes, fingering_chart = self.geometry_to_openwind(geometry)

        # If caller passed a set of notes, constrain to those fingerings
        note_filter = list(fingering_notes) if fingering_notes else None
        entries = fingering_sequence(note_filter)
        requested_labels = [entry["label"] for entry in entries]
        if requested_labels:
            fingering_chart = build_fingering_chart(geometry.tone_holes, notes=requested_labels)

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
        return solver, entries

    def run_simulation(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> SimulationBundle:
        solver, entries = self._build_solver(geometry, options, fingering_notes)
        base_impedance = np.asarray(solver.impedance)
        frequencies = np.asarray(solver.frequencies)
        intonation = self._compute_intonation(solver, entries, options)
        note_labels = [entry["label"] for entry in entries]
        return SimulationBundle(
            frequencies=frequencies,
            impedance=base_impedance,
            intonation=intonation,
            fingering_notes=note_labels,
        )

    def compute_impedance(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> SimulationData:
        bundle = self.run_simulation(geometry, options, fingering_notes)
        return SimulationData(frequencies=bundle.frequencies, impedance=bundle.impedance)

    def predict_intonation(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        fingering_notes: Iterable[str] | None = None,
    ) -> List[IntonationResult]:
        return self.run_simulation(geometry, options, fingering_notes).intonation

    def _compute_intonation(
        self,
        solver: ImpedanceComputation,
        entries: List[Dict[str, object]],
        options: SimulationOptions,
    ) -> List[IntonationResult]:
        results: List[IntonationResult] = []
        for entry in entries:
            note_label = str(entry["label"])
            solver.set_note(note_label)
            written_note = str(entry["note"])
            resonances = np.asarray(
                solver.resonance_frequencies(options.modes, display_warning=False)
            )
            if resonances.size == 0:
                continue

            # Use options for concert pitch & transposition; return simple names
            targets, cents, names = match_freqs_with_notes(
                resonances[:1],
                concert_pitch_A=options.concert_pitch_hz,
                transposition=options.transposition,
                simple_name=True,
            )
            display_note = names[0] if names else written_note
            variant = str(entry.get("variant", "standard"))
            if variant and variant != "standard":
                display_note = f"{display_note} ({variant})"

            results.append(
                IntonationResult(
                    note=display_note,
                    midi=int(entry.get("midi", 0)),
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
        objective: ObjectiveWeights,
        max_iter: int,
        mutate: Callable[[Geometry, int], Geometry],
        callback: Callable[[int, float, Geometry, Dict[str, float]], None],
        fingering_notes: Iterable[str] | None = None,
    ) -> Tuple[Geometry, List[float], List[Dict[str, float]], List[Dict[str, float]]]:
        """Simple iterative optimizer with callback and sensitivity analysis.

        Returns:
            best_geom, convergence (best score per iter),
            sensitivities (avg cents deltas per hole),
            history (per-iter metrics)
        """
        best_geom = geometry
        best_score, best_metrics, _ = self._score_geometry(
            best_geom, options, objective, fingering_notes
        )
        convergence: List[float] = [best_score]
        history: List[Dict[str, float]] = [{"iteration": 0, "score": best_score, **best_metrics}]

        for iteration in range(1, max_iter + 1):
            candidate = mutate(best_geom, iteration)
            score, metrics, _ = self._score_geometry(candidate, options, objective, fingering_notes)
            history.append({"iteration": iteration, "score": score, **metrics})
            if score < best_score:
                best_geom = candidate
                best_score = score
                best_metrics = metrics
            convergence.append(best_score)
            callback(iteration, score, candidate, metrics)

        sensitivity = self._compute_sensitivity(best_geom, options, objective, fingering_notes)
        return best_geom, convergence, sensitivity, history

    def _score_geometry(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        objective: ObjectiveWeights,
        fingering_notes: Iterable[str] | None = None,
    ) -> Tuple[float, Dict[str, float], SimulationBundle]:
        bundle = self.run_simulation(geometry, options, fingering_notes)
        metrics = self._evaluate_metrics(bundle, objective)
        score = metrics["score"]
        return score, metrics, bundle

    def _evaluate_metrics(self, bundle: SimulationBundle, objective: ObjectiveWeights) -> Dict[str, float]:
        # Intonation RMSE (cents)
        cents = np.array([item.cents for item in bundle.intonation], dtype=float)
        intonation_rmse = float(np.sqrt(np.mean(np.square(cents)))) if cents.size else float("inf")

        # Impedance smoothness: average norm of first differences
        magnitude = np.abs(bundle.impedance)
        if magnitude.size > 1:
            smoothness = float(np.linalg.norm(np.diff(magnitude)) / (magnitude.size - 1))
        else:
            smoothness = 0.0

        # Register alignment (below/above A4/Pitch class split via MIDI 69)
        lower = [item.cents for item in bundle.intonation if item.midi < 69]
        upper = [item.cents for item in bundle.intonation if item.midi >= 69]
        if lower and upper:
            register_alignment = float(abs(np.mean(lower) - np.mean(upper)))
        else:
            register_alignment = float(np.mean(np.abs(cents))) if cents.size else 0.0

        score = (
            objective.intonation * intonation_rmse
            + objective.impedance_smoothness * smoothness
            + objective.register_alignment * register_alignment
        )

        return {
            "intonation_rmse": float(intonation_rmse),
            "impedance_smoothness": float(smoothness),
            "register_alignment": float(register_alignment),
            "score": float(score),
        }

    def _compute_sensitivity(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        objective: ObjectiveWeights,
        fingering_notes: Iterable[str] | None = None,
    ) -> List[Dict[str, float]]:
        """Per-hole sensitivity via small axial and diameter perturbations (finite diff proxy)."""
        base_bundle = self.run_simulation(geometry, options, fingering_notes)
        base_map = {item.note: item.cents for item in base_bundle.intonation}
        sensitivities: List[Dict[str, float]] = []
        if not base_map:
            return sensitivities

        for hole in geometry.tone_holes:
            clone = geometry.model_copy(deep=True)
            try:
                idx = next(i for i, h in enumerate(clone.tone_holes) if h.index == hole.index)
            except StopIteration:
                continue

            # Axial perturbation (+0.5 mm)
            clone.tone_holes[idx].axial_pos_mm += 0.5
            axial_bundle = self.run_simulation(clone, options, fingering_notes)
            axial_map = {item.note: item.cents for item in axial_bundle.intonation}
            axial_diff = [abs(axial_map.get(note, cents) - cents) for note, cents in base_map.items() if note in axial_map]

            # Diameter perturbation (+0.3 mm, with a floor)
            clone_diam = geometry.model_copy(deep=True)
            try:
                idx_d = next(i for i, h in enumerate(clone_diam.tone_holes) if h.index == hole.index)
            except StopIteration:
                continue
            clone_diam.tone_holes[idx_d].diameter_mm = max(clone_diam.tone_holes[idx_d].diameter_mm + 0.3, 2.0)
            diam_bundle = self.run_simulation(clone_diam, options, fingering_notes)
            diam_map = {item.note: item.cents for item in diam_bundle.intonation}
            diam_diff = [abs(diam_map.get(note, cents) - cents) for note, cents in base_map.items() if note in diam_map]

            sensitivities.append(
                {
                    "hole_index": hole.index,
                    "axial_delta_cents": float(np.mean(axial_diff)) if axial_diff else float("nan"),
                    "diameter_delta_cents": float(np.mean(diam_diff)) if diam_diff else float("nan"),
                }
            )
        return sensitivities


__all__ = ["OpenWInDAdapter", "SimulationData", "SimulationBundle"]
