"""
Headless demo / regression harness for the OsdagBridge report generator.

It builds an ``input_dict`` / ``output_dict`` pair that mirrors a real design
run (40 m span, 9 girders, ...) and calls ``generate_report`` — no GUI, no
OpenSees needed.  Use it to check layout changes in seconds:

    cd OsdagBridge/src
    python ../tests/report_demo/generate_demo_report.py  [output_dir]  [--fail]

``--fail`` perturbs a few results so UR > 1.0 bars/FAIL cells are visible.
Requires: pdflatex on PATH (or osdag_latex_env), matplotlib.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "src")))

from osdagbridge.core.utils import common as K                       # noqa: E402
from osdagbridge.core.reports import (                               # noqa: E402
    ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report)

N = 9
SPAN = 40.0


def build_inputs():
    d = {
        K.KEY_STRUCTURE_TYPE: "Highway Bridge", K.KEY_SPAN: "40", K.KEY_CARRIAGEWAY_WIDTH: "20.2",
        K.KEY_INCLUDE_MEDIAN: "No", K.KEY_FOOTPATH: "None", K.KEY_SKEW_ANGLE: "",
        K.KEY_GIRDER: "E 350A", K.KEY_CROSS_BRACING: "E 350A", K.KEY_END_DIAPHRAGM: "E 350A",
        K.KEY_DECK_CONCRETE_GRADE_BASIC: "M40", K.KEY_DESIGN_MODE: "Optimized",
        K.KEY_TS_OVERALL_WIDTH: 21.099999999999998, K.KEY_TS_NO_OF_GIRDERS: str(N),
        K.KEY_TS_GIRDER_SPACING: "2.3444", K.KEY_TS_DECK_OVERHANG: "1.1722",
        K.KEY_TS_DECK_THICKNESS: "250.0", K.KEY_TS_FOOTPATH_WIDTH: "0.0", K.KEY_WC_LD_LANE_TABLE_COUNT: "5",
        K.KEY_CB_TYPE: "IRC 5 - RCC Crash Barrier", K.KEY_CB_LOAD: "7.56",
        K.KEY_RL_TYPE: "IRC 5 - RCC Railing", K.KEY_RL_LOAD_VALUE: "6.806",
        K.KEY_WC_MATERIAL: "Concrete", K.KEY_WC_THICKNESS: "50.0",
        "latitude": "18.5204", "longitude": "73.8567", "seismic_zone": "III", "wind_speed": "39",
        "shade_temp_max": "43.3", "shade_temp_min": "1.7",
        K.KEY_DO_GAMMA_M0: "1.1", K.KEY_DO_GAMMA_M1: "1.25", K.KEY_DO_GAMMA_C_BASIC: "1.5",
        K.KEY_DO_GAMMA_S: "1.15", K.KEY_DO_GAMMA_V: "1.25", K.KEY_DO_GAMMA_FLT: "1.0", K.KEY_DO_GAMMA_MF: "1.35",
        # loads
        K.KEY_MATERIAL_GIRDER_DENSITY: "76.4", K.KEY_MATERIAL_DECK_DENSITY: "24.5", K.KEY_PL_SELF_WEIGHT_FACTOR: "1.0",
        K.KEY_LL_IRC_CLASS_A: True, K.KEY_LL_IRC_70R_WHEELED: True, K.KEY_LL_IRC_70R_TRACKED: True,
        K.KEY_LL_IRC_AA_WHEELED: True, K.KEY_LL_IRC_AA_TRACKED: True, K.KEY_LL_IRC_CLASS_SV: True,
        K.KEY_LL_IRC_70R_BOGIE: True, K.KEY_LL_IRC_CLASS_FATIGUE: True, K.KEY_BL_IRC_CLASS_SV: False,
        K.KEY_LL_ECCENTRICITY: "1.2", K.KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
        K.KEY_WL_TERRAIN_TYPE: "Plain Terrain", K.KEY_WL_AVG_EXPOSED_HEIGHT: "10",
        K.KEY_SL_ZONE_FACTOR: "0.16", K.KEY_SL_IMPORTANCE_FACTOR: "1.0",
        K.KEY_SL_SOIL_TYPE: "Type I \u2013 Rocky or Hard", K.KEY_SL_SPECTRAL_COEFF: "2.8",
        K.KEY_SL_HORIZONTAL_COEFF: "0.224", K.KEY_SL_VERTICAL_COEFF: "0.1493",
        # shear connectors etc.
        K.KEY_DS_TOP_CLEAR_COVER: "50", K.KEY_DS_BOTTOM_CLEAR_COVER: "50", K.KEY_DS_REINF_MATERIAL: "Fe 500",
        K.KEY_MATERIAL_DECK_FCK: "40.0", K.KEY_MATERIAL_DECK_FCTM: "3.0", K.KEY_DS_STUD_DIAMETER: "20.0",
        "typical_section.crash_barrier.area": 380000,
    }
    for i in range(1, N + 1):
        g = f".G{i}.M1"
        d[f"{K.KEY_MP_GD_SELECT_GIRDER}.G{i}"] = f"G{i}"
        d[f"{K.KEY_MP_GD_MEMBER_ID}.G{i}.M1"] = f"G{i}M1"
        # girder dims are in METRES at report time (designer converts mm -> m)
        d[K.KEY_MP_GIRDER_DEPTH + g] = 2.23; d[K.KEY_MP_GIRDER_WEB_THICKNESS + g] = 0.012
        d[K.KEY_MP_GIRDER_TOP_FLANGE_WIDTH + g] = 0.67; d[K.KEY_MP_GIRDER_TOP_FLANGE_THICKNESS + g] = 0.028
        d[K.KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH + g] = 0.67; d[K.KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS + g] = 0.028
        d[K.KEY_MP_GIRDER_TYPE + g] = "Welded Girder"; d[K.KEY_MP_GIRDER_SYMMETRY + g] = "Symmetric"
        d[K.KEY_MP_GIRDER_TORSIONAL_RESTRAINT + g] = "Fully Restrained"
        d[K.KEY_MP_GIRDER_WARPING_RESTRAINT + g] = "Both Flanges Restrained"
        d[K.KEY_MP_GIRDER_WEB_TYPE + g] = "Thin Web with ITS"
        d[K.KEY_MP_STIFFENER_INTERMEDIATE + g] = "Yes"
        d[K.KEY_MP_STIFFENER_INTERMEDIATE_SPACING + g] = "3260"
        d[K.KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS + g] = "10"
        d[K.KEY_MP_STIFFENER_LONGITUDINAL + g] = "No"
        d[K.KEY_MP_STIFFENER_NO_BEARING_STIFFENERS + g] = "4"
        d[K.KEY_MP_STIFFENER_SPACING + g] = "100"; d[K.KEY_MP_STIFFENER_BEARING_THICKNESS + g] = "10"
    for i in range(1, N):
        p = f".G{i}G{i+1}"
        d[f"{K.KEY_MP_CB_SELECT_GIRDERS}{p}.B{i}M1"] = f"G{i} to G{i+1}"
        d[f"{K.KEY_MP_CB_MEMBER_ID}{p}.B{i}M1"] = f"B{i}M1 to B{i}M1"
        d[f"{K.KEY_MP_CB_TYPE}{p}.B{i}M1"] = "X-Bracing"
        d[f"{K.KEY_MP_CB_BRACING_SECTION_DESIGNATION}{p}.B{i}M1"] = "IS 100 x 100 x 10"
        d[f"{K.KEY_MP_CB_SPACING}{p}.B{i}M1"] = "20.0"
        d[f"{K.KEY_MP_ED_SELECT_GIRDERS}{p}.E{i}M1"] = f"G{i} to G{i+1}"
        d[f"{K.KEY_MP_ED_MEMBER_ID}{p}.E{i}M1"] = f"E{i}M1 to E{i}M2"
        d[f"{K.KEY_MP_ED_TYPE}{p}.E{i}M1"] = "Cross Bracing"
        d[f"{K.KEY_MP_ED_BRACING_SECTION_DESIGNATION}{p}.E{i}M1"] = "IS 100 x 100 x 10"
    return d


def _member_results(ur_d, ur_c, sec_d="40 x 40 x 3", sec_c="40 x 40 x 3"):
    def r(sec, cap, ur, slend):
        return {"section_size.designation": sec, "Member.tension_capacity": cap, "Member.efficiency": ur,
                "Member.Slenderness": slend}
    return {"diagonal": {"compression": r(sec_d, 45.0, ur_d, 159.3), "tension": r(sec_d, 45.0, ur_d * 0.8, 159.3)},
            "chord": {"compression": r(sec_c, 45.0, ur_c, 123.9), "tension": r(sec_c, 45.0, ur_c * 0.7, 123.9)}}


def build_outputs(fail=False):
    o = {}
    sd = {
        K.KEY_SD_SECTION_DESIGNATION: "2230 x 670 x 28 x 670 x 28", K.KEY_SD_TOTAL_DEPTH: "2230.0",
        K.KEY_SD_TOP_FLANGE_WIDTH: "670.0", K.KEY_SD_BOTTOM_FLANGE_WIDTH: "670.0",
        K.KEY_SD_TOP_FLANGE_THICKNESS: "28.0", K.KEY_SD_BOTTOM_FLANGE_THICKNESS: "28.0", K.KEY_SD_WEB_THICKNESS: "12.0",
        K.KEY_SD_SECTION_PROP_AREA: "636.08", K.KEY_SD_SECTION_PROP_IZ: "5575915.69",
        K.KEY_SD_SECTION_PROP_ZZ: "50008.21", K.KEY_SD_SECTION_PROP_ZUZ: "55488.35",
        K.KEY_SD_EFFECTIVE_SLAB_WIDTH: "2344.4", K.KEY_SD_COMPOSITE_IZ: "11008347.91", K.KEY_SD_PNA_DEPTH: "277.8",
        K.KEY_SD_FLANGE_SLENDERNESS: "11.75", K.KEY_SD_FLANGE_CLASS_LIMIT: "11.49", K.KEY_SD_CLASS_FLANGE: "Slender",
        K.KEY_SD_WEB_SLENDERNESS: "181.17", K.KEY_SD_WEB_CLASS_LIMIT: "106.49", K.KEY_SD_CLASS_WEB: "Slender",
        K.KEY_SD_SECTION_CLASS: "Slender", K.KEY_SD_MU_APPLIED: "5008.28", K.KEY_SD_MD_CAPACITY: "23657.99",
        K.KEY_UTIL_FLEXURE: 21.0, K.KEY_UTIL_SHEAR: 63.0, K.KEY_UTIL_INTERACTION: 21.4,
        K.KEY_SD_SHEAR_VU: "585.07", K.KEY_SD_SHEAR_AV: "26088.0", K.KEY_SD_PANEL_CD: "1.5", K.KEY_SD_SHEAR_KV: "7.129",
        K.KEY_SD_SHEAR_LAMBDA_W: "2.269", K.KEY_SD_SHEAR_TAU_B: "39.26", K.KEY_SD_SHEAR_VCR: "931.15",
        K.KEY_SD_HIGH_SHEAR: "No", K.KEY_SD_MDV: "23657.99",
        K.KEY_SD_LTB_MCR: "339350.44", K.KEY_SD_LTB_LAMBDA: "0.227", K.KEY_SD_LTB_CHI: "1.0", K.KEY_SD_LTB_MB: "17655.38",
        K.KEY_SD_STIFF_METHOD: "post critical", K.KEY_SD_STIFF_INT_THICK: "27.8", K.KEY_SD_STIFF_END_THICK: "1.8",
        K.KEY_SD_STIFF_END_COUNT: "4", K.KEY_SD_STIFF_LONG: "None",
        K.KEY_SD_SHEAR_DIAMETER: "20.0", K.KEY_SD_SHEAR_HEIGHT: "100.0", K.KEY_SD_SHEAR_YIELD_STRENGTH: "385.0",
        K.KEY_SD_SHEAR_ULTIMATE_STRENGTH: "495.0", K.KEY_SD_SHEAR_STUDS_PER_SECTION: "2",
        K.KEY_SD_SC_Qu_kN: "95.36", K.KEY_SD_SC_Qr_kN: "25.0",
    }
    o.update(sd)
    for i in range(1, N + 1):
        o[f"{K.KEY_SD_DEFL_LIVE}.G{i}"] = 19.873 + 0.05 * min(i - 1, N - i)
        o[f"{K.KEY_SD_DEFL_TOTAL}.G{i}"] = 68.112 + 0.2 * min(i - 1, N - i)
    # per-girder DCR engine results
    checks = [("Moment", 1, 0.21), ("Shear", 2, 0.78), ("LTB (constr.)", 5, 0.41), ("Deflection", 14, 0.52),
              ("Stress", 11, 0.28), ("Fatigue Normal Stress", 8, 1.73), ("Int.Stiff: Leg H limit", 20, 1.92)]
    per_girder = {}
    for i in range(1, N + 1):
        per_girder[f"G{i}"] = {"checks": [
            {"name": n, "check_id": cid, "id": cid, "dcr": (u + (0.4 if fail and n == "Moment" else 0)),
             "status": "FAIL" if u > 1 else "PASS", "demand": 100 * u, "capacity": 100.0,
             "demand_unit": "kN", "capacity_unit": "kN"} for n, cid, u in checks],
            "per_lc": {"SW": {"checks": [], "max_dcr": 0.4}}}
    o["design_results"] = {"per_girder": per_girder, K.KEY_SD_ULS_PER_GIRDER: {"fatigue": {
        f"G{i}": {"demand": 154.4, "capacity": 89.91, "ur": 1.72, "status": "FAIL"} for i in range(1, N + 1)}}}
    o["deck_design_results"] = {"ur_bot_uls": 0.89, "ur_top_uls": 0.88, "ur_oh_uls": 0.92, "ur_bot_shear": 0.80,
                                "ur_bot_punch": 0.34, "ur_bot_crack": 0.72, "ur_bot_sls_c": 0.55, "ur_bot_sls_s": 0.61,
                                "rebar_bottom_area": 685, "rebar_top_area": 514}
    o["deck_report_values"] = {
        K.KEY_DD_SPAN: 2.344, K.KEY_DD_FY: 500, K.KEY_DD_WDL: 6.13, K.KEY_DD_WHEEL_LOAD: 83.4, K.KEY_DD_TYRE_WIDTH: 0.3,
        K.KEY_DD_TYRE_LENGTH: 150, K.KEY_DD_IMPACT_FACTOR: 1.1, K.KEY_DD_VEHICLE: "Class70R(W)",
        K.KEY_DD_M_DL: 3.37, K.KEY_DD_M_LL: 27.12, K.KEY_DD_GAMMA_DL: 1.35, K.KEY_DD_GAMMA_LL: 1.5,
        K.KEY_DD_M_ULS_SAG: 49.3, K.KEY_DD_D_BOT: 194.0, K.KEY_DD_MU_BOT: 55.25, K.KEY_DD_M_ULS_HOG: 36.98,
        K.KEY_DD_AS_REQ_TOP: 488, K.KEY_DD_MU_TOP: 41.92, K.KEY_DD_HAS_OVERHANG: True, K.KEY_DD_M_BARRIER: 7.5,
        K.KEY_DD_M_DL_OH: 5.94, K.KEY_DD_M_LL_OH: 52.4, K.KEY_DD_M_ULS_OH: 105.73, K.KEY_DD_MU_OH: 114.71,
        K.KEY_DD_PUNCH_VED_KN: 137.6, K.KEY_DD_PUNCH_C1: 400, K.KEY_DD_PUNCH_C2: 250, K.KEY_DD_PUNCH_U1: 3738,
        K.KEY_DD_PUNCH_VED: 0.19, K.KEY_DD_VRD_C_MPA: 0.555, K.KEY_DD_PUNCH_OK: True,
        K.KEY_DD_AS_MIN: 303, K.KEY_DD_DIA_BOT: 12, K.KEY_DD_SPC_BOT: 165, K.KEY_DD_AS_BOT: 685, K.KEY_DD_WK_LIMIT: 0.3,
        K.KEY_DD_WK_BOT: 0.216, K.KEY_DD_WK_TOP: 0.2, K.KEY_DD_WK_OH: 0.1, K.KEY_DD_SHEAR_VED: 86.06,
        K.KEY_DD_SHEAR_VRDC: 107.58, K.KEY_DD_SHEAR_OK: True, K.KEY_DD_AS_REQ_BOT: 642, K.KEY_DD_SPACING_MAX: 300,
        K.KEY_DD_AS_LONG: 377, K.KEY_DD_AS_TOP: 514, K.KEY_DD_MIN_COVER: 50, K.KEY_DD_COVER_OK: True,
    }
    # cross bracing + end diaphragm (same structure)
    pairs, forces, designs = {}, {}, {}
    for i in range(1, N):
        pr = f"G{i}-G{i+1}"
        forces[pr] = {"diag_tension_kN": 12.0 + i, "diag_compression_kN": 12.3 + i, "chord_tension_kN": 9.0 + i,
                      "chord_compression_kN": 9.5 + i, "diag_compression_gov_lc": "1.5 EQ (a)",
                      "chord_compression_gov_lc": "1.5 EQ (a)", "diag_tension_gov_lc": "1.5 EQ (a)",
                      "chord_tension_gov_lc": "1.5 EQ (a)"}
        designs[pr] = _member_results(0.78 if i == 1 else 0.2 + 0.03 * i, 0.81 if i == 1 else 0.2 + 0.02 * i)
        for grp in ("bracing", "top_chord", "bottom_chord"):
            for pre in ("cb", "ed"):
                gname = "end_diaphragm" if (pre == "ed" and grp == "bracing") else grp
                o[f"transverse_member_design.{pre}.section_properties.{gname}.G{i}G{i+1}.A"] = 2.37
                o[f"transverse_member_design.{pre}.section_properties.{gname}.G{i}G{i+1}.rv"] = 0.8
    o["crossbracing_forces_dict"] = {"pairs": forces, "brace_type": "X",
                                     "geometry": {"diagonal_length_m": 3.015, "horiz_proj_m": 2.344, "alpha_deg": 50.0,
                                                  "cb_spacing_m": 5.0}}
    o["crossbracing_design_results"] = designs
    o["end_diaphragm_forces_dict"] = {"pairs": {k: dict(v) for k, v in forces.items()}}
    o["end_diaphragm_design_results"] = {k: _member_results(0.55 + 0.01 * j, 0.4) for j, k in enumerate(designs)}
    o["analysis_summary"] = {
        "load_cases": {f"LC {j}: 1.0DL + {j/10:.1f}LL": {"max_bm": 3000 + 40 * j, "bm_girder": "G5", "bm_location": 14.8,
                                                         "max_sf": 500 + 5 * j, "sf_girder": "G1", "sf_location": 0.0}
                       for j in range(1, 46)},
        "reactions": {f"LC {j}: 1.0DL + {j/10:.1f}LL": {"left_kN": -3000 - 20 * j, "right_kN": 2800 + 10 * j} for j in range(1, 46)}}
    o["design_log"] = []
    return o


def main(out_dir, fail=False):
    inputs, outputs = build_inputs(), build_outputs(fail)
    meta = ReportMetadata(project_name="OsdagBridge", project_location="Pune, Maharashtra", designer="", client="",
                          company="", job_number="", report_date="2026-11-23", reviewer="")
    opts = ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"], include_figures=True,
                         include_toc=True, include_pdf=True)
    req = ReportRequest(metadata=meta, options=opts, output_dir=out_dir, file_stem="Report_After")
    payload = build_report_payload(req, inputs, outputs)
    res = generate_report(payload, req)
    print("PDF:", res.pdf_path, "\nTEX:", res.tex_path)
    return res


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(os.path.abspath(args[0]) if args else os.path.join(HERE, "out"), "--fail" in sys.argv)
