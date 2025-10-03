"""Clarinet geometry builder driven by fingering charts and OpenWInD simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
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


# Baseline measurements captured from a Buffet-style French Bb clarinet (values in mm).
# These serve as priors that are blended with the acoustically-derived targets so
# the generator follows the ergonomics of a production instrument.
_BASELINE_AXIAL_MM = np.array(
    [
        146.0,
        160.0,
        173.5,
        186.8,
        199.6,
        213.5,
        227.2,
        240.9,
        254.8,
        268.4,
        282.7,
        297.1,
        311.9,
        326.4,
        341.2,
        356.3,
        372.0,
    ]
)
_BASELINE_DIAMETER_MM = np.array(
    [
        6.4,
        7.1,
        7.5,
        8.1,
        8.4,
        9.0,
        9.3,
        9.5,
        9.7,
        10.0,
        10.2,
        10.5,
        10.8,
        11.2,
        11.5,
        11.9,
        12.3,
    ]
)
_BASELINE_CHIMNEY_MM = np.array(
    [
        12.0,
        11.8,
        11.6,
        11.4,
        11.1,
        10.8,
        10.6,
        10.3,
        10.0,
        9.7,
        9.4,
        9.1,
        8.8,
        8.4,
        8.1,
        7.8,
        7.5,
    ]
)
_BASELINE_UNDERCUT_MM = np.array(
    [
        1.3,
        1.25,
        1.20,
        1.15,
        1.10,
        1.05,
        1.00,
        0.95,
        0.90,
        0.85,
        0.80,
        0.75,
        0.70,
        0.65,
        0.60,
        0.55,
        0.50,
    ]
)


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


def _normalise_state(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0 if raw else 0.0
    return float(np.clip(value, 0.0, 1.0))


def _first_open_index(states: Sequence[object]) -> Tuple[int | None, bool]:
    """Locate the first hole that is not fully closed and whether it is a shading/half-hole."""

    for idx, raw in enumerate(states):
        value = _normalise_state(raw)
        if value >= 0.5:
            return idx, value < 0.95
    return None, False


@dataclass
class _HoleAggregate:
    """Collect acoustic statistics for each tone hole."""

    acoustic_lengths_m: List[float] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    support_lengths_m: List[float] = field(default_factory=list)
    freq_samples_hz: List[float] = field(default_factory=list)


@dataclass
class BuilderResult:
    geometry: Geometry
    notes: List[str]
    convergence: List[float]
    history: List[Dict[str, float]]
    intonation: List[Dict[str, object]]
    restarts: int = 1
    runs: List[Dict[str, object]] = field(default_factory=list)


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
        optimised, convergence, history, restarts, runs = self._optimise_geometry(
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
            "optimisation_restarts": restarts,
            "optimised_score": convergence[-1] if convergence else None,
            "optimisation_runs": runs,
            **impedance_bundle,
        }
        optimised = optimised.model_copy(update={"metadata": metadata})
        return BuilderResult(
            geometry=optimised,
            notes=notes,
            convergence=convergence,
            history=history,
            intonation=fingering_checks,
            restarts=restarts,
            runs=runs,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _geometry_from_fingerings(
        self, payload: RecommendRequest, entries: Sequence[Dict[str, object]]
    ) -> Geometry:
        """Construct an initial geometry consistent with the fingering chart."""

        constraints = payload.constraints
        bore_default = 14.7
        bore_mm = float(
            np.clip(
                bore_default,
                constraints.min_bore_mm or 13.5,
                constraints.max_bore_mm or 15.2,
            )
        )

        temp_c = self._simulation_options.temp_C
        speed = _speed_of_sound(temp_c)

        hole_count = len(entries[0]["holes"]) if entries else 0
        if hole_count == 0:
            raise ValueError("No fingering information provided for geometry construction.")

        aggregates, all_closed_lengths = self._collect_statistics(
            entries, payload, speed, hole_count
        )
        if all_closed_lengths:
            length_m = float(np.clip(np.median(all_closed_lengths), 0.62, 0.68))
        else:
            deepest_idx = max((idx for idx in aggregates if isinstance(idx, int)), default=hole_count - 1)
            deepest = aggregates.get(deepest_idx)
            if deepest and deepest.acoustic_lengths_m:
                length_m = float(np.clip(np.mean(deepest.acoustic_lengths_m), 0.63, 0.69))
            else:
                length_m = 0.66
        length_mm = length_m * M_TO_MM

        spacing_min_mm = constraints.min_spacing_mm or 9.5
        positions_mm = self._blend_positions(aggregates, hole_count, length_mm, spacing_min_mm)
        diameters_mm = self._blend_diameters(aggregates, bore_mm, hole_count)
        chimneys_mm = self._blend_profile(_BASELINE_CHIMNEY_MM, aggregates, hole_count, 0.65, 6.8, 12.2)
        undercuts_mm = self._blend_profile(_BASELINE_UNDERCUT_MM, aggregates, hole_count, 0.45, 0.35, 1.35)

        holes = [
            ToneHole(
                index=idx,
                axial_pos_mm=float(positions_mm[idx]),
                diameter_mm=float(diameters_mm[idx]),
                chimney_mm=float(chimneys_mm[idx]),
                undercut_mm=float(undercuts_mm[idx]),
                closed=False,
            )
            for idx in range(hole_count)
        ]

        metadata = {
            "fingerings_used": [entry["note"] for entry in entries],
            "fingering_labels": [entry["label"] for entry in entries],
            "speed_of_sound_mps": speed,
            "initial_length_mm": length_mm,
            "baseline_layout_mm": _BASELINE_AXIAL_MM[:hole_count].tolist(),
            "baseline_diameter_mm": _BASELINE_DIAMETER_MM[:hole_count].tolist(),
            "chimney_profile_mm": chimneys_mm.tolist(),
            "undercut_profile_mm": undercuts_mm.tolist(),
            "hole_statistics": {
                str(idx): self._serialise_hole_stats(aggregates.get(idx))
                for idx in range(hole_count)
            },
            "bell_profile": {"type": "bessel", "shape": 0.7},
        }

        geometry = Geometry(
            bore_mm=bore_mm,
            length_mm=length_mm,
            tone_holes=holes,
            metadata=metadata,
        )
        return geometry

    def _collect_statistics(
        self,
        entries: Sequence[Dict[str, object]],
        payload: RecommendRequest,
        speed: float,
        hole_count: int,
    ) -> Tuple[Dict[int, _HoleAggregate], List[float]]:
        aggregates: Dict[int, _HoleAggregate] = {idx: _HoleAggregate() for idx in range(hole_count)}
        closed_lengths: List[float] = []

        for entry in entries:
            midi = int(entry.get("midi", 0))
            freq = _note_frequency(midi, payload.target_a4_hz)
            mode = _register_mode(midi)
            length_m = (mode * speed) / (4.0 * freq)

            states = entry.get("holes", [])
            first_open, is_half = _first_open_index(states)

            if first_open is None:
                closed_lengths.append(length_m)
                continue

            open_indices = [idx for idx, raw in enumerate(states) if _normalise_state(raw) >= 0.5]
            if not open_indices:
                open_indices = [first_open]

            for position, idx in enumerate(open_indices):
                agg = aggregates.setdefault(idx, _HoleAggregate())
                openness = _normalise_state(states[idx])
                weight = 1.0 if idx == first_open else 0.28
                if position == 1:
                    weight *= 0.55
                elif position >= 2:
                    weight *= 0.35
                if openness < 0.95:
                    weight *= 0.7
                if is_half and idx == first_open:
                    weight *= 0.85

                agg.acoustic_lengths_m.append(length_m)
                agg.weights.append(float(weight))
                agg.freq_samples_hz.append(float(freq))

            previous = first_open - 1
            if previous >= 0:
                prev_agg = aggregates.setdefault(previous, _HoleAggregate())
                prev_agg.support_lengths_m.append(length_m)

        return aggregates, closed_lengths

    def _blend_positions(
        self,
        aggregates: Dict[int, _HoleAggregate],
        hole_count: int,
        length_mm: float,
        spacing_min_mm: float,
    ) -> np.ndarray:
        baseline = _BASELINE_AXIAL_MM[:hole_count]
        spacing_min_mm = max(spacing_min_mm, 8.5)
        result = np.empty(hole_count, dtype=float)
        previous = 18.0
        bell_guard = length_mm - 35.0

        for idx in range(hole_count):
            agg = aggregates.get(idx, _HoleAggregate())
            if agg.acoustic_lengths_m and agg.weights:
                target_mm = float(
                    np.average(
                        np.asarray(agg.acoustic_lengths_m) * M_TO_MM,
                        weights=np.asarray(agg.weights),
                    )
                )
            else:
                target_mm = float(baseline[idx]) if idx < baseline.size else baseline[-1]

            support_mm = (
                float(np.mean(np.asarray(agg.support_lengths_m) * M_TO_MM))
                if agg.support_lengths_m
                else target_mm
            )

            baseline_mm = float(baseline[idx]) if idx < baseline.size else baseline[-1]
            blended = 0.55 * baseline_mm + 0.35 * target_mm + 0.10 * support_mm
            blended = max(blended, previous + spacing_min_mm)
            blended = min(blended, bell_guard - (hole_count - idx - 1) * spacing_min_mm)
            result[idx] = blended
            previous = blended

        return result

    def _blend_diameters(
        self,
        aggregates: Dict[int, _HoleAggregate],
        bore_mm: float,
        hole_count: int,
    ) -> np.ndarray:
        baseline = _BASELINE_DIAMETER_MM[:hole_count]
        result = np.empty(hole_count, dtype=float)
        freq_samples: List[float] = []
        for idx in range(hole_count):
            freq_samples.extend(aggregates.get(idx, _HoleAggregate()).freq_samples_hz)

        if freq_samples:
            freq_array = np.asarray(freq_samples)
            freq_min = float(np.min(freq_array))
            freq_max = float(np.max(freq_array))
        else:
            freq_min = _note_frequency(48, 440.0)
            freq_max = _note_frequency(84, 440.0)

        for idx in range(hole_count):
            agg = aggregates.get(idx, _HoleAggregate())
            if agg.freq_samples_hz:
                freq = float(np.average(agg.freq_samples_hz, weights=agg.weights or None))
            else:
                ratio = idx / max(hole_count - 1, 1)
                freq = freq_min + ratio * (freq_max - freq_min)

            norm = (freq - freq_min) / max(freq_max - freq_min, 1e-6)
            baseline_mm = float(baseline[idx]) if idx < baseline.size else baseline[-1]
            adjusted = baseline_mm * (0.85 + 0.25 * norm)
            adjusted = np.clip(adjusted, 4.5, bore_mm * 1.25)
            result[idx] = float(adjusted)

        return result

    def _blend_profile(
        self,
        baseline: np.ndarray,
        aggregates: Dict[int, _HoleAggregate],
        hole_count: int,
        adaptability: float,
        lower: float,
        upper: float,
    ) -> np.ndarray:
        result = np.empty(hole_count, dtype=float)
        for idx in range(hole_count):
            base = float(baseline[idx]) if idx < baseline.size else baseline[-1]
            agg = aggregates.get(idx, _HoleAggregate())
            if agg.support_lengths_m:
                deviation = (np.mean(np.asarray(agg.support_lengths_m) * M_TO_MM) - base) * adaptability
            elif agg.acoustic_lengths_m:
                deviation = (np.mean(np.asarray(agg.acoustic_lengths_m) * M_TO_MM) - base) * 0.25
            else:
                deviation = 0.0
            value = np.clip(base + deviation, lower, upper)
            result[idx] = float(value)
        return result

    def _serialise_hole_stats(self, aggregate: _HoleAggregate | None) -> Dict[str, List[float]]:
        agg = aggregate or _HoleAggregate()
        return {
            "length_samples_mm": [l * M_TO_MM for l in agg.acoustic_lengths_m],
            "weights": list(agg.weights),
            "support_lengths_mm": [l * M_TO_MM for l in agg.support_lengths_m],
            "frequencies_hz": list(agg.freq_samples_hz),
        }

    def _optimise_geometry(
        self,
        payload: RecommendRequest,
        geometry: Geometry,
        notes: Sequence[str],
        options: SimulationOptions,
    ) -> Tuple[Geometry, List[float], List[Dict[str, float]], int, List[Dict[str, object]]]:
        """Refine geometry using OpenWInD impedance simulations."""

        profile = payload.player_pref.profile.lower()
        if profile == "bright":
            objective = ObjectiveWeights(intonation=1.0, impedance_smoothness=0.15, register_alignment=0.35)
        elif profile in {"dark", "warm"}:
            objective = ObjectiveWeights(intonation=1.1, impedance_smoothness=0.4, register_alignment=0.65)
        else:
            objective = ObjectiveWeights()

        restarts = 2 if len(notes) > 18 else 1
        best_geom = geometry
        best_convergence: List[float] = []
        best_history: List[Dict[str, float]] = []
        best_score = float("inf")
        runs_summary: List[Dict[str, object]] = []

        for restart in range(restarts):
            seed = (hash(payload.player_pref.profile.lower()) & 0xFFFF) ^ (restart << 11)
            rng = np.random.default_rng(seed)
            start_geom = geometry if restart == 0 else self._warm_start_geometry(geometry, rng, payload)
            candidate, convergence, history = self._run_single_optimisation(
                start_geom,
                rng,
                objective,
                options,
                notes,
                payload,
                restart,
            )
            final_score = convergence[-1] if convergence else float("inf")
            runs_summary.append(
                {
                    "restart": restart,
                    "final_score": final_score,
                    "iterations": len(convergence) - 1 if convergence else 0,
                    "convergence": list(convergence),
                }
            )
            if final_score < best_score:
                best_score = final_score
                best_geom = candidate
                best_convergence = convergence
                best_history = history

        return best_geom, best_convergence, best_history, restarts, runs_summary

    def _run_single_optimisation(
        self,
        start_geometry: Geometry,
        rng: np.random.Generator,
        objective: ObjectiveWeights,
        options: SimulationOptions,
        notes: Sequence[str],
        payload: RecommendRequest,
        restart_index: int,
    ) -> Tuple[Geometry, List[float], List[Dict[str, float]]]:
        """Execute a single optimisation run with a temperature-controlled mutator."""
        max_iter = 24
        constraints = payload.constraints
        spacing_min = constraints.min_spacing_mm or 9.5
        stats_meta = start_geometry.metadata.get("hole_statistics", {}) if start_geometry.metadata else {}
        baseline_layout = np.asarray(start_geometry.metadata.get("baseline_layout_mm", [])) if start_geometry.metadata else np.asarray([])

        hole_count = len(start_geometry.tone_holes)
        preferred_positions = np.empty(hole_count, dtype=float)
        diameter_targets = np.empty(hole_count, dtype=float)
        chimney_targets = np.empty(hole_count, dtype=float)
        undercut_targets = np.empty(hole_count, dtype=float)

        for hole in start_geometry.tone_holes:
            idx = hole.index
            stat = stats_meta.get(str(idx), {}) if isinstance(stats_meta, dict) else {}
            lengths = stat.get("length_samples_mm", []) if isinstance(stat, dict) else []
            weights = stat.get("weights", []) if isinstance(stat, dict) else []
            if lengths:
                preferred_positions[idx] = float(
                    np.average(np.asarray(lengths), weights=np.asarray(weights) if weights else None)
                )
            elif baseline_layout.size > idx:
                preferred_positions[idx] = float(baseline_layout[idx])
            else:
                preferred_positions[idx] = float(hole.axial_pos_mm)

            diameter_targets[idx] = float(hole.diameter_mm)
            chimney_targets[idx] = float(hole.chimney_mm)
            undercut_targets[idx] = float(hole.undercut_mm or 0.0)

        length_guard = max(start_geometry.length_mm - 32.0, start_geometry.length_mm * 0.7)
        bore_bounds = (
            constraints.min_bore_mm or 13.4,
            constraints.max_bore_mm or 15.4,
        )

        trace: List[Dict[str, float]] = []

        def mutate(base: Geometry, iteration: int) -> Geometry:
            clone = base.model_copy(deep=True)
            temperature = max(0.18, np.exp(-0.075 * (iteration + 1 + restart_index * 3)))
            bore_delta = float(rng.normal(0.0, 0.04 * temperature))
            clone.bore_mm = float(np.clip(clone.bore_mm + bore_delta, *bore_bounds))

            for hole in clone.tone_holes:
                idx = hole.index
                preferred = preferred_positions[idx] if idx < preferred_positions.size else hole.axial_pos_mm
                drift = preferred - hole.axial_pos_mm
                hole.axial_pos_mm += float(drift * 0.2)
                hole.axial_pos_mm += float(rng.normal(0.0, 0.42 * temperature))
                hole.axial_pos_mm = float(np.clip(hole.axial_pos_mm, 18.0 + idx * 3.8, length_guard))

                diameter_target = diameter_targets[idx] if idx < diameter_targets.size else hole.diameter_mm
                hole.diameter_mm += float((diameter_target - hole.diameter_mm) * 0.25)
                hole.diameter_mm += float(rng.normal(0.0, 0.28 * temperature))
                hole.diameter_mm = float(np.clip(hole.diameter_mm, 4.2, clone.bore_mm * 1.32))

                chimney_target = chimney_targets[idx] if idx < chimney_targets.size else hole.chimney_mm
                hole.chimney_mm = float(np.clip(
                    hole.chimney_mm + (chimney_target - hole.chimney_mm) * 0.3 + rng.normal(0.0, 0.22 * temperature),
                    6.4,
                    12.5,
                ))

                target_undercut = undercut_targets[idx] if idx < undercut_targets.size else (hole.undercut_mm or 0.0)
                hole.undercut_mm = float(
                    np.clip(
                        (hole.undercut_mm or 0.0)
                        + (target_undercut - (hole.undercut_mm or 0.0)) * 0.35
                        + rng.normal(0.0, 0.12 * temperature),
                        0.3,
                        1.5,
                    )
                )

            self._enforce_spacing(clone, spacing_min, length_guard)
            return clone

        def callback(iteration: int, score: float, geom: Geometry, metrics: Dict[str, float]) -> None:
            trace.append({"iteration": iteration, "score": score, "restart": restart_index, **metrics})

        best_geom, convergence, _sensitivities, history = self._adapter.optimise_geometry(
            start_geometry,
            options,
            objective,
            max_iter,
            mutate,
            callback,
            fingering_notes=notes,
        )

        combined_history: List[Dict[str, float]] = []
        trace_map = {int(item["iteration"]): item for item in trace}
        for record in history:
            iteration = int(record.get("iteration", -1))
            merged = {**record, **trace_map.get(iteration, {}), "restart": restart_index}
            combined_history.append(merged)

        return best_geom, convergence, combined_history

    def _warm_start_geometry(
        self,
        geometry: Geometry,
        rng: np.random.Generator,
        payload: RecommendRequest,
    ) -> Geometry:
        """Perturb the baseline geometry to explore a different optimisation basin."""
        warmed = geometry.model_copy(deep=True)
        spacing_min = payload.constraints.min_spacing_mm or 9.5
        length_guard = max(warmed.length_mm - 32.0, warmed.length_mm * 0.7)
        warmed.bore_mm = float(
            np.clip(
                warmed.bore_mm + rng.normal(0.0, 0.08),
                payload.constraints.min_bore_mm or 13.4,
                payload.constraints.max_bore_mm or 15.4,
            )
        )
        for idx, hole in enumerate(warmed.tone_holes):
            hole.axial_pos_mm += float(rng.normal(0.0, 1.2))
            hole.diameter_mm = float(np.clip(hole.diameter_mm + rng.normal(0.0, 0.35), 4.2, warmed.bore_mm * 1.35))
            hole.chimney_mm = float(np.clip(hole.chimney_mm + rng.normal(0.0, 0.3), 6.2, 12.8))
            hole.undercut_mm = float(np.clip((hole.undercut_mm or 0.0) + rng.normal(0.0, 0.15), 0.3, 1.55))
        self._enforce_spacing(warmed, spacing_min, length_guard)
        return warmed

    def _enforce_spacing(
        self,
        geometry: Geometry,
        spacing_min: float,
        length_guard: float,
    ) -> None:
        """Ensure tone holes remain ordered with ergonomic spacing constraints."""
        spacing_min = max(spacing_min, 8.0)
        sorted_holes = sorted(geometry.tone_holes, key=lambda h: h.axial_pos_mm)
        previous = 18.0
        remaining = len(sorted_holes)
        for idx, hole in enumerate(sorted_holes):
            remaining = len(sorted_holes) - idx - 1
            min_pos = previous + spacing_min
            max_pos = max(length_guard - remaining * spacing_min, min_pos)
            hole.axial_pos_mm = float(np.clip(hole.axial_pos_mm, min_pos, max_pos))
            previous = hole.axial_pos_mm
        geometry.tone_holes = sorted(sorted_holes, key=lambda h: h.index)

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

