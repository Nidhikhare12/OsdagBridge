"""
Pier Cap Geometry Builder
=========================

Builds the hammerhead / trapezoidal RCC pier cap that sits atop the pier
columns and bears the girder soffit.

Pattern:
  - Same module-level defaults, private helpers, and ``build_*`` function
    signature as other substructure builders and the superstructure components.
  - Returns raw TopoDS_Shapes; no viewer, no fusion, no colour.

Shape:
  A trapezoidal cross-section (wider at top, narrower at bottom) lofted along
  the transverse Y axis using BRepOffsetAPI_ThruSections between a wider
  rectangular top profile and a narrower rectangular bottom profile.
  The resulting solid looks like a hammerhead / tapered cap beam.

Units: mm throughout.
Coordinate system (from GEMINI.md):
  X = longitudinal, Y = transverse, Z = vertical.
  Origin = centre of span at deck level (Z = 0).
  Pier cap top face is at ``cap_top_z`` (≤ 0, just below girder soffit).
"""

import math

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
)
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

# ---------------------------------------------------------------------------
# Module-level defaults (mm) — match user spec
# ---------------------------------------------------------------------------
DEFAULT_CAP_TOP_WIDTH: float    = 3000.0   # mm — wider top of trapezoidal cap
DEFAULT_CAP_BOTTOM_WIDTH: float = 1200.0   # mm — narrower bottom of cap
DEFAULT_CAP_DEPTH: float        = 600.0    # mm — longitudinal depth of cap
DEFAULT_CAP_HEIGHT: float       = 600.0    # mm — vertical height of cap
DEFAULT_CAP_LENGTH: float       = 4000.0   # mm — transverse length (Y direction)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_rect_wire(cx, cy, z, half_depth_x, half_width_y):
    """
    Build a closed rectangular wire in the XY plane at elevation Z.

    Args:
        cx (float): X centre of the rectangle (mm).
        cy (float): Y centre of the rectangle (mm).
        z (float): Z elevation (mm).
        half_depth_x (float): Half the X-extent (longitudinal depth, mm).
        half_width_y (float): Half the Y-extent (transverse width, mm).

    Returns:
        TopoDS_Wire: Closed rectangular wire.
    """
    pts = [
        gp_Pnt(cx - half_depth_x, cy - half_width_y, z),
        gp_Pnt(cx + half_depth_x, cy - half_width_y, z),
        gp_Pnt(cx + half_depth_x, cy + half_width_y, z),
        gp_Pnt(cx - half_depth_x, cy + half_width_y, z),
    ]
    wire_maker = BRepBuilderAPI_MakeWire()
    n = len(pts)
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
        wire_maker.Add(edge)
    return wire_maker.Wire()


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_pier_cap(
    *,
    cap_top_width: float = DEFAULT_CAP_TOP_WIDTH,
    cap_bottom_width: float = DEFAULT_CAP_BOTTOM_WIDTH,
    cap_depth: float = DEFAULT_CAP_DEPTH,
    cap_height: float = DEFAULT_CAP_HEIGHT,
    cap_length: float = DEFAULT_CAP_LENGTH,
    cap_top_z: float = 0.0,
    pier_x_positions: list = None,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build trapezoidal hammerhead RCC pier caps.

    Each cap is a lofted solid (BRepOffsetAPI_ThruSections) between:
      - a **top rectangular wire** of width ``cap_top_width`` (in Y) at
        ``cap_top_z``
      - a **bottom rectangular wire** of width ``cap_bottom_width`` (in Y) at
        ``cap_top_z - cap_height``
    Both wires share the same longitudinal depth (``cap_depth`` in X) and are
    centred at the pier support X-position and Y = 0.

    Args:
        cap_top_width (float): Transverse width of the wider top face (mm).
        cap_bottom_width (float): Transverse width of the narrower bottom face (mm).
        cap_depth (float): Longitudinal depth of the cap (X direction, mm).
        cap_height (float): Vertical height of the cap (mm).
        cap_length (float): Alias for ``cap_top_width``; kept for back-compat.
            If both are provided, ``cap_top_width`` takes priority.
        cap_top_z (float): Z-coordinate of the top face of the cap (mm).
            Typically = -(girder_total_depth) so the top exactly meets
            the girder soffit.
        pier_x_positions (list[float] | None): X-coordinates (mm, along span)
            of each support.  Auto-derived from span / num_supports if None.
        span_length_L (float): Total bridge span (mm).
        num_supports (int): Number of supports (used only when
            ``pier_x_positions`` is None).

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pier_caps": [TopoDS_Shape, ...]}``.  One lofted solid per support.
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

    z_top = float(cap_top_z)
    z_bot = z_top - float(cap_height)
    half_depth = cap_depth / 2.0
    half_top_w = cap_top_width / 2.0
    half_bot_w = cap_bottom_width / 2.0

    pier_caps = []

    for x_pos in pier_x_positions:
        # Cap centred at span X-position, extending transversely in Y
        # Wire: X depth = cap_depth (longitudinal), Y width = cap_top/bottom_width (transverse)
        top_wire = _make_rect_wire(x_pos, 0.0, z_top, half_depth, half_top_w)
        bot_wire = _make_rect_wire(x_pos, 0.0, z_bot, half_depth, half_bot_w)

        # Loft through the two sections
        loft = BRepOffsetAPI_ThruSections(True, True)   # solid, ruled
        loft.AddWire(bot_wire)   # bottom section added first (lower Z)
        loft.AddWire(top_wire)   # top section
        loft.Build()

        if loft.IsDone():
            pier_caps.append(loft.Shape())
        else:
            # Fallback: rectangular box using top width if loft fails
            from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
            x0 = x_pos - half_depth
            y0 = -half_top_w
            box = BRepPrimAPI_MakeBox(
                gp_Pnt(float(x0), float(y0), float(z_bot)),
                float(cap_depth), float(cap_top_width), float(cap_height)
            ).Shape()
            pier_caps.append(box)

    return {"pier_caps": pier_caps}
