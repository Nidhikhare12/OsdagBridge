"""Unit tests for material quantities extraction and charts (T-QTY-1)."""

from pathlib import Path
import json
import pytest

from osdagbridge.core.reports.data.quantities import collect_quantities, QuantitySummary
from osdagbridge.core.reports.charts.quantity_charts import (
    plot_steel_quantities,
    plot_concrete_vs_rebar,
)
from osdagbridge.core.reports.report_generator import calculate_material_quantities


def _get_quantities_input():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    q = calculate_material_quantities(data["input_dict"], data["output_dict"])
    inp = dict(data["input_dict"])
    inp.update(q)
    return inp


def test_t_qty_1_collect_quantities():
    """T-QTY-1: Verify collect_quantities parses calculated quantities into floats."""
    inp = _get_quantities_input()
    qs = collect_quantities(inp)

    assert isinstance(qs, QuantitySummary)
    assert qs.steel_girders_wt == pytest.approx(16.98, 0.01)
    assert qs.bracing_top_wt == pytest.approx(0.08, 0.01)
    assert qs.bracing_bot_wt == pytest.approx(0.08, 0.01)
    assert qs.bracing_diag_wt == pytest.approx(0.19, 0.01)
    assert qs.bracing_total_wt == pytest.approx(0.35, 0.01)

    # End Diaphragm should be None (U8: not computed in upstream)
    assert qs.end_diaphragm_wt is None

    assert qs.shear_studs_wt == pytest.approx(0.158, 0.01)
    assert qs.concrete_deck_vol == pytest.approx(50.40, 0.01)
    assert qs.rebar_deck_wt == pytest.approx(6.05, 0.01)


def test_t_qty_2_quantity_charts_render(tmp_path):
    """Verify steel and concrete vs rebar quantity charts save successfully."""
    inp = _get_quantities_input()
    qs = collect_quantities(inp)

    steel_out = tmp_path / "steel_quantities.png"
    s_path = plot_steel_quantities(qs, steel_out)
    assert s_path and Path(s_path).is_file()
    assert steel_out.stat().st_size > 1000

    conc_out = tmp_path / "concrete_vs_rebar.png"
    c_path = plot_concrete_vs_rebar(qs, conc_out)
    assert c_path and Path(c_path).is_file()
    assert conc_out.stat().st_size > 1000


def test_t_qty_3_missing_data_handling():
    """Verify missing and 'N.A.' strings are parsed safely to None without errors."""
    sparse_inp = {
        "steel_girders_wt_total": "N.A.",
        "bracing_top_wt_total": None,
        "concrete_deck_vol_total": "",
        "rebar_deck_wt_total": "invalid_num",
    }
    qs = collect_quantities(sparse_inp)
    assert qs.steel_girders_wt is None
    assert qs.bracing_top_wt is None
    assert qs.concrete_deck_vol is None
    assert qs.rebar_deck_wt is None
