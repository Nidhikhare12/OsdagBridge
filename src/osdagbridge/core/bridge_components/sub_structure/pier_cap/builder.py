"""
Pier Cap (Hammerhead) — Geometry Builder (pythonOCC)
====================================================

Builds the 3D CAD solid of one trapezoidal hammerhead pier cap:

* a prism whose cross-section (longitudinal-vertical, X-Z plane) is a
  trapezoid — wide at the top where the girder bearings sit, narrow at
  the bottom where it lands on the circular column —
* extruded TRANSVERSELY (along global Y) over the cap length, which the
  bridge assembly matches to the deck width.

GEOMETRY ONLY (no viewer, no material). Returns raw ``TopoDS_Shape``
solids for the Bridge CAD pipeline, mirroring the superstructure
builders.

Units: millimetres (mm).

Coordinate convention (identical to the superstructure builders):
    X = longitudinal (along span), Y = transverse (deck width),
    Z = vertical (Z = 0 at girder mid-height).

The cap is placed in FINAL global coordinates: the caller passes the
support line (x_center) and the Z of the cap TOP face (the bearing
level / girder soffit). The cap extends DOWNWARD by ``depth``.
"""

from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
)
from OCC.Core.gp import gp_Trsf

from osdagbridge.core.bridge_components.sub_structure.pier_cap.geometry import (
    trapezoid_profile_points,
)
from osdagbridge.core.bridge_components.sub_structure.pier_cap.properties import (
    PierCapParams,
    PIER_CAP_TOP_WIDTH,
    PIER_CAP_BOTTOM_WIDTH,
    PIER_CAP_DEPTH,
)

# Visibility hint consumed by the display layer: concrete is rendered
# semi-transparent so the components below stay readable.
CONCRETE_OPACITY = 0.35


def _translate(shape, x=0.0, y=0.0, z=0.0):
    """Translate a shape by (x, y, z) and return the transformed copy."""
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def build_pier_cap(
    *,
    top_width: float = PIER_CAP_TOP_WIDTH,
    bottom_width: float = PIER_CAP_BOTTOM_WIDTH,
    depth: float = PIER_CAP_DEPTH,
    length: float = None,
    x_center: float = 0.0,
    y_center: float = 0.0,
    top_z: float = 0.0,
):
    """Build one trapezoidal hammerhead pier cap.

    Parameters
    ----------
    top_width : float
        Longitudinal (X) width at the cap TOP (bearing) face (mm).
        Default 3000.
    bottom_width : float
        Longitudinal (X) width at the cap BOTTOM face (mm). Default 1200.
    depth : float
        Vertical depth of the cap (mm). Default 600.
    length : float or None
        Transverse (Y) length of the cap (mm). ``None`` (default) falls
        back to ``3 x bottom_width`` so the builder also works
        standalone; the bridge assembly (cad_generator) passes the deck
        width instead (see ``pier_cap.geometry.auto_pier_cap_length``).
    x_center, y_center : float
        Global X (support line) and Y of the cap centreline (mm).
    top_z : float
        Global Z of the cap TOP face = bearing level / girder soffit.
        The cap extends downward to ``top_z - depth``.

    Returns
    -------
    dict
        {"concrete": [TopoDS_Shape]}   # 1 prismatic trapezoid solid
    """
    if length is None:
        length = 3.0 * bottom_width

    params = PierCapParams(
        top_width=top_width,
        bottom_width=bottom_width,
        depth=depth,
        length=length,
    )

    # Trapezoid corners in the longitudinal-vertical (X-Z) plane at Y = 0,
    # expressed in final global coordinates:
    #   global X = x_center + u
    #   global Z = top_z    - v      (v grows downward from the top face)
    pts_uv = trapezoid_profile_points(
        params.top_width, params.bottom_width, params.depth
    )
    pts_xyz = [
        gp_Pnt(x_center + u, 0.0, top_z - v)
        for (u, v) in pts_uv
    ]

    # Closed polygon -> planar face -> prism extruded along +Y.
    poly = BRepBuilderAPI_MakePolygon()
    for p in pts_xyz:
        poly.Add(p)
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    cap = BRepPrimAPI_MakePrism(face, gp_Vec(0.0, params.length, 0.0)).Shape()

    # Centre the extrusion on the cap centreline (extrusion started at Y=0).
    cap = _translate(cap, 0.0, y_center - params.length / 2.0, 0.0)

    return {"concrete": [cap]}
