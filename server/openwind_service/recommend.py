"""Generate starting geometries for a Bb clarinet."""

from __future__ import annotations

from datetime import datetime
from typing import List

import numpy as np

from .models import Geometry, RecommendRequest, RecommendResponse, ToneHole

_DEFAULT_BORE_MM = 14.6
_DEFAULT_LENGTH_MM = 660.0
_DEFAULT_CHIMNEY_MM = 12.0

# canonical offsets in millimetres from the top of the upper joint
_BASE_HOLE_POSITIONS = np.array([
    35, 63, 91, 119, 147, 175, 203, 231, 259, 287, 315, 343, 371, 399, 427, 455, 490
])
_BASE_HOLE_DIAMETERS = np.array([
    11.0, 8.5, 7.2, 6.5, 6.0, 6.0, 6.2, 6.4, 6.6, 6.8, 7.0, 8.8, 10.5, 12.5, 14.2, 15.0, 16.0
])


def recommend_geometry(payload: RecommendRequest) -> RecommendResponse:
    """Create a :class:`Geometry` based on heuristics and request constraints."""

    constraints = payload.constraints
    bore_mm = np.clip(
        _DEFAULT_BORE_MM,
        constraints.min_bore_mm or 13.5,
        constraints.max_bore_mm or 15.2,
    )

    length_mm = _DEFAULT_LENGTH_MM
    target_a4 = payload.target_a4_hz
    if target_a4 >= 442:
        length_mm *= 0.997
    elif target_a4 <= 438:
        length_mm *= 1.004

    hole_count = len(_BASE_HOLE_POSITIONS)
    if constraints.min_hole_count is not None:
        hole_count = max(hole_count, constraints.min_hole_count)
    if constraints.max_hole_count is not None:
        hole_count = min(hole_count, constraints.max_hole_count)

    scale = (length_mm - 120.0) / (_BASE_HOLE_POSITIONS[-1] - _BASE_HOLE_POSITIONS[0])
    spacing_min = constraints.min_spacing_mm or 10.0
    holes: List[ToneHole] = []
    previous = 0.0

    for idx in range(hole_count):
        base_pos = _BASE_HOLE_POSITIONS[min(idx, len(_BASE_HOLE_POSITIONS) - 1)]
        pos_mm = max(previous + spacing_min, base_pos * scale)
        diameter = float(_BASE_HOLE_DIAMETERS[min(idx, len(_BASE_HOLE_DIAMETERS) - 1)])
        diameter = np.clip(diameter, 5.0, bore_mm * 1.2)
        chimney_mm = max(_DEFAULT_CHIMNEY_MM - 0.2 * idx, 8.0)
        holes.append(
            ToneHole(
                index=idx,
                axial_pos_mm=pos_mm,
                diameter_mm=diameter,
                chimney_mm=chimney_mm,
                closed=False,
            )
        )
        previous = pos_mm

    geometry = Geometry(
        bore_mm=float(bore_mm),
        length_mm=float(length_mm),
        tone_holes=holes,
        mouthpiece_params={"reed_strength": payload.player_pref.profile},
        metadata={
            "target_a4_hz": payload.target_a4_hz,
            "scale": payload.scale,
            "player_pref": payload.player_pref.profile,
            "min_spacing_mm": spacing_min,

        },
    )
    notes = [fnote for fnote in (payload.include_register, "standard", "altissimo") if fnote]
    return RecommendResponse(geometry=geometry, notes=notes, created_at=datetime.utcnow())


__all__ = ["recommend_geometry"]
