# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports.latex_tables import (
    column_spec, longtable, figure, note, PASS_TEX, FAIL_TEX, NA_TEX, ur_cell,
)
from osdagbridge.core.reports.report_utils import _render_value, _tex, get_girder_entries
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


def executive_summary(input_dict, output_dict, fig_paths, ur_data=None) -> str:
    plan_fig = figure(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan', numbered=False)
    cs_fig = figure(fig_paths.get('cross_section'),
                    'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)', numbered=False)
    geom_fig = figure(fig_paths.get('final_geometry'),
                      'Figure 3 -- 3D View of Bridge Superstructure', numbered=False)

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

    # Overall Design Status — girder checks only: Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):     # skip edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
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

    if not per_girder:
        overall_design_status = ""
    elif failing:
        overall_design_status = "Fail (" + ", ".join(failing) + ")"
    else:
        overall_design_status = "Pass"

    # Overall Utilization Ratio — the maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.05 (Deck slab)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    for results, label in ((cb_results, "Cross bracing"), (ed_results, "End diaphragm")):
        m = _max_member_efficiency(results)
        if m is not None:
            component_urs.append((m, label))
    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

    gov = _tex(gov_name) if gov_name not in (None, '', 'None') else ''
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else ''

    # --- Table 1: one ROW per girder (the old one-column-per-girder layout ran
    # off the page for 9+ girders).  Header repeats on every page. ---------------
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    rows = []
    for lbl, mid in labels:
        rows.append(" & ".join([_tex(lbl), _tex(mid), sec, gov, ur]) + r" \\" + "\n\\hline")
    table1 = longtable("exec_geometry", "Final Bridge Geometry (after optimization)",
                       ["Girder", "Member ID", "Section Designation", "Governing Check",
                        "Utilization Ratio"], "\n".join(rows), label="tab:exec-geometry")

    # --- Key Design Outcomes: derived from the real results -------------------
    comp_status = {}
    if ur_data:
        from osdagbridge.core.reports.charts import component_status
        comp_status = component_status(ur_data)
    if "girder" not in comp_status or comp_status.get("girder") is None:
        if girder_max_ur is not None:
            comp_status["girder"] = girder_max_ur <= S.STATUS["ur_limit"]

    def _outcome(label, key):
        st = comp_status.get(key)
        if st is None:
            verdict = NA_TEX + r" \textit{(no result)}"
        else:
            verdict = PASS_TEX if st else FAIL_TEX
        return r"\item[] " + label + r" design: " + verdict

    outcomes = "\n".join([
        _outcome("Girder", "girder"), _outcome("Cross bracing", "bracing"),
        _outcome("End diaphragm", "diaphragm"), _outcome("Deck", "deck")])

    def _ov(key, unit=''):
        return _render_value(input_dict, key, unit)

    return (S.front_heading("Executive Summary") + r"""
This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

\begingroup""" + S.TABLE["table_font"] + r"""
\begin{tabular}{""" + column_spec('param_value') + r"""}
\hline
\cellcolor{osdagGreenLight}\textbf{Bridge Type} & """ + _ov(KEY_STRUCTURE_TYPE) + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\cellcolor{osdagGreenLight}\textbf{Span} & """ + _ov(KEY_SPAN, ' m') + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Carriageway Width} & """ + _ov(KEY_CARRIAGEWAY_WIDTH, ' m') + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{No. of Girders} & """ + _ov(KEY_TS_NO_OF_GIRDERS) + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Girder Spacing} & """ + _ov(KEY_TS_GIRDER_SPACING, ' m') + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Deck Thickness} & """ + _ov(KEY_TS_DECK_THICKNESS, ' mm') + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Overall Design Status} & """ + (_tex(overall_design_status)) + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Governing Check} & """ + gov + r""" \\
\hline
\cellcolor{osdagGreenLight}\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}
\endgroup

\vspace{1em}
""" + plan_fig + "\n\n" + cs_fig + "\n\n" + geom_fig + "\n\n" + table1 + note(
        r"Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.") + r"""

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\begin{itemize}[label={}, leftmargin=0pt]
""" + outcomes + r"""
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
""")
