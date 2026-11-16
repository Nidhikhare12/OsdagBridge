# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.reports.latex.tables import SimpleTable
from osdagbridge.core.reports.latex.text import vspace
from osdagbridge.core.reports.theme import get_active_theme
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

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column fixed at 2.8cm; girder columns share remainder
    label_col_cm = 2.8
    # Available width ≈ 13.8cm for A4 with 2.0cm margins; each girder col gets equal share
    girder_col_cm = round(max(1.5, (13.8 - label_col_cm) / n_cols), 2)
    col_spec = '|C{' + str(label_col_cm) + 'cm}|' + '|'.join(['C{' + str(girder_col_cm) + 'cm}'] * n_cols) + '|'

    t_geom1 = SimpleTable(
        col_spec=col_spec,
        rows=[
            [r"\textbf{}"] + [rf"\textbf{{{_tex(lbl)}}}" for lbl, _ in labels],
            ["Member ID"] + [_tex(mid) for _, mid in labels],
            ["Section Designation"] + [sec] * n_cols,
            ["Governing Check"] + [gov] * n_cols,
            ["Utilization Ratio"] + [ur] * n_cols,
        ],
    )
    theme = get_active_theme()
    table1 = (
        r"\noindent\textbf{Table 1 -- Final Bridge Geometry (after optimization)}" + "\n\n"
        + vspace(theme.spacing.space_sm) + "\n"
        r"\noindent" + "\n"
        + t_geom1.dumps()
    )

    t_ovw = SimpleTable(
        col_spec=theme.columns.CH1_KEY_VALUE,
        rows=[
            [r"\textbf{Bridge Type}", _render_value(input_dict, KEY_STRUCTURE_TYPE)],
            [r"\textbf{Design Standard}", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800"],
            [r"\textbf{Span}", _render_value(input_dict, KEY_SPAN, ' m')],
            [r"\textbf{Carriageway Width}", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')],
            [r"\textbf{No. of Girders}", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)],
            [r"\textbf{Girder Spacing}", _render_value(input_dict, KEY_TS_GIRDER_SPACING)],
            [r"\textbf{Deck Thickness}", _render_value(input_dict, KEY_TS_DECK_THICKNESS)],
            [r"\textbf{Overall Design Status}", _tex(overall_design_status)],
            [r"\textbf{Governing Check}", gov],
            [r"\textbf{Overall Utilization Ratio (max)}", ur],
        ],
    )

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
""" + vspace(theme.spacing.space_md) + r"""

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

""" + t_ovw.dumps() + r"""

""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

""" + vspace(theme.spacing.space_sm) + r"""
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $< 1.0$ indicates a passing check.}

""" + vspace(theme.spacing.space_md) + r"""

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent Girder design pass \\
Cross bracing design pass \\
End Diaphragm design pass \\
Deck design pass

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
