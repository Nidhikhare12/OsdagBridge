from .report_utils import _fig_embed


def _quantity(inputs, key):
    value = inputs.get(key)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value) if value is not None else "N/A"


def ch7_quantities(input_dict, charts=()):
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
1 & Structural Steel (IS 2062) for Girders & """ + _quantity(input_dict, "steel_girders_vol_formula") + r""" & """ + _quantity(input_dict, "steel_girders_qty") + r""" & """ + _quantity(input_dict, "steel_girders_vol_total") + r""" & """ + _quantity(input_dict, "steel_girders_wt_single") + r""" & """ + _quantity(input_dict, "steel_girders_wt_total") + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + _quantity(input_dict, "bracing_top_vol_formula") + r""" & """ + _quantity(input_dict, "bracing_top_qty") + r""" & """ + _quantity(input_dict, "bracing_top_vol_total") + r""" & """ + _quantity(input_dict, "bracing_top_wt_single") + r""" & """ + _quantity(input_dict, "bracing_top_wt_total") + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + _quantity(input_dict, "bracing_bot_vol_formula") + r""" & """ + _quantity(input_dict, "bracing_bot_qty") + r""" & """ + _quantity(input_dict, "bracing_bot_vol_total") + r""" & """ + _quantity(input_dict, "bracing_bot_wt_single") + r""" & """ + _quantity(input_dict, "bracing_bot_wt_total") + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + _quantity(input_dict, "bracing_diag_vol_formula") + r""" & """ + _quantity(input_dict, "bracing_diag_qty") + r""" & """ + _quantity(input_dict, "bracing_diag_vol_total") + r""" & """ + _quantity(input_dict, "bracing_diag_wt_single") + r""" & """ + _quantity(input_dict, "bracing_diag_wt_total") + r""" \\
\hline
2(d) & End Diaphragm Steel (design take-off) & -- & """ + _quantity(input_dict, "end_diaphragm_qty") + r""" & """ + _quantity(input_dict, "end_diaphragm_vol_total") + r""" & -- & """ + _quantity(input_dict, "end_diaphragm_wt_total") + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + _quantity(input_dict, "concrete_deck_vol_formula") + r""" & """ + _quantity(input_dict, "concrete_deck_qty") + r""" & """ + _quantity(input_dict, "concrete_deck_vol_total") + r""" & """ + _quantity(input_dict, "concrete_deck_wt_single") + r""" & """ + _quantity(input_dict, "concrete_deck_wt_total") + r""" \\
\hline
4 & Reinforcement Steel (Fe 500, estimate) & """ + _quantity(input_dict, "rebar_deck_vol_formula") + r""" & """ + _quantity(input_dict, "rebar_deck_qty") + r""" & """ + _quantity(input_dict, "rebar_deck_vol_total") + r""" & """ + _quantity(input_dict, "rebar_deck_wt_single") + r""" & """ + _quantity(input_dict, "rebar_deck_wt_total") + r""" \\
\hline
5 & Shear Stud Connectors & """ + _quantity(input_dict, "shear_studs_vol_formula") + r""" & """ + _quantity(input_dict, "shear_studs_qty") + r""" & """ + _quantity(input_dict, "shear_studs_vol_total") + r""" & """ + _quantity(input_dict, "shear_studs_wt_single") + r""" & """ + _quantity(input_dict, "shear_studs_wt_total") + r""" \\
\hline
6 & Crash Barrier & """ + _quantity(input_dict, "crash_barrier_vol_formula") + r""" & """ + _quantity(input_dict, "crash_barrier_qty") + r""" & """ + _quantity(input_dict, "crash_barrier_vol_total") + r""" & """ + _quantity(input_dict, "crash_barrier_wt_single") + r""" & """ + _quantity(input_dict, "crash_barrier_wt_total") + r""" \\
\hline
\end{longtable}
""" + "\n".join(
        _fig_embed(path, caption, width=r"0.85\textwidth")
        for path, caption in zip(charts, (
            "Structural steel weight by component.",
            "Deck concrete volume and estimated reinforcement weight.",
        ))
    )
