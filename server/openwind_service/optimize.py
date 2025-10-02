# -*- coding: utf-8 -*-
"""Simplified optimization manager for clarinet geometries."""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from queue import Queue, Empty
from typing import Dict, Iterable, List, Optional

import numpy as np

from .models import (
    Geometry,
    OptRequest,
    OptimizeResult,
    OptimizeResponse,
    SimulationOptions,
    ToneHole,
)
from .openwind_adapter import OpenWInDAdapter


@dataclass
class OptimizationJob:
    job_id: str
    status: str = "running"
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    history: List[Dict[str, float]] = field(default_factory=list)
    convergence: List[float] = field(default_factory=list)
    result_geometry: Optional[Geometry] = None
    sensitivity: List[Dict[str, float]] = field(default_factory=list)
    events: Queue = field(default_factory=Queue)


class OptimizationManager:
    """Manage asynchronous optimization jobs with streaming updates."""

    def __init__(self, adapter: OpenWInDAdapter) -> None:
        self._adapter = adapter
        self._jobs: Dict[str, OptimizationJob] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start_job(self, payload: OptRequest) -> OptimizeResponse:
        job_id = uuid.uuid4().hex
        job = OptimizationJob(job_id=job_id)
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(target=self._run_job, args=(job, payload), daemon=True)
        thread.start()

        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(job.created_at))
        return OptimizeResponse(job_id=job_id, status=job.status, created_at=created)

    def get_job(self, job_id: str) -> Optional[OptimizationJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def consume_events(self, job_id: str) -> Iterable[str]:
        job = self.get_job(job_id)
        if not job:
            yield json.dumps({"error": "unknown job"})
            return
        while True:
            try:
                event = job.events.get(timeout=1.0)
            except Empty:
                if job.status in {"completed", "failed"}:
                    break
                continue
            yield json.dumps(event)
            if event.get("msg") == "done":
                break

    def to_result(self, job_id: str) -> Optional[OptimizeResult]:
        job = self.get_job(job_id)
        if not job or job.result_geometry is None:
            return None
        completed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(job.completed_at or time.time()))
        return OptimizeResult(
            job_id=job.job_id,
            status=job.status,
            geometry=job.result_geometry,
            convergence=job.convergence,
            history=job.history,
            sensitivity=getattr(job, "sensitivity", []),
            completed_at=completed,
        )

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------
    def _run_job(self, job: OptimizationJob, payload: OptRequest) -> None:
        # RNG and inputs
        rng = np.random.default_rng(getattr(payload, "seed", None))
        bounds = getattr(payload, "bounds", None)
        sim_options: SimulationOptions = getattr(payload, "simulation", None) or SimulationOptions()
        objective = getattr(payload, "objective", None)
        fingering_notes: Optional[Iterable[str]] = getattr(payload, "fingering_notes", None)

        # Bounds defaults (robust to missing fields)
        hole_pos_delta = float(getattr(bounds, "hole_position_delta_mm", 1.0))  # mm
        hole_diam_delta = float(getattr(bounds, "hole_diameter_delta_mm", 0.5))  # mm
        bore_delta_mm = float(getattr(bounds, "bore_delta_mm", 0.1))  # mm

        def mutate(base: Geometry, iteration: int) -> Geometry:
            """Noisy mutate with spacing guard and positive diameter floor."""
            factor = max(0.1, 1.0 / (1.0 + iteration * 0.5))

            # Spacing guard
            min_spacing = float(getattr(base.metadata or {}, "min_spacing_mm", 6.0))

            # Sort holes by axial position and enforce spacing + bounds
            holes: List[ToneHole] = []
            previous = 0.0
            for original in sorted(base.tone_holes, key=lambda h: (h.axial_pos_mm, h.index)):
                delta_pos = rng.normal(0.0, hole_pos_delta * factor)
                delta_d = rng.normal(0.0, hole_diam_delta * factor)

                # Axial position with spacing and within body length
                axial = max(original.axial_pos_mm + delta_pos, previous + min_spacing)
                axial = min(axial, base.length_mm - min_spacing)
                axial = max(axial, previous + min_spacing)  # re-apply after upper clamp

                # Diameter with hard floor
                diameter = max(original.diameter_mm + delta_d, 3.5)

                holes.append(
                    ToneHole(
                        index=original.index,
                        axial_pos_mm=axial,
                        diameter_mm=diameter,
                        chimney_mm=original.chimney_mm,
                        closed=original.closed,
                    )
                )
                previous = axial

            # Bore mutation with floor
            bore = max(base.bore_mm + rng.normal(0.0, bore_delta_mm * factor), 12.0)

            return Geometry(
                bore_mm=bore,
                length_mm=base.length_mm,
                barrel_length_mm=base.barrel_length_mm,
                mouthpiece_params=base.mouthpiece_params,
                tone_holes=holes,
                metadata=base.metadata,
            )

        def callback(iteration: int, score: float, geom: Geometry, metrics: Dict[str, float]) -> None:
            record = {"iteration": iteration, "score": score, **metrics}
            job.history.append(record)
            job.convergence.append(metrics.get("score", score))
            pct = min(99, int(100 * iteration / max(1, getattr(payload, "max_iter", 1))))
            job.events.put({"pct": pct, "msg": f"Iteration {iteration}: score={score:.3f}", **metrics})

        try:
            best_geom, convergence, sensitivity, history = self._adapter.optimise_geometry(
                payload.geometry,
                sim_options,
                objective,
                getattr(payload, "max_iter", 1),
                mutate,
                callback,
                fingering_notes,
            )
            job.result_geometry = best_geom
            job.convergence = convergence
            job.history = history
            job.sensitivity = sensitivity
            job.status = "completed"
        except Exception as exc:  # pragma: no cover
            job.status = "failed"
            job.events.put({"pct": 100, "msg": f"Failed: {exc}"})
        finally:
            job.completed_at = time.time()
            job.events.put({"pct": 100, "msg": "done"})


__all__ = ["OptimizationManager"]
