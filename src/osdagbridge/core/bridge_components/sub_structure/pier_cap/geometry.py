"""
Pier Cap (Hammerhead) — Placement Geometry (pure Python)
========================================================

Profile / placement mathematics for the trapezoidal hammerhead pier cap.
Shared by the pythonOCC builder and the IFC extractor so that both
produce identical geometry.

Units: mm. Profile coordinates are LOCAL to the cap:
    u -> global X (longitudinal), 0 at the cap centreline,
    v -> global Z measured DOWN from the cap top face
         (the IFC profile plane is used with a +Y-down frame, see the
         builder / extractor docstrings for the axis mapping).
"""

import math


def auto_pier_cap_length(num_girders: int, girder_spacing: float,
                         deck_width: float = 0.0) -> float:
    """Transverse cap length (mm) when the user has not fixed one.

    Rule (Task C: "pier_cap_length = match deck width or parameterize"):
    use the deck width when known, but never shorter than the outermost
    girder spacing + 1000 mm (500 mm cantilever past each outer bearing).
    """
    span_girders = max(0.0, (num_girders - 1) * girder_spacing)
    minimum = span_girders + 1000.0
    if deck_width and deck_width > 0.0:
        return max(deck_width, minimum)
    return minimum


def trapezoid_profile_points(top_width: float, bottom_width: float,
                             depth: float) -> list:
    """Trapezoid corner points (u, v) of the hammerhead cross-section.

    v is measured DOWNWARD from the cap top face (v = 0 at top,
    v = depth at the bottom). The caller maps (u, v) to global
    (X = x_center + u, Z = top_z - v).

    Winding: the corners are returned COUNTER-CLOCKWISE in the (u, v)
    profile plane, i.e. top-left -> top-right -> bottom-right ->
    bottom-left. Because the profile local +v axis maps to global -Z
    while the extrusion runs along global +Y, this CCW order makes the
    face normal point along the extrusion direction - the convention of
    the known-good deck-slab polygon in ``super_structure/deck/
    builder.py`` - and satisfies the counter-clockwise rule of
    ``IfcArbitraryClosedProfileDef`` used by the IFC exporter
    (``bridge_cad_extraction._extract_substructure``).
    """
    return [
        (-top_width / 2.0, 0.0),        # top-left
        (top_width / 2.0, 0.0),         # top-right
        (bottom_width / 2.0, depth),    # bottom-right
        (-bottom_width / 2.0, depth),   # bottom-left
    ]
