from osdagbridge.core.reports.charts import material_chart_tex
from osdagbridge.core.reports.report_utils import make_longtable
from osdagbridge.core.reports import styles

# (S.N., item description, input_dict key prefix)
_BOM_ROWS = [
    ("1",    "Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord",              "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord",           "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal Chord",         "bracing_diag"),
    ("3",    "Concrete (M40) for Deck Slab",           "concrete_deck"),
    ("4",    "Reinforcement Steel (Fe 500)",           "rebar_deck"),
    ("5",    "Shear Stud Connectors",                  "shear_studs"),
    ("6",    "Crash Barrier",                          "crash_barrier"),
]
_BOM_SUFFIXES = ("vol_formula", "qty", "vol_total", "wt_single", "wt_total")


def _bom_body(input_dict):
    """Table 7.1 body rows; each row ends with \\\\ and its own \\hline (make_longtable format)."""
    rows = []
    for sn, desc, prefix in _BOM_ROWS:
        cells = [str(input_dict.get(f"{prefix}_{s}", "N.A.")) for s in _BOM_SUFFIXES]
        rows.append(" & ".join([sn, desc] + cells) + " \\\\\n\\hline")
    return "\n".join(rows)


def ch7_quantities(input_dict, chart_dir=None):
    tabcolsep = getattr(styles, "COMPACT_TABCOLSEP", "3.5pt")
    table = make_longtable(
        r"|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|",
        "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
        r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & "
        r"\textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)}",
        _bom_body(input_dict),
    )
    return (
        r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\setlength{\tabcolsep}{""" + tabcolsep + r"""}
""" + table + r"""
\endgroup
""" + material_chart_tex(input_dict, chart_dir)
    )