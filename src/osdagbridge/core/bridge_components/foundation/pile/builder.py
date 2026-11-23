"""
Pile builder - bored cast-in-situ circular RCC piles in a rectangular grid.

Geometry
--------
``n_x`` x ``n_y`` piles (default 2 x 2 = 4) of diameter ``diameter`` and
length ``length`` hang from the pile-cap soffit, at ``spacing`` c/c (an
independent ``spacing_y`` may be given for the transverse direction).

Reinforcement
-------------
* Longitudinal bars: ``max(6, ceil(2*pi*r_cage / s_long))`` bars of
  ``d_main`` on the cage circle, extended up into the pile cap
  (``bar_z_top`` from the assembly) for anchorage.
* Circular ties / helix: rings of ``d_tie`` at ``s_tie`` c/c.
"""

import math

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, straight_bar, polyline_bar, ring_bar, stepped, circular_bar_count,
    build_rebar_solids,
)

# Default pile parameters (mm) - screening-task defaults
N_PILES_PER_CAP = 4      # arranged 2 x 2
N_PILES_X = 2
N_PILES_Y = 2
PILE_DIAMETER = 400
PILE_LENGTH = 5000
PILE_SPACING = 600       # centre-to-centre
PILE_EMBEDMENT = 50      # pile head projects into the cap (IS 2911-1-2)


def pile_grid_positions(center_xy=(0.0, 0.0), n_x=N_PILES_X, n_y=N_PILES_Y,
                        spacing=PILE_SPACING, spacing_y=None):
    """(x, y) centres of an n_x x n_y pile group centred on ``center_xy``."""
    sy = spacing if spacing_y is None else spacing_y
    cx, cy = center_xy
    xs = [cx + (i - (n_x - 1) / 2.0) * spacing for i in range(n_x)]
    ys = [cy + (j - (n_y - 1) / 2.0) * sy for j in range(n_y)]
    return [(x, y) for y in ys for x in xs]


def pile_layout(
    *,
    center_xy,
    z_top,
    diameter=PILE_DIAMETER,
    length=PILE_LENGTH,
    rebar: RebarParams = None,
    bar_z_top=None,
    top_leg=0.0,
    embedment=0.0,
    name="Pile",
):
    """
    Pure-Python description of one pile (concrete + reinforcement).

    ``z_top`` is the pile-cap soffit; the pile concrete projects
    ``embedment`` mm into the cap and ``length`` is measured below the soffit.
    ``top_leg`` adds an inward 90 deg bend at the bar heads inside the cap
    (inward so the hook stays clear of the cap edge at close pile spacing).
    """
    rebar = rebar or RebarParams()
    cx, cy = center_xy
    R = diameter / 2.0
    z_bot = z_top - length
    height = length + embedment

    concrete = {
        "type": "cylinder",
        "name": name,
        "base": (cx, cy, z_bot),
        "radius": R,
        "height": height,
        "embedment": embedment,
        "volume_mm3": math.pi * R * R * height,
    }

    bars = []
    r_cage = R - rebar.cover - rebar.tie_dia - rebar.main_dia / 2.0
    n_main = circular_bar_count(r_cage, rebar.main_spacing)
    zt = bar_z_top if bar_z_top is not None else z_top - rebar.cover
    for k in range(n_main):
        a = 2 * math.pi * k / n_main + math.pi / n_main   # offset avoids cap-mat bars
        ux, uy = math.cos(a), math.sin(a)
        x, y = cx + r_cage * ux, cy + r_cage * uy
        p0, p1 = (x, y, z_bot + rebar.cover), (x, y, zt)
        if top_leg:
            bars.append(polyline_bar([p0, p1, (x - ux * top_leg, y - uy * top_leg, zt)],
                                     rebar.main_dia, "MAIN", name))
        else:
            bars.append(straight_bar(p0, p1, rebar.main_dia, "MAIN", name))

    r_tie = R - rebar.cover - rebar.tie_dia / 2.0
    for z in stepped(z_bot + rebar.cover, z_top - rebar.cover, rebar.tie_spacing):
        bars.append(ring_bar((cx, cy, z), r_tie, rebar.tie_dia, "LIGATURE", name))

    return {"name": name, "concrete": concrete, "bars": bars, "n_main": n_main}


def build_pile(layout):
    """Build OCC solids for a pile layout."""
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

    c = layout["concrete"]
    ax = gp_Ax2(gp_Pnt(*c["base"]), gp_Dir(0, 0, 1))
    solid = BRepPrimAPI_MakeCylinder(ax, c["radius"], c["height"]).Shape()
    return {"concrete": solid, "rebars": build_rebar_solids(layout["bars"])}
