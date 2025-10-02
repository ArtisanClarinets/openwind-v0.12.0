"""Simulation orchestration helpers."""

from __future__ import annotations

from typing import Iterable, List

import numpy as np

from .models import SimRequest, SimulationResult

from .openwind_adapter import OpenWInDAdapter


class SimulationService:
    """High-level helper orchestrating impedance computation and post-processing."""

    def __init__(self, adapter: OpenWInDAdapter) -> None:
        self._adapter = adapter

    def run(self, payload: SimRequest) -> SimulationResult:
        fingering_notes = payload.fingering_notes or None
        bundle = self._adapter.run_simulation(payload.geometry, payload.options, fingering_notes)
        return SimulationResult(
            freq_hz=bundle.frequencies.tolist(),
            zin_abs=np.abs(bundle.impedance).tolist(),
            zin_re=bundle.impedance.real.tolist(),
            zin_im=bundle.impedance.imag.tolist(),
            intonation=bundle.intonation,
            fingering_notes=bundle.fingering_notes,
        )


__all__ = ["SimulationService"]
