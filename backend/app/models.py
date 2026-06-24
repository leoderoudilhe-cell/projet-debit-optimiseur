from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Piece:
    lp_number: str
    name: str
    material: str
    thickness: int
    width: int
    length: int
    quantity: int
    grain_locked: bool = False


@dataclass
class PlacedPiece:
    piece: Piece
    instance_index: int
    x: int
    y: int
    w: int
    h: int
    rotated: bool = False


@dataclass
class Panel:
    panel_index: int
    material: str
    thickness: int
    width: int
    height: int
    placed: list[PlacedPiece] = field(default_factory=list)
    shelf_cuts: list[int] = field(default_factory=list)  # y-positions of horizontal cuts

    @property
    def used_area(self) -> float:
        return sum(p.w * p.h for p in self.placed)

    @property
    def total_area(self) -> float:
        return self.width * self.height

    @property
    def waste_ratio(self) -> float:
        return (1 - self.used_area / self.total_area) * 100


@dataclass
class OptimizeResult:
    panels: list[Panel]
    total_panels: int
    total_pieces: int
    global_waste_ratio: float
    materials_count: int
    consumed_area_m2: float
