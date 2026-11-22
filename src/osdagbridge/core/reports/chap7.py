def ch7_quantities(input_dict, image_dir=None):
    content = r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}}\\
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
2(d) & End Diaphragm Steel & """ + str(input_dict.get("end_diaphragm_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_qty", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_total", "N.A.")) + r""" \\
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
"""

    # Chapter 7 material quantity charts
    chart_latex = ""

    if image_dir:
        import os
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        os.makedirs(image_dir, exist_ok=True)

        def _quantity(key):
            """Convert a BOM quantity to a number."""
            value = input_dict.get(key)
            if value in (None, "", "N.A.", "N/A"):
                return None
            try:
                return float(
                    str(value).replace(",", "").split()[0]
                )
            except (ValueError, TypeError):
                return None

        # Chart 1: Structural steel tonnage
        # Chart 1: Structural steel tonnage
        steel_labels = [
            "Girders",
            "Top chord",
            "Bottom chord",
            "Diagonal chord",
            "End diaphragm",
        ]

        steel_values = [
            _quantity("steel_girders_wt_total"),
            _quantity("bracing_top_wt_total"),
            _quantity("bracing_bot_wt_total"),
            _quantity("bracing_diag_wt_total"),
            _quantity("end_diaphragm_wt_total"),
        ]

        steel_data = [
            (label, value)
            for label, value in zip(steel_labels, steel_values)
            if value is not None
        ]

        if steel_data:
            labels, values = zip(*steel_data)
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.bar(labels, values)
            ax.set_title("Structural Steel Quantity")
            ax.set_ylabel("Weight (MT)")
            ax.grid(axis="y", alpha=0.25)
            fig.tight_layout()

            path = os.path.join(image_dir, "material_steel.png")
            fig.savefig(path, dpi=180, bbox_inches="tight")
            plt.close(fig)

            steel_img = os.path.join(
                image_dir, "material_steel.png"
            ).replace("\\", "/")

            chart_latex += (
                "\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width=0.85\\textwidth]{{{steel_img}}}\n"
                "\\caption{Structural Steel Quantity by Component}\n"
                "\\end{figure}\n"
            )

        # Chart 2: Concrete volume vs reinforcement steel weight
        concrete = _quantity("concrete_deck_vol_total")
        reinforcement = _quantity("rebar_deck_wt_total")

        if concrete is not None and reinforcement is not None:
            fig, ax1 = plt.subplots(figsize=(7, 4.5))

            ax1.bar(
                ["Concrete"],
                [concrete],
                label="Concrete Volume",
            )
            ax1.set_ylabel("Concrete Volume (m³)")

            ax2 = ax1.twinx()
            ax2.bar(
                ["Reinforcement"],
                [reinforcement],
                label="Reinforcement Weight",
            )
            ax2.set_ylabel("Reinforcement Weight (MT)")

            ax1.set_title(
                "Concrete Volume and Reinforcement Steel Weight"
            )
            fig.tight_layout()

            path = os.path.join(image_dir, "material_concrete_rebar.png")
            fig.savefig(path, dpi=180, bbox_inches="tight")
            plt.close(fig)

            concrete_img = os.path.join(
                image_dir, "material_concrete_rebar.png"
            ).replace("\\", "/")

            chart_latex += (
                "\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width=0.8\\textwidth]{{{concrete_img}}}\n"
                "\\caption{Concrete Volume and Reinforcement Steel Weight}\n"
                "\\end{figure}\n"
            )

    return content + (
        "\\section{Material Quantity Charts}\n"
        "\\noindent The following charts summarize the material quantities "
        "recorded in the bill of materials.\n"
        + chart_latex
    )


