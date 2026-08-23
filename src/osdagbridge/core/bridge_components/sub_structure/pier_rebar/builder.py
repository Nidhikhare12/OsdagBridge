"""
Reinforcement (Rebar) Geometry Builder
=======================================

Builds visual reinforcement cages for bridge substructure components.
Rebar is modelled as cylinders for visual clarity (not structural simulation).
Returned shapes are separate compounds from the concrete so the display layer
can independently set colour/opacity.

Components covered:
  1. **Pier rebar**: vertical main bars around the circular perimeter +
     horizontal tie rings (torus) at regular spacing up the height.
  2. **Pile rebar**: same circular cage logic for each pile.
  3. **Pile cap rebar**: two orthogonal grids of horizontal bars near top
     and bottom faces.
  4. **Pier cap rebar**: same orthogonal grid logic as pile cap.

Pattern:
  - Same module-level defaults, private helpers, and ``build_*`` function
    as other substructure builders.
  - Returns raw TopoDS_Shapes; no viewer, no fusion, no colour.

Units: mm throughout.
Coordinate system (from  .md):
  X = longitudinal, Y = transverse, Z = vertical.
  Origin = centre of span at deck level (Z = 0).
  Substructure sits below Z = 0.
"""

import math

from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeTorus
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# ---------------------------------------------------------------------------
# Module-level defaults (mm) — match user spec
# ---------------------------------------------------------------------------
DEFAULT_MAIN_BAR_DIA: float        = 16.0   # mm — main bar diameter
DEFAULT_REBAR_SPACING_LONG: float  = 150.0  # mm — longitudinal bar spacing
DEFAULT_TRANS_BAR_DIA: float       = 8.0    # mm — transverse / tie bar diameter
DEFAULT_REBAR_SPACING_TRANS: float = 200.0  # mm — transverse bar / tie spacing
DEFAULT_COVER: float               = 40.0   # mm — clear cover to outer face of tie


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_vertical_bar(cx, cy, z_base, bar_radius, bar_length):
    """
    Create a single vertical cylindrical bar extending in +Z.

    Args:
        cx (float): X-coordinate of bar axis (mm).
        cy (float): Y-coordinate of bar axis (mm).
        z_base (float): Z of the bar bottom (mm).
        bar_radius (float): Bar cross-section radius (mm).
        bar_length (float): Bar length (mm).

    Returns:
        TopoDS_Shape: Vertical cylinder.
    """
    origin = gp_Pnt(float(cx), float(cy), float(z_base))
    ax = gp_Ax2(origin, gp_Dir(0.0, 0.0, 1.0))
    return BRepPrimAPI_MakeCylinder(ax, float(bar_radius), float(bar_length)).Shape()


def _make_horizontal_bar_x(cx, cy, cz, bar_radius, length):
    """
    Create a short horizontal bar running in the X direction.

    Args:
        cx (float): X of bar centre (mm).
        cy (float): Y of bar centre (mm).
        cz (float): Z of bar centre (mm).
        bar_radius (float): Cross-section radius (mm).
        length (float): Bar length in X (mm).

    Returns:
        TopoDS_Shape: Horizontal cylinder along X.
    """
    origin = gp_Pnt(float(cx - length / 2.0), float(cy), float(cz))
    ax = gp_Ax2(origin, gp_Dir(1.0, 0.0, 0.0))
    return BRepPrimAPI_MakeCylinder(ax, float(bar_radius), float(length)).Shape()


def _make_horizontal_bar_y(cx, cy, cz, bar_radius, length):
    """
    Create a short horizontal bar running in the Y direction.

    Args:
        cx (float): X of bar centre (mm).
        cy (float): Y of bar centre (mm).
        cz (float): Z of bar centre (mm).
        bar_radius (float): Cross-section radius (mm).
        length (float): Bar length in Y (mm).

    Returns:
        TopoDS_Shape: Horizontal cylinder along Y.
    """
    origin = gp_Pnt(float(cx), float(cy - length / 2.0), float(cz))
    ax = gp_Ax2(origin, gp_Dir(0.0, 1.0, 0.0))
    return BRepPrimAPI_MakeCylinder(ax, float(bar_radius), float(length)).Shape()


def _make_tie_ring(cx, cy, z_center, ring_radius, bar_radius):
    """
    Create a horizontal circular tie ring modelled as a torus.

    Args:
        cx (float): X-coordinate of ring axis (mm).
        cy (float): Y-coordinate of ring axis (mm).
        z_center (float): Z-coordinate of ring centre (mm).
        ring_radius (float): Major radius — from torus axis to tube centre (mm).
        bar_radius (float): Minor radius — cross-section radius of the bar (mm).

    Returns:
        TopoDS_Shape: Torus solid representing the tie ring.
    """
    origin = gp_Pnt(float(cx), float(cy), float(z_center))
    ax = gp_Ax2(origin, gp_Dir(0.0, 0.0, 1.0))
    return BRepPrimAPI_MakeTorus(ax, float(ring_radius), float(bar_radius)).Shape()


# ---------------------------------------------------------------------------
# Sub-helpers for rebar grids
# ---------------------------------------------------------------------------

def _make_slab_rebar_grid(
    cx, cy,
    z_face,
    len_x, len_y,
    main_bar_dia, main_spacing_long, main_spacing_trans,
    trans_bar_dia,
    cover,
    above_face=True,
):
    """
    Build two orthogonal layers of horizontal rebar near one face of a slab.

    Layer 1 (bottom of the face layer): bars running in X direction, spaced
    at ``main_spacing_trans`` along Y.
    Layer 2 (above layer 1): bars running in Y direction, spaced at
    ``main_spacing_long`` along X.

    Args:
        cx (float): Slab centre X (mm).
        cy (float): Slab centre Y (mm).
        z_face (float): Z of the slab face (top or bottom, mm).
        len_x (float): Slab dimension in X (mm).
        len_y (float): Slab dimension in Y (mm).
        main_bar_dia (float): Main bar diameter (mm).
        main_spacing_long (float): Bar spacing in longitudinal direction (mm).
        main_spacing_trans (float): Bar spacing in transverse direction (mm).
        trans_bar_dia (float): Transverse bar diameter (mm).
        cover (float): Clear cover to outermost bar face (mm).
        above_face (bool): True → bars placed above z_face (top-face mat),
            False → bars placed below z_face (bottom-face mat).

    Returns:
        list[TopoDS_Shape]: List of cylindrical bar shapes.
    """
    shapes = []
    bar_r = main_bar_dia / 2.0
    trans_r = trans_bar_dia / 2.0

    # Determine Z offsets (inward from the face)
    sign = 1.0 if above_face else -1.0
    z_layer1 = z_face + sign * (cover + bar_r)            # first layer (X-bars)
    z_layer2 = z_face + sign * (cover + main_bar_dia + trans_r)  # second layer (Y-bars)

    # X-direction bars, distributed along Y
    y_start = cy - len_y / 2.0 + cover + bar_r
    y_end   = cy + len_y / 2.0 - cover - bar_r
    y_pos = y_start
    while y_pos <= y_end + 1e-3:
        shapes.append(_make_horizontal_bar_x(cx, y_pos, z_layer1, bar_r, len_x - 2 * cover))
        y_pos += main_spacing_trans

    # Y-direction bars, distributed along X
    x_start = cx - len_x / 2.0 + cover + trans_r
    x_end   = cx + len_x / 2.0 - cover - trans_r
    x_pos = x_start
    while x_pos <= x_end + 1e-3:
        shapes.append(_make_horizontal_bar_y(x_pos, cy, z_layer2, trans_r, len_y - 2 * cover))
        x_pos += main_spacing_long

    return shapes


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_pier_rebar(
    *,
    pier_height: float,
    pier_diameter: float,
    pier_x_positions: list = None,
    pier_y_offsets: list = None,
    pier_base_z: float = -3600.0,
    cover: float = DEFAULT_COVER,
    main_bar_diameter: float = DEFAULT_MAIN_BAR_DIA,
    num_main_bars: int = 12,
    tie_diameter: float = DEFAULT_TRANS_BAR_DIA,
    tie_spacing: float = DEFAULT_REBAR_SPACING_TRANS,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
    num_piers: int = 2,
    pier_spacing: float = 2000.0,
):
    """
    Build the reinforcement cage for circular RCC pier shafts.

    Generates:
    - **Main bars**: vertical cylinders arranged in a ring at radius
      (pier_diameter/2 − cover − tie_diameter − main_bar_diameter/2),
      offset inward from the pier surface.
    - **Tie rings**: horizontal torus shapes at ``tie_spacing`` intervals
      up the pier height.

    Coordinate system ( .md):
      X = longitudinal (span), Y = transverse, Z = vertical.

    Args:
        pier_height (float): Height of the pier shaft (mm).
        pier_diameter (float): Outer diameter of the pier (mm).
        pier_x_positions (list[float] | None): X-coordinates (span, mm) of
            each support.  Auto-derived if None.
        pier_y_offsets (list[float] | None): Y-offsets of each pier column
            within each support group (mm).  Derived from num_piers /
            pier_spacing if None.
        pier_base_z (float): Z of the pier base (mm).
        cover (float): Clear cover to outer face of tie bar (mm).
        main_bar_diameter (float): Diameter of each main vertical bar (mm).
        num_main_bars (int): Number of main bars around the perimeter.
        tie_diameter (float): Diameter of each tie/stirrup bar (mm).
        tie_spacing (float): Centre-to-centre spacing of tie rings (mm).
        span_length_L (float): Total span (mm); used to derive
            ``pier_x_positions`` when None.
        num_supports (int): Support count; used only when
            ``pier_x_positions`` is None.
        num_piers (int): Pier columns per support; used to derive
            ``pier_y_offsets`` when that parameter is None.
        pier_spacing (float): Y c/c spacing between pier columns (mm).

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pier_rebar": [TopoDS_Shape, ...]}``.
            Vertical bars and tie rings in a single flat list.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [i * step for i in range(n)]

    if pier_y_offsets is None:
        total_spread = (num_piers - 1) * pier_spacing
        pier_y_offsets = [-total_spread / 2.0 + i * pier_spacing for i in range(num_piers)]

    bar_radius = main_bar_diameter / 2.0
    tie_radius = tie_diameter / 2.0

    # Ring radius to the main bar centreline
    main_ring_radius = (pier_diameter / 2.0) - cover - tie_diameter - bar_radius
    main_ring_radius = max(main_ring_radius, bar_radius)  # safety floor

    # Tie ring: radius to the tie bar centreline
    tie_ring_radius = (pier_diameter / 2.0) - cover - tie_radius
    tie_ring_radius = max(tie_ring_radius, tie_radius)

    rebar_shapes = []

    for x_pos in pier_x_positions:
        for y_off in pier_y_offsets:
            # X = span position, Y = transverse column offset
            # --- Main vertical bars ---
            for k in range(num_main_bars):
                angle = 2.0 * math.pi * k / num_main_bars
                bx = x_pos + main_ring_radius * math.cos(angle)
                by = y_off + main_ring_radius * math.sin(angle)
                rebar_shapes.append(
                    _make_vertical_bar(bx, by, pier_base_z, bar_radius, pier_height)
                )

            # --- Horizontal tie rings ---
            z_start = pier_base_z + cover + tie_radius
            z_end   = pier_base_z + pier_height - cover - tie_radius
            z_tie = z_start
            while z_tie <= z_end + 1e-3:
                rebar_shapes.append(
                    _make_tie_ring(x_pos, y_off, z_tie, tie_ring_radius, tie_radius)
                )
                z_tie += tie_spacing

    return {"pier_rebar": rebar_shapes}


def build_pile_cap_rebar(
    *,
    cap_len_x: float = 2200.0,
    cap_len_y: float = 1200.0,
    cap_thickness: float = 600.0,
    cap_top_z: float = -4200.0,
    pier_x_positions: list = None,
    pier_y_center: float = 0.0,
    main_bar_diameter: float = DEFAULT_MAIN_BAR_DIA,
    trans_bar_diameter: float = DEFAULT_TRANS_BAR_DIA,
    spacing_long: float = DEFAULT_REBAR_SPACING_LONG,
    spacing_trans: float = DEFAULT_REBAR_SPACING_TRANS,
    cover: float = DEFAULT_COVER,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build two orthogonal grids of horizontal rebar near the top and bottom
    faces of each rectangular pile cap.

    Args:
        cap_len_x (float): Longitudinal length of pile cap (mm).
        cap_len_y (float): Transverse width of pile cap (mm).
        cap_thickness (float): Vertical thickness of pile cap (mm).
        cap_top_z (float): Z of the pile cap top face (mm).
        pier_x_positions (list[float] | None): X-coordinates of supports (mm).
        pier_y_center (float): Y-coordinate of pile cap centre (mm).
        main_bar_diameter (float): Main bar diameter (mm).
        trans_bar_diameter (float): Transverse bar diameter (mm).
        spacing_long (float): Longitudinal bar spacing (mm).
        spacing_trans (float): Transverse bar spacing (mm).
        cover (float): Clear cover (mm).
        span_length_L (float): Total bridge span (mm).
        num_supports (int): Number of intermediate supports.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pile_cap_rebar": [TopoDS_Shape, ...]}``.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [i * step for i in range(n)]

    z_bottom = cap_top_z - cap_thickness

    shapes = []
    for x_pos in pier_x_positions:
        # Top face mat (below top face)
        shapes += _make_slab_rebar_grid(
            x_pos, pier_y_center, cap_top_z,
            cap_len_x, cap_len_y,
            main_bar_diameter, spacing_long, spacing_trans,
            trans_bar_diameter, cover,
            above_face=False,
        )
        # Bottom face mat (above bottom face)
        shapes += _make_slab_rebar_grid(
            x_pos, pier_y_center, z_bottom,
            cap_len_x, cap_len_y,
            main_bar_diameter, spacing_long, spacing_trans,
            trans_bar_diameter, cover,
            above_face=True,
        )

    return {"pile_cap_rebar": shapes}


def build_pier_cap_rebar(
    *,
    cap_top_width: float = 3000.0,
    cap_depth: float = 600.0,
    cap_height: float = 600.0,
    cap_top_z: float = 0.0,
    pier_x_positions: list = None,
    main_bar_diameter: float = DEFAULT_MAIN_BAR_DIA,
    trans_bar_diameter: float = DEFAULT_TRANS_BAR_DIA,
    spacing_long: float = DEFAULT_REBAR_SPACING_LONG,
    spacing_trans: float = DEFAULT_REBAR_SPACING_TRANS,
    cover: float = DEFAULT_COVER,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build orthogonal rebar grids near top and bottom faces of each pier cap.

    Args:
        cap_top_width (float): Transverse width of the cap (use top width, mm).
        cap_depth (float): Longitudinal depth of the cap (mm).
        cap_height (float): Vertical height of the cap (mm).
        cap_top_z (float): Z of the cap top face (mm).
        pier_x_positions (list[float] | None): X-coordinates of supports (mm).
        main_bar_diameter (float): Main bar diameter (mm).
        trans_bar_diameter (float): Transverse bar diameter (mm).
        spacing_long (float): Longitudinal bar spacing (mm).
        spacing_trans (float): Transverse bar spacing (mm).
        cover (float): Clear cover (mm).
        span_length_L (float): Total bridge span (mm).
        num_supports (int): Number of intermediate supports.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pier_cap_rebar": [TopoDS_Shape, ...]}``.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [i * step for i in range(n)]

    z_top = float(cap_top_z)
    z_bottom = z_top - float(cap_height)

    shapes = []
    for x_pos in pier_x_positions:
        shapes += _make_slab_rebar_grid(
            x_pos, 0.0, z_top,
            cap_depth, cap_top_width,
            main_bar_diameter, spacing_long, spacing_trans,
            trans_bar_diameter, cover,
            above_face=False,
        )
        shapes += _make_slab_rebar_grid(
            x_pos, 0.0, z_bottom,
            cap_depth, cap_top_width,
            main_bar_diameter, spacing_long, spacing_trans,
            trans_bar_diameter, cover,
            above_face=True,
        )

    return {"pier_cap_rebar": shapes}


def build_pile_rebar(
    *,
    pile_diameter: float = 400.0,
    pile_length: float = 5000.0,
    pile_rows: int = 2,
    pile_cols: int = 2,
    pile_spacing_x: float = 600.0,
    pile_spacing_y: float = 600.0,
    pile_top_z: float = -4800.0,
    pier_x_positions: list = None,
    pier_y_center: float = 0.0,
    cover: float = DEFAULT_COVER,
    main_bar_diameter: float = DEFAULT_MAIN_BAR_DIA,
    num_main_bars: int = 8,
    tie_diameter: float = DEFAULT_TRANS_BAR_DIA,
    tie_spacing: float = DEFAULT_REBAR_SPACING_TRANS,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build rebar cages for individual piles (circular cage of vertical bars
    + tie rings), same logic as pier rebar but scaled to pile geometry.

    Args:
        pile_diameter (float): Outer diameter of each pile (mm).
        pile_length (float): Length of each pile (mm).
        pile_rows (int): Number of pile rows in X per pile cap.
        pile_cols (int): Number of pile columns in Y per pile cap.
        pile_spacing_x (float): C/C pile spacing in X (mm).
        pile_spacing_y (float): C/C pile spacing in Y (mm).
        pile_top_z (float): Z of the pile tops (mm).
        pier_x_positions (list[float] | None): X-coordinates of supports (mm).
        pier_y_center (float): Y-coordinate of the pile cap centre (mm).
        cover (float): Clear cover to tie outer face (mm).
        main_bar_diameter (float): Main bar diameter (mm).
        num_main_bars (int): Number of main bars per pile.
        tie_diameter (float): Tie bar diameter (mm).
        tie_spacing (float): Tie ring spacing (mm).
        span_length_L (float): Total bridge span (mm).
        num_supports (int): Number of intermediate supports.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pile_rebar": [TopoDS_Shape, ...]}``.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [i * step for i in range(n)]

    bar_radius = main_bar_diameter / 2.0
    tie_radius = tie_diameter / 2.0

    main_ring_radius = (pile_diameter / 2.0) - cover - tie_diameter - bar_radius
    main_ring_radius = max(main_ring_radius, bar_radius)

    tie_ring_radius = (pile_diameter / 2.0) - cover - tie_radius
    tie_ring_radius = max(tie_ring_radius, tie_radius)

    total_x_spread = (pile_rows - 1) * pile_spacing_x
    total_y_spread = (pile_cols - 1) * pile_spacing_y
    x_offsets = [-total_x_spread / 2.0 + r * pile_spacing_x for r in range(pile_rows)]
    y_offsets_pile = [-total_y_spread / 2.0 + c * pile_spacing_y for c in range(pile_cols)]

    shapes = []

    for x_centre in pier_x_positions:
        for dx in x_offsets:
            for dy in y_offsets_pile:
                px = x_centre + dx
                py = pier_y_center + dy
                pile_base_z = pile_top_z - pile_length   # pile extends downward

                # Main bars
                for k in range(num_main_bars):
                    angle = 2.0 * math.pi * k / num_main_bars
                    bx = px + main_ring_radius * math.cos(angle)
                    by = py + main_ring_radius * math.sin(angle)
                    # Vertical bar in -Z direction (pile goes down): use z_base = pile_base_z
                    shapes.append(
                        _make_vertical_bar(bx, by, pile_base_z, bar_radius, pile_length)
                    )

                # Tie rings
                z_start = pile_base_z + cover + tie_radius
                z_end   = pile_base_z + pile_length - cover - tie_radius
                z_tie = z_start
                while z_tie <= z_end + 1e-3:
                    shapes.append(
                        _make_tie_ring(px, py, z_tie, tie_ring_radius, tie_radius)
                    )
                    z_tie += tie_spacing

    return {"pile_rebar": shapes}
