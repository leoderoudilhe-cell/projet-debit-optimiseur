"""
Shelf (strip) packer for panel-saw cutting.

Why shelves and not MaxRects:
  A panel saw makes full-width horizontal cuts first (producing strips), then
  vertical cuts within each strip. MaxRects can produce "interleaved" layouts
  that require impossible cut sequences on this kind of machine.

  A shelf layout guarantees:
    - One horizontal cut per shelf boundary → cut H1, H2, …
    - One vertical cut per piece within each shelf → cut V1, V2, …
  The layout is a direct cut program that Tom can follow step by step.

Algorithm (First-Fit Decreasing Height):
  1. Sort pieces by height descending (tallest first → better strip utilisation).
  2. For each piece:
     a. Try all existing shelves in order; place in the first that has room.
     b. If none fits, open a new shelf.
  3. Within each shelf pieces are packed left-to-right with kerf between them.

Trade-off: ~5–10% more waste than MaxRects, but layouts are always cuttable
on a panel saw without a non-guillotine move.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ShelfRect:
    x: int
    y: int
    w: int
    h: int
    rotated: bool = False


@dataclass
class _Shelf:
    y: int
    height: int
    bin_w: int
    kerf: int
    current_x: int = 0
    items: list[ShelfRect] = field(default_factory=list)

    @property
    def remaining_w(self) -> int:
        return self.bin_w - self.current_x

    def try_place(self, w: int, h: int, can_rotate: bool) -> Optional[ShelfRect]:
        """
        Try to place a piece in this shelf.
        Returns ShelfRect on success, None otherwise.
        Piece height must fit in the shelf; piece width must fit horizontally.
        """
        for pw, ph, rot in _orientations(w, h, can_rotate):
            if ph <= self.height and pw <= self.remaining_w:
                rect = ShelfRect(x=self.current_x, y=self.y, w=pw, h=ph, rotated=rot)
                self.current_x += pw + self.kerf
                self.items.append(rect)
                return rect
        return None


def _orientations(w: int, h: int, can_rotate: bool):
    yield w, h, False
    if can_rotate and w != h:
        yield h, w, True


class ShelfBin:
    """Single panel bin using the shelf (strip) algorithm."""

    def __init__(self, width: int, height: int, kerf: int = 3):
        self.width = width
        self.height = height
        self.kerf = kerf
        self._shelves: list[_Shelf] = []
        self._next_y: int = 0

    def insert(self, w: int, h: int, can_rotate: bool = True) -> Optional[ShelfRect]:
        # Try fitting in existing shelves first (First-Fit)
        for shelf in self._shelves:
            result = shelf.try_place(w, h, can_rotate)
            if result is not None:
                return result

        # Open a new shelf. Prefer the orientation that MINIMISES the shelf height
        # so a rotatable piece lies on its short side (consistent with the FFDH sort
        # by short side); otherwise a tall free piece opens an oversized shelf and
        # wastes the rest of the panel.
        best: Optional[tuple[int, int, bool]] = None
        for pw, ph, rot in _orientations(w, h, can_rotate):
            if self._next_y + ph <= self.height and pw <= self.width:
                if best is None or ph < best[1]:
                    best = (pw, ph, rot)
        if best is not None:
            pw, ph, rot = best
            new_shelf = _Shelf(
                y=self._next_y,
                height=ph,
                bin_w=self.width,
                kerf=self.kerf,
            )
            self._next_y += ph + self.kerf
            # Place directly with the chosen orientation so the `rotated` flag is exact
            # (try_place re-derives orientation and would lose the rotation here).
            rect = ShelfRect(x=new_shelf.current_x, y=new_shelf.y, w=pw, h=ph, rotated=rot)
            new_shelf.current_x += pw + new_shelf.kerf
            new_shelf.items.append(rect)
            self._shelves.append(new_shelf)
            return rect

        return None

    def occupancy(self) -> float:
        used = sum(r.w * r.h for s in self._shelves for r in s.items)
        return used / (self.width * self.height)

    @property
    def shelf_cuts(self) -> list[int]:
        """Y positions of horizontal shelf cuts (from top, for the PDF)."""
        return [s.y + s.height for s in self._shelves if s.items]
