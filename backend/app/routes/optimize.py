import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, ExportHistory
from app.engine.packer import optimize
from app.models import Piece
from app.parser.cadwork_csv import parse_cadwork_csv
from app.config import settings

router = APIRouter(prefix="/api")


def _read_raw(file, paste) -> bytes:
    if file and file.filename:
        return None  # will be awaited by caller
    if paste:
        return paste.encode("utf-8")
    return None


def _apply_grain_overrides(pieces: list[Piece], overrides: dict[str, bool]) -> list[Piece]:
    """Apply manual grain overrides keyed by material name."""
    if not overrides:
        return pieces
    for piece in pieces:
        if piece.material in overrides:
            piece.grain_locked = overrides[piece.material]
    return pieces


@router.post("/parse")
async def parse_only(
    file: UploadFile | None = None,
    paste: str | None = Form(None),
):
    """
    Parse a Cadwork CSV and return the list of unique materials with
    auto-detected grain status. The frontend uses this to show a
    per-material confirmation step before running the optimisation.
    """
    if file and file.filename:
        raw = await file.read()
    elif paste:
        raw = paste.encode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="No input provided")

    pieces = parse_cadwork_csv(raw)
    if not pieces:
        raise HTTPException(status_code=422, detail="No valid pieces found in input")

    # Aggregate by material
    by_material: dict[str, dict] = {}
    for p in pieces:
        if p.material not in by_material:
            by_material[p.material] = {
                "material": p.material,
                "grain_locked": p.grain_locked,
                "piece_count": 0,
                "thicknesses": set(),
            }
        by_material[p.material]["piece_count"] += p.quantity
        by_material[p.material]["thicknesses"].add(p.thickness)

    return {
        "piece_count": sum(p.quantity for p in pieces),
        "materials": [
            {
                "material": v["material"],
                "grain_locked": v["grain_locked"],
                "piece_count": v["piece_count"],
                "thicknesses": sorted(v["thicknesses"]),
            }
            for v in by_material.values()
        ],
        # Store the raw CSV as base64 so the frontend can send it back in /optimize
        # without re-uploading the file (avoids a second file upload round-trip)
        "raw_b64": __import__("base64").b64encode(raw).decode(),
    }


@router.post("/optimize")
async def run_optimize(
    file: UploadFile | None = None,
    paste: str | None = Form(None),
    raw_b64: str | None = Form(None),
    grain_overrides: str | None = Form(None),   # JSON string: {"Chêne massif": true, …}
    project_name: str | None = Form(None),
    panel_width: int | None = Form(None),
    panel_height: int | None = Form(None),
    kerf: int | None = Form(None),
    border_margin: int | None = Form(None),
    db: Session = Depends(get_db),
):
    # Priority: raw_b64 (from parse step) > file > paste
    if raw_b64:
        import base64
        raw = base64.b64decode(raw_b64)
    elif file and file.filename:
        raw = await file.read()
    elif paste:
        raw = paste.encode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="No input provided")

    # Validation des paramètres panneau (sans muter le singleton global settings).
    p_w = panel_width if panel_width is not None else settings.panel_width
    p_h = panel_height if panel_height is not None else settings.panel_height
    p_kerf = kerf if kerf is not None else settings.kerf
    p_margin = border_margin if border_margin is not None else settings.border_margin
    if p_w <= 0 or p_h <= 0 or p_kerf < 0 or p_margin < 0:
        raise HTTPException(status_code=422, detail="Paramètres panneau invalides (doivent être positifs)")
    if 2 * p_margin >= p_w or 2 * p_margin >= p_h:
        raise HTTPException(status_code=422, detail="Marge trop grande par rapport à la taille du panneau")

    pieces = parse_cadwork_csv(raw)
    if not pieces:
        raise HTTPException(status_code=422, detail="No valid pieces found in input")

    overrides: dict[str, bool] = {}
    if grain_overrides:
        try:
            overrides = json.loads(grain_overrides)
        except json.JSONDecodeError:
            pass

    pieces = _apply_grain_overrides(pieces, overrides)
    result = optimize(pieces, panel_w=p_w, panel_h=p_h, kerf=p_kerf, margin=p_margin)

    from app.pdf.recap import generate_recap_pdf
    from app.pdf.layout import generate_layout_pdf

    storage = Path(settings.storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex[:8]
    recap_path = storage / f"{uid}_recap.pdf"
    layout_path = storage / f"{uid}_layout.pdf"

    project_label = project_name or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    generate_recap_pdf(result, pieces, project_label, str(recap_path))
    generate_layout_pdf(result, project_label, str(layout_path))

    summary = {
        "total_panels": result.total_panels,
        "total_pieces": result.total_pieces,
        "global_waste_ratio": result.global_waste_ratio,
        "materials_count": result.materials_count,
        "consumed_area_m2": result.consumed_area_m2,
    }

    entry = ExportHistory(
        project_name=project_name,
        pdf_recap_path=str(recap_path),
        pdf_layout_path=str(layout_path),
        total_panels=result.total_panels,
        waste_ratio=int(result.global_waste_ratio),
        summary_json=json.dumps(summary),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "export_id": entry.id,
        "project_name": project_label,
        **summary,
    }


@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    entries = db.query(ExportHistory).order_by(ExportHistory.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "project_name": e.project_name,
            "created_at": e.created_at.isoformat(),
            "total_panels": e.total_panels,
            "waste_ratio": e.waste_ratio,
        }
        for e in entries
    ]


@router.get("/history/{export_id}/recap")
def download_recap(export_id: int, db: Session = Depends(get_db)):
    entry = db.query(ExportHistory).filter(ExportHistory.id == export_id).first()
    if not entry or not Path(entry.pdf_recap_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(entry.pdf_recap_path, media_type="application/pdf",
                        filename=f"recap_{export_id}.pdf")


@router.get("/history/{export_id}/layout")
def download_layout(export_id: int, db: Session = Depends(get_db)):
    entry = db.query(ExportHistory).filter(ExportHistory.id == export_id).first()
    if not entry or not Path(entry.pdf_layout_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(entry.pdf_layout_path, media_type="application/pdf",
                        filename=f"layout_{export_id}.pdf")
