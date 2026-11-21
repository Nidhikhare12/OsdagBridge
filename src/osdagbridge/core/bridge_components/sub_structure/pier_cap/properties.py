"""
Pier Cap (Hammerhead) — Parametric Properties
=============================================

Pure-Python parametric dataclass and quantity helpers for the trapezoidal
hammerhead pier cap. No OCC imports (importable by the IFC extractor).

Units: millimetres (mm).

The cap is a prism running TRANSVERSELY (along global Y = deck width).
Its cross-section lies in the longitudinal-vertical (X-Z) plane and is a
trapezoid, wider at the top (where the girder bearings sit) than at the
bottom (where the circular column head meets it).
"""

import math
from dataclasses import dataclass

# ----------------------------------------------------------------------------
# Default dimensions (Task C specification)
# ----------------------------------------------------------------------------

PIER_CAP_TOP_WIDTH = 3000.0     # Longitudinal (X) width at the cap top (mm)
PIER_CAP_BOTTOM_WIDTH = 1200.0  # Longitudinal (X) width at the cap bottom (mm)
PIER_CAP_DEPTH = 600.0          # Vertical depth of the cap (mm)
# PIER_CAP_LENGTH: transverse length of the cap (mm). No single default is
# meaningful — the bridge assembly passes the deck width (see
# ``pier_cap.geometry.auto_pier_cap_length``).


@dataclass(frozen=True)
class PierCapParams:
    """
    Parametric description of a trapezoidal hammerhead pier cap.

    Attributes
    ----------
    top_width : float
        Longitudinal (X) width of the cap at its TOP face (mm).
    bottom_width : float
        Longitudinal (X) width of the cap at its BOTTOM face (mm).
    depth : float
        Vertical depth of the cap (mm).
    length : float
        Transverse (Y) length of the cap (mm); the assembly normally
        matches this to the deck width.
    """

    top_width: float = PIER_CAP_TOP_WIDTH
    bottom_width: float = PIER_CAP_BOTTOM_WIDTH
    depth: float = PIER_CAP_DEPTH
    length: float = 0.0        # <= 0 -> auto (deck width) in the assembly


# ----------------------------------------------------------------------------
# Quantity helpers (BOQ-friendly, pure math)
# ----------------------------------------------------------------------------

def pier_cap_cross_section_area(params: PierCapParams) -> float:
    """Area of the trapezoidal cross-section (mm^2)."""
    return 0.5 * (params.top_width + params.bottom_width) * params.depth


def pier_cap_concrete_volume(params: PierCapParams) -> float:
    """Gross concrete volume of one pier cap (mm^3)."""
    return pier_cap_cross_section_area(params) * params.length
