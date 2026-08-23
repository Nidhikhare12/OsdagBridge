from osdagbridge.core.reports.report_utils import _fig_embed
from osdagbridge.core.reports.report_charts import save_material_bar_charts


def _flt(val):
    """Best-effort float parse; returns None for 'N.A.', blanks, or
    anything unparseable rather than raising or silently becoming 0 (a
    0-valued bar would misleadingly claim 'confirmed zero', which is not
    the same as 'no data')."""
    try:
        if val in (None, "", "N.A.", "N/A"):
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def ch7_quantities(input_dict, fig_dir=None):
    # ------------------------------------------------------------------
    # Requirement 5 (Phase 2): material quantity bar charts
    # ------------------------------------------------------------------
    # Steel tonnage by component. NOTE: this BOM table has no End Diaphragm
    # row at all (only Girders + the 3 Cross Bracing sub-items + Concrete +
    # Rebar + Shear Studs + Crash Barrier), so an "End Diaphragms" steel bar
    # can't be produced from what's itemized here without fabricating a
    # number. If End Diaphragm steel needs its own line item, that has to
    # be added to Table 7.1 itself first (a separate, larger change) — this
    # chart honestly reflects only what the BOM currently reports.
    _girder_wt = _flt(input_dict.get("steel_girders_wt_total"))
    _brace_parts = [
        _flt(input_dict.get("bracing_top_wt_total")),
        _flt(input_dict.get("bracing_bot_wt_total")),
        _flt(input_dict.get("bracing_diag_wt_total")),
    ]
    _brace_known = [v for v in _brace_parts if v is not None]
    _brace_wt = sum(_brace_known) if _brace_known else None

    _steel_by_component = {}
    if _girder_wt is not None:
        _steel_by_component["Girders"] = _girder_wt
    if _brace_wt is not None:
        _steel_by_component["Cross Bracing"] = _brace_wt

    _concrete_vol = _flt(input_dict.get("concrete_deck_vol_total"))
    _rebar_wt = _flt(input_dict.get("rebar_deck_wt_total"))

    _mat_charts = save_material_bar_charts(
        _steel_by_component, _concrete_vol, _rebar_wt, fig_dir=fig_dir
    )
    _steel_chart_block = (
        _fig_embed(_mat_charts["steel_tonnage"],
                   "Structural steel tonnage by component (Girders, Cross Bracing). "
                   "End Diaphragm steel is not currently itemized as a separate line "
                   "in Table 7.1 and so cannot be charted here.",
                   width=r"0.7\textwidth")
        if _mat_charts["steel_tonnage"] else ""
    )
    _concrete_chart_block = (
        _fig_embed(_mat_charts["concrete_vs_rebar"],
                   "Concrete volume (deck slab) versus reinforcement steel weight.",
                   width=r"0.7\textwidth")
        if _mat_charts["concrete_vs_rebar"] else ""
    )

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
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

\vspace{1em}
""" + _steel_chart_block + r"""

\vspace{1em}
""" + _concrete_chart_block + r"""
"""