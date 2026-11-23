"""Circular pier columns (concrete)."""
from osdagbridge.core.bridge_components.sub_structure.common import Part, cylinder, CONCRETE_COLOR


def build_piers(p):
    parts = []
    for i, y in enumerate(p.pier_y_positions, 1):
        shape = cylinder((p.pier_x, y, p.pier_bot_z), (0, 0, 1), p.pier_diameter / 2, p.pier_height)
        parts.append(Part(f"Pier_{i}", shape, "IfcColumn", "concrete",
                          CONCRETE_COLOR, p.concrete_opacity, {"y": y}))
    return parts
