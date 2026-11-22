from . import styles
from osdagbridge.core.reports.report_utils import _fig_or_placeholder


def _f(input_dict, key):
    try:
        return float(str(input_dict.get(key, "")).replace(",", ""))
    except (TypeError, ValueError):
        return None


def ch7_quantities(input_dict, chart_dir=None):
    return r"""
""" + styles.chapter_title(r"Material Take-off \& Quantity Summary") + r"""
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
""" + styles.table_padding(styles.TABCOLSEP_TIGHT) + r"""
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
\endfirsthead
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
\endhead
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\
\hline
4 & Reinforcement Steel (Fe 500) & """ + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\
\hline
5 & Shear Stud Connectors & """ + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\
\hline
6 & Crash Barrier & """ + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\
\hline
\end{longtable}

""" + _ch7_chart_block(input_dict, chart_dir) + r"""
"""

def _ch7_chart_block(input_dict, chart_dir):
    """Material bar charts for chapter 7: steel tonnage by component, and
    deck concrete volume against reinforcement weight."""
    if not chart_dir:
        return ""
    import os
    from .ur_charts import render_bar_chart

    bracing_parts = [_f(input_dict, key) for key in (
        "bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    bracing_total = (sum(bracing_parts)
                     if all(v is not None for v in bracing_parts) else None)
    steel = [
        ("Girders", _f(input_dict, "steel_girders_wt_total")),
        ("Cross Bracing", bracing_total),
        ("End Diaphragms", _f(input_dict, "end_diaphragms_wt_total")),
    ]
    concrete_vs_rebar = [
        ("Concrete (m3)", _f(input_dict, "concrete_deck_vol_total")),
        ("Reinforcement (MT)", _f(input_dict, "rebar_deck_wt_total")),
    ]
    figs = []
    specs = [
        ("Structural Steel Tonnage by Component", steel, "Weight (MT)", "qty_steel"),
        ("Deck Concrete Volume vs Reinforcement Weight", concrete_vs_rebar,
         "Quantity", "qty_concrete_rebar"),
    ]
    for title, points, ylabel, stem in specs:
        png = os.path.join(chart_dir, stem + ".png")
        try:
            ok = render_bar_chart(title, points, ylabel, png)
        except Exception:
            ok = False
        figs.append(_fig_or_placeholder("images/" + stem + ".png" if ok else None, title))
    return (
        r"\vspace{1em}" + "\n"
        + r"\noindent\textbf{Material Quantity Charts}" + "\n"
        + "\n".join(figs) + "\n"
        + r"\noindent\textit{N/A means that the material take-off has not supplied a quantity; it does not mean zero.}" + "\n"
    )

