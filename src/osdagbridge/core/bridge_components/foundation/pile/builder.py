"""
Pile Group (Circular Piles, 2x2 Grid) Geometry Builder
=========================================================
Units: millimeters. `top_center` is the point directly below the pile cap's
underside, centered on the 2x2 grid; piles extrude downward (-Z) by `length`.
"""
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeTorus
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

DEFAULT_PILE_DIAMETER = 400.0
DEFAULT_PILE_LENGTH = 5000.0
DEFAULT_PILE_SPACING = 600.0
DEFAULT_N_PILES = 4  # 2x2 grid

DEFAULT_REBAR_MAIN_DIA = 16.0
DEFAULT_REBAR_SPACING_LONGITUDINAL = 150.0
DEFAULT_REBAR_TRANSVERSE_DIA = 8.0
DEFAULT_REBAR_SPACING_TRANSVERSE = 200.0
DEFAULT_REBAR_COVER = 40.0


def _make_compound(shapes):
    if not shapes:
        return []
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for s in shapes:
        builder.Add(compound, s)
    return [compound]


def _pile_centers(top_center, spacing, n_x=2, n_y=2):
    x0, y0, z0 = top_center
    x_offsets = [(-0.5 + i) * spacing for i in range(n_x)] if n_x > 1 else [0.0]
    y_offsets = [(-0.5 + j) * spacing for j in range(n_y)] if n_y > 1 else [0.0]
    return [(x0 + dx, y0 + dy, z0) for dx in x_offsets for dy in y_offsets]


def build_pile_group_geometry(
    diameter=DEFAULT_PILE_DIAMETER,
    length=DEFAULT_PILE_LENGTH,
    spacing=DEFAULT_PILE_SPACING,
    top_center=(0.0, 0.0, 0.0),
    n_x=2,
    n_y=2,
    rebar_main_dia=DEFAULT_REBAR_MAIN_DIA,
    rebar_spacing_longitudinal=DEFAULT_REBAR_SPACING_LONGITUDINAL,
    rebar_transverse_dia=DEFAULT_REBAR_TRANSVERSE_DIA,
    rebar_spacing_transverse=DEFAULT_REBAR_SPACING_TRANSVERSE,
    rebar_cover=DEFAULT_REBAR_COVER,
    include_rebar=True,
):
    """
    Returns dict with keys:
        "pile_concrete": [TopoDS_Shape, ...]  -- one solid per pile (4 for 2x2)
        "pile_rebar": [TopoDS_Shape]           -- compounded cages for all piles
        "pile_centers": [(x, y, z), ...]       -- top-face center of each pile
    """
    radius = diameter / 2.0
    centers = _pile_centers(top_center, spacing, n_x, n_y)

    concrete_shapes = []
    rebar_shapes = []

    for (x0, y0, z0) in centers:
        axis = gp_Ax2(gp_Pnt(x0, y0, z0), gp_Dir(0, 0, -1))
        concrete_shapes.append(BRepPrimAPI_MakeCylinder(axis, radius, length).Shape())

        if include_rebar:
            cage_radius = radius - rebar_cover - rebar_transverse_dia - rebar_main_dia / 2.0
            if cage_radius > 0:
                import math

                circumference = 2 * math.pi * cage_radius
                n_bars = max(4, round(circumference / rebar_spacing_longitudinal))

                for i in range(n_bars):
                    theta = 2 * math.pi * i / n_bars
                    bx = x0 + cage_radius * math.cos(theta)
                    by = y0 + cage_radius * math.sin(theta)
                    bar_axis = gp_Ax2(gp_Pnt(bx, by, z0), gp_Dir(0, 0, -1))
                    rebar_shapes.append(
                        BRepPrimAPI_MakeCylinder(bar_axis, rebar_main_dia / 2.0, length).Shape()
                    )

                n_ties = max(1, int(length // rebar_spacing_transverse) + 1)
                for j in range(n_ties):
                    z = z0 - min(j * rebar_spacing_transverse, length)
                    tie_axis = gp_Ax2(gp_Pnt(x0, y0, z), gp_Dir(0, 0, 1))
                    rebar_shapes.append(
                        BRepPrimAPI_MakeTorus(tie_axis, cage_radius, rebar_transverse_dia / 2.0).Shape()
                    )

    return {
        "pile_concrete": concrete_shapes,
        "pile_rebar": _make_compound(rebar_shapes),
        "pile_centers": centers,
    }