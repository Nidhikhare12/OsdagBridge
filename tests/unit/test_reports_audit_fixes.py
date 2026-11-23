# =============================================================================
# OsdagBridge — Unit Tests: Final Report Audit Fixes
#
# Tests for:
#   1. End Diaphragm tables sourcing data from End Diaphragm results (not CB)
#   2. Deck report data integration (top-level and design_results fallback)
#   3. Clean missing input presentation (Chapter 2, 3, Executive Summary, BOQ)
#   4. Figure fallback box phrasing
# =============================================================================

import unittest
from osdagbridge.core.reports.report_generator import (
    ReportDataBridge,
    ReportPayload,
    ReportMetadata,
    ReportOptions,
    ReportFigures,
)
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap2 import ch2_input_parameters
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _fig_embed
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.utils.common import (
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
)


class TestReportAuditFixes(unittest.TestCase):
    """Test suite covering the verified audit fixes."""

    def setUp(self):
        self.metadata = ReportMetadata(
            project_name="Audit Fix Test Bridge",
            project_location="Test City",
            designer="Designer A",
            client="Client B",
            company="Company C",
        )
        self.options = ReportOptions(
            sections=["inputs", "loads", "design_checks"],
            include_figures=False,
            include_toc=True,
            include_pdf=True,
        )
        self.figures = ReportFigures()

    def test_01_end_diaphragm_tables_use_ed_data_not_cb(self):
        """Verify Table 5.21(a)-(c) uses End Diaphragm results, distinct from Cross Bracing."""
        cb_forces = {
            "brace_type": "X",
            "pairs": {
                "G1-G2": {
                    "diag_tension_kN": 222.0,
                    "diag_compression_kN": -210.0,
                    "chord_tension_kN": 180.0,
                    "chord_compression_kN": -190.0,
                    "diag_compression_gov_lc": "LC_CB_GOV",
                    "diag_tension_gov_lc": "LC_CB_GOV",
                    "chord_compression_gov_lc": "LC_CB_GOV",
                    "chord_tension_gov_lc": "LC_CB_GOV",
                }
            },
        }
        cb_designs = {
            "G1-G2": {
                "diagonal": {
                    "compression": {
                        "section": "2 x ISA 110 x 110 x 12",
                        "capacity_kN": 320.0,
                        "efficiency": 0.65,
                        "slenderness": 110.0,
                        "connection": "Bolted",
                    }
                },
                "chord": {
                    "compression": {
                        "section": "ISMC 200",
                        "capacity_kN": 300.0,
                        "efficiency": 0.63,
                        "slenderness": 80.0,
                        "connection": "Bolted",
                    }
                },
            }
        }
        ed_forces = {
            "brace_type": "X",
            "pairs": {
                "G1-G2": {
                    "diag_tension_kN": 111.0,
                    "diag_compression_kN": -105.0,
                    "chord_tension_kN": 90.0,
                    "chord_compression_kN": -95.0,
                    "diag_compression_gov_lc": "LC_ED_GOV",
                    "diag_tension_gov_lc": "LC_ED_GOV",
                    "chord_compression_gov_lc": "LC_ED_GOV",
                    "chord_tension_gov_lc": "LC_ED_GOV",
                }
            },
        }
        ed_designs = {
            "G1-G2": {
                "diagonal": {
                    "compression": {
                        "section": "2 x ISA 80 x 80 x 8",
                        "capacity_kN": 190.0,
                        "efficiency": 0.55,
                        "slenderness": 135.0,
                        "connection": "Bolted",
                    },
                    "tension": {
                        "section": "2 x ISA 80 x 80 x 8",
                        "capacity_kN": 210.0,
                        "efficiency": 0.53,
                        "slenderness": 135.0,
                        "connection": "Bolted",
                    },
                },
                "chord": {
                    "compression": {
                        "section": "ISMC 100",
                        "capacity_kN": 180.0,
                        "efficiency": 0.53,
                        "slenderness": 95.0,
                        "connection": "Bolted",
                    },
                    "tension": {
                        "section": "ISMC 100",
                        "capacity_kN": 200.0,
                        "efficiency": 0.45,
                        "slenderness": 95.0,
                        "connection": "Bolted",
                    },
                },
            }
        }

        output_dict = {
            "crossbracing_forces_dict": cb_forces,
            "crossbracing_design_results": cb_designs,
            "end_diaphragm_forces_dict": ed_forces,
            "end_diaphragm_design_results": ed_designs,
            "transverse_member_design.cb.section_properties.bracing.G1G2.A": 45.0,
            "transverse_member_design.cb.section_properties.bracing.G1G2.rv": 3.4,
            "transverse_member_design.cb.section_properties.bottom_chord.G1G2.A": 28.0,
            "transverse_member_design.cb.section_properties.bottom_chord.G1G2.rv": 2.5,
            "transverse_member_design.ed.section_properties.end_diaphragm.G1G2.A": 24.5,
            "transverse_member_design.ed.section_properties.end_diaphragm.G1G2.rv": 2.4,
            "transverse_member_design.ed.section_properties.bottom_chord.G1G2.A": 14.2,
            "transverse_member_design.ed.section_properties.bottom_chord.G1G2.rv": 1.6,
        }

        payload = ReportPayload(
            metadata=self.metadata,
            options=self.options,
            inputs={"typical_section.no_of_girders": 2, "span": 24.0, "typical_section.girder_spacing": 3.5},
            analysis_summary={},
            design_checks=[],
            figures=self.figures,
            output_dict=output_dict,
        )
        bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
        latex = ch5_design_checks([], bridge)

        # Confirm End Diaphragm section contains ED values and not CB values
        ed_section_idx = latex.find(r"\section{End Diaphragm Design}")
        self.assertGreater(ed_section_idx, 0, "End Diaphragm section must exist in chapter 5")
        ed_latex = latex[ed_section_idx:]

        # ED values must be in ED section
        self.assertIn("2 x ISA 80 x 80 x 8", ed_latex)
        self.assertIn("ISMC 100", ed_latex)
        self.assertIn(r"LC\_\allowbreak{}ED\_\allowbreak{}GOV", ed_latex)
        self.assertIn("2450.0", ed_latex)  # 24.5 cm² -> 2450 mm²
        self.assertIn("OsdagBridge end diaphragm module used", ed_latex)

        # CB values must NOT be in ED section
        self.assertNotIn("2 x ISA 110 x 110 x 12", ed_latex)
        self.assertNotIn("ISMC 200", ed_latex)
        self.assertNotIn("LC_CB_GOV", ed_latex)

    def test_02_deck_report_values_integration_top_level(self):
        """Verify deck_report_values at top level of output_dict populates deck tables."""
        deck_vals = {
            KEY_DD_M_ULS_SAG: 185.0,
            KEY_DD_MU_BOT: 260.0,
            KEY_DD_M_ULS_HOG: 142.0,
            KEY_DD_MU_TOP: 215.0,
        }
        output_dict = {"deck_report_values": deck_vals}
        payload = ReportPayload(
            metadata=self.metadata,
            options=self.options,
            inputs={"typical_section.no_of_girders": 2},
            analysis_summary={},
            design_checks=[],
            figures=self.figures,
            output_dict=output_dict,
        )
        bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
        latex = ch5_design_checks([], bridge)
        self.assertIn("185.00", latex)
        self.assertIn("260.00", latex)
        self.assertIn("142.00", latex)
        self.assertIn("215.00", latex)

    def test_03_deck_report_values_integration_nested_fallback(self):
        """Verify deck_report_values under design_results falls back properly."""
        deck_vals = {
            KEY_DD_M_ULS_SAG: 195.5,
            KEY_DD_MU_BOT: 275.0,
        }
        output_dict = {"design_results": {"deck_report_values": deck_vals}}
        payload = ReportPayload(
            metadata=self.metadata,
            options=self.options,
            inputs={"typical_section.no_of_girders": 2},
            analysis_summary={},
            design_checks=[],
            figures=self.figures,
            output_dict=output_dict,
        )
        bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
        latex = ch5_design_checks([], bridge)
        self.assertIn("195.50", latex)
        self.assertIn("275.00", latex)

    def test_04_missing_input_presentation_clean_dashes(self):
        """Missing geographic, temperature, and seismic values render as '---'."""
        inputs = {}
        ch2_tex = ch2_input_parameters(self.metadata, inputs)
        self.assertIn(r"\textnormal{Latitude / Longitude} & --- \\", ch2_tex)
        self.assertIn(r"\textnormal{Shade Temp. Max / Min (IRC 6)} & --- \\", ch2_tex)

        ch3_tex = ch3_loads(inputs)
        self.assertIn(r"\textnormal{Horizontal Seismic Force (longitudinal)} & --- \\[6pt]", ch3_tex)
        self.assertIn(r"\textnormal{Horizontal Seismic Force (transverse)} & --- \\[6pt]", ch3_tex)
        self.assertNotIn("&  kN", ch3_tex)

    def test_05_figure_placeholder_improved_fallback(self):
        """Figure fallback box uses '[ Figure unavailable in this report export ]'."""
        fbox_standalone = _fig_embed("", "Bridge Cross Section")
        self.assertIn("Figure unavailable in this report export", fbox_standalone)
        self.assertNotIn("PLACEHOLDER", fbox_standalone)

        fig_env = _fig_or_placeholder("", "3D Superstructure")
        self.assertIn("Figure unavailable in this report export", fig_env)
        self.assertNotIn("PLACEHOLDER", fig_env)

    def test_06_boq_placeholder_eliminated(self):
        """calculate_material_quantities defaults to '---' rather than placeholder macros."""
        inputs = {}
        outputs = {}
        quantities = calculate_material_quantities(inputs, outputs)
        for k, v in quantities.items():
            self.assertNotIn("placeholder", str(v).lower(), f"Key {k} has placeholder: {v}")

    def test_07_executive_summary_girder_id_fallback(self):
        """Executive summary falls back to G1, G2 when member IDs are blank."""
        inputs = {"typical_section.no_of_girders": "2"}
        output_dict = {"design_results": {"per_girder": {}}}
        tex = executive_summary(inputs, output_dict, {})
        self.assertIn(r"\textbf{G1}", tex)
        self.assertIn(r"\textbf{G2}", tex)
        self.assertIn("Member ID & G1 & G2", tex)

    def test_08_missing_bending_demand_or_capacity_cannot_produce_pass_or_fail(self):
        """1 & 2: Missing bending demand/capacity produces 'Not calculated', never false PASS or FAIL."""
        # Case A: Both demand and capacity missing
        output_dict = {"deck_report_values": {"vehicle_class": "Class A"}}
        payload = ReportPayload(
            metadata=self.metadata,
            options=self.options,
            inputs={"typical_section.no_of_girders": 2},
            analysis_summary={},
            design_checks=[],
            figures=self.figures,
            output_dict=output_dict,
        )
        bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
        latex = ch5_design_checks([], bridge)

        sag_row_start = latex.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2")
        self.assertGreater(sag_row_start, 0)
        sag_row = latex[sag_row_start:sag_row_start + 120]
        self.assertIn("Not calculated", sag_row)
        self.assertNotIn("PASS", sag_row)
        self.assertNotIn("FAIL", sag_row)

        # Case B: Only demand present, capacity missing
        output_dict2 = {"deck_report_values": {KEY_DD_M_ULS_SAG: 185.0}}
        bridge2 = ReportDataBridge(output_dict2, payload.inputs, payload)
        latex2 = ch5_design_checks([], bridge2)
        sag_row2 = latex2[latex2.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2"):latex2.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2") + 120]
        self.assertIn("Not calculated", sag_row2)
        self.assertNotIn("PASS", sag_row2)
        self.assertNotIn("FAIL", sag_row2)

    def test_09_genuine_bending_pass_and_fail_preserved(self):
        """3 & 4: Genuine calculated PASS and FAIL are preserved."""
        # PASS case: Mu_bot (260) >= M_uls_sag (185)
        output_pass = {
            "deck_report_values": {
                KEY_DD_M_ULS_SAG: 185.0,
                KEY_DD_MU_BOT: 260.0,
            }
        }
        bridge_pass = ReportDataBridge(output_pass, {"typical_section.no_of_girders": 2}, None)
        latex_pass = ch5_design_checks([], bridge_pass)
        sag_row = latex_pass[latex_pass.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2"):latex_pass.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2") + 120]
        self.assertIn("PASS", sag_row)
        self.assertNotIn("FAIL", sag_row)

        # FAIL case: Mu_bot (150) < M_uls_sag (185)
        output_fail = {
            "deck_report_values": {
                KEY_DD_M_ULS_SAG: 185.0,
                KEY_DD_MU_BOT: 150.0,
            }
        }
        bridge_fail = ReportDataBridge(output_fail, {"typical_section.no_of_girders": 2}, None)
        latex_fail = ch5_design_checks([], bridge_fail)
        sag_row_fail = latex_fail[latex_fail.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2"):latex_fail.find("Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2") + 120]
        self.assertIn("FAIL", sag_row_fail)
        self.assertNotIn("PASS", sag_row_fail)

    def test_10_unsupported_shear_displays_not_calculated(self):
        """5 & 6: Unsupported punching shear and one-way shear display Not calculated, not FAIL."""
        output_dict = {
            "deck_report_values": {
                "M_uls_sag": 185.0,
                "Mu_bot": 260.0,
                "punch_ved": 0.62,
                "vrd_c_mpa": 1.10,
                "shear_ved": 110.0,
                "shear_vrdc": 165.0,
            }
        }
        bridge = ReportDataBridge(output_dict, {"typical_section.no_of_girders": 2}, None)
        latex = ch5_design_checks([], bridge)

        # Punching shear check row:
        punch_idx = latex.find(r"Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$")
        self.assertGreater(punch_idx, 0)
        punch_row = latex[punch_idx:punch_idx + 120]
        self.assertIn("Not calculated", punch_row)
        self.assertNotIn("FAIL", punch_row)

        # One-way shear check row:
        shear_idx = latex.find(r"One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$")
        self.assertGreater(shear_idx, 0)
        shear_row = latex[shear_idx:shear_idx + 120]
        self.assertIn("Not calculated", shear_row)
        self.assertNotIn("FAIL", shear_row)

        # Shear disclosures in footnotes:
        self.assertIn("Punching shear verification is not implemented in the current release.", latex)
        self.assertIn("One-way transverse shear verification is not implemented in the current release.", latex)

    def test_11_missing_crack_width_does_not_display_zero_or_pass(self):
        """7: Missing crack width does not display 0.0000 mm or PASS."""
        output_dict = {
            "deck_report_values": {
                "M_uls_sag": 185.0,
                "Mu_bot": 260.0,
            }
        }
        bridge = ReportDataBridge(output_dict, {"typical_section.no_of_girders": 2}, None)
        latex = ch5_design_checks([], bridge)

        cw_start = latex.find(r"\caption{\textbf{Crack Width Check (Deck Slab)}}")
        cw_end = latex.find(r"\caption{\textbf{One-Way (Beam) Shear Check (Deck Slab)}}")
        cw_section = latex[cw_start:cw_end]
        self.assertNotIn("0.0000 mm", cw_section)
        self.assertIn("Not calculated", cw_section)
        self.assertNotIn("PASS", cw_section)

    def test_12_deck_key_resolution_and_canonical_precedence(self):
        """8, 9 & 10: Canonical keys resolve, short aliases resolve, and canonical takes precedence."""
        # 8: Canonical keys
        out_canonical = {
            "deck_report_values": {
                "deck.report.m_uls_sag": 185.0,
                "deck.report.mu_bot": 260.0,
            }
        }
        bridge_canon = ReportDataBridge(out_canonical, {"typical_section.no_of_girders": 2}, None)
        latex_canon = ch5_design_checks([], bridge_canon)
        self.assertIn("185.00", latex_canon)
        self.assertIn("260.00", latex_canon)

        # 9: Short aliases
        out_short = {
            "deck_report_values": {
                "M_uls_sag": 175.5,
                "Mu_bot": 245.5,
            }
        }
        bridge_short = ReportDataBridge(out_short, {"typical_section.no_of_girders": 2}, None)
        latex_short = ch5_design_checks([], bridge_short)
        self.assertIn("175.50", latex_short)
        self.assertIn("245.50", latex_short)

        # 10: Precedence - both provided, canonical must win
        out_both = {
            "deck_report_values": {
                "deck.report.m_uls_sag": 222.0,
                "M_uls_sag": 111.0,
                "deck.report.mu_bot": 333.0,
                "Mu_bot": 444.0,
            }
        }
        bridge_both = ReportDataBridge(out_both, {"typical_section.no_of_girders": 2}, None)
        latex_both = ch5_design_checks([], bridge_both)
        self.assertIn("222.00", latex_both)
        self.assertNotIn("111.00", latex_both)
        self.assertIn("333.00", latex_both)
        self.assertNotIn("444.00", latex_both)

    def test_13_reinforcement_detailing_population_and_missing_handling(self):
        """11 & 12: Available reinforcement detailing populates, missing values remain unavailable."""
        # 11: Available values populate
        out_avail = {
            "deck_report_values": {
                "As_min": 450.0,
                "dia_bot": 16.0,
                "spc_bot": 150.0,
                "As_bot": 1340.0,
                "As_req_bot": 1120.0,
                "As_top": 1340.0,
                "As_req_top": 980.0,
                "As_long": 450.0,
                "min_cover": 40.0,
                "cover_ok": True,
                "spacing_max": 250.0,
            }
        }
        bridge_avail = ReportDataBridge(out_avail, {"typical_section.no_of_girders": 2}, None)
        latex_avail = ch5_design_checks([], bridge_avail)
        self.assertIn(r"$\phi$16 @ 150 mm c/c", latex_avail)
        self.assertIn("1340 mm²/m", latex_avail)
        self.assertIn("1120 mm²/m", latex_avail)
        self.assertIn("450 mm²/m", latex_avail)
        self.assertIn("40 mm", latex_avail)

        # 12: Missing values remain clearly unavailable (placeholder or Not calculated)
        out_miss = {
            "deck_report_values": {
                "M_uls_sag": 185.0,
            }
        }
        bridge_miss = ReportDataBridge(out_miss, {"typical_section.no_of_girders": 2}, None)
        latex_miss = ch5_design_checks([], bridge_miss)
        reinf_sec = latex_miss[latex_miss.find(r"\caption{\textbf{Reinforcement Detailing Summary (Deck Slab)}}"):]
        self.assertIn(r"\placeholder{---}", reinf_sec)
        self.assertNotIn(r"$\phi$\placeholder{---}", reinf_sec)
        self.assertIn("Not calculated", reinf_sec)


if __name__ == "__main__":
    unittest.main()
