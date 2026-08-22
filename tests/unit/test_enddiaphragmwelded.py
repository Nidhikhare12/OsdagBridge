import unittest
from unittest.mock import MagicMock

from osdagbridge.core.bridge_types.plate_girder.enddiaphragmwelded import EndDiaphragmWelded
from osdagbridge.core.utils.common import (
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_SYMMETRY,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)
from osdagbridge.core.utils.connect import (
    design_dict_plate_girder,
    run_calculation,
)


class TestEndDiaphragmWelded(unittest.TestCase):
    def setUp(self):
        self.mock_bridge = MagicMock()
        self.mock_bridge.input_dict = {
            KEY_TS_NO_OF_GIRDERS: 3,
            KEY_TS_GIRDER_SPACING: 2.5,
        }
        self.mock_bridge.additional_inputs = {
            KEY_MP_ED_TYPE: "Welded Beam",
            KEY_MP_ED_TOTAL_DEPTH: 1000.0,
            KEY_MP_ED_WEB_THICKNESS: 10.0,
            KEY_MP_ED_TOP_FLANGE_WIDTH: 250.0,
            KEY_MP_ED_TOP_FLANGE_THICKNESS: 14.0,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH: 250.0,
            KEY_MP_ED_BOTTOM_FLANGE_THICKNESS: 14.0,
            KEY_MP_ED_SYMMETRY: "Symmetric",
        }
        self.mock_bridge.result_data = {
            "girders": {
                "G1": {"nodes": [1, 2], "index": 0},
                "G2": {"nodes": [3, 4], "index": 1},
                "G3": {"nodes": [5, 6], "index": 2},
            },
            "members": {
                "101": [1, 3],  # G1-G2 start edge
                "102": [2, 4],  # G1-G2 end edge
                "103": [3, 5],  # G2-G3 start edge
                "104": [4, 6],  # G2-G3 end edge
            },
            "loadcases": ["SW", "DL", "LL_Special"],
            "forces": {
                "SW": {
                    "101": {"Vy_i": 15000.0, "Vy_j": 15000.0, "Mz_i": 20000.0, "Mz_j": 20000.0},
                    "102": {"Vy_i": 18000.0, "Vy_j": 18000.0, "Mz_i": 24000.0, "Mz_j": 24000.0},
                    "103": {"Vy_i": 14000.0, "Vy_j": 14000.0, "Mz_i": 19000.0, "Mz_j": 19000.0},
                    "104": {"Vy_i": 16000.0, "Vy_j": 16000.0, "Mz_i": 22000.0, "Mz_j": 22000.0},
                },
                "DL": {
                    "101": {"Vy_i": 35000.0, "Vy_j": 35000.0, "Mz_i": 50000.0, "Mz_j": 50000.0},
                    "102": {"Vy_i": 32000.0, "Vy_j": 32000.0, "Mz_i": 48000.0, "Mz_j": 48000.0},
                    "103": {"Vy_i": 34000.0, "Vy_j": 34000.0, "Mz_i": 49000.0, "Mz_j": 49000.0},
                    "104": {"Vy_i": 31000.0, "Vy_j": 31000.0, "Mz_i": 45000.0, "Mz_j": 45000.0},
                },
                "LL_Special": {
                    "101": {"Vy_i": 85000.0, "Vy_j": 85000.0, "Mz_i": 140000.0, "Mz_j": 140000.0},
                    "102": {"Vy_i": 80000.0, "Vy_j": 80000.0, "Mz_i": 130000.0, "Mz_j": 130000.0},
                    "103": {"Vy_i": 82000.0, "Vy_j": 82000.0, "Mz_i": 135000.0, "Mz_j": 135000.0},
                    "104": {"Vy_i": 78000.0, "Vy_j": 78000.0, "Mz_i": 128000.0, "Mz_j": 128000.0},
                },
            },
        }

    def test_initialization_and_geometry(self):
        ed = EndDiaphragmWelded(self.mock_bridge)
        geom = ed.get_geometry_info()
        self.assertEqual(geom["ed_type"], "Welded Beam")
        self.assertEqual(geom["total_depth_mm"], 1000.0)
        self.assertEqual(geom["web_thickness_mm"], 10.0)
        self.assertEqual(geom["top_flange_width_mm"], 250.0)
        self.assertEqual(geom["top_flange_thickness_mm"], 14.0)
        self.assertEqual(geom["bottom_flange_width_mm"], 250.0)
        self.assertEqual(geom["bottom_flange_thickness_mm"], 14.0)
        self.assertEqual(geom["span_length_mm"], 2500.0)
        self.assertEqual(geom["girder_spacing_m"], 2.5)

    def test_map_edge_elements(self):
        ed = EndDiaphragmWelded(self.mock_bridge)
        pair_map = ed._map_edge_elements()
        self.assertIn("G1-G2", pair_map)
        self.assertIn("G2-G3", pair_map)
        self.assertEqual(set(pair_map["G1-G2"]), {"101", "102"})
        self.assertEqual(set(pair_map["G2-G3"]), {"103", "104"})

    def test_compute_panel_forces(self):
        ed = EndDiaphragmWelded(self.mock_bridge)
        df = ed.compute_panel_forces()
        self.assertFalse(df.empty)
        self.assertIn("Vy_max (kN)", df.columns)
        self.assertIn("Mz_max (kNm)", df.columns)
        row = df[(df["LoadCase"] == "LL_Special") & (df["Member"] == "101")].iloc[0]
        self.assertAlmostEqual(row["Vy_max (kN)"], 85.0, places=2)
        self.assertAlmostEqual(row["Mz_max (kNm)"], 140.0, places=2)

    def test_get_design_forces_dict(self):
        ed = EndDiaphragmWelded(self.mock_bridge)
        fd = ed.get_design_forces_dict()
        self.assertEqual(fd["ed_type"], "Welded Beam")
        self.assertIn("G1-G2", fd["pairs"])
        self.assertIn("G2-G3", fd["pairs"])
        g1_g2 = fd["pairs"]["G1-G2"]
        self.assertAlmostEqual(g1_g2["shear_Vy_kN"], 85.0, places=2)
        self.assertEqual(g1_g2["shear_Vy_gov_lc"], "LL_Special")
        self.assertAlmostEqual(g1_g2["moment_Mz_kNm"], 140.0, places=2)
        self.assertEqual(g1_g2["moment_Mz_gov_lc"], "LL_Special")

    def test_live_osdag_plate_girder_calculation(self):
        d = dict(design_dict_plate_girder)
        d["Member.Length"] = "2500"
        d["Total.Depth"] = "1000"
        d["Web.Thickness"] = "10"
        d["Topflange.Width"] = "250"
        d["TopFlange.Thickness"] = "14"
        d["Bottomflange.Width"] = "250"
        d["BottomFlange.Thickness"] = "14"
        d["Load.Moment"] = "140.0"
        d["Load.Shear"] = "85.0"

        result = run_calculation(d)
        self.assertIsNotNone(result)
        self.assertIn("Optimum.Designation", result)
        self.assertTrue(result.get("Optimum.Designation").startswith("PG"))
        self.assertIn("Moment.Strength", result)
        self.assertIn("Shear.Strength", result)
        self.assertGreater(float(result["Moment.Strength"]), 140.0)
        self.assertGreater(float(result["Shear.Strength"]), 85.0)


if __name__ == "__main__":
    unittest.main()
