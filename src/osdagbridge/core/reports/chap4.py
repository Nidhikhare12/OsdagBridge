from typing import TYPE_CHECKING
import os
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed

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

    reaction_rows = []
    for _lc, _reaction in rxn_summary.items():
        _reaction = _reaction or {}
        reaction_rows.append(
            _tex(_lc) + r" & "
            + _fmt(_reaction.get("left_kN")) + r" & "
            + _fmt(_reaction.get("right_kN")) + r" \\[6pt]"
        )
    if reaction_rows:
        reaction_body = ("\n\\hline\n").join(reaction_rows)
    else:
        reaction_body = (
            r"\multicolumn{3}{|p{14.8cm}|}{Support reaction values were not "
            r"returned in the analysis summary for this run.} \\[6pt]"
        )

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
    _live_status     = ("PASS" if _live_mm  <= _allow_live_mm  else r"\ReportFailText{FAIL}") if _live_mm  is not None else "---"
    _total_status    = ("PASS" if _total_mm <= _allow_total_mm else r"\ReportFailText{FAIL}") if _total_mm is not None else "---"
    _analysis_figures = [
        _fig_embed(fig_paths.get("bm_envelope"), "Bending Moment Envelope", width=r"0.75\\textwidth"),
        _fig_embed(fig_paths.get("sf_envelope"), "Shear Force Envelope", width=r"0.75\\textwidth"),
        _fig_embed(fig_paths.get("defl_ll"), "Vertical Deflection (Live Load)", width=r"0.75\\textwidth"),
    ]
    _analysis_figures_tex = "".join(_analysis_figures)
    _available_analysis_figures = sum(
        1 for _key in ("bm_envelope", "sf_envelope", "defl_ll")
        if fig_paths.get(_key) and os.path.isfile(os.fspath(fig_paths.get(_key)))
    )
    if _available_analysis_figures == 0:
        _analysis_figures_tex = (
            r"\noindent\textit{Analysis plots were not supplied by the current analysis run. "
            r"The numerical load, reaction and deflection tables above are retained.}"
        )
    elif _available_analysis_figures < 3:
        _analysis_figures_tex += (
            r"\noindent\footnotesize Some analysis plots were not supplied by the current run.\normalsize"
        )

    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\vspace{1em}
\begingroup
\footnotesize
\setlength{\tabcolsep}{\ReportDenseTablePadding}
\renewcommand{\arraystretch}{\ReportDenseTableStretch}

\begin{longtable}{|
>{\centering\arraybackslash}p{2.4cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.1cm}|
>{\centering\arraybackslash}p{1.1cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.1cm}|
>{\centering\arraybackslash}p{1.1cm}|
>{\centering\arraybackslash}p{1.1cm}|
>{\centering\arraybackslash}p{1.1cm}|}

\caption{\textbf{Summary of Maximum Demands}}\\
\hline
\multirow{2}{*}{\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \scriptsize\textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \scriptsize\textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right }}\\
\hline
\endfirsthead

\hline
\multirow{2}{*}{\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \scriptsize\textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \scriptsize\textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right}}\\
\hline
\endhead

""" + merged_body + r"""

\hline
\end{longtable}
\endgroup

\ReportTopicBreak
\begin{longtable}{|>{\centering\arraybackslash}p{4.7cm}|>{\centering\arraybackslash}p{4.7cm}|>{\centering\arraybackslash}p{4.7cm}|}
\caption{\textbf{Reactions at Supports}}\\
\hline
\textbf{Load Case} & \textbf{Left Support (kN)} & \textbf{Right Support (kN)} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{Load Case} & \textbf{Left Support (kN)} & \textbf{Right Support (kN)} \\
\hline
\endhead
""" + reaction_body + r"""
\hline
\end{longtable}

\ReportTopicBreak
\begin{longtable}{|L{6.5cm}|p{8.2cm}|}
\caption{\textbf{Deflection Summary (Live Load \& Total Load)}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Deflection due to Live Load, $\delta_{LL}$} & """ + _live_str + r""" \\[6pt]
\hline
\textnormal{Allowable Live Load Deflection ($\Delta_{allow}$)} & """ + _allow_live_str + r""" \\[6pt]
\hline
\textnormal{Live Load Deflection Check Status} & """ + _live_status + r""" \\[6pt]
\hline
\textnormal{Deflection due to Total Load, $\delta_{total}$} & """ + _total_str + r""" \\[6pt]
\hline
\textnormal{Allowable Total Deflection ($\Delta_{allow}$)} & """ + _allow_total_str + r""" \\[6pt]
\hline
\textnormal{Total Load Deflection Check Status} & """ + _total_status + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent
""" + _analysis_figures_tex

