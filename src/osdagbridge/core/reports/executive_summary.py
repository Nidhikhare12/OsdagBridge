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
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # ── Pull the stored result dicts once, then work off these locals ─────────
    # (no value is recomputed here — the pipeline already filled these in).
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    # Component status derivation from computed results only
    # 1. Girder checks
    girder_failing = []                 # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    girder_status = "NOT CALCULATED"

    if per_girder:
        girder_status = "PASS"
        for g, gd in per_girder.items():
            if str(g).startswith("EB"):     # skip edge-beam pseudo girders
                continue
            for chk in (gd.get("checks") or []):
                try:
                    _val = chk.get("dcr")
                    dcr = float(_val) if _val is not None else None
                except (TypeError, ValueError):
                    dcr = None
                name = str(chk.get("name", "")).strip()
                chk_status = str(chk.get("status", "")).upper()
                is_fail = ("FAIL" in chk_status) or (dcr is not None and dcr > 1.0)
                if is_fail and name and name not in girder_failing:
                    girder_failing.append(name)
                if dcr is not None:
                    if gov_dcr is None or dcr > gov_dcr:
                        gov_dcr, gov_name = dcr, name
                    if girder_max_ur is None or dcr > girder_max_ur:
                        girder_max_ur = dcr
        if girder_failing:
            girder_status = "FAIL"

    # 2. Cross Bracing checks
    cb_max_ur = _max_member_efficiency(cb_results)
    if not cb_results or not isinstance(cb_results, dict) or cb_max_ur is None:
        cb_status = "NOT CALCULATED"
    elif cb_max_ur > 1.0:
        cb_status = "FAIL"
    else:
        cb_status = "PASS"

    # 3. End Diaphragm checks
    ed_max_ur = _max_member_efficiency(ed_results)
    if not ed_results or not isinstance(ed_results, dict) or ed_max_ur is None:
        ed_status = "NOT CALCULATED"
    elif ed_max_ur > 1.0:
        ed_status = "FAIL"
    else:
        ed_status = "PASS"

    # 4. Deck Slab checks
    deck_max_ur = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if not deck_results or not isinstance(deck_results, dict) or deck_max_ur is None:
        deck_status = "NOT CALCULATED"
    elif deck_max_ur > 1.0:
        deck_status = "FAIL"
    else:
        deck_status = "PASS"

    # 5. Overall Design Status aggregation
    component_statuses = {
        "Girder": girder_status,
        "Cross bracing": cb_status,
        "End diaphragm": ed_status,
        "Deck slab": deck_status,
    }
    failing_comps = [c for c, st in component_statuses.items() if st == "FAIL"]
    if failing_comps:
        reasons = []
        if girder_failing:
            reasons.append(f"Girder: {', '.join(girder_failing)}")
        for c in failing_comps:
            if c != "Girder":
                reasons.append(c)
        overall_design_status = f"FAIL ({'; '.join(reasons)})"
    elif any(st == "NOT CALCULATED" for st in component_statuses.values()):
        uncalced = [c for c, st in component_statuses.items() if st == "NOT CALCULATED"]
        overall_design_status = f"PARTIAL ({', '.join(uncalced)} not calculated)"
    elif all(st == "PASS" for st in component_statuses.values()):
        overall_design_status = "PASS"
    else:
        overall_design_status = "NOT CALCULATED"

    # Overall Utilization Ratio — the maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.58 (Girder)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    if deck_max_ur is not None:
        component_urs.append((deck_max_ur, "Deck slab"))
    if cb_max_ur is not None:
        component_urs.append((cb_max_ur, "Cross bracing"))
    if ed_max_ur is not None:
        component_urs.append((ed_max_ur, "End diaphragm"))
    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

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
    # Available width budget ≈ 14.4cm for A4 with 1in margins (15.92cm minus cell padding & rules)
    girder_col_cm = round(max(1.5, (14.4 - label_col_cm) / n_cols), 1)
    col_spec = '|C{' + str(label_col_cm) + 'cm}|' + '|'.join(['C{' + str(girder_col_cm) + 'cm}'] * n_cols) + '|'

    # Header row
    hdr_cells = ' &\n  '.join([r'\textbf{' + _tex(lbl) + '}' for lbl, _ in labels])
    header_row = r'  \textbf{} &' + '\n  ' + hdr_cells + r' \\' + '\n'

    # Member ID row
    mid_cells = ' & '.join([_tex(mid) for _, mid in labels])
    member_id_row = 'Member ID & ' + mid_cells + r' \\' + '\n'

    # Section / Governing Check / UR rows
    sec_cells = ' & '.join([sec] * n_cols)
    sections = f"Section Designation & {sec_cells} \\\\"
    gov_cells = ' & '.join([gov] * n_cols)
    gov_checks = f"Governing Check & {gov_cells} \\\\"
    ur_cells = ' & '.join([ur] * n_cols)
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

    def _comp_line(title, status, max_ur=None, failing_checks=None):
        out = r"\textbf{" + title + r":} "
        if status == "PASS":
            out += r"\textcolor{black}{PASS}"
        elif status == "FAIL":
            out += r"\textcolor{red}{FAIL}"
        elif status == "NOT CALCULATED":
            out += r"\textit{NOT CALCULATED}"
        else:
            out += _tex(status)
        if max_ur is not None:
            out += f" (Max UR = {max_ur:.2f})"
        if failing_checks:
            out += r" -- \textit{Failing: " + _tex(", ".join(failing_checks)) + r"}"
        return out

    outcomes_summary = "\n".join([
        r"\noindent " + _comp_line("Girder Design", girder_status, girder_max_ur, girder_failing) + r" \\",
        _comp_line("Cross Bracing Design", cb_status, cb_max_ur) + r" \\",
        _comp_line("End Diaphragm Design", ed_status, ed_max_ur) + r" \\",
        _comp_line("Deck Slab Design", deck_status, deck_max_ur),
    ])

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
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $< 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

""" + outcomes_summary + r"""

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
