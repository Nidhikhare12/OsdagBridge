"""
Pier Cap (Hammerhead/Trapezoidal) Geometry Builder
=====================================================
Cross-section (X-Z plane, looking along transverse Y) is a trapezoid: wide at
the deck soffit (top_width), tapering to a narrower base where it meets the
pier (bottom_width), over a vertical `depth`. Extruded along Y by `length`
(set this to the deck width so the cap spans under the whole deck).

Units: millimeters. `top_center` = midpoint of the top edge at the cap's
transverse start (local Y=0) -- typically set so the cap is centered across
the deck width and centered on the pier in X.
"""
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

DEFAULT_TOP_WIDTH = 3000.0
DEFAULT_BOTTOM_WIDTH = 1200.0
DEFAULT_DEPTH = 600.0

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


def build_pier_cap_geometry(
    top_width=DEFAULT_TOP_WIDTH,
    bottom_width=DEFAULT_BOTTOM_WIDTH,
    depth=DEFAULT_DEPTH,
    length=5000.0,  # set to deck width by the caller
    top_center=(0.0, 0.0, 0.0),
    rebar_main_dia=DEFAULT_REBAR_MAIN_DIA,
    rebar_spacing_longitudinal=DEFAULT_REBAR_SPACING_LONGITUDINAL,
    rebar_transverse_dia=DEFAULT_REBAR_TRANSVERSE_DIA,
    rebar_spacing_transverse=DEFAULT_REBAR_SPACING_TRANSVERSE,
    rebar_cover=DEFAULT_REBAR_COVER,
    include_rebar=True,
):
    """
    Build the pier cap concrete solid and its two-way reinforcement mesh.

    Returns dict with keys:
        "pier_cap_concrete": [TopoDS_Shape]
        "pier_cap_rebar": [TopoDS_Shape]
        "pier_cap_bottom_z": float  -- Z where the cap meets the pier below
    """
    x0, y0, z0 = top_center
    half_top = top_width / 2.0
    half_bottom = bottom_width / 2.0

    poly = BRepBuilderAPI_MakePolygon()
    poly.Add(gp_Pnt(x0 - half_top, y0, z0))
    poly.Add(gp_Pnt(x0 + half_top, y0, z0))
    poly.Add(gp_Pnt(x0 + half_bottom, y0, z0 - depth))
    poly.Add(gp_Pnt(x0 - half_bottom, y0, z0 - depth))
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    concrete = BRepPrimAPI_MakePrism(face, gp_Vec(0, length, 0)).Shape()

    rebar_shapes = []
    if include_rebar:
        from OCC.Core.gp import gp_Dir, gp_Ax2
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

        inset = rebar_cover + rebar_transverse_dia + rebar_main_dia / 2.0
        z_positions = [z0 - inset, z0 - depth + inset]  # near top face, near bottom face

        for z in z_positions:
            # Bars running along Y (transverse), spaced along local X (top_width span).
            x = x0 - half_top + inset
            while x <= x0 + half_top - inset:
                axis = gp_Ax2(gp_Pnt(x, y0 + inset, z), gp_Dir(0, 1, 0))
                bar = BRepPrimAPI_MakeCylinder(axis, rebar_main_dia / 2.0, length - 2 * inset).Shape()
                rebar_shapes.append(bar)
                x += rebar_spacing_longitudinal

            # Bars running along X, spaced along Y (length).
            y = y0 + inset
            while y <= y0 + length - inset:
                axis = gp_Ax2(gp_Pnt(x0 - half_top + inset, y, z), gp_Dir(1, 0, 0))
                bar = BRepPrimAPI_MakeCylinder(axis, rebar_main_dia / 2.0, top_width - 2 * inset).Shape()
                rebar_shapes.append(bar)
                y += rebar_spacing_longitudinal

    return {
        "pier_cap_concrete": [concrete],
        "pier_cap_rebar": _make_compound(rebar_shapes),
        "pier_cap_bottom_z": z0 - depth,
    }