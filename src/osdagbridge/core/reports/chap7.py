import os
from osdagbridge.core.reports.report_utils import make_longtable_header


def ch7_quantities(input_dict, tmp_dir=None):
    def _v(key, fallback="N.A."):
        val = input_dict.get(key)
        if val in (None, "", "N.A.") or "placeholder" in str(val).lower():
            return fallback
        return str(val)

    charts_latex = ""
    if tmp_dir and isinstance(tmp_dir, str) and os.path.isdir(tmp_dir):
        try:
            from osdagbridge.core.reports.visualizations import (
                extract_quantity_data,
                generate_quantity_charts,
            )
            qty_data = extract_quantity_data(input_dict)
            chart1_path, chart2_path = generate_quantity_charts(qty_data, tmp_dir)

            parts = []
            if chart1_path and os.path.isfile(chart1_path):
                parts.append(
                    r"\vspace{1.5em}" + "\n"
                    r"\begin{figure}[H]" + "\n"
                    r"\centering" + "\n"
                    r"\includegraphics[width=0.88\textwidth]{qty_chart_steel.png}" + "\n"
                    r"\caption{\textbf{Fig.~7.1 --- Structural Steel Material Quantities (MT).} "
                    r"Breakdown of structural steel components. End-diaphragm quantity is not calculated in the current release; "
                    r"subtotal includes plate girders and cross bracing only.}" + "\n"
                    r"\label{fig:steel-quantities}" + "\n"
                    r"\end{figure}"
                )
            if chart2_path and os.path.isfile(chart2_path):
                parts.append(
                    r"\vspace{1.5em}" + "\n"
                    r"\begin{figure}[H]" + "\n"
                    r"\centering" + "\n"
                    r"\includegraphics[width=0.88\textwidth]{qty_chart_concrete_rebar.png}" + "\n"
                    r"\caption{\textbf{Fig.~7.2 --- Concrete and Reinforcement Quantities.} "
                    r"Left: Deck slab concrete volume (m$^3$). "
                    r"Right: Reinforcement steel weight (MT), based on an empirical estimate of "
                    r"120~kg/m$^3$ of concrete slab (actual bar schedule not computed).}" + "\n"
                    r"\label{fig:concrete-rebar-quantities}" + "\n"
                    r"\end{figure}"
                )
            charts_latex = "\n".join(parts)
        except Exception:
            charts_latex = (
                "\n"
                r"\noindent\textit{[Material quantity visualizations could not be generated.]}"
            )

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\setlength{\tabcolsep}{3.5pt}
""" + make_longtable_header(
        col_spec=r"|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|",
        caption=r"\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}",
        header_row=r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)}",
        label="tab:bom",
    ) + r"""
1 & Structural Steel (IS 2062) for Girders & """ + _v("steel_girders_vol_formula") + r""" & """ + _v("steel_girders_qty") + r""" & """ + _v("steel_girders_vol_total") + r""" & """ + _v("steel_girders_wt_single") + r""" & """ + _v("steel_girders_wt_total") + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + _v("bracing_top_vol_formula") + r""" & """ + _v("bracing_top_qty") + r""" & """ + _v("bracing_top_vol_total") + r""" & """ + _v("bracing_top_wt_single") + r""" & """ + _v("bracing_top_wt_total") + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + _v("bracing_bot_vol_formula") + r""" & """ + _v("bracing_bot_qty") + r""" & """ + _v("bracing_bot_vol_total") + r""" & """ + _v("bracing_bot_wt_single") + r""" & """ + _v("bracing_bot_wt_total") + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + _v("bracing_diag_vol_formula") + r""" & """ + _v("bracing_diag_qty") + r""" & """ + _v("bracing_diag_vol_total") + r""" & """ + _v("bracing_diag_wt_single") + r""" & """ + _v("bracing_diag_wt_total") + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + _v("concrete_deck_vol_formula") + r""" & """ + _v("concrete_deck_qty") + r""" & """ + _v("concrete_deck_vol_total") + r""" & """ + _v("concrete_deck_wt_single") + r""" & """ + _v("concrete_deck_wt_total") + r""" \\
\hline
4 & Reinforcement Steel (Fe 500) & """ + _v("rebar_deck_vol_formula") + r""" & """ + _v("rebar_deck_qty") + r""" & """ + _v("rebar_deck_vol_total") + r""" & """ + _v("rebar_deck_wt_single") + r""" & """ + _v("rebar_deck_wt_total") + r""" \\
\hline
5 & Shear Stud Connectors & """ + _v("shear_studs_vol_formula") + r""" & """ + _v("shear_studs_qty") + r""" & """ + _v("shear_studs_vol_total") + r""" & """ + _v("shear_studs_wt_single") + r""" & """ + _v("shear_studs_wt_total") + r""" \\
\hline
6 & Crash Barrier & """ + _v("crash_barrier_vol_formula") + r""" & """ + _v("crash_barrier_qty") + r""" & """ + _v("crash_barrier_vol_total") + r""" & """ + _v("crash_barrier_wt_single") + r""" & """ + _v("crash_barrier_wt_total") + r""" \\
\hline
\end{longtable}
\endgroup
""" + charts_latex + "\n"
