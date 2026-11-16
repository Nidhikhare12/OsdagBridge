"""Chapter 7 -- Material Take-off & Quantity Summary."""

from osdagbridge.core.reports import styles

# (S.N., Item description, quantity-key prefix used by boq_generator)
_BOM_ITEMS = [
    ("1", r"Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord", "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag"),
    ("2(d)", "End Diaphragms (both supports)", "end_diaphragm"),
    ("3", r"Concrete (M40) for Deck Slab", "concrete_deck"),
    ("4", r"Reinforcement Steel (Fe 500)", "rebar_deck"),
    ("5", "Shear Stud Connectors", "shear_studs"),
    ("6", "Crash Barrier", "crash_barrier"),
]

_BOM_HEADERS = [
    r"\textbf{S.N.}",
    r"\textbf{Item Description}",
    r"\textbf{Volume}",
    r"\textbf{Quantity}",
    r"\textbf{Total Volume}",
    r"\textbf{Weight (MT)}",
    r"\textbf{Total Weight (MT)}",
]

_BOM_COLSPEC = "|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|"


def _value(input_dict, key):
    """Return a BOM cell value, falling back to N.A. when the key is absent."""
    value = input_dict.get(key)
    if value in ("", None):
        return "N.A."
    return str(value)


def _bom_rows(input_dict):
    for sn, description, prefix in _BOM_ITEMS:
        yield (
            sn,
            description,
            _value(input_dict, f"{prefix}_vol_formula"),
            _value(input_dict, f"{prefix}_qty"),
            _value(input_dict, f"{prefix}_vol_total"),
            _value(input_dict, f"{prefix}_wt_single"),
            _value(input_dict, f"{prefix}_wt_total"),
        )


def ch7_quantities(input_dict, figures=None):
    table = styles.longtable(
        colspec=_BOM_COLSPEC,
        headers=_BOM_HEADERS,
        body=styles.rows(_bom_rows(input_dict)),
        caption=r"\textbf{Bill of Materials (Steel, Concrete, and Reinforcement "
                r"Quantities)}",
        label="tab:bom",
        tabcolsep="3.5pt",
    )

    figures = figures or {}
    charts = []
    if figures.get("steel"):
        charts.append(styles.figure_block(
            figures["steel"],
            "Structural steel tonnage by component",
            width=r"0.92\textwidth",
        ))
    if figures.get("concrete"):
        charts.append(styles.figure_block(
            figures["concrete"],
            "Deck concrete volume versus reinforcement steel weight",
            width=r"0.80\textwidth",
        ))

    charts_tex = ("\n\n" + "\n\n".join(charts)) if charts else ""

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

""" + table + charts_tex + "\n"

