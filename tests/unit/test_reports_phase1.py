"""Unit and integration tests for Phase 1 report generator refactoring.

Covers:
- Centralized styles and geometry settings (styles.py).
- Reusable longtable header helper with repeated continuation headers (report_utils.py).
- Chapters 2, 3, and 5 longtable header repeating.
- Footer and preamble geometry without negative vertical spacing hacks.
- Complete LaTeX compilation test to verify valid document generation.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_utils import make_longtable_header
from osdagbridge.core.reports.report_generator import (
    preamble,
    generate_report,
    ReportPayload,
    ReportMetadata,
    ReportOptions,
    ReportFigures,
    ReportRequest,
)
from osdagbridge.core.reports.chap2 import ch2_input_parameters
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks


class TestReportStyles(unittest.TestCase):
    """Test styles.py constants and formatting definitions."""

    def test_geometry_constants_defined(self):
        self.assertEqual(styles.MARGIN_TOP, "1.0in")
        self.assertEqual(styles.MARGIN_BOTTOM, "1.2in")
        self.assertEqual(styles.MARGIN_LEFT, "1.0in")
        self.assertEqual(styles.MARGIN_RIGHT, "1.0in")
        self.assertEqual(styles.HEAD_HEIGHT, "18pt")
        self.assertEqual(styles.FOOT_SKIP, "36pt")

        geom = styles.get_geometry_latex()
        self.assertIn("top=1.0in", geom)
        self.assertIn("bottom=1.2in", geom)
        self.assertIn("footskip=36pt", geom)

    def test_color_definitions(self):
        self.assertEqual(styles.COLOR_OSDAG_GREEN_HEX, "91B014")
        self.assertEqual(styles.COLOR_OSDAG_GREEN_NAME, "osdagGreen")
        colors = styles.get_color_definitions_latex()
        self.assertIn("91B014", colors)
        self.assertIn("osdagGreen", colors)

    def test_table_spacing_constants(self):
        self.assertEqual(styles.TABCOLSEP_DEFAULT, "6pt")
        self.assertEqual(styles.ARRAY_STRETCH, "1.12")
        self.assertEqual(styles.EXTRA_ROW_HEIGHT, "0.6pt")
        self.assertIn("5\\baselineskip", styles.NEEDSPACE_THRESHOLD)

    def test_footer_notice(self):
        self.assertIn("Osdag", styles.INSTITUTION_FOOTER_TEXT)
        self.assertIn("FOSSEE", styles.INSTITUTION_FOOTER_TEXT)
        self.assertIn("Indian Institute of Technology Bombay", styles.INSTITUTION_FOOTER_TEXT)
        self.assertIn("Software default value", styles.SOFTWARE_DEFAULT_TEXT)


class TestMakeLongtableHeader(unittest.TestCase):
    """Test make_longtable_header helper in report_utils.py."""

    def test_basic_table_structure(self):
        col_spec = r"|C{3cm}|L{6cm}|"
        caption = r"\textbf{Test Table}"
        header_row = r"\textbf{Col 1} & \textbf{Col 2}"
        result = make_longtable_header(col_spec, caption, header_row, label="tab:test")

        self.assertIn(r"\begin{longtable}{|C{3cm}|L{6cm}|}", result)
        self.assertIn(r"\caption{\textbf{Test Table}}\label{tab:test}", result)
        self.assertIn(r"\endfirsthead", result)
        self.assertIn(r"\endhead", result)
        self.assertIn(r"\endfoot", result)
        self.assertIn(r"\endlastfoot", result)
        self.assertIn(r"continued from previous page", result)
        self.assertIn(header_row, result)

    def test_repeated_header_matches_first_header(self):
        col_spec = r"|c|c|c|"
        caption = "Three Columns"
        header_row = r"A & B & C"
        result = make_longtable_header(col_spec, caption, header_row)

        first_head_part = result.split(r"\endfirsthead")[0]
        second_head_part = result.split(r"\endfirsthead")[1].split(r"\endhead")[0]

        self.assertIn(header_row, first_head_part)
        self.assertIn(header_row, second_head_part)
        self.assertIn(r"\multicolumn{3}{r@{}}", result)

    def test_explicit_num_cols(self):
        col_spec = r"|C{2cm}|L{3cm}|"
        result = make_longtable_header(col_spec, "Title", "A & B", num_cols=2)
        self.assertIn(r"\multicolumn{2}{r@{}}", result)


class TestPreambleAndFooter(unittest.TestCase):
    """Test preamble geometry and footer definition."""

    def test_no_negative_vspace_in_preamble(self):
        p = preamble("Test Bridge", "JOB-01", "2026-11-21")
        self.assertNotIn(r"\vspace{-20pt}", p)
        self.assertNotIn(r"\vspace{-8pt}", p)

    def test_preamble_uses_styles(self):
        p = preamble("Test Bridge", "JOB-01", "2026-11-21")
        self.assertIn("footskip=36pt", p)
        self.assertIn("osdagGreen", p)
        self.assertIn(styles.TABCOLSEP_DEFAULT, p)
        self.assertIn(styles.ARRAY_STRETCH, p)

    def test_preamble_loads_array_package(self):
        p = preamble("Test Bridge", "JOB-01", "2026-11-21")
        self.assertIn(r"\usepackage{array}", p)


class TestChaptersRepeatedHeaders(unittest.TestCase):
    """Test that every longtable in Chapter 2, 3, and 5 contains repeated headers."""

    def setUp(self):
        self.metadata = ReportMetadata(
            project_name="Test Bridge Project",
            project_location="Mumbai",
            designer="Test Engineer",
            client="NHAI",
            company="IIT Bombay",
        )
        self.inputs = {
            "girder_type": "plate_girder",
            "span": 30.0,
            "carriage_way_width": 7.5,
            "num_girders": 3,
        }
        self.outputs = {}
        self.bridge = MagicMock()
        self.bridge.input_dict = self.inputs
        self.bridge.output_dict = self.outputs

    def test_chapter_2_longtables_have_endhead(self):
        content = ch2_input_parameters(self.metadata, self.inputs, self.outputs)
        lt_count = content.count(r"\begin{longtable}")
        endhead_count = content.count(r"\endhead")
        self.assertGreater(lt_count, 0)
        self.assertEqual(lt_count, endhead_count, "Every longtable in Chap 2 must have an \\endhead")

    def test_chapter_3_longtables_have_endhead(self):
        content = ch3_loads(self.inputs)
        lt_count = content.count(r"\begin{longtable}")
        endhead_count = content.count(r"\endhead")
        self.assertGreater(lt_count, 0)
        self.assertEqual(lt_count, endhead_count, "Every longtable in Chap 3 must have an \\endhead")

    def test_chapter_5_longtables_have_endhead(self):
        content = ch5_design_checks({}, self.bridge)
        lt_count = content.count(r"\begin{longtable}")
        endhead_count = content.count(r"\endhead")
        self.assertGreater(lt_count, 0)
        self.assertEqual(lt_count, endhead_count, "Every longtable in Chap 5 must have an \\endhead")


class TestReportCompilation(unittest.TestCase):
    """Test compiling a complete document through pdflatex."""

    def test_full_report_compiles_successfully(self):
        metadata = ReportMetadata(
            project_name="Phase 1 Verification Report",
            project_location="Mumbai",
            designer="FOSSEE Tester",
            client="FOSSEE",
            company="FOSSEE, IIT Bombay",
        )
        inputs = {
            "title": "Plate Girder Bridge",
            "total_length": 30.0,
            "carriage_way_width": 7.5,
            "num_girders": 3,
            "girder_spacing": 2.5,
            "deck_thickness": 220.0,
        }
        options = ReportOptions(
            sections=["inputs", "loads", "design_checks"],
            include_figures=False,
            include_toc=True,
            include_pdf=True,
        )
        figures = ReportFigures()
        payload = ReportPayload(
            metadata=metadata,
            options=options,
            inputs=inputs,
            analysis_summary={},
            design_checks=[],
            figures=figures,
            output_dict={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            request = ReportRequest(
                metadata=metadata,
                options=options,
                output_dir=tmpdir,
                file_stem="test_report",
            )
            res = generate_report(payload, request)

            self.assertIsNotNone(res.pdf_path, "generate_report must produce a pdf_path")
            self.assertTrue(os.path.isfile(res.pdf_path), "Compiled PDF file must exist")
            self.assertGreater(os.path.getsize(res.pdf_path), 1000, "Compiled PDF must be non-empty")


if __name__ == "__main__":
    unittest.main()
