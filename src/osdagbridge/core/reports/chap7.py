# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
#
# Generates Table 7.1 (Bill of Materials) as a PyLaTeX LongTable with repeated
# column headers and embeds dynamic material quantity charts:
# - Structural Steel Tonnage Breakdown by Component (Girders, Bracing, Diaphragms)
# - Major Bridge Materials Summary (Concrete volume m³, Rebar MT)
# =============================================================================

from osdagbridge.core.reports.styles import format_longtable
from osdagbridge.core.reports.report_utils import _fig_embed


def ch7_quantities(input_dict, fig_paths=None):
    fig_paths = fig_paths or {}

    col_spec = r"|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|"
    caption = "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)"
    header_cells = (
        r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & "
        r"\textbf{Quantity} & \textbf{Total Vol. (m$^3$)} & \textbf{Wt. (MT)} & \textbf{Total Wt. (MT)}"
    )

    rows = []
    # 1. Structural Steel for Girders
    rows.append(
        r"1 & Structural Steel (IS 2062) for Girders & " +
        str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("steel_girders_qty", "N.A.")) + r" & " +
        str(input_dict.get("steel_girders_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("steel_girders_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("steel_girders_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 2. Cross Bracing
    rows.append(
        r"2(a) & Cross Bracing --- Top Chord & " +
        str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("bracing_top_qty", "N.A.")) + r" & " +
        str(input_dict.get("bracing_top_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("bracing_top_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("bracing_top_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )
    rows.append(
        r"2(b) & Cross Bracing --- Bottom Chord & " +
        str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("bracing_bot_qty", "N.A.")) + r" & " +
        str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )
    rows.append(
        r"2(c) & Cross Bracing --- Diagonal Chord & " +
        str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("bracing_diag_qty", "N.A.")) + r" & " +
        str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 3. End Diaphragms
    rows.append(
        r"3 & End Diaphragms (IS 2062) & " +
        str(input_dict.get("steel_ed_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("steel_ed_qty", "N.A.")) + r" & " +
        str(input_dict.get("steel_ed_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("steel_ed_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("steel_ed_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 4. Concrete Deck Slab
    rows.append(
        r"4 & Concrete (M40) for Deck Slab & " +
        str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("concrete_deck_qty", "N.A.")) + r" & " +
        str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 5. Reinforcement Steel
    rows.append(
        r"5 & Reinforcement Steel (Fe 500) & " +
        str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("rebar_deck_qty", "N.A.")) + r" & " +
        str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 6. Shear Studs
    rows.append(
        r"6 & Shear Stud Connectors & " +
        str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("shear_studs_qty", "N.A.")) + r" & " +
        str(input_dict.get("shear_studs_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("shear_studs_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("shear_studs_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    # 7. Crash Barrier
    rows.append(
        r"7 & Crash Barrier & " +
        str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r" & " +
        str(input_dict.get("crash_barrier_qty", "N.A.")) + r" & " +
        str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r" & " +
        str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r" & " +
        str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r" \\[4pt]" + "\n" + r"\hline"
    )

    body_rows = "\n".join(rows)

    table_tex = format_longtable(
        col_spec=col_spec,
        caption=caption,
        header_rows=header_cells,
        body_rows=body_rows,
        ncols=7,
        label="tab:material-takeoff",
        note="Note: All quantities computed from completed design geometry and material unit weights per IS 2062 and IRC 112."
    )

    # Dynamic Material Quantity Charts (Requirement 5)
    steel_chart_p = fig_paths.get("steel_tonnage")
    mat_chart_p = fig_paths.get("materials_summary")

    charts_tex = r"""
\vspace{1.5em}
\section{Material Quantity Charts}
\label{sec:material-charts}

This section illustrates the distribution of structural steel tonnage across bridge superstructure components and summarizes total volume and weight for primary construction materials.

\vspace{1em}
"""

    if steel_chart_p:
        charts_tex += (
            r"\begin{figure}[H]" + "\n"
            r"\centering" + "\n"
            r"\includegraphics[width=0.88\textwidth]{" + steel_chart_p.replace('\\', '/') + r"}" + "\n"
            r"\caption{\textbf{Structural Steel Tonnage Breakdown by Component (MT)}}" + "\n"
            r"\label{fig:steel-tonnage-chart}" + "\n"
            r"\end{figure}" + "\n\n"
        )

    if mat_chart_p:
        charts_tex += (
            r"\begin{figure}[H]" + "\n"
            r"\centering" + "\n"
            r"\includegraphics[width=0.88\textwidth]{" + mat_chart_p.replace('\\', '/') + r"}" + "\n"
            r"\caption{\textbf{Major Bridge Materials Summary (Concrete Volume and Rebar Weight)}}" + "\n"
            r"\label{fig:materials-summary-chart}" + "\n"
            r"\end{figure}" + "\n"
        )

    return rf"""
\chapter{{Material Take-off \& Quantity Summary}}
\label{{ch:material-takeoff}}

This chapter presents the bill of materials and dynamic quantity distributions for structural steel, concrete, reinforcement, and connector elements based on the final completed design.

\begingroup
\setlength{{\tabcolsep}}{{3.5pt}}
{table_tex}
\endgroup

{charts_tex}
"""
