"""
Cutting optimization engine — shelf (strip) based.

Uses ShelfBin (shelf.py) to guarantee panel-saw-compatible layouts:
  - Every shelf boundary = one horizontal cut
  - Every piece boundary within a shelf = one vertical cut
  - Tom gets a numbered cut sequence directly from the PDF

Grain constraint: grain-locked pieces always have their long side in x
(panel grain direction). Free pieces may rotate to better fill a shelf.

Grouping: pieces with different (thickness, material) are never mixed on
the same panel — each group is optimized independently.
"""

from __future__ import annotations

from collections import defaultdict

from app.config import settings
from app.engine.shelf import ShelfBin, ShelfRect
from app.models import Piece, PlacedPiece, Panel, OptimizeResult


def _expand(pieces: list[Piece]) -> list[tuple[Piece, int]]:
    instances = []
    for piece in pieces:
        for i in range(piece.quantity):
            instances.append((piece, i))
    return instances


def _sort_key(item: tuple[Piece, int]) -> int:
    piece = item[0]
    # For sorting: use the height that will actually be placed in the shelf
    # (short side for grain-locked, min for free)
    if piece.grain_locked:
        return min(piece.width, piece.length)
    return min(piece.width, piece.length)


def _pack_group(
    instances: list[tuple[Piece, int]],
    panel_w: int,
    panel_h: int,
    kerf: int,
    margin: int,
    material: str,
    thickness: int,
    panel_index_start: int,
) -> list[Panel]:
    eff_w = panel_w - 2 * margin
    eff_h = panel_h - 2 * margin

    # Sort tallest first so shelves pack well (FFDH heuristic)
    def placed_height(item: tuple[Piece, int]) -> int:
        p = item[0]
        if p.grain_locked:
            return min(p.width, p.length)   # short side = shelf height
        return min(p.width, p.length)        # same for free (rotate taller → shorter)

    instances = sorted(instances, key=placed_height, reverse=True)

    panels: list[Panel] = []
    remaining = list(instances)

    while remaining:
        panel = Panel(
            panel_index=panel_index_start + len(panels),
            material=material,
            thickness=thickness,
            width=panel_w,
            height=panel_h,
        )
        panels.append(panel)
        bin_ = ShelfBin(eff_w, eff_h, kerf=kerf)
        still_remaining: list[tuple[Piece, int]] = []

        for piece, idx in remaining:
            if piece.grain_locked:
                # Long side → x (grain direction), short side → y (shelf height)
                long_s = max(piece.width, piece.length)
                short_s = min(piece.width, piece.length)
                result = bin_.insert(long_s + kerf, short_s + kerf, can_rotate=False)
                placed_w = long_s
                placed_h = short_s
            else:
                result = bin_.insert(piece.width + kerf, piece.length + kerf, can_rotate=True)
                if result is not None:
                    if result.rotated:
                        placed_w = piece.length
                        placed_h = piece.width
                    else:
                        placed_w = piece.width
                        placed_h = piece.length

            if result is None:
                still_remaining.append((piece, idx))
                continue

            panel.placed.append(PlacedPiece(
                piece=piece,
                instance_index=idx,
                x=result.x + margin,
                y=result.y + margin,
                w=placed_w,
                h=placed_h,
                rotated=result.rotated,
            ))

        # Safety: if nothing was placed (single oversized piece), force-place first
        if not panel.placed and remaining:
            piece, idx = remaining[0]
            long_s = max(piece.width, piece.length) if piece.grain_locked else piece.width
            short_s = min(piece.width, piece.length) if piece.grain_locked else piece.length
            panel.placed.append(PlacedPiece(
                piece=piece,
                instance_index=idx,
                x=margin,
                y=margin,
                w=min(long_s, eff_w),
                h=min(short_s, eff_h),
                rotated=False,
            ))
            still_remaining = remaining[1:]

        # Store shelf cut positions on the panel for PDF rendering
        panel.shelf_cuts = [c + margin for c in bin_.shelf_cuts]
        remaining = still_remaining

    return panels


def optimize(
    pieces: list[Piece],
    panel_w: int | None = None,
    panel_h: int | None = None,
    kerf: int | None = None,
    margin: int | None = None,
) -> OptimizeResult:
    if not pieces:
        return OptimizeResult(
            panels=[],
            total_panels=0,
            total_pieces=0,
            global_waste_ratio=0.0,
            materials_count=0,
            consumed_area_m2=0.0,
        )

    groups: dict[tuple[int, str], list[Piece]] = defaultdict(list)
    for piece in pieces:
        groups[(piece.thickness, piece.material)].append(piece)

    # Paramètres passés explicitement (sinon valeurs par défaut de settings).
    # On NE mute plus le singleton global → pas de fuite entre requêtes concurrentes.
    panel_w = settings.panel_width if panel_w is None else panel_w
    panel_h = settings.panel_height if panel_h is None else panel_h
    kerf = settings.kerf if kerf is None else kerf
    margin = settings.border_margin if margin is None else margin

    all_panels: list[Panel] = []
    for (thickness, material), group_pieces in sorted(groups.items()):
        instances = _expand(group_pieces)
        panels = _pack_group(
            instances=instances,
            panel_w=panel_w,
            panel_h=panel_h,
            kerf=kerf,
            margin=margin,
            material=material,
            thickness=thickness,
            panel_index_start=len(all_panels),
        )
        all_panels.extend(panels)

    total_pieces = sum(p.quantity for p in pieces)
    total_area = sum(pan.total_area for pan in all_panels)
    used_area = sum(pan.used_area for pan in all_panels)
    global_waste = (1 - used_area / total_area) * 100 if total_area > 0 else 0.0
    consumed_m2 = total_area / 1_000_000

    return OptimizeResult(
        panels=all_panels,
        total_panels=len(all_panels),
        total_pieces=total_pieces,
        global_waste_ratio=round(global_waste, 1),
        materials_count=len(groups),
        consumed_area_m2=round(consumed_m2, 2),
    )
