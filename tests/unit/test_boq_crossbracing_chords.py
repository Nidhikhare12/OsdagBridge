# =============================================================================
# OsdagBridge — Unit Tests: BOQ Cross-Bracing Chord Configuration
#
# Regression tests for:
#   - X-bracing with both chords enabled
#   - K-bracing with top chord disabled
#   - K-bracing with top chord enabled
#   - Bottom chord disabled
#   - Input dictionary fallback
#   - Backward-compatible defaults when keys are missing
#   - Safe string / boolean normalization
#   - True zero quantities for disabled members
# =============================================================================

import unittest

from osdagbridge.core.boq.boq_generator import (
    calculate_material_quantities,
    _normalize_chord_enabled,
)
from osdagbridge.core.utils.common import (
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_BOTTOM_CHORD,
)


class TestBOQCrossBracingChords(unittest.TestCase):
    """Focused regression tests for cross-bracing chord configuration in BOQ."""

    def setUp(self):
        self.base_inputs = {
            "geometry.span": "24.0",
            "typical_section.no_of_girders": "2",
            "typical_section.girder_spacing": "3.0",
        }
        self.base_cb_geom = {
            "cb_spacing_m": 3.0,
            "diagonal_length_m": 3.60,
        }

    def test_01_boq_x_bracing_both_chords_enabled(self):
        """X-bracing with both top and bottom chords enabled produces positive weights for both."""
        cb_forces = {
            "geometry": self.base_cb_geom,
            "brace_type": "X",
            "top_chord": True,
            "bottom_chord": True,
        }
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,  # 10 cm²
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(self.base_inputs, outputs)

        self.assertNotEqual(q["bracing_top_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_bot_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_diag_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_top_qty"], "0")
        self.assertNotEqual(q["bracing_bot_qty"], "0")
        self.assertIn(r"\text{ m}^3", q["bracing_top_vol_formula"])

        top_wt = float(q["bracing_top_wt_total"])
        bot_wt = float(q["bracing_bot_wt_total"])
        diag_wt = float(q["bracing_diag_wt_total"])
        self.assertGreater(top_wt, 0.0)
        self.assertGreater(bot_wt, 0.0)
        self.assertGreater(diag_wt, 0.0)

    def test_02_boq_k_bracing_top_chord_disabled(self):
        """K-bracing with top chord disabled produces exactly 0.00 for top chord."""
        cb_forces = {
            "geometry": self.base_cb_geom,
            "brace_type": "K",
            "top_chord": False,
            "bottom_chord": True,
        }
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(self.base_inputs, outputs)

        self.assertEqual(q["bracing_top_qty"], "0")
        self.assertEqual(q["bracing_top_vol_total"], "0.00")
        self.assertEqual(q["bracing_top_wt_single"], "0.0000")
        self.assertEqual(q["bracing_top_wt_total"], "0.00")
        self.assertEqual(q["bracing_top_vol_formula"], "N.A.")

        # Bottom chord and diagonals must remain positive
        self.assertNotEqual(q["bracing_bot_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_diag_wt_total"], "0.00")

    def test_03_boq_k_bracing_top_chord_enabled(self):
        """K-bracing with top chord enabled produces positive weight for top chord."""
        cb_forces = {
            "geometry": self.base_cb_geom,
            "brace_type": "K",
            "top_chord": True,
            "bottom_chord": True,
        }
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(self.base_inputs, outputs)
        self.assertNotEqual(q["bracing_top_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_bot_wt_total"], "0.00")

    def test_04_boq_bottom_chord_disabled(self):
        """Disabling bottom chord produces exactly 0.00 and suppresses formula."""
        cb_forces = {
            "geometry": self.base_cb_geom,
            "brace_type": "X",
            "top_chord": True,
            "bottom_chord": False,
        }
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(self.base_inputs, outputs)
        self.assertEqual(q["bracing_bot_qty"], "0")
        self.assertEqual(q["bracing_bot_wt_total"], "0.00")
        self.assertEqual(q["bracing_bot_vol_formula"], "N.A.")
        self.assertNotEqual(q["bracing_top_wt_total"], "0.00")

    def test_05_boq_chord_fallback_from_inputs(self):
        """When cb_forces lacks top_chord/bottom_chord, falls back to inputs dict."""
        inputs = dict(self.base_inputs)
        inputs[KEY_MP_CB_TOP_CHORD] = "No"
        inputs[KEY_MP_CB_BOTTOM_CHORD] = "Yes"

        cb_forces = {"geometry": self.base_cb_geom}  # no chord keys
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(inputs, outputs)
        self.assertEqual(q["bracing_top_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_bot_wt_total"], "0.00")

    def test_06_boq_missing_keys_backward_compatible_fallback(self):
        """When chord keys are completely absent from both outputs and inputs, defaults to enabled."""
        cb_forces = {"geometry": self.base_cb_geom}
        outputs = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces,
        }
        q = calculate_material_quantities(self.base_inputs, outputs)
        self.assertNotEqual(q["bracing_top_wt_total"], "0.00")
        self.assertNotEqual(q["bracing_bot_wt_total"], "0.00")

    def test_07_boq_string_normalization_edge_cases(self):
        """_normalize_chord_enabled handles boolean, string variants, None, and fallbacks."""
        # True cases
        self.assertTrue(_normalize_chord_enabled(True))
        self.assertTrue(_normalize_chord_enabled("Yes"))
        self.assertTrue(_normalize_chord_enabled("TRUE"))
        self.assertTrue(_normalize_chord_enabled("1"))
        self.assertTrue(_normalize_chord_enabled("Enabled"))

        # False cases
        self.assertFalse(_normalize_chord_enabled(False))
        self.assertFalse(_normalize_chord_enabled("No"))
        self.assertFalse(_normalize_chord_enabled("false"))
        self.assertFalse(_normalize_chord_enabled("0"))
        self.assertFalse(_normalize_chord_enabled("Disabled"))
        self.assertFalse(_normalize_chord_enabled("None"))

        # None / empty / unrecognized defaults
        self.assertTrue(_normalize_chord_enabled(None, default=True))
        self.assertFalse(_normalize_chord_enabled(None, default=False))
        self.assertTrue(_normalize_chord_enabled("", default=True))
        self.assertTrue(_normalize_chord_enabled("unknown", default=True))

    def test_08_boq_crossbracing_aggregate_reflects_disabled_chord(self):
        """Cross-bracing component sum reduces by exactly the disabled chord's weight."""
        # 1. With top chord enabled
        cb_forces_enabled = {
            "geometry": self.base_cb_geom,
            "brace_type": "K",
            "top_chord": True,
            "bottom_chord": True,
        }
        outputs_enabled = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces_enabled,
        }
        q_enabled = calculate_material_quantities(self.base_inputs, outputs_enabled)
        cb_sum_enabled = (
            float(q_enabled["bracing_top_wt_total"])
            + float(q_enabled["bracing_bot_wt_total"])
            + float(q_enabled["bracing_diag_wt_total"])
        )

        # 2. With top chord disabled
        cb_forces_disabled = dict(cb_forces_enabled)
        cb_forces_disabled["top_chord"] = False
        outputs_disabled = {
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 10.0,
            "crossbracing_forces_dict": cb_forces_disabled,
        }
        q_disabled = calculate_material_quantities(self.base_inputs, outputs_disabled)
        cb_sum_disabled = (
            float(q_disabled["bracing_top_wt_total"])
            + float(q_disabled["bracing_bot_wt_total"])
            + float(q_disabled["bracing_diag_wt_total"])
        )

        top_chord_wt = float(q_enabled["bracing_top_wt_total"])
        self.assertGreater(top_chord_wt, 0.0)
        self.assertAlmostEqual(cb_sum_enabled - cb_sum_disabled, top_chord_wt, places=2)


if __name__ == "__main__":
    unittest.main()
