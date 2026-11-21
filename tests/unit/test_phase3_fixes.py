import unittest
from osdagbridge.core.reports.report_generator import ReportDataBridge
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap4 import ch4_analysis
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.report_utils import _fig_embed
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_GIRDER_DEPTH,
)


class TestPhase3Fixes(unittest.TestCase):
    def test_end_diaphragm_data_independence_in_bridge(self):
        """Verify ReportDataBridge accesses distinct End Diaphragm vs Cross Bracing results."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "2",
            KEY_TS_GIRDER_SPACING: "2.5",
            KEY_MP_GIRDER_DEPTH: "1.67",
        }
        output_dict = {
            "crossbracing_forces_dict": {
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN": 45.123,
                        "diag_compression_kN": 55.456,
                        "diag_compression_gov_lc": "BASIC_1",
                    }
                }
            },
            "end_diaphragm_forces_dict": {
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN": 120.789,
                        "diag_compression_kN": 140.321,
                        "diag_compression_gov_lc": "SEISMIC_1",
                    }
                }
            },
            "crossbracing_design_results": {
                "G1-G2": {
                    "diagonal": {
                        "compression": {
                            "section": "ISA 90x90x8",
                            "capacity_kN": 150.0,
                            "efficiency": 0.370,
                            "slenderness": 110.5,
                        }
                    }
                }
            },
            "end_diaphragm_design_results": {
                "G1-G2": {
                    "diagonal": {
                        "compression": {
                            "section": "ISA 150x150x12",
                            "capacity_kN": 350.0,
                            "efficiency": 0.401,
                            "slenderness": 85.2,
                        }
                    }
                }
            },
        }

        bridge = ReportDataBridge(output_dict, input_dict, None)

        # Cross Bracing accessors
        self.assertEqual(bridge.get_cb_section("G1-G2", "diagonal", "compression"), "ISA 90x90x8")
        self.assertEqual(bridge.get_cb_capacity("G1-G2", "diagonal", "compression"), "150.000")
        self.assertEqual(bridge.get_cb_efficiency("G1-G2", "diagonal", "compression"), "0.370")
        self.assertEqual(bridge.get_cb_slenderness("G1-G2", "diagonal"), "110.5")
        self.assertIn("PASS", bridge.get_cb_status("G1-G2", "diagonal", "compression"))
        self.assertEqual(bridge.get_cb_gov_lc("G1-G2", "diagonal", "compression"), "BASIC\\_\\allowbreak{}1")

        # End Diaphragm accessors
        self.assertEqual(bridge.get_ed_section("G1-G2", "diagonal", "compression"), "ISA 150x150x12")
        self.assertEqual(bridge.get_ed_capacity("G1-G2", "diagonal", "compression"), "350.000")
        self.assertEqual(bridge.get_ed_efficiency("G1-G2", "diagonal", "compression"), "0.401")
        self.assertEqual(bridge.get_ed_slenderness("G1-G2", "diagonal"), "85.2")
        self.assertIn("PASS", bridge.get_ed_status("G1-G2", "diagonal", "compression"))
        self.assertEqual(bridge.get_ed_gov_lc("G1-G2", "diagonal", "compression"), "SEISMIC\\_\\allowbreak{}1")

    def test_chapter5_end_diaphragm_tables_independent(self):
        """Verify Chapter 5 End Diaphragm tables render separate results and never reuse CB content."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "2",
            KEY_TS_GIRDER_SPACING: "2.5",
            KEY_MP_GIRDER_DEPTH: "1.67",
        }
        output_dict = {
            "crossbracing_forces_dict": {
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN": 45.0,
                        "diag_compression_kN": 50.0,
                        "diag_compression_gov_lc": "BASIC_1",
                    }
                }
            },
            "end_diaphragm_forces_dict": {
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN": 120.0,
                        "diag_compression_kN": 140.0,
                        "diag_compression_gov_lc": "SEISMIC_1",
                    }
                }
            },
            "crossbracing_design_results": {
                "G1-G2": {
                    "diagonal": {
                        "compression": {
                            "section": "ISA 90x90x8",
                            "capacity_kN": 150.0,
                            "efficiency": 0.333,
                            "slenderness": 110.0,
                        }
                    }
                }
            },
            "end_diaphragm_design_results": {
                "G1-G2": {
                    "diagonal": {
                        "compression": {
                            "section": "ISA 150x150x12",
                            "capacity_kN": 350.0,
                            "efficiency": 0.400,
                            "slenderness": 85.0,
                        }
                    }
                }
            },
        }

        bridge = ReportDataBridge(output_dict, input_dict, None)
        ch5_tex = ch5_design_checks([], bridge)

        # Both sections should appear
        self.assertIn(r"\section{Cross Bracing Design}", ch5_tex)
        self.assertIn(r"\section{End Diaphragm Design}", ch5_tex)

        # Cross bracing table should contain ISA 90x90x8
        self.assertIn("ISA 90x90x8", ch5_tex)
        # End diaphragm table should contain ISA 150x150x12
        self.assertIn("ISA 150x150x12", ch5_tex)

        # End diaphragm section must NOT reuse CB values:
        # Check that End Diaphragm capacity summary mentions 350.000 kN and SEISMIC_1
        ed_sec = ch5_tex.split(r"\section{End Diaphragm Design}")[1].split(r"\section{Overall Design Check Summary}")[0]
        self.assertIn("ISA 150x150x12", ed_sec)
        self.assertIn("350.000", ed_sec)
        self.assertIn("85.0", ed_sec)
        self.assertNotIn("ISA 90x90x8", ed_sec)

    def test_missing_design_status_handling(self):
        """Verify uncalculated transverse designs report NOT CALCULATED and do not claim PASS."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "2",
        }
        output_dict = {
            "crossbracing_forces_dict": {},
            "end_diaphragm_forces_dict": {},
            "crossbracing_design_results": {},
            "end_diaphragm_design_results": {},
        }
        bridge = ReportDataBridge(output_dict, input_dict, None)

        # Status must return NOT CALCULATED, not "" and not PASS
        self.assertEqual(bridge.get_cb_status("G1-G2", "diagonal", "compression"), "NOT CALCULATED")
        self.assertEqual(bridge.get_ed_status("G1-G2", "diagonal", "compression"), "NOT CALCULATED")

        ch5_tex = ch5_design_checks([], bridge)
        self.assertIn("NOT CALCULATED", ch5_tex)
        # End diaphragm capacity table should show NOT CALCULATED
        ed_sec = ch5_tex.split(r"\section{End Diaphragm Design}")[1]
        self.assertIn("NOT CALCULATED", ed_sec)

    def test_chapter3_seismic_and_wind_applicability(self):
        """Verify Chapter 3 distinguishes inapplicable seismic checks (Zone II) from uncalculated loads."""
        # Case A: Zone II, span <= 30m -> Not Applicable per IRC 6 Cl. 219.1
        input_dict_zone2 = {
            "seismic_zone": "Zone II",
            KEY_SPAN: "25.0",
        }
        ch3_tex_zone2 = ch3_loads(input_dict_zone2)
        self.assertIn("Not Applicable (Zone II, IRC:6 Cl. 219", ch3_tex_zone2)
        self.assertIn("Not Calculated", ch3_tex_zone2)  # wind force

        # Case B: Zone IV -> Not Calculated
        input_dict_zone4 = {
            "seismic_zone": "Zone IV",
            KEY_SPAN: "25.0",
        }
        ch3_tex_zone4 = ch3_loads(input_dict_zone4)
        self.assertIn("Zone IV", ch3_tex_zone4)
        self.assertNotIn("Not Applicable (Zone II", ch3_tex_zone4)

    def test_chapter4_reactions_table_population(self):
        """Verify Chapter 4 Reactions at Supports table populates real values from rxn_summary."""
        asum = {
            "load_cases": {
                "BASIC_COMBINATION_1": {"max_bm": 2500.0, "bm_girder": "G1", "bm_location": 12.5, "max_sf": 400.0, "sf_girder": "G1", "sf_location": 0.0},
            },
            "reactions": {
                "BASIC_COMBINATION_1": {"left_kN": 450.123, "right_kN": 450.123},
                "BASIC_COMBINATION_2": {"left_kN": 510.456, "right_kN": 505.789},
            }
        }
        bridge = ReportDataBridge({}, {KEY_SPAN: "25.0"}, None)
        ch4_tex = ch4_analysis(asum, {}, bridge, 25.0)

        # Reactions at Supports table should contain both load cases with left/right values
        self.assertIn(r"\caption{\textbf{Reactions at Supports}}", ch4_tex)
        self.assertIn("450.123", ch4_tex)
        self.assertIn("510.456", ch4_tex)
        self.assertIn("505.789", ch4_tex)
        self.assertNotIn(r""" &  &  \\[6pt]""", ch4_tex)

    def test_figure_placeholder_professional_notice(self):
        """Verify missing figure produces professional unavailable marker without fictitious diagram."""
        tex = _fig_embed(None, "Bridge 3D View")
        self.assertIn(r"\textbf{Figure Unavailable: } Bridge 3D View", tex)
        self.assertIn("figure export is not available", tex)
        self.assertNotIn("PLACEHOLDER:", tex)


if __name__ == "__main__":
    unittest.main()

