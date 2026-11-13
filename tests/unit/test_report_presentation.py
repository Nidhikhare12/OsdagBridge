from pathlib import Path

from osdagbridge.core.reports.chart_generator import material_charts, utilization_chart, utilization_ratios
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.table_utils import longtable, normalise_longtables


def test_longtable_has_complete_continuation_structure():
    tex = longtable("|l|l|", "Caption", "A & B", ["one & two"])
    for marker in (r"\endfirsthead", r"\endhead", r"\endfoot", r"\endlastfoot"):
        assert marker in tex


def test_legacy_chapter_tables_gain_repeated_headers():
    tex = normalise_longtables(ch3_loads({}))
    assert tex.count(r"\endfirsthead") >= 6
    assert "Vehicle Live Loads" in tex
    assert "Footway Live Load" in tex


def test_utilization_chart_uses_available_results_only(tmp_path: Path):
    output = {
        "design_results": {"per_girder": {"G1": {"checks": [{"dcr": 0.8}]}}},
        "deck_design_results": {"utilization_ratio": 1.0},
        "crossbracing_design_results": {"G1-G2": {"efficiency": 1.2}},
    }
    ratios = utilization_ratios(output)
    assert ratios == {"Steel Plate Girders": 0.8, "Concrete Deck Slab": 1.0, "Cross Bracing": 1.2}
    image = utilization_chart(output, tmp_path / "ur.png")
    assert image and image.exists()


def test_material_charts_skip_unavailable_values_and_keep_zero(tmp_path: Path):
    steel, concrete = material_charts({"steel_girders_wt_total": "0", "rebar_deck_wt_total": "2.5"}, tmp_path)
    assert steel and steel.exists()
    assert concrete and concrete.exists()
