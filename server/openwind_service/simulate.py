"""Simulation orchestration helpers."""

from __future__ import annotations

from typing import Iterable, List

import numpy as np

from .models import IntonationResult, SimRequest, SimulationResult
from .openwind_adapter import OpenWInDAdapter


class SimulationService:
    """High-level helper orchestrating impedance computation and post-processing."""

    def __init__(self, adapter: OpenWInDAdapter) -> None:
        self._adapter = adapter

    def run(self, payload: SimRequest) -> SimulationResult:
        fingering_notes = payload.fingering_notes or []
        data = self._adapter.compute_impedance(payload.geometry, payload.options, fingering_notes)
        intonation = self._adapter.predict_intonation(payload.geometry, payload.options, fingering_notes)
        return SimulationResult(
            freq_hz=data.frequencies.tolist(),
            zin_abs=np.abs(data.impedance).tolist(),
            zin_re=data.impedance.real.tolist(),
            zin_im=data.impedance.imag.tolist(),
            intonation=intonation,
            fingering_notes=[item.note for item in intonation],
        )


__all__ = ["SimulationService"]
