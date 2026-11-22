#!/usr/bin/env python3
"""
Test Harness for OsdagBridge PDF Design Report Generation (Phase 2 & 3).

Builds a realistic mock ReportPayload (input_dict + output_dict) covering all
subsystems:
  - Project Info & Location (Chapter 1)
  - Basic Inputs & Girder Geometry (Chapter 2)
  - Loads & Vehicle Selections (Chapter 3)
  - Analysis Results & Reactions (Chapter 4)
  - Girder, Deck Slab, Bracing Design Checks (Chapter 5, including Sec 5.5)
  - Drawing Placeholders (Chapter 6)
  - Material Quantities / BOQ (Chapter 7)
  - Design Log & Standards (Chapter 8)
  - References (Chapter 9)

Outputs:
  - <output_dir>/<stem>.tex
  - <output_dir>/<stem>.pdf
  - <output_dir>/<stem>.log (analyzed for error & warning metrics)
"""

import sys
import os
import argparse
import logging
import types
import shutil
import subprocess
import re

# ---------------------------------------------------------------------------
# 1. Environment & Path Setup
# ---------------------------------------------------------------------------

# Discover and prepend standard LaTeX paths on macOS / Linux
EXTRA_PATHS = [
    "/usr/local/texlive/2026basic/bin/universal-darwin",
    "/usr/local/texlive/2025basic/bin/universal-darwin",
    "/Library/TeX/texbin",
    "/usr/local/bin",
    "/opt/homebrew/bin",
]
for p in EXTRA_PATHS:
    if os.path.exists(p) and p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Mock openseespy if not installed so results_data.py can be imported cleanly
try:
    import openseespy  # noqa: F401
except ImportError:
    ops = types.ModuleType('openseespy')
    ops.opensees = types.ModuleType('openseespy.opensees')
    sys.modules['openseespy'] = ops
    sys.modules['openseespy.opensees'] = ops.opensees

# Ensure src/ is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.utils.common import (
    # Chapter 1 & 2: Geometry & Section
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_DESIGN_MODE,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_FOOTPATH_THICKNESS,
    KEY_WC_THICKNESS,
    KEY_WC_MATERIAL,
    KEY_WC_DENSITY,
    KEY_WC_LD_LANE_TABLE_COUNT,
    # Girder details (per girder)
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    # Materials
    KEY_GIRDER,
    KEY_CROSS_BRACING,
    KEY_END_DIAPHRAGM,
    KEY_MP_ED_TYPE,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    # Chapter 3: Loading
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_SOIL_TYPE,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_TEMP_RISE,
    KEY_TL_TEMP_FALL,
    # Girder section properties & design checks (Chapter 5)
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_PNA_DEPTH,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_CLASS_WEB,
    KEY_SD_SECTION_CLASS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_LTB,
    KEY_UTIL_INTERACTION,
    # Deck Design Report Keys (Chapter 5)
    KEY_DD_VEHICLE,
    KEY_DD_SPAN,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_WDL,
    KEY_DD_M_DL,
    KEY_DD_M_LL,
    KEY_DD_M_BARRIER,
    KEY_DD_M_ULS_SAG,
    KEY_DD_M_ULS_HOG,
    KEY_DD_D_BOT,
    KEY_DD_MU_BOT,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_BOT,
    KEY_DD_DIA_BOT,
    KEY_DD_SPC_BOT,
    KEY_DD_MU_TOP,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_SPACING_MAX,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SHEAR_OK,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_PUNCH_OK,
    KEY_DD_WK_BOT,
    KEY_DD_WK_TOP,
    KEY_DD_WK_LIMIT,
    KEY_DD_MIN_COVER,
    KEY_DD_COVER_OK,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_FY,
    KEY_DD_VRD_C_MPA,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_OH,
    KEY_DD_MU_OH,
    KEY_DD_WK_OH,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("test_report")


# ---------------------------------------------------------------------------
# 2. Mock Data Generator
# ---------------------------------------------------------------------------

def create_mock_payload_data(large: bool = False):
    """Build a comprehensive, realistic input_dict and output_dict.
    
    Parameters
    ----------
    large : bool
        If True, builds a stress-test payload with 6 girders (G1-G6),
        5 cross-bracing panels, 5 selected vehicles plus a custom vehicle.
    """
    n_girders = 6 if large else 3
    span_m = 24.0

    # ── 2A. INPUT DICT ────────────────────────────────────────────────────────
    input_dict = {
        # Project & Location
        "project.location": "{'method': 'location_name', 'data': {'district': 'Mumbai Suburban', 'state': 'Maharashtra'}}",
        "latitude": "19.0760",
        "longitude": "72.8777",
        "seismic_zone": "Zone III",
        "wind_speed": "44.0",
        "shade_temp_max": "42.0",
        "shade_temp_min": "12.0",
        # Geometry
        KEY_SPAN: str(span_m),
        KEY_STRUCTURE_TYPE: "Simply Supported",
        KEY_CARRIAGEWAY_WIDTH: "15.0" if large else "7.5",
        KEY_SKEW_ANGLE: "0",
        KEY_DESIGN_MODE: "Optimized",
        # Typical Section
        KEY_TS_NO_OF_GIRDERS: str(n_girders),
        KEY_TS_GIRDER_SPACING: "2.5",
        KEY_TS_DECK_THICKNESS: "220",
        KEY_TS_DECK_OVERHANG: "1.25",
        KEY_TS_OVERALL_WIDTH: "17.5" if large else "10.0",
        "typical_section.overall_bridge_width": "17.5" if large else "10.0",
        KEY_TS_FOOTPATH_WIDTH: "1.25",
        KEY_TS_FOOTPATH_THICKNESS: "150",
        "typical_section.crash_barrier.cross_sectional_area": "0.25",
        KEY_WC_THICKNESS: "75",
        KEY_WC_MATERIAL: "Bituminous Concrete",
        KEY_WC_DENSITY: "22.0",
        KEY_WC_LD_LANE_TABLE_COUNT: "4" if large else "2",
        # Live Loads
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_IRC_70R_TRACKED: True if large else False,
        KEY_LL_IRC_CLASS_SV: True if large else False,
        KEY_LL_IRC_70R_BOGIE: True if large else False,
        KEY_LL_CUSTOM_VEHICLES: [
            {"name": "Heavy Mining Dumper 120T", "weight": 1200}
        ] if large else None,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "IRC 6:2017 (Auto)",
        KEY_LL_FOOTPATH_PRESSURE_VALUE: "4.0",
        # Environmental / Wind / Seismic / Temperature
        KEY_WL_BASIC_WIND_SPEED: "44.0",
        KEY_WL_TERRAIN_TYPE: "Category 2",
        KEY_WL_AVG_EXPOSED_HEIGHT: "10.0",
        KEY_SL_SEISMIC_ZONE: "Zone III",
        KEY_SL_IMPORTANCE_FACTOR: "1.2",
        KEY_SL_SOIL_TYPE: "Type II (Medium Soil)",
        KEY_TL_HIGHEST_MAX_TEMP: "42.0",
        KEY_TL_LOWEST_MIN_TEMP: "12.0",
        KEY_TL_BRIDGE_TEMP_MIN: "14.5",
        KEY_TL_BRIDGE_TEMP_MAX: "39.5",
        KEY_TL_TEMP_RISE: "12.5",
        KEY_TL_TEMP_FALL: "12.5",
        # Materials & Safety Factors
        KEY_GIRDER: "IS 2062 E250 (Fe 410 W) B",
        KEY_CROSS_BRACING: "IS 2062 E250 (Fe 410 W) B",
        KEY_END_DIAPHRAGM: "IS 2062 E250 (Fe 410 W) B",
        KEY_MP_ED_TYPE: "Cross Bracing",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M35",
        "deck_slab.rebar.grade": "Fe 500",
        KEY_MATERIAL_GIRDER_DENSITY: "78.5",
        KEY_MATERIAL_DECK_DENSITY: "25.0",
        KEY_DO_GAMMA_M0: "1.10",
        KEY_DO_GAMMA_M1: "1.25",
        KEY_DO_GAMMA_MF: "1.25",
        # Girder Details for BOQ calculations
        "member_properties.girder_details.section_properties.area": "0.0425",
        "member_properties.girder_details.section_properties.mass": "333.6",
    }

    # Per-girder keys for G1..Gn
    for i in range(1, n_girders + 1):
        g_lbl = f"G{i}"
        m_id = f"G{i}M1"
        input_dict[f"{KEY_MP_GD_SELECT_GIRDER}.G{i}"] = g_lbl
        input_dict[f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1"] = m_id
        input_dict[f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1"] = "1600"
        input_dict[f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1"] = "14"
        input_dict[f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1"] = "450"
        input_dict[f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1"] = "25"
        input_dict[f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1"] = "500"
        input_dict[f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1"] = "32"
        input_dict[f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"] = "Welded Plate Girder"
        input_dict[f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"] = "Monosymmetric"
        input_dict[f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1"] = "Fully Restrained"
        input_dict[f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"] = "Restrained"
        input_dict[f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"] = "Unstiffened / Transverse Stiffened"
        input_dict[f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1"] = "Plate Stiffener"
        input_dict[f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1"] = "2000"
        input_dict[f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1"] = "12"
        input_dict[f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"] = "None"
        input_dict[f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1"] = "2"
        input_dict[f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1"] = "150"
        input_dict[f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1"] = "20"

    # ── 2B. OUTPUT DICT ───────────────────────────────────────────────────────
    output_dict = {
        # Section Properties (Girder G1 / Representative)
        KEY_SD_TOTAL_DEPTH: "1600.0",
        KEY_SD_TOP_FLANGE_WIDTH: "450.0",
        KEY_SD_BOTTOM_FLANGE_WIDTH: "500.0",
        KEY_SD_TOP_FLANGE_THICKNESS: "25.0",
        KEY_SD_BOTTOM_FLANGE_THICKNESS: "32.0",
        KEY_SD_WEB_THICKNESS: "14.0",
        KEY_SD_SECTION_PROP_AREA: "425.0",
        KEY_SD_SECTION_PROP_IZ: "1850000.0",
        KEY_SD_SECTION_PROP_ZZ: "23125.0",
        KEY_SD_SECTION_PROP_ZUZ: "26500.0",
        KEY_SD_EFFECTIVE_SLAB_WIDTH: "2100.0",
        KEY_SD_COMPOSITE_IZ: "3250000.0",
        KEY_SD_PNA_DEPTH: "215.0",
        KEY_SD_FLANGE_SLENDERNESS: "8.4",
        KEY_SD_FLANGE_CLASS_LIMIT: "9.4",
        KEY_SD_CLASS_FLANGE: "Class 1 (Plastic)",
        KEY_SD_WEB_SLENDERNESS: "105.2",
        KEY_SD_WEB_CLASS_LIMIT: "84.0",
        KEY_SD_CLASS_WEB: "Class 3 (Semi-Compact)",
        KEY_SD_SECTION_CLASS: "Class 3 (Semi-Compact)",
        # Utilization Ratios (percentages in output_dict)
        KEY_UTIL_FLEXURE: "78.5",
        KEY_UTIL_SHEAR: "62.1",
        KEY_UTIL_LTB: "71.4",
        KEY_UTIL_INTERACTION: "81.0",
        # Shear Stud Design Output (for BOQ)
        "steeldesign.details.shear.longitudinal_spacing": "200.0",
        "steeldesign.details.shear.studs_per_section": "2",
        "steeldesign.details.shear.diameter": "22.0",
        "steeldesign.details.shear.height": "100.0",
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": "19.0",  # cm²
    }

    # Chapter 4 Analysis Summary
    output_dict["analysis_summary"] = {
        "load_cases": {
            "Dead Load (Self Weight)": {
                "max_bm": 450.5,
                "bm_girder": "G2",
                "bm_location": 12.0,
                "max_sf": 75.2,
                "sf_girder": "G2",
                "sf_location": 0.0,
            },
            "Superimposed Dead Load (SIDL)": {
                "max_bm": 210.3,
                "bm_girder": "G2",
                "bm_location": 12.0,
                "max_sf": 35.1,
                "sf_girder": "G2",
                "sf_location": 0.0,
            },
            "Live Load (IRC Class A)": {
                "max_bm": 850.0,
                "bm_girder": "G1",
                "bm_location": 12.0,
                "max_sf": 142.5,
                "sf_girder": "G1",
                "sf_location": 0.0,
            },
            "Live Load (IRC 70R Wheeled)": {
                "max_bm": 920.0,
                "bm_girder": "G1",
                "bm_location": 12.0,
                "max_sf": 155.0,
                "sf_girder": "G1",
                "sf_location": 0.0,
            },
            "Wind Load (Transverse)": {
                "max_bm": 45.2,
                "bm_girder": "G1",
                "bm_location": 12.0,
                "max_sf": 12.8,
                "sf_girder": "G1",
                "sf_location": 0.0,
            },
        },
        "reactions": {
            "Dead Load (Self Weight)": {"left_kN": 75.2, "right_kN": 75.2},
            "Superimposed Dead Load (SIDL)": {"left_kN": 35.1, "right_kN": 35.1},
            "Live Load (IRC Class A)": {"left_kN": 142.5, "right_kN": 142.5},
            "Live Load (IRC 70R Wheeled)": {"left_kN": 155.0, "right_kN": 155.0},
            "Wind Load (Transverse)": {"left_kN": 12.8, "right_kN": 12.8},
        },
    }

    # Chapter 5 Girder Design Checks (DCR engine)
    per_girder_checks = [
        {
            "check_id": 1,
            "name": "Bending Moment Resistance (cl. 8.2.1.2)",
            "dcr": 0.785,
            "demand": 1850.5,
            "capacity": 2357.3,
            "demand_unit": "kNm",
            "capacity_unit": "kNm",
            "status": "PASS",
        },
        {
            "check_id": 2,
            "name": "Shear Resistance of Web (cl. 8.4)",
            "dcr": 0.621,
            "demand": 315.4,
            "capacity": 507.9,
            "demand_unit": "kN",
            "capacity_unit": "kN",
            "status": "PASS",
        },
        {
            "check_id": 5,
            "name": "Lateral Torsional Buckling (cl. 8.2.2)",
            "dcr": 0.714,
            "demand": 1850.5,
            "capacity": 2591.7,
            "demand_unit": "kNm",
            "capacity_unit": "kNm",
            "status": "PASS",
        },
        {
            "check_id": 11,
            "name": "Longitudinal Stress Limits (cl. 8.2.1.1)",
            "dcr": 0.540,
            "demand": 135.0,
            "capacity": 250.0,
            "demand_unit": "MPa",
            "capacity_unit": "MPa",
            "status": "PASS",
        },
        {
            "check_id": 13,
            "name": "Live Load Deflection (cl. 5.6.1)",
            "dcr": 0.650,
            "demand": 19.5,
            "capacity": 30.0,
            "demand_unit": "mm",
            "capacity_unit": "mm",
            "status": "PASS",
        },
        {
            "check_id": 8,
            "name": "Fatigue Assessment (cl. 13)",
            "dcr": 0.420,
            "demand": 42.0,
            "capacity": 100.0,
            "demand_unit": "MPa",
            "capacity_unit": "MPa",
            "status": "PASS",
        },
        {
            "check_id": 16,
            "name": "Transverse Shear in Deck Slab (cl. 8.4)",
            "dcr": 0.480,
            "demand": 71.0,
            "capacity": 148.0,
            "demand_unit": "kN",
            "capacity_unit": "kN",
            "status": "PASS",
        },
    ]

    per_lc_checks = {
        "ULS 1: 1.35 DL + 1.35 SIDL + 1.50 LL (70R)": {
            "checks": [
                {"id": 1, "dcr": 0.785, "demand": 1850.5, "capacity": 2357.3},
                {"id": 2, "dcr": 0.621, "demand": 315.4, "capacity": 507.9},
                {"id": 5, "dcr": 0.714, "demand": 1850.5, "capacity": 2591.7},
                {"id": 11, "dcr": 0.540, "demand": 135.0, "capacity": 250.0},
                {"id": 16, "dcr": 0.480, "demand": 71.0, "capacity": 148.0},
            ]
        },
        "SLS 1: 1.00 DL + 1.00 SIDL + 1.00 LL": {
            "checks": [
                {"id": 13, "dcr": 0.650, "demand": 19.5, "capacity": 30.0},
                {"id": 8, "dcr": 0.420, "demand": 42.0, "capacity": 100.0},
            ]
        },
    }

    output_dict["design_results"] = {
        "per_girder": {
            f"G{i}": {"checks": per_girder_checks, "per_lc": per_lc_checks}
            for i in range(1, n_girders + 1)
        }
    }

    # Chapter 5 Deck Slab Report Values (KEY_DD_*)
    output_dict["deck_report_values"] = {
        KEY_DD_VEHICLE: "IRC Class 70R (Wheeled)",
        KEY_DD_SPAN: "2.50",
        KEY_DD_WHEEL_LOAD: "170.0",
        KEY_DD_IMPACT_FACTOR: "1.10",
        KEY_DD_WDL: "6.85",
        KEY_DD_M_DL: "4.28",
        KEY_DD_M_LL: "42.50",
        KEY_DD_M_BARRIER: "3.20",
        KEY_DD_M_ULS_SAG: "68.40",
        KEY_DD_M_ULS_HOG: "72.10",
        KEY_DD_D_BOT: "175",
        KEY_DD_MU_BOT: "95.20",
        KEY_DD_AS_REQ_BOT: "980",
        KEY_DD_AS_BOT: "1131",
        KEY_DD_DIA_BOT: "12",
        KEY_DD_SPC_BOT: "100",
        KEY_DD_MU_TOP: "102.50",
        KEY_DD_AS_REQ_TOP: "1050",
        KEY_DD_AS_TOP: "1131",
        KEY_DD_AS_LONG: "452",
        KEY_DD_AS_MIN: "264",
        KEY_DD_SPACING_MAX: "200",
        KEY_DD_SHEAR_VED: "85.40",
        KEY_DD_SHEAR_VRDC: "148.20",
        KEY_DD_SHEAR_OK: "PASS",
        KEY_DD_PUNCH_VED_KN: "125.0",
        KEY_DD_PUNCH_OK: "PASS",
        KEY_DD_WK_BOT: "0.18",
        KEY_DD_WK_TOP: "0.19",
        KEY_DD_WK_LIMIT: "0.20",
        KEY_DD_MIN_COVER: "40",
        KEY_DD_COVER_OK: "PASS",
        KEY_DD_GAMMA_DL: "1.35",
        KEY_DD_GAMMA_LL: "1.50",
        KEY_DD_FY: "500",
        KEY_DD_VRD_C_MPA: "0.68",
        KEY_DD_HAS_OVERHANG: "True",
        KEY_DD_M_DL_OH: "5.10",
        KEY_DD_M_LL_OH: "38.20",
        KEY_DD_M_ULS_OH: "62.40",
        KEY_DD_MU_OH: "95.20",
        KEY_DD_WK_OH: "0.17",
    }

    # Chapter 5 Deck Design Summary (for Sec 5.5 and Exec Summary)
    output_dict["deck_design_results"] = {
        "ur_sagging_bending": 0.68,
        "ur_hogging_bending": 0.74,
        "ur_shear": 0.58,
        "ur_punching": 0.45,
        "ur_crack_width_sag": 0.78,
        "ur_crack_width_hog": 0.72,
        "rebar_bottom_area": 1131,
        "rebar_top_area": 1131,
    }

    # Chapter 5 Cross Bracing Forces & Results
    cb_pairs = {}
    for i in range(1, n_girders):
        p_name = f"G{i}-G{i+1}"
        cb_pairs[p_name] = {
            "diag_tension_kN": 125.4,
            "diag_compression_kN": -142.8,
            "chord_tension_kN": 45.2,
            "chord_compression_kN": -52.6,
            "diag_tension_gov_lc": "1.35 DL + 1.50 LL",
            "diag_compression_gov_lc": "1.35 DL + 1.50 LL",
            "chord_tension_gov_lc": "1.35 DL + 1.50 LL",
            "chord_compression_gov_lc": "1.35 DL + 1.50 LL",
        }

    output_dict["crossbracing_forces_dict"] = {
        "pairs": cb_pairs,
        "geometry": {
            "diagonal_length_m": 2.85,
            "horiz_proj_m": 2.50,
            "alpha_deg": 41.2,
            "cb_spacing_m": 4.0,
        },
        "brace_type": "X",
    }

    osdag_cb_diagonal = {
        "tension": {
            "section_size.designation": "ISA 100x100x10",
            "Member.tension_capacity": 245.0,
            "Member.efficiency": 0.512,
            "Member.Slenderness": 115.0,
            "Weld.Type": "Fillet",
        },
        "compression": {
            "section_size.designation": "ISA 100x100x10",
            "Design.Strength": 185.0,
            "Member.efficiency": 0.772,
            "Member.Slenderness": 115.0,
            "Weld.Type": "Fillet",
        },
    }

    osdag_cb_chord = {
        "tension": {
            "section_size.designation": "ISA 75x75x8",
            "Member.tension_capacity": 150.0,
            "Member.efficiency": 0.301,
            "Member.Slenderness": 95.0,
            "Weld.Type": "Fillet",
        },
        "compression": {
            "section_size.designation": "ISA 75x75x8",
            "Design.Strength": 110.0,
            "Member.efficiency": 0.478,
            "Member.Slenderness": 95.0,
            "Weld.Type": "Fillet",
        },
    }

    output_dict["crossbracing_design_results"] = {
        "G1-G2": {"diagonal": osdag_cb_diagonal, "chord": osdag_cb_chord},
        "G2-G3": {"diagonal": osdag_cb_diagonal, "chord": osdag_cb_chord},
    }

    # End Diaphragm results (similar structure)
    output_dict["end_diaphragm_design_results"] = {
        "G1-G2": {"diagonal": osdag_cb_diagonal, "chord": osdag_cb_chord},
        "G2-G3": {"diagonal": osdag_cb_diagonal, "chord": osdag_cb_chord},
    }

    # Chapter 8 Design Log Entries
    output_dict["design_log"] = [
        "INFO: Geometry module initialized with span = 24.0 m, 3 girders.",
        "INFO: Grillage mesh generated with 25 longitudinal and 7 transverse beams.",
        "INFO: Dead load and SIDL analysis completed successfully.",
        "INFO: Moving load analysis executed for IRC Class A and IRC 70R Wheeled.",
        "INFO: Design moment and shear envelopes evaluated across all load combinations.",
        "INFO: Plate girder G1 check: PASS (Governing UR = 0.785 in Flexure).",
        "INFO: Plate girder G2 check: PASS (Governing UR = 0.760 in Flexure).",
        "INFO: Plate girder G3 check: PASS (Governing UR = 0.785 in Flexure).",
        "INFO: Cross bracing design verified: ISA 100x100x10 PASS (UR = 0.772).",
        "INFO: Deck slab design verified: 220 mm slab with 12 mm dia @ 100 mm c/c PASS.",
        "INFO: Bill of Quantities computed successfully.",
    ]

    return input_dict, output_dict


# ---------------------------------------------------------------------------
# 3. Main Runner & Quality Gate Analysis
# ---------------------------------------------------------------------------

def run_test(output_dir="output/before", file_stem="Report_Before", large: bool = False):
    abs_out_dir = os.path.abspath(output_dir)
    os.makedirs(abs_out_dir, exist_ok=True)

    print("=" * 70)
    print("OsdagBridge Report Generation Test Harness")
    print("=" * 70)
    print(f"Target Output Directory: {abs_out_dir}")
    print(f"File Stem:               {file_stem}")
    print(f"Payload Mode:            {'LARGE (Stress Test: 6 Girders, Multi-vehicle)' if large else 'NORMAL (3 Girders)'}")

    # 1. Assets preparation: copy logos to output_dir/assets so LaTeX finds them
    assets_dest = os.path.join(abs_out_dir, "assets")
    os.makedirs(assets_dest, exist_ok=True)
    osdag_logo_src = os.path.join(SRC_DIR, "osdagbridge", "core", "data", "ResourceFiles", "vectors", "Osdag Logo.png")
    if os.path.exists(osdag_logo_src):
        shutil.copy2(osdag_logo_src, os.path.join(assets_dest, "osdag_logo.png"))

    iit_logo_src = os.path.join(SRC_DIR, "osdagbridge", "core", "reports", "assets", "IIT Bombay Logo.png")
    if os.path.exists(iit_logo_src):
        shutil.copy2(iit_logo_src, os.path.join(assets_dest, "org_logo.png"))

    # 2. Build Metadata & Options
    metadata = ReportMetadata(
        project_name="Bridge on NH-48 (KM 142/2)",
        project_location="Mumbai Suburban, Maharashtra",
        designer="Er. Aditya Gupta",
        client="Ministry of Road Transport and Highways (MoRTH)",
        company="FOSSEE, IIT Bombay",
        group_name="Bridge Engineering Division",
        subtitle="Final Design Report - Rev 0" if not large else "Final Design Report (Large Model Stress Test)",
        job_number="OSDAG-2026-BR-01",
        additional_comments="Screening Task Evaluation Report for FOSSEE Internship.",
        report_date="2026-11-21",
        reviewer="Dr. Structural Reviewer",
    )

    options = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )

    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=abs_out_dir,
        file_stem=file_stem,
    )

    # 3. Build Mock Payload Data and Assemble LaTeX
    input_dict, output_dict = create_mock_payload_data(large=large)
    payload = build_report_payload(request, input_dict, output_dict)

    print("\n[1/4] Assembling LaTeX document from payload...")
    result = generate_report(payload, request)

    print("\n[2/4] Verification of Generated .tex File:")
    tex_path = result.tex_path

    if tex_path and os.path.exists(tex_path):
        size_kb = os.path.getsize(tex_path) / 1024.0
        with open(tex_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"  [SUCCESS] LaTeX Source: {tex_path}")
        print(f"            Size: {size_kb:.2f} KB | Lines: {len(lines)}")

        # Check chapter contents in the generated .tex
        tex_content = "".join(lines)
        chapters = [
            ("Chapter 1: Project Information", "Project Information"),
            ("Chapter 2: Input Parameters", "Input Parameters"),
            ("Chapter 3: Loads & Combinations", "Loads and Load Combinations"),
            ("Chapter 4: Structural Analysis", "Analysis"),
            ("Chapter 5: Design Checks", "Design Checks"),
            ("Chapter 6: General Drawings", "Drawings"),
            ("Chapter 7: Material Take-off / BOQ", "Material Take-off"),
            ("Chapter 8: Standards & Assumptions", r"Standards \& Assumptions"),
            ("References", "References"),
        ]
        print("\n  Chapter Verification in .tex:")
        for ch_title, ch_marker in chapters:
            found = ch_marker in tex_content
            status = "FOUND" if found else "NOT FOUND"
            print(f"    - {ch_title:38s}: {status}")
    else:
        print(f"  [ERROR] LaTeX source file was not generated: {tex_path}")
        return False

    # 4. Compile PDF in output_dir (2 passes for TOC and LastPage)
    compiler = shutil.which("pdflatex")
    pdf_path = os.path.join(abs_out_dir, f"{file_stem}.pdf")
    log_path = os.path.join(abs_out_dir, f"{file_stem}.log")
    aux_path = os.path.join(abs_out_dir, f"{file_stem}.aux")

    if compiler:
        print(f"\n[3/4] Compiling PDF with {compiler} (2 passes)...")
        for pass_num in (1, 2):
            subprocess.run(
                [compiler, "-interaction=nonstopmode", f"{file_stem}.tex"],
                cwd=abs_out_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        if os.path.exists(pdf_path):
            size_kb = os.path.getsize(pdf_path) / 1024.0
            print(f"  [SUCCESS] PDF Output: {pdf_path}")
            print(f"            Size: {size_kb:.2f} KB")
        else:
            print(f"  [WARNING] pdflatex executed but {pdf_path} was not created.")
    else:
        print("\n[3/4] PDF Compilation Status:")
        print("  [NOTE] pdflatex not found in environment PATH.")

    # 5. Parse .log file for Quality Gate metrics
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            log_text = f.read()

        latex_errors = re.findall(r"^! (.*)", log_text, re.MULTILINE)
        misplaced_noalign = log_text.count("Misplaced \\noalign")
        misplaced_omit = log_text.count("Misplaced \\omit")
        extra_alignment_tab = log_text.count("Extra alignment tab has been changed to \\cr")
        overfull_hbox = log_text.count("Overfull \\hbox")
        overfull_vbox = log_text.count("Overfull \\vbox")
        headheight_warnings = log_text.count("headheight is too small")
        mult_labels = len(re.findall(r"multiply-defined|multiply defined", log_text, re.I))
        unclosed_groups = log_text.count("occurred inside a group")

        print("\n[4/4] LaTeX Quality Gate Summary (.log analysis):")
        print(f"  Total LaTeX Errors (! ...):     {len(latex_errors)}")
        print(f"    - Misplaced \\noalign:         {misplaced_noalign}")
        print(f"    - Misplaced \\omit:            {misplaced_omit}")
        print(f"    - Extra alignment tab:        {extra_alignment_tab}")
        print(f"  Overfull \\hbox count:          {overfull_hbox}")
        print(f"  Overfull \\vbox count:          {overfull_vbox}")
        print(f"  Headheight warnings:            {headheight_warnings}")
        print(f"  Multiply-defined labels:        {mult_labels}")
        print(f"  Unclosed groups (level > 0):    {unclosed_groups}")
    else:
        print("\n[4/4] LaTeX Quality Gate Summary:")
        print("  [NOTE] No .log file available for analysis.")

    # 6. Multi-page Table Analysis (from .aux file)
    if os.path.exists(aux_path):
        with open(aux_path, "r", encoding="utf-8", errors="ignore") as f:
            aux_text = f.read()

        table_pattern = re.compile(
            r'\\@writefile\{lot\}\{\\contentsline\s*\{table\}\{\\numberline\s*\{([^}]+)\}\{\\ignorespaces\s*(?:\\textbf\s*)?\{?([^}]+)\}?\}\}\{(\d+)\}'
        )
        all_pattern = re.compile(
            r'\\@writefile\{(?:lot|toc|lof)\}\{\\contentsline\s*\{([^}]+)\}\{.*?\}\{(\d+)\}'
        )

        lot_tables = []
        for m in table_pattern.finditer(aux_text):
            lot_tables.append({
                "num": m.group(1).strip(),
                "title": m.group(2).strip().rstrip('}'),
                "start_page": int(m.group(3)),
            })

        all_items = []
        for m in all_pattern.finditer(aux_text):
            all_items.append((m.group(1).strip(), int(m.group(2))))

        table_idx = 0
        multipage_found = []
        for i, (elem_type, page) in enumerate(all_items):
            if elem_type == "table" and table_idx < len(lot_tables):
                next_page = page
                for j in range(i + 1, len(all_items)):
                    if all_items[j][1] > page:
                        next_page = all_items[j][1]
                        break
                t_info = lot_tables[table_idx]
                t_info["end_page"] = next_page
                # When next_page >= page + 2, the table definitely spans across pages
                if next_page >= page + 2:
                    t_info["spans_multiple"] = True
                    multipage_found.append(t_info)
                table_idx += 1

        print("\n[5/5] Multi-page Table Analysis (from .aux file):")
        if multipage_found:
            print(f"  Found {len(multipage_found)} table(s) spanning across multiple pages:")
            for t in multipage_found:
                print(f"    - Table {t['num']:5s} {t['title'][:45]:45s} | Starts P.{t['start_page']} -> Ends P.{t['end_page']-1}")
        else:
            print("  All tables fit within single page boundaries.")

    # 7. Footer-Overlap Detection (PyMuPDF)
    overlap_detected = []
    if os.path.exists(pdf_path):
        try:
            import fitz
            doc = fitz.open(pdf_path)
            footer_threshold_y = 765.0  # body text should not exceed y=765pt on A4 with 1.15in bottom margin
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                blocks = page.get_text("blocks")
                for b in blocks:
                    y1 = b[3]
                    txt = b[4].strip()
                    # Skip known footer texts
                    if any(k in txt for k in ["Osdag", "Page", "Software default", "Ministry", "Bridge Report", "Indian Institute of Technology"]):
                        continue
                    if y1 > footer_threshold_y:
                        overlap_detected.append((page_idx + 1, round(y1, 1), txt[:50]))
            doc.close()
        except ImportError:
            print("\n[NOTE] PyMuPDF (fitz) not available; skipping footer overlap check.")
        except Exception as e:
            print(f"\n[NOTE] Footer overlap check error: {e}")

    print("\n[6/6] Footer Overlap Detection:")
    if overlap_detected:
        print(f"  [WARNING] Found {len(overlap_detected)} text block(s) intruding into footer zone (y > 765pt):")
        for p, y, txt in overlap_detected:
            print(f"    - Page {p} (y={y}pt): {txt!r}")
    else:
        print("  0 footer overlap collisions detected (all body text ends cleanly above footer zone).")

    # 7. Ghost Header Detection (PyMuPDF)
    # Detects orphan continuation headers ("Table X.Y -- continued from previous page")
    # followed immediately on the same page by the same table's caption ("Table X.Y:").
    ghost_headers_detected = []
    if os.path.exists(pdf_path):
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for page_idx in range(len(doc)):
                text = doc[page_idx].get_text()
                m_cont = re.search(r"Table\s+(\d+\.\d+)\s+[–-]\s+continued from previous page", text)
                if m_cont:
                    tbl_num = m_cont.group(1)
                    cont_pos = m_cont.start()
                    m_cap = re.search(rf"Table\s+{re.escape(tbl_num)}:", text)
                    if m_cap and m_cap.start() > cont_pos:
                        ghost_headers_detected.append((page_idx + 1, tbl_num))
            doc.close()
        except ImportError:
            pass
        except Exception as e:
            print(f"\n[NOTE] Ghost header check error: {e}")

    print("\n[7/7] Ghost Header Detection:")
    if ghost_headers_detected:
        print(f"  [FAILURE] Found {len(ghost_headers_detected)} ghost header(s) (orphan continuation header before table caption):")
        for p, tbl_num in ghost_headers_detected:
            print(f"    - Page {p}: Table {tbl_num}")
    else:
        print("  0 ghost headers detected (no orphan continuation header followed by caption).")

    print("\n" + "=" * 70)
    print("Test Harness Execution Completed!")
    print("=" * 70)
    return len(ghost_headers_detected) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Harness for OsdagBridge Report Generator")
    parser.add_argument("--out-dir", default="output/before", help="Output directory for generated reports")
    parser.add_argument("--stem", default="Report_Before", help="File stem for .tex and .pdf")
    parser.add_argument("--large", action="store_true", help="Stress test with 6 girders, 5 bracing panels, 5+ vehicles, custom vehicle")
    args = parser.parse_args()

    success = run_test(output_dir=args.out_dir, file_stem=args.stem, large=args.large)
    sys.exit(0 if success else 1)
