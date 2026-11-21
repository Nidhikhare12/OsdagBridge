"""
Pile — Parametric Properties
============================

Pure-Python parametric dataclass and quantity helpers for the circular
bored piles below the pile cap. No OCC imports (importable by the IFC
extractor).

Units: millimetres (mm).
"""

import math
from dataclasses import dataclass

# ----------------------------------------------------------------------------
# Default dimensions (Task C specification)
# ----------------------------------------------------------------------------

N_PILES_PER_CAP = 4            # Total piles per pile cap (2 x 2 grid)
PILES_X = 2                    # Number of piles per row  (longitudinal, X)
PILES_Y = 2                    # Number of piles per line (transverse,  Y)
PILE_DIAMETER = 400.0          # Pile outside diameter (mm)
PILE_LENGTH = 5000.0           # Embedment length below the pile cap (mm)
PILE_SPACING = 600.0           # c/c pile spacing, both directions (mm)


@dataclass(frozen=True)
class PileParams:
    """
    Parametric description of a group of circular piles under one cap.

    Attributes
    ----------
    n_piles_x, n_piles_y : int
        Pile grid counts along global X / Y. Default 2 x 2 = 4 piles.
    pile_diameter : float
        Outside diameter of one pile (mm). Default 400.
    pile_length : float
        Length of one pile below the pile-cap soffit (mm). Default 5000.
    pile_spacing_x, pile_spacing_y : float
        Centre-to-centre pile spacing along X / Y (mm). Default 600.
    """

    n_piles_x: int = PILES_X
    n_piles_y: int = PILES_Y
    pile_diameter: float = PILE_DIAMETER
    pile_length: float = PILE_LENGTH
    pile_spacing_x: float = PILE_SPACING
    pile_spacing_y: float = PILE_SPACING

    @property
    def n_piles_per_cap(self) -> int:
        """Total number of piles in the group."""
        return self.n_piles_x * self.n_piles_y


# ----------------------------------------------------------------------------
# Quantity helpers (BOQ-friendly, pure math)
# ----------------------------------------------------------------------------

def pile_volume(params: PileParams) -> float:
    """Concrete volume of ONE pile (mm^3)."""
    return math.pi * (params.pile_diameter / 2.0) ** 2 * params.pile_length


def pile_group_volume(params: PileParams) -> float:
    """Concrete volume of the whole pile group under one cap (mm^3)."""
    return pile_volume(params) * params.n_piles_per_cap
