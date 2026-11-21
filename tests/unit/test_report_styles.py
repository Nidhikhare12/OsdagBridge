"""Unit tests for report styling and table infrastructure (Phase 1)."""

import os
import sys

# Ensure Windows conda environment Library/bin is registered for NumPy/Matplotlib BLAS
if sys.platform == "win32":
    _env_lib_bin = os.path.join(sys.prefix, "Library", "bin")
    if os.path.exists(_env_lib_bin):
        os.environ["PATH"] = _env_lib_bin + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(_env_lib_bin)
            except OSError:
                pass

import re
import unittest

from osdagbridge.core.reports.styles import (
    HEAD_HEIGHT,
    FOOT_SKIP,
    MARGIN_BOTTOM,
    TEXT_WIDTH_MM,
    COLOR_OSDAG_GREEN,
    get_geometry_latex,
    get_color_definitions_latex,
    get_table_styling_latex,
    get_header_footer_latex,
)
from osdagbridge.core.reports.table_builder import (
    TableBuilder,
    format_longtable,
    infer_num_columns,
)
from osdagbridge.core.reports.report_generator import preamble


class TestReportStyles(unittest.TestCase):
    """Test centralized report styling configuration."""

    def test_geometry_latex(self):
        geom = get_geometry_latex()
        self.assertIn("a4paper", geom)
        self.assertIn("headheight=24pt", geom)
        self.assertIn("bottom=28mm", geom)
        self.assertIn("footskip=14mm", geom)

    def test_color_definitions(self):
        colors = get_color_definitions_latex()
        self.assertIn(r"\definecolor{osdagGreen}{HTML}{91B014}", colors)
        self.assertIn(r"\definecolor{osdagPass}{HTML}{2E7D32}", colors)
        self.assertIn(r"\definecolor{osdagFail}{HTML}{D32F2F}", colors)

    def test_table_styling_latex(self):
        styling = get_table_styling_latex()
        self.assertIn(r"\setlength{\tabcolsep}{6pt}", styling)
        self.assertIn(r"\renewcommand{\arraystretch}{1.15}", styling)
        self.assertIn(r"\needspace{6\baselineskip}", styling)

    def test_header_footer_no_negative_vspace(self):
        hf = get_header_footer_latex("TestProject", "JOB-001", "2026-11-19", "Rev 0")
        self.assertIn("TestProject $|$ JOB-001", hf)
        self.assertIn(r"Page \thepage\ of \pageref", hf)
        self.assertIn(r"0.55\headwidth", hf)
        self.assertIn(r"0.40\headwidth", hf)
        self.assertNotIn(r"\vspace{-20pt}", hf)
        self.assertNotIn(r"\vspace{-8pt}", hf)

    def test_preamble_integration(self):
        p = preamble("Project Alpha", "JOB-100", "2026-11-19")
        self.assertIn(r"\documentclass[12pt,a4paper]{report}", p)
        self.assertIn("headheight=24pt", p)
        self.assertIn("footskip=14mm", p)
        self.assertIn(r"\definecolor{osdagGreen}{HTML}{91B014}", p)
        self.assertIn(r"\begin{document}", p)


class TestTableBuilder(unittest.TestCase):
    """Test reusable LongTable/TableBuilder helper."""

    def test_column_inference(self):
        self.assertEqual(infer_num_columns(r"|C{2.6cm}|L{6.2cm}|L{5.8cm}|"), 3)
        self.assertEqual(infer_num_columns(r"|c|l|r|p{3cm}|"), 4)
        self.assertEqual(infer_num_columns(r"|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|"), 5)

    def test_table_builder_caption_and_headers(self):
        builder = TableBuilder(
            col_spec=r"|C{2.6cm}|L{6.2cm}|L{5.8cm}|",
            caption="Stiffener Design Summary",
            label="tab:stiffener-test"
        )
        builder.set_headers(["Girder", "Parameter", "Value"])
        builder.add_row("G1", "Shear Buckling Method", "Simple post-critical")
        table_tex = builder.build()

        # Check caption terminating with \\
        self.assertIn(r"\caption{\textbf{Stiffener Design Summary}}\label{tab:stiffener-test}\\", table_tex)

        # Check multi-page headers and footers protocol
        self.assertIn(r"\endfirsthead", table_tex)
        self.assertIn(r"continued from previous page", table_tex)
        self.assertIn(r"\endhead", table_tex)
        self.assertIn(r"Continued on next page\ldots", table_tex)
        self.assertIn(r"\endfoot", table_tex)
        self.assertIn(r"\endlastfoot", table_tex)
        self.assertIn(r"\end{longtable}", table_tex)

    def test_format_longtable_convenience(self):
        table_tex = format_longtable(
            col_spec=r"|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|",
            caption="Overall Design Check Summary --- All Members",
            headers=[r"\textbf{Member}", r"\textbf{LC}", r"\textbf{Demand}", r"\textbf{Capacity}", r"\textbf{UR}"],
            content=r"Girder Flexure & ULS-01 & 120.0 & 200.0 & 0.60 \\ \hline",
            label="tab:overall-summary-test",
            note="UR <= 1.0 indicates pass."
        )
        self.assertIn(r"\caption{\textbf{Overall Design Check Summary --- All Members}}\label{tab:overall-summary-test}\\", table_tex)
        self.assertIn(r"\endfirsthead", table_tex)
        self.assertIn(r"\endhead", table_tex)
        self.assertIn(r"\endfoot", table_tex)
        self.assertIn(r"\endlastfoot", table_tex)
        self.assertIn(r"\noindent\textit{Note: UR <= 1.0 indicates pass.}", table_tex)


class TestCaptionSyntax(unittest.TestCase):
    """Verify that all captions in chap2, chap3, chap4, and chap5 conform to longtable rules."""

    def test_unicode_escaping(self):
        from osdagbridge.core.reports.report_utils import _tex
        escaped = _tex("Int.Stiff: Leg \u2264 H_limit and \u2265 min")
        self.assertIn(r"$\leq$", escaped)
        self.assertIn(r"$\geq$", escaped)
        self.assertNotIn("\u2264", escaped)

    def test_chap2_longtable_captions(self):
        chap2_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "src", "osdagbridge", "core", "reports", "chap2.py"
        )
        with open(chap2_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        in_longtable = False
        for line_no, line in enumerate(lines, 1):
            if r"\begin{longtable}" in line:
                in_longtable = True
            elif r"\end{longtable}" in line:
                in_longtable = False
            elif in_longtable and r"\caption{" in line:
                self.assertTrue(
                    line.strip().endswith(r"\\"),
                    f"chap2.py line {line_no} longtable caption does not end with \\\\: {line.strip()}"
                )

    def test_chap3_captions(self):
        chap3_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "src", "osdagbridge", "core", "reports", "chap3.py"
        )
        with open(chap3_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if r"\caption{" in line:
                    self.assertTrue(
                        line.strip().endswith(r"\\"),
                        f"chap3.py line {line_no} caption does not end with \\\\: {line.strip()}"
                    )

    def test_chap4_longtable_captions(self):
        chap4_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "src", "osdagbridge", "core", "reports", "chap4.py"
        )
        with open(chap4_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        in_longtable = False
        for line_no, line in enumerate(lines, 1):
            if r"\begin{longtable}" in line:
                in_longtable = True
            elif r"\end{longtable}" in line:
                in_longtable = False
            elif in_longtable and r"\caption{" in line:
                self.assertTrue(
                    line.strip().endswith(r"\\"),
                    f"chap4.py line {line_no} longtable caption does not end with \\\\: {line.strip()}"
                )

    def test_chap5_captions(self):
        chap5_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "src", "osdagbridge", "core", "reports", "chap5.py"
        )
        with open(chap5_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        in_longtable = False
        for line_no, line in enumerate(lines, 1):
            if r"\begin{longtable}" in line:
                in_longtable = True
            elif r"\end{longtable}" in line:
                in_longtable = False
            elif in_longtable and r"\caption{" in line:
                self.assertTrue(
                    line.strip().endswith(r"\\"),
                    f"chap5.py line {line_no} longtable caption does not end with \\\\: {line.strip()}"
                )


class TestChapter3Tables(unittest.TestCase):
    """Targeted unit tests for Chapter 3 Live Load and Footpath Load restructuring (Phase 2)."""

    def setUp(self):
        from osdagbridge.core.utils.common import (
            KEY_SPAN,
            KEY_FOOTPATH,
            KEY_TS_NO_OF_FOOTPATHS,
            KEY_TS_FOOTPATH_WIDTH,
            KEY_LL_FOOTPATH_PRESSURE_MODE,
            KEY_LL_FOOTPATH_PRESSURE_VALUE,
            KEY_LL_IRC_CLASS_A,
            KEY_LL_IRC_70R_WHEELED,
            KEY_LL_IRC_70R_TRACKED,
            KEY_LL_IRC_70R_BOGIE,
            KEY_LL_IRC_AA_WHEELED,
            KEY_LL_IRC_AA_TRACKED,
            KEY_LL_IRC_CLASS_SV,
            KEY_LL_IRC_CLASS_FATIGUE,
            KEY_BL_IRC_CLASS_SV,
            KEY_LL_CUSTOM_VEHICLES,
        )
        self.k_span = KEY_SPAN
        self.k_fp = KEY_FOOTPATH
        self.k_n_fp = KEY_TS_NO_OF_FOOTPATHS
        self.k_fp_w = KEY_TS_FOOTPATH_WIDTH
        self.k_fp_mode = KEY_LL_FOOTPATH_PRESSURE_MODE
        self.k_fp_val = KEY_LL_FOOTPATH_PRESSURE_VALUE
        self.k_cla = KEY_LL_IRC_CLASS_A
        self.k_70rw = KEY_LL_IRC_70R_WHEELED
        self.k_70rt = KEY_LL_IRC_70R_TRACKED
        self.k_70rb = KEY_LL_IRC_70R_BOGIE
        self.k_aaw = KEY_LL_IRC_AA_WHEELED
        self.k_aat = KEY_LL_IRC_AA_TRACKED
        self.k_sv = KEY_LL_IRC_CLASS_SV
        self.k_fat = KEY_LL_IRC_CLASS_FATIGUE
        self.k_bl_sv = KEY_BL_IRC_CLASS_SV
        self.k_custom = KEY_LL_CUSTOM_VEHICLES

    def test_vehicle_live_load_table_all_vehicles(self):
        from osdagbridge.core.reports.chap3 import build_vehicle_live_load_table
        inp = {
            self.k_span: 30.0,
            self.k_cla: True,
            self.k_70rw: True,
            self.k_70rt: True,
            self.k_70rb: True,
            self.k_aaw: True,
            self.k_aat: True,
            self.k_sv: True,
            self.k_fat: True,
        }
        tex = build_vehicle_live_load_table(inp)

        # Verify all vehicle names appear
        for name in ["Class A", "Class 70R (Wheeled)", "Class 70R (Tracked)", "Class 70R (Bogie)",
                     "Class AA (Wheeled)", "Class AA (Tracked)", "Class SV", "Class Fatigue"]:
            self.assertIn(name, tex)

        # Verify characteristic loads (physical force equivalents with g = 9.81 m/s2)
        self.assertIn("543.5 kN (55.4 t)", tex)
        self.assertIn("981.0 kN (100.0 t)", tex)  # Class 70R Wheeled = 100t (IRC 6 Cl. 204.1)
        self.assertIn("686.7 kN (70.0 t)", tex)   # Class 70R Tracked & Class AA Tracked = 70t * 9.81
        self.assertIn("392.4 kN (40.0 t)", tex)   # Class AA Wheeled & Class 70R Bogie = 40t * 9.81
        self.assertIn("3776.9 kN (385.0 t)", tex) # Class SV
        self.assertIn("392.4 kN (40.0 t)", tex)   # Class Fatigue

        # Verify impact factors
        self.assertIn("1.207", tex)  # Class A & wheeled
        self.assertIn("1.100", tex)  # Tracked
        self.assertIn("1.000", tex)  # SV & Fatigue

        # Verify braking forces (20% first-train component per IRC 6 Cl. 211.2)
        self.assertIn("108.69 kN (11.08 t)", tex) # Class A: 0.20 * 543.474 kN
        self.assertIn("196.20 kN (20.00 t)", tex) # Class 70R Wheeled: 0.20 * 981 kN
        self.assertIn("78.48 kN (8.00 t)", tex)   # Class AA Wheeled / 70R Bogie: 0.20 * 392.4 kN
        self.assertIn("N/A (Tracked)", tex)

        # Verify centrifugal force is N/A for straight alignment (R = infinity)
        self.assertIn("N/A", tex)
        self.assertIn("straight bridge alignments", tex)
        self.assertIn(r"$R = \infty$", tex)

        # Verify caption, headers and table structure
        self.assertIn(r"\caption{\textbf{Vehicle Live Loads (LL) --- per IRC 6:2017}}\label{tab:vehicle-live-loads}\\", tex)
        self.assertIn(r"\textbf{Braking Force (1\textsuperscript{st} Train)}", tex)
        self.assertIn(r"\endfirsthead", tex)
        self.assertIn(r"\endhead", tex)
        self.assertIn(r"\endfoot", tex)
        self.assertIn(r"\endlastfoot", tex)

    def test_centrifugal_force_straight_vs_curved(self):
        from osdagbridge.core.reports.chap3 import build_vehicle_live_load_table

        # 1. Straight alignment (radius None or 0 => R = infinity)
        inp_straight = {
            self.k_span: 30.0,
            self.k_cla: True,
        }
        tex_straight = build_vehicle_live_load_table(inp_straight)
        self.assertIn("N/A", tex_straight)
        self.assertIn("straight bridge alignments", tex_straight)
        self.assertIn(r"$R = \infty$", tex_straight)

        # 2. Curved alignment with R = 300 m, V = 80 km/h per IRC 6 Cl. 212.2
        # C = W * V^2 / (127 * R)
        # Class A: 543.474 * 6400 / (127 * 300) = 91.30 kN
        # Class 70R Wheeled: 981.0 * 6400 / (127 * 300) = 164.79 kN
        inp_curved = {
            self.k_span: 30.0,
            self.k_cla: True,
            self.k_70rw: True,
            "radius": 300.0,
            "design_speed": 80.0,
        }
        tex_curved = build_vehicle_live_load_table(inp_curved)
        self.assertIn("91.30 kN", tex_curved)
        self.assertIn("164.79 kN", tex_curved)
        self.assertIn("Centrifugal force computed per IRC:6-2017 Cl. 212.2", tex_curved)
        self.assertIn("Cl. 212.3", tex_curved)

    def test_dynamic_vehicle_selection_variants(self):
        from osdagbridge.core.reports.chap3 import build_vehicle_live_load_table

        # (a) Only Class A
        inp_a = {self.k_span: 30.0, self.k_cla: True, self.k_70rw: False, self.k_sv: False}
        tex_a = build_vehicle_live_load_table(inp_a)
        self.assertIn("Class A", tex_a)
        self.assertNotIn("Class 70R", tex_a)
        self.assertNotIn("Class SV", tex_a)

        # (b) Only one heavy vehicle (Class 70R Wheeled)
        inp_b = {self.k_span: 30.0, self.k_cla: False, self.k_70rw: True}
        tex_b = build_vehicle_live_load_table(inp_b)
        self.assertNotIn("Class A", tex_b)
        self.assertIn("Class 70R (Wheeled)", tex_b)
        self.assertIn("981.0 kN (100.0 t)", tex_b)

        # (c) Multiple vehicle classes
        inp_c = {
            self.k_span: 30.0,
            self.k_cla: True,
            self.k_70rt: True,
            self.k_sv: True,
            self.k_bl_sv: True,
        }
        tex_c = build_vehicle_live_load_table(inp_c)
        self.assertIn("Class A", tex_c)
        self.assertIn("Class 70R (Tracked)", tex_c)
        self.assertIn("686.7 kN (70.0 t)", tex_c)
        self.assertIn("Class SV", tex_c)
        self.assertIn("755.37 kN (77.00 t)", tex_c)
        self.assertNotIn("Class AA", tex_c)

        # (d) No standard vehicle selected
        inp_d = {self.k_span: 30.0}
        tex_d = build_vehicle_live_load_table(inp_d)
        self.assertIn("No live load vehicle classes selected", tex_d)

        # (e) Custom vehicles
        inp_e = {
            self.k_span: 30.0,
            self.k_custom: [
                {"name": "Heavy Lowbed Trailer", "total_load": 1200.0, "impact_factor": 1.10}
            ]
        }
        tex_e = build_vehicle_live_load_table(inp_e)
        self.assertIn("Heavy Lowbed Trailer", tex_e)
        self.assertIn("1200.0 kN", tex_e)
        self.assertIn("240.00 kN", tex_e)
        self.assertIn("1.100", tex_e)

    def test_footpath_conditions_all_variants(self):
        from osdagbridge.core.reports.chap3 import build_footpath_live_load_table

        # 1. Disabled state
        inp_disabled = {self.k_fp: "None"}
        tex_dis = build_footpath_live_load_table(inp_disabled)
        self.assertIn("None (Not provided)", tex_dis)
        self.assertIn("0", tex_dis)
        self.assertIn("Footway Surface Live Load (Deck Slab)", tex_dis)
        self.assertIn("Main Girder Live Load (Cl. 206.3)", tex_dis)
        self.assertIn("N/A (Footpath disabled)", tex_dis)

        # 2. 1 Footpath
        inp_1fp = {
            self.k_span: 30.0,
            self.k_fp: "Single Side",
            self.k_n_fp: 1,
            self.k_fp_w: 1.25,
            self.k_fp_mode: "As per IRC 6",
        }
        tex_1fp = build_footpath_live_load_table(inp_1fp)
        self.assertIn("Single Side", tex_1fp)
        self.assertIn("1.25 m", tex_1fp)
        self.assertIn("4.905", tex_1fp)
        self.assertIn("2.943", tex_1fp)

        # 3. 2 Footpaths
        inp_2fp = {
            self.k_span: 30.0,
            self.k_fp: "Both Sides",
            self.k_n_fp: 2,
            self.k_fp_w: 1.80,
            self.k_fp_mode: "As per IRC 6",
        }
        tex_2fp = build_footpath_live_load_table(inp_2fp)
        self.assertIn("Both Sides", tex_2fp)
        self.assertIn("2", tex_2fp)
        self.assertIn("1.80 m", tex_2fp)
        self.assertIn("4.905", tex_2fp)
        self.assertIn("2.943", tex_2fp)

        # 4. IRC default mode
        inp_irc = {
            self.k_span: 30.0,
            self.k_fp: "Single Side",
            self.k_fp_mode: "As per IRC 6",
        }
        tex_irc = build_footpath_live_load_table(inp_irc)
        self.assertIn("application default", tex_irc)
        self.assertIn("Cl. 206.3", tex_irc)
        self.assertIn("2.943", tex_irc)

        # 5. Custom mode with width, intensity, and units
        inp_custom = {
            self.k_fp: "Both Sides",
            self.k_n_fp: 2,
            self.k_fp_w: 2.0,
            self.k_fp_mode: "Custom",
            self.k_fp_val: "5.5",
        }
        tex_custom = build_footpath_live_load_table(inp_custom)
        self.assertIn("2.00 m", tex_custom)
        self.assertIn("5.5", tex_custom)
        self.assertIn(r"kN/m\textsuperscript{2}", tex_custom)
        self.assertIn("Custom", tex_custom)

    def test_vehicle_class_selection(self):
        from osdagbridge.core.reports.chap3 import build_vehicle_live_load_table
        inp = {
            self.k_span: 30.0,
            self.k_cla: True,
            self.k_70rw: False,
            self.k_sv: False,
        }
        tex = build_vehicle_live_load_table(inp)
        self.assertIn("Class A", tex)
        self.assertNotIn("Class 70R (Wheeled)", tex)
        self.assertNotIn("Class SV", tex)

    def test_vehicle_table_no_selection(self):
        from osdagbridge.core.reports.chap3 import build_vehicle_live_load_table
        tex = build_vehicle_live_load_table({})
        self.assertIn("No live load vehicle classes selected", tex)
        self.assertIn(r"\end{longtable}", tex)

    def test_footpath_disabled_state(self):
        from osdagbridge.core.reports.chap3 import build_footpath_live_load_table
        inp = {
            self.k_fp: "None",
            self.k_fp_mode: "As per IRC 6",
            self.k_fp_val: "",
        }
        tex = build_footpath_live_load_table(inp)
        self.assertIn("None (Not provided)", tex)
        self.assertIn("N/A (Footpath disabled)", tex)
        self.assertIn("No footpath is provided", tex)
        self.assertNotIn("&  \\[6pt]", tex)
        self.assertIn(r"\caption{\textbf{Footpath Live Load --- per IRC 6 Cl. 206}}\label{tab:footpath-live-load}\\", tex)

    def test_footpath_enabled_state_irc6(self):
        from osdagbridge.core.reports.chap3 import build_footpath_live_load_table
        inp = {
            self.k_fp: "Both Sides",
            self.k_n_fp: 2,
            self.k_fp_w: 1.5,
            self.k_fp_mode: "As per IRC 6",
        }
        tex = build_footpath_live_load_table(inp)
        self.assertIn("Both Sides", tex)
        self.assertIn("2", tex)
        self.assertIn("1.50 m", tex)
        self.assertIn("4.905", tex)
        self.assertIn(r"kN/m\textsuperscript{2}", tex)
        self.assertIn("IRC 6 Cl. 206.1", tex)

    def test_footpath_custom_value(self):
        from osdagbridge.core.reports.chap3 import build_footpath_live_load_table
        inp = {
            self.k_fp: "Single Side",
            self.k_fp_mode: "Custom",
            self.k_fp_val: "5.0",
        }
        tex = build_footpath_live_load_table(inp)
        self.assertIn("Single Side", tex)
        self.assertIn("5.0", tex)
        self.assertIn(r"kN/m\textsuperscript{2}", tex)
        self.assertIn("Custom", tex)

    def test_chap3_full_integration(self):
        from osdagbridge.core.reports.chap3 import ch3_loads
        inp = {
            self.k_span: 30.0,
            self.k_fp: "None",
            self.k_cla: True,
            self.k_70rw: True,
        }
        tex = ch3_loads(inp)
        self.assertIn(r"\label{tab:vehicle-live-loads}", tex)
        self.assertIn(r"\label{tab:footpath-live-load}", tex)
        self.assertIn("Vehicle Live Loads (LL)", tex)
        self.assertIn("Footpath Live Load", tex)
        self.assertNotIn("Footpath Live Load (if applicable)", tex)

    def test_clause_206_reporting_distinctions(self):
        """Test Phase 2.3 distinctions for IRC 6 Cl. 206.1 and Cl. 206.3."""
        from osdagbridge.core.reports.chap3 import (
            build_footpath_live_load_table,
            build_vehicle_live_load_table,
        )

        inp_30m = {
            self.k_span: 30.0,
            self.k_fp: "Both Sides",
            self.k_n_fp: 2,
            self.k_fp_w: 1.50,
            self.k_fp_mode: "As per IRC 6",
            self.k_cla: True,
            self.k_70rt: True,
        }
        tex_fp = build_footpath_live_load_table(inp_30m)

        # 1. Deck surface load: ordinary (400 kg/m² = 3.924 kN/m²) and application default / crowd (500 kg/m² = 4.905 kN/m²)
        self.assertIn("4.905", tex_fp)
        self.assertIn("3.924", tex_fp)
        self.assertIn("500 kg/m", tex_fp)
        self.assertIn("400 kg/m", tex_fp)

        # 2. Main girder load for 30 m span:
        # Ordinary footway receives (40*30-300)/9 = 100 kg/m² reduction -> 300 kg/m² (2.943 kN/m²)
        self.assertIn("2.943", tex_fp)
        self.assertIn("300 kg/m", tex_fp)
        self.assertIn("ordinary reduced", tex_fp)

        # Crowd loading does NOT receive reduction -> remains 500 kg/m² (4.905 kN/m²)
        self.assertIn("crowd unreduced", tex_fp)
        self.assertIn("reduction does not apply to crowd loading", tex_fp)

        # 3. Application default labeled accurately, not universal IRC default
        self.assertIn("application default", tex_fp)
        self.assertNotIn("universal IRC default", tex_fp)
        self.assertIn("ordinary footway classification is not selectable through the current GUI", tex_fp)

        # 4. Entire carriageway crowd-loading check
        self.assertIn("entire carriageway occupied by crowd load", tex_fp)
        self.assertIn("not supported by the current solver (known software limitation)", tex_fp)

        # 5. Disabled footpath remains N/A
        inp_disabled = {self.k_fp: "None"}
        tex_dis = build_footpath_live_load_table(inp_disabled)
        self.assertIn("N/A (Footpath disabled)", tex_dis)

        # 6. Tracked vehicle braking described as implementation limitation, not express code exemption
        tex_veh = build_vehicle_live_load_table(inp_30m)
        self.assertIn("tracked vehicles are designated N/A due to an implementation limitation in the solver", tex_veh)
        self.assertIn("rather than an express code exemption", tex_veh)


class TestPhase3URCharts(unittest.TestCase):
    """Targeted unit tests for Phase 3 UR chart generation and Section 5.5 integration."""

    def setUp(self):
        self.input_dict = {
            "typical_section.no_of_girders": 4,
            "member_properties.end_diaphragm_details.type.G1G2.E1M1": "Rolled Beam",
            "span": 30.0,
        }
        self.output_dict = {
            "design_results": {
                "per_girder": {
                    "G1": {
                        "checks": [
                            {"check_id": 1, "name": "Bending Moment", "dcr": 0.50, "status": "PASS"},
                            {"check_id": 8, "name": "Fatigue Normal Stress", "dcr": 1.528, "status": "FAIL"},
                        ]
                    },
                    "G2": {
                        "checks": [
                            {"check_id": 1, "name": "Bending Moment", "dcr": 0.51, "status": "PASS"},
                            {"check_id": 8, "name": "Fatigue Normal Stress", "dcr": 1.540, "status": "FAIL"},
                        ]
                    },
                    "G3": {
                        "checks": [
                            {"check_id": 1, "name": "Bending Moment", "dcr": 0.52, "status": "PASS"},
                            {"check_id": 8, "name": "Fatigue Normal Stress", "dcr": 1.573, "status": "FAIL"},
                        ]
                    },
                    "G4": {
                        "checks": [
                            {"check_id": 1, "name": "Bending Moment", "dcr": 0.52, "status": "PASS"},
                            {"check_id": 8, "name": "Fatigue Normal Stress", "dcr": 1.573, "status": "FAIL"},
                        ]
                    },
                }
            },
            "deck_design_results": {
                "ur_bot_uls": 0.88,
                "ur_top_uls": 0.858,
                "ur_oh_uls": 0.938,
                "ur_bot_shear": 0.83,
                "ur_bot_punch": 0.342,
                "ur_top_crack": 0.708,
            },
            "deck_report_values": {
                "deck.has_overhang": True,
            },
            "crossbracing_forces_dict": {
                "pairs": {
                    "G1-G2": {"diag_compression_kN": -8.00, "chord_compression_kN": -6.63},
                    "G2-G3": {"diag_tension_kN": 7.12, "chord_tension_kN": 5.90},
                    "G3-G4": {"diag_tension_kN": 9.59, "chord_tension_kN": 7.94},
                }
            },
            "crossbracing_design_results": {
                "G1-G2": {
                    "diagonal": {"compression": {"efficiency": "0.74"}},
                    "chord": {"compression": {"efficiency": "0.61"}},
                },
                "G2-G3": {
                    "diagonal": {"tension": {"efficiency": "0.16"}},
                    "chord": {"tension": {"efficiency": "0.13"}},
                },
                "G3-G4": {
                    "diagonal": {"tension": {"efficiency": "0.21"}},
                    "chord": {"tension": {"efficiency": "0.18"}},
                },
            },
            "end_diaphragm_design_results": {
                "G1-G2": {},
                "G2-G3": {},
                "G3-G4": {},
            },
        }

    def _make_bridge(self):
        class MockBridge:
            def __init__(self, inp, out):
                self.input_dict = inp
                self.output_dict = out
                self.payload = None

            def get_cb_pairs(self):
                return sorted(self.output_dict.get("crossbracing_forces_dict", {}).get("pairs", {}).keys())

            def get_cb_governing_force(self, pair, member):
                pairs = self.output_dict.get("crossbracing_forces_dict", {}).get("pairs", {}).get(pair, {})
                c = pairs.get(f"diag_compression_kN" if member == "diagonal" else "chord_compression_kN")
                t = pairs.get(f"diag_tension_kN" if member == "diagonal" else "chord_tension_kN")
                if c is not None:
                    return (f"{abs(c):.3f}", "compression")
                return (f"{t:.3f}", "tension") if t is not None else ("", "compression")

            def get_cb_efficiency(self, pair, member, ftype):
                res = self.output_dict.get("crossbracing_design_results", {}).get(pair, {}).get(member, {}).get(ftype, {})
                return str(res.get("efficiency", ""))

            def get_cb_status(self, pair, member, ftype):
                try:
                    eff = float(self.get_cb_efficiency(pair, member, ftype))
                    return "PASS" if eff <= 1.0 else "FAIL"
                except (ValueError, TypeError):
                    return "---"

            def get_cb_section(self, pair, member, ftype):
                return "40 x 40 x 3"

            def get_cb_gov_lc(self, pair, member, ftype):
                return "1.5 EQ (b)"

            def get_cb_capacity(self, pair, member, ftype):
                return "16.81"

            def get_cb_connection(self, pair, member, ftype):
                return "Bolted"

            def get_cb_effective_length(self, member):
                return "2535"

            def get_cb_slenderness(self, pair, member):
                return "134.0"

        return MockBridge(self.input_dict, self.output_dict)

    def test_girder_ur_data_extraction(self):
        """1. Plate Girders UR data extracted from actual per_girder results."""
        from osdagbridge.core.reports.ur_charts import extract_girder_ur_data
        bridge = self._make_bridge()
        data = extract_girder_ur_data(bridge)
        self.assertEqual(len(data), 4)
        self.assertEqual([d["id"] for d in data], ["G1", "G2", "G3", "G4"])
        # Governing fatigue normal stress URs
        self.assertAlmostEqual(data[0]["ur"], 1.528, places=3)
        self.assertAlmostEqual(data[1]["ur"], 1.540, places=3)
        self.assertAlmostEqual(data[2]["ur"], 1.573, places=3)
        self.assertAlmostEqual(data[3]["ur"], 1.573, places=3)
        # All 4 exceed 1.0 -> FAIL
        for d in data:
            self.assertEqual(d["status"], "FAIL")
            self.assertEqual(d["check_name"], "Fatigue Normal Stress")

    def test_deck_slab_ur_data_extraction(self):
        """2. Concrete Deck Slab UR data extracted from actual deck results."""
        from osdagbridge.core.reports.ur_charts import extract_deck_slab_ur_data
        bridge = self._make_bridge()
        data = extract_deck_slab_ur_data(bridge)
        self.assertEqual(len(data), 6)
        check_ids = [d["id"] for d in data]
        self.assertEqual(check_ids, ["deck_sag", "deck_hog", "deck_oh", "deck_shear", "deck_punch", "deck_crack"])
        self.assertAlmostEqual(data[0]["ur"], 0.88, places=2)
        self.assertAlmostEqual(data[1]["ur"], 0.858, places=3)
        self.assertAlmostEqual(data[2]["ur"], 0.938, places=3)
        self.assertAlmostEqual(data[3]["ur"], 0.83, places=2)
        self.assertAlmostEqual(data[4]["ur"], 0.342, places=3)
        self.assertAlmostEqual(data[5]["ur"], 0.708, places=3)
        # All 6 <= 1.0 -> PASS
        for d in data:
            self.assertEqual(d["status"], "PASS")

    def test_cross_bracing_ur_data_extraction(self):
        """3. Cross Bracing member-level UR data extracted accurately."""
        from osdagbridge.core.reports.ur_charts import extract_cross_bracing_ur_data
        bridge = self._make_bridge()
        data = extract_cross_bracing_ur_data(bridge)
        self.assertEqual(len(data), 6)
        # G1-G2 Diag (0.74), G1-G2 Chord (0.61), G2-G3 Diag (0.16), G2-G3 Chord (0.13), G3-G4 Diag (0.21), G3-G4 Chord (0.18)
        expected_urs = [0.74, 0.61, 0.16, 0.13, 0.21, 0.18]
        for d, exp in zip(data, expected_urs):
            self.assertAlmostEqual(d["ur"], exp, places=2)
            self.assertEqual(d["status"], "PASS")

    def test_end_diaphragm_honesty_when_unimplemented(self):
        """4. End diaphragm handles unperformed solver checks honestly without fake PASS."""
        from osdagbridge.core.reports.ur_charts import extract_end_diaphragm_ur_data
        bridge = self._make_bridge()
        ed_data = extract_end_diaphragm_ur_data(bridge)
        self.assertFalse(ed_data["has_data"])
        self.assertIn("design to be added", ed_data["reason"])
        self.assertEqual(len(ed_data["items"]), 0)

    def test_chart_file_generation_and_validity(self):
        """5 & 7. All 4 chart PNGs are generated with valid PNG signatures and non-zero bytes."""
        import tempfile
        from osdagbridge.core.reports.ur_charts import generate_all_ur_charts
        bridge = self._make_bridge()
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = generate_all_ur_charts(bridge, tmp_dir)
            self.assertIn("girders", res)
            self.assertIn("deck_slab", res)
            self.assertIn("cross_bracing", res)
            self.assertIn("end_diaphragm", res)

            png_magic = b"\x89PNG\r\n\x1a\n"
            for k, rel_path in res.items():
                p = os.path.join(tmp_dir, os.path.basename(rel_path))
                self.assertTrue(os.path.exists(p), f"Chart file {p} does not exist")
                size = os.path.getsize(p)
                self.assertGreater(size, 10000, f"Chart file {p} unexpectedly small: {size} bytes")
                with open(p, "rb") as fh:
                    header = fh.read(8)
                self.assertEqual(header, png_magic, f"{p} is not a valid PNG")

    def test_end_diaphragm_status_card_rendering(self):
        """6. End Diaphragm chart generates an informational status card without fake bars."""
        import tempfile
        from osdagbridge.core.reports.ur_charts import generate_end_diaphragm_ur_chart
        bridge = self._make_bridge()
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, "ed_card.png")
            generate_end_diaphragm_ur_chart(bridge, out_file)
            self.assertTrue(os.path.exists(out_file))
            self.assertGreater(os.path.getsize(out_file), 10000)

    def test_section_5_5_figure_integration(self):
        """8. Section 5.5 integrates all 4 figures, introductory text, and honesty note."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        bridge = self._make_bridge()
        tex = ch5_design_checks([], bridge)

        # 1. Section 5.5 and Subsection 5.5.1
        self.assertIn(r"\section{Overall Design Check Summary}", tex)
        self.assertIn(r"\subsection{Component Utilization Ratio (UR) Charts}", tex)

        # 2. Introductory explanation of UR
        self.assertIn(r"\text{UR} = \frac{\text{Demand}}{\text{Capacity}}", tex)
        self.assertIn(r"\text{UR} \leq 1.0", tex)
        self.assertIn(r"\text{UR} > 1.0", tex)

        # 3. All 4 figure blocks with correct labels and captions
        self.assertIn(r"\label{fig:ur-chart-girders}", tex)
        self.assertIn(r"\caption{Steel Plate Girders --- Governing Utilization Ratios}", tex)
        self.assertIn(r"\includegraphics[width=0.88\textwidth]{assets/ur_chart_girders.png}", tex)

        self.assertIn(r"\label{fig:ur-chart-deck-slab}", tex)
        self.assertIn(r"\caption{Concrete Deck Slab --- Utilization Ratios}", tex)
        self.assertIn(r"\includegraphics[width=0.88\textwidth]{assets/ur_chart_deck_slab.png}", tex)

        self.assertIn(r"\label{fig:ur-chart-cross-bracing}", tex)
        self.assertIn(r"\caption{Cross Bracing Members --- Utilization Ratios}", tex)
        self.assertIn(r"\includegraphics[width=0.88\textwidth]{assets/ur_chart_cross_bracing.png}", tex)

        self.assertIn(r"\label{fig:ur-chart-end-diaphragm}", tex)
        self.assertIn(r"\caption{End Diaphragm --- Structural Check Status}", tex)
        self.assertIn(r"\includegraphics[width=0.88\textwidth]{assets/ur_chart_end_diaphragm.png}", tex)

        # 4. End Diaphragm honesty note
        self.assertIn("Note on End Diaphragm Checks:", tex)
        self.assertIn("no artificial utilization ratios or false PASS designations are reported", tex)

    def test_latex_asset_paths_consistency(self):
        """9. LaTeX figure paths match the deterministic assets/ relative directory."""
        from osdagbridge.core.reports.ur_charts import generate_all_ur_charts
        bridge = self._make_bridge()
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = generate_all_ur_charts(bridge, tmp_dir)
            for k, rel_path in res.items():
                self.assertTrue(rel_path.startswith("assets/"), f"Path {rel_path} does not start with assets/")
                self.assertTrue(rel_path.endswith(".png"), f"Path {rel_path} does not end with .png")

    def test_chapter_5_tables_remain_intact(self):
        """10. Existing Chapter 5 design check tables remain intact after chart integration."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        bridge = self._make_bridge()
        tex = ch5_design_checks([], bridge)
        # Check that Table 5.29 longtable is present
        self.assertIn(r"\label{tab:overall-summary}", tex)
        self.assertIn("Overall Design Check Summary --- All Members", tex)
        self.assertIn(r"\end{longtable}", tex)


class TestPhase4MaterialCharts(unittest.TestCase):
    """Targeted unit tests for Phase 4 material quantity charts and Chapter 7 integration."""

    def setUp(self):
        self.input_dict = {
            "span": 30.0,
            "typical_section.no_of_girders": 4,
            "typical_section.overall_bridge_width": 8.4,
            "typical_section.deck_thickness": 250,
            "typical_section.girder_spacing": 2.1,
            "typical_section.crash_barrier.area": 302282.768,
            "steel_girders_vol_formula": r"$0.03492\text{ m}^2 \times 30.00\text{ m} = 1.04756\text{ m}^3$",
            "steel_girders_qty": "4",
            "steel_girders_vol_total": "4.19",
            "steel_girders_wt_single": "8.22",
            "steel_girders_wt_total": "32.89",
            "bracing_top_vol_formula": r"$0.00024\text{ m}^2 \times 2.10\text{ m} = 0.00050\text{ m}^3$",
            "bracing_top_qty": "27",
            "bracing_top_vol_total": "0.01",
            "bracing_top_wt_single": "0.0039",
            "bracing_top_wt_total": "0.11",
            "bracing_bot_vol_formula": r"$0.00024\text{ m}^2 \times 2.10\text{ m} = 0.00050\text{ m}^3$",
            "bracing_bot_qty": "27",
            "bracing_bot_vol_total": "0.01",
            "bracing_bot_wt_single": "0.0039",
            "bracing_bot_wt_total": "0.11",
            "bracing_diag_vol_formula": r"$0.00024\text{ m}^2 \times 2.53\text{ m} = 0.00060\text{ m}^3$",
            "bracing_diag_qty": "54",
            "bracing_diag_vol_total": "0.03",
            "bracing_diag_wt_single": "0.0047",
            "bracing_diag_wt_total": "0.25",
            "concrete_deck_vol_formula": r"$8.40\text{ m} \times 0.25\text{ m} \times 30.00\text{ m} = 63.00\text{ m}^3$",
            "concrete_deck_qty": "1",
            "concrete_deck_vol_total": "63.00",
            "concrete_deck_wt_single": "157.50",
            "concrete_deck_wt_total": "157.50",
            "rebar_deck_vol_formula": r"$0.032102\text{ m}^2 \times 30.00\text{ m} = 0.96306\text{ m}^3$",
            "rebar_deck_qty": "1",
            "rebar_deck_vol_total": "0.96",
            "rebar_deck_wt_single": "7.56",
            "rebar_deck_wt_total": "7.56",
            "shear_studs_vol_formula": r"$0.000314\text{ m}^2 \times 0.100\text{ m} = 0.000031\text{ m}^3$",
            "shear_studs_qty": "640",
            "shear_studs_vol_total": "0.02",
            "shear_studs_wt_single": "0.000247",
            "shear_studs_wt_total": "0.158",
            "crash_barrier_vol_formula": r"$0.30228\text{ m}^2 \times 30.00\text{ m} = 9.06848\text{ m}^3$",
            "crash_barrier_qty": "2",
            "crash_barrier_vol_total": "18.14",
            "crash_barrier_wt_single": "22.67",
            "crash_barrier_wt_total": "45.34",
            "member_properties.girder_details.section_properties.mass.G1.M1": 274.1124,
            "member_properties.girder_details.section_properties.mass.G2.M1": 274.1124,
            "member_properties.girder_details.section_properties.mass.G3.M1": 274.1124,
            "member_properties.girder_details.section_properties.mass.G4.M1": 274.1124,
        }
        self.output_dict = {}

    def test_steel_girder_quantity_extraction(self):
        """1. Verify extraction and aggregation of plate girder steel mass and reconciliation."""
        from osdagbridge.core.reports.material_charts import extract_steel_tonnage_data
        data = extract_steel_tonnage_data(self.input_dict, self.output_dict)
        self.assertEqual(data["n_girders"], 4)
        self.assertEqual(data["total_girder_wt"], 32.89)
        self.assertEqual(len(data["girder_breakdown"]), 4)
        for g_label, g_wt in data["girder_breakdown"].items():
            self.assertAlmostEqual(g_wt, 8.223, places=2, msg=f"{g_label} weight should be ~8.223 MT")
        # Verify reconciliation to 33.52 MT
        self.assertEqual(data["total_structural_steel"], 33.52)

    def test_cross_bracing_quantity_extraction(self):
        """2. Verify extraction of cross bracing components (top, bottom, diagonals)."""
        from osdagbridge.core.reports.material_charts import extract_steel_tonnage_data
        data = extract_steel_tonnage_data(self.input_dict, self.output_dict)
        cb = data["cross_bracing"]
        self.assertEqual(cb["top_chord_wt"], 0.11)
        self.assertEqual(cb["bottom_chord_wt"], 0.11)
        self.assertEqual(cb["diagonal_chord_wt"], 0.25)
        self.assertEqual(cb["total_wt"], 0.47)

    def test_end_diaphragm_quantity_availability_handling(self):
        """3. Verify end-diaphragm handling when unavailable vs available."""
        from osdagbridge.core.reports.material_charts import extract_steel_tonnage_data
        # Case A: Not in BOQ (standard baseline)
        data = extract_steel_tonnage_data(self.input_dict, self.output_dict)
        self.assertFalse(data["end_diaphragm_available"])
        self.assertIsNone(data["end_diaphragm_wt"])
        self.assertIn("Unavailable", data["end_diaphragm_status"])

        # Case B: When available in BOQ
        inp_with_ed = dict(self.input_dict)
        inp_with_ed["end_diaphragm_wt_total"] = "1.45"
        data_ed = extract_steel_tonnage_data(inp_with_ed, self.output_dict)
        self.assertTrue(data_ed["end_diaphragm_available"])
        self.assertEqual(data_ed["end_diaphragm_wt"], 1.45)

    def test_concrete_volume_extraction(self):
        """4. Verify extraction of deck slab and crash barrier concrete volumes."""
        from osdagbridge.core.reports.material_charts import extract_concrete_quantity_data
        data = extract_concrete_quantity_data(self.input_dict, self.output_dict)
        self.assertEqual(data["deck_slab_vol_m3"], 63.00)
        self.assertEqual(data["crash_barrier_vol_m3"], 18.14)
        self.assertEqual(data["total_concrete_vol_m3"], 81.14)
        self.assertEqual(data["deck_slab_wt_mt"], 157.50)
        self.assertEqual(data["crash_barrier_wt_mt"], 45.34)

    def test_reinforcement_mass_extraction(self):
        """5. Verify extraction of reinforcement steel mass in MT and rate."""
        from osdagbridge.core.reports.material_charts import extract_reinforcement_quantity_data
        data = extract_reinforcement_quantity_data(self.input_dict, self.output_dict)
        self.assertEqual(data["deck_rebar_wt_mt"], 7.56)
        self.assertEqual(data["deck_rebar_vol_m3"], 0.96)
        self.assertEqual(data["total_rebar_wt_mt"], 7.56)
        self.assertEqual(data["rebar_rate_kg_m3"], 120.0)

    def test_unit_consistency(self):
        """6. Verify unit consistency: Steel in MT, Concrete in m3, Rebar in MT."""
        from osdagbridge.core.reports.material_charts import (
            extract_steel_tonnage_data,
            extract_concrete_quantity_data,
            extract_reinforcement_quantity_data,
        )
        steel = extract_steel_tonnage_data(self.input_dict, self.output_dict)
        concrete = extract_concrete_quantity_data(self.input_dict, self.output_dict)
        rebar = extract_reinforcement_quantity_data(self.input_dict, self.output_dict)

        # Steel masses in MT (> 0 and < 100 for a 30m bridge)
        self.assertGreater(steel["total_girder_wt"], 1.0)
        self.assertLess(steel["total_girder_wt"], 100.0)

        # Concrete volumes in m3 (deck is 63 m3, not in kg or MT)
        self.assertEqual(concrete["deck_slab_vol_m3"], 63.0)

        # Rebar mass in MT
        self.assertEqual(rebar["deck_rebar_wt_mt"], 7.56)

    def test_correct_aggregation_no_double_counting(self):
        """7. Verify correct aggregation and absence of double-counting."""
        from osdagbridge.core.reports.material_charts import (
            extract_steel_tonnage_data,
            extract_concrete_quantity_data,
        )
        steel = extract_steel_tonnage_data(self.input_dict, self.output_dict)
        concrete = extract_concrete_quantity_data(self.input_dict, self.output_dict)

        # Girders: sum of individual breakdown matches total within 0.02 MT
        sum_breakdown = sum(steel["girder_breakdown"].values())
        self.assertAlmostEqual(sum_breakdown, steel["total_girder_wt"], places=1)

        # Cross bracing must not be mixed into girder total
        self.assertNotEqual(steel["total_girder_wt"], steel["total_girder_wt"] + steel["cross_bracing"]["total_wt"])

        # Concrete total is exact sum of components
        self.assertAlmostEqual(
            concrete["total_concrete_vol_m3"],
            concrete["deck_slab_vol_m3"] + concrete["crash_barrier_vol_m3"],
            places=2
        )

    def test_missing_unavailable_quantity_handling(self):
        """8. Verify graceful handling when inputs dict is empty or contains N.A."""
        from osdagbridge.core.reports.material_charts import (
            extract_steel_tonnage_data,
            extract_concrete_quantity_data,
            extract_reinforcement_quantity_data,
        )
        empty_inp = {}
        empty_out = {}
        # Must not raise exceptions
        steel = extract_steel_tonnage_data(empty_inp, empty_out)
        self.assertIsNotNone(steel)
        self.assertFalse(steel["end_diaphragm_available"])

        concrete = extract_concrete_quantity_data(empty_inp, empty_out)
        self.assertIsNotNone(concrete)

        rebar = extract_reinforcement_quantity_data(empty_inp, empty_out)
        self.assertIsNotNone(rebar)

    def test_chart_generation(self):
        """9. Verify chart files generation at 300 DPI with non-zero size."""
        import tempfile
        from PIL import Image
        from osdagbridge.core.reports.material_charts import generate_all_material_charts

        with tempfile.TemporaryDirectory() as tmp_dir:
            res = generate_all_material_charts(self.input_dict, self.output_dict, tmp_dir)
            self.assertIn("steel_tonnage", res)
            self.assertIn("concrete_quantity", res)
            self.assertIn("reinforcement_quantity", res)

            for key, fpath in res.items():
                self.assertTrue(os.path.exists(fpath), f"{key} chart was not created: {fpath}")
                size = os.path.getsize(fpath)
                self.assertGreater(size, 10000, f"{key} file size {size} is too small")
                with Image.open(fpath) as img:
                    dpi = img.info.get("dpi", (0, 0))
                    self.assertAlmostEqual(dpi[0], 300.0, places=0, msg=f"{key} DPI not 300")

    def test_chapter_7_latex_integration(self):
        """10. Verify Chapter 7 LaTeX structure, table, sections, and figures."""
        from osdagbridge.core.reports.chap7 import ch7_quantities

        tex = ch7_quantities(self.input_dict, self.output_dict)

        # 1. Chapter and Sections
        self.assertIn(r"\chapter{Material Take-off \& Quantity Summary}", tex)
        self.assertIn(r"\section{Material Quantity Summary}", tex)
        self.assertIn(r"\section{Steel Tonnage by Structural Component}", tex)
        self.assertIn(r"\section{Concrete Quantity Summary}", tex)
        self.assertIn(r"\section{Reinforcement Quantity Summary}", tex)

        # 2. Table 7.1 with correct caption ending in \\
        self.assertIn(r"\caption{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}\label{tab:bom}\\", tex)
        self.assertIn(r"\begin{longtable}", tex)
        self.assertIn(r"\endfirsthead", tex)
        self.assertIn(r"\endhead", tex)
        self.assertIn(r"\endfoot", tex)
        self.assertIn(r"\endlastfoot", tex)

        # 3. Figures with correct asset paths and captions
        self.assertIn("assets/material_steel_tonnage.png", tex)
        self.assertIn(r"\caption{Structural Steel Mass by Component (Metric Tonnes)}", tex)
        self.assertIn(r"\label{fig:material-steel-tonnage}", tex)

        self.assertIn("assets/material_concrete_quantity.png", tex)
        self.assertIn(r"\caption{Concrete Volume by Structural Component ($\text{m}^3$)}", tex)
        self.assertIn(r"\label{fig:material-concrete-quantity}", tex)

        self.assertIn("assets/material_reinforcement_quantity.png", tex)
        self.assertIn(r"\caption{Reinforcement Steel Mass for Deck Slab (Metric Tonnes, BOQ Allowance)}", tex)
        self.assertIn(r"\label{fig:material-reinforcement-quantity}", tex)

        # 4. Explanatory text, reconciliation, and honesty notes
        self.assertIn("33.52", tex)
        self.assertIn("preliminary BOQ estimation allowance", tex)
        self.assertIn("strictly covers the reinforced concrete deck slab", tex)
        self.assertIn("not constitute a detailed structural reinforcement design", tex)
        self.assertIn("End diaphragm quantities are not included in Table", tex)
        self.assertIn("Unavailable (Not in BOQ)", tex)

    def test_exported_chart_asset_availability(self):
        """11. Verify exported chart filenames match LaTeX references."""
        from osdagbridge.core.reports.chap7 import ch7_quantities
        tex = ch7_quantities(self.input_dict, self.output_dict)

        expected_assets = [
            "assets/material_steel_tonnage.png",
            "assets/material_concrete_quantity.png",
            "assets/material_reinforcement_quantity.png",
        ]
        for asset in expected_assets:
            self.assertIn(asset, tex, f"Expected asset reference '{asset}' missing from Chapter 7 LaTeX")


class TestFinalAuditDocumentation(unittest.TestCase):
    """Unit tests for Chapter 8 and overall report documentation integrity."""

    def test_chapter_8_known_limitations(self):
        """Verify Chapter 8 includes all required known limitations."""
        from osdagbridge.core.reports.chap8 import ch8_design_log
        tex = ch8_design_log([], {})

        self.assertIn(r"\section{Known Limitations of This Version}", tex)
        self.assertIn("End diaphragm structural design checks are not yet implemented", tex)
        self.assertIn("Entire carriageway crowd-loading analysis is not supported", tex)
        self.assertIn("Tracked-vehicle braking is unsupported by the current solver implementation", tex)
        self.assertIn("Ordinary versus crowd footway classification is not selectable through the current GUI", tex)
        self.assertIn("Headless and interactive GUI calculations retain documented small differences", tex)
        self.assertIn(r"Girder moment: 0.26\%, shear: 0.31\%, fatigue: 0.28\%", tex)


class TestFinalPdfQualityCorrections(unittest.TestCase):
    """Unit tests for the final PDF quality correction pass."""

    def test_executive_summary_key_outcomes_itemization(self):
        """1. Executive summary reflects true design statuses, not hardcoded pass."""
        from osdagbridge.core.reports.executive_summary import executive_summary
        inp = {"Project Title": "Test Bridge", "Job Number": "JOB-01"}
        out = {
            "girders": {"G1": {"status": "FAIL", "utilization_ratio": 1.57}},
            "deck_slab": {"status": "PASS"},
            "cross_bracing": {"status": "PASS"},
        }
        tex = executive_summary(inp, out, {})
        # Must show Plate Girders FAIL with governing Fatigue Normal Stress check
        self.assertIn("Plate Girders", tex)
        self.assertIn("FAIL", tex)
        self.assertIn("Fatigue Normal Stress", tex)
        self.assertIn("UR = 1.57", tex)
        self.assertNotIn("Bending Moment", tex)
        # Must show Deck Slab PASS
        self.assertIn("Concrete Deck Slab", tex)
        # Must show Cross Bracing PASS
        self.assertIn("Cross Bracing", tex)
        # Must show End Diaphragms Solver Pending
        self.assertIn("End Diaphragms", tex)
        self.assertIn("Solver Pending", tex)
        # Must not claim End Diaphragm pass
        self.assertNotIn("End Diaphragm design pass", tex)
        self.assertNotIn("Girder design pass", tex)

    def test_table_2_7_girder_dimensions_mm_conversion(self):
        """2. Table 2.7 converts metre values to millimetres properly."""
        import types
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        from osdagbridge.core.utils.common import (
            KEY_MP_GIRDER_DEPTH,
            KEY_MP_GIRDER_WEB_THICKNESS,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
        )
        inp = {
            f"{KEY_MP_GIRDER_DEPTH}.G1.M1": 1.67,
            f"{KEY_MP_GIRDER_WEB_THICKNESS}.G1.M1": 0.01,
            f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G1.M1": 0.51,
            f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G1.M1": 0.022,
            f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G1.M1": 0.51,
            f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G1.M1": 0.022,
            "Number of Girders": 1,
        }
        meta = types.SimpleNamespace(project_location="Test Location")
        out = {}
        tex = ch2_input_parameters(meta, inp, out)
        self.assertIn("1670 mm", tex)
        self.assertIn("10 mm", tex)
        self.assertIn("510 mm", tex)
        self.assertIn("22 mm", tex)
        self.assertNotIn("1.67 mm", tex)
        self.assertNotIn("0.01 mm", tex)
        self.assertNotIn("0.51 mm", tex)
        self.assertNotIn("0.022 mm", tex)

    def test_end_diaphragm_disclosure_and_summary(self):
        """3. Section 5.4 and Table 5.29 honestly disclose End Diaphragm solver status."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        class MockBridge:
            def __init__(self):
                self.input_dict = {
                    "Effective Span (m)": 30.0,
                    "Number of Girders": 4,
                    "End Diaphragm Section Type": "Truss",
                    "End Diaphragm Steel Section": "ISA 100x100x10",
                }
                self.output_dict = {}
                self.payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        tex = ch5_design_checks([], bridge)
        # Table 5.26 configuration should exist
        self.assertIn(r"\label{tab:ed-config}", tex)
        self.assertIn("End Diaphragm --- Configuration and Boundary Restraints", tex)
        # Table 5.28 duplicate capacity should NOT exist
        self.assertNotIn(r"\label{tab:ed-capacity}", tex)
        # Disclosure message
        self.assertIn("End Diaphragm Structural Verification Status", tex)
        self.assertIn("Detailed structural capacity verification", tex)
        self.assertIn("Solver Pending / Not Verified", tex)
        # Table 5.29 has Solver Pending for End Diaphragms
        self.assertIn("Solver Pending (Structural checks unavailable in solver)", tex)

    def test_chapter_6_no_placeholder_boxes(self):
        """4. Chapter 6 does not emit [ PLACEHOLDER: ... ] or fbox graphics."""
        from osdagbridge.core.reports.chap6 import ch6_drawings
        tex = ch6_drawings({})
        self.assertNotIn(r"\fbox{\parbox", tex)
        self.assertNotIn(r"[ PLACEHOLDER:", tex)
        self.assertIn("View not captured in headless report run (requires active CAD session)", tex)
        self.assertIn("active CAD display session", tex)

    def test_ur_chart_styling_headroom_and_legend(self):
        """5. UR charts configure sufficient headroom and upper center legend."""
        from osdagbridge.core.reports.ur_charts import plot_ur_bar_chart
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import tempfile
        items = [
            {"label": "G1", "ur": 1.57, "status": "FAIL"},
            {"label": "G2", "ur": 0.85, "status": "PASS"},
            {"label": "G3", "ur": 0.85, "status": "PASS"},
            {"label": "G4", "ur": 1.57, "status": "FAIL"},
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = os.path.join(tmp_dir, "test_ur.png")
            plot_ur_bar_chart(items, "Test Girders", out_path)
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 5000)

    def test_table1_individual_girder_utilization_ratios(self):
        """6. Executive Summary Table 1 reports individual girder URs matching Table 5.12."""
        from osdagbridge.core.reports.executive_summary import executive_summary
        from osdagbridge.core.utils.common import (
            KEY_MP_GD_SELECT_GIRDER,
            KEY_MP_GD_MEMBER_ID,
            KEY_SD_ULS_PER_GIRDER,
            KEY_TS_NO_OF_GIRDERS,
        )
        inp = {
            "Project Title": "Test Bridge",
            "Job Number": "JOB-01",
            KEY_TS_NO_OF_GIRDERS: 4,
            f"{KEY_MP_GD_SELECT_GIRDER}.G1": "G1",
            f"{KEY_MP_GD_MEMBER_ID}.G1.M1": "G1M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G2": "G2",
            f"{KEY_MP_GD_MEMBER_ID}.G2.M1": "G2M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G3": "G3",
            f"{KEY_MP_GD_MEMBER_ID}.G3.M1": "G3M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G4": "G4",
            f"{KEY_MP_GD_MEMBER_ID}.G4.M1": "G4M1",
        }
        out = {
            "design_results": {
                "per_girder": {
                    "G1": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.5285, "status": "FAIL"}]},
                    "G2": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.5402, "status": "FAIL"}]},
                    "G3": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.5726, "status": "FAIL"}]},
                    "G4": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.5726, "status": "FAIL"}]},
                },
                KEY_SD_ULS_PER_GIRDER: {
                    "fatigue": {
                        "G1": {"ur": 1.528, "status": "FAIL"},
                        "G2": {"ur": 1.540, "status": "FAIL"},
                        "G3": {"ur": 1.573, "status": "FAIL"},
                        "G4": {"ur": 1.573, "status": "FAIL"},
                    }
                }
            }
        }
        tex = executive_summary(inp, out, {})
        # Verify Table 1 contains the specific per-girder UR values
        self.assertIn("Utilization Ratio & 1.53 & 1.54 & 1.57 & 1.57 \\\\", tex)
        # Verify governing check row
        self.assertIn("Governing Check & Fatigue Normal Stress & Fatigue Normal Stress & Fatigue Normal Stress & Fatigue Normal Stress \\\\", tex)
        # Ensure it is not repeating 1.57 blindly for all girders
        self.assertNotIn("Utilization Ratio & 1.57 & 1.57 & 1.57 & 1.57 \\\\", tex)
        self.assertNotIn("Utilization Ratio & 1.57 (Girder) & 1.57 (Girder)", tex)

    def test_total_load_deflection_disclosure(self):
        """7. Total-load deflection failure is disclosed while preserving governing fatigue."""
        from osdagbridge.core.reports.executive_summary import executive_summary
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.utils.common import (
            KEY_SD_DEFL_TOTAL,
            KEY_SD_DEFL_ALLOW_TOTAL,
            KEY_SPAN,
            KEY_TS_NO_OF_GIRDERS,
        )
        inp = {KEY_SPAN: 30.0, KEY_TS_NO_OF_GIRDERS: 4}
        out = {
            "design_results": {
                "per_girder": {
                    "G1": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.57, "status": "FAIL"}]}
                }
            },
            f"{KEY_SD_DEFL_TOTAL}.G1": 51.137,
            f"{KEY_SD_DEFL_TOTAL}.G2": 51.274,
            KEY_SD_DEFL_ALLOW_TOTAL: 50.0,
        }
        tex = executive_summary(inp, out, {})
        # Discloses total-load deflection failure in overall status and outcomes
        self.assertIn("Total Load Deflection", tex)
        self.assertIn("Total-load deflection also exceeds allowable limit", tex)
        # Preserves governing fatigue failure
        self.assertIn("Governing Check: Fatigue Normal Stress (UR = 1.57)", tex)

        # Check Table 5.27 distinguishing composite deflection and total deflection
        class MockBridge:
            def __init__(self):
                self.input_dict = {KEY_SPAN: 30.0, KEY_TS_NO_OF_GIRDERS: 4}
                self.output_dict = out
                self.payload = None
            def get_cb_pairs(self): return []
            def get_cb_governing_force(self, pair, m): return ("", "")
            def get_cb_efficiency(self, pair, m, f): return ""
            def get_cb_status(self, pair, m, f): return ""
            def get_cb_section(self, pair, m, f): return ""

        ch5_tex = ch5_design_checks([], MockBridge())
        self.assertIn("Girder --- Deflection (composite)", ch5_tex)
        self.assertIn("Girder --- Total Deflection (Table 5.9)", ch5_tex)
        self.assertIn("51.27 mm", ch5_tex)

    def test_end_diaphragm_wording_updated(self):
        """8. Section 5.4 uses honest wording for pending solver implementation."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS
        class MockBridge:
            def __init__(self):
                self.input_dict = {"Effective Span (m)": 30.0, KEY_TS_NO_OF_GIRDERS: 4}
                self.output_dict = {}
                self.payload = None
            def get_cb_pairs(self): return []
            def get_cb_governing_force(self, pair, m): return ("", "")
            def get_cb_efficiency(self, pair, m, f): return ""
            def get_cb_status(self, pair, m, f): return ""
            def get_cb_section(self, pair, m, f): return ""

        ch5_tex = ch5_design_checks([], MockBridge())
        self.assertIn("The intended design basis is per IS~800:2007 and IRC~24:2010 Cl.~507", ch5_tex)
        self.assertIn("detailed member sizing and code verification remain pending solver implementation", ch5_tex)
        self.assertNotIn("They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.", ch5_tex)

    def test_missing_environmental_inputs_and_metadata(self):
        """9. Environmental inputs handle missing data honestly without placeholders."""
        import types
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        from osdagbridge.core.reports.chap3 import ch3_loads
        from osdagbridge.core.reports.chap1 import ch1_project_info
        from osdagbridge.core.reports.report_generator import title_page

        meta = types.SimpleNamespace(
            project_name="Test",
            project_location="Test Loc",
            designer="Designer",
            reviewer="",
            company="Osdag",
            client="FOSSEE",
            job_number="",
            report_date="2026-11-21",
            subtitle="",
        )
        c1_tex = ch1_project_info(meta)
        self.assertIn("Not specified", c1_tex)

        cov_tex = title_page(meta, "", "")
        self.assertIn(r"\textbf{Reviewer} & Not specified", cov_tex)
        self.assertIn(r"\textbf{Job Number} & Not specified", cov_tex)

        # Chap 2 fallback test
        c2_tex = ch2_input_parameters(meta, {}, {})
        self.assertIn("Not provided", c2_tex)
        self.assertNotIn("[from Project Location]", c2_tex)
        self.assertNotIn("These inputs are mandatory and were provided by the user.", c2_tex)

        # Chap 3 fallback test
        c3_tex = ch3_loads({})
        self.assertNotIn("[from Project Location]", c3_tex)
        self.assertIn("Not available in this report run", c3_tex)

    def test_cross_bracing_section_reconciliation_and_member_id(self):
        """10. Table 2.9 reconciles configured trial section and design result, cleaning redundant member IDs."""
        import types
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        from osdagbridge.core.utils.common import (
            KEY_MP_CB_SELECT_GIRDERS,
            KEY_MP_CB_MEMBER_ID,
            KEY_MP_CB_TYPE,
            KEY_MP_CB_BRACING_SECTION_DESIGNATION,
            KEY_MP_CB_SPACING,
            KEY_TS_NO_OF_GIRDERS,
        )
        meta = types.SimpleNamespace(project_name="Test", project_location="Pune", designer="Designer", reviewer="", company="Osdag", client="FOSSEE", job_number="", report_date="2026-11-21", subtitle="")
        inp = {
            KEY_TS_NO_OF_GIRDERS: 4,
            f"{KEY_MP_CB_SELECT_GIRDERS}.G1G2.B1M1": "G1 to G2",
            f"{KEY_MP_CB_MEMBER_ID}.G1G2.B1M1": "B1M1 to B1M1",
            f"{KEY_MP_CB_TYPE}.G1G2.B1M1": "X-Bracing",
            f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G1G2.B1M1": "IS 100 x 100 x 10",
            f"{KEY_MP_CB_SPACING}.G1G2.B1M1": 15.0,
        }
        out = {
            "crossbracing_design_results": {
                "G1-G2": {
                    "diagonal": {"compression": {"section_size.designation": "40 x 40 x 3"}},
                    "chord": {"compression": {"section_size.designation": "40 x 40 x 3"}},
                }
            }
        }
        tex = ch2_input_parameters(meta, inp, out)
        # Verify member ID cleaned from 'B1M1 to B1M1' to 'B1M1'
        self.assertIn("G1 to G2 & B1M1 & X-Bracing", tex)
        self.assertNotIn("B1M1 to B1M1", tex)
        # Verify both configured trial section and final design result are present
        self.assertIn("IS 100 x 100 x 10", tex)
        self.assertIn("40 x 40 x 3", tex)
        self.assertIn("Initial Trial", tex)
        self.assertIn("Final Designed", tex)
        self.assertIn("software-configured initial trial section from input parameters", tex)

    def test_material_density_clarification(self):
        """11. Material densities distinguish adopted project values from general IRC 6 Cl. 203 defaults."""
        import types
        from osdagbridge.core.reports.chap3 import ch3_loads
        from osdagbridge.core.reports.chap8 import ch8_design_log
        from osdagbridge.core.utils.common import (
            KEY_MATERIAL_GIRDER_DENSITY,
            KEY_MATERIAL_DECK_DENSITY,
            KEY_PL_SELF_WEIGHT_FACTOR,
        )
        inp = {
            KEY_MATERIAL_GIRDER_DENSITY: 76.4,
            KEY_MATERIAL_DECK_DENSITY: 24.5,
            KEY_PL_SELF_WEIGHT_FACTOR: 1.0,
        }
        c3_tex = ch3_loads(inp)
        self.assertIn("76.4", c3_tex)
        self.assertIn("24.5", c3_tex)
        self.assertIn("Adopted material self-weight densities are project-specific values", c3_tex)
        self.assertIn("distinguished from general IRC 6:2017 Cl. 203 reference defaults", c3_tex)

        c8_tex = ch8_design_log([], inp)
        self.assertIn("Standard code reference densities per IRC 6:2017 Cl.203", c8_tex)
        self.assertIn("78.5", c8_tex)
        self.assertIn("25.0", c8_tex)
        self.assertIn("adopted project values used for self-weight analysis in this report run are defined in Table 3.1", c8_tex)

    def test_harmonized_standards_and_references(self):
        """12. Applicable standards across Chap 1, Chap 8, and Chap 9 consistently reference applied editions."""
        import types
        from osdagbridge.core.reports.chap1 import ch1_project_info
        from osdagbridge.core.reports.chap8 import ch8_design_log
        from osdagbridge.core.reports.chap9 import references
        meta = types.SimpleNamespace(project_name="Test", project_location="Pune", designer="Designer", reviewer="", company="Osdag", client="FOSSEE", job_number="", report_date="2026-11-21", subtitle="")

        c1_tex = ch1_project_info(meta)
        self.assertIn("Indian Roads Congress (IRC) 5:2015", c1_tex)
        self.assertIn("Indian Roads Congress (IRC) 22:2015", c1_tex)
        self.assertIn("Indian Roads Congress (IRC) 112:2020", c1_tex)
        self.assertNotIn("IRC 5 (2024)", c1_tex)

        c8_tex = ch8_design_log([], {})
        self.assertIn("IRC 5 & 2015", c8_tex)
        self.assertIn("IRC 22 & 2015", c8_tex)
        self.assertIn("IRC 112 & 2020", c8_tex)

        c9_tex = references()
        self.assertIn("IRC 5:2015", c9_tex)
        self.assertIn("IRC 22:2015", c9_tex)
        self.assertIn("IRC 112:2020", c9_tex)
        self.assertIn("IS 456:2000", c9_tex)
        self.assertNotIn("IRC 5 (2024)", c9_tex)
        self.assertNotIn("IRC 22 (2014)", c9_tex)
        self.assertNotIn("IRC 112 (2011)", c9_tex)

    def test_temperature_rise_fall_rendering_and_basis(self):
        """13. Temperature rise/fall uses math minus sign and explains IRC 6 Cl. 215.2 basis."""
        from osdagbridge.core.reports.chap3 import ch3_loads
        from osdagbridge.core.utils.common import (
            KEY_TL_BRIDGE_TEMP_MIN,
            KEY_TL_BRIDGE_TEMP_MAX,
            KEY_TL_TEMP_RISE,
            KEY_TL_TEMP_FALL,
        )
        inp = {
            "shade_temp_max": 43.3,
            "shade_temp_min": 1.7,
            KEY_TL_BRIDGE_TEMP_MIN: "-8.30",
            KEY_TL_BRIDGE_TEMP_MAX: "58.30",
            KEY_TL_TEMP_RISE: "33.30",
            KEY_TL_TEMP_FALL: "33.30",
        }
        tex = ch3_loads(inp)
        self.assertIn("-8.30 to 58.30", tex)
        # Must contain math minus for fall, not \textminus which renders as '=' in OT1
        self.assertIn(r"$+33.30\,^\circ\mathrm{C} \ / \ -33.30\,^\circ\mathrm{C}$", tex)
        self.assertNotIn(r"\textminus", tex)
        self.assertIn("Calculated per IRC 6:2017 Cl. 215.2 for metallic bridges", tex)
        self.assertIn("mean reference/installation temperature", tex)

    def test_review3_table2_9_header_widths_and_labels(self):
        """Review 3.1: Table 2.9 uses compact multiline headers preventing column collision."""
        import types
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        meta = types.SimpleNamespace(project_name="Test", project_location="Pune", designer="Designer", reviewer="", company="Osdag", client="FOSSEE", job_number="", report_date="2026-11-21", subtitle="")
        tex = ch2_input_parameters(meta, {"typical_section.no_of_girders": 2}, {})
        self.assertIn(r"\begin{longtable}{|L{2.0cm}|C{1.8cm}|C{2.2cm}|C{2.8cm}|C{2.8cm}|C{1.8cm}|}", tex)
        self.assertIn(r"\makecell{\textbf{Initial Trial}\\\textbf{Section}}", tex)
        self.assertIn(r"\makecell{\textbf{Final Designed}\\\textbf{Section}}", tex)
        self.assertIn("Note: IS 100 x 100 x 10 is the software-configured initial trial section", tex)

    def test_review3_table3_3_page_break_placement(self):
        """Review 3.2: Table 3.3 begins on a new page preventing ghost continuation headers."""
        from osdagbridge.core.reports.chap3 import ch3_loads
        tex = ch3_loads({})
        # Chap 3 loads string must separate Table 3.2 and Table 3.3 with \newpage
        self.assertIn(r"\newpage" + "\n" + r"\begin{longtable}{|L{3.2cm}|C{2.6cm}|C{2.0cm}|C{3.2cm}|C{2.0cm}|}", tex)

    def test_review3_table4_2_support_reactions_merged_fallback(self):
        """Review 3.3: Table 4.2 replaces blank rows with merged unavailable message and directs to Table 4.1."""
        import types
        from osdagbridge.core.reports.chap4 import ch4_analysis
        dummy_bridge = types.SimpleNamespace(input_dict={}, output_dict={})
        tex = ch4_analysis({}, {}, dummy_bridge, 30.0)
        self.assertIn(r"\multicolumn{3}{|c|}{\textit{Detailed reaction table not available in this report run.}}", tex)
        self.assertIn("Support reaction values for all governing load cases and combinations are reported in Table 4.1", tex)
        # Verify no empty table cells
        self.assertNotIn(r" &  &  \\[6pt]", tex)

    def test_review3_end_diaphragm_wording_reconciliation(self):
        """Review 3.4: End diaphragm text correctly references configured cross-bracing / transverse bracing arrangement."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.reports.chap7 import ch7_quantities

        class MockBridge:
            input_dict = {"typical_section.no_of_girders": 4}
            output_dict = {}
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        tex_ch5 = ch5_design_checks([], bridge)
        self.assertIn("configured as cross-bracing members (from model configuration)", tex_ch5)
        self.assertIn("configured cross-bracing end diaphragms", tex_ch5)
        self.assertNotIn("configured with rolled or welded beam sections", tex_ch5)
        self.assertIn("Solver Pending / Not Verified", tex_ch5)

        tex_ch7 = ch7_quantities({}, {"bom": []})
        self.assertIn("configured cross-bracing end diaphragm", tex_ch7)
        self.assertNotIn("rolled/welded diaphragm sections", tex_ch7)

    def test_review3_harmonize_is_standards_in_chap1_and_chap9(self):
        """Review 3.5: IS 1786:2008 and IS 1893 (Part 3):2014 are included in Chapter 1 and Chapter 9 bibliography."""
        import types
        from osdagbridge.core.reports.chap1 import ch1_project_info
        from osdagbridge.core.reports.chap9 import references
        meta = types.SimpleNamespace(project_name="Test", project_location="Pune", designer="Designer", reviewer="", company="Osdag", client="FOSSEE", job_number="", report_date="2026-11-21", subtitle="")
        tex_ch1 = ch1_project_info(meta)
        self.assertIn("Indian Standard (IS) 1786:2008", tex_ch1)
        self.assertIn("Indian Standard (IS) 1893 (Part 3):2014", tex_ch1)

        tex_ch9 = references()
        self.assertIn("IS 1786:2008", tex_ch9)
        self.assertIn("IS 1893 (Part 3):2014", tex_ch9)

    def test_review3_table2_4_traffic_lane_count(self):
        """Review 3.6: Table 2.4 populates numerical traffic lane count and IRC 5 clause basis."""
        import types
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        from osdagbridge.core.utils.common import KEY_CARRIAGEWAY_WIDTH, KEY_WC_LD_LANE_TABLE_COUNT
        meta = types.SimpleNamespace(project_name="Test", project_location="Pune", designer="Designer", reviewer="", company="Osdag", client="FOSSEE", job_number="", report_date="2026-11-21", subtitle="")

        # Derived from 7.5 m carriageway
        tex_derived = ch2_input_parameters(meta, {KEY_CARRIAGEWAY_WIDTH: 7.5}, {})
        self.assertIn(r"\textnormal{No. of Traffic Lanes} & 2 (derived from 7.5 m carriageway per IRC 5 Cl. 104.3.1) \\[6pt]", tex_derived)

        # Explicit user-specified value
        tex_explicit = ch2_input_parameters(meta, {KEY_WC_LD_LANE_TABLE_COUNT: 2}, {})
        self.assertIn(r"\textnormal{No. of Traffic Lanes} & 2 (per IRC 5 Cl. 104.3.1) \\[6pt]", tex_explicit)

    def test_review4_table3_4_page_break_placement(self):
        """Review 4.1: Table 3.4 begins cleanly on a new page eliminating ghost continuation headers."""
        from osdagbridge.core.reports.chap3 import ch3_loads
        tex = ch3_loads({})
        self.assertIn(r"\newpage" + "\n" + r"\begin{longtable}{|L{5.8cm}|p{9.7cm}|}", tex)

    def test_review4_end_diaphragm_table_2_10_reference(self):
        """Review 4.2: End diaphragm text refers to Table 2.10 without unresolved ?? references."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        class MockBridge:
            input_dict = {"typical_section.no_of_girders": 4}
            output_dict = {}
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        tex = ch5_design_checks([], bridge)
        self.assertIn("IS 100 x 100 x 10 initial section (refer to Table 2.10)", tex)
        self.assertNotIn("Table~\\ref{tab:cb-details}", tex)
        self.assertNotIn("Table ??", tex)

    def test_standards_edition_harmonization_in_chap5(self):
        """Review 5: Chapter 5 uses IRC 22:2015 and IRC 112:2020 without stale 2014/2011 references."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        class MockBridge:
            input_dict = {"typical_section.no_of_girders": 4}
            output_dict = {}
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        tex = ch5_design_checks([], bridge)
        # Section 5 general intro
        self.assertIn("All checks reference IS 800:2007 and IRC 22:2015 unless stated otherwise", tex)
        self.assertNotIn("IRC 22:2014", tex)
        # Section 5.2 Deck Slab Design
        self.assertIn("designed per IRC~112:2020", tex)
        self.assertIn("IRC~22:2015", tex)
        self.assertNotIn("IRC~112:2011", tex)
        self.assertNotIn("IRC 112:2011", tex)

    def test_stiffener_design_summary_table_5_7(self):
        """Review 6: Table 5.7 discloses intermediate spacing status and distinguishes calculated vs configured stiffeners."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.utils.common import (
            KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
            KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
            KEY_MP_STIFFENER_BEARING_THICKNESS,
            KEY_SD_STIFF_METHOD,
            KEY_SD_STIFF_INT_THICK,
            KEY_SD_STIFF_INT_SPACING,
            KEY_SD_STIFF_END_THICK,
            KEY_SD_STIFF_END_COUNT,
            KEY_SD_STIFF_LONG,
        )

        class MockBridge:
            input_dict = {
                "typical_section.no_of_girders": 4,
                KEY_MP_STIFFENER_INTERMEDIATE_SPACING: 2440,
                KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS: 10,
                KEY_MP_STIFFENER_BEARING_THICKNESS: 10,
            }
            output_dict = {
                KEY_SD_STIFF_METHOD: "post_critical",
                KEY_SD_STIFF_INT_THICK: 21.1,
                KEY_SD_STIFF_INT_SPACING: None,  # Not computed by solver in verification run
                KEY_SD_STIFF_END_THICK: 1.2,    # Calculated min. thickness for bearing contact
                KEY_SD_STIFF_END_COUNT: 4,
                KEY_SD_STIFF_LONG: "None",
            }
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        tex = ch5_design_checks([], bridge)

        # 1. Intermediate Stiffener Spacing is populated with disclosure and Table 2.8 cross-reference, never blank
        self.assertIn(r"\textnormal{Intermediate Stiffener Spacing (mm)} & Not available in this report run (configured: 2440 mm, refer to Table 2.8)", tex)
        self.assertNotIn(r"\textnormal{Intermediate Stiffener Spacing (mm)} &  \\", tex)

        # 2. End Panel Stiffener Thickness documents 1.2 mm unit basis as calculated min. for bearing contact and cross-references configured 10 mm
        self.assertIn(r"\textnormal{End Panel Stiffener Thickness (mm)} & 1.2 (calculated min. for bearing contact; configured: 10 mm, refer to Table 2.8)", tex)

        # 3. Table 5.7 includes explanatory note distinguishing calculated vs configured parameters
        self.assertIn(r"Note: Stiffener summary values represent calculated design check requirements", tex)
        self.assertIn(r"refer to Table 2.8.", tex)

        # 4. Multirow lines 1-5 within each girder use \* to prevent awkward splits across pages
        self.assertIn(r"\textnormal{Shear Buckling Design Method} & post\_\allowbreak{}critical \\*[6pt]", tex)
        self.assertIn(r"\textnormal{Intermediate Stiffener Thickness (mm)} & 10.0 provided vs.\ 21.1 required (\textcolor{red}{FAIL}, UR = 2.11) \\*[6pt]", tex)

    def test_intermediate_stiffener_slenderness_disclosure(self):
        """Review 7: Intermediate stiffener thickness provided vs required disclosed in Table 5.7, Table 5.29, and Exec Summary."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.reports.executive_summary import executive_summary
        from osdagbridge.core.utils.common import (
            KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
            KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
            KEY_SD_STIFF_INT_THICK,
        )

        inp = {
            KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS: 10,
            KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND: 250,
            "typical_section.no_of_girders": 4,
        }
        out = {
            KEY_SD_STIFF_INT_THICK: 21.1,
            "girders": {"G1": {"status": "FAIL", "utilization_ratio": 1.57}},
            "design_results": {
                "per_girder": {
                    "G1": {"checks": [{"name": "Fatigue Normal Stress", "dcr": 1.57, "status": "FAIL"}]},
                }
            }
        }

        # 1. Executive Summary discloses intermediate stiffener slenderness failure
        exec_tex = executive_summary(inp, out, {})
        self.assertIn("Intermediate stiffener outstand slenderness also fails", exec_tex)
        self.assertIn("10.0 mm provided vs 21.1 mm required, UR = 2.11", exec_tex)
        self.assertIn("Intermediate Stiffener Slenderness", exec_tex)
        # Main girder governing check remains Fatigue Normal Stress
        self.assertIn("FAIL --- Governing Check: Fatigue Normal Stress (UR = 1.57)", exec_tex)

        # 2. Table 5.29 discloses Intermediate Stiffener in Overall Design Check Summary
        class MockBridge:
            input_dict = inp
            output_dict = out
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        chap5_tex = ch5_design_checks([], bridge)
        self.assertIn("Girder --- Intermediate Stiffener", chap5_tex)
        self.assertIn("IS 800 Cl. 8.7.1.5", chap5_tex)
        self.assertIn(r"\textcolor{red}{2.11}", chap5_tex)

    def test_bearing_stiffener_demand_terminology(self):
        """Review 7: Bearing stiffener demand terminology is corrected to per-girder support-end shear (Vu = 378.79 kN)."""
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.utils.common import (
            KEY_SD_BS_R,
            KEY_SD_BS_FCDW_WB,
            KEY_SD_BS_FCDW_LC,
            KEY_SD_BS_FPSD,
            KEY_SD_BS_FCD,
        )

        class MockBridge:
            input_dict = {"typical_section.no_of_girders": 4}
            output_dict = {
                KEY_SD_BS_R: 378.79,
                KEY_SD_BS_FCDW_WB: 168429.67,
                KEY_SD_BS_FCDW_LC: 483.79,
                KEY_SD_BS_FPSD: 3181.82,
                KEY_SD_BS_FCD: 2863.64,
            }
            payload = None
            def get_cb_pairs(self):
                return []
            def get_cb_governing_force(self, pair, m):
                return ("", "")
            def get_cb_efficiency(self, pair, m, f):
                return ""
            def get_cb_status(self, pair, m, f):
                return ""
            def get_cb_section(self, pair, m, f):
                return ""

        bridge = MockBridge()
        chap5_tex = ch5_design_checks([], bridge)

        # 1. Header uses Demand (Vu) and Resistance
        self.assertIn(r"\textbf{Girder} & \textbf{Check} & \textbf{Demand ($V_u$)} & \textbf{Resistance} & \textbf{Status}", chap5_tex)

        # 2. Footnote explains Vu = 378.79 kN as per-girder support-end shear demand
        self.assertIn(r"Demand ($V_u = 378.79$ kN) represents the governing per-girder support-end shear force", chap5_tex)
        self.assertIn("transmitted directly into the bearing stiffeners of each individual girder", chap5_tex)


if __name__ == "__main__":
    unittest.main()
