# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# Refactored per FOSSEE Winter Internship Requirements:
# - Executive Summary Box on Page 1 (geometry, overall status badge, controlling UR)
# - Dynamic status indicators for Girder, Deck, Cross Bracing, and End Diaphragms
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import (
    _fig_or_placeholder,
    _render_value,
    _tex,
    format_check_name,
    get_girder_entries,
)
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if out is None or f > out:
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Maximum Osdag 'efficiency' (utilization ratio) over a cross-bracing or
    end-diaphragm result dump (nested pair -> member -> force_type -> raw).
    Reads already-computed results only; nothing is recalculated here."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for raw in force_types.values():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best is None or f > best:
                    best = f
    return best


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    '3D View of Bridge Superstructure')

    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # Stored result dicts
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    failing = []
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                dcr = None if _val is None else float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    is_overall_pass = bool(per_girder and not failing)
    if not per_girder:
        overall_design_status = "N/A"
        overall_badge = "\\textbf{\\color{OsdagMuted}{NOT RUN}}"
    elif is_overall_pass:
        overall_design_status = "SAFE (PASS)"
        overall_badge = "\\textbf{\\color{OsdagPass}{SAFE (PASS)}}"
    else:
        failing_tex = [format_check_name(f) for f in failing]
        overall_design_status = "UNSAFE (FAIL: " + ", ".join(failing_tex) + ")"
        overall_badge = "\\textbf{\\color{OsdagFail}{UNSAFE (FAIL)}}"

    component_urs = []
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    cb_max = _max_member_efficiency(cb_results)
    if cb_max is not None:
        component_urs.append((cb_max, "Cross bracing"))
    ed_max = _max_member_efficiency(ed_results)
    if ed_max is not None:
        component_urs.append((ed_max, "End diaphragm"))

    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = "N/A"

    gov = format_check_name(gov_name) if gov_name not in (None, '', 'None') else '-'
    ur = f"{gov_dcr:.2f}" if gov_dcr is not None else '-'

    labels = get_girder_entries(input_dict)
    if not labels:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        labels = [(f"Girder {i}", f"G{i}M1") for i in range(1, n + 1)]

    n_cols = len(labels)
    col_w = f"{min(8.0 / max(n_cols, 1), 2.2):.1f}cm"
    col_spec = '|L{4.2cm}|' + '|'.join([f'C{{{col_w}}}'] * n_cols) + '|'

    header_cells = ' & '.join([r'\textbf{' + _tex(lbl) + r'}' for lbl, _ in labels])
    header_row = r'\textbf{Girder}' + ' & ' + header_cells + r' \\' + '\n'

    mid_cells = ' & '.join([_tex(mid) for _, mid in labels])
    member_id_row = r'\textbf{Member ID} & ' + mid_cells + r' \\' + '\n'

    sec_cells = ' & '.join([sec] * n_cols)
    sections = f"\\textbf{{Section Designation}} & {sec_cells} \\\\"
    gov_cells = ' & '.join([gov] * n_cols)
    gov_checks = f"\\textbf{{Governing Check}} & {gov_cells} \\\\"
    ur_cells = ' & '.join([ur] * n_cols)
    urs = f"\\textbf{{Utilization Ratio}} & {ur_cells} \\\\"

    table1 = (r'\noindent\textbf{Table 1: Final Bridge Geometry (after optimization)}' + '\n\n'
              r'\vspace{0.4em}' + '\n'
              r'\noindent' + '\n'
              r'\begin{tabular}{' + col_spec + '}\n'
              r'\hline' + '\n'
              r'\rowcolor{OsdagHeaderBg}' + '\n'
              + header_row +
              r'\hline' + '\n'
              + member_id_row +
              r'\hline' + '\n'
              + sections + '\n'
              r'\hline' + '\n'
              + gov_checks + '\n'
              r'\hline' + '\n'
              + urs + '\n'
              r'\hline' + '\n'
              r'\end{tabular}')

    # Component status lines
    failing_tex = [_tex(f) for f in failing]
    girder_outcome = "\\textbf{\\color{OsdagPass}{PASS}}" if not failing else f"\\textbf{{\\color{{OsdagFail}}{{FAIL}}}} ({', '.join(failing_tex)})"
    deck_outcome = "\\textbf{\\color{OsdagPass}{PASS}}" if (deck_max is not None and deck_max <= 1.0) else ("\\textbf{\\color{OsdagFail}{FAIL}}" if deck_max is not None else "\\textbf{\\color{OsdagMuted}{N/A}}")
    cb_outcome = "\\textbf{\\color{OsdagPass}{PASS}}" if (cb_max is not None and cb_max <= 1.0) else ("\\textbf{\\color{OsdagFail}{FAIL}}" if cb_max is not None else "\\textbf{\\color{OsdagMuted}{N/A}}")
    ed_outcome = "\\textbf{\\color{OsdagPass}{PASS}}" if (ed_max is not None and ed_max <= 1.0) else ("\\textbf{\\color{OsdagFail}{FAIL}}" if ed_max is not None else "\\textbf{\\color{OsdagMuted}{N/A}}")

    span_str = _render_value(input_dict, KEY_SPAN, ' m')
    span_val = _render_value(input_dict, KEY_SPAN)
    span_str = (span_val + ' m') if span_val else '-'
    cw_val = _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH)
    cw_str = (cw_val + ' m') if cw_val else '-'
    girders_str = _render_value(input_dict, KEY_TS_NO_OF_GIRDERS) or '-'
    spacing_val = _render_value(input_dict, KEY_TS_GIRDER_SPACING)
    spacing_str = (spacing_val + ' m') if spacing_val else '-'
    deck_thk_val = _render_value(input_dict, KEY_TS_DECK_THICKNESS)
    deck_thk_str = (deck_thk_val + ' mm') if deck_thk_val else '-'

    return r"""
\newpage
{\centering\Large\bfseries\color{OsdagPrimary} Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

% Executive Summary Callout Box
\begin{center}
\setlength{\fboxsep}{12pt}
\setlength{\fboxrule}{0.8pt}
\fcolorbox{OsdagBorder}{OsdagZebra}{%
\parbox{0.95\linewidth}{%
{\color{OsdagGreen}\rule{\linewidth}{2.0pt}}\\[8pt]
\centering
{\large\bfseries\color{OsdagPrimary} EXECUTIVE DESIGN SUMMARY}\\[8pt]
\begin{tabular}{@{}p{0.54\linewidth}p{0.44\linewidth}@{}}
\textbf{Structure:} Plate Girder Highway Bridge & \textbf{Overall Status:} """ + overall_badge + r""" \\[5pt]
\textbf{Span:} """ + span_str + r""" \quad\textbar\quad \textbf{Carriageway:} """ + cw_str + r""" & \textbf{Controlling UR:} \textbf{""" + overall_utilization_ratio + r"""} \\[5pt]
\textbf{Girders:} """ + girders_str + r""" \quad\textbar\quad \textbf{Spacing:} """ + spacing_str + r""" & \textbf{Governing Check:} """ + gov + r""" \\[5pt]
\textbf{Design Codes:} IRC 5, 6, 22, 24, IS 800 & \textbf{Deck Thickness:} """ + deck_thk_str + r""" \\[2pt]
\end{tabular}
}}
\end{center}

\vspace{0.8em}
This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Design Specification} \\
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Design Standards} & IRC 5:2015, IRC 6:2017, IRC 22:2015, IRC 24:2010, IS 800:2007 \\
\hline
\textbf{Span (m)} & """ + span_val + r""" \\
\hline
\textbf{Carriageway Width (m)} & """ + cw_val + r""" \\
\hline
\textbf{No. of Girders} & """ + girders_str + r""" \\
\hline
\textbf{Girder Spacing (m)} & """ + spacing_val + r""" \\
\hline
\textbf{Deck Thickness (mm)} & """ + deck_thk_val + r""" \\
\hline
\textbf{Overall Design Status} & """ + overall_design_status + r""" \\
\hline
\textbf{Governing Check} & """ + gov + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}

\vspace{1em}
""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

\vspace{0.4em}
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $\le 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\begin{itemize}[leftmargin=1.5em, itemsep=4pt]
\item \textbf{Steel Plate Girders:} """ + girder_outcome + r"""
\item \textbf{Concrete Deck Slab:} """ + deck_outcome + r"""
\item \textbf{Cross Bracing System:} """ + cb_outcome + r"""
\item \textbf{End Diaphragms:} """ + ed_outcome + r"""
\end{itemize}

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

% Restore numbered chapter format
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{-30pt}{10pt}
"""
