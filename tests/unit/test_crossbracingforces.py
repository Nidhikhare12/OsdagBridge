import unittest
from types import SimpleNamespace

from osdagbridge.core.bridge_types.plate_girder.crossbracingforces import (
    BRACE_K,
    BRACE_X,
    CrossBracingForces,
)
from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
from osdagbridge.core.utils.common import (
    KEY_MP_CB_BOTTOM_CHORD,
    KEY_MP_CB_BRACING_CONNECTION,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_TYPE,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)


def _dummy_bridge(additional_inputs: dict = None, input_dict: dict = None) -> SimpleNamespace:
    base_inp = {
        KEY_MP_GIRDER_DEPTH: 1.67,
        KEY_MP_GIRDER_TOP_FLANGE_THICKNESS: 0.022,
        KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS: 0.022,
        KEY_TS_GIRDER_SPACING: 2.08,
    }
    if input_dict:
        base_inp.update(input_dict)
    return SimpleNamespace(
        additional_inputs=additional_inputs or {},
        grillage_geometry=object(),
        input_dict=base_inp,
    )


class CrossBracingForcesTests(unittest.TestCase):
    def test_crossbracing_configuration_reads_dynamic_ui_keys(self):
        suffix = ".G1G2.B1M1"
        bridge = _dummy_bridge(
            {
                f"{KEY_MP_CB_TYPE}{suffix}": "K-Bracing",
                f"{KEY_MP_CB_BRACING_CONNECTION}{suffix}": "Welded",
                f"{KEY_MP_CB_TOP_CHORD}{suffix}": False,
                f"{KEY_MP_CB_BOTTOM_CHORD}{suffix}": True,
                f"{KEY_MP_CB_SPACING}{suffix}": 3.5,
            }
        )

        cb = CrossBracingForces(bridge=bridge)

        self.assertEqual(cb.brace_type, BRACE_K)
        self.assertEqual(cb.connection_type, "Welded")
        self.assertFalse(cb.top_chord)
        self.assertTrue(cb.bottom_chord)
        self.assertEqual(cb.cb_spacing, 3.5)

    def test_crossbracing_configuration_defaults_to_bolted(self):
        bridge = _dummy_bridge({})
        cb = CrossBracingForces(bridge=bridge)
        self.assertEqual(cb.connection_type, "Bolted")
        self.assertEqual(cb.brace_type, BRACE_X)

    def test_extract_osdag_summary_handles_welded_tension_and_compression(self):
        tension = {
            "section_size.designation": "35 x 35 x 3",
            "Member.tension_capacity": 30.9,
            "Member.efficiency": 0.14,
            "Member.Slenderness": 364.9,
            "Weld.Type": "Fillet Weld",
        }
        compression = {
            "Optimum.Designation": "50 x 50 x 4",
            "Design.Strength": 17.37,
            "Optimum.UR": 0.371,
            "ESR": 170.8,
            "Weld.Type": "Fillet Weld",
        }

        self.assertEqual(
            _extract_osdag_summary(tension),
            {
                "section": "35 x 35 x 3",
                "capacity_kN": 30.9,
                "efficiency": 0.14,
                "slenderness": 364.9,
                "connection": "Welded",
            },
        )
        self.assertEqual(
            _extract_osdag_summary(compression),
            {
                "section": "50 x 50 x 4",
                "capacity_kN": 17.37,
                "efficiency": 0.371,
                "slenderness": 170.8,
                "connection": "Welded",
            },
        )

    def test_extract_osdag_summary_handles_bolted(self):
        tension_bolted = {
            "section_size.designation": "40 x 40 x 3",
            "Member.tension_capacity": 45.0,
            "Member.efficiency": 0.1,
            "Member.Slenderness": 211.5,
        }
        self.assertEqual(
            _extract_osdag_summary(tension_bolted),
            {
                "section": "40 x 40 x 3",
                "capacity_kN": 45.0,
                "efficiency": 0.1,
                "slenderness": 211.5,
                "connection": "Bolted",
            },
        )


if __name__ == "__main__":
    unittest.main()
