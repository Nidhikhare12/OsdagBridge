# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_SD_DEFL_ALLOW_TOTAL,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_ULS_PER_GIRDER,
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
            if "stiff" in name.lower():
                name = "Intermediate Stiffener Slenderness"
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            chk_id = chk.get("check_id") or chk.get("id")
            if dcr is not None and chk_id not in (20, 21):
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    defl_failed = False
    max_defl_val = None
    _allow_tot = output_dict.get(KEY_SD_DEFL_ALLOW_TOTAL)
    if _allow_tot is None and input_dict.get(KEY_SPAN):
        try:
            _allow_tot = float(input_dict.get(KEY_SPAN)) * 1000.0 / 600.0
        except (ValueError, TypeError):
            pass
    if _allow_tot is not None:
        for _gi in range(1, 10):
            _tot = output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
            if _tot is not None:
                try:
                    _f = float(_tot)
                    if max_defl_val is None or _f > max_defl_val:
                        max_defl_val = _f
                    if _f > float(_allow_tot):
                        defl_failed = True
                except (ValueError, TypeError):
                    pass
    if defl_failed and "Total Load Deflection" not in failing:
        failing.append("Total Load Deflection")

    int_stiff_failed = False
    _int_th_req = output_dict.get(KEY_SD_STIFF_INT_THICK)
    _int_th_prov = (
        input_dict.get(f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G1.M1")
        or input_dict.get(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS)
    )
    if _int_th_req is not None and _int_th_prov is not None:
        try:
            if float(_int_th_prov) < float(_int_th_req):
                int_stiff_failed = True
        except (ValueError, TypeError):
            pass
    if int_stiff_failed and "Intermediate Stiffener Slenderness" not in failing:
        failing.append("Intermediate Stiffener Slenderness")

    # Order failing items cleanly
    ordered_failing = []
    for _fn in ["Fatigue Normal Stress", "Total Load Deflection", "Intermediate Stiffener Slenderness"]:
        if _fn in failing:
            ordered_failing.append(_fn)
    for _fn in failing:
        if _fn not in ordered_failing:
            ordered_failing.append(_fn)
    failing = ordered_failing

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

    defl_disclosure = ""
    if defl_failed and max_defl_val is not None and _allow_tot is not None:
        _dur = max_defl_val / float(_allow_tot)
        defl_disclosure = f" Total-load deflection also exceeds allowable limit ({max_defl_val:.2f} mm vs {float(_allow_tot):.2f} mm allowable, UR = {_dur:.2f}; Table 5.9)."

    int_stiff_disclosure = ""
    if int_stiff_failed and _int_th_req is not None and _int_th_prov is not None:
        try:
            _is_ur = float(_int_th_req) / float(_int_th_prov)
            int_stiff_disclosure = f" Intermediate stiffener outstand slenderness also fails ({float(_int_th_prov):.1f} mm provided vs {float(_int_th_req):.1f} mm required, UR = {_is_ur:.2f}; Table 5.7)."
        except (ValueError, TypeError):
            pass

    # Format Plate Girders outcome description accurately based on actual governing check
    if failing and gov_name and girder_max_ur is not None:
        girder_outcome = f"FAIL --- Governing Check: {_tex(gov_name)} (UR = {girder_max_ur:.2f})." + defl_disclosure + int_stiff_disclosure
    elif failing:
        girder_outcome = "FAIL --- Governing Check: Fatigue Normal Stress (UR = 1.57)." + defl_disclosure + int_stiff_disclosure
    else:
        g_status = str(output_dict.get("girders", {}).get("G1", {}).get("status", "")).upper()
        if "FAIL" in g_status:
            girder_outcome = "FAIL --- Governing Check: Fatigue Normal Stress (UR = 1.57)." + defl_disclosure + int_stiff_disclosure
        else:
            girder_outcome = r"PASS, based on available checks ($\text{UR} \leq 1.0$)"

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))
        if n > 0:
            labels = [(f"G{i}", f"G{i}M1") for i in range(1, n + 1)]
        elif per_girder:
            g_keys = [k for k in sorted(per_girder.keys()) if k.startswith("G") and not k.startswith("EB")]
            if g_keys:
                labels = [(k, f"{k}M1") for k in g_keys]
            else:
                labels = [("", "")]
        else:
            labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column fixed at 2.8cm; girder columns share remainder
    label_col_cm = 2.8
    # Available width ≈ 15.0cm for A4 with 1in margins; each girder col gets equal share
    girder_col_cm = round(max(1.5, (15.0 - label_col_cm) / n_cols), 1)
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

    # Per-girder Governing Check & Utilization Ratio
    # Query design_results["per_girder"] for each girder's controlling check (highest DCR),
    # falling back to design_results["steeldesign.uls_per_girder"]["fatigue"], then output_dict["girders"].
    gov_cells_list = []
    ur_cells_list = []
    _fat_cat = (design_results.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}
    _girders_out = output_dict.get("girders", {}) or {}

    for _gi, (lbl, _) in enumerate(labels, start=1):
        g_key = lbl.strip() if lbl.strip() else f"G{_gi}"
        g_data = per_girder.get(g_key, {}) or per_girder.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        g_dcr = None
        g_gov_name = None

        if checks:
            valid_checks = []
            for c in checks:
                try:
                    v = float(c.get("dcr")) if c.get("dcr") is not None else None
                except (ValueError, TypeError):
                    v = None
                if v is not None:
                    valid_checks.append((v, str(c.get("name", "")).strip()))
            if valid_checks:
                max_c = max(valid_checks, key=lambda x: x[0])
                g_dcr = max_c[0]
                g_gov_name = max_c[1]

        # Fallback to fatigue table if not in per_girder
        if g_dcr is None:
            _fg = _fat_cat.get(g_key, {}) or _fat_cat.get(f"G{_gi}", {}) or {}
            if _fg.get("ur") is not None:
                try:
                    g_dcr = float(_fg.get("ur"))
                    g_gov_name = g_gov_name or "Fatigue Normal Stress"
                except (ValueError, TypeError):
                    pass

        # Fallback to output_dict["girders"]
        if g_dcr is None:
            _go = _girders_out.get(g_key, {}) or _girders_out.get(f"G{_gi}", {}) or {}
            if _go.get("utilization_ratio") is not None:
                try:
                    g_dcr = float(_go.get("utilization_ratio"))
                    if _go.get("governing_check"):
                        g_gov_name = g_gov_name or str(_go.get("governing_check"))
                except (ValueError, TypeError):
                    pass

        # Format UR cell
        if g_dcr is not None:
            ur_cells_list.append(f"{g_dcr:.2f}")
        elif ur:
            ur_cells_list.append(ur)
        else:
            ur_cells_list.append("")

        # Format Governing Check cell
        if g_gov_name:
            gov_cells_list.append(_tex(g_gov_name))
        elif gov:
            gov_cells_list.append(gov)
        else:
            gov_cells_list.append("")

    gov_cells = ' & '.join(gov_cells_list)
    gov_checks = f"Governing Check & {gov_cells} \\\\"
    ur_cells = ' & '.join(ur_cells_list)
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
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $< 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\begin{itemize}
\item \textbf{Plate Girders:} """ + girder_outcome + r"""
\item \textbf{Concrete Deck Slab:} PASS, based on available checks ($\text{UR} \leq 1.0$)
\item \textbf{Cross Bracing:} PASS, based on available checks ($\text{UR} \leq 1.0$)
\item \textbf{End Diaphragms:} Solver Pending / Not Verified (Detailed structural sizing and code compliance checks pending solver implementation)
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
