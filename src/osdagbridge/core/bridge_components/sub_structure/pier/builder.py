"""
Pier (Circular Column) — Geometry Builder (pythonOCC)
=====================================================

Builds the 3D CAD solids of one circular reinforced-concrete pier column:

* concrete solid  : vertical cylinder (semi-transparent when displayed),
* reinforcement   : longitudinal (vertical) bars on a ring + circular
                    transverse tie rings, both with correct clear cover
                    so the cage is visible through the concrete.

The builder is GEOMETRY ONLY (no viewer, no material assignment) and
returns raw ``TopoDS_Shape`` objects for the Bridge CAD pipeline, exactly
like the superstructure builders (see ``super_structure/plate_girder/
builder.py``).

Units: millimetres (mm).

Coordinate convention (identical to the superstructure builders):
    X = longitudinal (along span, 0 .. span_length_L)
    Y = transverse  (deck width, centred on 0)
    Z = vertical    (Z = 0 at girder mid-height)

The column is placed in FINAL global coordinates: the caller (cad_generator)
passes the support line (x_center, y_center) and the Z of the column top
(the pier-cap soffit). The column extends DOWNWARD by ``pier_height``.
"""

import math

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut

from osdagbridge.core.bridge_components.sub_structure.pier.geometry import (
    bar_ring_radius,
    longitudinal_bar_angles,
    longitudinal_bar_count,
    tie_levels,
)
from osdagbridge.core.bridge_components.sub_structure.pier.properties import (
    PierParams,
    PIER_DIAMETER,
    PIER_HEIGHT,
    REBAR_MAIN_DIAMETER,
    REBAR_SPACING_LONGITUDINAL,
    REBAR_TRANSVERSE_DIAMETER,
    REBAR_SPACING_TRANSVERSE,
    REBAR_COVER,
)

# Visibility hint consumed by the display layer (cad_generator / cad_3d):
# concrete is rendered semi-transparent so the cage inside is visible.
CONCRETE_OPACITY = 0.35          # 0.0 opaque .. 1.0 fully transparent


def _translate(shape, x=0.0, y=0.0, z=0.0):
    """Translate a shape by (x, y, z) and return the transformed copy."""
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _make_vertical_bar(x, y, z_bottom, length, diameter):
    """One vertical rebar cylinder centred on (x, y), from z_bottom up."""
    axis = gp_Ax2(gp_Pnt(x, y, z_bottom), gp_Dir(0, 0, 1))
    return BRepPrimAPI_MakeCylinder(axis, diameter / 2.0, length).Shape()


def _make_tie_ring(x_center, y_center, z, ring_radius, tie_diameter):
    """One circular transverse tie (a thin solid annulus) at height z.

    Modelled as a short outer cylinder minus a coaxial inner cylinder
    (BRepAlgoAPI_Cut), giving a washer-shaped ring whose centreline
    radius is ``ring_radius`` and whose bar diameter is ``tie_diameter``.
    The inner cylinder is slightly taller so the cut faces never end up
    coplanar with the outer ones.
    """
    outer = BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(x_center, y_center, z), gp_Dir(0, 0, 1)),
        ring_radius + tie_diameter / 2.0,
        tie_diameter,
    ).Shape()
    inner = BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(x_center, y_center, z - 0.5), gp_Dir(0, 0, 1)),
        max(0.1, ring_radius - tie_diameter / 2.0),
        tie_diameter + 1.0,
    ).Shape()
    return BRepAlgoAPI_Cut(outer, inner).Shape()


def build_pier(
    *,
    pier_diameter: float = PIER_DIAMETER,
    pier_height: float = PIER_HEIGHT,
    x_center: float = 0.0,
    y_center: float = 0.0,
    top_z: float = 0.0,
    include_rebar: bool = True,
    rebar_main_diameter: float = REBAR_MAIN_DIAMETER,
    rebar_spacing_longitudinal: float = REBAR_SPACING_LONGITUDINAL,
    rebar_transverse_diameter: float = REBAR_TRANSVERSE_DIAMETER,
    rebar_spacing_transverse: float = REBAR_SPACING_TRANSVERSE,
    rebar_cover: float = REBAR_COVER,
):
    """Build one circular RC pier column with its reinforcement cage.

    Parameters
    ----------
    pier_diameter : float
        Outside diameter of the column (mm). Default 800.
    pier_height : float
        Clear height between pier-cap soffit and pile-cap top (mm).
        Default 3000.
    x_center, y_center : float
        Global X (support line) and Y (transverse) of the column axis (mm).
    top_z : float
        Global Z of the column TOP face = pier-cap soffit (mm). The
        column extends downward to ``top_z - pier_height``.
    include_rebar : bool
        Generate the reinforcement solids (default True).
    rebar_main_diameter : float
        Longitudinal bar diameter (mm). Default 16.
    rebar_spacing_longitudinal : float
        Nominal c/c spacing of longitudinal bars around the core (mm).
        Default 150.
    rebar_transverse_diameter : float
        Tie ring bar diameter (mm). Default 8.
    rebar_spacing_transverse : float
        Nominal vertical c/c spacing of ties (mm). Default 200.
    rebar_cover : float
        Clear cover to the concrete face (mm). Default 40.

    Returns
    -------
    dict
        {
          "concrete":            [TopoDS_Shape],   # 1 column solid
          "rebar_longitudinal":  [TopoDS_Shape],   # vertical bars
          "rebar_transverse":    [TopoDS_Shape],   # tie rings (annuli)
        }
    """
    params = PierParams(
        pier_diameter=pier_diameter,
        pier_height=pier_height,
        rebar_main_diameter=rebar_main_diameter,
        rebar_spacing_longitudinal=rebar_spacing_longitudinal,
        rebar_transverse_diameter=rebar_transverse_diameter,
        rebar_spacing_transverse=rebar_spacing_transverse,
        rebar_cover=rebar_cover,
    )

    z_bottom = top_z - pier_height

    # --- Concrete column: single cylinder from bottom face up to top_z ---
    concrete = BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(x_center, y_center, z_bottom), gp_Dir(0, 0, 1)),
        pier_diameter / 2.0,
        pier_height,
    ).Shape()

    rebar_longitudinal = []
    rebar_transverse = []

    if include_rebar:
        # --- Longitudinal (vertical) bars on a ring ----------------------
        ring_r = bar_ring_radius(
            pier_diameter, rebar_cover, rebar_main_diameter
        )
        n_bars = longitudinal_bar_count(
            pier_diameter, rebar_cover, rebar_spacing_longitudinal
        )
        bar_length = max(0.0, pier_height - 2.0 * rebar_cover)
        z_bar_bottom = z_bottom + rebar_cover

        for angle in longitudinal_bar_angles(n_bars):
            bx = x_center + ring_r * math.cos(angle)
            by = y_center + ring_r * math.sin(angle)
            if bar_length > 0.0:
                rebar_longitudinal.append(
                    _make_vertical_bar(bx, by, z_bar_bottom,
                                       bar_length, rebar_main_diameter)
                )

        # --- Transverse circular ties (rings) ----------------------------
        # The tie centreline wraps the longitudinal-bar ring.
        for z_offset in tie_levels(pier_height, rebar_cover,
                                   rebar_spacing_transverse):
            rebar_transverse.append(
                _make_tie_ring(
                    x_center, y_center,
                    z_bottom + z_offset,
                    ring_r, rebar_transverse_diameter,
                )
            )

    return {
        "concrete": [concrete],
        "rebar_longitudinal": rebar_longitudinal,
        "rebar_transverse": rebar_transverse,
    }
