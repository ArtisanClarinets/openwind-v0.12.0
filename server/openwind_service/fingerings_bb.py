"""Standard Bb clarinet fingering utilities with alternate variants."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .models import ToneHole


def _normalise_state(value: object) -> float:
    """Convert fingering state objects to ``float`` values."""

    if isinstance(value, (int, float)):
        return float(value)
    return 1.0 if value else 0.0


def _first_open_index(holes: Sequence[object]) -> int | None:
    for idx, value in enumerate(holes):
        if _normalise_state(value) >= 0.5:
            return idx
    return None


def _previous_closed_index(holes: Sequence[object], start: int) -> int | None:
    for idx in range(start - 1, -1, -1):
        if _normalise_state(holes[idx]) < 0.5:
            return idx
    return None


def _next_closed_index(holes: Sequence[object], start: int) -> int | None:
    for idx in range(start + 1, len(holes)):
        if _normalise_state(holes[idx]) < 0.5:
            return idx
    return None


def _make_entry(note: str, midi: int, holes: Sequence[object], variant: str = "standard") -> Dict[str, object]:
    label = note if variant == "standard" else f"{note} ({variant})"
    return {
        "note": note,
        "midi": midi,
        "holes": list(holes),
        "variant": variant,
        "label": label,
    }


__FRENCH_STANDARD: List[Dict[str, object]] = [
    _make_entry("C3", 48, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("C#3", 49, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
    _make_entry("D3", 50, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
    _make_entry("Eb3", 51, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]),
    _make_entry("E3", 52, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]),
    _make_entry("F3", 53, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]),
    _make_entry("F#3", 54, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]),
    _make_entry("G3", 55, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("Ab3", 56, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("A3", 57, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("Bb3", 58, [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("B3", 59, [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("C4", 60, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("C#4", 61, [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("D4", 62, [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("Eb4", 63, [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("E4", 64, [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("F4", 65, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    _make_entry("F#4", 66, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5]),
    _make_entry("G4", 67, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]),
    _make_entry("Ab4", 68, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]),
    _make_entry("A4", 69, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]),
    _make_entry("Bb4", 70, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]),
    _make_entry("B4", 71, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]),
    _make_entry("C5", 72, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("C#5", 73, [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("D5", 74, [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("Eb5", 75, [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("E5", 76, [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("F5", 77, [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("F#5", 78, [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("G5", 79, [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("Ab5", 80, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("A5", 81, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("Bb5", 82, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("B5", 83, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    _make_entry("C6", 84, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
]


def _auto_variants(holes: Sequence[object]) -> List[tuple[str, List[object]]]:
    first_open = _first_open_index(holes)
    variants: List[tuple[str, List[object]]] = []

    if first_open is None:
        shaded = list(holes)
        shaded[-1] = 0.5
        variants.append(("bell-vent", shaded))

        register = list(holes)
        register[-2] = 0.5
        variants.append(("register-vent", register))
        return variants

    prev_idx = _previous_closed_index(holes, first_open)
    if prev_idx is not None:
        shaded = list(holes)
        shaded[prev_idx] = 0.5
        variants.append(("half-vent", shaded))

    next_idx = _next_closed_index(holes, first_open)
    if next_idx is not None:
        extended = list(holes)
        extended[next_idx] = 1
        variants.append(("long", extended))
    else:
        resonant = list(holes)
        resonant[-1] = 0.5
        variants.append(("resonance", resonant))

    if first_open > 0:
        shade = list(holes)
        shade[first_open - 1] = 0.5
        variants.append(("ring-shade", shade))

    unique: List[tuple[str, List[object]]] = []
    seen = {tuple(_normalise_state(v) for v in holes)}
    for name, variant in variants:
        key = tuple(_normalise_state(v) for v in variant)
        if key not in seen:
            unique.append((name, variant))
            seen.add(key)
    return unique


def _build_template() -> List[Dict[str, object]]:
    template: List[Dict[str, object]] = []
    for entry in __FRENCH_STANDARD:
        template.append(entry)
        for name, variant in _auto_variants(entry["holes"]):
            template.append(
                _make_entry(
                    entry["note"],
                    int(entry["midi"]),
                    variant,
                    variant=name,
                )
            )
    return template


FINGERING_TEMPLATE: List[Dict[str, object]] = _build_template()
_DEFAULT_BY_NOTE: Dict[str, List[Dict[str, object]]] = {}
_DEFAULT_BY_LABEL: Dict[str, Dict[str, object]] = {}
for entry in FINGERING_TEMPLATE:
    _DEFAULT_BY_LABEL[entry["label"]] = entry
    _DEFAULT_BY_NOTE.setdefault(entry["note"], []).append(entry)

DEFAULT_NOTES: List[str] = [entry["label"] for entry in FINGERING_TEMPLATE]


def _resolve_notes(notes: Iterable[str] | None) -> List[Dict[str, object]]:
    if notes is None:
        return list(FINGERING_TEMPLATE)

    resolved: List[Dict[str, object]] = []
    seen: set[str] = set()
    for item in notes:
        token = str(item)
        if token in _DEFAULT_BY_LABEL:
            entry = _DEFAULT_BY_LABEL[token]
            if entry["label"] not in seen:
                resolved.append(entry)
                seen.add(entry["label"])
            continue

        for entry in _DEFAULT_BY_NOTE.get(token, []):
            if entry["label"] not in seen:
                resolved.append(entry)
                seen.add(entry["label"])
    if not resolved:
        return list(FINGERING_TEMPLATE)
    return resolved


def build_fingering_chart(holes: Sequence[ToneHole], notes: Iterable[str] | None = None) -> List[List[object]]:
    """Create a fingering chart list compatible with :class:`InstrumentGeometry`."""

    entries = _resolve_notes(notes)
    tonehole_labels = [f"H{h.index+1}" for h in holes]
    column_labels = [entry["label"] for entry in entries]

    chart: List[List[object]] = [["label", *column_labels]]
    for label, hole in zip(tonehole_labels, holes):
        row: List[object] = [label]
        for entry in entries:
            holes_states: Sequence[object] = entry["holes"]
            idx = min(hole.index, len(holes_states) - 1)
            state = holes_states[idx]
            if isinstance(state, (int, float)):
                row.append(state)
            else:
                row.append(1 if state else 0)
        chart.append(row)
    return chart


def fingering_sequence(notes: Iterable[str] | None = None) -> List[Dict[str, object]]:
    """Return the fingering entries filtered by requested notes or labels."""

    return _resolve_notes(notes)


__all__ = [
    "FINGERING_TEMPLATE",
    "DEFAULT_NOTES",
    "build_fingering_chart",
    "fingering_sequence",
]
