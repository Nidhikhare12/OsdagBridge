"""
Pier (Circular Column) — Placement Geometry (pure Python)
=========================================================

Bar / tie placement mathematics for the circular RC pier column.
Shared by:

* ``sub_structure/pier/builder.py``  — builds the pythonOCC solids,
* ``ifc_export_bridge/bridge_cad_extraction.py`` — reconstructs the same
  reinforcement parametrically for the IFC export (no OCC available there).

Keeping the math here guarantees that the CAD solids and the IFC entities
are geometrically identical.

All units mm. All results are relative to the pier axis (x_center,
y_center) and the column BASE (z = 0 at column bottom face, +z up), so the
callers can offset them to global coordinates.
"""

import math


def core_radius(pier_diameter: float, cover: float) -> float:
    """Radius of the rebar core (concrete face minus clear cover) (mm)."""
    return max(0.0, pier_diameter / 2.0 - cover)


def bar_ring_radius(pier_diameter: float, cover: float, bar_diameter: float) -> float:
    """Centreline radius of the ring of longitudinal bars (mm).

    Bar centre sits one bar radius inside the core so the bar has full
    clear cover to the concrete face.
    """
    return max(0.0, core_radius(pier_diameter, cover) - bar_diameter / 2.0)


def longitudinal_bar_count(pier_diameter: float, cover: float, spacing: float) -> int:
    """Number of longitudinal bars distributed around the circumference.

    The count is rounded up from ``circumference / spacing`` with a
    practical minimum of 6 bars (needed for a stable circular cage).
    """
    circumference = 2.0 * math.pi * core_radius(pier_diameter, cover)
    if spacing <= 0:
        return 6
    return max(6, int(math.ceil(circumference / spacing)))


def longitudinal_bar_angles(count: int) -> list:
    """Evenly spaced bar angles (radians) around the column axis."""
    return [2.0 * math.pi * i / float(count) for i in range(count)]


def tie_count(pier_height: float, cover: float, spacing: float) -> int:
    """Number of transverse tie rings between the cover planes.

    The count is chosen so the ACTUAL tie spacing never exceeds the
    nominal ``spacing`` (a maximum-spacing rule): the usable height is
    divided into the smallest whole number of intervals whose length
    stays below the nominal value, with ties at both cover planes.
    """
    usable = max(0.0, pier_height - 2.0 * cover)
    if spacing <= 0 or usable <= 0:
        return 0
    return max(2, int(math.ceil(usable / spacing)) + 1)


def tie_levels(pier_height: float, cover: float, spacing: float) -> list:
    """Z-offsets (from column BOTTOM face) of the tie ring centres (mm)."""
    n = tie_count(pier_height, cover, spacing)
    if n <= 0:
        return []
    z0 = cover
    z1 = pier_height - cover
    if n == 1:
        return [(z0 + z1) / 2.0]
    step = (z1 - z0) / float(n - 1)
    return [z0 + i * step for i in range(n)]


def tie_ring_length(pier_diameter: float, cover: float,
                    main_bar_diameter: float, tie_diameter: float) -> float:
    """Developed (unrolled) length of one circular tie ring (mm).

    The tie centreline follows the longitudinal-bar ring so that the
    ties wrap the main bars.
    """
    r = bar_ring_radius(pier_diameter, cover, main_bar_diameter)
    return 2.0 * math.pi * r


def bearing_level_z(girder_depth: float, bottom_flange_thickness: float) -> float:
    """Global Z of the girder soffit / bearing seat (mm).

    The superstructure builders place the girder mid-height at Z = 0
    (web between ``-D/2 .. +D/2`` plus flanges), therefore the bottom of
    the bottom flange — the bearing level where the pier cap must start —
    is at ``-(D/2 + T_fb)``.
    """
    return -(girder_depth / 2.0 + bottom_flange_thickness)
