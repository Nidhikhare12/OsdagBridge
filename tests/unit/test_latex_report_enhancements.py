from pathlib import Path

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.report_charts import (
    collect_utilization_data,
    generate_material_charts,
    generate_utilization_chart,
)
from osdagbridge.core.reports.styles import ensure_repeated_longtable_headers
from osdagbridge.core.utils.common import (
    KEY_FOOTPATH,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_CLASS_A,
    KEY_SPAN,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
)


def test_every_longtable_receives_a_repeated_header():
    source = r"""
\chapter{Checks}
\begin{longtable}{|c|c|}
\caption{Example}
\hline
\textbf{A} & \textbf{B} \\
\hline
\multirow{2}{*}{\makecell{G4}} & two \\
\hline
\end{longtable}
\begin{longtable}{|c|}
\hline
\textbf{C} \\
\hline
three \\
\hline
\end{longtable}
"""
    rendered = ensure_repeated_longtable_headers(source)
    assert rendered.count(r"\endfirsthead") == 2
    assert rendered.count(r"\endhead") == 2
    assert rendered.count(r"\textbf{A} & \textbf{B}") == 2
    assert rendered.count(r"\textbf{C}") == 2
    assert r"\caption{Example}\\" in rendered
    assert rendered.count(r"\par\Needspace{12\baselineskip}") == 2
    assert r"\multirow" not in rendered
    assert r"\makecell{G4} & two" in rendered
    assert r"\chapter{Checks}" + "\n" + r"\thispagestyle{main}" in rendered


def test_longtable_without_column_headings_is_rejected():
    source = r"""
\begin{longtable}{|c|c|}
\caption{Headerless table}
\hline
first data value & second data value \\
\hline
\end{longtable}
"""
    try:
        ensure_repeated_longtable_headers(source)
    except ValueError as exc:
        assert "explicit bold column-heading row" in str(exc)
    else:
        raise AssertionError("A longtable without column headings was accepted")


def test_chapter_three_separates_selected_vehicle_and_footway_loads():
    inputs = {
        KEY_SPAN: 30,
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_TRACKED: False,
        KEY_WC_LD_LANE_TABLE_COUNT: 2,
        KEY_FOOTPATH: "Both Sides",
        KEY_TS_FOOTPATH_WIDTH: 1.5,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
    }
    latex = ch3_loads(inputs)
    assert "Vehicle Live Loads (LL)" in latex
    assert "Associated Vehicle Load Parameters" in latex
    assert "Footway Live Load" in latex
    assert "Class A" in latex
    assert "Class 70R (Tracked)" not in latex
    assert "Both Sides" in latex
    assert "No footway selected" not in latex


def test_all_four_utilization_groups_and_material_charts_are_generated(tmp_path):
    member_result = {
        "G1-G2": {
            "diagonal": {
                "compression": {
                    "Optimum.UR": 1.12,
                    "Optimum.Designation": "ISA 75x75x8",
                    "Design.Strength": 110.0,
                }
            }
        }
    }
    output = {
        "design_results": {
            "per_girder": {"G1": {"max_dcr": 0.82, "checks": []}}
        },
        "deck_report_values": {
            "deck_design.m_uls_sag": 40.0,
            "deck_design.mu_bot": 50.0,
        },
        "crossbracing_design_results": member_result,
        "end_diaphragm_design_results": member_result,
    }
    # Use the real key strings imported by the chart module for deck data.
    from osdagbridge.core.reports import report_charts
    output["deck_report_values"] = {
        report_charts.KEY_DD_M_ULS_SAG: 40.0,
        report_charts.KEY_DD_MU_BOT: 50.0,
    }
    grouped = collect_utilization_data(output)
    assert set(grouped) == {
        "Steel Plate Girders", "Concrete Deck Slab", "Cross Bracing", "End Diaphragms"
    }
    assert all(grouped.values())

    utilization_path = Path(generate_utilization_chart(output, str(tmp_path)))
    quantities = {
        "steel_girders_wt_total": 12.5,
        "bracing_top_wt_total": 0.3,
        "bracing_bot_wt_total": 0.3,
        "bracing_diag_wt_total": 0.8,
        "end_diaphragm_wt_total": 0.5,
        "concrete_deck_vol_total": 90.0,
        "rebar_deck_wt_total": 8.0,
    }
    material_paths = generate_material_charts(quantities, str(tmp_path))
    assert utilization_path.is_file() and utilization_path.stat().st_size > 0
    assert set(material_paths) == {"steel_quantities", "deck_material_quantities"}
    assert all(Path(path).is_file() and Path(path).stat().st_size > 0
               for path in material_paths.values())
