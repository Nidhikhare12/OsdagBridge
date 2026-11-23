"""
Pier builder - circular RCC column.

Local frame (support frame, mm)
-------------------------------
* origin  : on the pier-cap top surface, at the centre of the support line
* +X      : longitudinal (span) direction, perpendicular to the support line
* +Y      : transverse direction, along the support line
* +Z      : vertical, upwards

The pier is a vertical cylinder whose top touches the pier-cap soffit.

Reinforcement
-------------
* Longitudinal bars: ``n = max(6, ceil(2*pi*r_cage / s_long))`` bars on a
  circle of radius ``r_cage = R - cover - d_tie - d_main/2`` (IS 456
  cl. 26.5.3.1 requires at least 6 bars in a circular column).  The bars are
  anchored into the pile cap below and the pier cap above (starter bars), so
  ``bar_z_bottom`` / ``bar_z_top`` are supplied by the assembly.
* Circular ties: rings of centre-line radius ``R - cover - d_tie/2`` at
  ``s_tie`` c/c over the clear height of the pier.
"""

import math

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, straight_bar, polyline_bar, ring_bar, stepped, circular_bar_count,
    build_rebar_solids,
)

# Default pier dimensions (mm) - screening-task defaults
PIER_DIAMETER = 800
PIER_HEIGHT = 3000


def pier_layout(
    *,
    center_xy=(0.0, 0.0),
    z_top,
    diameter=PIER_DIAMETER,
    height=PIER_HEIGHT,
    rebar: RebarParams = None,
    bar_z_bottom=None,
    bar_z_top=None,
    bottom_leg=0.0,
    top_leg=0.0,
    name="Pier",
):
    """
    Pure-Python description of one pier (concrete + reinforcement).

    Args:
        center_xy:     (x, y) of the pier axis in the support frame.
        z_top:         Z of the pier top (= pier-cap soffit).
        diameter:      Pier diameter.
        height:        Pier height (pier-cap soffit to pile-cap top).
        rebar:         Reinforcement parameters.
        bar_z_bottom:  Z where longitudinal bars start (default: bottom cover).
        bar_z_top:     Z where longitudinal bars end (default: top cover).
        bottom_leg:    90 deg bend at the bar foot, pointing outwards into the
                       pile cap (L-bar anchorage); 0 -> straight.
        top_leg:       90 deg bend at the bar head, pointing inwards under the
                       pier-cap top steel; 0 -> straight.
        name:          Element name, also used as rebar host tag.

    Returns:
        dict with ``concrete`` (cylinder description) and ``bars`` (bar records).
    """
    rebar = rebar or RebarParams()
    cx, cy = center_xy
    R = diameter / 2.0
    z_bot = z_top - height

    concrete = {
        "type": "cylinder",
        "name": name,
        "base": (cx, cy, z_bot),
        "radius": R,
        "height": height,
        "volume_mm3": math.pi * R * R * height,
    }

    bars = []

    # Longitudinal bars on the cage circle
    r_cage = R - rebar.cover - rebar.tie_dia - rebar.main_dia / 2.0
    n_main = circular_bar_count(r_cage, rebar.main_spacing)
    zb = bar_z_bottom if bar_z_bottom is not None else z_bot + rebar.cover
    zt = bar_z_top if bar_z_top is not None else z_top - rebar.cover
    for k in range(n_main):
        a = 2 * math.pi * k / n_main
        ux, uy = math.cos(a), math.sin(a)
        x, y = cx + r_cage * ux, cy + r_cage * uy
        pts = [(x, y, zb), (x, y, zt)]
        if bottom_leg:
            pts.insert(0, (x + ux * bottom_leg, y + uy * bottom_leg, zb))
        if top_leg:
            pts.append((x - ux * top_leg, y - uy * top_leg, zt))
        bars.append(polyline_bar(pts, rebar.main_dia, "MAIN", name) if len(pts) > 2
                    else straight_bar(pts[0], pts[1], rebar.main_dia, "MAIN", name))

    # Circular ties over the pier height
    r_tie = R - rebar.cover - rebar.tie_dia / 2.0
    for z in stepped(z_bot + rebar.cover, z_top - rebar.cover, rebar.tie_spacing):
        bars.append(ring_bar((cx, cy, z), r_tie, rebar.tie_dia, "LIGATURE", name))

    return {"name": name, "concrete": concrete, "bars": bars,
            "n_main": n_main, "r_cage": r_cage}


def build_pier(layout):
    """
    Build OCC solids for a pier layout.

    Returns:
        dict with ``concrete`` (TopoDS_Shape) and ``rebars`` (list of shapes).
    """
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

    c = layout["concrete"]
    ax = gp_Ax2(gp_Pnt(*c["base"]), gp_Dir(0, 0, 1))
    solid = BRepPrimAPI_MakeCylinder(ax, c["radius"], c["height"]).Shape()
    return {"concrete": solid, "rebars": build_rebar_solids(layout["bars"])}
