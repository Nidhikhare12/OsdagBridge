"""
=============================================================================
Unit and Regression Tests for Phase 2, Task R3:
Live Load & Footway Load Table Refactoring in Chapter 3
=============================================================================
"""

import os
import tempfile
import unittest

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.report_generator import (
    ReportFigures,
    ReportMetadata,
    ReportOptions,
    ReportPayload,
    ReportRequest,
    generate_report,
)
from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
    KEY_TS_FOOTPATH_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
)


class TestChapter3LiveLoadTables(unittest.TestCase):
    """Test suite for separated and dynamically structured Live Load tables."""

    def setUp(self):
        self.base_inputs = {
            KEY_SPAN: "24.0",
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_TS_FOOTPATH_THICKNESS: "200",
            KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
            KEY_LL_FOOTPATH_PRESSURE_VALUE: "",
            KEY_LL_ECCENTRICITY: "1.2",
            KEY_BL_IRC_CLASS_SV: True,
        }

    def test_two_separate_tables_present(self):
        """Verify Table 3.3 (Carriageway Live Loads) and Table 3.4 (Footway Live Loads) exist separately."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        tex = ch3_loads(inputs)

        self.assertIn(r"\textbf{Carriageway Live Loads (IRC 6)}", tex)
        self.assertIn(r"\textbf{Footway Live Loads (FL)}", tex)
        # Ensure the old merged caption is gone
        self.assertNotIn(r"\caption{\textbf{Live Loads (LL)}}", tex)

    def test_vehicle_selection_status_dynamic(self):
        """Selected vehicles show 'Yes' while unselected show 'No'."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_WHEELED] = True
        inputs[KEY_LL_IRC_70R_TRACKED] = False
        inputs[KEY_LL_IRC_AA_WHEELED] = False

        tex = ch3_loads(inputs)

        # Class A and 70R Wheeled are selected
        self.assertIn(r"\textnormal{Class A} & Yes", tex)
        self.assertIn(r"\textnormal{Class 70R (Wheeled)} & Yes", tex)
        # Class 70R Tracked and Class AA Wheeled are not selected
        self.assertIn(r"\textnormal{Class 70R (Tracked)} & No", tex)
        self.assertIn(r"\textnormal{Class AA (Wheeled)} & No", tex)

    def test_impact_allowance_and_multiplier_consistency(self):
        """Verify fractional impact allowance i and total multiplier (1+i) for span = 24.0 m."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_TRACKED] = True
        inputs[KEY_LL_IRC_CLASS_SV] = True
        inputs[KEY_LL_IRC_CLASS_FATIGUE] = True

        tex = ch3_loads(inputs)

        # Class A: 9.0 / (13.5 + 24.0) = 0.240 -> multiplier 1.240
        self.assertIn("0.240", tex)
        self.assertIn("1.240", tex)
        # Class 70R Tracked: 0.100 -> multiplier 1.100
        self.assertIn("0.100", tex)
        self.assertIn("1.100", tex)
        # Class SV / Fatigue: Nil allowance -> multiplier 1.000
        self.assertIn("0.000", tex)
        self.assertIn("1.000", tex)

    def test_analysis_status_distinction(self):
        """Verify FE analyzed vs excluded from FE model distinction."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_WHEELED] = True
        inputs[KEY_LL_IRC_70R_TRACKED] = True
        inputs[KEY_LL_IRC_CLASS_FATIGUE] = True

        tex = ch3_loads(inputs)

        self.assertIn("Analysed in FE Model", tex)
        self.assertIn("Excluded from FE Model", tex)
        self.assertIn("Fatigue Checks (SLS)", tex)

    def test_custom_vehicles_rendering(self):
        """Custom vehicles are rendered with user-defined status."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_CUSTOM_VEHICLES] = [
            {"name": "Heavy Dumper 120T", "vehicle_type": "Wheeled"}
        ]
        tex = ch3_loads(inputs)

        self.assertIn("Heavy Dumper 120T", tex)
        self.assertIn("User-defined", tex)

    def test_centrifugal_force_missing_or_unknown_alignment(self):
        """Centrifugal force documents unknown / not specified when neither alignment nor radius is set."""
        inputs = dict(self.base_inputs)
        tex = ch3_loads(inputs)

        self.assertIn("N/A (Alignment unknown / not specified in inputs per IRC 6 Cl. 212)", tex)

    def test_centrifugal_force_explicit_straight_alignment(self):
        """Centrifugal force documents straight alignment when explicitly specified."""
        inputs = dict(self.base_inputs)
        inputs["alignment"] = "straight"
        tex = ch3_loads(inputs)

        self.assertIn("N/A (Straight Alignment per IRC 6, Clause 212.1)", tex)

    def test_centrifugal_force_curved_alignment(self):
        """Centrifugal force extracts and reports curved alignment when valid radius is set."""
        inputs = dict(self.base_inputs)
        inputs["radius_of_curvature"] = "300.0"
        tex = ch3_loads(inputs)

        self.assertIn("Curved alignment noted in inputs (R = 300.0 m)", tex)
        self.assertIn("centrifugal force not applied in structural analysis", tex)
        self.assertNotIn("Straight Alignment", tex)
        self.assertNotIn("Applied for curved alignment", tex)

    def test_centrifugal_force_invalid_radius(self):
        """Centrifugal force handles negative radius or non-numeric radius gracefully."""
        inputs_neg = dict(self.base_inputs)
        inputs_neg["radius_of_curvature"] = "-50.0"
        tex_neg = ch3_loads(inputs_neg)
        self.assertIn("Invalid radius R <= 0", tex_neg)

        inputs_invalid = dict(self.base_inputs)
        inputs_invalid["radius_of_curvature"] = "invalid_number"
        tex_invalid = ch3_loads(inputs_invalid)
        self.assertIn("Invalid radius format", tex_invalid)

    def test_braking_force_documentation(self):
        """Longitudinal braking force is documented as bearing/substructure action."""
        inputs = dict(self.base_inputs)
        inputs[KEY_LL_ECCENTRICITY] = "1.25"
        inputs[KEY_BL_IRC_CLASS_SV] = True
        tex = ch3_loads(inputs)

        self.assertIn("Longitudinal Braking Force (IRC 6 Cl. 211)", tex)
        self.assertIn("1.25 m", tex)
        self.assertIn("Class SV braking opt-in: \\textbf{Included}", tex)
        self.assertIn("bearing/substructure action", tex)

    def test_footway_irc_mode(self):
        """Footway in IRC mode correctly renders 4.905 kN/m²."""
        inputs = dict(self.base_inputs)
        inputs[KEY_FOOTPATH] = "Both Sides"
        inputs[KEY_LL_FOOTPATH_PRESSURE_MODE] = "As per IRC 6"
        tex = ch3_loads(inputs)

        self.assertIn("Both Sides", tex)
        self.assertIn("1.50 m", tex)
        self.assertIn("As per IRC 6 Cl. 206.1", tex)
        self.assertIn("4.905 kN/m", tex)
        self.assertIn("500 kg/m", tex)

    def test_footway_custom_mode(self):
        """Footway in Custom mode renders user-defined pressure."""
        inputs = dict(self.base_inputs)
        inputs[KEY_FOOTPATH] = "Single Side"
        inputs[KEY_LL_FOOTPATH_PRESSURE_MODE] = "Custom"
        inputs[KEY_LL_FOOTPATH_PRESSURE_VALUE] = "3.85"
        tex = ch3_loads(inputs)

        self.assertIn("Single Side", tex)
        self.assertIn("User-defined Custom Pressure", tex)
        self.assertIn("3.850 kN/m", tex)

    def test_footway_none_mode(self):
        """Footway when None states no footway is provided."""
        inputs = dict(self.base_inputs)
        inputs[KEY_FOOTPATH] = "None"
        tex = ch3_loads(inputs)

        self.assertIn("None (No footway provided on typical section)", tex)

    def test_repeated_headers_preserved_in_ch3(self):
        """Verify that all longtable environments in Chapter 3 retain \\endhead."""
        inputs = dict(self.base_inputs)
        tex = ch3_loads(inputs)

        lt_count = tex.count(r"\begin{longtable}")
        endhead_count = tex.count(r"\endhead")
        endfirsthead_count = tex.count(r"\endfirsthead")

        self.assertGreaterEqual(lt_count, 8)  # Now 8 tables instead of 7
        self.assertEqual(lt_count, endhead_count)
        self.assertEqual(lt_count, endfirsthead_count)


class TestFullReportCompilationR3(unittest.TestCase):
    """Integration test verifying end-to-end PDF generation with R3 refactored Chapter 3."""

    def test_full_report_compiles_successfully_with_r3(self):
        metadata = ReportMetadata(
            project_name="R3 Verification Bridge",
            project_location="Mumbai",
            job_number="JOB-2026-R3",
            client="FOSSEE",
            designer="OsdagBridge Team",
            company="IIT Bombay",
        )
        options = ReportOptions(
            sections=["loads"],
            include_toc=False,
            include_figures=False,
            include_pdf=True,
        )
        inputs = {
            KEY_SPAN: "24.0",
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_LL_IRC_70R_TRACKED: False,
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: "1.5",
            KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
            KEY_LL_ECCENTRICITY: "1.2",
            KEY_BL_IRC_CLASS_SV: True,
        }
        payload = ReportPayload(
            metadata=metadata,
            options=options,
            inputs=inputs,
            analysis_summary={},
            design_checks=[],
            figures=ReportFigures(),
            log_entries=[],
            output_dict={},
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            request = ReportRequest(
                metadata=metadata,
                options=options,
                output_dir=tmp_dir,
                file_stem="Test_Report_R3",
            )
            res = generate_report(payload, request)
            self.assertIsNotNone(res.pdf_path, "PDF generation failed")
            self.assertTrue(os.path.isfile(res.pdf_path), "PDF file was not created on disk")
            self.assertGreater(os.path.getsize(res.pdf_path), 1000, "PDF file is smaller than 1 KB")


if __name__ == "__main__":
    unittest.main()
