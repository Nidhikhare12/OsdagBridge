import pytest

from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.reports import report_charts
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.design_summary import design_summary, verdict
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.utils.common import KEY_SPAN, KEY_TS_NO_OF_GIRDERS


def test_summary_uses_per_girder_checks_and_stored_verdicts():
    inputs = {KEY_TS_NO_OF_GIRDERS: 2}
    outputs = {
        "design_results": {"per_girder": {
            "G1": {"checks": [{"name": "Bending", "dcr": 0.5, "status": "PASS"}]},
            "G2": {"checks": [{"name": "Shear", "dcr": 1.0, "status": "PASS"}]},
        }},
        "deck_design_results": {
            "ur_oh_punch": 1.0, "check_statuses": {"ur_oh_punch": False},
        },
        "crossbracing_design_results": {
            "G1-G2": {"diagonal": {"tension": {"Member.efficiency": 0.7}}},
        },
        "end_diaphragm_design_results": {
            "G1-G2": {"diagonal": {"compression": {"Optimum.UR": 0.8}}},
        },
    }
    _, groups = design_summary(inputs, outputs)
    assert verdict(groups["Girder"]) == "Pass"
    assert verdict(groups["Deck slab"]) == "Fail"
    assert groups["Cross bracing"][0].ur == 0.7
    assert groups["End Diaphragm"][0].ur == 0.8
    latex = executive_summary(inputs, outputs, {})
    assert "Overall Design Status} & Fail" in latex
    assert "Governing Check & Bending & Shear" in latex
    assert "Utilization Ratio & 0.50 & 1.00" in latex

    outputs["design_results"]["per_girder"]["G2"]["checks"][0]["status"] = "FAIL"
    _, groups = design_summary(inputs, outputs)
    assert verdict(groups["Girder"]) == "Fail"
    assert groups["Girder"][1].ur == 1.0


def test_configured_diaphragm_without_checks_is_incomplete():
    inputs = {KEY_TS_NO_OF_GIRDERS: 2}
    outputs = {"member_properties.end_diaphragm_details.G1G2.type": "Rolled Beam"}
    _, groups = design_summary(inputs, outputs)
    assert verdict(groups["End Diaphragm"]) == "Incomplete"


@pytest.mark.parametrize("missing_mass", [False, True])
def test_design_takeoff_for_all_diaphragm_types(monkeypatch, tmp_path, missing_mass):
    inputs = {KEY_SPAN: 20, KEY_TS_NO_OF_GIRDERS: 4}
    outputs = {}
    for pair, kind in (("G1G2", "Rolled Beam"), ("G2G3", "Welded Beam"),
                       ("G3G4", "Cross Bracing")):
        outputs[f"member_properties.end_diaphragm_details.{pair}.type"] = kind
    outputs["member_properties.end_diaphragm_details.G3G4.bottom_chord"] = False
    for pair, member, length_key, length, mass, area in (
        ("G1G2", "end_diaphragm", "L", 2, 10, 25),
        ("G2G3", "end_diaphragm", "L", 3, 30, 45),
        ("G3G4", "end_diaphragm", "design_length_m", 4, 20, 10),
        ("G3G4", "top_chord", "design_length_m", 2, 15, 20),
    ):
        prefix = f"transverse_member_design.ed.section_properties.{member}.{pair}"
        outputs.update({f"{prefix}.{length_key}": length, f"{prefix}.M": mass, f"{prefix}.A": area})
    if missing_mass:
        del outputs["transverse_member_design.ed.section_properties.top_chord.G3G4.M"]

    quantities = calculate_material_quantities(inputs, outputs)
    assert quantities["end_diaphragm_qty"] == 10
    assert quantities["end_diaphragm_vol_total"] == pytest.approx(0.061)
    expected = quantities["end_diaphragm_wt_total"]
    assert expected == (None if missing_mass else pytest.approx(0.60))

    plotted = {}
    def capture(directory, filename, labels, values, *args):
        plotted[filename] = dict(zip(labels, values))
        return filename

    monkeypatch.setattr(report_charts, "_save_chart", capture)
    charts = report_charts.materials_charts(tmp_path, quantities)
    assert plotted["material_steel_quantities.pdf"]["End Diaphragms"] == expected
    row = next(line for line in ch7_quantities(quantities, charts).splitlines()
               if "End Diaphragm Steel" in line)
    assert "& -- & " + ("N/A" if missing_mass else "0.60") in row
