from osdagbridge.core.reports.report_utils import write_bar_chart, write_dual_axis_chart


def ch7_quantities(input_dict, chart_dir=None):
    # Charts use calculated quantities already injected into input_dict by
    # report_generator.calculate_material_quantities().
    _steel_labels = []
    _steel_values = []
    _steel_candidates = [
        ("Plate girders", "steel_girders_wt_total"),
        ("Cross bracing — top chord", "bracing_top_wt_total"),
        ("Cross bracing — bottom chord", "bracing_bot_wt_total"),
        ("Cross bracing — diagonal", "bracing_diag_wt_total"),
    ]
    for _label, _key in _steel_candidates:
        _value = input_dict.get(_key)
        if _value not in (None, "", "N.A.", "N/A"):
            _steel_labels.append(_label)
            _steel_values.append(_value)
    _end_diaphragm_weight = next(
        (input_dict.get(k) for k in (
            "end_diaphragm_wt_total", "end_diaphragms_wt_total",
            "diaphragm_wt_total", "end_diaphragm_steel_mt"
        ) if input_dict.get(k) not in (None, "", "N.A.", "N/A")),
        None
    )
    if _end_diaphragm_weight is not None:
        _steel_labels.append("End diaphragms")
        _steel_values.append(_end_diaphragm_weight)

    _steel_chart = write_bar_chart(
        chart_dir, "material_steel_tonnage.png", _steel_labels, _steel_values,
        "Steel Tonnage by Bridge Component", "Steel weight (MT)",
        horizontal=True
    )
    _comparison_chart = write_dual_axis_chart(
        chart_dir, "material_concrete_reinforcement.png",
        "Concrete deck", input_dict.get("concrete_deck_vol_total"),
        "Reinforcement steel", input_dict.get("rebar_deck_wt_total"),
        "Concrete and Reinforcement Quantities",
        "Concrete volume (m³)", "Reinforcement steel weight (MT)"
    )
    _charts_latex = ""
    if _steel_chart:
        _charts_latex += (
            "\n\\begin{figure}[H]\n\\centering\n"
            + r"\includegraphics[width=0.92\textwidth]{" + _steel_chart + "}\n"
            + r"\caption*{\textcolor{osdagGreen}{Steel tonnage by component (MT)}}" + "\n"
            + r"\end{figure}" + "\n"
        )
    if _comparison_chart:
        _charts_latex += (
            "\n\\begin{figure}[H]\n\\centering\n"
            + r"\includegraphics[width=0.92\textwidth]{" + _comparison_chart + "}\n"
            + r"\caption*{\textcolor{osdagGreen}{Concrete volume and reinforcement steel weight; separate axes retain the original units.}}" + "\n"
            + r"\end{figure}" + "\n"
        )

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
""" + _charts_latex + r"""
"""
