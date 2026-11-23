"""Trapezoidal (hammerhead) pier cap running transversely under the deck."""
from osdagbridge.core.bridge_components.sub_structure.common import Part, trapezoid_prism, CONCRETE_COLOR


def build_pier_cap(p):
    shape = trapezoid_prism(p.pier_cap_top_width, p.pier_cap_bottom_width,
                            p.cap_top_z, p.cap_bot_z, p.pier_x,
                            -p.pier_cap_length / 2, p.pier_cap_length)
    return [Part("PierCap", shape, "IfcBeam", "concrete", CONCRETE_COLOR, p.concrete_opacity)]
