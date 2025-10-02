"""Geometry export helpers."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import HTTPException

from .models import Geometry

EXPORT_ROOT = Path(__file__).resolve().parent.parent / "exports"
EXPORT_ROOT.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def export_json(geometry: Geometry, metadata: dict | None = None) -> Path:
    payload = geometry.model_dump(mode="json")
    if metadata:
        payload["metadata"] = {**geometry.metadata, **metadata}
    path = EXPORT_ROOT / f"clarinet-geometry-{_timestamp()}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def export_csv(geometry: Geometry) -> Path:
    path = EXPORT_ROOT / f"clarinet-geometry-{_timestamp()}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "axial_pos_mm", "diameter_mm", "chimney_mm", "closed"])
        for hole in geometry.tone_holes:
            writer.writerow([hole.index, hole.axial_pos_mm, hole.diameter_mm, hole.chimney_mm, int(hole.closed)])
    return path


def export_dxf(geometry: Geometry) -> Path:
    path = EXPORT_ROOT / f"clarinet-geometry-{_timestamp()}.dxf"
    content = [
        "0", "SECTION", "2", "ENTITIES",
    ]
    length_m = geometry.length_mm / 1000.0
    content.extend(["0", "LINE", "8", "CENTER", "10", "0", "20", "0", "30", "0", "11", str(length_m), "21", "0", "31", "0"])
    for hole in geometry.tone_holes:
        x = hole.axial_pos_mm / 1000.0
        r = hole.diameter_mm / 2000.0
        content.extend(["0", "CIRCLE", "8", "HOLES", "10", str(x), "20", "0", "30", "0", "40", str(r)])
    content.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(content))
    return path


def export_step(geometry: Geometry) -> Path:
    try:
        import cadquery as cq  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=501, detail="CadQuery not available. Install cadquery to enable STEP export.") from exc

    length = geometry.length_mm / 1000.0
    bore_radius = geometry.bore_mm / 2000.0
    workplane = cq.Workplane("XY").circle(bore_radius).extrude(length)
    model = workplane
    path = EXPORT_ROOT / f"clarinet-geometry-{_timestamp()}.step"
    cq.exporters.export(model, str(path))
    return path


EXPORTERS: dict[str, Callable[..., Path]] = {
    "json": export_json,
    "csv": export_csv,
    "dxf": export_dxf,
    "step": export_step,
}


__all__ = ["export_json", "export_csv", "export_dxf", "export_step", "EXPORTERS"]
