from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.latex_tables import longtable, param_table, figure, status_cell
from osdagbridge.core.reports.report_utils import _tex

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    def _merged_row(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return (
            _tex(lc)                              + r" & "
            + _fmt(bm_d.get('max_bm'))           + r" & "
            + _tex(bm_d.get('bm_girder', '---')) + r" & "
            + _fmt(bm_d.get('bm_location'))      + r" & "
            + _fmt(bm_d.get('max_sf'))           + r" & "
            + _tex(bm_d.get('sf_girder', '---')) + r" & "
            + _fmt(bm_d.get('sf_location'))      + r" & "
            + _fmt(rxn_d.get('left_kN'))         + r" & "
            + _fmt(rxn_d.get('right_kN'))        + r" \\[6pt]"
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    merged_body = ("\n\\hline\n").join(
        _merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc))
        for lc in all_lcs
    ) if all_lcs else r"--- & --- & --- & --- & --- & --- & --- & --- & --- \\[6pt]"

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = status_cell(_live_mm  <= _allow_live_mm)  if _live_mm  is not None else "---"
    _total_status    = status_cell(_total_mm <= _allow_total_mm) if _total_mm is not None else "---"
    # Table 4.2 — reactions (same analysis data, listed per load case)
    rxn_rows = "\n".join(
        _tex(lc) + " & " + _fmt((rxn_summary.get(lc) or {}).get('left_kN')) + " & "
        + _fmt((rxn_summary.get(lc) or {}).get('right_kN')) + r" \\" + "\n\\hline"
        for lc in all_lcs) or (r"--- & --- & --- \\" + "\n\\hline")

    summary_header = (
        r"\hdrfill \multirow{2}{*}{\makecell{\hcell{Load}\\\hcell{Case/}\\\hcell{Comb.}}}" "\n"
        r"& \multicolumn{3}{c|}{\hcell{Bending Moment}}" "\n"
        r"& \multicolumn{3}{c|}{\hcell{Shear Force}}" "\n"
        r"& \multicolumn{2}{c|}{\hcell{Reaction at Supports (kN)}}\\" "\n"
        r"\cline{2-9}" "\n"
        r"\hdrfill & \makecell{\hcell{Max}\\\hcell{(kNm)}} & \hcell{Girder} & \makecell{\hcell{Loc.}\\\hcell{(m)}}" "\n"
        r"& \makecell{\hcell{Max}\\\hcell{(kN)}} & \hcell{Girder} & \makecell{\hcell{Loc.}\\\hcell{(m)}}" "\n"
        r"& \hcell{Left} & \hcell{Right}\\")

    fig_w = r"0.8\textwidth"
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\vspace{0.6em}
\begingroup\scriptsize
""" + longtable("analysis_summary", "Summary of Maximum Demands", summary_header, merged_body,
                label="tab:max-demands", small=False) + r"""
\endgroup
""" + longtable("reactions", "Reactions at Supports", ["Load Case", "Left Support (kN)", "Right Support (kN)"],
                rxn_rows, label="tab:reactions") + param_table("Deflection Summary (Live Load \\& Total Load)", [
        (r"Deflection due to Live Load, $\delta_{LL}$", _live_str),
        (r"Allowable Live Load Deflection ($\Delta_{allow}$)", _allow_live_str),
        ("Live Load Deflection Check Status", _live_status),
        (r"Deflection due to Total Load, $\delta_{total}$", _total_str),
        (r"Allowable Total Deflection ($\Delta_{allow}$)", _allow_total_str),
        ("Total Load Deflection Check Status", _total_status),
    ], label="tab:deflection") + r"""
\vspace{0.6em}
""" + figure(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=fig_w, label="fig:bm-env") + "\n" + figure(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=fig_w, label="fig:sf-env") + "\n" + figure(fig_paths.get('defl_ll'), r'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=fig_w, label="fig:defl-ll") + "\n"
