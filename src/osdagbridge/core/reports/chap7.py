import re


def ch7_quantities(input_dict):
    report = r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\setlength{\tabcolsep}{\ReportCompactTablePadding}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \scriptsize\textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
\endfirsthead
\multicolumn{7}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \scriptsize\textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
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
2(d) & End Diaphragms & """ + str(input_dict.get("end_diaphragm_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_qty", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_total", "N.A.")) + r""" \\
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
\vspace{0.4em}
\noindent\footnotesize\textit{Quantity basis:} deck concrete is calculated from the full deck width, slab thickness and span. End-diaphragm steel uses design-stage member mass where available, with the saved per-member section mass and configured support-frame geometry as a fallback. Deck reinforcement is a theoretical straight-bar estimate from the designed bar diameters and spacings (main transverse bars per girder bay and longitudinal distribution bars); hooks, anchorage, laps, chairs and wastage are excluded.\normalsize
"""

    # -------------------------------------------------------------------------
    # Material quantity charts. Do not put m3 and MT on one numerical axis.
    # Structural steel and reinforcement are shown in MT; concrete is shown
    # separately in m3. Missing quantities remain visibly unavailable.
    # -------------------------------------------------------------------------
    def _quantity(value):
        if value in (None, ""):
            return None
        text_value = str(value).strip().replace(",", "")
        if text_value.upper() in {"N.A.", "NA", "NONE", "-"}:
            return None
        try:
            number = float(text_value)
            return number if number >= 0 and number == number else None
        except (TypeError, ValueError):
            return None

    girder_mt = _quantity(input_dict.get("steel_girders_wt_total"))
    cb_parts = [_quantity(input_dict.get(key)) for key in (
        "bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    cross_bracing_mt = (sum(cb_parts) if all(v is not None for v in cb_parts) else None)
    end_diaphragm_mt = _quantity(input_dict.get("end_diaphragm_wt_total"))
    shear_studs_mt = _quantity(input_dict.get("shear_studs_wt_total"))
    steel_components = [
        ("Girders", girder_mt), ("Cross bracing", cross_bracing_mt),
        ("End diaphragms", end_diaphragm_mt), ("Shear studs", shear_studs_mt),
    ]
    known_steel_subtotal = _quantity(input_dict.get("structural_steel_wt_subtotal"))
    deck_concrete_m3 = _quantity(input_dict.get("concrete_deck_vol_total"))
    barrier_m3 = _quantity(input_dict.get("crash_barrier_vol_total"))
    barrier_configured = str(input_dict.get("crash_barrier_qty", "0")).strip() not in {"0", "", "N.A."}
    rebar_mt = _quantity(input_dict.get("rebar_deck_wt_total"))
    steel_mt = known_steel_subtotal

    if any(v is not None for v in (steel_mt, deck_concrete_m3, barrier_m3, rebar_mt)):
        try:
            import os
            import tempfile
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg

            figure = Figure(figsize=(10.0, 4.8), constrained_layout=True)
            FigureCanvasAgg(figure)
            steel_ax, volume_ax = figure.subplots(1, 2)

            # Left panel: comparable steel weights (MT).
            present = [(label, value) for label, value in steel_components if value is not None]
            if rebar_mt is not None:
                present.append(("Reinforcement", rebar_mt))
            if present:
                bars = steel_ax.bar([x[0] for x in present], [x[1] for x in present], width=0.62)
                steel_ax.set_ylabel("Weight (MT)")
                steel_ax.set_title("Steel quantities")
                steel_ax.tick_params(axis="x", labelrotation=18)
                steel_ax.grid(axis="y", linestyle=":", alpha=0.35)
                steel_ax.set_axisbelow(True)
                for bar, (_, value) in zip(bars, present):
                    steel_ax.annotate(f"{value:,.3f} MT",
                        (bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=7)
                missing = [label for label, value in steel_components if value is None]
                if rebar_mt is None:
                    missing.append("Reinforcement")
                if missing:
                    steel_ax.text(0.5, -0.34, "Unavailable: " + ", ".join(missing),
                                  ha="center", va="top", transform=steel_ax.transAxes, fontsize=7)
            else:
                steel_ax.text(0.5, 0.5, "Steel weights unavailable", ha="center", va="center",
                              transform=steel_ax.transAxes)
                steel_ax.set_axis_off()

            # Right panel: show each configured concrete component in m³.
            concrete_items = []
            if deck_concrete_m3 is not None:
                concrete_items.append(("Deck slab", deck_concrete_m3))
            if barrier_m3 is not None and barrier_m3 > 0:
                concrete_items.append(("Crash barrier", barrier_m3))
            if concrete_items:
                bars = volume_ax.bar([x[0] for x in concrete_items],
                                     [x[1] for x in concrete_items], width=0.52)
                volume_ax.set_ylabel("Volume (m³)")
                volume_ax.set_title("Concrete quantities")
                volume_ax.tick_params(axis="x", labelrotation=12)
                volume_ax.grid(axis="y", linestyle=":", alpha=0.35)
                volume_ax.set_axisbelow(True)
                for bar, (_, value) in zip(bars, concrete_items):
                    volume_ax.annotate(f"{value:,.3f} m³",
                        (bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)
                if barrier_configured and barrier_m3 is None:
                    volume_ax.text(0.5, -0.26, "Crash barrier volume unavailable",
                                   ha="center", va="top", transform=volume_ax.transAxes, fontsize=7)
            else:
                volume_ax.text(0.5, 0.5, "Concrete volume unavailable", ha="center", va="center",
                               transform=volume_ax.transAxes)
                volume_ax.set_axis_off()

            figure.suptitle("Material Quantity Summary")
            fd, chart_path = tempfile.mkstemp(prefix="osdagbridge_ch7_materials_", suffix=".png")
            os.close(fd)
            figure.savefig(chart_path, dpi=200, bbox_inches="tight")
            chart_path_tex = chart_path.replace("\\", "/")
            report += (
                r"\ReportTopicBreak" + "\n"
                + r"\section{Material Quantity Chart}" + "\n"
                + r"\begin{figure}[H]\centering" + "\n"
                + r"\includegraphics[width=0.96\textwidth,height=0.62\textheight,keepaspectratio]{"
                + r"\detokenize{" + chart_path_tex + r"}}" + "\n"
                + r"\caption{Material quantities reported in their appropriate units: structural steel components and reinforcement in MT, and deck-slab and crash-barrier concrete volumes in m³.}" + "\n"
                + r"\end{figure}" + "\n"
                + r"\noindent\footnotesize Steel component weights are shown separately; an unavailable component is not treated as zero or silently included in a complete total.\\"
                + r" Reinforcement is estimated from the deck designer's selected bar diameters and spacings; theoretical straight-bar quantities exclude hooks, laps, chairs and wastage.\normalsize" + "\n"
            )
        except Exception as exc:
            report += (r"\noindent\textit{Material quantity chart could not be generated: "
                       + str(exc).replace("_", r"\_")
                       + r". Refer to Table 7.1 for the available bill-of-materials data.}" + "\n")
    else:
        report += (r"\noindent\textit{Material quantity chart was not generated because no supported quantity values are available. "
                   r"Refer to Table 7.1 for the bill-of-materials data.}" + "\n")

    return report
