"""
Pile Cap — Parametric Properties
================================

Pure-Python parametric dataclass and quantity helpers for the rectangular
reinforced-concrete pile cap. No OCC imports (importable by the IFC
extractor).

Units: millimetres (mm).

The pile cap is a rectangular prism:
    length -> global X (longitudinal),
    width  -> global Y (transverse),
    depth  -> global Z (vertical).
"""

import math
from dataclasses import dataclass

# ----------------------------------------------------------------------------
# Default dimensions (Task C specification)
# ----------------------------------------------------------------------------

PILE_CAP_LENGTH = 2200.0       # Longitudinal (X) dimension (mm)
PILE_CAP_WIDTH = 1200.0        # Transverse (Y) dimension (mm)
PILE_CAP_DEPTH = 600.0         # Vertical (Z) dimension (mm)

REBAR_MAIN_DIAMETER = 16.0     # Main (longitudinal, X-direction) bar dia (mm)
REBAR_SPACING_LONGITUDINAL = 150.0   # c/c spacing of main bars along Y (mm)
REBAR_TRANSVERSE_DIAMETER = 8.0      # Transverse (Y-direction) bar dia (mm)
REBAR_SPACING_TRANSVERSE = 200.0     # c/c spacing of transverse bars along X (mm)
REBAR_COVER = 40.0             # Clear cover (mm)


@dataclass(frozen=True)
class PileCapParams:
    """
    Parametric description of a rectangular RC pile cap with a bottom
    reinforcement mat (main bars along X + transverse bars along Y).

    Attributes
    ----------
    length, width, depth : float
        Prism dimensions along global X / Y / Z (mm).
    rebar_main_diameter : float
        Diameter of the main (bottom, longitudinal) bars (mm).
    rebar_spacing_longitudinal : float
        c/c spacing of the main bars across the width (mm).
    rebar_transverse_diameter : float
        Diameter of the transverse distribution bars (mm).
    rebar_spacing_transverse : float
        c/c spacing of the transverse bars along the length (mm).
    rebar_cover : float
        Clear cover, also used as the bar end inset (mm).
    """

    length: float = PILE_CAP_LENGTH
    width: float = PILE_CAP_WIDTH
    depth: float = PILE_CAP_DEPTH
    rebar_main_diameter: float = REBAR_MAIN_DIAMETER
    rebar_spacing_longitudinal: float = REBAR_SPACING_LONGITUDINAL
    rebar_transverse_diameter: float = REBAR_TRANSVERSE_DIAMETER
    rebar_spacing_transverse: float = REBAR_SPACING_TRANSVERSE
    rebar_cover: float = REBAR_COVER


# ----------------------------------------------------------------------------
# Quantity helpers (BOQ-friendly, pure math)
# ----------------------------------------------------------------------------

def pile_cap_concrete_volume(params: PileCapParams) -> float:
    """Gross concrete volume of one pile cap (mm^3)."""
    return params.length * params.width * params.depth


def pile_cap_steel_volume(params: PileCapParams) -> float:
    """Total steel volume of the bottom rebar mat (mm^3).

    Counts / lengths follow the same formulas as
    ``pile_cap.geometry`` so the quantities always match the modelled
    solids.
    """
    from osdagbridge.core.bridge_components.foundation.pile_cap.geometry import (
        main_bar_positions,
        transverse_bar_positions,
    )

    main_len = max(0.0, params.length - 2.0 * params.rebar_cover)
    trans_len = max(0.0, params.width - 2.0 * params.rebar_cover)

    n_main = len(main_bar_positions(params.width, params.rebar_cover,
                                    params.rebar_spacing_longitudinal))
    n_trans = len(transverse_bar_positions(params.length, params.rebar_cover,
                                           params.rebar_spacing_transverse))

    vol_main = n_main * math.pi * (params.rebar_main_diameter / 2.0) ** 2 * main_len
    vol_trans = n_trans * math.pi * (params.rebar_transverse_diameter / 2.0) ** 2 * trans_len
    return vol_main + vol_trans
