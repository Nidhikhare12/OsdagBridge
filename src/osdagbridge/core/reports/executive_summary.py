# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    from osdagbridge.core.reports.report_data import check_records, governing_checks
    report_checks = check_records(output_dict, input_dict)
    component_checks = governing_checks(report_checks)
    outcomes = r" \\ ".join(_tex(r.component + ": " + r.status) for r in component_checks)
    known = [r for r in component_checks if r.ur is not None]
    overall_design_status = ("Fail" if any(r.ur > 1 for r in known) else
                             "Incomplete - results unavailable" if len(known) < 4 else "Pass")
    if known:
        controlling = max(known, key=lambda r: r.ur)
        overall_utilization_ratio = f"{controlling.ur:.3f} ({controlling.component})"
        gov_name = controlling.check
    else:
        overall_utilization_ratio = "Not available"
        gov_name = "Not available"

    gov = _tex(gov_name) if gov_name not in (None, '', 'None') else ''
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else ''

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column fixed at 2.8cm; girder columns share remainder
    label_col_cm = 2.8
    # Available width ≈ 15.0cm for A4 with 1in margins; each girder col gets equal share
    girder_col_cm = round(max(1.5, (15.0 - label_col_cm) / n_cols), 1)
    col_spec = '|C{' + str(label_col_cm) + 'cm}|' + '|'.join(['C{' + str(girder_col_cm) + 'cm}'] * n_cols) + '|'

    from osdagbridge.core.reports.styles import fit_table_columns
    col_spec = fit_table_columns(col_spec)

    # Header row
    hdr_cells = ' &\n  '.join([r'\textbf{' + _tex(lbl) + '}' for lbl, _ in labels])
    header_row = r'  \textbf{} &' + '\n  ' + hdr_cells + r' \\' + '\n'

    # Member ID row
    mid_cells = ' & '.join([_tex(mid) for _, mid in labels])
    member_id_row = 'Member ID & ' + mid_cells + r' \\' + '\n'

    # Section / Governing Check / UR rows
    sec_cells = ' & '.join([sec] * n_cols)
    sections = f"Section Designation & {sec_cells} \\\\"
    member_checks = []
    for label, _ in labels:
        candidates = [r for r in report_checks if r.member == label and r.ur is not None]
        member_checks.append(max(candidates, key=lambda r: r.ur) if candidates else None)
    gov_cells = ' & '.join(_tex(r.check) if r else 'Not available' for r in member_checks)
    gov_checks = f"Governing Check & {gov_cells} \\\\"
    ur_cells = ' & '.join(f'{r.ur:.3f} ({r.status})' if r else 'Not available' for r in member_checks)
    urs = f"Utilization Ratio & {ur_cells} \\\\"

    table1 = (r'\noindent\textbf{Table 1 -- Final Bridge Geometry (after optimization)}' + '\n\n'
              r'\vspace{0.4em}' + '\n'
              r'\noindent' + '\n'
              r'\begin{tabular}{' + col_spec + '}\n'
              r'\hline' + '\n'
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

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING)) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS)) + r""" \\
\hline
\textbf{Overall Design Status} & """ + (_tex(overall_design_status)) + r""" \\
\hline
\textbf{Governing Check} & """ + gov + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}


""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

\vspace{0.4em}
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent """ + outcomes + r"""

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
