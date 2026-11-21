import os
import unittest
import tempfile

from osdagbridge.core.reports.report_generator import ReportDataBridge, preamble
from osdagbridge.core.reports import styles
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chart_generator import (
    generate_ur_charts,
    generate_material_quantity_charts,
)
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
)


class TestPhase5Fixes(unittest.TestCase):
    def test_centralized_styles_module(self):
        """Verify styles.py provides geometry, colors, table presets, and continuation headers."""
        self.assertIn("a4paper", styles.GEOMETRY_OPTIONS)
        self.assertIn("headheight=26pt", styles.GEOMETRY_OPTIONS)
        self.assertEqual(styles.PRIMARY_GREEN, "91B014")
        self.assertEqual(styles.COLOR_OSDAG_GREEN, "#91B014")
        self.assertEqual(styles.COLOR_THRESHOLD, "#e41a1c")
        
        doc_s = styles.document_style()
        self.assertIn(r"\definecolor{osdagGreen}{HTML}{91B014}", doc_s)
        self.assertIn(r"\setlength{\tabcolsep}", doc_s)
        
        cap = styles.longtable_continuation_caption("My Table")
        self.assertIn(r"\caption[]{\textbf{My Table (Continued)}}\\", cap)

        # Status badge derivation
        self.assertEqual(styles.format_status_badge("PASS"), "PASS")
        self.assertIn(r"\textcolor{red}{FAIL}", styles.format_status_badge("FAIL"))
        self.assertIn("NOT CALCULATED", styles.format_status_badge("NOT CALCULATED"))
        self.assertIn("NOT APPLICABLE", styles.format_status_badge("NOT APPLICABLE"))

    def test_preamble_uses_centralized_geometry(self):
        """Verify report_generator.preamble consumes styles.GEOMETRY_OPTIONS."""
        tex = preamble("Project", "JOB-1", "Date", "Rev 0")
        self.assertIn(styles.GEOMETRY_OPTIONS, tex)

    def test_chapter3_live_load_and_footway_tables_separated(self):
        """Verify Chapter 3 has separate tables for Vehicle Live Loads and Footway Load."""
        input_dict = {
            KEY_SPAN: "25.0",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_LL_IRC_CLASS_A: "1",
            KEY_LL_IRC_70R_WHEELED: "1",
        }
        tex = ch3_loads(input_dict)
        self.assertIn(r"\caption{\textbf{Vehicle Live Loads (LL) --- per IRC 6}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Vehicle Live Loads (LL) --- per IRC 6 (Continued)}}\\", tex)
        self.assertIn(r"\caption{\textbf{Footway / Pedestrian Live Load --- per IRC 6}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Footway / Pedestrian Live Load (Continued)}}\\", tex)
        self.assertIn("Class A", tex)
        self.assertIn("Class 70R (Wheeled)", tex)
        self.assertIn("Centrifugal Force", tex)
        self.assertIn("Straight Alignment", tex)
        self.assertIn("kN", tex)

    def test_ur_charts_generation(self):
        """Verify programmatic generation of UR summary charts with PASS/FAIL and missing handling."""
        output_dict = {
            "design_results": {
                "per_girder": {
                    "G1": {"checks": [{"name": "Moment", "dcr": 0.75, "status": "PASS"}]},
                    "G2": {"checks": [{"name": "Fatigue", "dcr": 1.58, "status": "FAIL"}]},
                },
                "deck_design": {}
            }
        }
        bridge = ReportDataBridge(output_dict, {KEY_SPAN: "25.0", KEY_TS_NO_OF_GIRDERS: "2"}, None)
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = generate_ur_charts(bridge, tmp_dir)
            self.assertIn("ur_summary", res)
            self.assertTrue(os.path.exists(res["ur_summary"]))
            self.assertGreater(os.path.getsize(res["ur_summary"]), 1000)

    def test_material_quantity_charts_generation(self):
        """Verify BOQ charts generate separate steel tonnage and concrete volume / rebar plots."""
        inputs = {
            "steel_girders_wt_total": "15.36",
            "bracing_top_wt_total": "1.20",
            "bracing_bot_wt_total": "1.10",
            "bracing_diag_wt_total": "1.50",
            "concrete_deck_vol_total": "53.12",
            "rebar_deck_wt_total": "5.31",
            "shear_studs_wt_total": "0.45",
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = generate_material_quantity_charts(inputs, tmp_dir)
            self.assertIn("boq_steel_tonnage", res)
            self.assertIn("boq_materials", res)
            self.assertTrue(os.path.exists(res["boq_steel_tonnage"]))
            self.assertTrue(os.path.exists(res["boq_materials"]))
            self.assertGreater(os.path.getsize(res["boq_steel_tonnage"]), 1000)
            self.assertGreater(os.path.getsize(res["boq_materials"]), 1000)

    def test_chapters_embed_figures_when_provided(self):
        """Verify ch5_design_checks and ch7_quantities embed figures when present in fig_paths."""
        fig_paths = {
            "ur_summary": "images/ur_summary_chart.png",
            "boq_steel_tonnage": "images/steel_tonnage_breakdown.png",
            "boq_materials": "images/materials_deck_summary.png",
        }
        bridge = ReportDataBridge({}, {KEY_SPAN: "25.0", KEY_TS_NO_OF_GIRDERS: "2"}, None)
        ch5_tex = ch5_design_checks([], bridge, fig_paths=fig_paths)
        self.assertIn("ur_summary_chart.png", ch5_tex)
        self.assertIn(r"\label{fig:ur_summary}", ch5_tex)

        ch7_tex = ch7_quantities({}, fig_paths=fig_paths)
        self.assertIn("steel_tonnage_breakdown.png", ch7_tex)
        self.assertIn("materials_deck_summary.png", ch7_tex)
        self.assertIn(r"\label{fig:boq_steel_tonnage}", ch7_tex)
        self.assertIn(r"\label{fig:boq_materials}", ch7_tex)


if __name__ == "__main__":
    unittest.main()

