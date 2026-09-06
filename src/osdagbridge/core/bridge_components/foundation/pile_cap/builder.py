"""
Pile Cap Geometry Builder
=========================

Builds the rectangular prism RCC pile cap (footing block) that distributes
load from the pier shaft to the individual piles below.

Pattern:
  - Same module-level defaults, private helpers, and ``build_*`` function
    as other substructure and superstructure builders.
  - Returns raw TopoDS_Shapes; no viewer, no fusion, no colour.

Shape:
  A rectangular prism (BRepPrimAPI_MakeBox), centred at the pier support
  X-position and Y = 0, sitting immediately below the pier base.

Units: mm throughout.
Coordinate system (from  .md):
  X = longitudinal, Y = transverse, Z = vertical.
  Origin = centre of span at deck level (Z = 0).
  Pile cap top face = pier base Z (negative, below deck level).
"""

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# ---------------------------------------------------------------------------
# Module-level defaults (mm) — match user spec
# ---------------------------------------------------------------------------
DEFAULT_CAP_LENGTH: float    = 2200.0   # mm — longitudinal (X) dimension
DEFAULT_CAP_WIDTH: float     = 1200.0   # mm — transverse (Y) dimension
DEFAULT_CAP_DEPTH: float     = 600.0    # mm — vertical thickness


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _translate(shape, dx=0.0, dy=0.0, dz=0.0):
    """Translate a TopoDS_Shape by (dx, dy, dz) mm."""
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(float(dx), float(dy), float(dz)))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_pile_cap(
    *,
    cap_len_x: float = DEFAULT_CAP_LENGTH,
    cap_len_y: float = DEFAULT_CAP_WIDTH,
    cap_thickness: float = DEFAULT_CAP_DEPTH,
    cap_top_z: float = -4200.0,
    pier_x_positions: list = None,
    pier_y_center: float = 0.0,
    span_length_L: float = 20000.0,
    num_supports: int = 1,
):
    """
    Build rectangular RCC pile caps.

    Each pile cap is centred at the pier support X-position and at
    ``pier_y_center`` in the transverse direction.  Its top face is at
    ``cap_top_z``, which must match the ``pier_base_z`` used in the pier
    builder.

    Args:
        cap_len_x (float): Longitudinal length of the pile cap (mm).
        cap_len_y (float): Transverse width of the pile cap (mm).
        cap_thickness (float): Vertical thickness of the pile cap (mm).
        cap_top_z (float): Z-coordinate of the top face of the pile cap (mm).
            Must equal ``pier_base_z`` from the pier builder.
        pier_x_positions (list[float] | None): X-coordinates (mm) of each
            intermediate support.  Auto-derived from span/num_supports if None.
        pier_y_center (float): Y-coordinate of the centre of each pile cap (mm).
            Typically 0 (bridge centreline).
        span_length_L (float): Total bridge span (mm).
        num_supports (int): Number of intermediate supports.

    Returns:
        dict[str, list[TopoDS_Shape]]:
            ``{"pile_caps": [TopoDS_Shape, ...]}``.  One box per support.
    """
    if pier_x_positions is None:
        n = max(1, int(num_supports))
        if n == 1:
            pier_x_positions = [0.0]
        elif n == 2:
            pier_x_positions = [0.0, span_length_L]
        else:
            step = span_length_L / (n - 1)
            pier_x_positions = [step * i for i in range(n)]

    pile_caps = []

    for x_pos in pier_x_positions:
        # Cap centred at X=span position, Y=transverse centre
        x0 = x_pos - cap_len_x / 2.0
        y0 = pier_y_center - cap_len_y / 2.0
        z0 = cap_top_z - cap_thickness

        box = BRepPrimAPI_MakeBox(
            gp_Pnt(float(x0), float(y0), float(z0)),
            float(cap_len_x),
            float(cap_len_y),
            float(cap_thickness),
        ).Shape()

        pile_caps.append(box)

    return {"pile_caps": pile_caps}
