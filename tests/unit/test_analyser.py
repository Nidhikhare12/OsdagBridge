import math

from osdagbridge.core.bridge_types.plate_girder.dto import SectionProperties


def test_section_properties_accepts_valid_physical_values():
    section = SectionProperties(
        A=1.5,
        J=0.02,
        Iz=0.8,
        Iy=0.35,
        Az=0.9,
        Ay=0.9,
    )

    assert math.isclose(section.A, 1.5)
