# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Refactored for OsdagBridge LaTeX Report Enhancement
# - Repeated table headers across page breaks on Bill of Materials
# - Dynamic embedding of Structural Steel & Concrete vs. Rebar Bar Charts
# =============================================================================

from typing import Optional, Dict


def ch7_quantities(input_dict: dict, fig_paths: Optional[Dict[str, str]] = None) -> str:
    fig_paths = fig_paths or {}

    charts_tex = ""
    steel_chart_path = fig_paths.get("steel_quantities")
    conc_chart_path = fig_paths.get("concrete_vs_rebar")

    if steel_chart_path:
        p_steel = steel_chart_path.replace("\\", "/")
        charts_tex += (
            r"\vspace{1.5em}" + "\n"
            r"\begin{figure}[H]" + "\n"
            r"\centering" + "\n"
            r"\includegraphics[width=0.88\textwidth]{" + p_steel + "}\n"
            r"\caption{\textbf{Structural Steel Tonnage Breakdown by Superstructure Component}}" + "\n"
            r"\label{fig:steel-tonnage-breakdown}" + "\n"
            r"\end{figure}" + "\n"
        )

    if conc_chart_path:
        p_conc = conc_chart_path.replace("\\", "/")
        charts_tex += (
            r"\vspace{1.5em}" + "\n"
            r"\begin{figure}[H]" + "\n"
            r"\centering" + "\n"
            r"\includegraphics[width=0.84\textwidth]{" + p_conc + "}\n"
            r"\caption{\textbf{Deck Slab Material Balance: Concrete Volume ($m^3$) vs. Reinforcement Steel Weight (MT)}}" + "\n"
            r"\label{fig:concrete-vs-rebar}" + "\n"
            r"\end{figure}" + "\n"
        )

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

This chapter details the Bill of Materials (BoQ) for all primary structural components, including plate girders, cross bracing, deck slab concrete, reinforcement steel, shear connectors, and crash barriers.

\vspace{1em}
\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{4.2cm}|C{2.4cm}|C{1.6cm}|C{2.0cm}|C{1.8cm}|C{2.0cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}} \label{tab:bom} \\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Unit Formula} & \textbf{Qty} & \textbf{Total Vol.} & \textbf{Unit Wt (MT)} & \textbf{Total Wt (MT)} \\[6pt]
\hline
\endfirsthead
\multicolumn{7}{c}{\small\textit{Table \thetable{} (Continued) --- Bill of Materials}} \\[4pt]
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Unit Formula} & \textbf{Qty} & \textbf{Total Vol.} & \textbf{Unit Wt (MT)} & \textbf{Total Wt (MT)} \\[6pt]
\hline
\endhead
\hline
\multicolumn{7}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing --- Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing --- Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing --- Diagonal & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
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
\endgroup

\noindent\textit{Note: Material quantities are derived directly from 3D analytical geometry and component cross-sections per IS:2062 and IRC:112-2020.}

""" + charts_tex
