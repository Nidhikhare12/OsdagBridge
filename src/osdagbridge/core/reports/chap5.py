# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
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

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries
from osdagbridge.core.reports.latex.tables import ReportTable
from osdagbridge.core.reports.latex.text import status_fail
from osdagbridge.core.reports.latex.figures import figure
from osdagbridge.core.reports.latex.text import vspace, row_end, row_pad, row_end_nobreak
from osdagbridge.core.reports.theme import get_active_theme

_THEME = get_active_theme()
_ROW_END = row_end()
_ROW_PAD_3 = row_pad(3.0)
_ROW_NOBREAK = row_end_nobreak(6.0)
_VSPACE_MD = vspace(_THEME.spacing.space_md)
_VSPACE_SM = vspace(_THEME.spacing.space_sm)
_C5 = _THEME.columns.ch5
from osdagbridge.core.reports.latex.text import vspace, row_end, row_pad, row_end_nobreak
from osdagbridge.core.reports.theme import get_active_theme

_THEME = get_active_theme()
_ROW_END = row_end()
_ROW_PAD_3 = row_pad(3.0)
_ROW_NOBREAK = row_end_nobreak(6.0)
_VSPACE_MD = vspace(_THEME.spacing.space_md)
_VSPACE_SM = vspace(_THEME.spacing.space_sm)
_C5 = _THEME.columns.ch5

if TYPE_CHECKING:
    pass
def ch5_design_checks(checks_data, bridge) -> str:
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
            r"\multirow{13}{*}{\makecell{" + lbl + r"""}} & \textnormal{Depth, D (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOTAL_DEPTH) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Top Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_WIDTH) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Bottom Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_WIDTH) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Top Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_THICKNESS) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Bottom Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_THICKNESS) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Web Thickness, $t_w$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_WEB_THICKNESS) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Gross Area, A (cm$^2$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_AREA) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Moment of Inertia, $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_IZ) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Elastic Section Modulus, $Z_{ez}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZZ) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Plastic Section Modulus, $Z_{pz}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZUZ) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Effective Slab Width, $b_{eff}$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_EFFECTIVE_SLAB_WIDTH) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Transformed Composite $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_COMPOSITE_IZ) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Depth to Plastic Neutral Axis (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_PNA_DEPTH) + " " + _ROW_END + r"""
\hline"""
        )
    def _chunk_girders(rows, per_chunk=2):
        if len(rows) <= per_chunk:
            return "\n".join(rows)
        parts = []
        for i in range(0, len(rows), per_chunk):
            parts.append("\n".join(rows[i:i + per_chunk]))
        return "\n\\pagebreak\n".join(parts)

    t51_content = _chunk_girders(t51_rows, per_chunk=2)

    # Generate Table 5.2 rows
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Top Flange & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + " " + _ROW_END + r"""
\cline{2-5}
 & Web & """ + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + " " + _ROW_END + r"""
\cline{2-5}
 & Overall Section & --- & --- & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + " " + _ROW_END + r"""
\hline"""
        )
    t52_content = "\n".join(t52_rows)

    # Generate Table 5.3 rows
    # Flexure UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _flex_ur = float(bridge.output_dict.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = "PASS" if _flex_ur <= 1.0 else status_fail("FAIL")
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = "---"
    t53_rows = []
    for lbl, _ in girder_entries:
        t53_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Applied Moment, $M_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_MU_APPLIED, " kN-m") + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & Design Moment Capacity, $M_d$ & IRC 22 Cl. 603.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_MD_CAPACITY, " kN-m") + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & Utilization Ratio, $M_u / M_d$ & $M_u / M_d$ & """ + _flex_ur_str + r""" & """ + _flex_status + " " + _ROW_END + r"""
\hline"""
        )
    t53_content = "\n".join(t53_rows)

    # Generate Table 5.4 rows
    # Shear UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _shear_ur = float(bridge.output_dict.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = "PASS" if _shear_ur <= 1.0 else status_fail("FAIL")
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = "---"
    t54_rows = []
    for lbl, _ in girder_entries:
        t54_rows.append(
            r"\multirow{8}{*}{\makecell{" + lbl + r"""}} & Applied Shear, $V_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VU, " kN") + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Shear Area, $A_v$ & $d_w \times t_w$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_AV, " mm$^2$") + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Panel Aspect Ratio, c/d & --- & """ + _render_value(bridge.output_dict, KEY_SD_PANEL_CD) + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Shear Buckling Coefficient, $k_v$ & IS 800 Cl. 8.4.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_KV) + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_LAMBDA_W) + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Design Shear Stress, $\tau_b$ & IRC 22 Cl. 603.3.3.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_TAU_B, " MPa") + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Shear Buckling Resistance, $V_{cr}$ & $A_v \times \tau_b$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VCR, " kN") + r""" & --- """ + _ROW_NOBREAK + r"""
\cline{2-5}
 & Utilization Ratio, $V_u / V_d$ & $V_u / V_d$ & """ + _shear_ur_str + r""" & """ + _shear_status + " " + _ROW_END + r"""
\hline"""
        )
    t54_content = _chunk_girders(t54_rows, per_chunk=2)

    # Generate Table 5.5 rows
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return status_fail("FAIL")
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
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & High Shear Condition? & $V_u > 0.6\,V_d$ & """ + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & """ + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & """ + _mv_ur_str + r""" & """ + _mv_status + " " + _ROW_END + r"""
\cline{2-5}
 & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & """ + _mn_cond + r""" & """ + _mn_val + r""" & """ + _mn_status + " " + _ROW_END + r"""
\hline"""
        )
    t55_content = "\n".join(t55_rows)

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
            r"\multirow{5}{*}{\makecell{" + lbl + r"""}} & Elastic Critical Moment, $M_{cr}$ & IRC 22 Cl. 603.3.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & LTB Reduction Factor, $\chi_{LT}$ & IS 800 Cl. 8.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & LTB Resistance, $M_b$ & $\chi_{LT}\,M_p / \gamma_{m0}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r""" & --- """ + _ROW_END + r"""
\cline{2-5}
 & $M_u \leq M_b$ & $M_u / M_b$ & """ + _ltb_ur_str + r""" & """ + _ltb_status + " " + _ROW_END + r"""
\hline"""
        )
    t56_content = "\n".join(t56_rows)

    # Generate Table 5.7 rows
    t57_rows = []
    for idx, (lbl, _) in enumerate(girder_entries):
        if idx == 2:
            t57_rows.append(r"\pagebreak")
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + lbl + r"""}} & \textnormal{Shear Buckling Design Method} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_METHOD) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Intermediate Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Intermediate Stiffener Spacing (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{End Panel Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{No. of End Panel Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + " " + _ROW_END + r"""
\cline{2-3}
 & \textnormal{Longitudinal Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + " " + _ROW_END + r"""
\hline"""
        )
    t57_content = "\n".join(t57_rows)

    # Generate table - intermediate stiffener checks (IS 800 CL. 8.7.1.2)
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else status_fail("FAIL")
        except (TypeError, ValueError):
            return "---"
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Min. Moment of Inertia, $I_s$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r""" & """ + _iys_status + " " + _ROW_END + r"""
\cline{2-5}
 & Buckling Resistance, $F_{qd} \geq F_q$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r""" & """ + _fqd_status + " " + _ROW_END + r"""
\hline"""
        )
    t58_content = "\n".join(t58_rows)

    # (Intermediate Stiffener Checks) is a verification table — it only
    # has data when the user supplied stiffener sizes (Design Type = Custom). In
    # Optimized mode the stiffeners are auto-sized (nothing to verify), so the
    # whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = "\n" + _VSPACE_MD + "\n" + _make_table(
            _C5.CAPACITY_5COL,
            r"\textbf{Intermediate Stiffener Checks}",
            [["", "Check", "Required", "Provided", "Status"]],
            t58_content,
        ) + r"""
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
        status = "PASS" if float(prov) >= float(_bs_r) else status_fail("FAIL")
        return (req_s, prov_s, status)
    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & Web Buckling Resistance & """ + _wb_req + r""" & """ + _wb_prov + r""" & """ + _wb_st + " " + _ROW_END + r"""
\cline{2-5}
 & Local Crushing Resistance & """ + _lc_req + r""" & """ + _lc_prov + r""" & """ + _lc_st + " " + _ROW_END + r"""
\cline{2-5}
 & Bearing Capacity & """ + _ps_req + r""" & """ + _ps_prov + r""" & """ + _ps_st + " " + _ROW_END + r"""
\cline{2-5}
 & Column Buckling Resistance & """ + _cb_req + r""" & """ + _cb_prov + r""" & """ + _cb_st + " " + _ROW_END + r"""
\hline"""
        )
    t59_content = "\n".join(t59_rows)

    # ── Table 5.10: Serviceability — Deflection Checks (IRC 22 Cl. 604.3.2) ──────
    # Allowable limits: span-dependent, same for all girders, from output_dict.
    # Actual deflections: per-girder from bridge._deflections_cache — the same
    # source used by resolve_deflection_live_load/total in generate_results_values_builder.py.
    # Keys: {"G1": {"live_mm": X, "total_mm": Y}, ...}
    # lbl from girder_entries is "G1", "G2", ... which matches cache keys exactly.

    def _defl_status(actual, allowable):
        """PASS / red FAIL for deflection; '---' when values are missing."""
        try:
            return "PASS" if float(actual) <= float(allowable) else status_fail("FAIL")
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
            + _defl_status(_live_mm,  _allow_live_mm) + " " + _ROW_END + r"""
\cline{2-5}
 & Total Load Deflection, $\delta_{total}$ (mm) & """
            + _allow_total_str + r""" & """
            + _dfmt(_total_mm, nd=3) + r""" & """
            + _defl_status(_total_mm, _allow_total_mm) + " " + _ROW_END + r"""
\hline"""
        )
    t510_content = "\n".join(t510_rows)

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
            return "PASS" if float(actual) <= float(allow) else status_fail("FAIL")
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
            + _steel_status + " " + _ROW_END + r"""
\hline"""
        )
    t511_content = "\n".join(t511_rows)

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
        return status_fail(str(s)) if "FAIL" in str(s).upper() else str(s)

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + lbl + r"""} & """
            + _mpa(_g.get("demand")) + r""" & """
            + _mpa(_g.get("capacity")) + r""" & """
            + _dfmt(_g.get("ur"), nd=2) + r""" & """
            + _fat_status(_g.get("status")) + " " + _ROW_END + r"""
\hline"""
        )
    t512_content = "\n".join(t512_rows)

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
            g_summary_rows.append(lbl + r""" &  &  &  &  &  &  """ + _ROW_END + r"""
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
            + r""" & """ + _fat_status(ctrl.get("status")) + " " + _ROW_END + r"""
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
        r"""Design Resistance, $Q_u$ & \footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$""" + _ROW_PAD_3 + r"""$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$""" + _ROW_PAD_3 + r"""$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$} & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qu_kN)) + r""" & IRC 22 Cl. 606.3.1 (Eq. 6.1) """ + _ROW_END + r"""
\hline
Fatigue Shear Resistance, $Q_r$ & IRC 22 Table 8 ($\phi d$, $N_{sc}$) & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qr_kN)) + r""" & IRC 22 Cl. 606.3.2 (Table 8) """ + _ROW_END + r"""
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
                + _defl_status(_sc_prov, req) + " " + _ROW_END)

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
    _ts_status = (status_fail("FAIL") if _ts_ok is False else "PASS") if _ts_ok is not None else "---"

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
        return check + r" & " + value + r" & " + status + " " + _ROW_END

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

    # Generate Table 5.20(a) rows
    cb_forces_rows = []
    pairs = bridge.get_cb_pairs()

    if not pairs:
        # fallback: one placeholder row
        cb_forces_rows.append(
            r"""Between Girders & Diagonal &  &  &  &  """ + _ROW_END + r"""
\hline"""
        )
    else:
        for pair in pairs:
            pair_id = pair.replace("-", "")
            for member, label in [("diagonal", "Diagonal"),
                                ("chord", "Top / Bottom chord")]:
                force_str, ftype = bridge.get_cb_governing_force(pair, member)
                conn_type = bridge.get_cb_connection(pair, member, ftype)
                section  = bridge.get_cb_section(pair, member, ftype)

                # Fetch properties from output_dict
                if member == "diagonal":
                    pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
                else:
                    pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                    if bridge.output_dict.get(f"{pfx}.A") is None:
                        pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"

                area_cm2 = bridge.output_dict.get(f"{pfx}.A")
                rv_cm = bridge.output_dict.get(f"{pfx}.rv")

                # Convert Area: cm² -> mm²
                area_str = f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else ""
                # Convert rv: cm -> mm
                rmin_str = f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""
                cb_forces_rows.append(
                    r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}} & "
                    + label + r" & " + conn_type + r" & " + section
                    + r" & " + area_str + r" & " + rmin_str
                    + " " + _ROW_END + r"\cline{2-6}"
                )
            cb_forces_rows.append(r"\hline")
    cb_forces_content = "\n".join(cb_forces_rows)

    # Generate Table 5.20(b) rows
    def get_status_str(slnd_str, limit):
        try:
            v = float(slnd_str)
            return "PASS" if v <= limit else status_fail("FAIL")
        except (ValueError, TypeError):
            return ""
    cb_slenderness_rows = []
    if not pairs:
        cb_slenderness_rows.append(
            r"""Between Girders & Diagonal & C &  &  &  ---  """ + _ROW_END + r"""
\hline"""
        )
    else:
        for pair in pairs:
            kl_diag = bridge.get_cb_effective_length("diagonal")
            slnd_diag = bridge.get_cb_slenderness(pair, "diagonal")
            status_diag = get_status_str(slnd_diag, 250)
            
            kl_tc = bridge.get_cb_effective_length("chord")
            slnd_tc = bridge.get_cb_slenderness(pair, "chord")
            status_tc = get_status_str(slnd_tc, 250)
            
            kl_bc = bridge.get_cb_effective_length("chord")
            slnd_bc = bridge.get_cb_slenderness(pair, "chord")
            status_bc = get_status_str(slnd_bc, 400)
            
            top_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
            bottom_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)
            
            num_rows = 1 + int(top_chord_enabled) + int(bottom_chord_enabled)
            row_tex = r"\multirow{" + str(num_rows) + r"}{*}{\makecell{" + _tex(pair) + r"}}"
            row_tex += f" & Diagonal & C & {kl_diag} & {slnd_diag} & 250 --- {status_diag} " + _ROW_END
            
            if top_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Top chord & C & {kl_tc} & {slnd_tc} & 250 --- {status_tc} " + _ROW_END
            if bottom_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Bottom chord & T & {kl_bc} & {slnd_bc} & 400 --- {status_bc} " + _ROW_END
                
            row_tex += "\n\\hline"
            cb_slenderness_rows.append(row_tex)
    cb_slenderness_content = "\n".join(cb_slenderness_rows)

    # Generate Table 5.20(c) rows
    cb_capacity_rows = []
    for pair in pairs:
        rows_for_pair = []
        for member, label in [("diagonal", "Diagonal"),
                            ("chord", "Chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            section  = bridge.get_cb_section(pair, member, ftype)
            gov_lc   = bridge.get_cb_gov_lc(pair, member, ftype)
            capacity = bridge.get_cb_capacity(pair, member, ftype)
            ur       = bridge.get_cb_efficiency(pair, member, ftype)
            status   = bridge.get_cb_status(pair, member, ftype)
            rows_for_pair.append(
                r" & " + label + r" & " + section
                + r" & " + gov_lc + r" & " + force_str + r" & " + capacity
                + r" & " + ur + r" & " + status + " " + _ROW_END + r"\cline{2-8}"
            )
        first = r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}" + rows_for_pair[0]
        rest  = rows_for_pair[1:]
        cb_capacity_rows.append(first)
        cb_capacity_rows.extend(rest)
        cb_capacity_rows.append(r"\hline")
    cb_capacity_content = "\n".join(cb_capacity_rows)



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

    # ── Table 5.22: Overall Design Check Summary — rendered from data/utilization.py (R4)
    from osdagbridge.core.reports.data.utilization import collect_utilization
    ud = collect_utilization(bridge)

    def _render_t522_row(r):
        if r.note and ("design to be added" in r.note or "not implemented" in r.note):
            return f"{r.check_name} & \\multicolumn{{4}}{{c|}}{{{r.note}}} " + _ROW_END + "\n\\hline"
        ur_str = "---"
        if r.ur is not None:
            ur_str = f"{r.ur:.2f}"
            if r.ur > 1.0:
                ur_str = status_fail(ur_str)
        cells = [r.governing_combo or "---", r.demand_str or "---", r.capacity_str or "---", ur_str]
        return f"{r.check_name} & " + " & ".join(cells) + " " + _ROW_END + "\n\\hline"

    t522_content = "\n".join(_render_t522_row(r) for r in ud.records)

    def _make_table(col_spec, caption, header_rows, content):
        tbl = ReportTable(columns=col_spec, caption=caption, header_rows=header_rows)
        tbl.add_raw_rows(content)
        return tbl.dumps()

    t51_table = _make_table(
        _C5.PROPERTIES_3COL,
        r"\textbf{Girder Section Properties (Final Optimized / User-selected)}",
        [["Girder", "Property", "Value"]],
        t51_content,
    )
    t52_table = _make_table(
        _C5.CLASSIFICATION_5COL,
        r"\textbf{Girder Section Classification}",
        [["", "Element", "Slenderness Ratio", "Class Limit", "Classification"]],
        t52_content,
    )
    t53_table = _make_table(
        _C5.CAPACITY_5COL,
        r"\textbf{Moment Capacity Check}",
        [["", "Parameter", "Formula", "Value", "Status"]],
        t53_content,
    )
    t54_table = _make_table(
        _C5.CAPACITY_5COL,
        r"\textbf{Shear Capacity Check}",
        [["", "Parameter", "Formula", "Value", "Status"]],
        t54_content,
    )
    t55_table = _make_table(
        _C5.CAPACITY_5COL,
        r"\textbf{Interaction Checks (M-V and M-N)}",
        [["", "Check", "Condition", "Value", "Status"]],
        t55_content,
    )
    t56_table = _make_table(
        _C5.CAPACITY_5COL,
        r"\textbf{Lateral Torsional Buckling Check -- Construction Stage}",
        [["", "Parameter", "Formula", "Value", "Status"]],
        t56_content,
    )
    t57_table = _make_table(
        _C5.STIFFENER_SUMMARY_3COL,
        r"\textbf{Stiffener Design Summary}",
        [["Girder", "Parameter", "Value"]],
        t57_content,
    )
    if _is_custom:
        t58_block = "\n" + _VSPACE_MD + "\n" + _make_table(
            _C5.CAPACITY_5COL,
            "Intermediate Stiffener Checks",
            [["", "Check", "Required", "Provided", "Status"]],
            t58_content,
        ) + "\n\\noindent\\textit{Note: IS 800 Cl. 8.7.1.2}\n"
    else:
        t58_block = ""

    t59_table = _make_table(
        _C5.CAPACITY_ALT_5COL,
        r"\textbf{End Panel Stiffener Checks}",
        [["", "Check", "Required", "Provided", "Status"]],
        t59_content,
    )
    t510_table = _make_table(
        _C5.CAPACITY_ALT2_5COL,
        r"\textbf{Serviceability -- Deflection Checks}",
        [["", "Check", "Allowable", "Actual", "Status"]],
        t510_content,
    )
    t511_table = _make_table(
        _C5.CAPACITY_ALT2_5COL,
        r"\textbf{Serviceability -- Maximum Stress Limitation}",
        [["", "Element", "Allowable Stress", "Actual Stress", "Status"]],
        t511_content,
    )
    t512_table = _make_table(
        _C5.CAPACITY_ALT3_5COL,
        r"\textbf{Serviceability -- Fatigue Assessment}",
        [["", r"Stress Range, $\Delta\sigma$ (MPa)", r"Fatigue Limit, $f_{fd}$ (MPa)", "Utilization Ratio", "Status"]],
        t512_content,
    )
    t513_table = _make_table(
        _C5.BRACING_PROPERTIES_7COL,
        r"\textbf{Girder Design Summary (DCR / Utilization Ratio)}",
        [["Girder", "Controlling LC / Combination", "Controlling Check", "Demand", "Capacity", "UR", "Status"]],
        g_summary_table_content,
    )
    t514_table = _make_table(
        _C5.SHEAR_FORCES_4COL,
        r"\textbf{Shear Connector Capacity}",
        [["Parameter", "Formula", "Value", "Reference"]],
        t514_content,
    )
    t515_table = _make_table(
        _C5.DECK_DETAILS_4COL,
        r"\textbf{Shear Connector Spacing}",
        [["Criterion", "Governing Spacing", "Actual Spacing Provided", "Status"]],
        t515_content,
    )
    t516_table = _make_table(
        _C5.SHEAR_CHECKS_3COL,
        r"\textbf{Transverse Shear and Detailing Checks}",
        [["Check", "Value", "Status"]],
        t516_content,
    )

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

""" + _VSPACE_MD + r"""
""" + t51_table + r"""

""" + _VSPACE_MD + r"""
""" + t52_table + r"""
\noindent\textit{Note: IS 800:2007 Table 2}

""" + _VSPACE_MD + r"""
""" + t53_table + r"""
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

""" + _VSPACE_MD + r"""
""" + t54_table + r"""
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

""" + _VSPACE_MD + r"""
""" + t55_table + r"""
\noindent\textit{Note: IRC 22 Cl. 603.3.3.3}

""" + _VSPACE_MD + r"""
""" + t56_table + r"""
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}

\clearpage
""" + t57_table + r"""
""" + t58_block + r"""
""" + _VSPACE_MD + r"""

""" + t59_table + r"""
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}

""" + _VSPACE_MD + r"""
""" + t510_table + r"""
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

""" + _VSPACE_MD + r"""
""" + t511_table + r"""

""" + _VSPACE_MD + r"""
""" + t512_table + r"""
\noindent\textit{Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness > 25 mm.}

""" + _VSPACE_MD + r"""
""" + _VSPACE_SM + r"""
""" + t513_table + r"""
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.}

""" + _VSPACE_MD + r"""

""" + t514_table + r"""

""" + _VSPACE_MD + r"""

""" + t515_table + r"""
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}

""" + _VSPACE_MD + r"""
""" + t516_table + r"""
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.SHEAR_KEYVAL_2COL,
        r"\textbf{Deck Slab --- Loading and Geometry}",
        None,
        r"""\textnormal{Effective Span of Deck Slab, $l_{eff}$} & """ + _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + r""" mm (girder spacing, c/c) """ + _ROW_END + r"""
\hline
\textnormal{Deck Thickness, $t_s$} & """ + _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + r""" mm """ + _ROW_END + r"""
\hline
\textnormal{Clear Cover (IRC 112 Cl. 15.2)} & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm """ + _ROW_END + r"""
\hline
\textnormal{Concrete Grade (IRC 112 Cl. 6.4)} & """ + _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC) + r""" ($f_{ck}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r""" MPa, $f_{ctm}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + r""" MPa) """ + _ROW_END + r"""
\hline
\textnormal{Reinforcement Grade (IRC 112 Cl. 6.2)} & """ + _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL) + r""" ($f_y$ = """ + _dkf(KEY_DD_FY, nd=0) + r""" MPa) """ + _ROW_END + r"""
\hline
\textnormal{Dead Load per Unit Area, $w_{DL}$} & """ + _dkf(KEY_DD_WDL, nd=2) + r""" kN/m² (slab self-weight) """ + _ROW_END + r"""
\hline
\textnormal{IRC 6 Wheel Load (Class A / 70R)} & """ + _dkf(KEY_DD_WHEEL_LOAD, nd=1) + r""" kN """ + _ROW_END + r"""
\hline
\textnormal{Tyre Contact Width (IRC 6 Annex~A)} & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" mm (transverse) """ + _ROW_END + r"""
\hline
\textnormal{Impact Factor (IRC 6 Cl. 208.2)} & """ + _dkf(KEY_DD_IMPACT_FACTOR, nd=3) + " " + _ROW_END + r"""
\hline
\textnormal{Governing Live Load Case} & """ + _dkf(KEY_DD_VEHICLE) + " " + _ROW_END + r"""
\hline"""
    ) + r"""

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.CAPACITY_ALT4_5COL,
        r"\textbf{Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}",
        [["Location", "Parameter", "Formula / Reference", "Value", "Status"]],
        r"""\multirow{5}{*}{\makecell{At Midspan\\(Sagging)}} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/10$ & """ + _dkf(KEY_DD_M_DL, nd=2) + r""" kN-m/m & --- """ + _ROW_END + r"""
\cline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Effective width (IRC 112 B3.1) & """ + _dkf(KEY_DD_M_LL, nd=2) + r""" kN-m/m & --- """ + _ROW_END + r"""
\cline{2-5}
 & Total Design BM, $M_{u,sag}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL & """ + _dkf(KEY_DD_M_ULS_SAG, nd=2) + r""" kN-m/m & --- """ + _ROW_END + r"""
\cline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- """ + _ROW_END + r"""
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_BOT, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG)) + " " + _ROW_END + r"""
\hline
\multirow{3}{*}{\makecell{At Support\\(Hogging)}} & Total Design BM, $M_{u,hog}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL (at support) & """ + _dkf(KEY_DD_M_ULS_HOG, nd=2) + r""" kN-m/m & --- """ + _ROW_END + r"""
\cline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & --- """ + _ROW_END + r"""
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_TOP, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG)) + " " + _ROW_END + r"""
\hline"""
    ) + r"""
\noindent\textit{Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.SHEAR_STUDS_4COL,
        r"\textbf{Deck Slab --- Cantilever Overhang Flexure Check}",
        [["Parameter", "Formula", "Value", "Status"]],
        r"""Overhang Length, $l_{oh}$ & --- & """ + _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m") + r""" & --- """ + _ROW_END + r"""
\hline
Crash Barrier Load Moment & IRC 6 Cl. 206.4 & """ + _dkoh(KEY_DD_M_BARRIER, nd=2, unit=" kN-m/m") + r""" & --- """ + _ROW_END + r"""
\hline
Dead Load Moment & $w_{DL}\,l_{oh}^2/2$ + railing & """ + _dkoh(KEY_DD_M_DL_OH, nd=2, unit=" kN-m/m") + r""" & --- """ + _ROW_END + r"""
\hline
Live Load Moment (eccentric wheel) & Wheel load $\times$ arm & """ + _dkoh(KEY_DD_M_LL_OH, nd=2, unit=" kN-m/m") + r""" & --- """ + _ROW_END + r"""
\hline
Total Hogging Moment, $M_{u,oh}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" (LL + CB) & """ + _dkoh(KEY_DD_M_ULS_OH, nd=2, unit=" kN-m/m") + r""" & --- """ + _ROW_END + r"""
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 12.2 & """ + _dkoh(KEY_DD_MU_OH, nd=2, unit=" kN-m/m") + r""" & """ + (_dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else "---")) + " " + _ROW_END + r"""
\hline"""
    ) + r"""
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.SHEAR_STUDS_4COL,
        r"\textbf{Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}",
        [["Parameter", "Formula / Reference", "Value", "Status"]],
        r"""Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q\,(1+IF)\,P_w$ & """ + _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + r""" kN & --- """ + _ROW_END + r"""
\hline
Tyre Contact Area & $a \times b$ (IRC 6 Annex~A) & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" $\times$ """ + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + r""" mm & --- """ + _ROW_END + r"""
\hline
Loaded Area at mid-depth, $b_0$ & $c_1 \times c_2$ (incl.\ WC dispersion) & """ + _dkf(KEY_DD_PUNCH_C1, nd=0) + r""" $\times$ """ + _dkf(KEY_DD_PUNCH_C2, nd=0) + r""" mm & --- """ + _ROW_END + r"""
\hline
Control Perimeter, $u_1$ & $2(c_1+c_2) + 4\pi d$ & """ + _dkf(KEY_DD_PUNCH_U1, nd=0) + r""" mm & --- """ + _ROW_END + r"""
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed} / (u_1\,d)$ & """ + _dkf(KEY_DD_PUNCH_VED, nd=3) + r""" MPa & --- """ + _ROW_END + r"""
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Eq.\ 10.1 & """ + _dkf(KEY_DD_VRD_C_MPA, nd=3) + r""" MPa & --- """ + _ROW_END + r"""
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK))) + " " + _ROW_END + r"""
\hline"""
    ) + r"""
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

""" + _VSPACE_MD + r"""
\clearpage
""" + _make_table(
        _C5.DIAPHRAGM_ASSUMPTIONS_2COL,
        r"\textbf{Crack Width Check (Deck Slab)}",
        [["Parameter", "Value / Reference"]],
        r"""\textnormal{Min. Reinforcement for Crack Control, $A_{s,min}$} & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m [IRC 112 Cl. 16.5.1] """ + _ROW_END + r"""
\hline
\textnormal{Provided Reinforcement (bottom)} & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c (""" + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m) """ + _ROW_END + r"""
\hline
\textnormal{Max. Permissible Crack Width} & """ + _dkf(KEY_DD_WK_LIMIT, nd=2) + r""" mm """ + _ROW_END + r"""
\hline
\textnormal{Calculated Crack Width, $w_k$ (governing)} & """ + _dk_gov_wk_str + r""" mm """ + _ROW_END + r"""
\hline
\textnormal{Crack Width Check} & """ + _dks(_dk_crack_ok) + " " + _ROW_END + r"""
\hline"""
    ) + r"""

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.SHEAR_STUDS_4COL,
        r"\textbf{One-Way (Beam) Shear Check (Deck Slab)}",
        [["Parameter", "Formula / Reference", "Value", "Status"]],
        r"""Design Shear per unit width, $V_{Ed}$ & $\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$ & """ + _dkf(KEY_DD_SHEAR_VED, nd=2) + r""" kN/m & --- """ + _ROW_END + r"""
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- """ + _ROW_END + r"""
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & """ + (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- """ + _ROW_END + r"""
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b_w\,d) \leq 0.02$ & """ + (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- """ + _ROW_END + r"""
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & $v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2) & """ + _dkf(KEY_DD_SHEAR_VRDC, nd=2) + r""" kN/m & --- """ + _ROW_END + r"""
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK))) + " " + _ROW_END + r"""
\hline"""
    ) + r"""
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.DEFLECTION_4COL,
        r"\textbf{Reinforcement Detailing Summary (Deck Slab)}",
        [["Parameter", "Required / Limit", "Provided", "Status"]],
        r"""\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} """ + _ROW_END + r"""
\hline
Required Area, $A_{st,req}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT)) + " " + _ROW_END + r"""
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c & --- """ + _ROW_END + r"""
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN)) + " " + _ROW_END + r"""
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & """ + _dkf(KEY_DD_SPACING_MAX, nd=0) + r""" mm & """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm & """ + _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX)) + " " + _ROW_END + r"""
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} """ + _ROW_END + r"""
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & """ + _dkf(KEY_DD_AS_LONG, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN))) + " " + _ROW_END + r"""
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support / Cantilever Overhang)}} """ + _ROW_END + r"""
\hline
Required Area, $A_{st,top}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_TOP, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP)) + " " + _ROW_END + r"""
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} """ + _ROW_END + r"""
\hline
Clear Cover (IRC 112 Cl. 15.2) & $\geq$ """ + _dkf(KEY_DD_MIN_COVER, nd=0) + r""" mm (Table 14.2) & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm & """ + _dks(bool(deck_rpt.get(KEY_DD_COVER_OK))) + " " + _ROW_END + r"""
\hline"""
    ) + r"""
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_MEMBERS_6COL,
        r"\textbf{Cross Bracing --- Connection and Section Properties}",
        [["Panel", "Member", "Connection", "Section", r"$A_g$ (mm²)", r"$r_{min}$ (mm)"]],
        cb_forces_content,
    ) + r"""
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_CHECKS_6COL,
        r"\textbf{Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}",
        [["Panel", "Member", "Nature", r"Eff.\ Length $KL$ (mm)", r"$KL/r$", "Limit / Status"]],
        cb_slenderness_content,
    ) + r"""
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_FORCES_8COL,
        r"\textbf{Cross Bracing Design --- Capacity Summary}",
        [["Panel", "Member", "Section", "Governing LC", "Demand (kN)", "Capacity (kN)", "UR", "Status"]],
        cb_capacity_content,
    ) + r"""
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_MEMBERS_6COL,
        r"\textbf{End Diaphragm --- Connection and Section Properties}",
        [["Panel", "Member", "Connection", "Section", r"$A_g$ (mm²)", r"$r_{min}$ (mm)"]],
        cb_forces_content,
    ) + r"""
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_CHECKS_6COL,
        r"\textbf{End Diaphragm --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}",
        [["Panel", "Member", "Nature", r"Eff.\ Length $KL$ (mm)", r"$KL/r$", "Limit / Status"]],
        cb_slenderness_content,
    ) + r"""
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.BRACING_FORCES_8COL,
        r"\textbf{End Diaphragm Design --- Capacity Summary}",
        [["Panel", "Member", "Section", "Governing LC", "Demand (kN)", "Capacity (kN)", "UR", "Status"]],
        cb_capacity_content,
    ) + r"""
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{Overall Design Check Summary}
\label{sec:overall-summary}
% ===========================

""" + _VSPACE_MD + r"""
""" + _make_table(
        _C5.SUMMARY_4COL,
        r"\textbf{Overall Design Check Summary --- All Members}",
        [["Member / Check", "Governing Load Combo", "Demand", "Capacity", "UR"]],
        t522_content,
    ) + r"""
\noindent\textit{Note: UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.}

""" + (
        (
            "\n\n"
            + "\n\n".join(
                [
                    figure(
                        path=getattr(bridge, "ur_overall_chart"),
                        caption=r"\textbf{Overall Design Check Summary --- Utilization Ratios (UR = Demand / Capacity)} \textit{(Red dashed line indicates UR = 1.0 limit; hatching indicates failing checks)}",
                        width=r"\textwidth",
                    )
                ]
                if getattr(bridge, "ur_overall_chart", None)
                else []
            )
            + "\n\n"
            + "\n\n".join(
                [
                    figure(
                        path=getattr(bridge, "ur_girder_chart"),
                        caption=r"\textbf{Governing Utilization Ratio per Plate Girder} \textit{(Critical check displayed in parentheses; red dashed line indicates UR = 1.0 limit)}",
                        width=r"0.92\textwidth",
                    )
                ]
                if getattr(bridge, "ur_girder_chart", None)
                else []
            )
            + "\n\n"
        )
        if (getattr(bridge, "ur_overall_chart", None) or getattr(bridge, "ur_girder_chart", None))
        else "\n\n"
    )

