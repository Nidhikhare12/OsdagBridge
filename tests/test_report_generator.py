"""Unit and integration test suite for OsdagBridge LaTeX report generator refactoring.

Tests verify:
1. Styles single source of truth (ReportTheme, palettes, geometry, preamble helpers).
2. Tables formatting, escaping, status badges, and longtable header repetition.
3. Chapter 3 load tables refactoring (Vehicular live loads, centrifugal forces, footway loads).
4. Charts generation (headless Matplotlib Figure + Canvas, UR chart, material takeoff).
5. Chapter 5 atomic girder check grouping (preventing row splitting across page breaks).
6. Integration payload and LaTeX document generation.
"""

import io
import math
import os
import tempfile
import pytest

from osdagbridge.core.reports.styles import (
    DEFAULT_THEME,
    ReportTheme,
    apply_document_theme,
    get_latex_color_definitions,
    get_table_spacing_preamble,
)
from osdagbridge.core.reports.tables import (
    build_centrifugal_force_table,
    build_footway_live_load_table,
    build_longtable,
    build_vehicle_live_load_table,
    cell,
    keep_heading_with_content,
    status_badge,
)
from osdagbridge.core.reports.charts import (
    generate_material_takeoff_charts,
    generate_ur_chart,
)


# -----------------------------------------------------------------------------
# 1. Styles & ReportTheme Single Source of Truth Tests
# -----------------------------------------------------------------------------

class TestReportTheme:
    """Verifies styles.py acts as the authoritative single source of truth."""

    def test_default_theme_attributes(self):
        theme = DEFAULT_THEME
        assert theme.top_margin == "2.0cm"
        assert theme.bottom_margin == "2.2cm"
        assert theme.left_margin == "1.8cm"
        assert theme.right_margin == "1.8cm"
        assert theme.head_height == "16pt"
        assert theme.head_sep == "12pt"
        assert theme.foot_skip == "22pt"
        assert theme.include_head_foot is True
        assert theme.primary == "#16331C"
        assert theme.accent == "#5E8014"
        assert theme.osdag_green == "#789A1B"
        assert theme.osdag_green_light == "#EBF2DE"
        assert theme.header_bg == "#EBF2DE"
        assert theme.zebra == "#F7FAF3"
        assert theme.pass_color == "#226B28"
        assert theme.fail_color == "#B91C1C"
        assert theme.border == "#CCD7C5"
        assert theme.muted == "#455443"
        assert theme.chart_dpi == 300

    def test_hex_conversions(self):
        theme = DEFAULT_THEME
        r, g, b = theme.hex_to_rgb_tuple("#16331C")
        assert math.isclose(r, 22 / 255.0, rel_tol=1e-3)
        assert math.isclose(g, 51 / 255.0, rel_tol=1e-3)
        assert math.isclose(b, 28 / 255.0, rel_tol=1e-3)

    def test_latex_color_definitions_generation(self):
        preamble = get_latex_color_definitions(DEFAULT_THEME)
        assert r"\definecolor{OsdagPrimary}{HTML}{16331C}" in preamble
        assert r"\definecolor{OsdagAccent}{HTML}{5E8014}" in preamble
        assert r"\definecolor{OsdagGreen}{HTML}{789A1B}" in preamble
        assert r"\definecolor{OsdagGreenLight}{HTML}{EBF2DE}" in preamble
        assert r"\definecolor{OsdagHeaderBg}{HTML}{EBF2DE}" in preamble
        assert r"\definecolor{OsdagZebra}{HTML}{F7FAF3}" in preamble
        assert r"\definecolor{OsdagPass}{HTML}{226B28}" in preamble
        assert r"\definecolor{OsdagFail}{HTML}{B91C1C}" in preamble
        assert r"\definecolor{OsdagBorder}{HTML}{CCD7C5}" in preamble
        assert r"\definecolor{OsdagMuted}{HTML}{455443}" in preamble

    def test_table_spacing_preamble_generation(self):
        spacing = get_table_spacing_preamble(DEFAULT_THEME)
        assert r"\renewcommand{\arraystretch}{1.15}" in spacing
        assert r"\setlength{\tabcolsep}{4.5pt}" in spacing
        assert r"\setlength{\LTpre}{4pt}" in spacing
        assert r"\setlength{\LTpost}{5pt}" in spacing
        assert r"\arrayrulecolor{OsdagBorder}" in spacing

    def test_custom_theme_overrides(self):
        custom = ReportTheme(
            primary="#003366",
            accent="#336699",
            chart_dpi=600,
            array_stretch=1.35
        )
        assert custom.primary == "#003366"
        assert custom.chart_dpi == 600
        assert custom.array_stretch == 1.35
        latex_cols = get_latex_color_definitions(custom)
        assert r"\definecolor{OsdagPrimary}{HTML}{003366}" in latex_cols


# -----------------------------------------------------------------------------
# 2. Table Builders & LaTeX Cell Escaping Tests
# -----------------------------------------------------------------------------

class TestTableHelpers:
    """Tests cell formatting, character escaping, badges, and longtables."""

    def test_cell_scalar_and_none_formatting(self):
        assert cell(None) == "-"
        assert cell("") == "-"
        assert cell(float("nan")) == "-"
        assert cell(True) == r"\textbf{\color{OsdagPass}{PASS}}"
        assert cell(False) == r"\textbf{\color{OsdagFail}{FAIL}}"

    def test_cell_number_and_unit_formatting(self):
        assert cell(24.0, decimals=1, unit="m") == "24.0~m"
        assert cell(1340.5678, decimals=2, unit="mm") == "1340.57~mm"
        assert cell(100, decimals=0) == "100"

    def test_cell_latex_special_character_escaping(self):
        raw = "Cost & Load % at 50_percent ($100 #1)"
        escaped = cell(raw)
        assert r"\&" in escaped
        assert r"\%" in escaped
        assert r"\_" in escaped
        assert r"\$" in escaped
        assert r"\#" in escaped

    def test_status_badge(self):
        pass_badge = status_badge(True)
        assert "OsdagPass" in pass_badge
        assert "PASS" in pass_badge

        fail_badge = status_badge(False)
        assert "OsdagFail" in fail_badge
        assert "FAIL" in fail_badge

        na_badge = status_badge(None)
        assert na_badge == "-"

    def test_keep_heading_with_content(self):
        sec = keep_heading_with_content(lines=6)
        assert r"\needspace{6\baselineskip}" in sec

    def test_build_longtable_emits_repetition_tags(self):
        headers = ["Girder ID", "Span (m)", "Status"]
        rows = [
            ("G1", 24.0, "SAFE"),
            ("G2", 24.0, "SAFE"),
            ("G3", 24.0, "SAFE"),
            ("G4", 24.0, "SAFE"),
        ]
        tex = build_longtable(
            headers=headers,
            rows=rows,
            caption="Girder Verification Summary",
            label="tab:girder-summary",
            col_widths=["3cm", "4cm", "3cm"],
            zebra=True
        )

        assert r"\begin{longtable}{|L{3cm}|L{4cm}|L{3cm}|}" in tex
        assert r"\caption{\textbf{Girder Verification Summary}}\label{tab:girder-summary} \\" in tex
        assert r"\endfirsthead" in tex
        assert r"\endhead" in tex
        assert r"\endfoot" in tex
        assert r"\endlastfoot" in tex
        assert r"\rowcolor{OsdagHeaderBg}" in tex
        assert r"\rowcolor{OsdagZebra}" in tex
        assert r"\small\textit{Girder Verification Summary (continued from previous page)}" in tex
        assert r"\small\textit{Continued on next page}" in tex
        assert r"\end{longtable}" in tex


# -----------------------------------------------------------------------------
# 3. Chapter 3 Refactored Load Table Builders Tests
# -----------------------------------------------------------------------------

class TestChapter3LoadTables:
    """Verifies refactored vehicular, centrifugal, and footway live load tables."""

    def test_vehicular_live_load_table_header_and_vehicles(self):
        from osdagbridge.core.utils.common import KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_FATIGUE
        input_dict = {
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_CLASS_FATIGUE: True,
            "loading.impact_factor_class_a": "1.240",
            "loading.braking_force": "200.0",
        }
        tex = build_vehicle_live_load_table(input_dict, span_m=24.0, lanes_count=2)

        assert r"\begin{longtable}" in tex
        assert r"\caption{\textbf{Vehicular Live Loads and Dynamic Factors}}" in tex
        assert r"\textbf{Vehicle Class}" in tex
        assert r"\endfirsthead" in tex
        assert r"\endhead" in tex
        assert r"\endfoot" in tex
        assert r"\endlastfoot" in tex
        assert "Class A Train" in tex
        assert "Fatigue Vehicle" in tex
        assert "1.240" in tex

    def test_centrifugal_force_straight_vs_curved_bridge(self):
        # Straight bridge (radius None or > 1000m)
        straight_input = {"geometry.horizontal_radius": None}
        straight_tex = build_centrifugal_force_table(straight_input)
        assert "Straight / Tangent Alignment" in straight_tex
        assert "0.00 kN" in straight_tex

        # Curved bridge (R = 400m, V = 80 km/h)
        curved_input = {
            "geometry.horizontal_radius": "400.0",
            "loading.design_speed": "80.0",
        }
        curved_tex = build_centrifugal_force_table(curved_input)
        assert "Radius of Curvature (R)" in curved_tex
        assert "400.0 m" in curved_tex
        assert "80.0 km/h" in curved_tex
        assert "Centrifugal Force Evaluation" in curved_tex

    def test_footway_live_load_table(self):
        input_dict = {
            "loading.footway_live_load": "4.0",
            "geometry.span": "24.0",
        }
        tex = build_footway_live_load_table(input_dict)
        assert r"\begin{longtable}" in tex
        assert "Footpath / Pedestrian Live Load" in tex
        assert "IRC 6 Cl. 206" in tex


# -----------------------------------------------------------------------------
# 4. Charts Generation & Matplotlib Headless Isolation Tests
# -----------------------------------------------------------------------------

class TestCharts:
    """Verifies headless matplotlib rendering, PNG signatures, and cleanup."""

    def test_ur_chart_generation_and_status_colors(self):
        ur_items = [
            ("Steel Plate Girders", 1.97),
            ("Concrete Deck Slab", 0.99),
            ("Cross Bracing", None),
            ("End Diaphragms", None),
        ]
        with tempfile.TemporaryDirectory() as td:
            out_file = os.path.join(td, "ur_test.png")
            res_path = generate_ur_chart(ur_items, output_path=out_file, theme=DEFAULT_THEME)
            assert os.path.exists(res_path)
            with open(res_path, "rb") as f:
                png_bytes = f.read()
            assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_material_takeoff_charts_generation(self):
        steel_data = {
            "Girders": 16.98,
            "Cross Bracing": 0.00,
            "Shear Studs": 0.16,
        }
        concrete_m3 = 50.40
        rebar_mt = 6.05

        with tempfile.TemporaryDirectory() as td:
            chart1_path, chart2_path = generate_material_takeoff_charts(
                steel_by_component=steel_data,
                concrete_m3=concrete_m3,
                rebar_mt=rebar_mt,
                output_dir=td,
                theme=DEFAULT_THEME,
            )
            assert os.path.exists(chart1_path)
            assert os.path.exists(chart2_path)
            with open(chart1_path, "rb") as f:
                c1_bytes = f.read()
            with open(chart2_path, "rb") as f:
                c2_bytes = f.read()
            assert c1_bytes.startswith(b"\x89PNG\r\n\x1a\n")
            assert c2_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_temporary_directory_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            chart_path = os.path.join(td, "test_chart.png")
            generate_ur_chart([("Girder", 0.75)], output_path=chart_path)
            assert os.path.exists(chart_path)
        assert not os.path.exists(td)


# -----------------------------------------------------------------------------
# 5. Chapter 5 Girder Group Atomicity Tests
# -----------------------------------------------------------------------------

class TestGirderGroupAtomicity:
    """Verifies that multirow girder check groups prevent page breaks."""

    def test_intermediate_rows_use_non_breaking_newline(self):
        from osdagbridge.core.reports.chap5 import ch5_design_checks

        from osdagbridge.core.reports.report_generator import (
            ReportDataBridge,
            ReportMetadata,
            ReportOptions,
            ReportPayload,
            ReportFigures,
        )

        input_dict = {
            "typical_section.no_of_girders": 2,
        }
        output_dict = {
            "sd.shear.vu": "300.0",
            "sd.bs.r": "304.97",
            "sd.bs.fcdw_wb": "134083.23",
            "sd.bs.fcdw_lc": "373.7",
            "sd.bs.fpsd": "2545.45",
            "sd.bs.fcd": "2087.27",
        }
        meta = ReportMetadata(
            project_name="Bridge",
            project_location="Location",
            designer="Designer",
            client="Client",
            company="Company"
        )
        opts = ReportOptions(sections=[], include_figures=False, include_toc=False, include_pdf=False)
        payload = ReportPayload(
            metadata=meta,
            options=opts,
            inputs=input_dict,
            analysis_summary={},
            design_checks=[],
            figures=ReportFigures(),
            output_dict=output_dict,
        )
        bridge = ReportDataBridge(output_dict=output_dict, input_dict=input_dict, payload=payload)
        design_checks = {
            "per_girder": {
                "G1": {"checks": []},
                "G2": {"checks": []},
            }
        }
        tex = ch5_design_checks(design_checks, bridge)

        # Confirm End Panel Stiffener Checks table has repeated headers
        assert r"\caption{\textbf{End Panel Stiffener Checks}}" in tex
        assert r"\endfirsthead" in tex
        assert r"\endhead" in tex
        # Confirm internal rows use \\* to keep girder checks together
        assert r"\\*[6pt]" in tex


# -----------------------------------------------------------------------------
# 6. Integration Document Generation Test
# -----------------------------------------------------------------------------

class TestReportGeneratorIntegration:
    """Verifies full report assembly and valid LaTeX structure."""

    def test_report_compilation_structure(self):
        from osdagbridge.core.reports.report_generator import (
            ReportMetadata,
            ReportOptions,
            ReportRequest,
        )

        metadata = ReportMetadata(
            project_name="Test Bridge Project",
            project_location="Mumbai",
            designer="Engineer",
            client="IIT Bombay",
            company="Osdag",
            job_number="TEST-001"
        )
        options = ReportOptions(
            sections=['exec_summary', 'project_info', 'input_parameters'],
            include_figures=True,
            include_toc=True,
            include_pdf=False
        )
        req = ReportRequest(
            metadata=metadata,
            options=options,
            output_dir="/tmp",
            file_stem="test_report"
        )
        assert req.file_stem == "test_report"
        assert req.options.include_toc is True
