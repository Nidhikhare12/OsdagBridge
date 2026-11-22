from osdagbridge.core.reports.report_utils import _fig_embed
from osdagbridge.core.reports.styles import (
    TABCOLSEP_COMPACT,
    VSPACE_TABLE,
    lt_begin,
    lt_end,
    table_group,
)


def ch7_quantities(input_dict, images_dir=None):
    """Chapter 7 — BOM table plus quantity bar charts (no dummy numbers)."""
    grp_open, grp_close = table_group(tabcolsep=TABCOLSEP_COMPACT)

    def _cell(key):
        return str(input_dict.get(key, "N.A."))

    rows = (
        r"1 & Structural Steel (IS 2062) for Girders & "
        + _cell("steel_girders_vol_formula") + r" & "
        + _cell("steel_girders_qty") + r" & "
        + _cell("steel_girders_vol_total") + r" & "
        + _cell("steel_girders_wt_single") + r" & "
        + _cell("steel_girders_wt_total") + r" \\" + "\n\\hline\n"
        + r"2(a) & Cross Bracing - Top Chord & "
        + _cell("bracing_top_vol_formula") + r" & "
        + _cell("bracing_top_qty") + r" & "
        + _cell("bracing_top_vol_total") + r" & "
        + _cell("bracing_top_wt_single") + r" & "
        + _cell("bracing_top_wt_total") + r" \\" + "\n\\hline\n"
        + r"2(b) & Cross Bracing - Bottom Chord & "
        + _cell("bracing_bot_vol_formula") + r" & "
        + _cell("bracing_bot_qty") + r" & "
        + _cell("bracing_bot_vol_total") + r" & "
        + _cell("bracing_bot_wt_single") + r" & "
        + _cell("bracing_bot_wt_total") + r" \\" + "\n\\hline\n"
        + r"2(c) & Cross Bracing - Diagonal Chord & "
        + _cell("bracing_diag_vol_formula") + r" & "
        + _cell("bracing_diag_qty") + r" & "
        + _cell("bracing_diag_vol_total") + r" & "
        + _cell("bracing_diag_wt_single") + r" & "
        + _cell("bracing_diag_wt_total") + r" \\" + "\n\\hline\n"
        + r"3 & Concrete (M40) for Deck Slab & "
        + _cell("concrete_deck_vol_formula") + r" & "
        + _cell("concrete_deck_qty") + r" & "
        + _cell("concrete_deck_vol_total") + r" & "
        + _cell("concrete_deck_wt_single") + r" & "
        + _cell("concrete_deck_wt_total") + r" \\" + "\n\\hline\n"
        + r"4 & Reinforcement Steel (Fe 500) & "
        + _cell("rebar_deck_vol_formula") + r" & "
        + _cell("rebar_deck_qty") + r" & "
        + _cell("rebar_deck_vol_total") + r" & "
        + _cell("rebar_deck_wt_single") + r" & "
        + _cell("rebar_deck_wt_total") + r" \\" + "\n\\hline\n"
        + r"5 & Shear Stud Connectors & "
        + _cell("shear_studs_vol_formula") + r" & "
        + _cell("shear_studs_qty") + r" & "
        + _cell("shear_studs_vol_total") + r" & "
        + _cell("shear_studs_wt_single") + r" & "
        + _cell("shear_studs_wt_total") + r" \\" + "\n\\hline\n"
        + r"6 & Crash Barrier & "
        + _cell("crash_barrier_vol_formula") + r" & "
        + _cell("crash_barrier_qty") + r" & "
        + _cell("crash_barrier_vol_total") + r" & "
        + _cell("crash_barrier_wt_single") + r" & "
        + _cell("crash_barrier_wt_total") + r" \\" + "\n"
    )

    header = (
        r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & "
        r"\textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & "
        r"\textbf{Total Weight (MT)} \\"
    )

    charts_tex = ""
    if images_dir:
        try:
            from osdagbridge.core.reports.charts import render_quantity_charts
            paths = render_quantity_charts(input_dict, images_dir)
            if paths.get("steel"):
                charts_tex += _fig_embed(
                    paths["steel"],
                    "Structural steel quantities (MT) from Table 7.1.",
                    width=r"0.85\textwidth",
                )
            if paths.get("deck"):
                charts_tex += _fig_embed(
                    paths["deck"],
                    "Deck concrete volume (m$^3$) and reinforcement steel (MT).",
                    width=r"0.75\textwidth",
                )
        except Exception:
            charts_tex = ""

    return (
        r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

"""
        + grp_open
        + lt_begin(
            r"|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|",
            "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
            header,
        )
        + rows
        + lt_end() + "\n"
        + grp_close
        + VSPACE_TABLE + "\n"
        + charts_tex
    )
