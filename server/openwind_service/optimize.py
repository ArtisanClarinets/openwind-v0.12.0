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

    def start_job(self, payload: OptRequest) -> OptimizeResponse:
        job_id = uuid.uuid4().hex
        job = OptimizationJob(job_id=job_id)
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(target=self._run_job, args=(job, payload), daemon=True)
        thread.start()
        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(job.created_at))
        return OptimizeResponse(job_id=job_id, status=job.status, created_at=created)

    def _run_job(self, job: OptimizationJob, payload: OptRequest) -> None:
        rng = np.random.default_rng(payload.seed)
        bounds = payload.bounds
        sim_options = payload.simulation
        objective = payload.objective
        fingering_notes = payload.fingering_notes or None

        def mutate(base: Geometry, iteration: int) -> Geometry:
            factor = max(0.1, 1.0 / (1.0 + iteration * 0.5))
            holes = []
            min_spacing = float(base.metadata.get("min_spacing_mm", 6.0))
            previous = 0.0
            for original in sorted(base.tone_holes, key=lambda h: (h.axial_pos_mm, h.index)):
                delta_pos = rng.normal(0.0, bounds.hole_position_delta_mm * factor)
                delta_d = rng.normal(0.0, bounds.hole_diameter_delta_mm * factor)
                axial = max(original.axial_pos_mm + delta_pos, previous + min_spacing)
                axial = min(axial, base.length_mm - min_spacing)
                axial = max(axial, previous + min_spacing)
                diameter = max(original.diameter_mm + delta_d, 3.5)
                new_hole = ToneHole(
                    index=original.index,
                    axial_pos_mm=axial,
                    diameter_mm=diameter,
                    chimney_mm=original.chimney_mm,
                    closed=original.closed,
                )
                previous = axial
                holes.append(new_hole)
            bore_delta = rng.normal(0.0, bounds.bore_delta_mm * factor)
            return Geometry(
                bore_mm=max(base.bore_mm + bore_delta, 12.0),
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
            pct = min(99, int(100 * iteration / payload.max_iter))
            job.events.put({"pct": pct, "msg": f"Iteration {iteration}: score={score:.3f}", **metrics})

        try:
            best_geom, convergence, sensitivity, history = self._adapter.optimise_geometry(
                payload.geometry,
                sim_options,
                objective,
                payload.max_iter,
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


__all__ = ["OptimizationManager"]
