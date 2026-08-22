"""
Pile Cap (Rectangular Prism) Geometry Builder
================================================
Units: millimeters. `top_center` is the center point of the cap's top face;
the solid extrudes downward (-Z) by `depth`.
"""
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

DEFAULT_LENGTH = 2200.0
DEFAULT_WIDTH = 1200.0
DEFAULT_DEPTH = 600.0

DEFAULT_REBAR_MAIN_DIA = 16.0
DEFAULT_REBAR_SPACING_LONGITUDINAL = 150.0
DEFAULT_REBAR_TRANSVERSE_DIA = 8.0
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


def build_pile_cap_geometry(
    length=DEFAULT_LENGTH,
    width=DEFAULT_WIDTH,
    depth=DEFAULT_DEPTH,
    top_center=(0.0, 0.0, 0.0),
    rebar_main_dia=DEFAULT_REBAR_MAIN_DIA,
    rebar_spacing_longitudinal=DEFAULT_REBAR_SPACING_LONGITUDINAL,
    rebar_transverse_dia=DEFAULT_REBAR_TRANSVERSE_DIA,
    rebar_cover=DEFAULT_REBAR_COVER,
    include_rebar=True,
):
    """
    Returns dict with keys:
        "pile_cap_concrete": [TopoDS_Shape]
        "pile_cap_rebar": [TopoDS_Shape]
        "pile_cap_bottom_z": float  -- Z where piles begin below
    """
    x0, y0, z0 = top_center
    corner = gp_Pnt(x0 - length / 2.0, y0 - width / 2.0, z0 - depth)
    axis = gp_Ax2(corner, gp_Dir(0, 0, 1))
    concrete = BRepPrimAPI_MakeBox(axis, length, width, depth).Shape()

    rebar_shapes = []
    if include_rebar:
        inset = rebar_cover + rebar_transverse_dia + rebar_main_dia / 2.0
        z_positions = [z0 - inset, z0 - depth + inset]  # top mat, bottom mat

        for z in z_positions:
            # Bars running along X, spaced along Y.
            y = y0 - width / 2.0 + inset
            while y <= y0 + width / 2.0 - inset:
                bar_axis = gp_Ax2(gp_Pnt(x0 - length / 2.0 + inset, y, z), gp_Dir(1, 0, 0))
                bar = BRepPrimAPI_MakeCylinder(bar_axis, rebar_main_dia / 2.0, length - 2 * inset).Shape()
                rebar_shapes.append(bar)
                y += rebar_spacing_longitudinal

            # Bars running along Y, spaced along X.
            x = x0 - length / 2.0 + inset
            while x <= x0 + length / 2.0 - inset:
                bar_axis = gp_Ax2(gp_Pnt(x, y0 - width / 2.0 + inset, z), gp_Dir(0, 1, 0))
                bar = BRepPrimAPI_MakeCylinder(bar_axis, rebar_main_dia / 2.0, width - 2 * inset).Shape()
                rebar_shapes.append(bar)
                x += rebar_spacing_longitudinal

    return {
        "pile_cap_concrete": [concrete],
        "pile_cap_rebar": _make_compound(rebar_shapes),
        "pile_cap_bottom_z": z0 - depth,
    }