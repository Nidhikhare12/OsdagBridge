"""
Pile Geometry Builder
=====================

Builds bored cast-in-situ RCC circular piles extending downward from the
base of the pile cap.

Pattern:
  - Same module-level defaults, private helpers, and ``build_*`` function
    as other substructure and superstructure builders.
  - Returns raw TopoDS_Shapes; no viewer, no fusion, no colour.

Shape:
  Solid vertical cylinders (BRepPrimAPI_MakeCylinder on a gp_Ax2 with -Z
  direction) positioned in a rectangular grid symmetrically under each pile
  cap, spaced by ``pile_spacing`` (centre-to-centre) in both X and Y.

Defaults follow user specification:
  n_piles_per_cap = 4 (2×2 grid)
  pile_diameter   = 400 mm
  pile_length     = 5000 mm
  pile_spacing    = 600 mm (c/c in both X and Y)

Units: mm throughout.
Coordinate system (from GEMINI.md):
  X = longitudinal, Y = transverse, Z = vertical.
  Piles extend downward (−Z) from ``pile_top_z``.
"""

import math

from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# ---------------------------------------------------------------------------
# Module-level defaults (mm) — match user spec
# ---------------------------------------------------------------------------
DEFAULT_PILE_DIAMETER: float  = 400.0    # mm — outer diameter
DEFAULT_PILE_LENGTH: float    = 5000.0  # mm — extends downward from pile-cap base
DEFAULT_PILE_ROWS: int        = 2        # rows in X direction (total = rows × cols)
DEFAULT_PILE_COLS: int        = 2        # columns in Y direction
DEFAULT_PILE_SPACING: float   = 600.0   # mm — c/c spacing in both X and Y


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_pile_cylinder(x, y, z_top, radius, length):
    """
    Create one vertical downward pile cylinder.

    Args:
        x (float): X-coordinate of pile centre (mm).
        y (float): Y-coordinate of pile centre (mm).
        z_top (float): Z-coordinate of the pile top (mm).
        radius (float): Pile radius (mm).
        length (float): Pile length, extending downward (mm).

    Returns:
        TopoDS_Shape: Pile cylinder solid.
    """
    origin = gp_Pnt(float(x), float(y), float(z_top))
    # Axis points downward (−Z) so pile extends below z_top
    axis = gp_Ax2(origin, gp_Dir(0.0, 0.0, -1.0))
    return BRepPrimAPI_MakeCylinder(axis, float(radius), float(length)).Shape()


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_piles(
    *,
    pile_diameter: float = DEFAULT_PILE_DIAMETER,
    pile_length: float = DEFAULT_PILE_LENGTH,
    pile_rows: int = DEFAULT_PILE_ROWS,
    pile_cols: int = DEFAULT_PILE_COLS,
    pile_spacing_x: float = DEFAULT_PILE_SPACING,
    pile_spacing_y: float = DEFAULT_PILE_SPACING,
    pile_top_z: float = -4800.0,
    pier_x_positions: list = None,
    pier_y_center: float = 0.0,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build bored RCC piles under each pile cap.

    Piles are arranged in a rectangular grid of ``pile_rows`` (X direction)
    by ``pile_cols`` (Y direction), centred on each support X-position and
    ``pier_y_center``.  Each pile extends downward from ``pile_top_z``.

    Args:
        pile_diameter (float): Outer diameter of each pile (mm).
        pile_length (float): Length of each pile, extending downward (mm).
        pile_rows (int): Number of pile rows in the X (longitudinal) direction.
        pile_cols (int): Number of pile columns in the Y (transverse) direction.
        pile_spacing_x (float): Centre-to-centre pile spacing in X (mm).
        pile_spacing_y (float): Centre-to-centre pile spacing in Y (mm).
        pile_top_z (float): Z-coordinate of pile tops (mm).  Must equal
            the bottom face of the pile cap
            (``pile_cap.cap_top_z - pile_cap.cap_thickness``).
        pier_x_positions (list[float] | None): X-coordinates (mm) of each
            intermediate support.  Auto-derived if None.
        pier_y_center (float): Y-coordinate of each pile group centre (mm).
        span_length_L (float): Total bridge span (mm); used to derive
            ``pier_x_positions`` when None.
        num_supports (int): Number of intermediate support rows; used only
            when ``pier_x_positions`` is None.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"piles": [TopoDS_Shape, ...]}``.  One cylinder per pile.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [step * i for i in range(n)]

    radius = pile_diameter / 2.0

    # Pile positions relative to group centre
    # X offsets = longitudinal spread, Y offsets = transverse spread
    total_x_spread = (pile_rows - 1) * pile_spacing_x
    total_y_spread = (pile_cols - 1) * pile_spacing_y
    x_offsets = [-total_x_spread / 2.0 + r * pile_spacing_x for r in range(pile_rows)]
    y_offsets = [-total_y_spread / 2.0 + c * pile_spacing_y for c in range(pile_cols)]

    piles = []

    for x_centre in pier_x_positions:
        for dx in x_offsets:
            for dy in y_offsets:
                pile = _make_pile_cylinder(
                    x=x_centre + dx,
                    y=pier_y_center + dy,
                    z_top=pile_top_z,
                    radius=radius,
                    length=pile_length,
                )
                piles.append(pile)

    return {"piles": piles}
