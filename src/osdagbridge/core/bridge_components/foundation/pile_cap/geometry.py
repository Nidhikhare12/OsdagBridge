"""
Pile Cap — Placement Geometry (pure Python)
===========================================

Rebar-mat placement mathematics for the rectangular pile cap.
Shared by the pythonOCC builder and the IFC extractor so both produce
identical geometry.

Units: mm. Bar positions are offsets from the cap CENTRELINE (Y for the
main bars, X for the transverse bars); callers add the global cap centre.
"""

import math


def _even_positions(usable: float, spacing: float, minimum_count: int = 2) -> list:
    """Symmetric, evenly distributed bar offsets across ``usable`` width.

    The count is the smallest that keeps the ACTUAL c/c spacing at or
    below the nominal ``spacing`` (a maximum-spacing rule, never fewer
    than ``minimum_count``); the exact spacing is then
    ``usable / (n - 1)`` so the bars always land on both cover planes.
    """
    if usable <= 0.0:
        return [0.0]
    if spacing <= 0.0:
        return [0.0]
    n = max(minimum_count, int(math.ceil(usable / spacing)) + 1)
    if n == 1:
        return [0.0]
    step = usable / float(n - 1)
    return [-usable / 2.0 + i * step for i in range(n)]


def main_bar_positions(cap_width: float, cover: float, spacing: float) -> list:
    """Y-offsets of the main (longitudinal, X-direction) bars (mm).

    Main bars run along the cap LENGTH (global X) and are distributed
    across the cap WIDTH with clear side cover.
    """
    return _even_positions(cap_width - 2.0 * cover, spacing)


def transverse_bar_positions(cap_length: float, cover: float, spacing: float) -> list:
    """X-offsets of the transverse (Y-direction) bars (mm).

    Transverse bars run across the cap WIDTH (global Y) and are
    distributed along the cap LENGTH with clear end cover.
    """
    return _even_positions(cap_length - 2.0 * cover, spacing)


def main_bar_z(cap_depth: float, cover: float, main_diameter: float) -> float:
    """Z-offset (from cap BOTTOM face) of the main-bar axis (mm)."""
    return cover + main_diameter / 2.0


def transverse_bar_z(cap_depth: float, cover: float,
                     main_diameter: float, transverse_diameter: float) -> float:
    """Z-offset (from cap BOTTOM face) of the transverse-bar axis (mm).

    Transverse bars rest ON TOP of the main bars (classic bottom-mat
    detailing), one main-bar radius plus one transverse-bar radius above
    the main-bar axis level.
    """
    return main_bar_z(cap_depth, cover, main_diameter) \
        + main_diameter / 2.0 + transverse_diameter / 2.0
