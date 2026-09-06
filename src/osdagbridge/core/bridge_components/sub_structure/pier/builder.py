"""
Pier Geometry Builder
=====================

Builds circular RCC pier column(s) for plate-girder bridge substructure.

Pattern:
  - Same import style, module-level defaults, private helpers, and
    ``build_*`` public function as superstructure components (e.g.
    cross_bracing/builder.py, plate_girder/builder.py).
  - Returns raw TopoDS_Shapes; no viewer, no fusion, no colour.
  - Default pier shape: solid circular cylinder (BRepPrimAPI_MakeCylinder
    on a gp_Ax2 aligned with Z).
  - Set wall_thickness > 0 to create a hollow annular shaft (outer minus inner
    cylinder via BRepAlgoAPI_Cut).

Units: mm throughout.
Coordinate system (from  .md):
  X = longitudinal (span direction)
  Y = transverse (deck width direction)
  Z = vertical, positive upward
  Origin = centre of span at deck level (Z = 0).
  Substructure sits below Z = 0.
"""

import math

from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# ---------------------------------------------------------------------------
# Module-level defaults (mm) — match user spec
# ---------------------------------------------------------------------------
DEFAULT_PIER_DIAMETER: float = 800.0     # mm — outer diameter of pier shaft
DEFAULT_PIER_HEIGHT: float   = 3000.0   # mm — from pile-cap top to pier-cap soffit
DEFAULT_WALL_THICKNESS: float = 0.0     # mm — 0 = solid shaft


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_cylinder(origin_xyz, radius_mm, height_mm):
    """
    Create an upright solid cylinder aligned with +Z.

    Args:
        origin_xyz (tuple): (x, y, z) of the cylinder base centre (mm).
        radius_mm (float): Cylinder radius (mm).
        height_mm (float): Cylinder height (mm), extends in +Z direction.

    Returns:
        TopoDS_Shape: The cylinder solid.
    """
    origin = gp_Pnt(float(origin_xyz[0]), float(origin_xyz[1]), float(origin_xyz[2]))
    ax = gp_Ax2(origin, gp_Dir(0.0, 0.0, 1.0))
    return BRepPrimAPI_MakeCylinder(ax, float(radius_mm), float(height_mm)).Shape()


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_pier(
    *,
    pier_height: float = DEFAULT_PIER_HEIGHT,
    pier_diameter: float = DEFAULT_PIER_DIAMETER,
    wall_thickness: float = DEFAULT_WALL_THICKNESS,
    num_piers: int = 2,
    pier_spacing: float = 2000.0,
    pier_x_positions: list = None,
    pier_base_z: float = -DEFAULT_PIER_HEIGHT,
    num_supports: int = 1,
    span_length_L: float = 20000.0,
):
    """
    Build circular RCC pier shafts.

    Creates ``num_piers`` columns placed side-by-side in the Y (transverse)
    direction at each support X-position along the span.
    Columns are centred symmetrically around Y = 0 with
    ``pier_spacing`` centre-to-centre.

    Coordinate system ( .md):
      X = longitudinal (span), Y = transverse, Z = vertical.

    Args:
        pier_height (float): Vertical height of each pier shaft (mm).
            Shaft extends from ``pier_base_z`` to ``pier_base_z + pier_height``.
        pier_diameter (float): Outer diameter of each circular pier (mm).
        wall_thickness (float): Wall thickness for hollow piers (mm).
            Pass 0 (default) for a solid shaft.
        num_piers (int): Number of pier columns in the transverse (Y) direction
            at each support location.
        pier_spacing (float): Centre-to-centre spacing between adjacent pier
            columns in the Y direction (mm).
        pier_x_positions (list[float] | None): Explicit X-coordinates (mm) of
            each support along the span.  If None, equally-spaced positions are
            derived from ``span_length_L`` and ``num_supports``.
        pier_base_z (float): Z-coordinate of the base of each pier shaft (mm).
            Must be negative (below deck level).
        num_supports (int): Number of support rows.  Used only when
            ``pier_x_positions`` is None.
        span_length_L (float): Total bridge span (mm).  Used to auto-derive
            ``pier_x_positions`` when that parameter is None.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pier_shafts": [TopoDS_Shape, ...]}``.
            One solid per pier column (solid cylinder or hollow annulus).
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

    radius = pier_diameter / 2.0
    inner_radius = max(0.0, radius - float(wall_thickness)) if wall_thickness > 0.0 else 0.0

    # Y offsets: centre the columns symmetrically in Y (transverse) around Y = 0
    total_spread = (num_piers - 1) * pier_spacing
    y_offsets = [-total_spread / 2.0 + i * pier_spacing for i in range(num_piers)]

    pier_shafts = []

    for x_pos in pier_x_positions:
        for y_off in y_offsets:
            # X = span position, Y = transverse column offset, Z = pier base
            origin = (x_pos, y_off, pier_base_z)
            outer = _make_cylinder(origin, radius, pier_height)

            if wall_thickness > 0.0 and inner_radius > 0.0:
                inner = _make_cylinder(origin, inner_radius, pier_height)
                shaft = BRepAlgoAPI_Cut(outer, inner).Shape()
            else:
                shaft = outer

            pier_shafts.append(shaft)

    return {"pier_shafts": pier_shafts}
