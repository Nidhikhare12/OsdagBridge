r"""
Comprehensive Unit & Regression Tests for OsdagBridge LaTeX Report Enhancements
=============================================================================
Validates all six requirements specified in the project scope:
  1. Repeated Table Headers across page breaks (\endfirsthead / \endhead)
  2. Layout, Footer Overlap, and Vertical Spacing Fixes (Geometry & Footskip)
  3. Load & Geometry Table Refactoring (Separated Live Load & Footway tables)
  4. Utilization Ratio (Demand/Capacity) Summary Visualizations (UR = 1.0 line)
  5. Material Quantity Bar Charts (Structural Steel & Concrete vs. Rebar)
  6. Centralized Formatting & Style System (Single Source of Truth)
"""

import os
import re
import unittest
from unittest.mock import MagicMock

from osdagbridge.core.reports.styles import (
    COLOR_OSDAG_GREEN,
    COLOR_PASS,
    COLOR_WARN,
    COLOR_FAIL,
    COLOR_THRESHOLD_LINE,
    GEOMETRY_OPTIONS,
    build_longtable_header,
    get_latex_color_definitions,
    get_table_environment_settings,
    get_header_footer_styles
)
import osdagbridge.core.reports.theme as theme
from osdagbridge.core.reports.chart_generator import (
    generate_ur_summary_chart,
    generate_material_steel_chart,
    generate_concrete_vs_rebar_chart
)
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chap8 import ch8_design_log
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportFigures,
    ReportPayload,
    generate_report,
    preamble
)
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH
)


class TestReportEnhancements(unittest.TestCase):
    """Test suite verifying all report generator refactoring deliverables."""

    def test_01_centralized_styles_and_theme_alias(self):
        """Verify centralized styling constants and theme module aliasing."""
        self.assertEqual(COLOR_OSDAG_GREEN, "#91B014")
        self.assertEqual(COLOR_THRESHOLD_LINE, "#DC2626")
        self.assertEqual(theme.COLOR_OSDAG_GREEN, COLOR_OSDAG_GREEN)
        self.assertEqual(theme.GEOMETRY_OPTIONS, GEOMETRY_OPTIONS)

        # Check geometry includes safe footskip
        self.assertIn("footskip=14mm", GEOMETRY_OPTIONS)
        self.assertIn("a4paper", GEOMETRY_OPTIONS)

        # Verify LaTeX builder outputs
        colors_tex = get_latex_color_definitions()
        self.assertIn(r"\definecolor{osdagGreen}{HTML}{91B014}", colors_tex)
        self.assertIn(r"\definecolor{statusPass}{HTML}{15803D}", colors_tex)

        env_tex = get_table_environment_settings()
        self.assertIn(r"\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}", env_tex)

    def test_02_longtable_header_builder(self):
        """Verify repeated longtable header generator produces complete LaTeX headers."""
        header = build_longtable_header(
            caption="Test Summary",
            label="tab:test",
            header_rows=r"\textbf{Col 1} & \textbf{Col 2} \\[6pt]",
            col_count=2
        )
        self.assertIn(r"\caption{\textbf{Test Summary}} \label{tab:test} \\", header)
        self.assertIn(r"\endfirsthead", header)
        self.assertIn(r"\multicolumn{2}{c}{\small\textit{Test Summary (Continued)}}", header)
        self.assertIn(r"\endhead", header)
        self.assertIn(r"\multicolumn{2}{r}{\small\textit{Continued on next page...}}", header)
        self.assertIn(r"\endfoot", header)
        self.assertIn(r"\endlastfoot", header)

    def test_03_no_negative_footer_spacing(self):
        """Verify footer rule has no negative vspace that collides with table rows."""
        footer_tex = get_header_footer_styles("Project Alpha", "JOB-101", "2026-11-17", "Rev 0")
        # Ensure destructive negative spacing like \vspace{-20pt} or \vspace{-8pt} is not present
        self.assertNotIn(r"\vspace{-20pt}", footer_tex)
        self.assertNotIn(r"\vspace{-8pt}", footer_tex)
        self.assertIn("osdagGreen", footer_tex)
        self.assertIn("Project Alpha", footer_tex)

    def test_04_repeated_headers_across_all_chapters(self):
        r"""Verify that every single longtable in chapters 2, 3, 4, 5, 7, 8 contains \endhead."""
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src", "osdagbridge", "core", "reports")
        reports_dir = os.path.abspath(reports_dir)

        checked_chapters = ["chap2.py", "chap3.py", "chap4.py", "chap5.py", "chap7.py", "chap8.py"]
        total_longtables = 0
        total_endfirstheads = 0
        total_endheads = 0

        for chap in checked_chapters:
            fpath = os.path.join(reports_dir, chap)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            lt_count = content.count(r"\begin{longtable}")
            efh_count = content.count(r"\endfirsthead")
            eh_count = content.count(r"\endhead")

            self.assertGreater(lt_count, 0, f"{chap} must have at least one longtable")
            self.assertEqual(lt_count, efh_count, f"{chap}: mismatch between longtable ({lt_count}) and \\endfirsthead ({efh_count})")
            self.assertEqual(lt_count, eh_count, f"{chap}: mismatch between longtable ({lt_count}) and \\endhead ({eh_count})")

            total_longtables += lt_count
            total_endfirstheads += efh_count
            total_endheads += eh_count

        self.assertGreaterEqual(total_longtables, 50, "Total refactored longtables across chapters should exceed 50")
        self.assertEqual(total_longtables, total_endfirstheads)
        self.assertEqual(total_longtables, total_endheads)

    def test_05_load_table_refactoring(self):
        """Verify separation of Vehicle Live Loads and Footpath Live Loads in Chapter 3."""
        input_dict = {
            KEY_SPAN: "24.0",
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_LL_IRC_CLASS_SV: True,
            KEY_FOOTPATH: "Yes",
            KEY_TS_FOOTPATH_WIDTH: "1.50",
            "KEY_WC_LD_LANE_TABLE_COUNT": "2"
        }
        tex = ch3_loads(input_dict)

        # 1. Distinct tables
        self.assertIn(r"\caption{\textbf{Vehicle Live Loads (LL) --- IRC:6-2017 Specification}}", tex)
        self.assertIn(r"\caption{\textbf{Footway Live Load (Pedestrian Load) --- IRC:6-2017 Cl. 206}}", tex)

        # 2. Multi-column schema with Braking Load subcolumns
        self.assertIn(r"\multicolumn{3}{c|}{\textbf{Braking Load}}", tex)
        self.assertIn(r"\textbf{Considered?}", tex)
        self.assertIn(r"\textbf{Value (kN)}", tex)
        self.assertIn(r"\textbf{Eccentricity}", tex)

        # 3. Dynamic vehicle selection rows
        self.assertIn("Class A", tex)
        self.assertIn("Class 70R (Wheeled)", tex)
        self.assertIn("Class SV (Special Vehicle)", tex)

        # 4. Footpath table fields
        self.assertIn("Footpath Width, $w_{fp}$", tex)
        self.assertIn("Design Pedestrian Pressure", tex)
        self.assertIn("IRC 6:2017 Clause 206.1", tex)

    def test_06_ur_summary_chart_generation(self):
        """Verify programmatic generation of the UR summary chart with threshold line."""
        output_dict = {
            "overall_utilization_ratio": "0.85",
            "design_results": {
                "per_girder": {
                    "G1": {"checks": {"flexure": {"ur": "0.78"}}},
                    "G2": {"checks": {"flexure": {"ur": "0.82"}}}
                }
            },
            "deck_design_results": {"deck_max_ur": "0.65"},
            "cb_governing_ur": "0.55",
            "ed_governing_ur": "0.45"
        }
        png_bytes = generate_ur_summary_chart(output_dict)
        self.assertIsInstance(png_bytes, bytes)
        self.assertGreater(len(png_bytes), 1000)
        # Check standard PNG magic header
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_07_material_takeoff_charts_generation(self):
        """Verify programmatic generation of Chapter 7 material quantity charts."""
        inputs = {
            "steel_girders_wt_total": "18.50",
            "bracing_top_wt_total": "0.80",
            "bracing_bot_wt_total": "0.75",
            "bracing_diag_wt_total": "1.20",
            "steel_ed_wt_total": "0.90",
            "shear_studs_wt_total": "0.35",
            "concrete_deck_vol_total": "32.40",
            "rebar_deck_wt_total": "4.15"
        }
        steel_png = generate_material_steel_chart(inputs)
        conc_png = generate_concrete_vs_rebar_chart(inputs)

        self.assertTrue(steel_png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(conc_png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(steel_png), 1000)
        self.assertGreater(len(conc_png), 1000)

    def test_08_chapter_7_figure_embedding(self):
        """Verify Chapter 7 embeds figures when provided in fig_paths."""
        inputs = {"steel_girders_vol_formula": "A x L"}
        fig_paths = {
            "steel_quantities": "images/steel_quantities.png",
            "concrete_vs_rebar": "images/concrete_vs_rebar.png"
        }
        tex = ch7_quantities(inputs, fig_paths)
        self.assertIn(r"\includegraphics[width=0.88\textwidth]{images/steel_quantities.png}", tex)
        self.assertIn(r"\includegraphics[width=0.84\textwidth]{images/concrete_vs_rebar.png}", tex)
        self.assertIn(r"\label{fig:steel-tonnage-breakdown}", tex)
        self.assertIn(r"\label{fig:concrete-vs-rebar}", tex)

    def test_09_full_report_tex_assembly(self):
        """Verify end-to-end report generation outputs valid .tex with all chapters."""
        meta = ReportMetadata(
            project_name="Bridge Screening Verification",
            project_location="Mumbai, Maharashtra",
            designer="Lead Bridge Engineer",
            client="NHAI / Ministry of Road Transport",
            company="Osdag Structural Laboratory",
            job_number="OB-2026-001",
            report_date="2026-11-17"
        )
        opts = ReportOptions(
            include_toc=True,
            include_figures=True,
            include_pdf=True,
            sections=['loads', 'analysis', 'design_checks', 'drawings']
        )
        payload = ReportPayload(
            metadata=meta,
            options=opts,
            inputs={
                KEY_SPAN: "20.0",
                KEY_TS_NO_OF_GIRDERS: "3",
                KEY_LL_IRC_CLASS_A: True,
                KEY_LL_IRC_70R_WHEELED: True,
                KEY_FOOTPATH: "Yes"
            },
            analysis_summary={},
            design_checks=[],
            figures=ReportFigures(),
            output_dict={
                "overall_design_status": "PASS",
                "overall_utilization_ratio": "0.76",
                "governing_check": "Shear Buckling Check"
            }
        )
        req = ReportRequest(
            metadata=meta,
            options=opts,
            output_dir="tmp_test_report",
            file_stem="Test_Report"
        )
        res = generate_report(payload, req)

        self.assertIsNotNone(res.tex_path)
        self.assertTrue(os.path.exists(res.tex_path))

        with open(res.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Check key sections are present
        self.assertIn(r"\chapter{Loads and Load Combinations}", tex_content)
        self.assertIn(r"\chapter{Analysis Results}", tex_content)
        self.assertIn(r"\chapter{Material Take-off \& Quantity Summary}", tex_content)
        self.assertIn(r"\end{document}", tex_content)

        # Cleanup
        if os.path.exists(res.tex_path):
            os.remove(res.tex_path)
        if os.path.exists("tmp_test_report"):
            import shutil
            shutil.rmtree("tmp_test_report")


if __name__ == "__main__":
    unittest.main()
