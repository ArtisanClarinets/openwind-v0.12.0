"""Pydantic schemas for the OpenWInD Bb clarinet microservice."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ToneHole(BaseModel):
    """Tone-hole description in millimetres."""

    index: int = Field(ge=0)
    axial_pos_mm: float = Field(..., ge=0)
    diameter_mm: float = Field(..., gt=0)
    chimney_mm: float = Field(..., gt=0)
    undercut_mm: Optional[float] = Field(default=None, ge=0)
    closed: bool = False

    @property
    def radius_m(self) -> float:
        """Return the radius in meters."""

        return self.diameter_mm / 2000.0


class Geometry(BaseModel):
    """Simplified description of a Bb clarinet geometry."""

    bore_mm: float = Field(..., gt=0, description="Inner bore diameter in millimetres.")
    length_mm: float = Field(..., gt=0, description="Overall acoustic length in millimetres.")
    barrel_length_mm: Optional[float] = Field(default=65.0, gt=0)
    mouthpiece_params: Dict[str, Any] = Field(default_factory=dict)
    tone_holes: List[ToneHole]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("tone_holes")
    def ensure_sorted(cls, holes: List[ToneHole]) -> List[ToneHole]:
        """Keep tone holes ordered by axial position then index."""

        return sorted(holes, key=lambda h: (h.axial_pos_mm, h.index))


class BoreConstraints(BaseModel):
    min_bore_mm: Optional[float] = Field(default=None, gt=0)
    max_bore_mm: Optional[float] = Field(default=None, gt=0)
    min_hole_count: Optional[int] = Field(default=None, ge=0)
    max_hole_count: Optional[int] = Field(default=None, ge=0)
    min_spacing_mm: Optional[float] = Field(default=None, ge=0)
    max_spacing_mm: Optional[float] = Field(default=None, ge=0)


class PlayerPreference(BaseModel):
    profile: str = Field(default="balanced")
    articulation: str = Field(default="standard")
    brightness: str = Field(default="neutral")


class RecommendRequest(BaseModel):
    target_a4_hz: float = Field(default=440.0, gt=0)
    scale: str = Field(default="equal")
    constraints: BoreConstraints = Field(default_factory=BoreConstraints)
    player_pref: PlayerPreference = Field(default_factory=PlayerPreference)
    include_register: str = Field(default="standard")


class RecommendResponse(BaseModel):
    geometry: Geometry
    notes: List[str]
    created_at: datetime


class SimulationOptions(BaseModel):
    temp_C: float = Field(default=22.0)
    freq_min_hz: float = Field(default=100.0, ge=0)
    freq_max_hz: float = Field(default=2500.0, gt=0)
    n_points: int = Field(default=2048, gt=10)
    modes: int = Field(default=8, gt=0)


class SimRequest(BaseModel):
    geometry: Geometry
    options: SimulationOptions = Field(default_factory=SimulationOptions)
    fingering_notes: Optional[List[str]] = None


class IntonationResult(BaseModel):
    note: str
    midi: int
    target_hz: float
    resonance_hz: float
    cents: float


class SimulationResult(BaseModel):
    freq_hz: List[float]
    zin_abs: List[float]
    zin_re: List[float]
    zin_im: List[float]
    intonation: List[IntonationResult]
    fingering_notes: List[str]


class ObjectiveWeights(BaseModel):
    intonation: float = Field(default=1.0, ge=0)
    impedance_smoothness: float = Field(default=0.25, ge=0)
    register_alignment: float = Field(default=0.5, ge=0)


class OptimizationBounds(BaseModel):
    bore_delta_mm: float = Field(default=0.5, ge=0)
    hole_diameter_delta_mm: float = Field(default=0.6, ge=0)
    hole_position_delta_mm: float = Field(default=2.5, ge=0)


class OptRequest(BaseModel):
    geometry: Geometry
    objective: ObjectiveWeights = Field(default_factory=ObjectiveWeights)
    bounds: OptimizationBounds = Field(default_factory=OptimizationBounds)
    max_iter: int = Field(default=40, gt=0)
    seed: int = Field(default=1234)


class OptimizeResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class OptimizeResult(BaseModel):
    job_id: str
    status: str
    geometry: Geometry
    convergence: List[float]
    history: List[Dict[str, Any]]
    sensitivity: List[Dict[str, Any]]
    completed_at: datetime


class ExportRequest(BaseModel):
    geometry: Geometry
    fmt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
