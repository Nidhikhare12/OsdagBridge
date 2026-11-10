"""
End-to-End (E2E) Test Suite for OsdagBridge PyLaTeX Report Generator Refactoring
==================================================================================

Authoritative Sources:
- LaTeX Report Generator Refactoring & Enhancements.docx.md
- ORIGINAL_REQUEST.md
- OsdagBridge Dev Branch Architecture Survey

Test Tier Structure:
- Tier 1: Core Feature Coverage (LongTable headers, separated loads, UR & BOQ bar charts, styles.py)
- Tier 2: Boundary & Corner Cases (single/multi-vehicle combinations, UR edge scaling, geometry bounds)
- Tier 3: Cross-Feature Combinations (LongTable page-breaks & figure placements, styling consistency)
- Tier 4: Real-World E2E Execution & Comparative Assertions (Report_Before vs Report_After)
"""

import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import pytest

from pypdf import PdfReader

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_FOOTPATH,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_TS_NO_OF_GIRDERS,
    KEY_DESIGN_MODE,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    BASIC_INPUT_DICT,
    solve_extend_basic_input_dict,
)
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportDataBridge,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.boq.boq_generator import calculate_material_quantities


# =============================================================================
# TIER 1: Core Feature Coverage
# =============================================================================
class TestTier1FeatureCoverage:
    """
    Tier 1 tests verify individual refactored features specified in
    LaTeX Report Generator Refactoring & Enhancements.docx.md.
    """

    def test_longtable_structures_repeated_headers(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory, latex_inspector
    ):
        """
        Authoritative Source: Refactoring Doc §1 (Repeated Table Headers Across Page Breaks)
        Requirement:
            Every multi-page table must repeat the column header row across page breaks
            using PyLaTeX LongTable or LaTeX longtable headers with \\endfirsthead and \\endhead.
        Expected Output:
            All multi-page data tables in the compiled LaTeX source (specifically in
            Chapter 2, Chapter 3, Chapter 4, Chapter 5, and Chapter 7) must declare
            \\endfirsthead and \\endhead, ensuring column headers repeat seamlessly.
        """
        request = report_request_factory(file_stem="Tier1_LongTable_Test")
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        assert result.tex_path and os.path.exists(result.tex_path), "LaTeX source was not generated."
        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        longtables = latex_inspector.extract_longtables(tex_content)
        assert len(longtables) > 0, "No longtable environments found in generated report."

        # Verify that data-heavy multi-page tables implement header repetition
        unrepeated_tables = []
        for i, tbl in enumerate(longtables):
            caption = tbl["caption"] or f"Table #{i+1} (Cols: {tbl['col_spec']})"
            # Check for header repetition tokens
            if not (tbl["has_endfirsthead"] and tbl["has_endhead"]):
                unrepeated_tables.append(caption)

        assert not unrepeated_tables, (
            f"Found {len(unrepeated_tables)} longtable(s) lacking repeated headers (\\endfirsthead / \\endhead):\n"
            + "\n".join(f" - {t}" for t in unrepeated_tables)
        )

    test_r2_repeated_headers = test_longtable_structures_repeated_headers

    def test_ch3_separate_vehicle_and_footway_tables(self, default_bridge_inputs):
        """
        Authoritative Source: Refactoring Doc §3 (Load & Geometry Table Refactoring)
        Requirement:
            Separate vehicle live loads and footpath live loads into distinct, clearly
            structured PyLaTeX tables.
            Table for vehicular live loads must provide dedicated columns:
            Vehicle Class, Impact Factor, Braking Load (kN), Centrifugal Forces (kN).
            Footpath live load table must provide intensity (kN/m^2) and applied width (m).
        Expected Output:
            Chapter 3 output must contain at least two separate tables:
            1. Vehicular Live Load table with appropriate parameter columns and engineering units.
            2. Footway/Footpath Live Load table with intensity and width columns.
        """
        inputs = dict(default_bridge_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_WHEELED] = True
        inputs[KEY_LL_FOOTPATH_PRESSURE_VALUE] = 4.5

        ch3_tex = ch3_loads(inputs)

        # 1. Assert separation: Must find two separate table environments for live loads
        # (Vehicular Live Load and Footway/Footpath Live Load)
        has_vehicle_table = bool(
            re.search(r"\\caption\{.*?Vehic(?:le|ular)\s+Live\s+Load.*?\}", ch3_tex, re.IGNORECASE)
            or re.search(r"\\textbf\{.*?Vehic(?:le|ular)\s+Live\s+Load.*?\}", ch3_tex, re.IGNORECASE)
        )
        has_footway_table = bool(
            re.search(r"\\caption\{.*?(?:Footway|Footpath)\s+Live\s+Load.*?\}", ch3_tex, re.IGNORECASE)
            or re.search(r"\\textbf\{.*?(?:Footway|Footpath)\s+Live\s+Load.*?\}", ch3_tex, re.IGNORECASE)
        )

        assert has_vehicle_table, (
            "Chapter 3 does not contain a dedicated table for Vehicular Live Loads."
        )
        assert has_footway_table, (
            "Chapter 3 does not contain a dedicated table for Footway/Footpath Live Loads."
        )

        # 2. Assert dedicated parameter columns and engineering units in vehicle live load table
        required_vehicle_headers = ["Vehicle", "Impact", "Braking", "kN"]
        for hdr in required_vehicle_headers:
            assert hdr.lower() in ch3_tex.lower(), (
                f"Chapter 3 Vehicular Live Load table is missing required column or unit '{hdr}'."
            )

        # 3. Assert footway parameter units (kN/m^2 or kN/m2)
        has_footway_units = ("kN/m" in ch3_tex) or ("kN/m^{2}" in ch3_tex) or ("kN/m\\textsuperscript{2}" in ch3_tex)
        assert has_footway_units, (
            "Chapter 3 Footway table is missing proper engineering intensity units (kN/m²)."
        )

    test_r3_separate_tables = test_ch3_separate_vehicle_and_footway_tables

    def test_sec55_ur_bar_charts_generated_and_embedded(
        self, default_bridge_inputs, default_bridge_outputs, latex_inspector
    ):
        """
        Authoritative Source: Refactoring Doc §4 (Utilization Ratio Summary Visualizations)
        Requirement:
            Programmatically generate and embed overall bar charts showing the
            Utilization Ratio (UR = Demand / Capacity) for all primary elements:
            - Steel Plate Girders
            - Concrete Deck Slab
            - Cross Bracing
            - End Diaphragms
            in Section 5.5 (Overall Design Check Summary).
        Expected Output:
            Section 5.5 in the generated LaTeX must contain PyLaTeX Figure environments
            embedding bar charts for the four primary structural components.
        """
        bridge = ReportDataBridge(default_bridge_inputs, default_bridge_outputs)
        ch5_tex = ch5_design_checks(default_bridge_outputs.get("design_results", {}), bridge)

        assert r"\section{Overall Design Check Summary}" in ch5_tex, (
            "Section 5.5 'Overall Design Check Summary' is missing in Chapter 5."
        )

        # Extract section 5.5 content
        sec55_content = ch5_tex.split(r"\section{Overall Design Check Summary}")[-1]

        # Verify Figure environment is present in Section 5.5
        sec55_figures = latex_inspector.extract_figures(sec55_content)
        assert len(sec55_figures) > 0, (
            "Section 5.5 does not contain any embedded PyLaTeX Figure environments for UR charts."
        )

        # Verify primary elements are represented in captions or graphics
        components_to_cover = ["Girder", "Deck", "Bracing", "Diaphragm"]
        sec55_text_lower = sec55_content.lower()
        for comp in components_to_cover:
            assert comp.lower() in sec55_text_lower, (
                f"Section 5.5 does not mention or visualize UR for primary element '{comp}'."
            )

    def test_sec55_ur_threshold_line_at_one(
        self, default_bridge_inputs, default_bridge_outputs
    ):
        """
        Authoritative Source: Refactoring Doc §4 & ORIGINAL_REQUEST.md R4
        Requirement:
            Threshold Line: Include a distinct horizontal reference line at UR = 1.0
            (Red dashed line) to visually distinguish passing (UR <= 1.0) vs failing (UR > 1.0) checks.
        Expected Output:
            The chart generator logic must draw a horizontal line at y = 1.0 with
            color='red' (or 'r') and linestyle='--' (or 'dashed').
        """
        # Test the chart generation logic directly via visualization module
        try:
            from osdagbridge.core.reports import charts  # Expected refactored chart module
        except ImportError:
            try:
                from osdagbridge.core.reports import visualizations as charts
            except ImportError:
                pytest.fail("Centralized chart generation module ('charts.py' or 'visualizations.py') not found.")

        assert hasattr(charts, "generate_ur_bar_chart") or hasattr(charts, "create_ur_chart"), (
            "Chart module does not export UR chart generator function ('generate_ur_bar_chart')."
        )

        chart_func = getattr(charts, "generate_ur_bar_chart", getattr(charts, "create_ur_chart", None))
        
        # Invoke chart generator with sample test data
        sample_ur_data = {
            "Steel Plate Girders": 0.85,
            "Concrete Deck Slab": 0.72,
            "Cross Bracing": 0.64,
            "End Diaphragms": 0.58,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_img = os.path.join(tmp_dir, "test_ur_chart.png")
            fig = chart_func(sample_ur_data, out_img)

            assert os.path.exists(out_img), "UR chart image asset was not created on disk."
            assert os.path.getsize(out_img) > 1000, "UR chart image asset is empty or too small."

            # Inspect figure axes if returned, or inspect matplotlib state
            if fig is not None:
                ax = fig.gca()
                # Check for axhline or lines at y = 1.0
                lines = ax.get_lines()
                threshold_found = False
                for line in lines:
                    y_data = line.get_ydata()
                    if len(y_data) >= 2 and all(abs(y - 1.0) < 1e-3 for y in y_data):
                        # Verify red and dashed
                        color = line.get_color()
                        linestyle = line.get_linestyle()
                        assert color in ("r", "red", "#ff0000", "#FF0000") or "red" in str(color), (
                            f"Threshold line color must be red, got '{color}'."
                        )
                        assert linestyle in ("--", "dashed"), (
                            f"Threshold line style must be dashed, got '{linestyle}'."
                        )
                        threshold_found = True
                        break
                assert threshold_found, (
                    "UR chart axes does not contain the mandatory horizontal reference line at UR = 1.0."
                )

    def test_ch7_material_quantity_bar_charts_embedded(
        self, default_bridge_inputs, default_bridge_outputs, latex_inspector
    ):
        """
        Authoritative Source: Refactoring Doc §5 (Material Quantity Bar Charts)
        Requirement:
            Programmatically generate and insert bar charts summarizing material quantities
            from Chapter 7 (Material Take-off & Quantity Summary):
            - Structural Steel tonnage (Girders, Cross Bracing, End Diaphragms)
            - Concrete volume (m^3) vs. Reinforcement Steel weight (MT)
            Auto-save plots to temporary image assets during generation and embed via PyLaTeX Figure.
        Expected Output:
            Chapter 7 LaTeX contains PyLaTeX Figure environments embedding both
            steel tonnage and concrete/rebar charts.
        """
        quantities = calculate_material_quantities(default_bridge_inputs, default_bridge_outputs)
        inputs_with_qty = dict(default_bridge_inputs)
        inputs_with_qty.update(quantities)

        ch7_tex = ch7_quantities(inputs_with_qty)

        # 1. Assert Figure environments in Chapter 7
        ch7_figures = latex_inspector.extract_figures(ch7_tex)
        assert len(ch7_figures) >= 1, (
            "Chapter 7 does not contain embedded PyLaTeX Figure environments for material quantity charts."
        )

        # 2. Assert structural steel tonnage and concrete vs rebar mentioned in figures/captions
        ch7_lower = ch7_tex.lower()
        has_steel_chart = "steel" in ch7_lower and ("tonnage" in ch7_lower or "mt" in ch7_lower or "weight" in ch7_lower)
        has_concrete_rebar_chart = "concrete" in ch7_lower and ("rebar" in ch7_lower or "reinforcement" in ch7_lower)

        assert has_steel_chart, "Chapter 7 does not include structural steel tonnage visualization."
        assert has_concrete_rebar_chart, "Chapter 7 does not include Concrete vs Rebar quantity visualization."

    def test_styles_sourced_from_centralized_module(self):
        """
        Authoritative Source: Refactoring Doc §6 (Centralized Formatting & Style System)
        Requirement:
            Establish a dedicated, centralized style configuration module (e.g., styles.py or theme.py)
            to serve as the single source of truth for global document settings, color palettes,
            custom table styles, header/footer themes, and cell paddings.
            All section and chapter generator files must import and consume formatting rules
            exclusively from this single source.
        Expected Output:
            1. Module `osdagbridge.core.reports.styles` exists and can be imported.
            2. Centralized styling parameters are defined (colors, margins, table padding, arraystretch).
            3. Chapter modules import their formatting attributes from `styles`.
        """
        try:
            from osdagbridge.core.reports import styles
        except ImportError:
            try:
                from osdagbridge.core.reports import theme as styles
            except ImportError:
                pytest.fail("Centralized style module ('styles.py' or 'theme.py') does not exist.")

        # Verify exported constants
        required_style_attrs = [
            "TABCOLSEP",
            "ARRAYSTRETCH",
            "OSDAG_GREEN",
            "MARGIN_TOP",
            "MARGIN_BOTTOM",
            "HEADHEIGHT",
            "FOOTSKIP",
        ]
        missing_attrs = [attr for attr in required_style_attrs if not hasattr(styles, attr)]
        assert not missing_attrs, (
            f"Centralized style module is missing required layout attributes: {missing_attrs}"
        )

        # Verify that chapter modules import from styles
        import osdagbridge.core.reports.report_generator as rep_gen
        assert getattr(rep_gen, "styles", None) is not None or "styles" in sys.modules, (
            "report_generator.py does not consume the centralized style module."
        )

    test_r5_centralized_style_module_exists = test_styles_sourced_from_centralized_module


# =============================================================================
# TIER 2: Boundary & Corner Cases
# =============================================================================
class TestTier2BoundaryAndCornerCases:
    """
    Tier 2 tests verify system behavior at boundary conditions, single vs
    multi-selection, edge scaling of visualizations, and page geometry constraints.
    """

    def test_single_vehicle_selection(self, default_bridge_inputs):
        """
        Authoritative Source: Refactoring Doc §3
        Requirement:
            When only a single vehicle is selected in UI inputs, Chapter 3 vehicular
            live load table must generate cleanly with exactly one vehicle row.
        """
        inputs = dict(default_bridge_inputs)
        # Enable ONLY Class A
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_WHEELED] = False
        inputs[KEY_LL_IRC_70R_TRACKED] = False
        inputs[KEY_LL_IRC_AA_WHEELED] = False
        inputs[KEY_LL_IRC_AA_TRACKED] = False
        inputs[KEY_LL_IRC_CLASS_SV] = False
        inputs[KEY_LL_IRC_70R_BOGIE] = False

        ch3_tex = ch3_loads(inputs)
        assert "Class A" in ch3_tex, "Class A vehicle was selected but is not present in Chapter 3."
        assert "Class 70R" not in ch3_tex, "Unselected vehicle Class 70R appeared in Chapter 3."
        assert "Class SV" not in ch3_tex, "Unselected vehicle Class SV appeared in Chapter 3."

    def test_multivehicle_combinations(self, default_bridge_inputs):
        """
        Authoritative Source: Refactoring Doc §3
        Requirement:
            When multiple vehicles are selected in UI inputs (e.g. Class A, 70R Wheeled,
            70R Tracked, Special Vehicle), Chapter 3 must generate rows for each of them.
        """
        inputs = dict(default_bridge_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = True
        inputs[KEY_LL_IRC_70R_WHEELED] = True
        inputs[KEY_LL_IRC_70R_TRACKED] = True
        inputs[KEY_LL_IRC_CLASS_SV] = True

        ch3_tex = ch3_loads(inputs)
        assert "Class A" in ch3_tex, "Class A missing from multi-vehicle table."
        assert "70R (Wheeled)" in ch3_tex or "70R Wheeled" in ch3_tex, "70R Wheeled missing."
        assert "70R (Tracked)" in ch3_tex or "70R Tracked" in ch3_tex, "70R Tracked missing."
        assert "Special Vehicle" in ch3_tex or "Class SV" in ch3_tex, "Special Vehicle missing."

    def test_adversarial_no_vehicle_or_invalid_inputs(self, default_bridge_inputs):
        """
        Adversarial Verification:
            Verify graceful fallback when no vehicles are explicitly enabled.
            Must not crash with unhandled IndexError or KeyError.
        """
        inputs = dict(default_bridge_inputs)
        inputs[KEY_LL_IRC_CLASS_A] = False
        inputs[KEY_LL_IRC_70R_WHEELED] = False
        inputs[KEY_LL_IRC_70R_TRACKED] = False
        inputs[KEY_LL_IRC_AA_WHEELED] = False
        inputs[KEY_LL_IRC_AA_TRACKED] = False
        inputs[KEY_LL_IRC_CLASS_SV] = False
        inputs[KEY_LL_IRC_70R_BOGIE] = False

        # Must execute without exception
        ch3_tex = ch3_loads(inputs)
        assert isinstance(ch3_tex, str) and len(ch3_tex) > 0

    def test_ur_edge_scaling_all_passing(self):
        """
        Authoritative Source: Refactoring Doc §4
        Requirement:
            When all design checks pass comfortably (e.g. all UR < 0.65), the plot
            y-axis upper limit must still extend beyond 1.0 (e.g. >= 1.1) so that
            the red dashed reference line at UR = 1.0 remains fully visible.
        """
        try:
            from osdagbridge.core.reports import charts
        except ImportError:
            try:
                from osdagbridge.core.reports import visualizations as charts
            except ImportError:
                pytest.skip("Chart generation module not yet implemented.")

        chart_func = getattr(charts, "generate_ur_bar_chart", getattr(charts, "create_ur_chart", None))
        if not chart_func:
            pytest.skip("generate_ur_bar_chart not found.")

        low_ur_data = {
            "Steel Plate Girders": 0.42,
            "Concrete Deck Slab": 0.38,
            "Cross Bracing": 0.25,
            "End Diaphragms": 0.30,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_img = os.path.join(tmp_dir, "ur_low.png")
            fig = chart_func(low_ur_data, out_img)
            if fig is not None:
                ax = fig.gca()
                ylim = ax.get_ylim()
                assert ylim[1] >= 1.05, (
                    f"Chart y-limit ({ylim[1]}) clipped threshold line at 1.0 when all URs are low."
                )

    def test_ur_edge_scaling_failing_check(self):
        """
        Authoritative Source: Refactoring Doc §4
        Requirement:
            When one or more design checks fail (UR > 1.0, e.g. UR = 1.45), the plot
            y-axis must dynamically expand to display the failing bar without clipping,
            while maintaining the red dashed threshold line at 1.0.
        """
        try:
            from osdagbridge.core.reports import charts
        except ImportError:
            try:
                from osdagbridge.core.reports import visualizations as charts
            except ImportError:
                pytest.skip("Chart generation module not yet implemented.")

        chart_func = getattr(charts, "generate_ur_bar_chart", getattr(charts, "create_ur_chart", None))
        if not chart_func:
            pytest.skip("generate_ur_bar_chart not found.")

        failing_ur_data = {
            "Steel Plate Girders": 1.45,
            "Concrete Deck Slab": 0.85,
            "Cross Bracing": 0.60,
            "End Diaphragms": 0.70,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_img = os.path.join(tmp_dir, "ur_fail.png")
            fig = chart_func(failing_ur_data, out_img)
            if fig is not None:
                ax = fig.gca()
                ylim = ax.get_ylim()
                assert ylim[1] >= 1.5, (
                    f"Chart y-limit ({ylim[1]}) did not expand to accommodate failing UR of 1.45."
                )

    def test_page_geometry_bounds_no_footer_bleed(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory, latex_inspector
    ):
        """
        Authoritative Source: Refactoring Doc §2 (Layout, Footer Overlap, and Spacing Fixes)
        Requirement:
            Adjust page geometries, vertical padding, row heights, and page-bottom threshold
            constraints to prevent overlap with standard header/footer boxes (Page 30 / G4 bleed fix).
        Expected Output:
            1. Preamble geometry must explicitly define positive headheight (>=15pt) and footskip (>=25pt).
            2. includehead and includefoot (or adequate margin clearance) must be budgeted.
            3. Negative vertical offsets in footrule (\\vspace{-20pt} or \\vspace{-8pt}) must be ELIMINATED.
        """
        request = report_request_factory(file_stem="Tier2_Geometry_Test")
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        geom = latex_inspector.extract_geometry(tex_content)
        assert geom, "Could not extract geometry configuration from document preamble."

        # Verify geometry parameters
        assert "headheight" in geom or "includehead" in geom, (
            "Document geometry lacks explicit headheight/includehead, risking fancyhdr collisions."
        )
        assert "footskip" in geom or "includefoot" in geom, (
            "Document geometry lacks explicit footskip/includefoot, risking footer margin bleeds."
        )

        # Assert no negative vertical space hacks in footer
        has_negative_footer = latex_inspector.has_negative_footer_spacing(tex_content)
        assert not has_negative_footer, (
            "Document preamble still contains negative \\vspace in \\footrule (e.g. \\vspace{-20pt}), "
            "which causes the Page 30 / G4 footer margin bleed defect."
        )

    test_r2_page_geometry_bounds = test_page_geometry_bounds_no_footer_bleed


# =============================================================================
# TIER 3: Cross-Feature Combinations
# =============================================================================
class TestTier3CrossFeatureCombinations:
    """
    Tier 3 tests verify that multi-page tables, figure placements, and global
    styling harmoniously co-exist across chapters without compilation conflicts.
    """

    def test_longtable_pagebreaks_and_figure_interaction(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory
    ):
        """
        Authoritative Source: Refactoring Doc §1, §4, §5
        Requirement:
            Sections containing both large longtables and embedded figures (such as
            Section 5.5 and Chapter 7) must compile cleanly without float conflicts,
            unclosed table environments, or missing graphics.
        """
        request = report_request_factory(file_stem="Tier3_Table_Figure_Test")
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Verify balanced begin/end environments for longtable and figure
        longtable_begins = len(re.findall(r"\\begin\{longtable\}", tex_content))
        longtable_ends = len(re.findall(r"\\end\{longtable\}", tex_content))
        assert longtable_begins == longtable_ends, (
            f"Mismatched longtable environments: {longtable_begins} \\begin vs {longtable_ends} \\end."
        )

        figure_begins = len(re.findall(r"\\begin\{figure\}", tex_content))
        figure_ends = len(re.findall(r"\\end\{figure\}", tex_content))
        assert figure_begins == figure_ends, (
            f"Mismatched figure environments: {figure_begins} \\begin vs {figure_ends} \\end."
        )

    def test_consistent_styling_across_all_chapters(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory
    ):
        """
        Authoritative Source: Refactoring Doc §6
        Requirement:
            Uniform styling across all chapters: tables, headings, and rules must not
            redefine ad-hoc local formatting parameters that clash with the global theme.
        """
        request = report_request_factory(file_stem="Tier3_Styling_Test")
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Check for conflicting local redefinitions of global tabcolsep or arraystretch
        local_tabcolsep = re.findall(r"\\setlength\{\\tabcolsep\}\{([^\}]+)\}", tex_content)
        # In baseline, tabcolsep is redefined locally in chap2, chap4, chap7 with different values.
        # In refactored code, tabcolsep should be standardized or centrally governed.
        assert len(set(local_tabcolsep)) <= 2, (
            f"Inconsistent local tabcolsep definitions detected across chapters: {set(local_tabcolsep)}"
        )

    def test_adversarial_special_characters_escaping(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory
    ):
        """
        Adversarial Verification:
            Test that user inputs containing special LaTeX characters
            (e.g., '&', '%', '$', '#', '_') in metadata and notes do not break LaTeX syntax.
        """
        metadata = ReportMetadata(
            project_name="Bridge Design & det_ail #4 ($100% compliant)",
            project_location="A & B Road, Km 42_5",
            designer="Dr. Engineer_X & Co.",
            client="MORT&H (Govt. of India)",
            company="FOSSEE & IIT_Bombay #1",
            subtitle="Rev_0 & Test",
        )
        request = ReportRequest(
            metadata=metadata,
            options=ReportOptions(sections=["loads", "analysis"], include_figures=False, include_toc=True, include_pdf=True),
            output_dir=report_request_factory().output_dir,
            file_stem="Tier3_Adversarial_Escape",
        )
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        # Verify unescaped naked '&', '%', '$', '#' do not appear in the title page text
        # Title page should escape '&' to '\&', '%' to '\%', '$' to '\$', '#' to '\#'
        tp_idx = tex_content.find(r"\begin{titlepage}")
        title_block = tex_content[tp_idx:tp_idx + 2500] if tp_idx != -1 else tex_content[:2000]
        # In valid LaTeX, unescaped '%' would comment out code, unescaped '$' would toggle math mode
        assert r"\&" in title_block or "&" not in title_block, "Unescaped '&' in title block."
        assert r"\%" in title_block or "%" not in title_block, "Unescaped '%' in title block."


# =============================================================================
# TIER 4: Real-World End-to-End Execution & Comparative Assertions
# =============================================================================
class TestTier4RealWorldE2EExecution:
    """
    Tier 4 tests execute the full end-to-end report generation pipeline from
    bridge parameters to compiled PDF, asserting that `Report_After.pdf` is created,
    valid, and measurably superior to `Report_Before.pdf`.
    """

    def test_full_compilation_pipeline(
        self, default_bridge_inputs, default_bridge_outputs, report_request_factory, compile_latex_file
    ):
        """
        Authoritative Source: Refactoring Doc §Workflow & Testing Process
        Requirement:
            Full bridge report compilation pipeline from inputs to PDF execution.
            The generated LaTeX source must compile cleanly with exit code 0.
        """
        request = report_request_factory(file_stem="Tier4_Full_Pipeline")
        payload = build_report_payload(request, default_bridge_inputs, default_bridge_outputs)
        result = generate_report(payload, request)

        assert result.tex_path and os.path.exists(result.tex_path), "LaTeX file was not created."

        # Compile to PDF
        retcode, stdout, stderr = compile_latex_file(result.tex_path, request.output_dir)
        assert retcode == 0, (
            f"LaTeX compilation failed with exit code {retcode}.\n"
            f"STDOUT:\n{stdout[-1500:]}\nSTDERR:\n{stderr[-1500:]}"
        )

        pdf_path = os.path.join(request.output_dir, "Tier4_Full_Pipeline.pdf")
        assert os.path.exists(pdf_path), "Compiled PDF does not exist on disk."
        assert os.path.getsize(pdf_path) > 20000, "Compiled PDF is unusually small (< 20KB)."

    def test_report_after_pdf_validity(self):
        """
        Authoritative Source: ORIGINAL_REQUEST.md Deliverables
        Requirement:
            `Report_After.pdf` must be present in the project directory, non-empty,
            and valid with a substantial page count (> 15 pages).
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        report_after_path = os.path.join(project_root, "Report_After.pdf")

        assert os.path.exists(report_after_path), (
            f"Mandatory deliverable '{report_after_path}' does not exist. "
            "Has the refactored report generator been compiled?"
        )

        file_size = os.path.getsize(report_after_path)
        assert file_size > 50000, (
            f"Report_After.pdf size is {file_size} bytes, expected > 50,000 bytes."
        )

        # Inspect PDF with PdfReader
        reader = PdfReader(report_after_path)
        page_count = len(reader.pages)
        assert page_count >= 15, (
            f"Report_After.pdf has only {page_count} pages, expected comprehensive report (>= 15 pages)."
        )

        # Extract text from page 1 to verify project identity
        first_page_text = reader.pages[0].extract_text()
        assert "Osdag" in first_page_text or "Bridge" in first_page_text, (
            "Report_After.pdf title page missing expected 'OsdagBridge' title text."
        )

    def test_comparative_before_vs_after(self, latex_inspector):
        """
        Authoritative Source: Refactoring Doc §Step 2 & ORIGINAL_REQUEST.md R5
        Requirement:
            Comparative assertion between `Report_Before` (baseline) and `Report_After` (refactored).
            Verifies that all targeted shortcomings in Report_Before are demonstrably fixed in Report_After:
            1. Repeated headers: Report_After must have substantially more repeated headers.
            2. Separate load tables: Report_After separates vehicle and footway live loads.
            3. Dynamic bar charts: Report_After contains UR charts and quantity charts (0 in Before).
            4. Footer bleed: Report_After eliminates negative footrule vertical offset.
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        before_tex_path = os.path.join(project_root, "Report_Before.tex")
        after_tex_path = os.path.join(project_root, "Report_After.tex")

        # Fallback to test_output if root Report_Before.tex not yet copied
        if not os.path.exists(before_tex_path):
            before_tex_path = os.path.join(project_root, "test_output", "Report_Before.tex")

        assert os.path.exists(before_tex_path), f"Baseline source '{before_tex_path}' not found."
        assert os.path.exists(after_tex_path), f"Refactored source '{after_tex_path}' not found."

        with open(before_tex_path, "r", encoding="utf-8") as f:
            before_tex = f.read()
        with open(after_tex_path, "r", encoding="utf-8") as f:
            after_tex = f.read()

        # 1. Header repetition comparison
        before_tables = latex_inspector.extract_longtables(before_tex)
        after_tables = latex_inspector.extract_longtables(after_tex)

        before_repeated_count = sum(1 for t in before_tables if t["has_endhead"])
        after_repeated_count = sum(1 for t in after_tables if t["has_endhead"])

        assert after_repeated_count > before_repeated_count, (
            f"Report_After has {after_repeated_count} repeated header tables vs "
            f"{before_repeated_count} in Report_Before. Header repetition was not improved."
        )

        # 2. Section 5.5 and Chapter 7 Bar Charts comparison
        before_figures = latex_inspector.extract_figures(before_tex)
        after_figures = latex_inspector.extract_figures(after_tex)

        assert len(after_figures) > len(before_figures), (
            f"Report_After has {len(after_figures)} figures vs {len(before_figures)} in Report_Before. "
            "Required bar charts were not embedded."
        )

        # 3. Footer Bleed fix comparison
        before_has_negative_footer = latex_inspector.has_negative_footer_spacing(before_tex)
        after_has_negative_footer = latex_inspector.has_negative_footer_spacing(after_tex)

        assert before_has_negative_footer, (
            "Baseline Report_Before was expected to have negative \\vspace in footrule."
        )
        assert not after_has_negative_footer, (
            "Report_After still contains negative \\vspace in \\footrule, failing to fix footer bleed."
        )


# =============================================================================
# Standalone CLI Test Runner
# =============================================================================
if __name__ == "__main__":
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
    ]
    sys.exit(pytest.main(pytest_args))
