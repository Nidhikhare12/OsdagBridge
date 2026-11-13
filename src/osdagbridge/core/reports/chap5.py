# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
import os
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries, keep_rows_together
from osdagbridge.core.reports.report_charts import (
    safe_chart, utilization_summary_chart, utilization_detail_chart,
)

if TYPE_CHECKING:
    pass
# Shown in place of end-diaphragm results when the analysis gives the end
# diaphragm no force (e.g. the grillage restrains every girder end laterally,
# so lateral load goes straight to the supports).
_ED_NO_RESULT_NOTE = (
    r"\noindent\textit{No end-diaphragm design results: the structural analysis "
    r"produced no force in the end-diaphragm members, because the analysis model "
    r"restrains every girder end laterally at the supports and lateral load is taken "
    r"directly by the supports. The end-diaphragm section is therefore not checked in "
    r"this report; it is not a passing (UR = 0) result.}"
)


def ch5_design_checks(checks_data, bridge, images_dir=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    n_girders = len(girder_entries)

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}

    # Generate Table 5.1 rows (per-girder section properties)
    t51_rows = []
    for lbl, _ in girder_entries:
        t51_rows.append(
            r"\multirow{13}{*}{\makecell{" + lbl + r"""}} & \textnormal{Depth, D (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOTAL_DEPTH) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Top Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_WIDTH) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Bottom Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_WIDTH) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Top Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_THICKNESS) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Bottom Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_THICKNESS) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Web Thickness, $t_w$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_WEB_THICKNESS) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Gross Area, A (cm$^2$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_AREA) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Moment of Inertia, $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_IZ) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Elastic Section Modulus, $Z_{ez}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZZ) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Plastic Section Modulus, $Z_{pz}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZUZ) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Effective Slab Width, $b_{eff}$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_EFFECTIVE_SLAB_WIDTH) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Transformed Composite $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_COMPOSITE_IZ) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Depth to Plastic Neutral Axis (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_PNA_DEPTH) + r""" \\[\osdagRowGap]
\hline"""
        )
    t51_content = "\n".join(keep_rows_together(r) for r in t51_rows)

    # Generate Table 5.2 rows
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Top Flange & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + r""" \\[\osdagRowGap]
\cline{2-5}
 & Web & """ + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + r""" \\[\osdagRowGap]
\cline{2-5}
 & Overall Section & --- & --- & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + r""" \\[\osdagRowGap]
\hline"""
        )
    t52_content = "\n".join(keep_rows_together(r) for r in t52_rows)

    # Generate Table 5.3 rows
    # Flexure UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _flex_ur = float(bridge.output_dict.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = "PASS" if _flex_ur <= 1.0 else r"\osdagFailText{FAIL}"
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = "---"
    t53_rows = []
    for lbl, _ in girder_entries:
        t53_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Applied Moment, $M_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_MU_APPLIED, " kN-m") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Design Moment Capacity, $M_d$ & IRC 22 Cl. 603.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_MD_CAPACITY, " kN-m") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Utilization Ratio, $M_u / M_d$ & $M_u / M_d$ & """ + _flex_ur_str + r""" & """ + _flex_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t53_content = "\n".join(keep_rows_together(r) for r in t53_rows)

    # Generate Table 5.4 rows
    # Shear UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _shear_ur = float(bridge.output_dict.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = "PASS" if _shear_ur <= 1.0 else r"\osdagFailText{FAIL}"
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = "---"
    t54_rows = []
    for lbl, _ in girder_entries:
        t54_rows.append(
            r"\multirow{8}{*}{\makecell{" + lbl + r"""}} & Applied Shear, $V_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VU, " kN") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Shear Area, $A_v$ & $d_w \times t_w$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_AV, " mm$^2$") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Panel Aspect Ratio, c/d & --- & """ + _render_value(bridge.output_dict, KEY_SD_PANEL_CD) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Shear Buckling Coefficient, $k_v$ & IS 800 Cl. 8.4.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_KV) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_LAMBDA_W) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Design Shear Stress, $\tau_b$ & IRC 22 Cl. 603.3.3.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_TAU_B, " MPa") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Shear Buckling Resistance, $V_{cr}$ & $A_v \times \tau_b$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VCR, " kN") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Utilization Ratio, $V_u / V_d$ & $V_u / V_d$ & """ + _shear_ur_str + r""" & """ + _shear_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t54_content = "\n".join(keep_rows_together(r) for r in t54_rows)

    # Generate Table 5.5 rows
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return r"\osdagFailText{FAIL}"
    # M-V interaction UR stored as percent → show ratio (2 dp).
    try:
        _mv_ur = float(bridge.output_dict.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = "---"
    # M-N interaction: None → no axial load → N/A.
    _mn_r  = bridge.output_dict.get(KEY_SD_MN_RATIO)
    _mn_ax = bridge.output_dict.get(KEY_SD_MN_AXIAL)
    _mn_mo = bridge.output_dict.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55_rows = []
    for lbl, _ in girder_entries:
        t55_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & High Shear Condition? & $V_u > 0.6\,V_d$ & """ + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & """ + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & """ + _mv_ur_str + r""" & """ + _mv_status + r""" \\[\osdagRowGap]
\cline{2-5}
 & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & """ + _mn_cond + r""" & """ + _mn_val + r""" & """ + _mn_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t55_content = "\n".join(keep_rows_together(r) for r in t55_rows)

    # Generate Table 5.6 rows
    # LTB UR stored as percent → show ratio (2 dp); engine bands via _interaction_status.
    try:
        _ltb_ur = float(bridge.output_dict.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = "---"
    t56_rows = []
    for lbl, _ in girder_entries:
        t56_rows.append(
            r"\multirow{5}{*}{\makecell{" + lbl + r"""}} & Elastic Critical Moment, $M_{cr}$ & IRC 22 Cl. 603.3.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & LTB Reduction Factor, $\chi_{LT}$ & IS 800 Cl. 8.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & LTB Resistance, $M_b$ & $\chi_{LT}\,M_p / \gamma_{m0}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r""" & --- \\[\osdagRowGap]
\cline{2-5}
 & $M_u \leq M_b$ & $M_u / M_b$ & """ + _ltb_ur_str + r""" & """ + _ltb_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t56_content = "\n".join(keep_rows_together(r) for r in t56_rows)

    # Generate Table 5.7 rows
    t57_rows = []
    for lbl, _ in girder_entries:
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + lbl + r"""}} & \textnormal{Shear Buckling Design Method} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_METHOD) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Intermediate Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Intermediate Stiffener Spacing (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{End Panel Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{No. of End Panel Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + r""" \\[\osdagRowGap]
\cline{2-3}
 & \textnormal{Longitudinal Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + r""" \\[\osdagRowGap]
\hline"""
        )
    t57_content = "\n".join(keep_rows_together(r) for r in t57_rows)

    # Generate table - intermediate stiffener checks (IS 800 CL. 8.7.1.2)
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else r"\osdagFailText{FAIL}"
        except (TypeError, ValueError):
            return "---"
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Min. Moment of Inertia, $I_s$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r""" & """ + _iys_status + r""" \\[\osdagRowGap]
\cline{2-5}
 & Buckling Resistance, $F_{qd} \geq F_q$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r""" & """ + _fqd_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t58_content = "\n".join(keep_rows_together(r) for r in t58_rows)

    # (Intermediate Stiffener Checks) is a verification table — it only
    # has data when the user supplied stiffener sizes (Design Type = Custom). In
    # Optimized mode the stiffeners are auto-sized (nothing to verify), so the
    # whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = r"""
\vspace{\osdagBlockGap}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Intermediate Stiffener Checks}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t58_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.7.1.2}
"""
    else:
        t58_block = ""

    # Generate Table 5.9 rows — bearing stiffener checks (IS 800 Cl.8.7.3).
    # End panel == bearing stiffener for this bridge. Each resistance vs reaction R.
    # Resistances are 0 in guidance-only mode (optimized w/o outstand) → N/A until
    # the designer defaults outstand to (bf−tw)/2.
    _bs_r = bridge.output_dict.get(KEY_SD_BS_R)
    def _bs_check(resist_key):
        prov = bridge.output_dict.get(resist_key)
        # Resistance not computed (guidance mode) → N/A.
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        req_s  = f"{_bs_r} kN"
        prov_s = f"{prov} kN"
        status = "PASS" if float(prov) >= float(_bs_r) else r"\osdagFailText{FAIL}"
        return (req_s, prov_s, status)
    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & Web Buckling Resistance & """ + _wb_req + r""" & """ + _wb_prov + r""" & """ + _wb_st + r""" \\[\osdagRowGap]
\cline{2-5}
 & Local Crushing Resistance & """ + _lc_req + r""" & """ + _lc_prov + r""" & """ + _lc_st + r""" \\[\osdagRowGap]
\cline{2-5}
 & Bearing Capacity & """ + _ps_req + r""" & """ + _ps_prov + r""" & """ + _ps_st + r""" \\[\osdagRowGap]
\cline{2-5}
 & Column Buckling Resistance & """ + _cb_req + r""" & """ + _cb_prov + r""" & """ + _cb_st + r""" \\[\osdagRowGap]
\hline"""
        )
    t59_content = "\n".join(keep_rows_together(r) for r in t59_rows)

    # ── Table 5.10: Serviceability — Deflection Checks (IRC 22 Cl. 604.3.2) ──────
    # Allowable limits: span-dependent, same for all girders, from output_dict.
    # Actual deflections: per-girder from bridge._deflections_cache — the same
    # source used by resolve_deflection_live_load/total in generate_results_values_builder.py.
    # Keys: {"G1": {"live_mm": X, "total_mm": Y}, ...}
    # lbl from girder_entries is "G1", "G2", ... which matches cache keys exactly.

    def _defl_status(actual, allowable):
        """PASS / red FAIL for deflection; '---' when values are missing."""
        try:
            return "PASS" if float(actual) <= float(allowable) else r"\osdagFailText{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _dfmt(v, nd=2):
        """Format a numeric value to nd decimal places; empty string when None."""
        try:
            return f"{float(v):.{nd}f}"
            
        except (TypeError, ValueError):
            return ""

    # Mirror generate_results_values_builder.resolve_deflection_live/total_load
    # exactly so the report shows the same numbers as the Generate Results dialog:
    # allowable from span (L/800, L/600), actual from _deflections_cache.
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm  = _span_m * 1000.0 / 800.0
        _allow_total_mm = _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str  = (f"L/800 = {_allow_live_mm:.1f} mm")  if _allow_live_mm  is not None else ""
    _allow_total_str = (f"L/600 = {_allow_total_mm:.1f} mm") if _allow_total_mm is not None else ""

    # The report has no live _deflections_cache (it builds a ReportDataBridge from
    # output_dict only). design() persists the same per-girder cache values that
    # the Generate Results dialog shows into output_dict under the canonical
    # "G1".."Gn" suffix, so read them from there by loop index.
    t510_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _live_mm  = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _total_mm = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")

        t510_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Live Load Deflection, $\delta_{LL}$ (mm) & """
            + _allow_live_str + r""" & """
            + _dfmt(_live_mm,  nd=3) + r""" & """
            + _defl_status(_live_mm,  _allow_live_mm) + r""" \\[\osdagRowGap]
\cline{2-5}
 & Total Load Deflection, $\delta_{total}$ (mm) & """
            + _allow_total_str + r""" & """
            + _dfmt(_total_mm, nd=3) + r""" & """
            + _defl_status(_total_mm, _allow_total_mm) + r""" \\[\osdagRowGap]
\hline"""
        )
    t510_content = "\n".join(keep_rows_together(r) for r in t510_rows)

    # Generate Table 5.11 rows — SLS steel stress limitation (IRC 22 Cl. 604.3.1).
    # Concrete & rebar deck stresses are deck-global and belong with the deck
    # checks, so this table shows only the per-girder steel check. Steel stress is
    # a single envelope-SLS value (same for every girder); allowable = 0.9·fy.
    # Both live in the nested output_dict["design_results"] dict, not as flat keys.
    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    def _stress_status(actual, allow):
        try:
            return "PASS" if float(actual) <= float(allow) else r"\osdagFailText{FAIL}"
        except (TypeError, ValueError):
            return "---"

    _dr_511        = bridge.output_dict.get("design_results", {}) or {}
    _steel_sigma   = _dr_511.get(KEY_SD_STRESS_STEEL)
    _steel_allow   = _dr_511.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    _steel_sig_str = _mpa(_steel_sigma)
    _steel_alw_str = _mpa(_steel_allow)
    _steel_status  = _stress_status(_steel_sigma, _steel_allow)

    t511_rows = []
    for lbl, _ in girder_entries:
        t511_rows.append(
            r"\makecell{" + lbl + r"""} & Structural Steel ($0.9\,f_y$) & """
            + _steel_alw_str + r""" & """
            + _steel_sig_str + r""" & """
            + _steel_status + r""" \\[\osdagRowGap]
\hline"""
        )
    t511_content = "\n".join(keep_rows_together(r) for r in t511_rows)

    # Generate Table 5.12 rows — per-girder fatigue assessment (IRC 22 Cl. 605),
    # mirroring the Generate Results dialog: one row per girder showing the
    # GOVERNING fatigue check (worst of normal/shear by DCR). Source is the nested
    # design_results["steeldesign.uls_per_girder"]["fatigue"][G{i}] dict, keyed by
    # the canonical girder index, with {demand, capacity, ur, status}.
    _fat_cat = ((bridge.output_dict.get("design_results", {}) or {})
                .get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}

    def _fat_status(s):
        if s is None or str(s).strip() == "":
            return "---"
        return r"\osdagFailText{" + str(s) + "}" if "FAIL" in str(s).upper() else str(s)

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + lbl + r"""} & """
            + _mpa(_g.get("demand")) + r""" & """
            + _mpa(_g.get("capacity")) + r""" & """
            + _dfmt(_g.get("ur"), nd=2) + r""" & """
            + _fat_status(_g.get("status")) + r""" \\[\osdagRowGap]
\hline"""
        )
    t512_content = "\n".join(keep_rows_together(r) for r in t512_rows)

    # Generate Table 5.13 rows — per-girder design summary, mirroring the Generate
    # Results dialog's resolve_design_results_summary: one row per girder showing
    # the CONTROLLING check (highest DCR among all checks) plus the real load
    # case/combination that drives it. Source: design_results["per_girder"][G{i}].
    _pg_summary = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _with_unit(value, unit):
        s = _dfmt(value, nd=2)
        if not s:
            return ""
        return (s + " " + unit) if unit and str(unit) not in ("-", "–") else s

    g_summary_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = _pg_summary.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            g_summary_rows.append(lbl + r""" &  &  &  &  &  &  \\[\osdagRowGap]
\hline""")
            continue

        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)

        # Worst real load case for the controlling check id (skip Envelope pseudo-LCs)
        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""

        g_summary_rows.append(
            lbl + r""" & """ + _tex(str(ctrl_lc)) + r""" & """ + _tex(str(ctrl.get("name", "")))
            + r""" & """ + _with_unit(ctrl.get("demand"),   ctrl.get("demand_unit"))
            + r""" & """ + _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit"))
            + r""" & """ + _dfmt(ctrl.get("dcr"), nd=3)
            + r""" & """ + _fat_status(ctrl.get("status")) + r""" \\[\osdagRowGap]
\hline"""
        )
    g_summary_table_content = "\n".join(g_summary_rows)

    # ── Table 5.14: Shear Connector Capacity (bridge-level) ──────────────────
    # Qu (Cl.606.3.1, Eq.6.1) and Qr (Cl.606.3.2, Table 8) are single per-stud
    # values for the bridge, stored flat inside output_dict["design_results"].
    _dr_sc = bridge.output_dict.get("design_results", {}) or {}

    def _kn(v):
        s = _dfmt(v, nd=2)
        return (s + " kN") if s else ""

    t514_content = (
        r"Design Resistance, $Q_u$ & \footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[\osdagRowGapSmall]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[\osdagRowGapSmall]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$} & "
        + _kn(_dr_sc.get(KEY_SD_SC_Qu_kN)) + r""" & IRC 22 Cl. 606.3.1 (Eq. 6.1) \\[\osdagRowGap]
\hline
Fatigue Shear Resistance, $Q_r$ & IRC 22 Table 8 ($\phi d$, $N_{sc}$) & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qr_kN)) + r""" & IRC 22 Cl. 606.3.2 (Table 8) \\[\osdagRowGap]
\hline"""
    )

    # ── Table 5.15: Shear Connector Spacing (bridge-level) ───────────────────
    # Required spacings SL1/SL2/SR and the max-spacing limit are single bridge
    # values in design_results. Each criterion passes when the provided spacing
    # is no larger than that criterion's required spacing (denser = safe).
    def _mm(v):
        s = _dfmt(v, nd=1)
        return (s + " mm") if s else ""

    _sc_prov     = _dr_sc.get("stud_spacing_provided_mm")
    _sc_prov_str = _mm(_sc_prov)

    def _sp_row(crit, req):
        return (crit + r" & " + _mm(req) + r" & " + _sc_prov_str + r" & "
                + _defl_status(_sc_prov, req) + r" \\[\osdagRowGap]")

    t515_content = (
        _sp_row("ULS Shear (SL1)",            _dr_sc.get(KEY_SD_SC_SL1)) + "\n\\hline\n"
        + _sp_row("Full Composite (SL2)",       _dr_sc.get(KEY_SD_SC_SL2)) + "\n\\hline\n"
        + _sp_row("SLS Fatigue (SR)",           _dr_sc.get(KEY_SD_SC_SR)) + "\n\\hline\n"
        + _sp_row("Max Spacing Limit (IRC 22)", _dr_sc.get("stud_spacing_max_mm")) + "\n\\hline"
    )

    # ── Table 5.16: Transverse Shear & Detailing Checks (bridge-level) ───────
    # Transverse shear (Cl.606.10): VL vs slab capacity VRd. Detailing (Cl.606.6):
    # min transverse reinforcement, stud diameter ≤ 2·tf, edge distance ≥ 25 mm.
    # All single bridge values in design_results; stud diameter from input_dict.
    def _cm2m(v):
        s = _dfmt(v, nd=2)
        return (s + r" cm$^2$/m") if s else ""

    def _knm(v):
        s = _dfmt(v, nd=2)
        return (s + " kN/m") if s else ""

    _ts_vl  = _dr_sc.get(KEY_SD_TS_VL)
    _ts_vrd = _dr_sc.get(KEY_SD_TS_VRD)
    if _ts_vl is not None and _ts_vrd is not None:
        try:
            _ts_vl_f = float(_ts_vl)
            _ts_vrd_f = float(_ts_vrd)
            if _ts_vrd_f > 0.0:
                _ts_ur_str = f"{_ts_vl_f / _ts_vrd_f:.2f}"
            else:
                _ts_ur_str = "---"
        except (TypeError, ValueError):
            _ts_ur_str = "---"
    else:
        _ts_ur_str = "---"
    _ts_ok = _dr_sc.get("transverse_shear_ok")
    _ts_status = (r"\osdagFailText{FAIL}" if _ts_ok is False else "PASS") if _ts_ok is not None else "---"

    _ast_req  = _dr_sc.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which run
    # transversely between girders and cross the shear plane. The deck design
    # computes these (>= minimum) and they are what is actually provided. The
    # steel designer's own Ast_provided is 0 because its transverse-shear check
    # runs before design_deck_slab(), so read the deck-design value here instead.
    _dd_516 = bridge.output_dict.get("deck_design_results", {}) or {}
    try:
        _ast_prov = (float(_dd_516.get("rebar_bottom_area") or 0)
                     + float(_dd_516.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        _ast_prov = None
    _stud_d   = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    _d_lim    = _dr_sc.get(KEY_SD_SC_D_LIMIT)
    _edge     = _dr_sc.get(KEY_SD_SC_EDGE_DIST)
    _edge_req = _dr_sc.get(KEY_SD_SC_REQ_EDGE_DIST)

    def _row516(check, value, status):
        return check + r" & " + value + r" & " + status + r" \\[\osdagRowGap]"

    t516_content = (
        _row516(r"\textnormal{Longitudinal Shear per unit length, $V_L$}", _knm(_ts_vl), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Capacity of Slab, $V_{Rd}$}", _knm(_ts_vrd), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Check}", r"$V_L/V_{Rd}$ = " + _ts_ur_str, _ts_status) + "\n\\hline\n"
        + _row516(r"\textnormal{Min. Transverse Reinforcement, $A_{st,min}$}",
                  r"Required " + _cm2m(_ast_req) + r", Provided " + _cm2m(_ast_prov),
                  _defl_status(_ast_req, _ast_prov)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Diameter $\leq 2\,t_f$}",
                  r"$d$ = " + _mm(_stud_d) + r" $\leq 2t_f$ = " + _mm(_d_lim),
                  _defl_status(_stud_d, _d_lim)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Edge Distance}",
                  r"Provided " + _mm(_edge) + r" (req. $\geq$ " + _mm(_edge_req) + r")",
                  _defl_status(_edge_req, _edge)) + "\n\\hline"
    )

    def _bracing_tables(src, props_ns, diag_props, details_ns):
        """Rows for the connection, slenderness and capacity tables of one
        bracing system (intermediate cross bracing or end diaphragm).
        `src` is a ReportDataBridge (or an end-diaphragm view of it)."""
        # Generate Table 5.20(a) rows
        cb_forces_rows = []
        pairs = src.get_cb_pairs()

        if not pairs:
            # fallback: one placeholder row
            cb_forces_rows.append(
                r"""Between Girders & Diagonal &  &  &  &  \\[\osdagRowGap]
    \hline"""
            )
        else:
            for pair in pairs:
                pair_id = pair.replace("-", "")
                _pair_rows = []
                for member, label in [("diagonal", "Diagonal"),
                                    ("chord", "Top / Bottom chord")]:
                    force_str, ftype = src.get_cb_governing_force(pair, member)
                    conn_type = src.get_cb_connection(pair, member, ftype)
                    section  = src.get_cb_section(pair, member, ftype)

                    # Fetch properties from output_dict
                    if member == "diagonal":
                        pfx = f"{props_ns}.{diag_props}.{pair_id}"
                    else:
                        pfx = f"{props_ns}.bottom_chord.{pair_id}"
                        if src.output_dict.get(f"{pfx}.A") is None:
                            pfx = f"{props_ns}.top_chord.{pair_id}"

                    area_cm2 = src.output_dict.get(f"{pfx}.A")
                    rv_cm = src.output_dict.get(f"{pfx}.rv")

                    # Convert Area: cm² -> mm²
                    area_str = f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else ""
                    # Convert rv: cm -> mm
                    rmin_str = f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""
                    # Panel label only on the first member row of the pair
                    # (it was repeated on both rows).
                    _panel = (r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}"
                              if member == "diagonal" else "")
                    _pair_rows.append(
                        _panel + r" & "
                        + label + r" & " + conn_type + r" & " + section
                        + r" & " + area_str + r" & " + rmin_str
                        + r" \\[\osdagRowGap]"
                    )
                # One block per panel so keep_rows_together keeps both rows on
                # the same page as their multirow panel label.
                cb_forces_rows.append("\n\\cline{2-6}\n".join(_pair_rows) + "\n\\hline")
        cb_forces_content = "\n".join(keep_rows_together(r) for r in cb_forces_rows)

        # Generate Table 5.20(b) rows
        def get_status_str(slnd_str, limit):
            try:
                v = float(slnd_str)
                return r"\osdagPassText{PASS}" if v <= limit else r"\osdagFailText{FAIL}"
            except (ValueError, TypeError):
                return ""
        cb_slenderness_rows = []
        if not pairs:
            cb_slenderness_rows.append(
                r"""Between Girders & Diagonal & C &  &  &  ---  \\[\osdagRowGap]
    \hline"""
            )
        else:
            for pair in pairs:
                kl_diag = src.get_cb_effective_length("diagonal")
                slnd_diag = src.get_cb_slenderness(pair, "diagonal")
                status_diag = get_status_str(slnd_diag, 250)
            
                kl_tc = src.get_cb_effective_length("chord")
                slnd_tc = src.get_cb_slenderness(pair, "chord")
                status_tc = get_status_str(slnd_tc, 250)
            
                kl_bc = src.get_cb_effective_length("chord")
                slnd_bc = src.get_cb_slenderness(pair, "chord")
                status_bc = get_status_str(slnd_bc, 400)
            
                top_chord_enabled = src.output_dict.get(f"{details_ns}.top_chord", True)
                bottom_chord_enabled = src.output_dict.get(f"{details_ns}.bottom_chord", True)
            
                num_rows = 1 + int(top_chord_enabled) + int(bottom_chord_enabled)
                row_tex = r"\multirow{" + str(num_rows) + r"}{*}{\makecell{" + _tex(pair) + r"}}"
                row_tex += f" & Diagonal & C & {kl_diag} & {slnd_diag} & 250 --- {status_diag} \\\\[\\osdagRowGap]"
            
                if top_chord_enabled:
                    row_tex += f"\n\\cline{{2-6}}\n & Top chord & C & {kl_tc} & {slnd_tc} & 250 --- {status_tc} \\\\[\\osdagRowGap]"
                if bottom_chord_enabled:
                    row_tex += f"\n\\cline{{2-6}}\n & Bottom chord & T & {kl_bc} & {slnd_bc} & 400 --- {status_bc} \\\\[\\osdagRowGap]"
                
                row_tex += "\n\\hline"
                cb_slenderness_rows.append(row_tex)
        cb_slenderness_content = "\n".join(keep_rows_together(r) for r in cb_slenderness_rows)

        # Generate Table 5.20(c) rows
        cb_capacity_rows = []
        for pair in pairs:
            rows_for_pair = []
            for member, label in [("diagonal", "Diagonal"),
                                ("chord", "Chord")]:
                force_str, ftype = src.get_cb_governing_force(pair, member)
                section  = src.get_cb_section(pair, member, ftype)
                gov_lc   = src.get_cb_gov_lc(pair, member, ftype)
                capacity = src.get_cb_capacity(pair, member, ftype)
                ur       = src.get_cb_efficiency(pair, member, ftype)
                status   = src.get_cb_status(pair, member, ftype)
                rows_for_pair.append(
                    r" & " + label + r" & " + section
                    + r" & " + gov_lc + r" & " + force_str + r" & " + capacity
                    + r" & " + ur + r" & " + status + r" \\[\osdagRowGap]\cline{2-8}"
                )
            first = r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}" + rows_for_pair[0]
            rest  = rows_for_pair[1:]
            cb_capacity_rows.append(first)
            cb_capacity_rows.extend(rest)
            cb_capacity_rows.append(r"\hline")
        cb_capacity_content = "\n".join(keep_rows_together(r) for r in cb_capacity_rows)
        return cb_forces_content, cb_slenderness_content, cb_capacity_content

    cb_forces_content, cb_slenderness_content, cb_capacity_content = _bracing_tables(
        bridge, "transverse_member_design.cb.section_properties", "bracing",
        "member_properties.cross_bracing_details")
    _ed_view = bridge.end_diaphragm_view()
    _ed_has_results = _ed_view.has_bracing_results()
    ed_forces_content, ed_slenderness_content, ed_capacity_content = _bracing_tables(
        _ed_view, "transverse_member_design.ed.section_properties", "end_diaphragm",
        "member_properties.end_diaphragm_details")



    # ── Deck slab design value helpers (Tables 5.17 a/b/c/e/g) ────────────────
    # Read from deck_rpt = output_dict["deck_report_values"] (common.KEY_DD_*).
    # Tables 5.17(d) punching shear and 5.17(f) one-way shear stay as
    # placeholders — those are not computed by design_deck_slab().
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    def _dkv(key, default=0.0):
        """Raw float for status comparisons (0.0 if missing/non-numeric)."""
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        """Formatted display string; placeholder when deck design not run."""
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return str(v)

    def _dks(ok):
        """PASS/FAIL status; '---' when deck design not run."""
        return ("PASS" if ok else "FAIL") if _dk_has else "---"

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        """Overhang value; 'N/A' when there is no overhang."""
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    # Governing crack width = max(bottom, top[, overhang]) vs the limit.
    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)]
    if _dk_oh:
        _dk_wks.append(_dkv(KEY_DD_WK_OH))
    _dk_gov_wk = max(_dk_wks)
    _dk_gov_wk_str = (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH)
    _dk_crack_ok = _dk_has and _dk_gov_wk <= _dkv(KEY_DD_WK_LIMIT)

    # ── Table 5.22: Overall Design Check Summary — fill all rows ─────────────
    # Three row families:
    #  (1) Girder DCR-engine checks: one source (design_results["per_girder"])
    #      gives Demand, Capacity, UR, and the governing LC together. Worst
    #      girder = highest DCR. Most checks fire on the envelope demand (units
    #      available in per_girder["checks"]); SLS-conditional checks (e.g.
    #      deflection) only appear per-LC, so fall back to per_lc for those.
    #  (2) Deck slab: URs from deck_design_results (Demand/Capacity not stored).
    #  (3) Cross bracing: existing get_cb_* helpers (worst pair/member by UR).
    #      End diaphragm has no report helpers yet → "---" for now.
    _pg_522 = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    _dd_522 = bridge.output_dict.get("deck_design_results", {}) or {}

    def _vu_522(v, unit):
        s = _dfmt(v, nd=2)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _ur_522(v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return ""
        s = f"{f:.2f}"
        return (r"\osdagFailText{" + s + "}") if f > 1.0 else s

    def _lc_short(lc):
        # Show the full combination expression as-is, e.g.
        # "ACCIDENTAL 1: 1.0DL + 1.0DW + 0.75LL" (the per_lc key).
        return _tex(str(lc).strip())

    def _gov_lc_in_522(g, check_ids):
        gd = _pg_522.get(g) or {}
        best = None
        for _lc, _ld in (gd.get("per_lc") or {}).items():
            if str(_lc).lower().startswith("envelope"):
                continue
            for _chk in (_ld.get("checks") or []):
                if _chk.get("id") in check_ids:
                    _d = _chk.get("dcr") or 0.0
                    if best is None or _d > best[0]:
                        best = (_d, _lc)
        return _lc_short(best[1]) if best else "---"

    def _dcr_row(check_ids, fallback_unit=""):
        # Prefer per_girder["checks"] (carries units); worst girder by DCR.
        best = None  # (dcr, demand, capacity, dunit, cunit, g)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g,
                                chk.get("dcr"))
        if best is not None:
            d, dem, cap, du, cu, g, raw = best
            return (_gov_lc_in_522(g, check_ids),
                    _vu_522(dem, du) or "---", _vu_522(cap, cu) or "---", _ur_522(d) or "---",
                    raw)
        # Fallback: per_lc (no units) for SLS-conditional checks (e.g. deflection).
        best = None  # (dcr, demand, capacity, lc)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), _lc, chk.get("dcr"))
        if best is None:
            return ("---", "---", "---", "---")
        d, dem, cap, _lc, raw = best
        return (_lc_short(_lc),
                _vu_522(dem, fallback_unit) or "---", _vu_522(cap, fallback_unit) or "---",
                _ur_522(d) or "---", raw)

    # (3) Cross bracing — worst pair/member by UR for the given force type.
    def _cb_row(force_type, src=bridge):
        best = None  # (ur, pair, member, capacity_str)
        for pair in src.get_cb_pairs():
            for member in ("diagonal", "chord"):
                cap = src.get_cb_capacity(pair, member, force_type)
                eff = src.get_cb_efficiency(pair, member, force_type)
                try:
                    ur = float(eff)
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return ("---", "---", "---", "---")
        ur, pair, member, cap = best
        gov = src.get_cb_gov_lc(pair, member, force_type) or "---"
        dem = f"{float(cap) * ur:.2f} kN" if cap else "---"
        cap_s = (cap + " kN") if cap else "---"
        return (gov, dem, cap_s, _ur_522(ur), ur)

    def _cb_slender_row(src=bridge):
        best = None  # (ratio, slend, limit)
        for pair in src.get_cb_pairs():
            for member in ("diagonal", "chord"):
                s = src.get_cb_slenderness(pair, member)
                try:
                    sf = float(s)
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                ratio = sf / lim
                if best is None or ratio > best[0]:
                    best = (ratio, sf, lim)
        if best is None:
            return ("---", "---", "---", "---")
        ratio, sf, lim = best
        return ("---", f"{sf:.1f}", f"{lim:.0f}", _ur_522(ratio), ratio)

    # (element, check label, UR) for every summary row that has a UR; the
    # Section 5.5 graph is drawn from exactly these values.
    ur_records = []

    def _row522(label, cells, element=None, check=None):
        raw = cells[4] if len(cells) > 4 else None
        c = [x if x else "---" for x in cells[:4]]
        if element and raw is not None:
            try:
                ur_records.append((element, check or label, float(raw)))
            except (TypeError, ValueError):
                pass
        return label + r" & " + r" & ".join(c) + r" \\[\osdagRowGap]" + "\n\\hline"

    # Deck rows: Demand/Capacity from deck_report_values (KEY_DD_*, the same dict
    # the 5.17 tables use); UR = Demand/Capacity. The deck is designed for the
    # IRC:6 Basic ULS combination — build that combo string from the stored
    # partial factors (gamma_dl, gamma_ll).
    _deck_combo = (
        r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")
    ) if _dk_has else "---"

    def _deck_row(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return ("---", "---", "---", "---")
        if is_oh and not _dk_oh:
            return (_deck_combo, "N/A", "N/A", "N/A")
        dem = _dkv(dem_key)
        cap = _dkv(cap_key)
        ur = (dem / cap) if cap > 0 else None
        return (_deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", _ur_522(ur), ur)

    def _row522_msg(label, msg):
        # Single message spanning the 4 data columns.
        return label + r" & \multicolumn{4}{c|}{" + msg + r"} \\[\osdagRowGap]" + "\n\\hline"

    # End diaphragm rows come from the backend's own end-diaphragm results
    # (previously they repeated the intermediate cross-bracing values).
    #  * Cross Bracing type with results -> axial rows, like cross bracing.
    #  * Cross Bracing type, no results  -> the analysis gave no force.
    #  * Rolled / Welded beam            -> design not implemented in backend.
    _ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            _ed_type = str(_v)
            break
    _ed_is_cb = "brac" in _ed_type.strip().lower()
    _ED = "End Diaphragms"
    if _ed_is_cb and _ed_has_results:
        _ed_rows = [
            _row522(r"End Diaphragm --- Compression", _cb_row("compression", _ed_view), _ED, "Compression"),
            _row522(r"End Diaphragm --- Tension",     _cb_row("tension", _ed_view),     _ED, "Tension"),
            _row522(r"End Diaphragm --- Slenderness", _cb_slender_row(_ed_view),        _ED, "Slenderness"),
        ]
    elif _ed_is_cb:
        _ed_rows = [_row522_msg(r"End Diaphragm", r"No force from analysis --- see Section~\ref{sec:end-diaphragm}")]
    else:
        _ed_rows = [_row522_msg(r"End Diaphragm", r"Rolled / Welded section --- design to be added")]

    # Crack width (slab): governing crack width vs limit from the deck designer
    # (frequent SLS combination). _dk_gov_wk is the max of bottom/top/overhang wk.
    # The governing load combo is the SLS-frequent combination with the highest
    # DCR (its full expression comes straight from the per_lc keys).
    def _gov_sls_frequent():
        best = None  # (dcr, lc)
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"):
                continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower():
                    continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    _wk_lim = _dkv(KEY_DD_WK_LIMIT)
    _crack_cells = (
        (_gov_sls_frequent() if _dk_has else "---"),
        (f"{_dk_gov_wk:.3f} mm" if _dk_has else "---"),
        (f"{_wk_lim:.3f} mm" if _dk_has else "---"),
        (_ur_522(_dk_gov_wk / _wk_lim) if (_dk_has and _wk_lim > 0) else "---"),
        ((_dk_gov_wk / _wk_lim) if (_dk_has and _wk_lim > 0) else None),
    )

    _t522 = [
        _row522(r"Girder --- Moment", _dcr_row({1}), "Steel Plate Girders", "Moment"),
        _row522(r"Girder --- Shear", _dcr_row({2}), "Steel Plate Girders", "Shear"),
        _row522(r"Girder --- LTB (constr.)", _dcr_row({5}), "Steel Plate Girders", "LTB"),
        _row522(r"Girder --- Deflection", _dcr_row({13, 14}, fallback_unit="mm"), "Steel Plate Girders", "Deflection"),
        _row522(r"Girder --- Stress", _dcr_row({11}, fallback_unit="MPa"), "Steel Plate Girders", "Stress"),
        _row522(r"Girder --- Fatigue", _dcr_row({8, 9}, fallback_unit="MPa"), "Steel Plate Girders", "Fatigue"),
        _row522(r"Transverse Shear (slab)", _dcr_row({16}), "Concrete Deck Slab", "Transverse shear"),
        _row522(r"Crack Width (slab)", _crack_cells, "Concrete Deck Slab", "Crack width"),
        _row522(r"Deck --- Flexure (sagging)", _deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m"), "Concrete Deck Slab", "Sagging"),
        _row522(r"Deck --- Flexure (hogging)", _deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m"), "Concrete Deck Slab", "Hogging"),
        _row522(r"Deck --- Cantilever Overhang", _deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True), "Concrete Deck Slab", "Overhang"),
        _row522(r"Deck --- Punching Shear", _deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa"), "Concrete Deck Slab", "Punching"),
        _row522(r"Deck --- One-Way Shear", _deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m"), "Concrete Deck Slab", "One-way shear"),
        _row522(r"Cross Bracing --- Compression", _cb_row("compression"), "Cross Bracing", "Compression"),
        _row522(r"Cross Bracing --- Tension", _cb_row("tension"), "Cross Bracing", "Tension"),
        _row522(r"Cross Bracing --- Slenderness", _cb_slender_row(), "Cross Bracing", "Slenderness"),
    ] + _ed_rows
    t522_content = "\n".join(_t522)

    # ── Section 5.5 utilization graphs ─────────────────────────────────────
    # Drawn from ur_records, i.e. exactly the URs printed in the summary table.
    _ur_figures_tex = ""
    if images_dir:
        _no_data = {}
        if _ed_is_cb and not _ed_has_results:
            _no_data["End Diaphragms"] = "No force from\nanalysis"
        elif not _ed_is_cb:
            _no_data["End Diaphragms"] = "Design not\nimplemented"
        _sum_png = safe_chart(utilization_summary_chart, ur_records,
                              os.path.join(images_dir, "ur_summary.png"), _no_data)
        _det_png = safe_chart(utilization_detail_chart, ur_records,
                              os.path.join(images_dir, "ur_detail.png"))
        if _sum_png:
            _ur_figures_tex += (
                "\n\\begin{figure}[H]\n\\centering\n"
                "\\includegraphics[width=0.92\\linewidth]{" + _sum_png.replace("\\", "/") + "}\n"
                "\\caption{Overall utilization ratio of each structural element "
                "(governing check shown in brackets). Bars above the dashed line at "
                "UR = 1.0 fail.}\n\\label{fig:ur-summary}\n\\end{figure}\n")
        if _det_png:
            _ur_figures_tex += (
                "\n\\begin{figure}[H]\n\\centering\n"
                "\\includegraphics[width=\\linewidth]{" + _det_png.replace("\\", "/") + "}\n"
                "\\caption{Utilization ratio of every design check in Table~\\ref{tab:overall-summary}, "
                "grouped by structural element.}\n\\label{fig:ur-detail}\n\\end{figure}\n")

    # Intro under the 5.5 heading (also keeps the heading from being stranded
    # at a page bottom, since the section would otherwise open with a table).
    _ur_intro_tex = (
        r"Table~\ref{tab:overall-summary} lists the governing load combination, demand, "
        r"capacity and utilization ratio (UR = Demand / Capacity) of every design check."
    )
    if _ur_figures_tex:
        _ur_intro_tex += (
            r" The same values are plotted in Figure~\ref{fig:ur-summary} and "
            r"Figure~\ref{fig:ur-detail}. The overall UR of a structural element is "
            r"the highest UR among its checks (its governing check), so a failure of any "
            r"one check is shown as a failure of the element."
        )

    # End diaphragm section body: real end-diaphragm tables when the backend
    # designed the members; otherwise say why there is nothing to report
    # (previously the cross-bracing tables were repeated here).
    if _ed_has_results:
        _ed_body = r"""\vspace{\osdagBlockGap}

\vspace{\osdagSmallGap}
\begingroup  % table-local settings
\setlength{\LTleft}{0pt}
\setlength{\LTright}{\fill}

\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\caption{End Diaphragm --- Connection and Section Properties}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{6}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{6}
\endfoot
\endlastfoot
""" + ed_forces_content + r"""
\end{longtable}
\endgroup
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.4cm}|C{2.4cm}|C{2.4cm}|>{\centering\arraybackslash}p{3.4cm}|}
\caption{End Diaphragm --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{6}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{6}
\endfoot
\endlastfoot
""" + ed_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\vspace{\osdagBlockGap}

\begin{longtable}{|C{1.6cm}|L{1.6cm}|C{2.0cm}|C{2.8cm}|C{1.7cm}|C{1.7cm}|C{1.2cm}|C{1.6cm}|}
\caption{End Diaphragm Design --- Capacity Summary}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{8}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{8}
\endfoot
\endlastfoot
""" + ed_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge end-diaphragm bracing design.}

"""
    else:
        _ed_body = _ED_NO_RESULT_NOTE + "\n"

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|L{8.0cm}|>{\centering\arraybackslash}p{5.0cm}|}
\caption{Girder Section Properties (Final Optimized / User-selected)}\\
\hline
\osdagHeadRow \textbf{Girder} & \textbf{Property} & \textbf{Value} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{3}
\hline
\osdagHeadRow \textbf{Girder} & \textbf{Property} & \textbf{Value} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{3}
\endfoot
\endlastfoot
""" + t51_content + r"""
\end{longtable}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|L{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{4.0cm}|}
\caption{Girder Section Classification}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t52_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800:2007 Table 2}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Moment Capacity Check}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t53_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Shear Capacity Check}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t54_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Interaction Checks (M-V and M-N)}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t55_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.3}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Lateral Torsional Buckling Check -- Construction Stage}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t56_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}p{6.5cm}|}
\caption{Stiffener Design Summary}\\
\hline
\endfirsthead
\ltcontinuedhead{3}
\hline
\endhead
\ltcontinuedfoot{3}
\endfoot
\endlastfoot
""" + t57_content + r"""
\end{longtable}
""" + t58_block + r"""
\vspace{\osdagBlockGap}

\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{End Panel Stiffener Checks}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t59_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{Serviceability -- Deflection Checks}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t510_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{Serviceability -- Maximum Stress Limitation}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t511_content + r"""
\end{longtable}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{Serviceability -- Fatigue Assessment}\\
\hline
\osdagHeadRow \textbf{} & \textbf{Stress Range, $\Delta\sigma$ (MPa)} & \textbf{Fatigue Limit, $f_{fd}$ (MPa)} & \textbf{Utilization Ratio} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{} & \textbf{Stress Range, $\Delta\sigma$ (MPa)} & \textbf{Fatigue Limit, $f_{fd}$ (MPa)} & \textbf{Utilization Ratio} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t512_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness > 25 mm.}

\vspace{\osdagBlockGap}
\vspace{\osdagSmallGap}
\begin{longtable}{|C{1.6cm}|>{\centering\arraybackslash}p{3.6cm}|C{2.4cm}|C{2.0cm}|C{2.1cm}|C{1.7cm}|C{1.5cm}|}
\caption{Girder Design Summary (DCR / Utilization Ratio)}\\
\hline
\osdagHeadRow \textbf{Girder} & \textbf{Controlling LC / Combination} & \textbf{Controlling Check} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{7}
\hline
\osdagHeadRow \textbf{Girder} & \textbf{Controlling LC / Combination} & \textbf{Controlling Check} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{7}
\endfoot
\endlastfoot
""" + g_summary_table_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.}

\vspace{\osdagBlockGap}

\begin{longtable}{|L{3.6cm}|C{5.6cm}|>{\centering\arraybackslash}p{2.6cm}|L{3.0cm}|}
\caption{Shear Connector Capacity}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
""" + t514_content + r"""
\end{longtable}

\vspace{\osdagBlockGap}

\begingroup  % table-local settings
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{3.2cm}|>{\centering\arraybackslash}p{4.3cm}|>{\centering\arraybackslash}p{4.3cm}|C{2.0cm}|}
\caption{Shear Connector Spacing}\\
\hline
\osdagHeadRow \textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
""" + t515_content + r"""
\end{longtable}
\endgroup
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.3cm}|>{\arraybackslash}p{7.2cm}|C{2.0cm}|}
\caption{Transverse Shear and Detailing Checks}\\
\hline
\osdagHeadRow \textbf{Check} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{3}
\hline
\osdagHeadRow \textbf{Check} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{3}
\endfoot
\endlastfoot
""" + t516_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{Deck Slab --- Loading and Geometry}\\
\hline
\endfirsthead
\ltcontinuedhead{2}
\hline
\endhead
\ltcontinuedfoot{2}
\endfoot
\endlastfoot
\textnormal{Effective Span of Deck Slab, $l_{eff}$} & """ + _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + r""" mm (girder spacing, c/c) \\[\osdagRowGap]
\hline
\textnormal{Deck Thickness, $t_s$} & """ + _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + r""" mm \\[\osdagRowGap]
\hline
\textnormal{Clear Cover (IRC 112 Cl. 15.2)} & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm \\[\osdagRowGap]
\hline
\textnormal{Concrete Grade (IRC 112 Cl. 6.4)} & """ + _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC) + r""" ($f_{ck}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r""" MPa, $f_{ctm}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + r""" MPa) \\[\osdagRowGap]
\hline
\textnormal{Reinforcement Grade (IRC 112 Cl. 6.2)} & """ + _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL) + r""" ($f_y$ = """ + _dkf(KEY_DD_FY, nd=0) + r""" MPa) \\[\osdagRowGap]
\hline
\textnormal{Dead Load per Unit Area, $w_{DL}$} & """ + _dkf(KEY_DD_WDL, nd=2) + r""" kN/m² (slab self-weight) \\[\osdagRowGap]
\hline
\textnormal{IRC 6 Wheel Load (Class A / 70R)} & """ + _dkf(KEY_DD_WHEEL_LOAD, nd=1) + r""" kN \\[\osdagRowGap]
\hline
\textnormal{Tyre Contact Width (IRC 6 Annex~A)} & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" mm (transverse) \\[\osdagRowGap]
\hline
\textnormal{Impact Factor (IRC 6 Cl. 208.2)} & """ + _dkf(KEY_DD_IMPACT_FACTOR, nd=3) + r""" \\[\osdagRowGap]
\hline
\textnormal{Governing Live Load Case} & """ + _dkf(KEY_DD_VEHICLE) + r""" \\[\osdagRowGap]
\hline
\end{longtable}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}\\
\hline
\osdagHeadRow \textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
\multirow{5}{*}{\makecell{At Midspan\\(Sagging)}} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/10$ & """ + _dkf(KEY_DD_M_DL, nd=2) + r""" kN-m/m & --- \\[\osdagRowGap]
\cline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Effective width (IRC 112 B3.1) & """ + _dkf(KEY_DD_M_LL, nd=2) + r""" kN-m/m & --- \\[\osdagRowGap]
\cline{2-5}
 & Total Design BM, $M_{u,sag}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL & """ + _dkf(KEY_DD_M_ULS_SAG, nd=2) + r""" kN-m/m & --- \\[\osdagRowGap]
\cline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[\osdagRowGap]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_BOT, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG)) + r""" \\[\osdagRowGap]
\hline
\multirow{3}{*}{\makecell{At Support\\(Hogging)}} & Total Design BM, $M_{u,hog}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL (at support) & """ + _dkf(KEY_DD_M_ULS_HOG, nd=2) + r""" kN-m/m & --- \\[\osdagRowGap]
\cline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & --- \\[\osdagRowGap]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_TOP, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG)) + r""" \\[\osdagRowGap]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{Deck Slab --- Cantilever Overhang Flexure Check}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
Overhang Length, $l_{oh}$ & --- & """ + _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m") + r""" & --- \\[\osdagRowGap]
\hline
Crash Barrier Load Moment & IRC 6 Cl. 206.4 & """ + _dkoh(KEY_DD_M_BARRIER, nd=2, unit=" kN-m/m") + r""" & --- \\[\osdagRowGap]
\hline
Dead Load Moment & $w_{DL}\,l_{oh}^2/2$ + railing & """ + _dkoh(KEY_DD_M_DL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[\osdagRowGap]
\hline
Live Load Moment (eccentric wheel) & Wheel load $\times$ arm & """ + _dkoh(KEY_DD_M_LL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[\osdagRowGap]
\hline
Total Hogging Moment, $M_{u,oh}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" (LL + CB) & """ + _dkoh(KEY_DD_M_ULS_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[\osdagRowGap]
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 12.2 & """ + _dkoh(KEY_DD_MU_OH, nd=2, unit=" kN-m/m") + r""" & """ + (_dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else "---")) + r""" \\[\osdagRowGap]
\hline
\end{longtable}
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.}

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q\,(1+IF)\,P_w$ & """ + _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + r""" kN & --- \\[\osdagRowGap]
\hline
Tyre Contact Area & $a \times b$ (IRC 6 Annex~A) & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" $\times$ """ + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + r""" mm & --- \\[\osdagRowGap]
\hline
Loaded Area at mid-depth, $b_0$ & $c_1 \times c_2$ (incl.\ WC dispersion) & """ + _dkf(KEY_DD_PUNCH_C1, nd=0) + r""" $\times$ """ + _dkf(KEY_DD_PUNCH_C2, nd=0) + r""" mm & --- \\[\osdagRowGap]
\hline
Control Perimeter, $u_1$ & $2(c_1+c_2) + 4\pi d$ & """ + _dkf(KEY_DD_PUNCH_U1, nd=0) + r""" mm & --- \\[\osdagRowGap]
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed} / (u_1\,d)$ & """ + _dkf(KEY_DD_PUNCH_VED, nd=3) + r""" MPa & --- \\[\osdagRowGap]
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Eq.\ 10.1 & """ + _dkf(KEY_DD_VRD_C_MPA, nd=3) + r""" MPa & --- \\[\osdagRowGap]
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK))) + r""" \\[\osdagRowGap]
\hline
\end{longtable}
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

\vspace{\osdagBlockGap}
\clearpage
\begin{longtable}{|L{7cm}|>{\arraybackslash}p{8.5cm}|}
\caption{Crack Width Check (Deck Slab)}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Value / Reference} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{2}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Value / Reference} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{2}
\endfoot
\endlastfoot
\textnormal{Min. Reinforcement for Crack Control, $A_{s,min}$} & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m [IRC 112 Cl. 16.5.1] \\[\osdagRowGap]
\hline
\textnormal{Provided Reinforcement (bottom)} & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c (""" + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m) \\[\osdagRowGap]
\hline
\textnormal{Max. Permissible Crack Width} & """ + _dkf(KEY_DD_WK_LIMIT, nd=2) + r""" mm \\[\osdagRowGap]
\hline
\textnormal{Calculated Crack Width, $w_k$ (governing)} & """ + _dk_gov_wk_str + r""" mm \\[\osdagRowGap]
\hline
\textnormal{Crack Width Check} & """ + _dks(_dk_crack_ok) + r""" \\[\osdagRowGap]
\hline
\end{longtable}

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{One-Way (Beam) Shear Check (Deck Slab)}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
Design Shear per unit width, $V_{Ed}$ & $\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$ & """ + _dkf(KEY_DD_SHEAR_VED, nd=2) + r""" kN/m & --- \\[\osdagRowGap]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[\osdagRowGap]
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & """ + (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[\osdagRowGap]
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b_w\,d) \leq 0.02$ & """ + (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[\osdagRowGap]
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & $v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2) & """ + _dkf(KEY_DD_SHEAR_VRDC, nd=2) + r""" kN/m & --- \\[\osdagRowGap]
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK))) + r""" \\[\osdagRowGap]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

\vspace{\osdagBlockGap}
\begin{longtable}{|L{5.5cm}|>{\centering\arraybackslash}p{4.1cm}|>{\centering\arraybackslash}p{4.1cm}|C{1.8cm}|}
\caption{Reinforcement Detailing Summary (Deck Slab)}\\
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{4}
\hline
\osdagHeadRow \textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{4}
\endfoot
\endlastfoot
\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} \\[\osdagRowGap]
\hline
Required Area, $A_{st,req}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT)) + r""" \\[\osdagRowGap]
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c & --- \\[\osdagRowGap]
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN)) + r""" \\[\osdagRowGap]
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & """ + _dkf(KEY_DD_SPACING_MAX, nd=0) + r""" mm & """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm & """ + _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX)) + r""" \\[\osdagRowGap]
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} \\[\osdagRowGap]
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & """ + _dkf(KEY_DD_AS_LONG, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN))) + r""" \\[\osdagRowGap]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support / Cantilever Overhang)}} \\[\osdagRowGap]
\hline
Required Area, $A_{st,top}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_TOP, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP)) + r""" \\[\osdagRowGap]
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} \\[\osdagRowGap]
\hline
Clear Cover (IRC 112 Cl. 15.2) & $\geq$ """ + _dkf(KEY_DD_MIN_COVER, nd=0) + r""" mm (Table 14.2) & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm & """ + _dks(bool(deck_rpt.get(KEY_DD_COVER_OK))) + r""" \\[\osdagRowGap]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).

\vspace{\osdagBlockGap}

\vspace{\osdagSmallGap}
\begingroup  % table-local settings
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\caption{Cross Bracing --- Connection and Section Properties}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{6}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{6}
\endfoot
\endlastfoot
""" + cb_forces_content + r"""
\end{longtable}
\endgroup
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.4cm}|C{2.4cm}|C{2.4cm}|>{\centering\arraybackslash}p{3.4cm}|}
\caption{Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{6}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{6}
\endfoot
\endlastfoot
""" + cb_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\vspace{\osdagBlockGap}
\begin{longtable}{|C{1.6cm}|L{1.6cm}|C{2.0cm}|C{2.8cm}|C{1.7cm}|C{1.7cm}|C{1.2cm}|C{1.6cm}|}
\caption{Cross Bracing Design --- Capacity Summary}\\
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{8}
\hline
\osdagHeadRow \textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{8}
\endfoot
\endlastfoot
""" + cb_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

""" + _ed_body + r"""
% ===========================
\section{Overall Design Check Summary}
\label{sec:overall-summary}
% ===========================

""" + _ur_intro_tex + r"""

\vspace{\osdagSmallGap}
\begin{longtable}{|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|}
\caption{Overall Design Check Summary --- All Members}\label{tab:overall-summary}\\
\hline
\osdagHeadRow \textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[\osdagRowGap]
\hline
\endfirsthead
\ltcontinuedhead{5}
\hline
\osdagHeadRow \textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[\osdagRowGap]
\hline
\endhead
\ltcontinuedfoot{5}
\endfoot
\endlastfoot
""" + t522_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.}
""" + _ur_figures_tex + r"""
"""

