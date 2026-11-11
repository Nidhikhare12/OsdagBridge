# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Refactored with PyLaTeX LongTable, repeated headers, and dynamic visualizations.
# =============================================================================

from osdagbridge.core.reports.styles import TABCOLSEP, ARRAYSTRETCH

def ch7_quantities(input_dict):
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

This chapter details the comprehensive Bill of Materials (BOM) for all structural components, including structural steel (IS 2062), deck concrete (M40), reinforcement steel (Fe 500), and shear connector studs.

\vspace{1em}
\begingroup
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.18}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}} \label{tab:bom} \\
\hline
\rowcolor{tableHeaderBg} \textbf{No.} & \textbf{Item Description} & \textbf{Vol.} & \textbf{Qty.} & \textbf{Total Volume} & \textbf{Wt. (MT)} & \textbf{Total Wt. (MT)} \\
\hline
\endfirsthead

\multicolumn{7}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{No.} & \textbf{Item Description} & \textbf{Vol.} & \textbf{Qty.} & \textbf{Total Volume} & \textbf{Wt. (MT)} & \textbf{Total Wt. (MT)} \\
\hline
\endhead

\hline
\multicolumn{7}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

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
\endgroup
\noindent\textit{Reinforcement weight is an estimate using 120 kg per cubic metre of concrete. End-diaphragm quantity is not available from the backend.}

\vspace{1.5em}
\begin{figure}[H]
\centering
\includegraphics[width=0.88\linewidth,keepaspectratio]{images/material_steel_tonnage.png}
\caption{\textbf{Structural Steel Tonnage Breakdown by Component (MT) --- Girders, Cross Bracing, End Diaphragms}}
\label{fig:steel_tonnage}
\end{figure}

\vspace{1.0em}
\begin{figure}[H]
\centering
\includegraphics[width=0.85\linewidth,keepaspectratio]{images/material_concrete_rebar.png}
\caption{\textbf{Primary Deck Materials: Concrete Volume ($m^3$) vs. Reinforcement Steel Weight (MT) Take-off}}
\label{fig:concrete_rebar}
\end{figure}
"""
