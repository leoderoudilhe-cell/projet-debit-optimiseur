"""Tests du rendu PDF des plans : légende des petites pièces + axe Y inversé."""
import os

from app.models import Piece, PlacedPiece, Panel, OptimizeResult
from app.pdf.layout import _legend_for_panel, PanelFlowable, generate_layout_pdf, MIN_FONT_PT


def _piece(lp, w, h, grain=False):
    return Piece(lp_number=str(lp), name=f"p{lp}", material="MDF",
                 thickness=19, width=w, length=h, quantity=1, grain_locked=grain)


def _panel():
    p = Panel(panel_index=0, material="MDF", thickness=19, width=2800, height=2070)
    p.placed = [
        PlacedPiece(piece=_piece(100, 800, 600), instance_index=0, x=5, y=5, w=800, h=600),
        PlacedPiece(piece=_piece(520, 30, 30), instance_index=0, x=900, y=5, w=30, h=30),
        PlacedPiece(piece=_piece(603, 25, 40), instance_index=0, x=940, y=5, w=25, h=40),
    ]
    p.shelf_cuts = [610, 1200]
    return p


def test_legend_captures_only_small_pieces():
    # À cette échelle, la grosse pièce affiche ses cotes ; les deux petites non.
    legend = _legend_for_panel(_panel(), scale=0.3)
    assert "100" not in legend            # grosse pièce : cotes dans le rectangle
    assert legend.get("520") == "30×30"   # bug corrigé : petite pièce → légende
    assert legend.get("603") == "25×40"


def test_flip_y_first_shelf_on_top():
    panel = _panel()
    fl = PanelFlowable(panel, scale=0.3, draw_w=2800 * 0.3, draw_h=2070 * 0.3)
    # Une pièce en bas côté moteur (y=5) doit être rendue en HAUT (y proche de draw_h).
    y_top = fl._flip_y(5, 600)
    assert y_top > fl.draw_h / 2          # rendue dans la moitié haute
    # ... et rester dans les limites du panneau dessiné.
    assert 0 <= y_top <= fl.draw_h


def test_layout_pdf_generated(tmp_path):
    result = OptimizeResult(panels=[_panel()], total_panels=1, total_pieces=3,
                            global_waste_ratio=20.0, materials_count=1, consumed_area_m2=1.0)
    out = tmp_path / "layout.pdf"
    generate_layout_pdf(result, "Test", str(out))
    assert out.exists() and out.read_bytes()[:4] == b"%PDF"
