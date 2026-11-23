"""Circular piles in a 2x2 (or n x n) grid under each pile cap."""
from osdagbridge.core.bridge_components.sub_structure.common import Part, cylinder, CONCRETE_COLOR


def build_piles(p):
    parts = []
    for ci, y in enumerate(p.pier_y_positions, 1):
        for pi, (dx, dy) in enumerate(p.pile_offsets(), 1):
            shape = cylinder((p.pier_x + dx, y + dy, p.pile_bot_z), (0, 0, 1),
                             p.pile_diameter / 2, p.pile_length)
            parts.append(Part(f"Pile_{ci}_{pi}", shape, "IfcPile", "concrete",
                              CONCRETE_COLOR, p.concrete_opacity, {"x": p.pier_x + dx, "y": y + dy}))
    return parts
