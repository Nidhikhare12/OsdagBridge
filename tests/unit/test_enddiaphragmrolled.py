import unittest
from unittest.mock import MagicMock

from osdagbridge.core.bridge_types.plate_girder.enddiaphragmrolled import EndDiaphragmRolled
from osdagbridge.core.utils.common import (
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TYPE,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)
from osdagbridge.core.utils.connect import (
    design_dict_simply_supported,
    run_calculation,
)


class TestEndDiaphragmRolled(unittest.TestCase):
    def setUp(self):
        self.mock_bridge = MagicMock()
        self.mock_bridge.input_dict = {
            KEY_TS_NO_OF_GIRDERS: 3,
            KEY_TS_GIRDER_SPACING: 2.5,
        }
        self.mock_bridge.additional_inputs = {
            KEY_MP_ED_TYPE: "Rolled Beam",
            KEY_MP_ED_IS_SECTION: "MB 300",
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
            "loadcases": ["SW", "DL", "LL_Truck"],
            "forces": {
                "SW": {
                    "101": {"Vy_i": 10000.0, "Vy_j": 10000.0, "Mz_i": 15000.0, "Mz_j": 15000.0},
                    "102": {"Vy_i": 12000.0, "Vy_j": 12000.0, "Mz_i": 18000.0, "Mz_j": 18000.0},
                    "103": {"Vy_i": 9000.0, "Vy_j": 9000.0, "Mz_i": 14000.0, "Mz_j": 14000.0},
                    "104": {"Vy_i": 11000.0, "Vy_j": 11000.0, "Mz_i": 16000.0, "Mz_j": 16000.0},
                },
                "DL": {
                    "101": {"Vy_i": 25000.0, "Vy_j": 25000.0, "Mz_i": 40000.0, "Mz_j": 40000.0},
                    "102": {"Vy_i": 22000.0, "Vy_j": 22000.0, "Mz_i": 38000.0, "Mz_j": 38000.0},
                    "103": {"Vy_i": 24000.0, "Vy_j": 24000.0, "Mz_i": 39000.0, "Mz_j": 39000.0},
                    "104": {"Vy_i": 21000.0, "Vy_j": 21000.0, "Mz_i": 35000.0, "Mz_j": 35000.0},
                },
                "LL_Truck": {
                    "101": {"Vy_i": 60000.0, "Vy_j": 60000.0, "Mz_i": 95000.0, "Mz_j": 95000.0},
                    "102": {"Vy_i": 55000.0, "Vy_j": 55000.0, "Mz_i": 90000.0, "Mz_j": 90000.0},
                    "103": {"Vy_i": 58000.0, "Vy_j": 58000.0, "Mz_i": 92000.0, "Mz_j": 92000.0},
                    "104": {"Vy_i": 54000.0, "Vy_j": 54000.0, "Mz_i": 88000.0, "Mz_j": 88000.0},
                },
            },
        }

    def test_initialization_and_geometry(self):
        ed = EndDiaphragmRolled(self.mock_bridge)
        geom = ed.get_geometry_info()
        self.assertEqual(geom["ed_type"], "Rolled Beam")
        self.assertEqual(geom["span_length_m"], 2.5)
        self.assertEqual(geom["girder_spacing_m"], 2.5)
        self.assertEqual(ed.is_section, "MB 300")

    def test_map_edge_elements(self):
        ed = EndDiaphragmRolled(self.mock_bridge)
        pair_map = ed._map_edge_elements()
        self.assertIn("G1-G2", pair_map)
        self.assertIn("G2-G3", pair_map)
        self.assertEqual(set(pair_map["G1-G2"]), {"101", "102"})
        self.assertEqual(set(pair_map["G2-G3"]), {"103", "104"})

    def test_compute_panel_forces(self):
        ed = EndDiaphragmRolled(self.mock_bridge)
        df = ed.compute_panel_forces()
        self.assertFalse(df.empty)
        self.assertIn("Vy_max (kN)", df.columns)
        self.assertIn("Mz_max (kNm)", df.columns)
        row = df[(df["LoadCase"] == "LL_Truck") & (df["Member"] == "101")].iloc[0]
        self.assertAlmostEqual(row["Vy_max (kN)"], 60.0, places=2)
        self.assertAlmostEqual(row["Mz_max (kNm)"], 95.0, places=2)

    def test_get_design_forces_dict(self):
        ed = EndDiaphragmRolled(self.mock_bridge)
        fd = ed.get_design_forces_dict()
        self.assertEqual(fd["ed_type"], "Rolled Beam")
        self.assertIn("G1-G2", fd["pairs"])
        self.assertIn("G2-G3", fd["pairs"])
        g1_g2 = fd["pairs"]["G1-G2"]
        self.assertAlmostEqual(g1_g2["shear_Vy_kN"], 60.0, places=2)
        self.assertEqual(g1_g2["shear_Vy_gov_lc"], "LL_Truck")
        self.assertAlmostEqual(g1_g2["moment_Mz_kNm"], 95.0, places=2)
        self.assertEqual(g1_g2["moment_Mz_gov_lc"], "LL_Truck")

    def test_live_osdag_simply_supported_calculation(self):
        d = dict(design_dict_simply_supported)
        d["Member.Length"] = "2.5"
        d["Load.Moment"] = "60.0"
        d["Load.Shear"] = "40.0"
        d["Member.Designation"] = ["MB 300", "MB 350", "MB 400"]

        result = run_calculation(d)
        self.assertIsNotNone(result)
        self.assertIn("Optimum.Designation", result)
        self.assertTrue(result.get("Optimum.Designation").startswith("MB"))
        self.assertIn("Moment.Strength", result)
        self.assertIn("Shear.Strength", result)
        self.assertGreater(float(result["Moment.Strength"]), 60.0)
        self.assertGreater(float(result["Shear.Strength"]), 40.0)


if __name__ == "__main__":
    unittest.main()
