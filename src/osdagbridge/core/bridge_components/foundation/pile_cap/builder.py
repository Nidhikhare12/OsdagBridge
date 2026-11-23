"""Rectangular pile caps, one beneath each pier."""
from osdagbridge.core.bridge_components.sub_structure.common import Part, box, CONCRETE_COLOR


def build_pile_caps(p):
    parts = []
    for i, y in enumerate(p.pier_y_positions, 1):
        shape = box(p.pier_x - p.pile_cap_length / 2, y - p.pile_cap_width / 2, p.pilecap_bot_z,
                    p.pile_cap_length, p.pile_cap_width, p.pile_cap_depth)
        parts.append(Part(f"PileCap_{i}", shape, "IfcFooting", "concrete",
                          CONCRETE_COLOR, p.concrete_opacity, {"y": y}))
    return parts
