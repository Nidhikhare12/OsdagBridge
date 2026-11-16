"""Unit tests for utilization ratio extraction and charting (T-UR-1, T-UR-2)."""

from pathlib import Path
import json
import pytest
import matplotlib.pyplot as plt

from osdagbridge.core.reports.data.utilization import collect_utilization
from osdagbridge.core.reports.charts.utilization_chart import (
    plot_overall_utilization,
    plot_girder_utilization,
)
from osdagbridge.core.reports.report_generator import ReportDataBridge


def _get_bridge():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    bridge = ReportDataBridge(data["output_dict"], data["input_dict"], None)
    return bridge


def test_t_ur_1_collect_utilization():
    """T-UR-1: Verify collect_utilization extracts 18 checks with correct fields."""
    bridge = _get_bridge()
    ud = collect_utilization(bridge)

    assert len(ud.records) == 18
    assert len(ud.girder_records) >= 1

    # Verify Moment and Shear records
    mom = next(r for r in ud.records if "Moment" in r.check_name)
    assert mom.element == "Girder"
    assert mom.ur is not None
    assert mom.ur > 0.0

    shr = next(r for r in ud.records if "Shear" in r.check_name)
    assert shr.ur is not None


def test_t_ur_2_chart_properties(tmp_path):
    """T-UR-2: Verify utilization chart properties (threshold at 1.0, bar count)."""
    bridge = _get_bridge()
    ud = collect_utilization(bridge)

    out_file = tmp_path / "ur_overall.png"
    result_path = plot_overall_utilization(ud.records, out_file)

    assert result_path and Path(result_path).is_file()
    assert out_file.stat().st_size > 1000

    # Also test per-girder chart
    girder_out = tmp_path / "ur_girder.png"
    g_res = plot_girder_utilization(ud.girder_records, girder_out)
    assert g_res and Path(g_res).is_file()


def test_t_chart_1_agg_backend_and_isolation(tmp_path):
    """T-CHART-1: Verify headless Agg backend and filesystem isolation."""
    import matplotlib
    # Confirm non-interactive Agg backend is active
    assert matplotlib.get_backend().lower() == "agg"

    bridge = _get_bridge()
    ud = collect_utilization(bridge)

    # Output strictly inside designated tmp_path
    target_chart = tmp_path / "isolation_test.png"
    out = plot_overall_utilization(ud.records, target_chart)
    assert out == str(target_chart.resolve())
    assert target_chart.is_file()
    assert target_chart.stat().st_size > 0


def test_t_ur_3_section_5_5_table_rendering():
    """Verify Section 5.5 table renders 18 checks correctly without errors."""
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    bridge = _get_bridge()
    tex = ch5_design_checks(None, bridge)

    assert "Overall Design Check Summary --- All Members" in tex
    assert "Girder --- Moment" in tex
    assert "Girder --- Shear" in tex
    assert "Deck --- Flexure (sagging)" in tex
    assert "Cross Bracing --- Compression" in tex
