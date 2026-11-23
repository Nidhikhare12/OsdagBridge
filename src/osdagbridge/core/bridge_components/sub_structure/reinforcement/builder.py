"""
Substructure reinforcement builder.

Shared reinforcement definitions and geometry helpers used by every concrete
substructure component (pier, pier cap, pile cap, pile).

The module is split in two layers so that the *same* bar geometry feeds both
the pythonOCC viewer and the IFC exporter:

1. **Layout layer (pure Python, no OCC)** - functions such as
   :func:`straight_bar`, :func:`ring_bar` and :func:`polygon_bar` return plain
   ``dict`` records ("bar records") holding the bar's centre-line path in
   millimetres.  The IFC exporter turns each record into an
   ``IfcReinforcingBar`` with an ``IfcSweptDiskSolid`` body.

2. **Solid layer (pythonOCC)** - :func:`make_bar_solid` converts a bar record
   into an OCC solid (cylinders for straight legs, a torus for circular ties).

Bar record keys
---------------
``role``      "MAIN" (longitudinal / main bars) or "LIGATURE" (ties, stirrups)
``dia``       nominal bar diameter (mm)
``path``      list of (x, y, z) centre-line points (mm).  For ties and
              stirrups the path goes once round the loop, back to the start
              and continues for a lap length (``tie_lap_length``) - i.e. it is
              an *open* polyline, which is how the bar is actually bent and is
              also what IFC swept-disk solids require.
``closed``    True for loops (stirrups / ties)
``ring``      optional ``{"center": (x, y, z), "radius": r}`` for circular ties
              (horizontal rings, axis = +Z)
``length``    developed centre-line length (mm) - used for BOQ / IFC BarLength
``host``      name of the concrete element that contains the bar
"""

import math
from dataclasses import dataclass


# Default reinforcement parameters (mm) - screening-task defaults

REBAR_MAIN_DIAMETER = 16          # main / longitudinal bar diameter
REBAR_SPACING_LONGITUDINAL = 150  # max c/c spacing of main bars
REBAR_TRANSVERSE_DIAMETER = 8     # ties / stirrups diameter
REBAR_SPACING_TRANSVERSE = 200    # c/c spacing of ties / stirrups
REBAR_COVER = 40                  # clear cover to outermost bar

RING_SEGMENTS = 24                # polyline facets used to describe a ring in IFC
TIE_LAP_FACTOR = 10               # lap / hook extension of closed ties = 10 d ...
TIE_LAP_MIN = 75                  # ... but not less than 75 mm (IS 13920 hook rule)

STEEL_DENSITY_KG_M3 = 7850.0      # IS 1786 reinforcement steel
REBAR_GRADE_FY = 500.0            # Fe 500 (IS 1786)
BEND_LEG_FACTOR = 12              # 90 deg bend leg = 12 d (standard L-bar) ...
BEND_ANCHORAGE_FACTOR = 8         # ... worth 8 d of anchorage (IS 456 cl. 26.2.2.1 b)

# Design bond stress for plain bars in tension, IS 456 cl. 26.2.1.1 (MPa);
# deformed bars: x 1.6.
TAU_BD_PLAIN = {20: 1.2, 25: 1.4, 30: 1.5, 35: 1.7, 40: 1.9}


@dataclass
class RebarParams:
    """Parametric reinforcement definition shared by all substructure parts."""

    main_dia: float = REBAR_MAIN_DIAMETER
    main_spacing: float = REBAR_SPACING_LONGITUDINAL
    tie_dia: float = REBAR_TRANSVERSE_DIAMETER
    tie_spacing: float = REBAR_SPACING_TRANSVERSE
    cover: float = REBAR_COVER


# ---------------------------------------------------------------------------
# Layout layer (pure Python)
# ---------------------------------------------------------------------------

def _path_length(path, closed=False):
    """Length of an (open) polyline path."""
    return sum(math.dist(a, b) for a, b in zip(path[:-1], path[1:]))


def tie_lap_length(dia):
    """Lap / hook extension for closed ties and stirrups."""
    return max(TIE_LAP_FACTOR * dia, TIE_LAP_MIN)


def _close_with_lap(corners, lap):
    """
    Walk round the loop ``corners`` back to the start, then continue along the
    loop for ``lap`` mm, returning an open polyline.
    """
    path = list(corners) + [corners[0]]
    remaining = lap
    i = 0
    n = len(corners)
    while remaining > 1e-9:
        a, b = corners[i % n], corners[(i + 1) % n]
        seg = math.dist(a, b)
        if seg >= remaining:
            t = remaining / seg
            path.append(tuple(pa + t * (pb - pa) for pa, pb in zip(a, b)))
            break
        path.append(b)
        remaining -= seg
        i += 1
    return path


def bend_leg_length(dia, available=None):
    """Leg of a 90 deg bend: 12 d, limited to the room ``available`` (if given)."""
    leg = BEND_LEG_FACTOR * dia
    if available is not None:
        leg = max(4 * dia, min(leg, available))   # never below IS 456 min bend extension 4 d
    return leg


def concrete_fck(grade):
    """'M35' -> 35.0 (defaults to 35)."""
    try:
        return float(str(grade).upper().replace("M", "").strip())
    except ValueError:
        return 35.0


def development_length(dia, fck=35.0, fy=REBAR_GRADE_FY):
    """
    Development length of a deformed bar in tension, IS 456 cl. 26.2.1:
        Ld = 0.87 fy phi / (4 tau_bd),  tau_bd = 1.6 x plain-bar value.
    """
    grades = sorted(TAU_BD_PLAIN)
    g = max([k for k in grades if k <= fck] or [grades[0]])
    tau_bd = TAU_BD_PLAIN[g] * 1.6
    return 0.87 * fy * dia / (4.0 * tau_bd)


def polyline_bar(points, dia, role="MAIN", host=""):
    """Bent bar along an open polyline (L-bars, U-bars, cranked bars)."""
    path = [tuple(map(float, p)) for p in points]
    return {
        "role": role, "dia": float(dia), "path": path, "closed": False,
        "length": _path_length(path), "host": host,
    }


def straight_bar(p1, p2, dia, role="MAIN", host=""):
    """Straight bar between two points."""
    path = [tuple(map(float, p1)), tuple(map(float, p2))]
    return {
        "role": role, "dia": float(dia), "path": path, "closed": False,
        "length": _path_length(path, False), "host": host,
    }


def ring_bar(center, radius, dia, role="LIGATURE", host=""):
    """Horizontal circular tie (axis +Z) of centre-line radius ``radius``."""
    cx, cy, cz = map(float, center)
    corners = [
        (cx + radius * math.cos(2 * math.pi * k / RING_SEGMENTS),
         cy + radius * math.sin(2 * math.pi * k / RING_SEGMENTS),
         cz)
        for k in range(RING_SEGMENTS)
    ]
    lap = tie_lap_length(dia)
    return {
        "role": role, "dia": float(dia), "path": _close_with_lap(corners, lap),
        "closed": True, "ring": {"center": (cx, cy, cz), "radius": float(radius)},
        "length": 2 * math.pi * radius + lap, "host": host,
    }


def polygon_bar(points, dia, role="LIGATURE", host=""):
    """Closed polygonal stirrup through ``points`` (centre-line corners), lapped."""
    corners = [tuple(map(float, p)) for p in points]
    path = _close_with_lap(corners, tie_lap_length(dia))
    return {
        "role": role, "dia": float(dia), "path": path, "closed": True,
        "length": _path_length(path), "host": host,
    }


def evenly_spaced(start, end, max_spacing):
    """Positions from ``start`` to ``end`` (inclusive) with spacing <= max_spacing."""
    span = end - start
    if span <= 0:
        return [(start + end) / 2.0]
    n_gaps = max(1, math.ceil(span / max_spacing - 1e-9))
    return [start + span * i / n_gaps for i in range(n_gaps + 1)]


def stepped(start, end, spacing):
    """Positions from ``start`` at exactly ``spacing`` while <= ``end``."""
    if end < start:
        return [(start + end) / 2.0]
    n = int(math.floor((end - start) / spacing + 1e-9)) + 1
    return [start + i * spacing for i in range(n)]


def circular_bar_count(cage_radius, spacing, minimum=6):
    """Number of longitudinal bars on a circle (IS 456 cl. 26.5.3.1: >= 6)."""
    return max(minimum, math.ceil(2 * math.pi * cage_radius / spacing))


def inset_convex_polygon(points, d):
    """
    Offset a convex, counter-clockwise 2D polygon inwards by distance ``d``.

    Each edge is moved along its inward normal and consecutive offset edges
    are intersected to obtain the new corners.
    """
    n = len(points)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = points[i], points[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        le = math.hypot(ex, ey)
        nx, ny = -ey / le, ex / le          # inward normal for a CCW polygon
        lines.append(((x1 + nx * d, y1 + ny * d), (ex, ey)))

    out = []
    for i in range(n):
        (p, r) = lines[i - 1]
        (q, s) = lines[i]
        cross = r[0] * s[1] - r[1] * s[0]
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / cross
        out.append((p[0] + t * r[0], p[1] + t * r[1]))
    return out


def polygon_half_width_at(points, z):
    """Half of the horizontal chord of a convex polygon (x, z) at height z."""
    xs = []
    n = len(points)
    for i in range(n):
        (x1, z1), (x2, z2) = points[i], points[(i + 1) % n]
        if (z1 - z) * (z2 - z) <= 0 and z1 != z2:
            t = (z - z1) / (z2 - z1)
            xs.append(x1 + t * (x2 - x1))
    if len(xs) < 2:
        return 0.0
    return (max(xs) - min(xs)) / 2.0


def bar_mass_kg(bar):
    """Mass of one bar record in kg."""
    area_m2 = math.pi * (bar["dia"] / 1000.0) ** 2 / 4.0
    return area_m2 * bar["length"] / 1000.0 * STEEL_DENSITY_KG_M3


def summarize_bars(bars):
    """Group bars by (host, role, dia) -> count, total length (m), mass (kg)."""
    summary = {}
    for b in bars:
        key = (b["host"], b["role"], b["dia"])
        s = summary.setdefault(key, {"count": 0, "length_m": 0.0, "mass_kg": 0.0})
        s["count"] += 1
        s["length_m"] += b["length"] / 1000.0
        s["mass_kg"] += bar_mass_kg(b)
    return summary


# ---------------------------------------------------------------------------
# Solid layer (pythonOCC)
# ---------------------------------------------------------------------------

def _cylinder_between(p1, p2, radius, extend=0.0):
    """OCC cylinder of ``radius`` whose axis runs from p1 to p2 (+extend each end)."""
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

    v = [b - a for a, b in zip(p1, p2)]
    length = math.sqrt(sum(c * c for c in v))
    if length < 1e-6:
        return None
    u = [c / length for c in v]
    start = [a - c * extend for a, c in zip(p1, u)]
    ax = gp_Ax2(gp_Pnt(*start), gp_Dir(*u))
    return BRepPrimAPI_MakeCylinder(ax, radius, length + 2 * extend).Shape()


def make_bar_solid(bar):
    """
    Convert a bar record into an OCC solid (or compound of solids).

    * straight bars        -> one cylinder
    * circular ties        -> torus
    * stirrups / bent bars -> one cylinder per leg, legs extended by d/2 so
                              that the bends close neatly
    """
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeTorus

    r = bar["dia"] / 2.0
    if bar.get("ring"):
        c = bar["ring"]["center"]
        ax = gp_Ax2(gp_Pnt(*c), gp_Dir(0, 0, 1))
        return BRepPrimAPI_MakeTorus(ax, bar["ring"]["radius"], r).Shape()

    pts = bar["path"]           # already an open polyline (loops include their lap)
    legs = []
    bent = len(pts) > 2         # extend legs by r so that bends close neatly
    for a, b in zip(pts[:-1], pts[1:]):
        leg = _cylinder_between(a, b, r, extend=r if bent else 0.0)
        if leg is not None:
            legs.append(leg)
    if len(legs) == 1:
        return legs[0]
    return make_compound(legs)


def make_compound(shapes):
    """Pack a list of OCC shapes into a single TopoDS_Compound."""
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.TopoDS import TopoDS_Compound

    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    for s in shapes:
        if s is not None:
            builder.Add(comp, s)
    return comp


def build_rebar_solids(bars):
    """Return OCC solids for a list of bar records."""
    return [make_bar_solid(b) for b in bars]
