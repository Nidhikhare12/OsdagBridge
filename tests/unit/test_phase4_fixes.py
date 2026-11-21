import unittest
from osdagbridge.core.reports.report_generator import preamble, ReportDataBridge
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.reports.chap2 import ch2_input_parameters, _get_traffic_lanes
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap4 import ch4_analysis
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap6 import ch6_drawings
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chap8 import ch8_design_log
from osdagbridge.core.reports.chap9 import references
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GD_MEMBER_ID,
)


class TestPhase4Fixes(unittest.TestCase):
    def test_preamble_headheight_configured(self):
        """Verify preamble sets headheight to at least 26pt to prevent fancyhdr overflow."""
        tex = preamble("Test Project", "JOB-1", "2026-11-21", "Rev 0")
        self.assertIn("headheight=26pt", tex)

    def test_executive_summary_table1_column_width_budget(self):
        """Verify Table 1 columns fit within textwidth to prevent overfull hbox."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "2",
            f"{KEY_MP_GD_SELECT_GIRDER}.G1": "G1",
            f"{KEY_MP_GD_MEMBER_ID}.G1.M1": "G1M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G2": "G2",
            f"{KEY_MP_GD_MEMBER_ID}.G2.M1": "G2M1",
        }
        output_dict = {}
        tex = executive_summary(input_dict, output_dict, {})
        # For 2 girders, girder_col_cm should be 5.8cm (not 6.1cm which caused 11.8pt overfull)
        self.assertIn("C{5.8cm}", tex)
        self.assertNotIn("C{6.1cm}", tex)

    def test_chapter2_traffic_lanes_fallback_and_continuation_headers(self):
        """Verify traffic lane fallback per IRC 5 Cl. 104.3.1 and continuation headers."""
        input_dict = {
            KEY_CARRIAGEWAY_WIDTH: "7.5",
            KEY_TS_NO_OF_GIRDERS: "2",
            f"{KEY_MP_GD_SELECT_GIRDER}.G1": "G1",
            f"{KEY_MP_GD_MEMBER_ID}.G1.M1": "G1M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G2": "G2",
            f"{KEY_MP_GD_MEMBER_ID}.G2.M1": "G2M1",
        }
        lanes = _get_traffic_lanes(input_dict)
        self.assertEqual(lanes, "2")

        tex = ch2_input_parameters(type("Meta", (), {"project_location": "Delhi"})(), input_dict)
        self.assertIn(r"\caption[]{\textbf{Typical Section Details (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Components Details (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Girder General Information (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Member Properties: Cross Bracing Details (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Member Properties: End Diaphragm Details (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Shear Connector Details (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Partial Safety Factors (Continued)}}\\", tex)

    def test_chapter3_tables_continuation_and_safe_widths(self):
        """Verify all Chapter 3 tables have continuation headers and column width <= 15cm."""
        input_dict = {
            KEY_SPAN: "25.0",
            "seismic_zone": "Zone II",
        }
        tex = ch3_loads(input_dict)
        self.assertIn(r"\begin{longtable}{|L{5.5cm}|p{9.2cm}|}", tex)
        self.assertIn(r"\caption[]{\textbf{Dead Load -- Self Weight (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Vehicle Live Loads (LL) --- per IRC 6 (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Footway / Pedestrian Live Load (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Wind Load (WL) --- per IRC 6 (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Earthquake Load (EL) --- per IRC 6 (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Temperature Load (TL) --- per IRC 6 (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Load Combinations (Continued)}}\\", tex)

    def test_chapter4_demands_and_reactions_continuation(self):
        """Verify Chapter 4 analysis demands, reactions, and deflection continuation headers."""
        input_dict = {KEY_SPAN: "25.0", KEY_TS_NO_OF_GIRDERS: "2"}
        bridge = ReportDataBridge({}, input_dict, None)
        tex = ch4_analysis({}, {}, bridge, 25.0)
        self.assertIn(r"\caption[]{\textbf{Summary of Maximum Demands (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Reactions at Supports (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Deflection Summary (Live Load \& Total Load) (Continued)}}\\", tex)

    def test_chapter5_all_tables_continuation_and_code_editions(self):
        """Verify all longtables in Chapter 5 have continuation headers and updated codes."""
        input_dict = {
            KEY_SPAN: "25.0",
            KEY_TS_NO_OF_GIRDERS: "2",
            f"{KEY_MP_GD_SELECT_GIRDER}.G1": "G1",
            f"{KEY_MP_GD_MEMBER_ID}.G1.M1": "G1M1",
            f"{KEY_MP_GD_SELECT_GIRDER}.G2": "G2",
            f"{KEY_MP_GD_MEMBER_ID}.G2.M1": "G2M1",
        }
        bridge = ReportDataBridge({}, input_dict, None)
        tex = ch5_design_checks([], bridge)
        self.assertIn("IRC 22:2015", tex)
        self.assertIn("IRC~112:2020", tex)
        self.assertIn(r"\caption[]{\textbf{Girder Section Properties (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Girder Section Classification (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Moment Capacity Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Shear Capacity Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Interaction Checks (M-V and M-N) (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Lateral Torsional Buckling Check -- Construction Stage (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Stiffener Design Summary (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{End Panel Stiffener Checks (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Serviceability -- Deflection Checks (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Serviceability -- Maximum Stress Limitation (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Serviceability -- Fatigue Assessment (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Girder Design Summary (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Shear Connector Capacity (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Shear Connector Spacing (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Transverse Shear and Detailing Checks (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Deck Slab --- Loading and Geometry (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Deck Slab --- Flexure Check: Interior Panel (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Deck Slab --- Cantilever Overhang Flexure Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Deck Slab --- Punching Shear Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Crack Width Check (Deck Slab) (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{One-Way (Beam) Shear Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Reinforcement Detailing Summary (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Cross Bracing --- Connection and Section Properties (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Cross Bracing --- Slenderness Ratio Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Cross Bracing Design --- Capacity Summary (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{End Diaphragm --- Connection and Section Properties (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{End Diaphragm --- Slenderness Ratio Check (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{End Diaphragm Design --- Capacity Summary (Continued)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Overall Design Check Summary (Continued)}}\\", tex)

    def test_chapter7_table_caption_and_closed_group(self):
        """Verify Chapter 7 has proper longtable caption, continuation header, and closed group."""
        tex = ch7_quantities({})
        self.assertIn(r"\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}}\\", tex)
        self.assertIn(r"\caption[]{\textbf{Bill of Materials (Continued)}}\\", tex)
        self.assertIn(r"\endgroup", tex)

    def test_chapter8_and_chapter9_code_edition_alignment(self):
        """Verify code editions in Chapter 8 and 9 are standardized and groups are closed."""
        ch8_tex = ch8_design_log([], {})
        self.assertIn(r"\endgroup", ch8_tex)
        self.assertIn(r"\begin{tabular}{|C{2.0cm}|C{1.5cm}|L{10.8cm}|}", ch8_tex)
        self.assertIn("IRC 5", ch8_tex)
        self.assertIn("IRC 22", ch8_tex)

        ch9_tex = references()
        self.assertIn("IRC 5 (2015)", ch9_tex)
        self.assertIn("IRC 22 (2015)", ch9_tex)
        self.assertIn("IRC 112 (2020)", ch9_tex)


if __name__ == "__main__":
    unittest.main()
