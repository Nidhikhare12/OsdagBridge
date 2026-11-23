"""Unit and integration regression tests for geometry data normalization and footpath consistency.

Covers:
- Legacy carriageway_width and carriage_way_width aliases.
- Canonical key precedence over aliases.
- Missing structure type default.
- Missing median default.
- Missing skew angle default.
- Footpath None, One Side, Both Sides.
- Missing, zero, and invalid footpath count.
- Existing canonical configurations.
- Original input dictionary remains unchanged.
- End-to-end PDF compilation with pdflatex.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_FOOTPATH,
    KEY_STRUCTURE_TYPE,
    KEY_INCLUDE_MEDIAN,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    SKEW_ANGLE_DEFAULT,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT
from osdagbridge.core.reports.report_generator import (
    normalize_geometry_inputs,
    build_report_payload,
    generate_report,
    ReportMetadata,
    ReportOptions,
    ReportPayload,
    ReportRequest,
    ReportFigures,
)
from osdagbridge.core.reports.chap2 import ch2_input_parameters


class TestGeometryNormalization(unittest.TestCase):
    """Test unit behavior of normalize_geometry_inputs()."""

    def test_01_legacy_carriageway_width_alias(self):
        """carriageway_width maps to KEY_CARRIAGEWAY_WIDTH."""
        inp = {"carriageway_width": 7.5}
        norm = normalize_geometry_inputs(inp)
        self.assertEqual(norm[KEY_CARRIAGEWAY_WIDTH], 7.5)

    def test_02_legacy_carriage_way_width_alias(self):
        """carriage_way_width maps to KEY_CARRIAGEWAY_WIDTH."""
        inp = {"carriage_way_width": 7.5}
        norm = normalize_geometry_inputs(inp)
        self.assertEqual(norm[KEY_CARRIAGEWAY_WIDTH], 7.5)

    def test_03_canonical_key_precedence_over_aliases(self):
        """Canonical namespaced keys take precedence and are not overwritten."""
        inp = {
            KEY_CARRIAGEWAY_WIDTH: 8.5,
            "carriage_way_width": 7.5,
            "carriageway_width": 7.0,
            KEY_FOOTPATH: "One Side",
            "footpath": "Both Sides",
            KEY_SKEW_ANGLE: 0.0,
            "skew_angle": 10.0,
            KEY_STRUCTURE_TYPE: "Special Bridge",
            "structure_type": "Other Bridge",
            KEY_INCLUDE_MEDIAN: "Yes",
            "include_median": "No",
        }
        norm = normalize_geometry_inputs(inp)
        self.assertEqual(norm[KEY_CARRIAGEWAY_WIDTH], 8.5)
        self.assertEqual(norm[KEY_FOOTPATH], "One Side")
        self.assertEqual(norm[KEY_SKEW_ANGLE], 0.0)
        self.assertEqual(norm[KEY_STRUCTURE_TYPE], "Special Bridge")
        self.assertEqual(norm[KEY_INCLUDE_MEDIAN], "Yes")

    def test_04_missing_structure_type_default(self):
        """Missing structure type falls back to software default 'Highway Bridge'."""
        norm = normalize_geometry_inputs({})
        self.assertEqual(norm[KEY_STRUCTURE_TYPE], BASIC_INPUT_DICT.get(KEY_STRUCTURE_TYPE, "Highway Bridge"))

        # Explicit alias is respected
        norm2 = normalize_geometry_inputs({"structure_type": "Custom Bridge"})
        self.assertEqual(norm2[KEY_STRUCTURE_TYPE], "Custom Bridge")

    def test_05_missing_median_default(self):
        """Missing median falls back to software default 'No'."""
        norm = normalize_geometry_inputs({})
        self.assertEqual(norm[KEY_INCLUDE_MEDIAN], BASIC_INPUT_DICT.get(KEY_INCLUDE_MEDIAN, "No"))

        norm2 = normalize_geometry_inputs({"include_median": "Yes"})
        self.assertEqual(norm2[KEY_INCLUDE_MEDIAN], "Yes")

    def test_06_missing_skew_angle_default(self):
        """Missing skew angle falls back to SKEW_ANGLE_DEFAULT (0.0)."""
        norm = normalize_geometry_inputs({})
        self.assertEqual(norm[KEY_SKEW_ANGLE], SKEW_ANGLE_DEFAULT)

        # Explicit numeric 0 is preserved
        norm2 = normalize_geometry_inputs({"skew_angle": 0})
        self.assertEqual(norm2[KEY_SKEW_ANGLE], 0)

        # Explicit non-zero
        norm3 = normalize_geometry_inputs({"skew_angle": 12.5})
        self.assertEqual(norm3[KEY_SKEW_ANGLE], 12.5)

    def test_07_no_carriageway_fabrication(self):
        """When neither canonical nor alias carriageway width exists, it is not fabricated."""
        norm = normalize_geometry_inputs({})
        self.assertNotIn(KEY_CARRIAGEWAY_WIDTH, norm)

    def test_08_original_input_dictionary_remains_unchanged(self):
        """Original input dictionary is not mutated by normalization."""
        orig = {"carriage_way_width": 7.5, "footpath": "Both Sides"}
        norm = normalize_geometry_inputs(orig)
        self.assertNotIn(KEY_CARRIAGEWAY_WIDTH, orig)
        self.assertNotIn(KEY_FOOTPATH, orig)
        self.assertIn(KEY_CARRIAGEWAY_WIDTH, norm)
        self.assertIn(KEY_FOOTPATH, norm)


class TestFootpathConsistencyInChapter2(unittest.TestCase):
    """Test Table 2.2 and Table 2.4 footpath consistency in chap2.py."""

    def setUp(self):
        self.metadata = ReportMetadata(
            project_name="Test Bridge",
            project_location="Mumbai",
            designer="Engineer",
            client="NHAI",
            company="IIT Bombay",
        )

    def test_09_footpath_none_renders_na_in_table_2_4(self):
        """When Footpath is None, Table 2.4 renders N/A and does not show default 1.5 m."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "None",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_NO_OF_FOOTPATHS: 0,
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        # Table 2.2 should report None for Footpath
        self.assertIn(r"\textnormal{Footpath} & None \\", tex)
        # Table 2.4 must NOT claim 1.5 m is provided
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex)
        self.assertNotIn(r"1.5 m (IRC 5 Cl. 104.3.6 min: 1.5 m)", tex)

    def test_10_footpath_one_side_renders_width(self):
        """Configured width 1.5 m reports 1.5 m with IRC minimum note."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "One Side",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_NO_OF_FOOTPATHS: 1,
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Footpath} & One Side \\", tex)
        self.assertIn(r"\textnormal{Footpath Width (m)} & 1.5 m (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]", tex)

    def test_11_footpath_both_sides_renders_width(self):
        """When Footpath is Both Sides and count is 2, Table 2.4 renders width."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.8",
            KEY_TS_NO_OF_FOOTPATHS: 2,
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Footpath} & Both Sides \\", tex)
        self.assertIn(r"\textnormal{Footpath Width (m)} & 1.8 m (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]", tex)

    def test_11b_footpath_configured_width_2_0m(self):
        """Configured width 2.0 m reports 2.0 m with IRC minimum note."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "2.0",
            KEY_TS_NO_OF_FOOTPATHS: 2,
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Footpath Width (m)} & 2.0 m (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]", tex)

    def test_12_missing_footpath_count_renders_na(self):
        """When footpath count is missing, Table 2.4 renders N/A."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            # KEY_TS_NO_OF_FOOTPATHS omitted
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex)

    def test_13_zero_footpath_count_renders_na(self):
        """When footpath count is 0, Table 2.4 renders N/A."""
        inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_NO_OF_FOOTPATHS: 0,
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex)

    def test_14_invalid_footpath_count_renders_na(self):
        """When footpath count is non-numeric or negative, Table 2.4 renders N/A."""
        inputs_invalid = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_NO_OF_FOOTPATHS: "invalid",
        }
        tex = ch2_input_parameters(self.metadata, inputs_invalid)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex)

        inputs_negative = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_NO_OF_FOOTPATHS: -1,
        }
        tex_neg = ch2_input_parameters(self.metadata, inputs_negative)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex_neg)

    def test_14b_configured_footpath_missing_or_invalid_width_renders_na_not_available(self):
        """When footpath is configured but width is missing or invalid, report N/A (width not available)."""
        # Missing width key
        inputs_missing = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "One Side",
            KEY_TS_NO_OF_FOOTPATHS: 1,
        }
        tex_missing = ch2_input_parameters(self.metadata, inputs_missing)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A (width not available) \\[6pt]", tex_missing)
        self.assertNotIn(r"1.5 m (IRC 5 Cl. 104.3.6 min: 1.5 m)", tex_missing)

        # None or empty string width
        inputs_empty = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_NO_OF_FOOTPATHS: 2,
            KEY_TS_FOOTPATH_WIDTH: "",
        }
        tex_empty = ch2_input_parameters(self.metadata, inputs_empty)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A (width not available) \\[6pt]", tex_empty)

        # Invalid width string
        inputs_invalid = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "One Side",
            KEY_TS_NO_OF_FOOTPATHS: 1,
            KEY_TS_FOOTPATH_WIDTH: "not_a_number",
        }
        tex_invalid = ch2_input_parameters(self.metadata, inputs_invalid)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A (width not available) \\[6pt]", tex_invalid)

    def test_14c_infinite_footpath_width_renders_na_not_available(self):
        """Infinite footpath width is reported as N/A (width not available)."""
        import math
        # String 'inf'
        inputs_str_inf = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_NO_OF_FOOTPATHS: 2,
            KEY_TS_FOOTPATH_WIDTH: "inf",
        }
        tex_str_inf = ch2_input_parameters(self.metadata, inputs_str_inf)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A (width not available) \\[6pt]", tex_str_inf)
        self.assertNotIn(r"inf m (IRC 5 Cl. 104.3.6 min: 1.5 m)", tex_str_inf)

        # Float math.inf
        inputs_float_inf = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "One Side",
            KEY_TS_NO_OF_FOOTPATHS: 1,
            KEY_TS_FOOTPATH_WIDTH: math.inf,
        }
        tex_float_inf = ch2_input_parameters(self.metadata, inputs_float_inf)
        self.assertIn(r"\textnormal{Footpath Width (m)} & N/A (width not available) \\[6pt]", tex_float_inf)

    def test_15_legacy_aliases_in_chapter_2(self):
        """Legacy aliases carriage_way_width and footpath are normalized in Table 2.2."""
        inputs = {
            "span": "24.0",
            "carriage_way_width": 7.5,
            "footpath": "Both Sides",
            KEY_TS_NO_OF_FOOTPATHS: 2,
            KEY_TS_FOOTPATH_WIDTH: "1.5",
        }
        tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Carriageway Width (m)} & 7.5 m \\", tex)
        self.assertIn(r"\textnormal{Footpath} & Both Sides \\", tex)
        self.assertIn(r"\textnormal{Type of Structure} & Highway Bridge \\", tex)
        self.assertIn(r"\textnormal{Include Median} & No \\", tex)
        self.assertIn(r"\textnormal{Skew Angle (degrees)} & 0.0°", tex)


class TestFullReportCompilationWithNormalizedGeometry(unittest.TestCase):
    """Verify full end-to-end PDF report generation with normalized geometry and consistent footpaths."""

    def test_16_full_pdf_compilation(self):
        metadata = ReportMetadata(
            project_name="Geometry Normalization Test",
            project_location="Mumbai",
            designer="Tester",
            client="NHAI",
            company="IIT Bombay",
        )
        options = ReportOptions(
            sections=["inputs", "loads", "design_checks"],
            include_figures=False,
            include_toc=False,
            include_pdf=True,
        )
        # Pass legacy un-namespaced keys and Footpath: None
        inputs = {
            "geometry.span": "24.0",
            "carriage_way_width": 7.5,
            "footpath": "None",
            "typical_section.no_of_girders": "2",
            "typical_section.girder_spacing": "3.5",
            "typical_section.deck_overhang": "1.75",
            "typical_section.deck_thickness": "250.0",
            "typical_section.footpath_width": "1.5",
            "steel_girders_wt_total": "20.0",
        }
        figures = ReportFigures()

        with tempfile.TemporaryDirectory() as td:
            req = ReportRequest(
                metadata=metadata, options=options, output_dir=td, file_stem="geom_norm_test"
            )
            payload = build_report_payload(req, inputs, {})
            # Verify build_report_payload preserved original inputs
            self.assertNotIn(KEY_CARRIAGEWAY_WIDTH, inputs)
            # Verify payload inputs got normalized
            self.assertEqual(payload.inputs[KEY_CARRIAGEWAY_WIDTH], 7.5)
            self.assertEqual(payload.inputs[KEY_FOOTPATH], "None")
            self.assertEqual(payload.inputs[KEY_STRUCTURE_TYPE], "Highway Bridge")

            res = generate_report(payload, req)
            self.assertIsNotNone(res.pdf_path, "PDF path must not be None")
            self.assertTrue(os.path.isfile(res.pdf_path), "Compiled PDF file must exist")
            self.assertGreater(os.path.getsize(res.pdf_path), 5000, "Compiled PDF must be non-empty")

            tex_path = os.path.join(td, "geom_norm_test.tex")
            with open(tex_path, "r", encoding="utf-8") as f:
                tex_content = f.read()

            # Table 2.2 assertions
            self.assertIn(r"\textnormal{Carriageway Width (m)} & 7.5 m \\", tex_content)
            self.assertIn(r"\textnormal{Footpath} & None \\", tex_content)
            self.assertIn(r"\textnormal{Type of Structure} & Highway Bridge \\", tex_content)
            self.assertIn(r"\textnormal{Include Median} & No \\", tex_content)
            self.assertIn(r"\textnormal{Skew Angle (degrees)} & 0.0°", tex_content)

            # Table 2.4 assertions
            self.assertIn(r"\textnormal{Footpath Width (m)} & N/A \\[6pt]", tex_content)


if __name__ == "__main__":
    unittest.main()
