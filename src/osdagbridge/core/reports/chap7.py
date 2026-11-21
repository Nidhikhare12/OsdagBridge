# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# - Bill of Materials table with repeating headers across page breaks
# - Structural steel tonnage breakdown chart (Chart 1)
# - Concrete volume vs. reinforcement steel weight comparison chart (Chart 2)
# =============================================================================

from osdagbridge.core.reports.report_utils import _tex


def _format_vol_formula(val, default="N.A."):
    if val in (None, "", "None"):
        return default
    s = str(val).strip()
    if s.startswith("$") and s.endswith("$"):
        inner = s[1:-1].strip()
        if "=" in inner:
            p1, p2 = inner.split("=", 1)
            return r"\makecell[c]{\footnotesize $" + p1.strip() + r"$ \\ \footnotesize $= " + p2.strip() + r"$}"
        return r"{\footnotesize $" + inner + r"$}"
    return _tex(s)


def ch7_quantities(input_dict):
    steel_girders_vol = _format_vol_formula(input_dict.get("steel_girders_vol_formula", "Area x Length"))
    steel_girders_qty = _tex(input_dict.get("steel_girders_qty", "N.A."))
    steel_girders_vol_tot = _tex(input_dict.get("steel_girders_vol_total", "N.A."))
    steel_girders_wt_s = _tex(input_dict.get("steel_girders_wt_single", "N.A."))
    steel_girders_wt_tot = _tex(input_dict.get("steel_girders_wt_total", "N.A."))

    bracing_top_vol = _format_vol_formula(input_dict.get("bracing_top_vol_formula", "Area x Length"))
    bracing_top_qty = _tex(input_dict.get("bracing_top_qty", "N.A."))
    bracing_top_vol_tot = _tex(input_dict.get("bracing_top_vol_total", "N.A."))
    bracing_top_wt_s = _tex(input_dict.get("bracing_top_wt_single", "N.A."))
    bracing_top_wt_tot = _tex(input_dict.get("bracing_top_wt_total", "N.A."))

    bracing_bot_vol = _format_vol_formula(input_dict.get("bracing_bot_vol_formula", "Area x Length"))
    bracing_bot_qty = _tex(input_dict.get("bracing_bot_qty", "N.A."))
    bracing_bot_vol_tot = _tex(input_dict.get("bracing_bot_vol_total", "N.A."))
    bracing_bot_wt_s = _tex(input_dict.get("bracing_bot_wt_single", "N.A."))
    bracing_bot_wt_tot = _tex(input_dict.get("bracing_bot_wt_total", "N.A."))

    bracing_diag_vol = _format_vol_formula(input_dict.get("bracing_diag_vol_formula", "Area x Length"))
    bracing_diag_qty = _tex(input_dict.get("bracing_diag_qty", "N.A."))
    bracing_diag_vol_tot = _tex(input_dict.get("bracing_diag_vol_total", "N.A."))
    bracing_diag_wt_s = _tex(input_dict.get("bracing_diag_wt_single", "N.A."))
    bracing_diag_wt_tot = _tex(input_dict.get("bracing_diag_wt_total", "N.A."))

    concrete_vol = _format_vol_formula(input_dict.get("concrete_deck_vol_formula", "Width x Thickness x Length"))
    concrete_qty = _tex(input_dict.get("concrete_deck_qty", "N.A."))
    concrete_vol_tot = _tex(input_dict.get("concrete_deck_vol_total", "N.A."))
    concrete_wt_s = _tex(input_dict.get("concrete_deck_wt_single", "N.A."))
    concrete_wt_tot = _tex(input_dict.get("concrete_deck_wt_total", "N.A."))

    rebar_vol = _format_vol_formula(input_dict.get("rebar_deck_vol_formula", "Area x Length"))
    rebar_qty = _tex(input_dict.get("rebar_deck_qty", "N.A."))
    rebar_vol_tot = _tex(input_dict.get("rebar_deck_vol_total", "N.A."))
    rebar_wt_s = _tex(input_dict.get("rebar_deck_wt_single", "N.A."))
    rebar_wt_tot = _tex(input_dict.get("rebar_deck_wt_total", "N.A."))

    shear_studs_vol = _format_vol_formula(input_dict.get("shear_studs_vol_formula", "Area x Height"))
    shear_studs_qty = _tex(input_dict.get("shear_studs_qty", "N.A."))
    shear_studs_vol_tot = _tex(input_dict.get("shear_studs_vol_total", "N.A."))
    shear_studs_wt_s = _tex(input_dict.get("shear_studs_wt_single", "N.A."))
    shear_studs_wt_tot = _tex(input_dict.get("shear_studs_wt_total", "N.A."))

    cb_vol = _format_vol_formula(input_dict.get("crash_barrier_vol_formula", "Area x Length"))
    cb_qty = _tex(input_dict.get("crash_barrier_qty", "N.A."))
    cb_vol_tot = _tex(input_dict.get("crash_barrier_vol_total", "N.A."))
    cb_wt_s = _tex(input_dict.get("crash_barrier_wt_single", "N.A."))
    cb_wt_tot = _tex(input_dict.get("crash_barrier_wt_total", "N.A."))

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

This chapter details the quantitative bill of materials (BoQ) for structural steel, concrete, reinforcement, and accessories, accompanied by visual component-level distribution charts.

\section{Material Breakdown Charts}
\label{sec:material-charts}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{assets/material_steel_breakdown.png}
\caption{Structural Steel Tonnage Breakdown by Superstructure Component}
\label{fig:material-steel-breakdown}
\end{figure}

\vspace{0.5em}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{assets/material_concrete_rebar.png}
\caption{Deck Superstructure Concrete Volume and Reinforcement Steel Take-off}
\label{fig:material-concrete-rebar}
\end{figure}

\clearpage
\section{Bill of Materials}
\label{sec:bill-of-materials}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\setlength\LTleft{0pt}
\setlength\LTright\fill
\begin{longtable}{|C{0.9cm}|L{3.0cm}|C{4.2cm}|C{1.1cm}|C{1.6cm}|C{1.6cm}|C{1.6cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}}\label{tab:bill-of-materials} \\
\hline
\rowcolor{OsdagHeaderBg}
\makecell{\textbf{S.N.}} & \makecell{\textbf{Item Description}} & \makecell{\textbf{Volume}} & \makecell{\textbf{Qty}} & \makecell{\textbf{Total}\\\textbf{Vol (m$^3$)}} & \makecell{\textbf{Unit}\\\textbf{Wt (MT)}} & \makecell{\textbf{Total}\\\textbf{Wt (MT)}} \\[6pt]
\hline
\endfirsthead
\multicolumn{7}{c}{\small\textit{Bill of Materials (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\makecell{\textbf{S.N.}} & \makecell{\textbf{Item Description}} & \makecell{\textbf{Volume}} & \makecell{\textbf{Qty}} & \makecell{\textbf{Total}\\\textbf{Vol (m$^3$)}} & \makecell{\textbf{Unit}\\\textbf{Wt (MT)}} & \makecell{\textbf{Total}\\\textbf{Wt (MT)}} \\[6pt]
\hline
\endhead
\hline
\multicolumn{7}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
1 & Structural Steel (IS 2062) for Girders & """ + steel_girders_vol + r""" & """ + steel_girders_qty + r""" & """ + steel_girders_vol_tot + r""" & """ + steel_girders_wt_s + r""" & """ + steel_girders_wt_tot + r""" \\
\hline
\rowcolor{OsdagZebra}
2(a) & Cross Bracing - Top Chord & """ + bracing_top_vol + r""" & """ + bracing_top_qty + r""" & """ + bracing_top_vol_tot + r""" & """ + bracing_top_wt_s + r""" & """ + bracing_top_wt_tot + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + bracing_bot_vol + r""" & """ + bracing_bot_qty + r""" & """ + bracing_bot_vol_tot + r""" & """ + bracing_bot_wt_s + r""" & """ + bracing_bot_wt_tot + r""" \\
\hline
\rowcolor{OsdagZebra}
2(c) & Cross Bracing - Diagonal Chord & """ + bracing_diag_vol + r""" & """ + bracing_diag_qty + r""" & """ + bracing_diag_vol_tot + r""" & """ + bracing_diag_wt_s + r""" & """ + bracing_diag_wt_tot + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + concrete_vol + r""" & """ + concrete_qty + r""" & """ + concrete_vol_tot + r""" & """ + concrete_wt_s + r""" & """ + concrete_wt_tot + r""" \\
\hline
\rowcolor{OsdagZebra}
4 & Reinforcement Steel (Fe 500) & """ + rebar_vol + r""" & """ + rebar_qty + r""" & """ + rebar_vol_tot + r""" & """ + rebar_wt_s + r""" & """ + rebar_wt_tot + r""" \\
\hline
5 & Shear Stud Connectors & """ + shear_studs_vol + r""" & """ + shear_studs_qty + r""" & """ + shear_studs_vol_tot + r""" & """ + shear_studs_wt_s + r""" & """ + shear_studs_wt_tot + r""" \\
\hline
\rowcolor{OsdagZebra}
6 & Crash Barrier & """ + cb_vol + r""" & """ + cb_qty + r""" & """ + cb_vol_tot + r""" & """ + cb_wt_s + r""" & """ + cb_wt_tot + r""" \\
\hline
\end{longtable}
\endgroup
"""
