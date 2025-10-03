"""Generate Bb clarinet geometries driven by fingering charts and simulations."""

from __future__ import annotations

from datetime import datetime

from .geometry_builder import ClarinetGeometryBuilder
from .models import RecommendRequest, RecommendResponse


_BUILDER = ClarinetGeometryBuilder()


def recommend_geometry(payload: RecommendRequest) -> RecommendResponse:
    """Create and optimise a :class:`~openwind_service.models.Geometry` instance."""

    result = _BUILDER.build(payload)
    geometry = result.geometry.model_copy(update={
        "mouthpiece_params": {"reed_strength": payload.player_pref.profile}
    })
    return RecommendResponse(
        geometry=geometry,
        notes=result.notes,
        created_at=datetime.utcnow(),
    )


__all__ = ["recommend_geometry"]
