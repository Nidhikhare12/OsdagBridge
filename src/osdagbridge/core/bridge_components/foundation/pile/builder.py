"""
Pile — Geometry Builder (pythonOCC)
===================================

Builds the 3D CAD solids of the pile group under one pile cap: ``n_x x
n_y`` circular vertical piles (default 2 x 2 = 4 piles) whose heads
start at the pile-cap soffit and extend DOWNWARD by ``pile_length``.

GEOMETRY ONLY (no viewer, no material). Returns raw ``TopoDS_Shape``
solids for the Bridge CAD pipeline, mirroring the superstructure
builders.

Units: millimetres (mm).

Coordinate convention (identical to the superstructure builders):
    X = longitudinal (along span), Y = transverse (deck width),
    Z = vertical (Z = 0 at girder mid-height).

The group is placed in FINAL global coordinates: the caller passes the
pile-group centreline (x_center, y_center) and the Z of the pile heads
(the pile-cap soffit).
"""

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder

from osdagbridge.core.bridge_components.foundation.pile.geometry import (
    pile_positions,
)
from osdagbridge.core.bridge_components.foundation.pile.properties import (
    PileParams,
    PILES_X,
    PILES_Y,
    PILE_DIAMETER,
    PILE_LENGTH,
    PILE_SPACING,
)


def build_pile(
    *,
    pile_diameter: float = PILE_DIAMETER,
    pile_length: float = PILE_LENGTH,
    x_center: float = 0.0,
    y_center: float = 0.0,
    top_z: float = 0.0,
):
    """Build ONE circular pile (convenience wrapper around the group).

    The pile head is at ``top_z`` and the pile extends downward by
    ``pile_length``.
    """
    # Cylinder built from the tip upward so the axis form matches the
    # known-good pattern in plate_girder/builder.py (create_shear_stud).
    axis = gp_Ax2(gp_Pnt(x_center, y_center, top_z - pile_length),
                  gp_Dir(0, 0, 1))
    return BRepPrimAPI_MakeCylinder(axis, pile_diameter / 2.0, pile_length).Shape()


def build_pile_group(
    *,
    n_piles_x: int = PILES_X,
    n_piles_y: int = PILES_Y,
    pile_diameter: float = PILE_DIAMETER,
    pile_length: float = PILE_LENGTH,
    pile_spacing_x: float = PILE_SPACING,
    pile_spacing_y: float = PILE_SPACING,
    x_center: float = 0.0,
    y_center: float = 0.0,
    top_z: float = 0.0,
):
    """Build the pile group under one pile cap.

    Parameters
    ----------
    n_piles_x, n_piles_y : int
        Pile grid counts along global X / Y. Defaults 2 x 2
        (``n_piles_per_cap = 4``).
    pile_diameter : float
        Outside diameter of one pile (mm). Default 400.
    pile_length : float
        Embedment length below the pile-cap soffit (mm). Default 5000.
    pile_spacing_x, pile_spacing_y : float
        Centre-to-centre spacing along X / Y (mm). Default 600 c/c.
    x_center, y_center : float
        Global centreline of the pile group = pile-cap centre (mm).
    top_z : float
        Global Z of the pile heads = pile-cap soffit (mm).

    Returns
    -------
    dict
        {
          "concrete": [TopoDS_Shape],  # one solid per pile
          "positions": [(dx, dy), ...] # local offsets, metadata only
        }
    """
    params = PileParams(
        n_piles_x=n_piles_x,
        n_piles_y=n_piles_y,
        pile_diameter=pile_diameter,
        pile_length=pile_length,
        pile_spacing_x=pile_spacing_x,
        pile_spacing_y=pile_spacing_y,
    )

    piles = []
    positions = pile_positions(params.n_piles_x, params.n_piles_y,
                               params.pile_spacing_x, params.pile_spacing_y)
    for (dx, dy) in positions:
        piles.append(
            build_pile(
                pile_diameter=params.pile_diameter,
                pile_length=params.pile_length,
                x_center=x_center + dx,
                y_center=y_center + dy,
                top_z=top_z,
            )
        )

    return {"concrete": piles, "positions": positions}
