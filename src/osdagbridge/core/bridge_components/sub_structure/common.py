"""Shared pythonOCC helpers and the Part record passed to display / IFC."""
import math
from dataclasses import dataclass, field

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Vec
from OCC.Core.BRepPrimAPI import (BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox,
                                  BRepPrimAPI_MakePrism, BRepPrimAPI_MakeTorus)
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace

CONCRETE_COLOR = (0.75, 0.75, 0.75)
STEEL_COLOR = (0.30, 0.36, 0.45)


@dataclass
class Part:
    name: str
    shape: object
    ifc_class: str                 # IfcColumn, IfcBeam, IfcFooting, IfcPile, IfcReinforcingBar
    kind: str                      # "concrete" | "steel"
    color: tuple = CONCRETE_COLOR
    opacity: float = 1.0
    meta: dict = field(default_factory=dict)


def cylinder(p0, direction, radius, length):
    """Cylinder starting at p0=(x,y,z) along `direction`."""
    ax = gp_Ax2(gp_Pnt(*p0), gp_Dir(*direction))
    return BRepPrimAPI_MakeCylinder(ax, radius, length).Shape()


def box(x0, y0, z0, dx, dy, dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), dx, dy, dz).Shape()


def ring(cx, cy, z, big_r, small_r):
    """Circular hoop (torus) in the XY plane at height z."""
    ax = gp_Ax2(gp_Pnt(cx, cy, z), gp_Dir(0, 0, 1))
    return BRepPrimAPI_MakeTorus(ax, big_r, small_r).Shape()


def trapezoid_prism(top_w, bot_w, z_top, z_bot, x_c, y0, length):
    """Trapezoid profile in XZ plane extruded along +Y from y0 by `length`."""
    pts = [(x_c - bot_w / 2, z_bot), (x_c + bot_w / 2, z_bot),
           (x_c + top_w / 2, z_top), (x_c - top_w / 2, z_top)]
    poly = BRepBuilderAPI_MakePolygon()
    for x, z in pts:
        poly.Add(gp_Pnt(x, y0, z))
    poly.Close()
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, length, 0)).Shape()


def grid_positions(half_span, step):
    """Symmetric bar positions about 0 within +-half_span at `step` spacing."""
    if half_span <= 0:
        return [0.0]
    n = int((2 * half_span) // step)
    start = -n * step / 2.0
    return [start + i * step for i in range(n + 1)]


def z_range(z0, z1, step):
    """Z levels from z0 to z1 inclusive at <= step spacing."""
    out, z = [], z0
    while z <= z1 + 1e-6:
        out.append(z)
        z += step
    return out


def circle_points(cx, cy, radius, n):
    return [(cx + radius * math.cos(2 * math.pi * i / n),
             cy + radius * math.sin(2 * math.pi * i / n)) for i in range(n)]
