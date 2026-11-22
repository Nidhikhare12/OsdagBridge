"""
Pile — Placement Geometry (pure Python)
=======================================

Pile-position mathematics for the pile group below a cap.
Shared by the pythonOCC builder and the IFC extractor so both produce
identical geometry.

Units: mm. Pile positions are offsets from the GROUP CENTRE; callers add
the global (x_center, y_center) of the pile group.
"""

import math


def _axis_offsets(count: int, spacing: float) -> list:
    """Symmetric offsets of ``count`` points along one axis.

    2 -> [-s/2, +s/2];  3 -> [-s, 0, +s];  ... always centred on 0.
    """
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    total = (count - 1) * spacing
    return [-total / 2.0 + i * spacing for i in range(count)]


def pile_positions(n_piles_x: int, n_piles_y: int,
                   spacing_x: float, spacing_y: float) -> list:
    """(dx, dy) offsets of every pile relative to the group centre (mm).

    Row-major over X then Y; e.g. the default 2 x 2 grid at 600 c/c
    returns [(-300,-300), (-300,+300), (+300,-300), (+300,+300)].
    """
    positions = []
    for dx in _axis_offsets(n_piles_x, spacing_x):
        for dy in _axis_offsets(n_piles_y, spacing_y):
            positions.append((dx, dy))
    return positions
