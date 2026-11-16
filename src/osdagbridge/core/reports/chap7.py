from osdagbridge.core.reports.latex.tables import ReportTable
from osdagbridge.core.reports.theme import get_active_theme


def ch7_quantities(input_dict):
    theme = get_active_theme()
    caption = "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)"
    headers = [
        "S.N.",
        "Item Description",
        "Volume",
        "Quantity",
        "Total Volume",
        "Weight (MT)",
        "Total Weight (MT)",
    ]

    tbl = ReportTable(
        columns=theme.columns.CH7_QUANTITY_7COL,
        caption=caption,
        label="ch:material-takeoff",
        header_rows=[headers],
    )

    rows = [
        ("1", "Structural Steel (IS 2062) for Girders", "steel_girders"),
        ("2(a)", "Cross Bracing - Top Chord", "bracing_top"),
        ("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot"),
        ("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag"),
        ("3", "Concrete (M40) for Deck Slab", "concrete_deck"),
        ("4", "Reinforcement Steel (Fe 500)", "rebar_deck"),
        ("5", "Shear Stud Connectors", "shear_studs"),
        ("6", "Crash Barrier", "crash_barrier"),
    ]

    for sn, desc, prefix in rows:
        tbl.add_row([
            sn,
            desc,
            str(input_dict.get(f"{prefix}_vol_formula", "N.A.")),
            str(input_dict.get(f"{prefix}_qty", "N.A.")),
            str(input_dict.get(f"{prefix}_vol_total", "N.A.")),
            str(input_dict.get(f"{prefix}_wt_single", "N.A.")),
            str(input_dict.get(f"{prefix}_wt_total", "N.A.")),
        ])

    charts_latex = []
    steel_chart_path = input_dict.get("_qty_steel_chart")
    conc_chart_path = input_dict.get("_qty_concrete_rebar_chart")

    if steel_chart_path:
        from osdagbridge.core.reports.latex.figures import figure
        charts_latex.append(
            figure(
                path=steel_chart_path,
                caption=r"\textbf{Structural Steel Tonnage Breakdown} \textit{(IS 2062 steel for girders and cross bracing; end diaphragm pending)}",
                width=r"\textwidth",
            )
        )
    if conc_chart_path:
        from osdagbridge.core.reports.latex.figures import figure
        charts_latex.append(
            figure(
                path=conc_chart_path,
                caption=r"\textbf{Concrete Volume (m$^3$) and Reinforcement Steel Weight (MT)} \textit{(M40 grade concrete and Fe 500 reinforcement for deck slab)}",
                width=r"\textwidth",
            )
        )
    charts_section = ("\n\n" + "\n\n".join(charts_latex) + "\n\n") if charts_latex else "\n"

    return rf"""
\chapter{{Material Take-off \& Quantity Summary}}
\label{{ch:material-takeoff}}

{tbl.dumps()}
{charts_section}"""
