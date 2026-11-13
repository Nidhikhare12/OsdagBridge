import os

from osdagbridge.core.reports.report_charts import (
    concrete_reinforcement_chart, parse_quantity, safe_chart, steel_tonnage_chart,
)

# Table 7.1 rows: (S.N., item description, quantity-key prefix). Values come
# from calculate_material_quantities() (boq_generator), injected into
# input_dict by generate_report().
_BOQ_ROWS = (
    ("1",    "Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord",              "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord",           "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal Chord",         "bracing_diag"),
    ("2(d)", "End Diaphragm - Top Chord",              "ed_top"),
    ("2(e)", "End Diaphragm - Bottom Chord",           "ed_bot"),
    ("2(f)", "End Diaphragm - Diagonals",              "ed_diag"),
    ("3",    "Concrete (M40) for Deck Slab",           "concrete_deck"),
    ("4",    "Reinforcement Steel (Fe 500)",           "rebar_deck"),
    ("5",    "Shear Stud Connectors",                  "shear_studs"),
    ("6",    "Crash Barrier",                          "crash_barrier"),
)
_COLS = ("vol_formula", "qty", "vol_total", "wt_single", "wt_total")


def _boq_row(input_dict, sn, label, prefix):
    cells = [str(input_dict.get(f"{prefix}_{c}", "N.A.")) for c in _COLS]
    return f"{sn} & {label} & " + " & ".join(cells) + " \\\\\n\\hline"


def _q(input_dict, key):
    return parse_quantity(input_dict.get(key))


def _quantity_figures(input_dict, images_dir):
    """Figures 7.1 / 7.2 drawn from exactly the values printed in Table 7.1."""
    if not images_dir:
        return ""
    tex = ""

    # Figure 7.1 -- structural steel by element (sum of each element's rows).
    steel = [
        ("Steel Plate Girders", _q(input_dict, "steel_girders_wt_total")),
        ("Cross Bracing", _sum_parts(input_dict, ("bracing_top", "bracing_bot", "bracing_diag"))),
        ("End Diaphragms", _sum_parts(input_dict, ("ed_top", "ed_bot", "ed_diag"))),
    ]
    res = safe_chart(steel_tonnage_chart, steel, os.path.join(images_dir, "qty_steel.png"))
    path, total = res if res else (None, None)
    if path:
        missing = [l for l, v in steel if v is None]
        cap = (f"Structural steel weight by element (total of plotted elements: "
               f"{total:,.2f} MT). Values from Table~\\ref{{tab:boq}}.")
        if missing:
            cap += " Not calculated: " + ", ".join(missing) + "."
        tex += _figure(path, cap, "fig:qty-steel")

    # Figure 7.2 -- concrete volume and reinforcement weight (separate axes).
    deck_c = _q(input_dict, "concrete_deck_vol_total")
    deck_r = _q(input_dict, "rebar_deck_wt_total")
    concrete = [("Deck Slab", deck_c), ("Crash Barriers", _q(input_dict, "crash_barrier_vol_total"))]
    rebar = [("Deck Slab", deck_r)]
    ratio = None
    if deck_c and deck_r is not None:
        ratio = f"Deck slab: {1000.0 * deck_r / deck_c:,.0f} kg of\nreinforcement per m$^3$ of concrete"
    path = safe_chart(concrete_reinforcement_chart, concrete, rebar,
                      os.path.join(images_dir, "qty_concrete.png"), ratio)
    if path:
        tex += _figure(path, "Concrete volume (m\\textsuperscript{3}) and reinforcement steel "
                             "weight (MT). Reinforcement is calculated for the deck slab only. "
                             "Values from Table~\\ref{tab:boq}.", "fig:qty-concrete")
    return tex


def _sum_parts(input_dict, prefixes):
    vals = [_q(input_dict, f"{p}_wt_total") for p in prefixes]
    return None if any(v is None for v in vals) else sum(vals)


def _figure(path, caption, label):
    return ("\n\\begin{figure}[H]\n\\centering\n"
            "\\includegraphics[width=\\linewidth]{" + path.replace("\\", "/") + "}\n"
            "\\caption{" + caption + "}\n\\label{" + label + "}\n\\end{figure}\n")


def ch7_quantities(input_dict, images_dir=None):
    rows = "\n".join(_boq_row(input_dict, *r) for r in _BOQ_ROWS)
    figures = _quantity_figures(input_dict, images_dir)
    intro = ""
    if figures:
        intro = (r"Table~\ref{tab:boq} lists the material quantities of the designed bridge. "
                 r"Figure~\ref{fig:qty-steel} compares the structural steel of each element and "
                 r"Figure~\ref{fig:qty-concrete} shows the concrete volume and reinforcement "
                 r"weight; both are drawn from the values in the table." + "\n")
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

""" + intro + r"""
\vspace{0.5em}
\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}}\label{tab:boq}\\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
\endfirsthead
\ltcontinuedhead{7}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
\endhead
\ltcontinuedfoot{7}
\endfoot
\endlastfoot
""" + rows + r"""
\end{longtable}
\endgroup
""" + figures
