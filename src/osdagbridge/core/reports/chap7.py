"""Chapter 7 - material take-off and calculated quantity visualization."""
from __future__ import annotations

from .styles import styled_chapter
from osdagbridge.core.reports.styles import chart_tex, repeating_longtable_header


def _value(data: dict, key: str) -> str:
    return str(data.get(key, "N.A."))


@styled_chapter
def ch7_quantities(input_dict: dict, figure_paths: dict | None = None) -> str:
    """Render the bill of materials and its data-derived quantity chart."""
    figure_paths = figure_paths or {}
    rows = (
        ("1", "Structural Steel (IS 2062) for Girders", "steel_girders"),
        ("2(a)", "Cross Bracing - Top Chord", "bracing_top"),
        ("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot"),
        ("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag"),
        ("2(d)", "End Diaphragms", "end_diaphragms"),
        ("3", "Concrete for Deck Slab", "concrete_deck"),
        ("4", "Reinforcement Steel (estimated)", "rebar_deck"),
        ("5", "Shear Stud Connectors", "shear_studs"),
        ("6", "Crash Barrier", "crash_barrier"),
    )
    body = "\n".join(
        " & ".join((number, label, _value(input_dict, f"{prefix}_vol_formula"),
                     _value(input_dict, f"{prefix}_qty"), _value(input_dict, f"{prefix}_vol_total"),
                     _value(input_dict, f"{prefix}_wt_single"), _value(input_dict, f"{prefix}_wt_total")))
        + r" \\[4pt]" + "\n" + r"\hline"
        for number, label, prefix in rows
    )
    header = repeating_longtable_header(
        r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & "
        r"\textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & "
        r"\textbf{Total Weight (MT)} \\[4pt]", columns=7
    )
    material_chart = chart_tex(
        figure_paths.get("material_quantities", ""),
        "Material quantities generated from the calculated bill of materials.",
    )
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1 Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\caption{\textbf{Bill of Materials}}\\
""" + header + body + r"""
\end{longtable}
\endgroup

""" + r"\noindent Reinforcement quantity is the existing take-off estimate (120 kg per cubic metre of deck), not a detailed bar schedule. N.A. indicates unavailable design quantities." + material_chart
