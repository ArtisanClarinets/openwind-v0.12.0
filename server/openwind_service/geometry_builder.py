"""Clarinet geometry builder driven by fingering charts and OpenWInD simulation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .fingerings_bb import FINGERING_TEMPLATE
from .models import Geometry, ObjectiveWeights, RecommendRequest, SimulationOptions, ToneHole
from .openwind_adapter import OpenWInDAdapter


MM_TO_M = 1e-3
M_TO_MM = 1e3


_REGISTER_BOUNDARIES = {
    "chalumeau": (-np.inf, 65),
    "clarion": (65, 82),
    "altissimo": (82, np.inf),
}


def _speed_of_sound(temp_c: float) -> float:
    """Approximate speed of sound in m/s for a given temperature."""

    return 331.4 + 0.6 * temp_c


def _note_frequency(midi: int, a4_hz: float) -> float:
    """Return the equal-tempered frequency for a MIDI number."""

    return float(a4_hz * (2.0 ** ((midi - 69) / 12.0)))


def _register_mode(midi: int) -> int:
    """Return the odd mode index (1, 3, 5, ...) for the clarinet register."""

    if midi >= _REGISTER_BOUNDARIES["altissimo"][0]:
        return 5
    if midi >= _REGISTER_BOUNDARIES["clarion"][0]:
        return 3
    return 1


def _first_open_index(states: Sequence[object]) -> Tuple[int | None, bool]:
    """Locate the first hole that is not fully closed.

    Returns (index, is_half_hole) where index is ``None`` for the all-closed fingering.
    """

    for idx, raw in enumerate(states):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            # Treat truthy values as open, falsy as closed.
            if raw:
                return idx, False
            continue
        if value >= 0.5:
            return idx, value < 1.0
    return None, False


@dataclass
class BuilderResult:
    geometry: Geometry
    notes: List[str]
    convergence: List[float]
    history: List[Dict[str, float]]
    intonation: List[Dict[str, object]]


class ClarinetGeometryBuilder:
    """Generate a Bb clarinet geometry from a fingering chart and simulations."""

    def __init__(
        self,
        adapter: OpenWInDAdapter | None = None,
        simulation_options: SimulationOptions | None = None,
    ) -> None:
        self._adapter = adapter or OpenWInDAdapter()
        self._simulation_options = simulation_options or SimulationOptions()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self, payload: RecommendRequest) -> BuilderResult:
        """Return an optimised clarinet geometry based on fingering data."""

        entries = self._select_entries(payload)
        notes = [entry["label"] for entry in entries]
        base_geometry = self._geometry_from_fingerings(payload, entries)
        options = self._options_for_payload(payload)
        optimised, convergence, history = self._optimise_geometry(
            payload, base_geometry, notes, options
        )
        fingering_checks, impedance_bundle = self._evaluate_fingerings(
            optimised, options, notes
        )

        # Merge metadata with optimisation traces
        metadata = {
            **optimised.metadata,
            "builder": "clarinet-fingering",
            "convergence": convergence,
            "history": history,
            "fingering_intonation": fingering_checks,
            "fingering_notes": notes,
            **impedance_bundle,
        }
        optimised = optimised.model_copy(update={"metadata": metadata})
        return BuilderResult(
            geometry=optimised,
            notes=notes,
            convergence=convergence,
            history=history,
            intonation=fingering_checks,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _geometry_from_fingerings(
        self, payload: RecommendRequest, entries: Sequence[Dict[str, object]]
    ) -> Geometry:
        """Construct an initial geometry consistent with the fingering chart."""

        constraints = payload.constraints
        bore_mm = float(
            np.clip(14.6, constraints.min_bore_mm or 13.4, constraints.max_bore_mm or 15.1)
        )

        temp_c = self._simulation_options.temp_C
        speed = _speed_of_sound(temp_c)

        first_open_targets: Dict[int, List[float]] = defaultdict(list)
        first_open_freqs: Dict[int, List[float]] = defaultdict(list)
        all_closed_lengths: List[float] = []

        for entry in entries:
            midi = int(entry.get("midi", 0))
            freq = _note_frequency(midi, payload.target_a4_hz)
            mode = _register_mode(midi)
            length_m = (mode * speed) / (4.0 * freq)

            index, half = _first_open_index(entry.get("holes", []))
            if index is None:
                all_closed_lengths.append(length_m)
                continue
            first_open_targets[index].append(length_m)
            if half:
                # Penalise half-hole with slightly shorter target to encourage chimney levelling
                first_open_targets[index][-1] *= 0.99
            first_open_freqs[index].append(freq)

        hole_count = len(entries[0]["holes"]) if entries else 0
        if hole_count == 0:
            raise ValueError("No fingering information provided for geometry construction.")

        # Determine overall acoustic length using the all-closed fingering or the deepest tone hole.
        if all_closed_lengths:
            length_m = float(np.mean(all_closed_lengths))
        else:
            deepest = max(first_open_targets.keys(), default=hole_count - 1)
            length_m = float(np.max(first_open_targets.get(deepest, [0.66])))

        length_mm = length_m * M_TO_MM

        spacing_min_mm = constraints.min_spacing_mm or 10.0
        spacing_min_m = spacing_min_mm * MM_TO_M

        positions: List[float] = []
        prev = 0.015  # keep a short lead from the mouthpiece interface
        for idx in range(hole_count):
            targets = first_open_targets.get(idx)
            if targets:
                pos_m = float(np.mean(targets))
            else:
                # Interpolate between neighbours or extend the last spacing
                if idx > 0 and positions:
                    pos_m = positions[-1] + spacing_min_m
                else:
                    pos_m = prev + spacing_min_m

            pos_m = max(prev + spacing_min_m, pos_m)
            pos_m = min(pos_m, length_m - 0.04)  # ensure holes stay above the bell flare
            positions.append(pos_m)
            prev = pos_m

        # Estimate diameters proportional to the target frequencies and bore
        if first_open_freqs:
            freq_values = np.concatenate(list(first_open_freqs.values()))
            freq_min = float(np.min(freq_values))
            freq_max = float(np.max(freq_values))
        else:
            freq_min = _note_frequency(48, payload.target_a4_hz)
            freq_max = _note_frequency(84, payload.target_a4_hz)

        diameters: List[float] = []
        chimneys: List[float] = []
        undercuts: List[float] = []
        for idx in range(hole_count):
            freq_list = first_open_freqs.get(idx)
            if freq_list:
                freq = float(np.mean(freq_list))
            else:
                # Interpolate frequency linearly across the bore
                ratio = idx / max(hole_count - 1, 1)
                freq = freq_min + ratio * (freq_max - freq_min)

            norm = (freq - freq_min) / max(freq_max - freq_min, 1.0)
            diameter = bore_mm * (0.45 + 0.4 * norm)
            diameter = float(np.clip(diameter, 4.5, bore_mm * 1.25))
            diameters.append(diameter)

            chimney = max(12.0 - 0.35 * idx, 7.5)
            chimneys.append(chimney)

            undercut = float(np.clip(1.25 - 0.045 * idx, 0.35, 1.45))
            undercuts.append(undercut)

        holes = [
            ToneHole(
                index=idx,
                axial_pos_mm=positions[idx] * M_TO_MM,
                diameter_mm=diameters[idx],
                chimney_mm=chimneys[idx],
                undercut_mm=undercuts[idx],
                closed=False,
            )
            for idx in range(hole_count)
        ]

        metadata = {
            "fingerings_used": [entry["note"] for entry in entries],
            "fingering_labels": [entry["label"] for entry in entries],
            "speed_of_sound_mps": speed,
            "initial_length_mm": length_mm,
            "bell_profile": {"type": "bessel", "shape": 0.7},
            "chimney_profile_mm": chimneys,
            "undercut_profile_mm": undercuts,
        }

        geometry = Geometry(
            bore_mm=bore_mm,
            length_mm=length_mm,
            tone_holes=holes,
            metadata=metadata,
        )
        return geometry

    def _optimise_geometry(
        self,
        payload: RecommendRequest,
        geometry: Geometry,
        notes: Sequence[str],
        options: SimulationOptions,
    ) -> Tuple[Geometry, List[float], List[Dict[str, float]]]:
        """Refine geometry using OpenWInD impedance simulations."""

        rng = np.random.default_rng(hash(payload.player_pref.profile.lower()) & 0xFFFF)

        profile = payload.player_pref.profile.lower()
        if profile == "bright":
            objective = ObjectiveWeights(intonation=1.0, impedance_smoothness=0.15, register_alignment=0.35)
        elif profile in {"dark", "warm"}:
            objective = ObjectiveWeights(intonation=1.1, impedance_smoothness=0.4, register_alignment=0.65)
        else:
            objective = ObjectiveWeights()

        max_iter = 15

        def mutate(base: Geometry, iteration: int) -> Geometry:
            clone = base.model_copy(deep=True)
            scale = max(0.25, np.exp(-0.12 * iteration))
            bore_delta = float(rng.normal(0.0, 0.05 * scale))
            clone.bore_mm = float(np.clip(clone.bore_mm + bore_delta, 13.5, 15.5))
            for idx, hole in enumerate(clone.tone_holes):
                pos_delta = float(rng.normal(0.0, 0.6 * scale))
                diam_delta = float(rng.normal(0.0, 0.4 * scale))
                chim_delta = float(rng.normal(0.0, 0.3 * scale))
                hole.axial_pos_mm = max(hole.axial_pos_mm + pos_delta, 18.0 + idx * 4.0)
                hole.diameter_mm = float(np.clip(hole.diameter_mm + diam_delta, 4.0, clone.bore_mm * 1.3))
                hole.chimney_mm = float(np.clip(hole.chimney_mm + chim_delta, 6.0, 14.0))

            # Ensure monotonic positions
            sorted_holes = sorted(clone.tone_holes, key=lambda h: h.axial_pos_mm)
            for idx, hole in enumerate(sorted_holes):
                min_pos = 15.0 + idx * (payload.constraints.min_spacing_mm or 10.0)
                hole.axial_pos_mm = max(hole.axial_pos_mm, min_pos)
            clone.tone_holes = sorted(sorted_holes, key=lambda h: h.index)
            return clone

        trace: List[Dict[str, float]] = []

        def callback(iteration: int, score: float, geom: Geometry, metrics: Dict[str, float]) -> None:
            trace.append({"iteration": iteration, "score": score, **metrics})

        best_geom, convergence, _sensitivities, history = self._adapter.optimise_geometry(
            geometry,
            options,
            objective,
            max_iter,
            mutate,
            callback,
            fingering_notes=notes,
        )

        # Combine optimiser history with callback trace for metadata
        combined_history: List[Dict[str, float]] = []
        trace_map = {int(item["iteration"]): item for item in trace}
        for record in history:
            iteration = int(record.get("iteration", -1))
            merged = {**record, **trace_map.get(iteration, {})}
            combined_history.append(merged)

        return best_geom, convergence, combined_history

    def _options_for_payload(self, payload: RecommendRequest) -> SimulationOptions:
        options = self._simulation_options.model_copy(deep=True)
        options.concert_pitch_hz = payload.target_a4_hz
        return options

    def _evaluate_fingerings(
        self,
        geometry: Geometry,
        options: SimulationOptions,
        notes: Sequence[str],
    ) -> Tuple[List[Dict[str, object]], Dict[str, List[float]]]:
        bundle = self._adapter.run_simulation(geometry, options, fingering_notes=notes)
        checks: List[Dict[str, object]] = [
            {
                "note": item.note,
                "midi": item.midi,
                "target_hz": item.target_hz,
                "resonance_hz": item.resonance_hz,
                "cents": item.cents,
            }
            for item in bundle.intonation
        ]
        return checks, {
            "frequencies": bundle.frequencies.tolist(),
            "impedance_real": bundle.impedance.real.tolist(),
            "impedance_imag": bundle.impedance.imag.tolist(),
            "impedance_abs": np.abs(bundle.impedance).tolist(),
        }

    def _select_entries(self, payload: RecommendRequest) -> List[Dict[str, object]]:
        """Filter fingering template entries according to requested register."""

        register = (payload.include_register or "").lower()
        if register in _REGISTER_BOUNDARIES:
            low, high = _REGISTER_BOUNDARIES[register]
            filtered = [
                entry for entry in FINGERING_TEMPLATE if low <= entry.get("midi", 0) < high
            ]
            if filtered:
                return filtered
        # Use the full traditional French Bb clarinet set by default
        return list(FINGERING_TEMPLATE)


__all__ = ["ClarinetGeometryBuilder", "BuilderResult"]

