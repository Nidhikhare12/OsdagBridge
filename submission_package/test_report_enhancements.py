# =============================================================================
# Automated Regression & Feature Test Suite: Report Generator Enhancements
# Validates styles.py, repeated headers, table refactoring, and chart embeds.
# =============================================================================

import os
import tempfile
import pytest

from osdagbridge.core.reports.styles import (
    PAGE_GEOMETRY,
    COLORS,
    TABLE_LAYOUT,
    build_longtable_header,
    get_geometry_tex,
    get_table_setup_tex
)
from osdagbridge.core.reports.report_charts import (
    generate_overall_ur_chart,
    generate_steel_tonnage_chart,
    generate_material_comparison_chart
)
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities


def test_styles_configuration():
    """Verify that styles.py defines the single source of truth for formatting."""
    assert "bottom" in PAGE_GEOMETRY
    assert "footskip" in PAGE_GEOMETRY
    assert PAGE_GEOMETRY["footskip"] == "18mm"
    assert COLORS["primary"] == "#91B014"
    assert COLORS["fail"] == "#DC2626"
    assert TABLE_LAYOUT["arraystretch"] == 1.15

    geo_tex = get_geometry_tex()
    assert "geometry" in geo_tex
    assert "footskip=18mm" in geo_tex

    tbl_tex = get_table_setup_tex()
    assert "\\tabcolsep" in tbl_tex
    assert "\\arraystretch" in tbl_tex


def test_repeated_headers_structure():
    """Verify that build_longtable_header creates full PyLaTeX/LaTeX repeat headers."""
    header = build_longtable_header(
        caption="Sample Multi-page Table",
        col_spec="|C{3cm}|L{6cm}|",
        headers=["Col 1", "Col 2"],
        label="tab:sample_table"
    )
    assert r"\caption{\textbf{Sample Multi-page Table}}\label{tab:sample_table}\\" in header
    assert r"\endfirsthead" in header
    assert r"\endhead" in header
    assert r"\endfoot" in header
    assert r"\endlastfoot" in header
    assert "Continued from previous page" in header
    assert "Continued on next page..." in header


def test_chapter3_load_tables_separation():
    """Verify Chapter 3 separates vehicle live loads and footpath live loads."""
    from osdagbridge.core.utils.common import (
        KEY_SPAN,
        KEY_WC_LD_LANE_TABLE_COUNT,
        KEY_LL_IRC_CLASS_A,
        KEY_LL_IRC_70R_WHEELED,
        KEY_LL_FOOTPATH_PRESSURE_MODE,
        KEY_TS_FOOTPATH_WIDTH
    )

    mock_inputs = {
        KEY_SPAN: "32.0",
        KEY_WC_LD_LANE_TABLE_COUNT: "2",
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "as per irc 6",
        KEY_TS_FOOTPATH_WIDTH: "1.5",
    }
    tex = ch3_loads(mock_inputs)

    # 1. Vehicular Live Loads Table check
    assert r"\label{tab:vehicular_live_loads}" in tex
    assert "Class A" in tex
    assert "Class 70R (Wheeled)" in tex
    assert "Braking Force" in tex
    assert "Impact Factor" in tex

    # 2. Footway Live Load Table check
    assert r"\label{tab:footway_loads}" in tex
    assert "Footway Width Provided" in tex
    assert "1.50 m" in tex
    assert "IRC:6-2017 Clause 206.1" in tex


def test_overall_ur_chart_creation():
    """Verify programmatic generation of the UR summary chart with threshold line."""
    with tempfile.TemporaryDirectory() as td:
        out_png = os.path.join(td, "overall_ur_chart.png")
        data = {
            "Steel Plate Girders": 0.82,
            "Concrete Deck Slab": 0.68,
            "Cross Bracing": 0.45,
            "End Diaphragms": 0.55
        }
        res_path = generate_overall_ur_chart(data, out_png)
        assert os.path.exists(res_path)
        assert os.path.getsize(res_path) > 1000


def test_boq_charts_creation():
    """Verify programmatic generation of Chapter 7 material quantity bar charts."""
    with tempfile.TemporaryDirectory() as td:
        steel_png = os.path.join(td, "boq_steel.png")
        mat_png = os.path.join(td, "boq_mat.png")

        inputs = {
            "steel_girders_wt_total": "45.2",
            "bracing_top_wt_total": "2.4",
            "bracing_bot_wt_total": "2.1",
            "bracing_diag_wt_total": "4.8",
            "shear_studs_wt_total": "0.8",
            "concrete_deck_vol_total": "120.5",
            "rebar_deck_wt_total": "14.5"
        }
        p1 = generate_steel_tonnage_chart(inputs, steel_png)
        p2 = generate_material_comparison_chart(inputs, mat_png)

        assert os.path.exists(p1) and os.path.getsize(p1) > 1000
        assert os.path.exists(p2) and os.path.getsize(p2) > 1000


def test_chapter7_figures_embed():
    """Verify that Chapter 7 embeds both visualization figures."""
    fig_paths = {
        "boq_steel_chart": "assets/boq_steel_chart.png",
        "boq_materials_chart": "assets/boq_materials_chart.png"
    }
    tex = ch7_quantities({}, fig_paths=fig_paths)
    assert "Figure 7.1" in tex
    assert "Figure 7.2" in tex
    assert "assets/boq_steel_chart.png" in tex
    assert "assets/boq_materials_chart.png" in tex
    assert r"\label{tab:bom_summary}" in tex
