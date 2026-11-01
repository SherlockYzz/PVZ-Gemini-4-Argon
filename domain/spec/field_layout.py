# -*- coding: utf-8 -*-
"""Field layout domain value object.
Unifies all grid metrics for Land and Pool environments into an immutable specification,
completely eliminating coordinate drift and multi-standard inconsistencies.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class FieldLayout:
    cols: int
    rows: int
    cell_w: int
    cell_h: int
    origin_x: int
    origin_y: int
    row_centers: Tuple[int, ...]
    row_grounds: Tuple[int, ...]
    row_bounds: Tuple[Tuple[int, int], ...]
    pool_rows: frozenset[int] = frozenset()
    is_pool: bool = False

    def center(self, col: int, row: int) -> Tuple[int, int]:
        """Compute the logical center of the given grid cell."""
        c = max(0, min(self.cols - 1, col))
        r = max(0, min(self.rows - 1, row))
        cx = self.origin_x + int((c + 0.5) * self.cell_w)
        cy = self.row_centers[r]
        return (cx, cy)

    def ground_y(self, row: int) -> int:
        """The authoritative baseline ground height for the given lane."""
        r = max(0, min(self.rows - 1, row))
        return self.row_grounds[r]

    def cell_rect(self, col: int, row: int) -> Tuple[int, int, int, int]:
        """Return (x, y, width, height) of the cell boundary."""
        c = max(0, min(self.cols - 1, col))
        r = max(0, min(self.rows - 1, row))
        gx = self.origin_x + c * self.cell_w
        top_y, bot_y = self.row_bounds[r]
        return (gx, top_y, self.cell_w, bot_y - top_y)

    def is_water(self, row: int) -> bool:
        """Whether the specified row is water surface."""
        return row in self.pool_rows

    def is_water_tile(self, col: int, row: int) -> bool:
        """Whether the specified grid tile is on water."""
        return self.is_water(row)

    @property
    def grid_x(self) -> int:
        return self.origin_x

    @property
    def grid_y(self) -> int:
        return self.origin_y

    @property
    def grid_w(self) -> int:
        return self.cols * self.cell_w

    @property
    def grid_right(self) -> int:
        return self.origin_x + self.cols * self.cell_w

    def get_cell_center(self, col: int, row: int) -> Tuple[int, int]:
        return self.center(col, row)

    def get_row_center_y(self, row: int) -> int:
        r = max(0, min(self.rows - 1, row))
        return self.row_centers[r]

    def get_row_ground_y(self, row: int) -> int:
        return self.ground_y(row)

    def get_cell_rect(self, col: int, row: int) -> Tuple[int, int, int, int]:
        return self.cell_rect(col, row)

    def pos_to_cell(self, x: float, y: float) -> Tuple[Optional[int], Optional[int]]:
        """Invert screen coordinates back to (col, row). Always returns a 2-tuple (col, row) or (None, None).
        Guarantees that tuple unpacking `col, row = pos_to_cell(...)` NEVER raises TypeError.
        """
        cell = self.cell_at(x, y)
        if cell is None:
            return (None, None)
        return cell

    def cell_at(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """Invert screen coordinates back to (col, row). Returns None if out of bounds."""
        grid_right = self.origin_x + self.cols * self.cell_w
        if not (self.origin_x <= x < grid_right):
            return None
        col = int((x - self.origin_x) // self.cell_w)
        for r, (top_y, bot_y) in enumerate(self.row_bounds):
            if top_y <= y < bot_y:
                return (col, r)
        return None

    def is_playable(self, x: float, y: float) -> bool:
        """Whether the coordinate is inside the playable lawn/pool area."""
        return self.cell_at(x, y) is not None


# Authoritative Layout Instances
# 1. Standard Daytime & Night Land Layout (5 rows, 9 columns)
LAND_ROW_CENTERS = tuple(124 + int((r + 0.5) * 116) for r in range(5))
LAND_ROW_GROUNDS = tuple(124 + (r + 1) * 116 - 13 for r in range(5))
LAND_ROW_BOUNDS = tuple((124 + r * 116, 124 + (r + 1) * 116) for r in range(5))

LAND_LAYOUT = FieldLayout(
    cols=9,
    rows=5,
    cell_w=111,
    cell_h=116,
    origin_x=70,
    origin_y=124,
    row_centers=LAND_ROW_CENTERS,
    row_grounds=LAND_ROW_GROUNDS,
    row_bounds=LAND_ROW_BOUNDS,
    pool_rows=frozenset(),
    is_pool=False,
)

# 2. Authentic Pool Layout (6 rows: row 2 & 3 are water, custom aligned with authentic background)
POOL_ROW_CENTERS = (155, 265, 406, 498, 615, 705)
POOL_LANE_GROUNDS = (190, 300, 435, 528, 645, 735)
POOL_ROW_BOUNDS = (
    (95, 210),
    (210, 335),
    (335, 452),
    (452, 560),
    (560, 660),
    (660, 755),
)

POOL_LAYOUT = FieldLayout(
    cols=9,
    rows=6,
    cell_w=80,
    cell_h=96,
    origin_x=140,
    origin_y=95,
    row_centers=POOL_ROW_CENTERS,
    row_grounds=POOL_LANE_GROUNDS,
    row_bounds=POOL_ROW_BOUNDS,
    pool_rows=frozenset({2, 3}),
    is_pool=True,
)
