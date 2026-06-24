"""Unit tests for the packing engine — run with: pytest tests/test_engine.py -v"""

import pytest
from app.models import Piece
from app.engine.packer import optimize


def make_piece(lp, w, h, qty=1, material="MDF", thickness=19, grain_locked=False):
    return Piece(
        lp_number=str(lp),
        name=f"piece_{lp}",
        material=material,
        thickness=thickness,
        width=w,
        length=h,
        quantity=qty,
        grain_locked=grain_locked,
    )


class TestBasicPacking:
    def test_single_small_piece_fits_one_panel(self):
        pieces = [make_piece(1, 500, 500)]
        result = optimize(pieces)
        assert result.total_panels == 1
        assert len(result.panels[0].placed) == 1

    def test_multiple_small_pieces_one_panel(self):
        pieces = [make_piece(i, 400, 300, qty=1) for i in range(6)]
        result = optimize(pieces)
        assert result.total_panels == 1

    def test_quantity_expansion(self):
        pieces = [make_piece(1, 400, 300, qty=10)]
        result = optimize(pieces)
        total_placed = sum(len(p.placed) for p in result.panels)
        assert total_placed == 10

    def test_pieces_never_overlap(self):
        pieces = [make_piece(i, 600, 400, qty=3) for i in range(5)]
        result = optimize(pieces)
        for panel in result.panels:
            for i, a in enumerate(panel.placed):
                for b in panel.placed[i + 1:]:
                    ax2, ay2 = a.x + a.w, a.y + a.h
                    bx2, by2 = b.x + b.w, b.y + b.h
                    overlap = (a.x < bx2 and ax2 > b.x and a.y < by2 and ay2 > b.y)
                    assert not overlap, f"Overlap detected: {a} vs {b}"

    def test_pieces_within_panel_bounds(self):
        pieces = [make_piece(i, 300, 200, qty=2) for i in range(8)]
        result = optimize(pieces)
        w, h = 2800, 2070
        for panel in result.panels:
            for pp in panel.placed:
                assert pp.x >= 0 and pp.y >= 0
                assert pp.x + pp.w <= w
                assert pp.y + pp.h <= h


class TestGrainConstraint:
    def test_grain_locked_pieces_not_rotated(self):
        # Tall narrow piece: grain-locked should stay tall (h > w)
        pieces = [make_piece(1, 200, 2000, qty=3, grain_locked=True)]
        result = optimize(pieces)
        for panel in result.panels:
            for pp in panel.placed:
                assert not pp.rotated, "Grain-locked piece must not be rotated"

    def test_free_pieces_may_rotate(self):
        # Create a situation where rotation clearly helps
        pieces = [make_piece(1, 100, 2000, qty=10, grain_locked=False)]
        result_free = optimize(pieces)

        locked_pieces = [make_piece(1, 100, 2000, qty=10, grain_locked=True)]
        result_locked = optimize(locked_pieces)

        # Free rotation should use fewer or equal panels
        assert result_free.total_panels <= result_locked.total_panels

    def test_mixed_grain_same_panel(self):
        pieces = [
            make_piece(1, 500, 1000, qty=2, grain_locked=True),
            make_piece(2, 400, 300, qty=4, grain_locked=False),
        ]
        result = optimize(pieces)
        for panel in result.panels:
            for pp in panel.placed:
                if pp.piece.grain_locked:
                    assert not pp.rotated


class TestGrouping:
    def test_different_thickness_separate_panels(self):
        pieces = [
            make_piece(1, 600, 400, qty=3, thickness=19),
            make_piece(2, 600, 400, qty=3, thickness=25),
        ]
        result = optimize(pieces)
        thicknesses_per_panel = [
            {pp.piece.thickness for pp in panel.placed}
            for panel in result.panels
        ]
        for t_set in thicknesses_per_panel:
            assert len(t_set) == 1, "Mixed thicknesses on same panel"

    def test_different_material_separate_panels(self):
        pieces = [
            make_piece(1, 600, 400, qty=3, material="MDF", thickness=19),
            make_piece(2, 600, 400, qty=3, material="Chêne", thickness=19),
        ]
        result = optimize(pieces)
        materials_per_panel = [
            {pp.piece.material for pp in panel.placed}
            for panel in result.panels
        ]
        for m_set in materials_per_panel:
            assert len(m_set) == 1, "Mixed materials on same panel"

    def test_waste_ratio_computed(self):
        pieces = [make_piece(1, 500, 500, qty=1)]
        result = optimize(pieces)
        assert 0 <= result.global_waste_ratio <= 100


class TestEdgeCases:
    def test_oversized_piece_handled(self):
        pieces = [make_piece(1, 2790, 2060, qty=1)]
        result = optimize(pieces)
        assert result.total_panels >= 1

    def test_many_tiny_pieces(self):
        pieces = [make_piece(i, 50, 50, qty=5) for i in range(20)]
        result = optimize(pieces)
        total = sum(len(p.placed) for p in result.panels)
        assert total == 100

    def test_empty_input(self):
        result = optimize([])
        assert result.total_panels == 0
        assert result.total_pieces == 0


class TestFreePieceShelfHeight:
    """Régression : une pièce libre étroite et longue doit s'allonger (rotation)
    sur son côté court comme hauteur de shelf, et non ouvrir un shelf surdimensionné
    qui gaspille le panneau (bug FFDH corrigé)."""

    def test_narrow_long_free_pieces_pack_on_single_panel(self):
        # 8 pièces 100×2000 libres sur un panneau 2800×2070.
        # Avant correctif : chacune ouvrait un shelf de ~2000 → 1 pièce/panneau (8 panneaux).
        # Après : rotation côté court (≈103 de haut) → toutes sur 1 panneau.
        pieces = [make_piece(i, 100, 2000, grain_locked=False) for i in range(8)]
        result = optimize(pieces)
        assert result.total_panels == 1
        placed = [pp for p in result.panels for pp in p.placed]
        assert len(placed) == 8

    def test_grain_locked_piece_keeps_long_side_in_x(self):
        # Une pièce verrouillée garde son côté long dans le sens du fil (x).
        result = optimize([make_piece(1, 100, 2000, grain_locked=True)])
        pp = result.panels[0].placed[0]
        assert pp.w >= pp.h  # côté long horizontal
