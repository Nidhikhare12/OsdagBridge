from osdagbridge.core.reports.chap2 import _girder_tables
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.reports.utilization import component_checks, governing, outcome, transverse_checks
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
    exported = list(transverse_checks(results))
    assert exported[0].ratio == 0.74
    assert exported[0].demand == 8.0
    assert exported[0].capacity is None
    assert not bracing
    assert [outcome(group) for group in (girder, deck, bracing, diaphragm)] == [
        "FAIL", "PASS", "Not available", "Not available",
    ]
    results["end_diaphragm_design_results"]["G1-G2"] = {
        "chord": {"tension": {"Optimum.UR": 1.04, "Design.Strength": 50.0}},
    }
    diaphragm = component_checks(results, {})["End Diaphragms"]
    assert list(transverse_checks(results, diaphragm=True))[0].ratio == 1.04
    assert outcome(diaphragm) == "Not available"


def test_executive_summary_distinguishes_member_and_bridge_outcomes(monkeypatch):
    def girder_entries(_):
        return [("G1", "G1M1"), ("G2", "G2M1")]

    monkeypatch.setattr("osdagbridge.core.reports.executive_summary.get_girder_entries", girder_entries)
    results = {"design_results": {"per_girder": {
        "G1": {"checks": [{"dcr": .8, "name": "Flexure"}]},
        "G2": {"checks": [{"dcr": 1.2, "name": "Fatigue"}]},
    }}}
    tex = executive_summary({}, results, {})
    assert "Flexure & Fatigue" in tex
    assert "0.800 & 1.200" in tex
    assert "Overall Design Status} & Fail" in tex
    assert r"Steel Plate Girders:\allowbreak{} FAIL" in tex
    assert tex.index(r"\begin{minipage}") < tex.index("Final Bridge Geometry") < tex.index(r"\end{minipage}")



def test_generated_tables_disclose_unverified_efficiency():
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    from osdagbridge.core.reports.report_generator import ReportDataBridge

    outputs = {
        "crossbracing_design_results": {"G1-G2": {"diagonal": {
            "compression": {"Member.efficiency": 0.74, "Member.tension_capacity": 16.81},
        }}},
        "crossbracing_forces_dict": {"pairs": {"G1-G2": {
            "diag_compression_kN": 8.049, "diag_compression_gov_lc": "1.5 EQ (b)",
        }}},
        "deck_design_results": {"ur_composite_crack": 0.9914, "ur_bot_crack": 0.71},
    }
    chapter = ch5_design_checks({}, ReportDataBridge(outputs, {}, None))
    table = chapter.split("Cross Bracing Design --- Exported Efficiency", 1)[1].split(
        r"\end{longtable}", 1)[0]
    assert "Diagonal (C)" in table
    assert "8.049" in table
    assert "0.740" in table
    assert "16.810" not in table
    assert "governing denominator is not identified" in chapter
    assert "crack width and minimum crack-control reinforcement are distinct" in chapter
    assert outcome(component_checks(outputs, {})["Cross Bracing"]) == "Not available"
    outputs["crossbracing_design_results"]["G1-G2"]["diagonal"]["compression"]["Member.efficiency"] = float("nan")
    missing = ch5_design_checks({}, ReportDataBridge(outputs, {}, None))
    missing_table = missing.split("Cross Bracing Design --- Exported Efficiency", 1)[1].split(
        r"\end{longtable}", 1)[0]
    assert "nan" not in missing_table.lower()
    assert "PASS" not in missing_table



def test_transverse_capacity_mapping_and_nonfinite_efficiency():
    results = {"crossbracing_design_results": {"G1-G2": {"diagonal": {
        "compression": {"Member.efficiency": .74, "Member.tension_capacity": 16.81},
        "tension": {"Member.efficiency": .21, "Member.tension_capacity": 45},
    }, "chord": {"compression": {"Member.efficiency": float("inf")}}}}}
    checks = list(transverse_checks(results))
    assert [(check.label, check.capacity) for check in checks] == [
        ("Diagonal compression", None), ("Diagonal tension", 45.0),
    ]
    assert outcome(component_checks(results, {})["Cross Bracing"]) == "Not available"
