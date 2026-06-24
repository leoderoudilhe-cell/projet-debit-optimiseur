"""
MaxRects-BSSF (Best Short Side Fit) bin-packing algorithm with per-rectangle
rotation control. Ported and extended from juj/RectangleBinPack (C++, public domain).

Key difference from off-the-shelf libs: every rectangle carries its own
`can_rotate` flag, so grain-locked pieces are never rotated while free pieces
can be rotated to improve packing — all within a single pass on one bin.

Algorithm: MaxRects-BSSF
  - Maintains a list of maximal free rectangles (Free Rectangle Maximality property)
  - On each insertion, picks the rectangle that minimises the shorter leftover side
  - After insertion, splits and prunes the free rectangle list
  - Gives ~88-95% occupancy on heterogeneous inputs (Jylänki 2010 benchmarks)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Rect:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    @property
    def area(self) -> int:
        return self.w * self.h

    def fits_in(self, aw: int, ah: int) -> bool:
        return self.w <= aw and self.h <= ah

    def __repr__(self) -> str:
        return f"Rect({self.x},{self.y} {self.w}×{self.h})"


@dataclass
class PlacementResult:
    rect: Rect
    rotated: bool


class MaxRectsBin:
    """
    A single bin using the MaxRects algorithm with BSSF placement heuristic.
    Accepts per-piece rotation control via the `can_rotate` argument.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._free: list[Rect] = [Rect(0, 0, width, height)]
        self._placed: list[Rect] = []

    # ── Public API ──────────────────────────────────────────────────────────

    def insert(self, w: int, h: int, can_rotate: bool = True) -> Optional[PlacementResult]:
        """Try to place a rectangle of size w×h. Returns placement or None."""
        best = self._find_bssf(w, h, can_rotate)
        if best is None:
            return None
        placed = Rect(best.rect.x, best.rect.y, best.w, best.h)
        self._place(placed)
        return PlacementResult(rect=placed, rotated=best.rotated)

    def occupancy(self) -> float:
        used = sum(r.area for r in self._placed)
        return used / (self.width * self.height)

    # ── Internal ─────────────────────────────────────────────────────────────

    @dataclass
    class _Candidate:
        rect: Rect      # free rect chosen
        w: int          # placed width
        h: int          # placed height
        rotated: bool
        score: int      # lower = better (shorter leftover side)

    def _find_bssf(self, w: int, h: int, can_rotate: bool) -> Optional[_Candidate]:
        best: Optional[MaxRectsBin._Candidate] = None
        for free in self._free:
            for (pw, ph, rot) in self._orientations(w, h, can_rotate):
                if pw <= free.w and ph <= free.h:
                    score = min(free.w - pw, free.h - ph)
                    if best is None or score < best.score:
                        best = MaxRectsBin._Candidate(free, pw, ph, rot, score)
        return best

    @staticmethod
    def _orientations(w: int, h: int, can_rotate: bool):
        yield w, h, False
        if can_rotate and w != h:
            yield h, w, True

    def _place(self, placed: Rect):
        new_free: list[Rect] = []
        for free in self._free:
            if _intersects(placed, free):
                new_free.extend(_split(free, placed))
            else:
                new_free.append(free)
        self._free = _prune(new_free)
        self._placed.append(placed)


# ── Geometry helpers ────────────────────────────────────────────────────────

def _intersects(a: Rect, b: Rect) -> bool:
    return (a.x < b.x + b.w and a.x + a.w > b.x and
            a.y < b.y + b.h and a.y + a.h > b.y)


def _split(free: Rect, placed: Rect) -> list[Rect]:
    """Split a free rect around a placed rect — up to 4 sub-rects."""
    result: list[Rect] = []
    if placed.x > free.x:
        result.append(Rect(free.x, free.y, placed.x - free.x, free.h))
    if placed.x + placed.w < free.x + free.w:
        result.append(Rect(placed.x + placed.w, free.y, free.x + free.w - placed.x - placed.w, free.h))
    if placed.y > free.y:
        result.append(Rect(free.x, free.y, free.w, placed.y - free.y))
    if placed.y + placed.h < free.y + free.h:
        result.append(Rect(free.x, placed.y + placed.h, free.w, free.y + free.h - placed.y - placed.h))
    return result


def _prune(rects: list[Rect]) -> list[Rect]:
    """Remove any rect fully contained within another (maximality property)."""
    result: list[Rect] = []
    for i, a in enumerate(rects):
        dominated = False
        for j, b in enumerate(rects):
            if i != j and _contains(b, a):
                dominated = True
                break
        if not dominated:
            result.append(a)
    return result


def _contains(outer: Rect, inner: Rect) -> bool:
    return (outer.x <= inner.x and outer.y <= inner.y and
            outer.x + outer.w >= inner.x + inner.w and
            outer.y + outer.h >= inner.y + inner.h)
