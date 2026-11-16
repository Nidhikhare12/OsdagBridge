from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed
from osdagbridge.core.reports.latex.tables import ReportTable, KeyValueTable
from osdagbridge.core.reports.latex.text import status_fail, vspace
from osdagbridge.core.reports.theme import get_active_theme

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

    def _merged_cells(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return [
            _tex(lc),
            _fmt(bm_d.get('max_bm')),
            _tex(bm_d.get('bm_girder', '---')),
            _fmt(bm_d.get('bm_location')),
            _fmt(bm_d.get('max_sf')),
            _tex(bm_d.get('sf_girder', '---')),
            _fmt(bm_d.get('sf_location')),
            _fmt(rxn_d.get('left_kN')),
            _fmt(rxn_d.get('right_kN')),
        ]

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

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
    _live_status     = ("PASS" if _live_mm  <= _allow_live_mm  else status_fail("FAIL")) if _live_mm  is not None else "---"
    _total_status    = ("PASS" if _total_mm <= _allow_total_mm else status_fail("FAIL")) if _total_mm is not None else "---"

    theme = get_active_theme()
    header_tex = r"""\hline
\multirow{2}{*}{\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\makecell{\textbf{Reaction at}\\\textbf{Supports}}}\\
\cline{2-9}
& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right}}\\
\hline"""

    demands_table = ReportTable(
        preset=theme.columns.DEMAND_9COL,
        caption=r"\textbf{Summary of Maximum Demands}",
        header_tex=header_tex,
    )
    if all_lcs:
        for lc in all_lcs:
            demands_table.add_row(_merged_cells(lc, lc_summary.get(lc), rxn_summary.get(lc)))
    else:
        demands_table.add_row(["---"] * 9)

    rxn_table = ReportTable(
        columns=theme.columns.CH4_RXN_3COL,
        caption=r"\textbf{Reactions at Supports}",
        header_rows=[["Load Case", "Left Support (kN)", "Right Support (kN)"]],
    )
    rxn_table.add_row(["", "", ""])
    rxn_table.add_row(["", "", ""])
    rxn_table.add_row(["", "", ""])

    defl_table = KeyValueTable(
        caption=r"\textbf{Deflection Summary (Live Load \& Total Load)}",
        preset=theme.columns.CH4_DEFL_KEY_VALUE,
        headers=("Parameter", "Value"),
        rows=[
            (r"\textnormal{Deflection due to Live Load, $\delta_{LL}$}", _live_str),
            (r"\textnormal{Allowable Live Load Deflection ($\Delta_{allow}$)}", _allow_live_str),
            (r"\textnormal{Live Load Deflection Check Status}", _live_status),
            (r"\textnormal{Deflection due to Total Load, $\delta_{total}$}", _total_str),
            (r"\textnormal{Allowable Total Deflection ($\Delta_{allow}$)}", _allow_total_str),
            (r"\textnormal{Total Load Deflection Check Status}", _total_status),
        ],
    )

    sp = vspace(theme.spacing.space_md)
    return rf"""
\chapter{{Analysis Results}}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

{sp}
{demands_table.dumps()}

{sp}
{rxn_table.dumps()}

{sp}
{defl_table.dumps()}

{sp}
\noindent
{_fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth')}
{_fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth')}
{_fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth')}
"""

