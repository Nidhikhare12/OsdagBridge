"""
Pedestal builder - plain RCC bearing pedestals on the pier cap.

One rectangular pedestal is placed under every girder line, on the pier-cap
top surface.  The gap left between the pedestal top and the girder soffit is
the bearing thickness (the bearing itself is shown by the existing support
glyphs of the superstructure).

Reinforcement: a mesh of ``d_tie`` bars at ``PEDESTAL_MESH_SPACING`` c/c in
both directions near the top and the bottom of the pedestal (bursting steel
under the bearing), plus four corner dowels of ``d_main`` anchored into the
pier cap.

Local frame: support frame (origin on the pier-cap top surface).
"""

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, straight_bar, evenly_spaced, bend_leg_length, build_rebar_solids,
)

# Default pedestal dimensions (mm)
PEDESTAL_LENGTH = 600       # along X (longitudinal)
PEDESTAL_WIDTH = 600        # along Y (transverse)
PEDESTAL_HEIGHT = 150
BEARING_THICKNESS = 100     # clear gap pedestal top -> girder soffit
PEDESTAL_MESH_SPACING = 100 # bursting-steel mesh spacing


def pedestal_layout(*, center_xy, z_bottom=0.0, length=PEDESTAL_LENGTH,
                    width=PEDESTAL_WIDTH, height=PEDESTAL_HEIGHT, rebar: RebarParams = None,
                    dowel_depth=None, name="Pedestal"):
    """
    Pure-Python description of one pedestal (axis-aligned box) and its steel.

    ``dowel_depth`` is how far the corner dowels go below the pedestal into
    the pier cap (default 12 d).
    """
    rebar = rebar or RebarParams()
    cx, cy = center_xy
    x0, x1 = cx - length / 2.0, cx + length / 2.0
    y0, y1 = cy - width / 2.0, cy + width / 2.0
    z1 = z_bottom + height
    c, dt, dm = rebar.cover, rebar.tie_dia, rebar.main_dia
    bars = []

    # Two meshes (bottom and top), each two orthogonal layers
    for z_a, sgn in ((z_bottom + c + dt / 2.0, 1.0), (z1 - c - dt / 2.0, -1.0)):
        z_b = z_a + sgn * dt
        for y in evenly_spaced(y0 + c + dt / 2.0, y1 - c - dt / 2.0, PEDESTAL_MESH_SPACING):
            bars.append(straight_bar((x0 + c, y, z_a), (x1 - c, y, z_a), dt, "MAIN", name))
        for x in evenly_spaced(x0 + c + dt / 2.0, x1 - c - dt / 2.0, PEDESTAL_MESH_SPACING):
            bars.append(straight_bar((x, y0 + c, z_b), (x, y1 - c, z_b), dt, "MAIN", name))

    # Corner dowels into the pier cap
    depth_below = bend_leg_length(dm) if dowel_depth is None else dowel_depth
    off = c + 2 * dt + dm / 2.0
    for x in (x0 + off, x1 - off):
        for y in (y0 + off, y1 - off):
            bars.append(straight_bar((x, y, z_bottom - depth_below), (x, y, z1 - c - 2 * dt - dm / 2.0),
                                     dm, "MAIN", name))

    return {
        "name": name,
        "concrete": {
            "type": "box",
            "name": name,
            "min": (x0, y0, z_bottom),
            "size": (length, width, height),
            "volume_mm3": length * width * height,
        },
        "bars": bars,
    }


def build_pedestal(layout):
    """Build the OCC box for a pedestal layout."""
    from OCC.Core.gp import gp_Pnt
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

    c = layout["concrete"]
    solid = BRepPrimAPI_MakeBox(gp_Pnt(*c["min"]), *c["size"]).Shape()
    return {"concrete": solid, "rebars": build_rebar_solids(layout["bars"])}
