# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Refactored in Phase 3B to use centralized styles and make_longtable
# =============================================================================

from typing import Optional
from osdagbridge.core.reports.helpers import make_longtable
from osdagbridge.core.reports.styles import TABLE_SPEC_BOQ, TABLE_COL_SEP_COMPACT


def ch7_quantities(input_dict: dict, steel_chart: Optional[str] = None, concrete_chart: Optional[str] = None) -> str:
    headers = [
        "S.N.",
        "Item Description",
        "Volume",
        "Quantity",
        "Total Volume",
        "Weight (MT)",
        "Total Weight (MT)",
    ]

    rows = [
        r"1 & Structural Steel (IS 2062) for Girders & " + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r" & " + str(input_dict.get("steel_girders_qty", "N.A.")) + r" & " + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r" & " + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r" & " + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"2(a) & Cross Bracing - Top Chord & " + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r" & " + str(input_dict.get("bracing_top_qty", "N.A.")) + r" & " + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r" & " + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r" & " + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"2(b) & Cross Bracing - Bottom Chord & " + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r" & " + str(input_dict.get("bracing_bot_qty", "N.A.")) + r" & " + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r" & " + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r" & " + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"2(c) & Cross Bracing - Diagonal Chord & " + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r" & " + str(input_dict.get("bracing_diag_qty", "N.A.")) + r" & " + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r" & " + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r" & " + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"3 & Concrete (M40) for Deck Slab & " + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r" & " + str(input_dict.get("concrete_deck_qty", "N.A.")) + r" & " + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r" & " + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r" & " + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"4 & Reinforcement Steel (Fe 500) & " + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r" & " + str(input_dict.get("rebar_deck_qty", "N.A.")) + r" & " + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r" & " + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r" & " + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"5 & Shear Stud Connectors & " + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r" & " + str(input_dict.get("shear_studs_qty", "N.A.")) + r" & " + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r" & " + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r" & " + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
        r"6 & Crash Barrier & " + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r" & " + str(input_dict.get("crash_barrier_qty", "N.A.")) + r" & " + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r" & " + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r" & " + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r" \\" + "\n" + r"\hline",
    ]

    table_tex = make_longtable(
        col_spec=TABLE_SPEC_BOQ,
        caption="Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
        headers=headers,
        rows=rows,
        label="tab:bom",
    )

    chart_block = ""
    if steel_chart and concrete_chart:
        chart_block = r"""
\vspace{1.5em}
\section{Material Breakdown Visualizations}
\label{sec:material-charts}

\begin{figure}[H]
\centering
\begin{subfigure}[b]{0.48\textwidth}
  \centering
  \includegraphics[width=\linewidth]{""" + steel_chart.replace("\\", "/") + r"""}
  \caption{Structural Steel Weight (MT)}
  \label{fig:steel-breakdown}
\end{subfigure}\hfill
\begin{subfigure}[b]{0.48\textwidth}
  \centering
  \includegraphics[width=\linewidth]{""" + concrete_chart.replace("\\", "/") + r"""}
  \caption{Concrete ($m^3$) vs Rebar (MT)}
  \label{fig:concrete-rebar}
\end{subfigure}
\caption{Material Quantity Breakdown}
\label{fig:material-breakdown}
\end{figure}
"""
    elif steel_chart:
        chart_block = r"""
\vspace{1.5em}
\section{Material Breakdown Visualizations}
\label{sec:material-charts}

\begin{figure}[H]
\centering
\includegraphics[width=0.7\textwidth]{""" + steel_chart.replace("\\", "/") + r"""}
\caption{Structural Steel Weight Breakdown (MT)}
\label{fig:steel-breakdown}
\end{figure}
"""

    return (
        r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\small
\setlength{\tabcolsep}{"""
        + TABLE_COL_SEP_COMPACT
        + r"""}
"""
        + table_tex
        + r"""
\endgroup
"""
        + chart_block
    )
