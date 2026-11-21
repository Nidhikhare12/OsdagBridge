import unittest
from osdagbridge.core.reports.chap2 import _girder_tables
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.utils.common import (
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SPAN,
    KEY_SD_SECTION_PROP_AREA,
)


class TestPhase2Fixes(unittest.TestCase):
    def test_girder_dimension_unit_conversion_chap2(self):
        """Verify that girder dimensions in SI metres are rendered in millimetres."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "1",
            f"{KEY_MP_GIRDER_DEPTH}.G1.M1": 1.67,             # 1.67 m -> 1670 mm
            f"{KEY_MP_GIRDER_WEB_THICKNESS}.G1.M1": 0.01,         # 0.01 m -> 10 mm
            f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G1.M1": 0.51,      # 0.51 m -> 510 mm
            f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G1.M1": 0.022, # 0.022 m -> 22 mm
            f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G1.M1": 0.51,
            f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G1.M1": 0.022,
        }
        # _girder_tables returns a combined string with all girder tables
        tables_tex = _girder_tables(input_dict, 1)
        self.assertIn("1670 mm", tables_tex)
        self.assertIn("10 mm", tables_tex)
        self.assertIn("510 mm", tables_tex)
        self.assertIn("22 mm", tables_tex)
        self.assertNotIn("1.67 mm", tables_tex)
        self.assertNotIn("0.01 mm", tables_tex)

    def test_executive_summary_status_aggregation_fail(self):
        """Verify that failing fatigue check (UR ~ 1.58) yields FAIL and never PASS."""
        input_dict = {
            KEY_TS_NO_OF_GIRDERS: "1",
            KEY_SPAN: "25.0",
        }
        output_dict = {
            "design_results": {
                "per_girder": {
                    "G1": {
                        "checks": [
                            {"name": "Flexure", "dcr": 0.85, "status": "PASS"},
                            {"name": "Fatigue", "dcr": 1.58, "status": "FAIL"},
                        ]
                    }
                }
            },
            "deck_design_results": {"ur_bending": 0.75},
            "crossbracing_design_results": {},
            "end_diaphragm_design_results": {},
        }
        summary_tex = executive_summary(input_dict, output_dict, {})
        # Overall status must report FAIL with Fatigue
        self.assertIn("FAIL", summary_tex)
        self.assertIn("Fatigue", summary_tex)
        # Outcomes summary must show FAIL for Girder Design
        self.assertIn(r"\textbf{Girder Design:} \textcolor{red}{FAIL} (Max UR = 1.58)", summary_tex)
        self.assertIn(r"\textit{Failing: Fatigue}", summary_tex)
        # Outcomes summary must show NOT CALCULATED for bracing without fabrication
        self.assertIn(r"\textbf{Cross Bracing Design:} \textit{NOT CALCULATED}", summary_tex)
        # Outcomes summary must not claim Girder design pass
        self.assertNotIn("Girder design pass", summary_tex)

    def test_boq_girder_area_priority_and_crash_barrier(self):
        """Verify BOQ uses designed steel area (387 cm² = 0.0387 m²) and resolves crash barrier."""
        inputs = {
            KEY_SPAN: "25.0",
            KEY_TS_NO_OF_GIRDERS: "4",
            "typical_section.overall_bridge_width": "12.0",
            "member_properties.girder_details.section_properties.area": "0.03492",  # stale initial sizing
        }
        outputs = {
            KEY_SD_SECTION_PROP_AREA: 387.0,  # designed section area in cm²
            "design_results": {
                "A_steel_mm2": 38700.0,
            }
        }
        quantities = calculate_material_quantities(inputs, outputs)
        # Girder area formula must use 0.03870 m², not 0.03492 m²
        self.assertIn("0.03870", quantities["steel_girders_vol_formula"])
        # Crash barrier should not be N.A.
        self.assertNotEqual(quantities["crash_barrier_vol_formula"], "N.A.")
        self.assertNotEqual(quantities["crash_barrier_qty"], "N.A.")


if __name__ == "__main__":
    unittest.main()
