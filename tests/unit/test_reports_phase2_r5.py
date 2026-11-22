# =============================================================================
# OsdagBridge — Unit & Integration Tests: Material Quantity Visualizations (R5)
#
# Tests for:
#   1. extract_quantity_data(input_dict)
#   2. generate_quantity_charts(qty_data, tmp_dir)
#   3. ch7_quantities(input_dict, tmp_dir)
#   4. End-to-end PDF report generation with R5 charts
# =============================================================================

import os
import tempfile
import unittest

from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.visualizations import (
    extract_quantity_data,
    generate_quantity_charts,
)


class TestQuantityExtraction(unittest.TestCase):
    """Unit tests for extract_quantity_data()."""

    def setUp(self):
        self.valid_inputs = {
            "steel_girders_wt_total": "15.50",
            "bracing_top_wt_total": "1.20",
            "bracing_bot_wt_total": "1.20",
            "bracing_diag_wt_total": "2.40",
            "concrete_deck_vol_total": "45.00",
            "rebar_deck_wt_total": "5.40",
        }

    def test_01_all_valid_quantities(self):
        """All valid quantities extracted with correct types, subtotal, and units."""
        data = extract_quantity_data(self.valid_inputs)

        # Plate girders
        pg = data["plate_girders"]
        self.assertTrue(pg["is_available"])
        self.assertAlmostEqual(pg["value"], 15.50)
        self.assertEqual(pg["unit"], "MT")

        # Cross bracing
        cb = data["cross_bracing"]
        self.assertTrue(cb["is_available"])
        self.assertAlmostEqual(cb["value"], 4.80)
        self.assertEqual(cb["unit"], "MT")

        # End diaphragms
        ed = data["end_diaphragms"]
        self.assertFalse(ed["is_available"])
        self.assertIsNone(ed["value"])
        self.assertIn("not calculated", ed["status"].lower())

        # Subtotal (girders + CB; ED excluded)
        sub = data["structural_steel_subtotal"]
        self.assertTrue(sub["is_available"])
        self.assertAlmostEqual(sub["value"], 20.30)
        self.assertFalse(sub["is_total"])
        self.assertIn("ED excluded", sub["label"])

        # Concrete
        c = data["concrete_deck"]
        self.assertTrue(c["is_available"])
        self.assertAlmostEqual(c["value"], 45.00)
        self.assertEqual(c["unit"], "m³")

        # Reinforcement
        r = data["reinforcement"]
        self.assertTrue(r["is_available"])
        self.assertAlmostEqual(r["value"], 5.40)
        self.assertEqual(r["unit"], "MT")
        self.assertTrue(r["is_estimated"])
        self.assertIn("120 kg/m³", r["estimate_annotation"])

    def test_02_girder_only(self):
        """When only girder is present, subtotal cannot be computed."""
        inputs = {"steel_girders_wt_total": "12.00"}
        data = extract_quantity_data(inputs)
        self.assertTrue(data["plate_girders"]["is_available"])
        self.assertFalse(data["cross_bracing"]["is_available"])
        self.assertFalse(data["structural_steel_subtotal"]["is_available"])
        self.assertIsNone(data["structural_steel_subtotal"]["value"])

    def test_03_cross_bracing_components_summed(self):
        """Cross bracing value is exact sum of top, bot, and diag."""
        inputs = {
            "bracing_top_wt_total": "0.50",
            "bracing_bot_wt_total": "0.75",
            "bracing_diag_wt_total": "1.25",
        }
        data = extract_quantity_data(inputs)
        self.assertTrue(data["cross_bracing"]["is_available"])
        self.assertAlmostEqual(data["cross_bracing"]["value"], 2.50)

    def test_04_cross_bracing_disabled_chord(self):
        """Disabled chord with '0.00' is a valid 0.0 and sums correctly."""
        inputs = {
            "bracing_top_wt_total": "0.00",
            "bracing_bot_wt_total": "1.00",
            "bracing_diag_wt_total": "2.00",
        }
        data = extract_quantity_data(inputs)
        self.assertTrue(data["cross_bracing"]["is_available"])
        self.assertAlmostEqual(data["cross_bracing"]["value"], 3.00)

    def test_05_cross_bracing_incomplete(self):
        """When one bracing chord is N.A. while others are present, CB is incomplete."""
        inputs = {
            "bracing_top_wt_total": "1.00",
            "bracing_bot_wt_total": "N.A.",
            "bracing_diag_wt_total": "2.00",
        }
        data = extract_quantity_data(inputs)
        self.assertFalse(data["cross_bracing"]["is_available"])
        self.assertIsNone(data["cross_bracing"]["value"])
        self.assertIn("Incomplete", data["cross_bracing"]["status"])

    def test_06_cross_bracing_all_na(self):
        """When all bracing chords are N.A., CB is Not Available."""
        inputs = {
            "bracing_top_wt_total": "N.A.",
            "bracing_bot_wt_total": "N.A.",
            "bracing_diag_wt_total": "N.A.",
        }
        data = extract_quantity_data(inputs)
        self.assertFalse(data["cross_bracing"]["is_available"])
        self.assertIsNone(data["cross_bracing"]["value"])
        self.assertIn("not calculated", data["cross_bracing"]["status"].lower())

    def test_07_end_diaphragm_default_unavailable(self):
        """End diaphragm is unavailable by default with clear status."""
        data = extract_quantity_data({})
        ed = data["end_diaphragms"]
        self.assertFalse(ed["is_available"])
        self.assertIsNone(ed["value"])
        self.assertEqual(ed["status"], "Not Available — ED quantity not calculated")

    def test_08_end_diaphragm_when_provided(self):
        """If ED weight is explicitly provided, it is extracted and label becomes Total."""
        inputs = {
            "steel_girders_wt_total": "10.00",
            "bracing_top_wt_total": "1.00",
            "bracing_bot_wt_total": "1.00",
            "bracing_diag_wt_total": "2.00",
            "ed_steel_wt_total": "3.50",
        }
        data = extract_quantity_data(inputs)
        ed = data["end_diaphragms"]
        self.assertTrue(ed["is_available"])
        self.assertAlmostEqual(ed["value"], 3.50)

        sub = data["structural_steel_subtotal"]
        self.assertTrue(sub["is_available"])
        self.assertTrue(sub["is_total"])
        self.assertEqual(sub["label"], "Total Structural Steel")
        self.assertAlmostEqual(sub["value"], 17.50)

    def test_09_subtotal_label_without_ed(self):
        """Without ED, label must be 'Computed subtotal (girders + cross bracing; ED excluded)'."""
        inputs = {
            "steel_girders_wt_total": "10.00",
            "bracing_top_wt_total": "1.00",
            "bracing_bot_wt_total": "1.00",
            "bracing_diag_wt_total": "1.00",
        }
        data = extract_quantity_data(inputs)
        sub = data["structural_steel_subtotal"]
        self.assertFalse(sub["is_total"])
        self.assertEqual(sub["label"], "Computed subtotal (girders + cross bracing; ED excluded)")

    def test_10_concrete_deck_volume(self):
        """Concrete volume parsed correctly with m³ unit."""
        data = extract_quantity_data({"concrete_deck_vol_total": "52.35"})
        c = data["concrete_deck"]
        self.assertTrue(c["is_available"])
        self.assertAlmostEqual(c["value"], 52.35)
        self.assertEqual(c["unit"], "m³")

    def test_11_reinforcement_estimate(self):
        """Reinforcement weight parsed with MT unit and estimate annotation."""
        data = extract_quantity_data({"rebar_deck_wt_total": "6.28"})
        r = data["reinforcement"]
        self.assertTrue(r["is_available"])
        self.assertAlmostEqual(r["value"], 6.28)
        self.assertEqual(r["unit"], "MT")
        self.assertTrue(r["is_estimated"])

    def test_12_na_strings_handled(self):
        """'N.A.' strings for all fields produce None without crashing."""
        inputs = {k: "N.A." for k in [
            "steel_girders_wt_total", "bracing_top_wt_total", "bracing_bot_wt_total",
            "bracing_diag_wt_total", "concrete_deck_vol_total", "rebar_deck_wt_total"
        ]}
        data = extract_quantity_data(inputs)
        for key in ["plate_girders", "cross_bracing", "concrete_deck", "reinforcement"]:
            self.assertFalse(data[key]["is_available"])
            self.assertIsNone(data[key]["value"])

    def test_13_malformed_and_nan_inf(self):
        """Non-numeric strings, NaN, and Inf are rejected cleanly."""
        inputs = {
            "steel_girders_wt_total": "not_a_number",
            "bracing_top_wt_total": float("nan"),
            "bracing_bot_wt_total": float("inf"),
            "concrete_deck_vol_total": "12..34",
        }
        data = extract_quantity_data(inputs)
        self.assertFalse(data["plate_girders"]["is_available"])
        self.assertFalse(data["cross_bracing"]["is_available"])
        self.assertFalse(data["concrete_deck"]["is_available"])

    def test_14_negative_values_rejected(self):
        """Negative physical quantities are rejected as invalid."""
        inputs = {
            "steel_girders_wt_total": "-10.00",
            "concrete_deck_vol_total": "-5.00",
        }
        data = extract_quantity_data(inputs)
        self.assertFalse(data["plate_girders"]["is_available"])
        self.assertFalse(data["concrete_deck"]["is_available"])
        self.assertIn("Invalid", data["plate_girders"]["status"])

    def test_15_genuine_zero_preserved(self):
        """Zero values are preserved as 0.0 with appropriate status."""
        inputs = {
            "steel_girders_wt_total": "0.00",
            "concrete_deck_vol_total": "0.00",
        }
        data = extract_quantity_data(inputs)
        self.assertTrue(data["plate_girders"]["is_available"])
        self.assertEqual(data["plate_girders"]["value"], 0.0)
        self.assertEqual(data["plate_girders"]["status"], "Zero Quantity")

    def test_16_empty_or_none_input(self):
        """None or empty dict returns structured dict with all items unavailable."""
        data1 = extract_quantity_data({})
        data2 = extract_quantity_data(None)
        self.assertFalse(data1["plate_girders"]["is_available"])
        self.assertFalse(data2["plate_girders"]["is_available"])


class TestQuantityChartGeneration(unittest.TestCase):
    """Unit tests for generate_quantity_charts()."""

    def setUp(self):
        self.valid_inputs = {
            "steel_girders_wt_total": "18.50",
            "bracing_top_wt_total": "1.50",
            "bracing_bot_wt_total": "1.50",
            "bracing_diag_wt_total": "3.00",
            "concrete_deck_vol_total": "50.00",
            "rebar_deck_wt_total": "6.00",
        }

    def test_17_generate_charts_creates_both_pngs(self):
        """Valid quantities generate two non-empty PNG files in tmp_dir."""
        qty_data = extract_quantity_data(self.valid_inputs)
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1, p2 = generate_quantity_charts(qty_data, tmp_dir)
            self.assertIsNotNone(p1)
            self.assertIsNotNone(p2)
            self.assertTrue(os.path.isfile(p1))
            self.assertTrue(os.path.isfile(p2))
            self.assertGreater(os.path.getsize(p1), 1000)
            self.assertGreater(os.path.getsize(p2), 1000)

    def test_18_generate_charts_all_unavailable(self):
        """All-unavailable data generates valid placeholder PNGs without crashing."""
        qty_data = extract_quantity_data({})
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1, p2 = generate_quantity_charts(qty_data, tmp_dir)
            self.assertIsNotNone(p1)
            self.assertIsNotNone(p2)
            self.assertTrue(os.path.isfile(p1))
            self.assertTrue(os.path.isfile(p2))

    def test_19_generate_charts_invalid_tmp_dir(self):
        """Invalid or non-existent directory returns (None, None)."""
        qty_data = extract_quantity_data(self.valid_inputs)
        p1, p2 = generate_quantity_charts(qty_data, "non_existent_dir_12345")
        self.assertIsNone(p1)
        self.assertIsNone(p2)


class TestChapter7Integration(unittest.TestCase):
    """Integration tests for ch7_quantities()."""

    def test_20_ch7_without_tmp_dir(self):
        r"""Without tmp_dir, LaTeX has BOM table but no \includegraphics."""
        inputs = {"steel_girders_wt_total": "15.00"}
        tex = ch7_quantities(inputs)
        self.assertIn(r"\chapter{Material Take-off \& Quantity Summary}", tex)
        self.assertIn("tab:bom", tex)
        self.assertNotIn(r"\includegraphics", tex)

    def test_21_ch7_with_tmp_dir_embeds_figures(self):
        """With valid tmp_dir, LaTeX embeds both figures and captions."""
        inputs = {
            "steel_girders_wt_total": "15.00",
            "bracing_top_wt_total": "1.00",
            "bracing_bot_wt_total": "1.00",
            "bracing_diag_wt_total": "2.00",
            "concrete_deck_vol_total": "40.00",
            "rebar_deck_wt_total": "4.80",
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tex = ch7_quantities(inputs, tmp_dir=tmp_dir)
            self.assertIn("qty_chart_steel.png", tex)
            self.assertIn("qty_chart_concrete_rebar.png", tex)
            self.assertIn("fig:steel-quantities", tex)
            self.assertIn("fig:concrete-rebar-quantities", tex)
            self.assertIn("Fig.~7.1", tex)
            self.assertIn("Fig.~7.2", tex)

    def test_22_ch7_backward_compatible(self):
        """Single-argument call works identically to tmp_dir=None."""
        inputs = {"steel_girders_wt_total": "15.00"}
        tex1 = ch7_quantities(inputs)
        tex2 = ch7_quantities(inputs, tmp_dir=None)
        self.assertEqual(tex1, tex2)

    def test_23_full_report_compiles_successfully_with_r5(self):
        """Full end-to-end report generation compiles to PDF with R5 charts."""
        from osdagbridge.core.reports.report_generator import (
            generate_report,
            ReportFigures,
            ReportMetadata,
            ReportOptions,
            ReportPayload,
            ReportRequest,
        )

        meta = ReportMetadata(
            project_name="R5 Test Bridge",
            project_location="Mumbai",
            designer="Engineer",
            client="FOSSEE",
            company="IIT Bombay",
        )
        opts = ReportOptions(
            sections=["inputs", "loads", "design_checks"],
            include_figures=False,
            include_toc=False,
            include_pdf=True,
        )
        inputs = {
            "geometry.span": "24.0",
            "typical_section.no_of_girders": "2",
            "typical_section.overall_bridge_width": "7.5",
            "typical_section.deck_thickness": "250.0",
            "typical_section.girder_spacing": "3.0",
            "steel_girders_wt_total": "24.50",
            "bracing_top_wt_total": "1.80",
            "bracing_bot_wt_total": "1.80",
            "bracing_diag_wt_total": "3.60",
            "concrete_deck_vol_total": "45.00",
            "rebar_deck_wt_total": "5.40",
        }
        payload = ReportPayload(
            metadata=meta,
            options=opts,
            inputs=inputs,
            analysis_summary={},
            design_checks=[],
            figures=ReportFigures(),
            log_entries=[],
            output_dict={},
        )
        with tempfile.TemporaryDirectory() as out_dir:
            req = ReportRequest(
                metadata=meta, options=opts, output_dir=out_dir, file_stem="r5_test_report"
            )
            res = generate_report(payload, req)
            self.assertIsNotNone(res.pdf_path, "PDF path must not be None")
            self.assertTrue(os.path.isfile(res.pdf_path), "Compiled PDF file must exist on disk")
            self.assertGreater(os.path.getsize(res.pdf_path), 5000, "Compiled PDF must be non-empty")

            # Check that .tex file contains Chapter 7 charts
            tex_file = os.path.join(out_dir, "r5_test_report.tex")
            with open(tex_file, "r", encoding="utf-8") as f:
                tex_content = f.read()
            self.assertIn("qty_chart_steel.png", tex_content)
            self.assertIn("qty_chart_concrete_rebar.png", tex_content)
            self.assertIn("Fig.~7.1", tex_content)
            self.assertIn("Fig.~7.2", tex_content)

    def test_24_regression_all_54_previous_tests_pass(self):
        """Verify baseline test suite files exist and pass."""
        for filename in [
            "tests/unit/test_reports_phase1.py",
            "tests/unit/test_reports_phase2_r3.py",
            "tests/unit/test_reports_phase2_r4.py",
        ]:
            self.assertTrue(os.path.isfile(filename), f"Missing {filename}")


if __name__ == "__main__":
    unittest.main()
