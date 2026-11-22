"""
Pile Cap — Geometry Builder (pythonOCC)
=======================================

Builds the 3D CAD solids of one rectangular reinforced-concrete pile cap:

* concrete solid : rectangular prism (semi-transparent when displayed),
* reinforcement  : bottom mat made of
      - main (longitudinal) bars  -> along global X, spread across Y,
      - transverse (distribution) bars -> along global Y, spread across X,
    all with correct clear cover; the transverse bars rest on top of the
    main bars so the mat is visible through the concrete.

GEOMETRY ONLY (no viewer, no material). Returns raw ``TopoDS_Shape``
solids for the Bridge CAD pipeline, mirroring the superstructure
builders.

Units: millimetres (mm).

Coordinate convention (identical to the superstructure builders):
    X = longitudinal (along span), Y = transverse (deck width),
    Z = vertical (Z = 0 at girder mid-height).

The cap is placed in FINAL global coordinates: the caller passes the
pile-group centreline (x_center, y_center) and the Z of the cap TOP face
(the pier column base). The cap extends DOWNWARD by ``depth``.
"""

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

from osdagbridge.core.bridge_components.foundation.pile_cap.geometry import (
    main_bar_positions,
    transverse_bar_positions,
    main_bar_z,
    transverse_bar_z,
)
from osdagbridge.core.bridge_components.foundation.pile_cap.properties import (
    PileCapParams,
    PILE_CAP_LENGTH,
    PILE_CAP_WIDTH,
    PILE_CAP_DEPTH,
    REBAR_MAIN_DIAMETER,
    REBAR_SPACING_LONGITUDINAL,
    REBAR_TRANSVERSE_DIAMETER,
    REBAR_SPACING_TRANSVERSE,
    REBAR_COVER,
)

# Visibility hint consumed by the display layer: concrete is rendered
# semi-transparent so the rebar mat inside is visible.
CONCRETE_OPACITY = 0.35


def _translate(shape, x=0.0, y=0.0, z=0.0):
    """Translate a shape by (x, y, z) and return the transformed copy."""
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _make_bar_along_x(x_start, y, z, length, diameter):
    """One rebar cylinder starting at (x_start, y, z) running along +X."""
    axis = gp_Ax2(gp_Pnt(x_start, y, z), gp_Dir(1, 0, 0))
    return BRepPrimAPI_MakeCylinder(axis, diameter / 2.0, length).Shape()


def _make_bar_along_y(x, y_start, z, length, diameter):
    """One rebar cylinder starting at (x, y_start, z) running along +Y."""
    axis = gp_Ax2(gp_Pnt(x, y_start, z), gp_Dir(0, 1, 0))
    return BRepPrimAPI_MakeCylinder(axis, diameter / 2.0, length).Shape()


def build_pile_cap(
    *,
    length: float = PILE_CAP_LENGTH,
    width: float = PILE_CAP_WIDTH,
    depth: float = PILE_CAP_DEPTH,
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
    """Build one rectangular RC pile cap with a bottom rebar mat.

    Parameters
    ----------
    length : float
        Longitudinal (X) dimension of the prism (mm). Default 2200.
    width : float
        Transverse (Y) dimension of the prism (mm). Default 1200.
    depth : float
        Vertical (Z) dimension of the prism (mm). Default 600.
    x_center, y_center : float
        Global centreline of the cap / pile group (mm).
    top_z : float
        Global Z of the cap TOP face (the pier column base). The cap
        extends downward to ``top_z - depth``.
    include_rebar : bool
        Generate the reinforcement solids (default True).
    rebar_main_diameter : float
        Main (longitudinal, +X) bar diameter (mm). Default 16.
    rebar_spacing_longitudinal : float
        c/c spacing of main bars across the width (mm). Default 150.
    rebar_transverse_diameter : float
        Transverse (+Y) bar diameter (mm). Default 8.
    rebar_spacing_transverse : float
        c/c spacing of transverse bars along the length (mm). Default 200.
    rebar_cover : float
        Clear cover / bar end inset (mm). Default 40.

    Returns
    -------
    dict
        {
          "concrete":           [TopoDS_Shape],  # 1 box solid
          "rebar_longitudinal": [TopoDS_Shape],  # main bars (+X)
          "rebar_transverse":   [TopoDS_Shape],  # distribution bars (+Y)
        }
    """
    params = PileCapParams(
        length=length,
        width=width,
        depth=depth,
        rebar_main_diameter=rebar_main_diameter,
        rebar_spacing_longitudinal=rebar_spacing_longitudinal,
        rebar_transverse_diameter=rebar_transverse_diameter,
        rebar_spacing_transverse=rebar_spacing_transverse,
        rebar_cover=rebar_cover,
    )

    z_bottom = top_z - depth

    # --- Concrete: axis-aligned box centred on (x_center, y_center) ------
    # MakeBox builds from (0,0,0) to (dx,dy,dz); translate into place
    # (same pattern as the deck slab in super_structure/deck/builder.py).
    box = BRepPrimAPI_MakeBox(length, width, depth).Shape()
    concrete = _translate(box, x_center - length / 2.0,
                          y_center - width / 2.0, z_bottom)

    rebar_longitudinal = []
    rebar_transverse = []

    if include_rebar:
        # --- Main bars: along +X, spread across Y -----------------------
        main_len = max(0.0, length - 2.0 * rebar_cover)
        z_main = z_bottom + main_bar_z(depth, rebar_cover, rebar_main_diameter)
        x_start = x_center - main_len / 2.0

        if main_len > 0.0:
            for dy in main_bar_positions(width, rebar_cover,
                                         rebar_spacing_longitudinal):
                rebar_longitudinal.append(
                    _make_bar_along_x(x_start, y_center + dy, z_main,
                                      main_len, rebar_main_diameter)
                )

        # --- Transverse bars: along +Y, spread across X -----------------
        trans_len = max(0.0, width - 2.0 * rebar_cover)
        z_trans = z_bottom + transverse_bar_z(
            depth, rebar_cover, rebar_main_diameter, rebar_transverse_diameter
        )
        y_start = y_center - trans_len / 2.0

        if trans_len > 0.0:
            for dx in transverse_bar_positions(length, rebar_cover,
                                               rebar_spacing_transverse):
                rebar_transverse.append(
                    _make_bar_along_y(x_center + dx, y_start, z_trans,
                                      trans_len, rebar_transverse_diameter)
                )

    return {
        "concrete": [concrete],
        "rebar_longitudinal": rebar_longitudinal,
        "rebar_transverse": rebar_transverse,
    }
