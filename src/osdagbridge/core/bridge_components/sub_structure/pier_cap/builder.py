"""
Pier cap builder - hammerhead / trapezoidal RCC cap beam.

Geometry
--------
Longitudinal section (X-Z): a trapezoid ``top_width`` wide at the bearing
seat tapering to ``bottom_width`` at the soffit.

Transverse elevation (Y-Z), style ``"HAMMERHEAD"`` (default):

        y=-L/2                                            y=+L/2
          ______________________________________________
         |                                              |  end_depth
          \\____                                    ____/
                \\_______   full depth   ________/        depth
                         |___ core ___|
                            |  pier  |

The cap has its full ``depth`` over the pier zone (``core_length``) and the
cantilevers taper linearly to ``end_depth`` at the tips.  Style
``"TRAPEZOIDAL"`` keeps the full depth over the whole length.

The solid is described as a ruled loft through trapezoidal sections at
"stations" along Y.  Because the longitudinal faces are planes
(x = w(z)/2 with w linear in z) and the soffit is piecewise linear in y,
every face of the loft is planar - the OCC solid (BRepOffsetAPI_ThruSections,
ruled) and the IFC solid (IfcFacetedBrep) are therefore exact.

Local frame: support frame (origin on the cap top surface at the support
line, +Y along the support line).

Reinforcement
-------------
* Stirrups (d_tie @ s_tie): closed trapezoidal loops following the *local*
  section depth, inset by cover + d_tie/2, closed with a lap.
* Top main bars (hogging over the pier): straight along +Y with 90 deg bends
  down at both tips.
* Bottom main bars: follow the hammerhead soffit (bent at the taper
  stations) with 90 deg bends up at both tips.
"""

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, polyline_bar, polygon_bar, stepped, evenly_spaced,
    inset_convex_polygon, polygon_half_width_at, build_rebar_solids, bend_leg_length,
)

# Default pier-cap dimensions (mm) - screening-task defaults
PIER_CAP_TOP_WIDTH = 3000
PIER_CAP_BOTTOM_WIDTH = 1200
PIER_CAP_DEPTH = 600
PIER_CAP_LENGTH = None           # None -> match the total deck width (set by the assembly)
PIER_CAP_DEFAULT_LENGTH = 10000  # fallback when no deck width is known
PIER_CAP_STYLE = "HAMMERHEAD"    # or "TRAPEZOIDAL"
PIER_CAP_END_DEPTH_RATIO = 0.5   # cantilever tip depth = 0.5 x depth
PIER_CAP_HAUNCH_OFFSET = 300     # taper starts this far beyond the outer pier face


def width_at_depth(top_width, bottom_width, depth, d):
    """Section width at a distance ``d`` below the cap top (linear taper)."""
    return top_width - (top_width - bottom_width) * d / depth


def section_profile(top_width, bottom_width, depth, local_depth, z_top=0.0):
    """CCW trapezoid (x, z) of the cap cut to ``local_depth`` below z_top."""
    wb = width_at_depth(top_width, bottom_width, depth, local_depth)
    zb = z_top - local_depth
    return [(-wb / 2.0, zb), (wb / 2.0, zb), (top_width / 2.0, z_top), (-top_width / 2.0, z_top)]


def pier_cap_profile(top_width, bottom_width, depth, z_top=0.0):
    """Full-depth section (kept for backwards compatibility)."""
    return section_profile(top_width, bottom_width, depth, depth, z_top)


def depth_at(y, *, length, depth, end_depth, core_length):
    """Local cap depth at transverse position y (hammerhead soffit)."""
    half, core = length / 2.0, core_length / 2.0
    a = abs(y)
    if a <= core or half <= core:
        return depth
    return depth - (depth - end_depth) * (a - core) / (half - core)


def _section_area(top_width, bottom_width, depth, d):
    return (top_width + width_at_depth(top_width, bottom_width, depth, d)) / 2.0 * d


def pier_cap_layout(
    *,
    z_top=0.0,
    top_width=PIER_CAP_TOP_WIDTH,
    bottom_width=PIER_CAP_BOTTOM_WIDTH,
    depth=PIER_CAP_DEPTH,
    length=PIER_CAP_DEFAULT_LENGTH,
    style=PIER_CAP_STYLE,
    end_depth=None,
    core_length=None,
    rebar: RebarParams = None,
    name="Pier Cap",
):
    """Pure-Python description of the pier cap (concrete + reinforcement)."""
    rebar = rebar or RebarParams()
    hammer = str(style).upper() == "HAMMERHEAD"
    end_depth = depth * PIER_CAP_END_DEPTH_RATIO if end_depth is None else end_depth
    if not hammer:
        end_depth = depth
    core_length = min(length, core_length if core_length else bottom_width)

    half, core = length / 2.0, core_length / 2.0
    ys = [-half, -core, core, half] if hammer and core < half else [-half, half]
    d_of = lambda y: depth_at(y, length=length, depth=depth, end_depth=end_depth,
                              core_length=core_length)
    stations = [{"y": y, "depth": d_of(y),
                 "profile_xz": section_profile(top_width, bottom_width, depth, d_of(y), z_top)}
                for y in ys]

    # Exact volume: section area is quadratic in y -> Simpson per segment
    volume = 0.0
    for s0, s1 in zip(stations[:-1], stations[1:]):
        ym = (s0["y"] + s1["y"]) / 2.0
        a0 = _section_area(top_width, bottom_width, depth, s0["depth"])
        am = _section_area(top_width, bottom_width, depth, d_of(ym))
        a1 = _section_area(top_width, bottom_width, depth, s1["depth"])
        volume += (s1["y"] - s0["y"]) / 6.0 * (a0 + 4 * am + a1)

    concrete = {
        "type": "lofted_sections",
        "name": name,
        "style": "HAMMERHEAD" if hammer else "TRAPEZOIDAL",
        "stations": stations,
        "profile_xz": stations[len(stations) // 2]["profile_xz"],   # full-depth section
        "y_min": -half, "y_max": half,
        "length": length, "depth": depth, "end_depth": end_depth, "core_length": core_length,
        "top_width": top_width, "bottom_width": bottom_width,
        "z_top": z_top,
        "max_area": _section_area(top_width, bottom_width, depth, depth),
        "volume_mm3": volume,
    }

    bars = []
    c, dt, dm = rebar.cover, rebar.tie_dia, rebar.main_dia

    # --- Stirrups: follow the local section depth ---
    y0, y1 = -half + c + dt / 2.0, half - c - dt / 2.0
    for y in stepped(y0, y1, rebar.tie_spacing):
        prof = section_profile(top_width, bottom_width, depth, d_of(y), z_top)
        loop = inset_convex_polygon(prof, c + dt / 2.0)
        bars.append(polygon_bar([(x, y, z) for x, z in loop], dt, "LIGATURE", name))

    # --- Main bars ---
    y_end = half - c - dt - dm / 2.0          # bend position, inside the end stirrup
    d_tip = d_of(y_end)
    leg = bend_leg_length(dm, d_tip - 2 * (c + dt) - 2 * dm)
    z_top_bar = z_top - c - dt - dm / 2.0

    def z_bot_bar(y):
        return z_top - d_of(y) + c + dt + dm / 2.0

    # top layer: across the top width (constant), bent down at both tips
    inner_full = inset_convex_polygon(section_profile(top_width, bottom_width, depth, depth, z_top), c + dt)
    half_top = polygon_half_width_at(inner_full, z_top_bar) - dm / 2.0
    for x in evenly_spaced(-half_top, half_top, rebar.main_spacing):
        bars.append(polyline_bar([(x, -y_end, z_top_bar - leg), (x, -y_end, z_top_bar),
                                  (x, y_end, z_top_bar), (x, y_end, z_top_bar - leg)],
                                 dm, "MAIN", name))

    # bottom layer: across the narrowest soffit (full depth), following the soffit
    half_bot = polygon_half_width_at(inner_full, z_bot_bar(0.0)) - dm / 2.0
    knots = [-y_end] + [y for y in ys if abs(y) < y_end] + [y_end]
    for x in evenly_spaced(-half_bot, half_bot, rebar.main_spacing):
        pts = [(x, -y_end, z_bot_bar(-y_end) + leg)]
        pts += [(x, y, z_bot_bar(y)) for y in knots]
        pts.append((x, y_end, z_bot_bar(y_end) + leg))
        bars.append(polyline_bar(pts, dm, "MAIN", name))

    return {"name": name, "concrete": concrete, "bars": bars}


def build_pier_cap(layout):
    """Build OCC solids: ruled loft through the section stations, plus rebars."""
    from OCC.Core.gp import gp_Pnt
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
    from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections

    c = layout["concrete"]
    loft = BRepOffsetAPI_ThruSections(True, True)     # solid, ruled
    for st in c["stations"]:
        poly = BRepBuilderAPI_MakePolygon()
        for x, z in st["profile_xz"]:
            poly.Add(gp_Pnt(x, st["y"], z))
        poly.Close()
        loft.AddWire(poly.Wire())
    loft.Build()
    return {"concrete": loft.Shape(), "rebars": build_rebar_solids(layout["bars"])}
