def ch7_quantities(input_dict, fig_paths=None):
    def _fmt_vol(key):
        val = input_dict.get(key, "N.A.")
        s = str(val) if val is not None else "N.A."
        return s.replace(r"\times", r"\times\allowbreak{}")

    boq_figs = ""
    if fig_paths:
        if fig_paths.get("boq_steel_tonnage"):
            p1 = str(fig_paths["boq_steel_tonnage"]).replace('\\', '/')
            boq_figs += r"""
\vspace{1.5em}
\begin{figure}[H]
\centering
\includegraphics[width=0.88\textwidth]{""" + p1 + r"""}
\caption{\textbf{Structural Steel Tonnage Breakdown by Component (MT)}}
\label{fig:boq_steel_tonnage}
\end{figure}
"""
        if fig_paths.get("boq_materials"):
            p2 = str(fig_paths["boq_materials"]).replace('\\', '/')
            boq_figs += r"""
\vspace{1.5em}
\begin{figure}[H]
\centering
\includegraphics[width=0.88\textwidth]{""" + p2 + r"""}
\caption{\textbf{Concrete Deck Slab Volume (m$^3$) and Reinforcement Steel Weight (MT)}}
\label{fig:boq_materials}
\end{figure}
\noindent\textit{Note: Concrete volume (m$^3$) and reinforcement steel weight (MT) are presented on separate subplots to prevent misleading comparisons across different physical units.}
"""

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\small
\setlength{\tabcolsep}{3pt}
\begin{longtable}{|C{1.0cm}|L{3.0cm}|C{2.8cm}|C{1.0cm}|C{2.0cm}|C{2.1cm}|C{2.1cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}}\\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Qty.} & \makecell{\textbf{Total Vol.}\\\textbf{(m$^3$)}} & \makecell{\textbf{Unit Wt.}\\\textbf{(MT)}} & \makecell{\textbf{Total Wt.}\\\textbf{(MT)}} \\
\hline
\endfirsthead
\caption[]{\textbf{Bill of Materials (Continued)}}\\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Qty.} & \makecell{\textbf{Total Vol.}\\\textbf{(m$^3$)}} & \makecell{\textbf{Unit Wt.}\\\textbf{(MT)}} & \makecell{\textbf{Total Wt.}\\\textbf{(MT)}} \\
\hline
\endhead
1 & Structural Steel (IS 2062) for Girders & """ + _fmt_vol("steel_girders_vol_formula") + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + _fmt_vol("bracing_top_vol_formula") + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + _fmt_vol("bracing_bot_vol_formula") + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + _fmt_vol("bracing_diag_vol_formula") + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + _fmt_vol("concrete_deck_vol_formula") + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\
\hline
4 & Reinforcement Steel (Fe 500) & """ + _fmt_vol("rebar_deck_vol_formula") + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\
\hline
5 & Shear Stud Connectors & """ + _fmt_vol("shear_studs_vol_formula") + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\
\hline
6 & Crash Barrier & """ + _fmt_vol("crash_barrier_vol_formula") + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\
\hline
\end{longtable}
\endgroup
""" + boq_figs
