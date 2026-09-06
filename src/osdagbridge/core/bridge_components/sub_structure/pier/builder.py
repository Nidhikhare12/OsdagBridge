"""
Pier (Circular Column) Geometry Builder
=========================================
Builds a pythonOCC solid for a circular bridge pier, plus its internal
reinforcement cage (longitudinal bars + circular ties), for display in the
OsdagBridge 3D viewer.

Units: millimeters, matching the rest of bridge_components (e.g. plate_girder).
Coordinate convention: X = longitudinal (span), Y = transverse (deck width),
Z = vertical. `top_center` is the point where the pier meets the pier cap
(i.e. the pier's TOP face center); the solid extrudes downward (-Z) by
`height` from there, since substructure sits below the deck.
"""
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeTorus
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

DEFAULT_PIER_DIAMETER = 800.0
DEFAULT_PIER_HEIGHT = 3000.0

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


def build_pier_geometry(
    diameter=DEFAULT_PIER_DIAMETER,
    height=DEFAULT_PIER_HEIGHT,
    top_center=(0.0, 0.0, 0.0),
    rebar_main_dia=DEFAULT_REBAR_MAIN_DIA,
    rebar_spacing_longitudinal=DEFAULT_REBAR_SPACING_LONGITUDINAL,
    rebar_transverse_dia=DEFAULT_REBAR_TRANSVERSE_DIA,
    rebar_spacing_transverse=DEFAULT_REBAR_SPACING_TRANSVERSE,
    rebar_cover=DEFAULT_REBAR_COVER,
    include_rebar=True,
):
    """
    Build the pier concrete solid and its reinforcement cage.

    Returns
    -------
    dict with keys:
        "pier_concrete": [TopoDS_Shape]      -- single solid cylinder
        "pier_rebar": [TopoDS_Shape]         -- compounded cage (longitudinal + ties)
        "pier_top_z": float                  -- Z of the pier's top face (== top_center z)
        "pier_bottom_z": float                -- Z of the pier's bottom face
    """
    radius = diameter / 2.0
    x0, y0, z0 = top_center

    # Concrete solid: extrude DOWN from top_center by `height`.
    axis = gp_Ax2(gp_Pnt(x0, y0, z0), gp_Dir(0, 0, -1))
    concrete = BRepPrimAPI_MakeCylinder(axis, radius, height).Shape()

    rebar_shapes = []
    if include_rebar:
        cage_radius = radius - rebar_cover - rebar_transverse_dia - rebar_main_dia / 2.0
        if cage_radius > 0:
            import math

            circumference = 2 * math.pi * cage_radius
            n_bars = max(4, round(circumference / rebar_spacing_longitudinal))

            # Longitudinal bars: vertical cylinders around the cage circle.
            for i in range(n_bars):
                theta = 2 * math.pi * i / n_bars
                bx = x0 + cage_radius * math.cos(theta)
                by = y0 + cage_radius * math.sin(theta)
                bar_axis = gp_Ax2(gp_Pnt(bx, by, z0), gp_Dir(0, 0, -1))
                bar = BRepPrimAPI_MakeCylinder(bar_axis, rebar_main_dia / 2.0, height).Shape()
                rebar_shapes.append(bar)

            # Transverse ties: circular hoops (torus) at intervals down the height.
            n_ties = max(1, int(height // rebar_spacing_transverse) + 1)
            for j in range(n_ties):
                z = z0 - min(j * rebar_spacing_transverse, height)
                tie_axis = gp_Ax2(gp_Pnt(x0, y0, z), gp_Dir(0, 0, 1))
                tie = BRepPrimAPI_MakeTorus(tie_axis, cage_radius, rebar_transverse_dia / 2.0).Shape()
                rebar_shapes.append(tie)

    return {
        "pier_concrete": [concrete],
        "pier_rebar": _make_compound(rebar_shapes),
        "pier_top_z": z0,
        "pier_bottom_z": z0 - height,
    }