import pytest
from osdagbridge.core.boq.boq_generator import _lookup_section_mass, calculate_material_quantities
from osdagbridge.core.utils.common import KEY_SPAN, KEY_TS_NO_OF_GIRDERS, KEY_TS_GIRDER_SPACING


def test_section_mass_lookup():
    """Verify section mass lookup from database/geometry for ISA 40x40x3 and other sections."""
    # ISA 40x40x3: Area = 237 mm2 (2.37 cm2) -> 237e-6 m2 * 7850 kg/m3 = 1.86045 kg/m
    mass_40 = _lookup_section_mass("40 x 40 x 3")
    assert mass_40 is not None
    assert abs(mass_40 - 1.86) < 0.05, f"Expected ~1.86 kg/m for 40x40x3, got {mass_40}"

    mass_40_isa = _lookup_section_mass("ISA 40x40x3")
    assert mass_40_isa is not None
    assert abs(mass_40_isa - 1.86) < 0.05, f"Expected ~1.86 kg/m for ISA 40x40x3, got {mass_40_isa}"

    # ISA 75x75x8: Area = 1138 mm2 (11.38 cm2) -> 1138e-6 m2 * 7850 kg/m3 = 8.93 kg/m (~8.95-9.0 kg/m)
    mass_75 = _lookup_section_mass("ISA 75x75x8")
    assert mass_75 is not None
    assert abs(mass_75 - 9.0) < 0.2, f"Expected ~8.95-9.0 kg/m for ISA 75x75x8, got {mass_75}"

    # ISA 100x100x10: Area = 1903 mm2 (19.03 cm2) -> ~14.9-15.04 kg/m
    mass_100 = _lookup_section_mass("ISA 100x100x10")
    assert mass_100 is not None
    assert abs(mass_100 - 15.0) < 0.3, f"Expected ~14.9-15.04 kg/m for ISA 100x100x10, got {mass_100}"


def test_end_diaphragm_boq_single_source_of_truth_real_run():
    """
    Verify that End Diaphragm uses the exact section area from the cross-frame
    design as single source of truth (237 mm2 -> 1.86 kg/m -> 0.12 MT for 6 panels).
    """
    inputs = {
        KEY_SPAN: 24.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.569,
        "member_properties.girder_details.section_input.web_depth": 1147.0,
        # Un-designed UI default in inputs must NOT override designed section
        "member_properties.end_diaphragm_details.bracing_section_designation": "IS 100 x 100 x 10",
    }
    outputs = {
        # Designed section area: 2.37 cm2 = 237 mm2 (ISA 40x40x3)
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 2.37,
        "crossbracing_forces_dict": {
            "geometry": {
                "diagonal_length_m": 2.810,
                "cb_spacing_m": 12.0,
            }
        },
        "crossbracing_design_results": {
            "G1-G2": {
                "diagonal": {"tension": {"section_size.designation": "40 x 40 x 3"}},
                "chord": {"tension": {"section_size.designation": "40 x 40 x 3"}},
            }
        },
    }

    q = calculate_material_quantities(inputs, outputs)

    assert q["steel_ed_qty"] == "6"
    assert q["steel_ed_diag_mass"] == "1.86"
    assert q["steel_ed_chord_mass"] == "1.86"
    assert q["steel_ed_diag_sec"] == "ISA 40x40x3"
    assert q["steel_ed_chord_sec"] == "ISA 40x40x3"
    # 6 panels * [2(2.569 * 1.86) + 2(2.813 * 1.86)] = 6 * 20.02 kg = 120.1 kg = 0.12 MT
    assert q["steel_ed_wt_total"] == "0.12"
    assert "1.86" in q["steel_ed_vol_formula"]
    assert q["steel_ed_is_assumed"] is False


def test_end_diaphragm_boq_with_isa_75_section():
    """Verify End Diaphragm calculation with another designed section (ISA 75x75x8)."""
    # 11.38 cm2 = 1138 mm2 -> 1138e-6 * 7850 = 8.93 kg/m
    inputs = {
        KEY_SPAN: 24.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.50,
        "member_properties.girder_details.section_input.web_depth": 1500.0,
    }
    outputs = {
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 11.38,
        "crossbracing_forces_dict": {
            "geometry": {
                "diagonal_length_m": 2.915,
                "cb_spacing_m": 6.0,
            }
        },
        "crossbracing_design_results": {
            "G1-G2": {
                "diagonal": {"tension": {"section_size.designation": "ISA 75x75x8"}},
                "chord": {"tension": {"section_size.designation": "ISA 75x75x8"}},
            }
        },
    }

    q = calculate_material_quantities(inputs, outputs)

    assert q["steel_ed_qty"] == "6"
    assert q["steel_ed_diag_mass"] == "8.93"
    assert q["steel_ed_chord_mass"] == "8.93"
    assert q["steel_ed_diag_sec"] == "ISA 75x75x8"
    # panel mass = 2*2.5*8.93 + 2*2.915*8.93 = 44.65 + 52.06 = 96.71 kg
    # 6 panels * 96.71 kg = 580.2 kg = 0.58 MT
    assert q["steel_ed_wt_total"] == "0.58"
    assert q["steel_ed_is_assumed"] is False
