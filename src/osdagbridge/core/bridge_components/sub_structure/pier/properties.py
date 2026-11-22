"""
Pier (Circular Column) — Parametric Properties
==============================================

Pure-Python parametric dataclass and quantity helpers for the circular
reinforced-concrete pier column. No OCC imports here (kept importable by
the IFC extractor, which runs without OpenCASCADE).

Units: millimetres (mm) unless noted otherwise.

Coordinate convention (identical to the superstructure builders):
    X = longitudinal (along span, 0 .. span_length_L)
    Y = transverse  (deck width, centred on 0)
    Z = vertical    (Z = 0 at girder mid-height, substructure below bearing)
"""

import math
from dataclasses import dataclass

# ----------------------------------------------------------------------------
# Default dimensions (Task C specification)
# ----------------------------------------------------------------------------

PIER_DIAMETER = 800.0          # Circular column outside diameter (mm)
PIER_HEIGHT = 3000.0           # Clear height between pier-cap and pile-cap (mm)

REBAR_MAIN_DIAMETER = 16.0     # Longitudinal (vertical) bar diameter (mm)
REBAR_SPACING_LONGITUDINAL = 150.0   # c/c spacing of bars around circumference (mm)
REBAR_TRANSVERSE_DIAMETER = 8.0      # Tie / ring bar diameter (mm)
REBAR_SPACING_TRANSVERSE = 200.0     # c/c vertical spacing of ties (mm)
REBAR_COVER = 40.0             # Clear cover to the concrete face (mm)


@dataclass(frozen=True)
class PierParams:
    """
    Parametric description of a circular RC pier column.

    Attributes
    ----------
    pier_diameter : float
        Outside diameter of the circular column (mm).
    pier_height : float
        Clear column height between the pier-cap soffit and the pile-cap
        top surface (mm).
    rebar_main_diameter : float
        Diameter of the longitudinal (vertical) reinforcement (mm).
    rebar_spacing_longitudinal : float
        Nominal c/c spacing of the longitudinal bars measured around the
        core circumference (mm). The actual count is rounded up and the
        bars are then spread evenly.
    rebar_transverse_diameter : float
        Diameter of the transverse circular ties / rings (mm).
    rebar_spacing_transverse : float
        Nominal vertical c/c spacing of the ties (mm). Actual spacing is
        adjusted so the ties fit between the cover planes.
    rebar_cover : float
        Clear concrete cover for all reinforcement (mm).
    """

    pier_diameter: float = PIER_DIAMETER
    pier_height: float = PIER_HEIGHT
    rebar_main_diameter: float = REBAR_MAIN_DIAMETER
    rebar_spacing_longitudinal: float = REBAR_SPACING_LONGITUDINAL
    rebar_transverse_diameter: float = REBAR_TRANSVERSE_DIAMETER
    rebar_spacing_transverse: float = REBAR_SPACING_TRANSVERSE
    rebar_cover: float = REBAR_COVER


# ----------------------------------------------------------------------------
# Quantity helpers (BOQ-friendly, pure math)
# ----------------------------------------------------------------------------

def pier_concrete_volume(params: PierParams) -> float:
    """Gross concrete volume of one pier column (mm^3)."""
    return math.pi * (params.pier_diameter / 2.0) ** 2 * params.pier_height


def pier_longitudinal_bar_length(params: PierParams) -> float:
    """Length of ONE longitudinal bar (mm).

    Bars run from (bottom + cover) to (top - cover).
    """
    return max(0.0, params.pier_height - 2.0 * params.rebar_cover)


def pier_steel_volume(params: PierParams) -> float:
    """Total steel volume of the reinforcement cage (mm^3).

    Longitudinal bars + transverse tie rings.
    Bar-level placement math lives in ``pier.geometry``; this helper only
    needs counts and lengths, which it derives with the same formulas so
    that quantities always match the modelled solid geometry.
    """
    from osdagbridge.core.bridge_components.sub_structure.pier.geometry import (
        longitudinal_bar_count,
        tie_ring_length,
        tie_count,
    )

    n_bars = longitudinal_bar_count(params.pier_diameter, params.rebar_cover,
                                    params.rebar_spacing_longitudinal)
    vol_long = n_bars * math.pi * (params.rebar_main_diameter / 2.0) ** 2 \
        * pier_longitudinal_bar_length(params)

    n_ties = tie_count(params.pier_height, params.rebar_cover,
                       params.rebar_spacing_transverse)
    vol_ties = n_ties * math.pi * (params.rebar_transverse_diameter / 2.0) ** 2 \
        * tie_ring_length(params.pier_diameter, params.rebar_cover,
                          params.rebar_main_diameter,
                          params.rebar_transverse_diameter)

    return vol_long + vol_ties
