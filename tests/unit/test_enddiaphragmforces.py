import unittest
from types import SimpleNamespace

from osdagbridge.core.bridge_types.plate_girder.crossbracingforces import (
    BRACE_K as CB_BRACE_K,
    BRACE_X as CB_BRACE_X,
    CrossBracingForces,
)
from osdagbridge.core.bridge_types.plate_girder.enddiaphragmforces import (
    BRACE_K,
    BRACE_X,
    EndDiaphragmForces,
)
from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
from osdagbridge.core.utils.common import (
    KEY_MP_CB_BOTTOM_CHORD,
    KEY_MP_CB_BRACING_CONNECTION,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_TYPE,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)


def _dummy_bridge(additional_inputs: dict = None, input_dict: dict = None, result_data: dict = None) -> SimpleNamespace:
    base_inp = {
        KEY_MP_GIRDER_DEPTH: 1.67,
        KEY_MP_GIRDER_TOP_FLANGE_THICKNESS: 0.022,
        KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS: 0.022,
        KEY_TS_GIRDER_SPACING: 2.08,
        KEY_TS_NO_OF_GIRDERS: 2,
    }
    if input_dict:
        base_inp.update(input_dict)
    return SimpleNamespace(
        additional_inputs=additional_inputs or {},
        grillage_geometry=object(),
        grillage_model=SimpleNamespace(model=None),
        input_dict=base_inp,
        result_data=result_data or {},
    )


class EndDiaphragmForcesTests(unittest.TestCase):
    def test_ed_configuration_reads_dynamic_ui_keys(self):
        suffix = ".G1G2.E1M1"
        bridge = _dummy_bridge(
            {
                f"{KEY_MP_ED_TYPE}{suffix}": "Cross Bracing",
                f"{KEY_MP_ED_BRACING_TYPE}{suffix}": "K-Bracing",
                f"{KEY_MP_ED_BRACING_CONNECTION}{suffix}": "Welded",
                f"{KEY_MP_ED_TOP_CHORD}{suffix}": False,
                f"{KEY_MP_ED_BOTTOM_CHORD}{suffix}": True,
            }
        )

        ed = EndDiaphragmForces(bridge=bridge)

        self.assertEqual(ed.brace_type, BRACE_K)
        self.assertEqual(ed.connection_type, "Welded")
        self.assertFalse(ed.top_chord)
        self.assertTrue(ed.bottom_chord)

    def test_ed_configuration_defaults_to_bolted_and_x(self):
        bridge = _dummy_bridge({})
        ed = EndDiaphragmForces(bridge=bridge)
        self.assertEqual(ed.connection_type, "Bolted")
        self.assertEqual(ed.brace_type, BRACE_X)
        self.assertTrue(ed.top_chord)
        self.assertTrue(ed.bottom_chord)

    def test_independence_cb_welded_ed_bolted(self):
        cb_suffix = ".G1G2.B1M1"
        ed_suffix = ".G1G2.E1M1"
        bridge = _dummy_bridge(
            {
                # Cross Bracing is Welded and K-type
                f"{KEY_MP_CB_TYPE}{cb_suffix}": "K-Bracing",
                f"{KEY_MP_CB_BRACING_CONNECTION}{cb_suffix}": "Welded",
                f"{KEY_MP_CB_TOP_CHORD}{cb_suffix}": False,
                f"{KEY_MP_CB_BOTTOM_CHORD}{cb_suffix}": True,
                # End Diaphragm is Bolted and X-type
                f"{KEY_MP_ED_BRACING_TYPE}{ed_suffix}": "X-Bracing",
                f"{KEY_MP_ED_BRACING_CONNECTION}{ed_suffix}": "Bolted",
                f"{KEY_MP_ED_TOP_CHORD}{ed_suffix}": True,
                f"{KEY_MP_ED_BOTTOM_CHORD}{ed_suffix}": False,
            }
        )

        cb = CrossBracingForces(bridge=bridge)
        ed = EndDiaphragmForces(bridge=bridge)

        self.assertEqual(cb.connection_type, "Welded")
        self.assertEqual(cb.brace_type, CB_BRACE_K)
        self.assertFalse(cb.top_chord)
        self.assertTrue(cb.bottom_chord)

        self.assertEqual(ed.connection_type, "Bolted")
        self.assertEqual(ed.brace_type, BRACE_X)
        self.assertTrue(ed.top_chord)
        self.assertFalse(ed.bottom_chord)

    def test_independence_cb_bolted_ed_welded(self):
        cb_suffix = ".G1G2.B1M1"
        ed_suffix = ".G1G2.E1M1"
        bridge = _dummy_bridge(
            {
                # Cross Bracing is Bolted and X-type
                f"{KEY_MP_CB_TYPE}{cb_suffix}": "X-Bracing",
                f"{KEY_MP_CB_BRACING_CONNECTION}{cb_suffix}": "Bolted",
                # End Diaphragm is Welded and K-type
                f"{KEY_MP_ED_BRACING_TYPE}{ed_suffix}": "K-Bracing",
                f"{KEY_MP_ED_BRACING_CONNECTION}{ed_suffix}": "Welded",
            }
        )

        cb = CrossBracingForces(bridge=bridge)
        ed = EndDiaphragmForces(bridge=bridge)

        self.assertEqual(cb.connection_type, "Bolted")
        self.assertEqual(cb.brace_type, CB_BRACE_X)

        self.assertEqual(ed.connection_type, "Welded")
        self.assertEqual(ed.brace_type, BRACE_K)

    def test_geometry_calculations(self):
        bridge = _dummy_bridge(
            input_dict={
                KEY_MP_GIRDER_DEPTH: 2.0,
                KEY_TS_GIRDER_SPACING: 2.0,
            }
        )
        # X-brace
        ed_x = EndDiaphragmForces(bridge=bridge, brace_type="X", depth_ratio=0.85)
        self.assertAlmostEqual(ed_x.h, 1.7)
        self.assertAlmostEqual(ed_x.horiz_proj, 2.0)
        self.assertAlmostEqual(ed_x.L_d, (2.0**2 + 1.7**2) ** 0.5)

        # K-brace
        ed_k = EndDiaphragmForces(bridge=bridge, brace_type="K", depth_ratio=0.85)
        self.assertAlmostEqual(ed_k.h, 1.7)
        self.assertAlmostEqual(ed_k.horiz_proj, 1.0)
        self.assertAlmostEqual(ed_k.L_d, (1.0**2 + 1.7**2) ** 0.5)

    def test_force_extraction_from_result_data(self):
        result_data = {
            "girders": {
                "G1": {"nodes": [1, 2], "index": 0},
                "G2": {"nodes": [3, 4], "index": 1},
            },
            "members": {
                "101": [1, 3],
                "102": [2, 4],
            },
            "loadcases": ["LC1", "LC2"],
            "forces": {
                "LC1": {
                    "101": {"Vz_i": 50000.0, "Vz_j": 50000.0},
                    "102": {"Vz_i": -30000.0, "Vz_j": -30000.0},
                },
                "LC2": {
                    "101": {"Vz_i": -60000.0, "Vz_j": -60000.0},
                    "102": {"Vz_i": 20000.0, "Vz_j": 20000.0},
                },
            },
        }
        bridge = _dummy_bridge(result_data=result_data)
        ed = EndDiaphragmForces(bridge=bridge, brace_type="X")
        forces_dict = ed.get_design_forces_dict()

        self.assertIn("G1-G2", forces_dict["pairs"])
        p = forces_dict["pairs"]["G1-G2"]
        expected_diag_tens = 50.0 / ed.cos_alpha
        self.assertAlmostEqual(p["diag_tension_kN"], expected_diag_tens, places=2)
        expected_diag_comp = 60.0 / ed.cos_alpha
        self.assertAlmostEqual(p["diag_compression_kN"], expected_diag_comp, places=2)
        self.assertAlmostEqual(p["chord_tension_kN"], 50.0, places=2)
        self.assertAlmostEqual(p["chord_compression_kN"], 60.0, places=2)


if __name__ == "__main__":
    unittest.main()
