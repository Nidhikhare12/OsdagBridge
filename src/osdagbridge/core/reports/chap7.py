import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from osdagbridge.core.reports.styles import TABLE_PADDING
def ch7_quantities(input_dict, figure_data=None):
    # Material quantity charts
    _girder_wt = float(input_dict.get("steel_girders_wt_total", 0) or 0)
    _bracing_wt = sum(
        float(input_dict.get(k, 0) or 0)
        for k in (
            "bracing_top_wt_total",
            "bracing_bot_wt_total",
            "bracing_diag_wt_total",
        )
    )
    _concrete_vol = float(input_dict.get("concrete_deck_vol_total", 0) or 0)
    _rebar_wt = float(input_dict.get("rebar_deck_wt_total", 0) or 0)
    # End diaphragm quantity is not currently provided by the Chapter 7 input data.
    _end_diaphragm_wt = None
    if figure_data is not None:
        _fig1, _ax1 = plt.subplots(figsize=(8, 4.5))
        _ax1.bar(
            ["Girders", "Cross Bracing", "End Diaphragms"],
            [_girder_wt, _bracing_wt, _end_diaphragm_wt or 0],
        )
        _ax1.set_ylabel("Weight (MT)")
        _ax1.set_title("Structural Steel Quantity")
        if _end_diaphragm_wt is None:
            _ax1.text(2, 0, "N/A", ha="center", va="bottom")
        _fig1.tight_layout()
        _buf1 = io.BytesIO()
        _fig1.savefig(_buf1, format="png", dpi=180, bbox_inches="tight")
        plt.close(_fig1)
        figure_data["material_steel"] = _buf1.getvalue()
        _fig2, _ax2 = plt.subplots(figsize=(7, 4.5))
        _ax2.bar(
            ["Concrete Deck\n(m³)", "Reinforcement Steel\n(MT)"],
            [_concrete_vol, _rebar_wt],
        )
        _ax2.set_ylabel("Quantity")
        _ax2.set_title("Concrete and Reinforcement Quantity")
        _fig2.tight_layout()
        _buf2 = io.BytesIO()
        _fig2.savefig(_buf2, format="png", dpi=180, bbox_inches="tight")
        plt.close(_fig2)
        figure_data["material_concrete_rebar"] = _buf2.getvalue()
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\setlength{\tabcolsep}{""" + TABLE_PADDING + r"""}
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
\begin{figure}[H]
\centering
\includegraphics[width=0.90\textwidth]{images/material_steel.png}
\caption{\textbf{Structural Steel Quantity}}
\end{figure}
\begin{figure}[H]
\centering
\includegraphics[width=0.90\textwidth]{images/material_concrete_rebar.png}
\caption{\textbf{Concrete and Reinforcement Quantity}}
\end{figure}
"""


