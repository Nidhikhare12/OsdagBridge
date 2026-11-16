from osdagbridge.core.reports.latex.tables import ReportTable


def ch7_quantities(input_dict):
    caption = "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)"
    col_spec = "|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|"
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
        columns=col_spec,
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

    return rf"""
\chapter{{Material Take-off \& Quantity Summary}}
\label{{ch:material-takeoff}}

\begingroup
\setlength{{\tabcolsep}}{{3.5pt}}
{tbl.dumps()}
\endgroup
"""
