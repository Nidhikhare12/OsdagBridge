"""Regression tests for chart generation and thread-safe styling."""

import os

import matplotlib

from osdagbridge.core.reports import charts, styles


def _ratio_data():
    return [("Girders", 0.82), ("Deck", 0.67),
            ("Cross Bracing", 0.71), ("End Diaphragms", 0.55)]


def _material_data():
    return {
        "steel_girders_wt_total": 63.59,
        "bracing_top_wt_total": 5.2,
        "bracing_bot_wt_total": 4.8,
        "bracing_diag_wt_total": 7.1,
        "concrete_deck_vol_total": 90.0,
        "rebar_deck_wt_total": 10.8,
    }


def test_charts_write_png_assets_and_latex(tmp_path):
    ur_tex = charts.utilization_ratio_figure(_ratio_data(), str(tmp_path))
    mat_tex = charts.material_quantity_figure(_material_data(), str(tmp_path))
    assert os.path.exists(tmp_path / "ur_summary.png")
    assert os.path.exists(tmp_path / "material_quantities.png")
    assert r"\includegraphics" in ur_tex and "fig:ur-summary" in ur_tex
    assert r"\includegraphics" in mat_tex and "fig:material-quantities" in mat_tex


def test_chart_calls_do_not_mutate_global_matplotlib_state(tmp_path):
    # rcParams are applied once at import (main thread); calling the chart
    # functions must not reassign them from a report worker thread.
    before = dict(matplotlib.rcParams)
    charts.utilization_ratio_figure(_ratio_data(), str(tmp_path))
    charts.material_quantity_figure(_material_data(), str(tmp_path))
    assert dict(matplotlib.rcParams) == before


def test_global_style_pass_shades_repeated_headers():
    table = r"""\begin{longtable}{|L{3cm}|C{2cm}|}
\caption{Table}
\hline
\textbf{A} & \textbf{B} \\[6pt]
\hline
x & 1 \\
\hline
\end{longtable}
"""
    styled = styles.apply_global_styles(table)
    assert styled.count(r"\rowcolor{tableHead}") == 2
    assert styled.count(r"\endhead") == 1
