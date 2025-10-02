"""FastAPI application exposing the OpenWInD Bb clarinet service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import exporters
from .deps import get_optimization_manager, get_simulation_service
from .models import (
    ExportRequest,
    OptRequest,
    RecommendRequest,
    RecommendResponse,
    SimRequest,
)
from .optimize import OptimizationManager
from .recommend import recommend_geometry
from .simulate import SimulationService


API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(title="OpenWInD Bb Clarinet Studio", default_response_class=ORJSONResponse)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"]
    )

    exports_dir = exporters.EXPORT_ROOT
    app.mount("/exports", StaticFiles(directory=str(exports_dir)), name="exports")

    @app.get(f"{API_PREFIX}/health")
    async def health() -> Dict[str, Any]:
        return {"status": "ok", "ts": datetime.utcnow().isoformat()}

    @app.get(f"{API_PREFIX}/presets/bb_clarinet", response_model=RecommendResponse)
    async def presets() -> RecommendResponse:
        payload = RecommendRequest()
        return recommend_geometry(payload)

    @app.post(f"{API_PREFIX}/recommend", response_model=RecommendResponse)
    async def recommend(payload: RecommendRequest) -> RecommendResponse:
        return recommend_geometry(payload)

    @app.post(f"{API_PREFIX}/simulate")
    async def simulate(
        payload: SimRequest,
        service: SimulationService = Depends(get_simulation_service),
    ):
        return service.run(payload)

    @app.post(f"{API_PREFIX}/optimize")
    async def optimize(
        payload: OptRequest,
        manager: OptimizationManager = Depends(get_optimization_manager),
    ):
        return manager.start_job(payload)

    @app.get(f"{API_PREFIX}/optimize/result/{{job_id}}")
    async def optimization_result(job_id: str, manager: OptimizationManager = Depends(get_optimization_manager)):
        result = manager.to_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Unknown job")
        return result

    @app.get(f"{API_PREFIX}/optimize/stream")
    async def optimization_stream(job_id: str, manager: OptimizationManager = Depends(get_optimization_manager)):
        events = manager.consume_events(job_id)
        return StreamingResponse((f"data: {event}\n\n" for event in events), media_type="text/event-stream")

    @app.post(f"{API_PREFIX}/export/{{fmt}}")
    async def export_geometry(fmt: str, payload: ExportRequest) -> Dict[str, Any]:
        fmt = fmt.lower()
        if fmt not in exporters.EXPORTERS:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        path = exporters.EXPORTERS[fmt](payload.geometry, payload.metadata)
        return {"path": str(path.relative_to(exporters.EXPORT_ROOT.parent))}

    return app


app = create_app()
