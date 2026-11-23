"""
Pile cap builder - rectangular RCC block that transfers the pier load to
the pile group.

Geometry
--------
Rectangular prism ``width`` (along X) x ``length`` (along Y) x ``depth``,
centred on the pier axis, with its top at the pier base.

Reinforcement
-------------
* Bottom mat (main tension steel over the piles): two orthogonal layers of
  ``d_main`` U-bars at <= ``s_long`` c/c, resting on the bottom cover, with
  both ends bent up the side faces to just below the top mat (full
  anchorage beyond the outer piles).
* Top mat (shrinkage / anti-crack steel): two orthogonal layers of
  ``d_tie`` bars at <= ``s_tie`` c/c under the top cover.
"""

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, straight_bar, polyline_bar, evenly_spaced, build_rebar_solids,
)

# Default pile-cap dimensions (mm) - screening-task defaults
PILE_CAP_LENGTH = 2200   # along Y (transverse)
PILE_CAP_WIDTH = 1200    # along X (longitudinal)
PILE_CAP_DEPTH = 600


def pile_cap_layout(
    *,
    center_xy=(0.0, 0.0),
    z_top,
    length=PILE_CAP_LENGTH,
    width=PILE_CAP_WIDTH,
    depth=PILE_CAP_DEPTH,
    rebar: RebarParams = None,
    embedded_volume_mm3=0.0,
    bottom_clearance=None,
    name="Pile Cap",
):
    """
    Pure-Python description of one pile cap (concrete + reinforcement).

    ``embedded_volume_mm3`` is the volume of pile heads projecting into the
    cap; it is subtracted to give the net concrete volume of the cap.
    ``bottom_clearance`` is the distance from the soffit to the underside of
    the bottom steel (default: cover); with pile heads projecting into the cap
    the bottom mat rests on the pile heads.
    """
    rebar = rebar or RebarParams()
    cx, cy = center_xy
    z_bot = z_top - depth
    x0, x1 = cx - width / 2.0, cx + width / 2.0
    y0, y1 = cy - length / 2.0, cy + length / 2.0

    concrete = {
        "type": "box",
        "name": name,
        "min": (x0, y0, z_bot),
        "size": (width, length, depth),
        "volume_mm3": width * length * depth - embedded_volume_mm3,     # net
        "gross_volume_mm3": width * length * depth,
    }

    c, dm, dt = rebar.cover, rebar.main_dia, rebar.tie_dia
    bars = []

    z_leg_top = z_top - c - 2 * dt - dm / 2.0    # U-bar legs stop under the top mat

    def _mat(z_first, dia, spacing, upward, u_bars=False):
        """Two orthogonal layers; ``upward`` selects stacking direction."""
        sgn = 1.0 if upward else -1.0
        for layer, z in (("A", z_first), ("B", z_first + sgn * dia)):
            # inset of the bar ends so the two layers' legs do not coincide
            e = c + dia / 2.0 + (dia if layer == "B" else 0.0)
            if layer == "A":     # bars along X, distributed over Y
                runs = [((x0 + e, y, z), (x1 - e, y, z))
                        for y in evenly_spaced(y0 + c + dia / 2.0, y1 - c - dia / 2.0, spacing)]
            else:                # bars along Y, distributed over X
                runs = [((x, y0 + e, z), (x, y1 - e, z))
                        for x in evenly_spaced(x0 + c + dia / 2.0, x1 - c - dia / 2.0, spacing)]
            for p, q in runs:
                if u_bars:
                    bars.append(polyline_bar([(p[0], p[1], z_leg_top), p, q,
                                              (q[0], q[1], z_leg_top)], dia, "MAIN", name))
                else:
                    bars.append(straight_bar(p, q, dia, "MAIN", name))

    clear = c if bottom_clearance is None else max(c, bottom_clearance)
    _mat(z_bot + clear + dm / 2.0, dm, rebar.main_spacing, upward=True, u_bars=True)  # bottom U-bars
    _mat(z_top - c - dt / 2.0, dt, rebar.tie_spacing, upward=False)               # top mat

    return {"name": name, "concrete": concrete, "bars": bars,
            "z_top": z_top, "z_bottom": z_bot}


def build_pile_cap(layout):
    """Build the OCC box and rebars for a pile-cap layout."""
    from OCC.Core.gp import gp_Pnt
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

    c = layout["concrete"]
    solid = BRepPrimAPI_MakeBox(gp_Pnt(*c["min"]), *c["size"]).Shape()
    return {"concrete": solid, "rebars": build_rebar_solids(layout["bars"])}
