from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports.latex_tables import longtable, figure, note


def _row(sn, desc, prefix, d):
    g = lambda k: str(d.get(f"{prefix}_{k}", "N.A."))
    return " & ".join([sn, desc, g("vol_formula"), g("qty"), g("vol_total"),
                       g("wt_single"), g("wt_total")]) + r" \\" + "\n\\hline"


def ch7_quantities(input_dict, fig_paths=None):
    fig_paths = fig_paths or {}
    d = input_dict
    rows = "\n".join([
        _row("1",    r"Structural Steel (IS 2062) for Girders", "steel_girders", d),
        _row("2(a)", "Cross Bracing - Top Chord", "bracing_top", d),
        _row("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot", d),
        _row("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag", d),
        _row("2(d)", "End Diaphragms (chords + diagonals)", "end_diaphragm", d),
        _row("3",    "Concrete (M40) for Deck Slab", "concrete_deck", d),
        _row("4",    "Reinforcement Steel (Fe 500)", "rebar_deck", d),
        _row("5",    "Shear Stud Connectors", "shear_studs", d),
        _row("6",    "Crash Barrier", "crash_barrier", d),
    ])
    table = longtable(
        "bom", "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
        ["S.N.", "Item Description", "Volume", "Quantity", r"Total Volume (m$^3$)",
         "Weight (MT)", "Total Weight (MT)"], rows, label="tab:bom")

    charts = ""
    if fig_paths.get("qty_steel") or fig_paths.get("qty_concrete"):
        charts = (r"""
\section{Material Quantity Charts}
\label{sec:quantity-charts}

The charts below are generated from the quantities in Table~\ref{tab:bom}.

""" + figure(fig_paths.get("qty_steel"),
             "Structural steel tonnage: girders, cross bracing and end diaphragms",
             width=S.FIGURE["chart_width"], label="fig:qty-steel", placeholder=False)
            + figure(fig_paths.get("qty_concrete"),
                     r"Concrete volume (m$^3$) versus reinforcement steel weight (MT)",
                     width=S.FIGURE["chart_width"], label="fig:qty-concrete", placeholder=False))

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

""" + table + note(r"Weights of steel use 7.85 t/m$^3$; concrete weight uses 2.5 t/m$^3$. "
                   r"End-diaphragm quantities are derived from the designed member sections.") + charts
