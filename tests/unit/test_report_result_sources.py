from osdagbridge.core.reports.chap2 import _girder_tables
from osdagbridge.core.reports.utilization import component_checks, governing, outcome
from osdagbridge.core.utils.common import (
    KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS, KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, KEY_TS_NO_OF_GIRDERS,
)


def test_girder_dimensions_use_normalized_metres():
    # G1 values from the desktop analysis input dictionary for test-design.osi.
    inputs = {f"{key}.G1.M1": value for key, value in (
        (KEY_MP_GIRDER_DEPTH, 1.67), (KEY_MP_GIRDER_WEB_THICKNESS, 0.01),
        (KEY_MP_GIRDER_TOP_FLANGE_WIDTH, 0.51), (KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, 0.022),
        (KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, 0.51), (KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, 0.022),
    )}
    assert "1670 & 10 & 510, 22 & 510, 22" in _girder_tables(inputs, 1)


def test_component_governing_checks_use_distinct_real_result_schema():
    results = {
        "design_results": {"per_girder": {
            "G1": {"checks": [{"dcr": 0.99}], "per_lc": {
                "ULS 1": {"checks": [{"dcr": 1.02, "name": "Flexure"}]},
                "Envelope": {"checks": [{"dcr": 5}]},
            }},
            "G2": {"checks": [{"dcr": 9}]},
        }},
        "deck_design_results": {"ur_bot_uls": 0.77, "ur_composite_crack": 0.99,
                                "ur_top_uls": float("inf"), "rebar_provided": 820},
        "crossbracing_design_results": {"G1-G2": {"diagonal": {
            "compression": {"Member.efficiency": 0.74, "Member.tension_capacity": 16.81}}}},
        "crossbracing_forces_dict": {"pairs": {"G1-G2": {
            "diag_compression_kN": -8.0, "diag_compression_gov_lc": "1.5 EQ (b)"}}},
        "end_diaphragm_design_results": {"G1-G2": {}},
    }
    girder, deck, bracing, diaphragm = component_checks(results, {KEY_TS_NO_OF_GIRDERS: 1}).values()
    assert governing(girder).ratio == 1.02
    assert governing(girder).load_case == "ULS 1"
    assert governing(deck).label == "Crack control reinforcement"
    assert governing(bracing).ratio == 0.74
    assert governing(bracing).demand == 8.0
    assert governing(bracing).capacity == 16.81
    assert [outcome(group) for group in (girder, deck, bracing, diaphragm)] == [
        "FAIL", "PASS", "PASS", "Not available",
    ]
    results["end_diaphragm_design_results"]["G1-G2"] = {
        "chord": {"tension": {"Optimum.UR": 1.04, "Design.Strength": 50.0}},
    }
    diaphragm = component_checks(results, {})["End Diaphragms"]
    assert governing(diaphragm).ratio == 1.04
    assert outcome(diaphragm) == "FAIL"
