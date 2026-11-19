from osdagbridge.core.reports import report_generator as report
from osdagbridge.core.reports.chap5 import ch5_design_checks


def test_diaphragm_summary_uses_its_own_governing_check():
    outputs = {
        "member_properties.end_diaphragm_details.G2G3.type": "Rolled Beam",
        "end_diaphragm_forces_dict": {"pairs": {
            "G1-G2": {"diag_compression_kN": 125, "diag_compression_gov_lc": "ED combination"},
        }},
        "end_diaphragm_design_results": {
            "G1-G2": {"diagonal": {"compression": {
                "Optimum.UR": 1.25, "Design.Strength": 100, "Design.Status": False,
            }}},
            "G3-G4": {"chord": {"compression": {
                "Optimum.UR": 1.0, "Design.Status": False,
            }}},
        },
        "crossbracing_forces_dict": {"pairs": {
            "G1-G2": {"diag_compression_kN": 80, "diag_compression_gov_lc": "CB combination"},
        }},
        "crossbracing_design_results": {
            "G1-G2": {"diagonal": {"compression": {"Optimum.UR": 0.8, "Design.Strength": 100}}},
        },
    }
    chapter = ch5_design_checks([], report.ReportDataBridge(outputs, {}, None))
    row = next(line for line in chapter.splitlines() if line.startswith("End Diaphragm --- Axial Compression"))
    assert "ED combination" in row
    assert "125.00 kN" in row and "1.25" in row and "FAIL" in row
    assert "Rolled Beam" in chapter and "Check unavailable" in chapter
    assert "1.00 & FAIL" in chapter
    summary = chapter.split(r"\section{Overall Design Check Summary}", 1)[1]
    assert r"\endhead" in summary
    assert "Verdicts follow the design checks." in summary


def test_solver_inequality_labels_are_safe_in_pdflatex():
    from osdagbridge.core.reports.report_utils import _tex

    assert _tex("Leg ≤ limit & load ≥ 0") == (
        r"Leg \ensuremath{\leq} limit \& load \ensuremath{\geq} 0"
    )
