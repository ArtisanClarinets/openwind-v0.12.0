"""Standard Bb clarinet fingering utilities."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .models import Geometry, ToneHole

# The fingering template is defined from the mouthpiece (index 0) to the bell (last).
# 0 -> closed, 1 -> open. Half-hole fingerings use 0.5.
FINGERING_TEMPLATE: List[Dict[str, object]] = [
    {"note": "C3", "midi": 48, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "C#3", "midi": 49, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]},
    {"note": "D3", "midi": 50, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]},
    {"note": "Eb3", "midi": 51, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]},
    {"note": "E3", "midi": 52, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]},
    {"note": "F3", "midi": 53, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]},
    {"note": "F#3", "midi": 54, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]},
    {"note": "G3", "midi": 55, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "Ab3", "midi": 56, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "A3", "midi": 57, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "Bb3", "midi": 58, "holes": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "B3", "midi": 59, "holes": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "C4", "midi": 60, "holes": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "C#4", "midi": 61, "holes": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "D4", "midi": 62, "holes": [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "Eb4", "midi": 63, "holes": [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "E4", "midi": 64, "holes": [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "F4", "midi": 65, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},
    {"note": "F#4", "midi": 66, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5]},
    {"note": "G4", "midi": 67, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]},
    {"note": "Ab4", "midi": 68, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]},
    {"note": "A4", "midi": 69, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]},
    {"note": "Bb4", "midi": 70, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]},
    {"note": "B4", "midi": 71, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]},
    {"note": "C5", "midi": 72, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "C#5", "midi": 73, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "D5", "midi": 74, "holes": [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "Eb5", "midi": 75, "holes": [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "E5", "midi": 76, "holes": [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "F5", "midi": 77, "holes": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "F#5", "midi": 78, "holes": [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "G5", "midi": 79, "holes": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "Ab5", "midi": 80, "holes": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "A5", "midi": 81, "holes": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "Bb5", "midi": 82, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "B5", "midi": 83, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
    {"note": "C6", "midi": 84, "holes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
]


DEFAULT_NOTES: List[str] = [entry["note"] for entry in FINGERING_TEMPLATE]


def build_fingering_chart(holes: Sequence[ToneHole], notes: Iterable[str] | None = None) -> List[List[object]]:
    """Create a fingering chart list compatible with :class:`InstrumentGeometry`."""

    if notes is None:
        notes = DEFAULT_NOTES
    notes = list(notes)
    labels = [f"H{h.index+1}" for h in holes]

    chart = [["label", *notes]]
    template_lookup: Dict[str, Dict[str, object]] = {entry["note"]: entry for entry in FINGERING_TEMPLATE}
    for label, hole in zip(labels, holes):
        row: List[object] = [label]
        for note in notes:
            state = template_lookup.get(note, {"holes": [1] * len(holes)})
            holes_states: Sequence[float] = state["holes"]  # type: ignore[index]
            idx = min(hole.index, len(holes_states) - 1)
            value = holes_states[idx]
            if isinstance(value, (int, float)):
                row.append(value)
            else:
                row.append(1 if value else 0)
        chart.append(row)
    return chart


def fingering_sequence(notes: Iterable[str] | None = None) -> List[Dict[str, object]]:
    """Return the fingering entries filtered by requested notes."""

    if notes is None:
        return FINGERING_TEMPLATE
    wanted = set(notes)
    return [entry for entry in FINGERING_TEMPLATE if entry["note"] in wanted]


__all__ = ["FINGERING_TEMPLATE", "DEFAULT_NOTES", "build_fingering_chart", "fingering_sequence"]
