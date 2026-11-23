from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING, KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_70R_TRACKED,
)


def test_boq_uses_pair_specific_bracing_areas_and_distinct_chord_sections():
    inputs = {
        KEY_SPAN: 10.0,
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_DECK_THICKNESS: 200.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        "typical_section.overall_bridge_width": 8.0,
    }
    outputs = {
        "crossbracing_forces_dict": {
            "geometry": {"diagonal_length_m": 3.0, "cb_spacing_m": 5.0}
        },
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
        "transverse_member_design.cb.section_properties.top_chord.G1G2.A": 20.0,
        "transverse_member_design.cb.section_properties.bottom_chord.G1G2.A": 30.0,
        "member_properties.cross_bracing_details.top_chord": "Yes",
        "member_properties.cross_bracing_details.bottom_chord": "Yes",
    }

    result = calculate_material_quantities(inputs, outputs)

    # 20 cm² and 30 cm² chord areas must not be replaced by the 10 cm²
    # diagonal area.  One panel is present in this 10 m / 5 m setup.
    assert result["bracing_top_vol_total"] == "0.0050"
    assert result["bracing_bot_vol_total"] == "0.0075"
    assert result["bracing_diag_vol_total"] == "0.0060"


def test_boq_does_not_assume_both_chords_when_disabled():
    inputs = {
        KEY_SPAN: 10.0,
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_DECK_THICKNESS: 200.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        "typical_section.overall_bridge_width": 8.0,
    }
    outputs = {
        "crossbracing_forces_dict": {
            "geometry": {"diagonal_length_m": 3.0, "cb_spacing_m": 5.0}
        },
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
        "member_properties.cross_bracing_details.top_chord": "No",
        "member_properties.cross_bracing_details.bottom_chord": "No",
    }
    result = calculate_material_quantities(inputs, outputs)
    assert result["bracing_top_qty"] == "0"
    assert result["bracing_bot_qty"] == "0"


def test_permanent_load_summary_counts_only_configured_footpaths():
    from osdagbridge.core.desktop.ui.dialogs.generate_results_values_builder import (
        resolve_permanent_load_summary,
    )
    from osdagbridge.core.utils.common import KEY_TS_FOOTPATH_WIDTH, KEY_TS_NO_OF_FOOTPATHS

    base = {
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_FOOTPATH_WIDTH: 1.5,
        KEY_TS_NO_OF_FOOTPATHS: 1,
    }
    one_side = resolve_permanent_load_summary(base)["rows"][0][0]
    no_footpath = resolve_permanent_load_summary({
        **base, KEY_TS_NO_OF_FOOTPATHS: 0,
    })["rows"][0][0]
    assert one_side == 3.679
    assert no_footpath == 0.0


def test_bridge_category_urs_envelopes_across_different_girders():
    from osdagbridge.core.bridge_types.plate_girder.dcr_utils import aggregate_bridge_category_urs

    per_girder = {
        "Girder 1": {"category_urs": {1: {"max_dcr": 0.72, "label": "Flexure"}, 2: {"max_dcr": 0.91, "label": "Shear"}}},
        "Girder 2": {"category_urs": {1: {"max_dcr": 0.88, "label": "Flexure"}, 2: {"max_dcr": 0.65, "label": "Shear"}}},
    }
    result = aggregate_bridge_category_urs(per_girder)
    assert result[1]["max_dcr"] == 0.88
    assert result[1]["governing_girder"] == "Girder 2"
    assert result[2]["max_dcr"] == 0.91
    assert result[2]["governing_girder"] == "Girder 1"


def test_reinforcement_takeoff_uses_designed_bar_sizes_and_spacing_not_generic_ratio():
    import math

    inputs = {
        KEY_SPAN: 10.0,
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_DECK_THICKNESS: 200.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        "typical_section.overall_bridge_width": 8.0,
    }
    outputs = {
        "deck_design_results": {
            "rebar_bottom_dia": "16", "rebar_bottom_spacing": "200",
            "rebar_top_dia": "16", "rebar_top_spacing": "200",
            "rebar_long_dia": "12", "rebar_long_spacing": "200",
        }
    }
    result = calculate_material_quantities(inputs, outputs)
    bottom_top = 2 * (math.ceil(10.0 * 1000 / 200) + 1) * 2.5 * (math.pi * 0.016**2 / 4) * 7850
    distribution = (math.ceil(8.0 * 1000 / 200) + 1) * 10.0 * (math.pi * 0.012**2 / 4) * 7850
    expected_mt = (bottom_top + distribution) / 1000
    assert math.isclose(float(result["rebar_deck_wt_total"]), expected_mt, rel_tol=1e-5)
    assert result["rebar_deck_qty"] == "143"


def test_report_vehicle_list_respects_false_string_values():
    from osdagbridge.core.reports.chap3 import ch3_loads

    report_tex = ch3_loads({
        KEY_SPAN: 20.0,
        KEY_LL_IRC_CLASS_A: "False",
        KEY_LL_IRC_70R_WHEELED: "No",
        KEY_LL_IRC_70R_TRACKED: "False",
    })
    assert "Vehicles Considered" in report_tex
    assert "Vehicles Considered} & None" in report_tex


def test_boq_aggregates_different_sections_per_girder_pair():
    inputs = {
        KEY_SPAN: 10.0,
        KEY_TS_NO_OF_GIRDERS: 3,
        KEY_TS_DECK_THICKNESS: 200.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        "typical_section.overall_bridge_width": 8.0,
        "member_properties.cross_bracing_details.top_chord.G1G2.B1M1": "Yes",
        "member_properties.cross_bracing_details.top_chord.G2G3.B2M1": "Yes",
        "member_properties.cross_bracing_details.bottom_chord.G1G2.B1M1": "Yes",
        "member_properties.cross_bracing_details.bottom_chord.G2G3.B2M1": "Yes",
        "member_properties.cross_bracing_details.type.G1G2.B1M1": "X-Bracing",
        "member_properties.cross_bracing_details.type.G2G3.B2M1": "X-Bracing",
    }
    outputs = {
        "crossbracing_forces_dict": {"geometry": {"diagonal_length_m": 3.0, "cb_spacing_m": 5.0}},
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
        "transverse_member_design.cb.section_properties.bracing.G2G3.A": 15.0,
        "transverse_member_design.cb.section_properties.top_chord.G1G2.A": 20.0,
        "transverse_member_design.cb.section_properties.top_chord.G2G3.A": 40.0,
        "transverse_member_design.cb.section_properties.bottom_chord.G1G2.A": 30.0,
        "transverse_member_design.cb.section_properties.bottom_chord.G2G3.A": 50.0,
    }
    result = calculate_material_quantities(inputs, outputs)
    assert result["bracing_top_vol_total"] == "0.0150"
    assert result["bracing_bot_vol_total"] == "0.0200"
    assert result["bracing_diag_vol_total"] == "0.0150"


def test_end_diaphragm_takeoff_uses_design_section_masses_and_member_lengths():
    import math

    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_DECK_THICKNESS: 200.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        "member_properties.girder_details.section_input.depth": 1000.0,
        "member_properties.end_diaphragm_details.type.G1G2.E1M1": "Cross Bracing",
        "member_properties.end_diaphragm_details.bracing_type.G1G2.E1M1": "X",
        "member_properties.end_diaphragm_details.top_chord.G1G2.E1M1": "Yes",
        "member_properties.end_diaphragm_details.bottom_chord.G1G2.E1M1": "Yes",
    }
    outputs = {
        "transverse_member_design.ed.section_properties.end_diaphragm.M.G1G2": 10.0,
        "transverse_member_design.ed.section_properties.top_chord.M.G1G2": 5.0,
        "transverse_member_design.ed.section_properties.bottom_chord.M.G1G2": 6.0,
    }
    result = calculate_material_quantities(inputs, outputs)
    diagonal_length = math.hypot(2.5, 0.85)
    expected_kg = 4 * 10.0 * diagonal_length + 2 * 5.0 * 2.5 + 2 * 6.0 * 2.5
    assert math.isclose(float(result["end_diaphragm_wt_total"]), expected_kg / 1000, abs_tol=1e-5)
    assert result["end_diaphragm_qty"] == "8"


def test_bridge_category_ur_ignores_nonfinite_and_negative_values():
    from osdagbridge.core.bridge_types.plate_girder.dcr_utils import aggregate_bridge_category_urs

    result = aggregate_bridge_category_urs({
        "G1": {"category_urs": {"3": {"max_dcr": 0.8, "checks": ["G1"]},
                                "4": {"max_dcr": float("nan")}}},
        "G2": {"category_urs": {"3": {"max_dcr": 0.9, "checks": ["G2"]},
                                "4": {"max_dcr": -0.1}}},
    })
    assert result[3]["max_dcr"] == 0.9
    assert result[3]["governing_girder"] == "G2"
    assert 4 not in result


def test_boq_uses_project_material_unit_weights_and_crash_barrier_area():
    import math

    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 3,
        KEY_TS_DECK_THICKNESS: 250.0,
        KEY_TS_GIRDER_SPACING: 1.7167,
        "typical_section.overall_bridge_width": 5.15,
        "material.deck.density": 24.5,  # kN/m3 from the supplied .osi
        "material.girder.density": 76.4,
        "typical_section.crash_barrier.type": "IRC 5 - RCC Crash Barrier",
        "typical_section.crash_barrier.area": 302282.768,  # mm2 in saved .osi
        "typical_section.crash_barrier.density": 25.0,  # kN/m3
    }
    result = calculate_material_quantities(inputs, {})
    expected_barrier_volume = 302282.768 / 1e6 * 20.0 * 2.0
    expected_barrier_mt = expected_barrier_volume * 25.0 / 9.80665
    expected_deck_mt = 20.0 * 5.15 * 0.25 * 24.5 / 9.80665
    assert math.isclose(float(result["crash_barrier_vol_total"]), expected_barrier_volume, rel_tol=1e-6)
    assert math.isclose(float(result["crash_barrier_wt_total"]), expected_barrier_mt, rel_tol=1e-5)
    assert math.isclose(float(result["concrete_deck_wt_total"]), expected_deck_mt, rel_tol=1e-5)
    assert math.isclose(float(result["concrete_volume_m3"]),
                        20.0 * 5.15 * 0.25 + expected_barrier_volume, rel_tol=1e-6)


def test_boq_crash_barrier_area_normalized_to_square_metres_is_not_divided_twice():
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 3,
        KEY_TS_DECK_THICKNESS: 250.0,
        KEY_TS_GIRDER_SPACING: 1.7167,
        "typical_section.overall_bridge_width": 5.15,
        "typical_section.crash_barrier.type": "IRC 5 - RCC Crash Barrier",
        "typical_section.crash_barrier.area": 0.302282768,  # normalized m2 snapshot
        "typical_section.crash_barrier.density": 25.0,
    }
    result = calculate_material_quantities(inputs, {})
    assert result["crash_barrier_vol_total"] == "12.0913"


def test_boq_reports_configured_barrier_with_missing_area_as_unavailable():
    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 3,
        KEY_TS_DECK_THICKNESS: 250.0,
        KEY_TS_GIRDER_SPACING: 1.7167,
        "typical_section.overall_bridge_width": 5.15,
        "typical_section.crash_barrier.type": "IRC 5 - RCC Crash Barrier",
        "typical_section.crash_barrier.area": None,
    }
    result = calculate_material_quantities(inputs, {})
    assert result["crash_barrier_vol_total"] == "N.A."
    assert result["crash_barrier_wt_total"] == "N.A."
    assert result["concrete_volume_m3"] == "N.A."


def test_end_diaphragm_takeoff_falls_back_to_configured_input_section_mass():
    import math

    inputs = {
        KEY_SPAN: 20.0,
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_DECK_THICKNESS: 250.0,
        KEY_TS_GIRDER_SPACING: 1.7167,
        "member_properties.girder_details.section_input.depth": 1120.0,
        "material.end_diaphragm.density": 76.4,
        "member_properties.end_diaphragm_details.type.G1G2.E1M1": "Cross Bracing",
        "member_properties.end_diaphragm_details.type.G1G2.E1M2": "Cross Bracing",
        "member_properties.end_diaphragm_details.bracing_type.G1G2.E1M1": "X-Bracing",
        "member_properties.end_diaphragm_details.top_chord.G1G2.E1M1": "Yes",
        "member_properties.end_diaphragm_details.bottom_chord.G1G2.E1M1": "Yes",
        "member_properties.end_diaphragm_details.section_properties.mass.G1G2.E1M1": 15.04,
        "member_properties.end_diaphragm_details.section_properties.mass.G1G2.E1M2": 15.04,
    }
    result = calculate_material_quantities(inputs, {})
    diagonal_length = math.hypot(1.7167, 0.85 * 1.12)
    expected_kg = 4 * 15.04 * diagonal_length + 2 * 15.04 * 1.7167 + 2 * 15.04 * 1.7167
    assert result["end_diaphragm_qty"] == "8"
    assert math.isclose(float(result["end_diaphragm_wt_total"]), expected_kg / 1000, rel_tol=1e-5)


def test_chapter6_does_not_render_empty_placeholder_frames():
    from osdagbridge.core.reports.chap6 import ch6_drawings

    tex = ch6_drawings({})
    assert "did not supply CAD figure assets" in tex
    assert "PLACEHOLDER" not in tex
