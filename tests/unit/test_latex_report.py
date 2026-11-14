"""Automated verification suite for OsdagBridge LaTeX Report Generator.

Evaluates:
1. Preamble geometry parameters and centralized style injections.
2. Load table separation (Vehicular vs Pedestrian) in Chapter 3.
3. Native LaTeX longtable continuation headers (endfirsthead, endhead, endfoot, endlastfoot)
   across Chapters 3, 5, and 7.
4. Dynamic headless Matplotlib chart generation (UR and BOQ takeoffs) with error-resilience.
5. End-to-end two-pass pdflatex compilation producing a valid, non-empty technical PDF report.
"""

import os
import sys
import re
import tempfile
import pytest

# Ensure src/ is on sys.path for test discovery
_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from osdagbridge.core.bridge_types.plate_girder.defaults import (
    BASIC_INPUT_DICT,
    solve_extend_basic_input_dict,
)
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_STRUCTURE_TYPE,
    KEY_DESIGN_MODE,
    KEY_FOOTPATH,
)
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportPayload,
    ReportFigures,
    ReportDataBridge,
    generate_report,
    preamble,
)
from osdagbridge.core.reports.styles import (
    COLOR_OSDAG_GREEN,
    COLOR_HEADER_NAVY,
    COLOR_PASS,
    COLOR_FAIL,
    ARRAY_STRETCH,
    LATEX_COLOR_DEFINITIONS,
    pass_indicator,
    fail_indicator,
    status_indicator,
)
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chart_generator import (
    generate_ur_chart,
    generate_quantity_charts,
)


@pytest.fixture
def sample_payload():
    """Create a fully-solved ReportPayload fixture."""
    inputs = dict(BASIC_INPUT_DICT)
    inputs[KEY_SPAN] = 30.0
    inputs[KEY_CARRIAGEWAY_WIDTH] = 7.5
    inputs[KEY_SKEW_ANGLE] = 0.0
    inputs[KEY_STRUCTURE_TYPE] = "Highway Bridge"
    inputs[KEY_DESIGN_MODE] = "Optimized"
    inputs[KEY_FOOTPATH] = "Both Sides"
    solve_extend_basic_input_dict(inputs)

    design_checks = [
        {"check_name": "Flexure Bending Check (Girder G1)", "demand": 1250.0, "capacity": 1500.0, "ur": 0.833, "status": "PASS"},
        {"check_name": "Shear Capacity Check (Girder G1)", "demand": 420.0, "capacity": 650.0, "ur": 0.646, "status": "PASS"},
        {"check_name": "Web Buckling Check (Girder G1)", "demand": 380.0, "capacity": 450.0, "ur": 0.844, "status": "PASS"},
        {"check_name": "Deck Slab Longitudinal Flexure", "demand": 45.0, "capacity": 60.0, "ur": 0.750, "status": "PASS"},
        {"check_name": "Deck Slab Transverse Flexure", "demand": 52.0, "capacity": 65.0, "ur": 0.800, "status": "PASS"},
        {"check_name": "Cross Bracing (Axial Check)", "demand": 110.0, "capacity": 180.0, "ur": 0.611, "status": "PASS"},
        {"check_name": "End Diaphragm (Axial / Shear)", "demand": 140.0, "capacity": 220.0, "ur": 0.636, "status": "PASS"},
    ]

    meta = ReportMetadata(
        project_name="Bridge Verification Test",
        project_location="Mumbai, Maharashtra",
        designer="Varad Joshi",
        reviewer="FOSSEE Evaluation Team",
        client="FOSSEE IIT Bombay",
        company="IIT Bombay - FOSSEE",
        group_name="Bridge Engineering Division",
        subtitle="Screening Task Verification",
        job_number="FOSSEE-2026-TEST",
        additional_comments="Automated Verification Suite",
        report_date="2026-11-14",
    )
    opts = ReportOptions(
        sections=['loads', 'analysis', 'design_checks', 'drawings'],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )
    return ReportPayload(
        metadata=meta,
        options=opts,
        figures=ReportFigures(),
        inputs=inputs,
        analysis_summary={},
        design_checks=design_checks,
        log_entries=[],
        output_dict={},
    )


class TestPreambleAndStyles:
    """Verify FR-2 (Page Geometry) & FR-6 (Centralized Style Architecture)."""

    def test_preamble_geometry_options(self):
        latex_preamble = preamble("Test Project", "JOB-01", "2026-11-14", "Rev 0")
        assert "a4paper" in latex_preamble
        assert "top=2.5cm" in latex_preamble
        assert "bottom=2.5cm" in latex_preamble
        assert "left=2.0cm" in latex_preamble
        assert "right=2.0cm" in latex_preamble
        assert "headheight=15pt" in latex_preamble
        assert "footskip=30pt" in latex_preamble

    def test_preamble_styles_and_colors(self):
        latex_preamble = preamble("Test Project", "JOB-01", "2026-11-14", "Rev 0")
        assert r"\definecolor{osdagGreen}{HTML}{91B014}" in latex_preamble
        assert r"\definecolor{headerNavy}{HTML}{1E3A8A}" in latex_preamble
        assert r"\definecolor{zebraLight}{HTML}{F3F4F6}" in latex_preamble
        assert r"\definecolor{passGreen}{HTML}{10B981}" in latex_preamble
        assert r"\definecolor{failRed}{HTML}{EF4444}" in latex_preamble
        assert rf"\renewcommand{{\arraystretch}}{{{ARRAY_STRETCH}}}" in latex_preamble

    def test_needspace_orphan_prevention(self):
        latex_preamble = preamble("Test Project", "JOB-01", "2026-11-14", "Rev 0")
        assert r"\needspace{5\baselineskip}" in latex_preamble
        assert r"\needspace{4\baselineskip}" in latex_preamble

    def test_status_indicators(self):
        assert "passGreen" in pass_indicator("PASS")
        assert "failRed" in fail_indicator("FAIL")
        assert "passGreen" in status_indicator(True)
        assert "failRed" in status_indicator(False)


class TestChapter3LoadSchedules:
    """Verify FR-3 (Load & Geometry Table Separation)."""

    def test_vehicular_and_pedestrian_separation(self, sample_payload):
        ch3_text = ch3_loads(sample_payload.inputs)
        assert "Vehicular Live Loads (IRC 6:2017)" in ch3_text
        assert "Footway and Pedestrian Live Loads (IRC 6 Cl. 206)" in ch3_text
        assert "Dead Load -- Self Weight" in ch3_text
        assert "Dead Load for Surfacing (DW)" in ch3_text
        assert "Wind Load (WL)" in ch3_text
        assert "Earthquake Load (EL)" in ch3_text
        assert "Temperature Load (TL)" in ch3_text
        assert "Load Combinations" in ch3_text

    def test_centrifugal_force_straight_alignment_fallback(self, sample_payload):
        ch3_text = ch3_loads(sample_payload.inputs)
        assert "0.00 kN (Straight)" in ch3_text

    def test_footway_pressure_calculation(self, sample_payload):
        ch3_text = ch3_loads(sample_payload.inputs)
        assert "kN/m" in ch3_text
        assert "Reduction Factor" in ch3_text


class TestLongTablePagination:
    """Verify FR-1 (Multi-Page Table Header Continuity)."""

    def test_chap3_longtable_headers(self, sample_payload):
        ch3_text = ch3_loads(sample_payload.inputs)
        num_lt = ch3_text.count(r"\begin{longtable}")
        assert num_lt == 8
        assert ch3_text.count(r"\endfirsthead") == 8
        assert ch3_text.count(r"\endhead") == 8
        assert ch3_text.count(r"\endfoot") == 8
        assert ch3_text.count(r"\endlastfoot") == 8

    def test_chap5_longtable_headers(self, sample_payload):
        bridge = ReportDataBridge(sample_payload.output_dict, sample_payload.inputs, sample_payload)
        ch5_text = ch5_design_checks(sample_payload.design_checks, bridge)
        num_lt = ch5_text.count(r"\begin{longtable}")
        assert num_lt >= 29
        assert ch5_text.count(r"\endfirsthead") == num_lt
        assert ch5_text.count(r"\endhead") == num_lt
        assert ch5_text.count(r"\endfoot") == num_lt
        assert ch5_text.count(r"\endlastfoot") == num_lt

    def test_chap7_longtable_headers(self, sample_payload):
        ch7_text = ch7_quantities(sample_payload.inputs)
        assert r"\begin{longtable}" in ch7_text
        assert r"\endfirsthead" in ch7_text
        assert r"\endhead" in ch7_text
        assert r"\endfoot" in ch7_text
        assert r"\endlastfoot" in ch7_text


class TestHeadlessChartGeneration:
    """Verify FR-4 & FR-5 (Dynamic Headless Matplotlib Charts)."""

    def test_ur_chart_generation(self, sample_payload, tmp_path):
        out_dir = str(tmp_path / "charts")
        ur_path = generate_ur_chart(sample_payload.design_checks, out_dir)
        assert os.path.exists(ur_path)
        assert os.path.getsize(ur_path) > 10000
        assert ur_path.endswith("ur_summary.png")

    def test_ur_chart_robustness_empty_data(self, tmp_path):
        out_dir = str(tmp_path / "charts_empty")
        ur_path = generate_ur_chart([], out_dir)
        assert os.path.exists(ur_path)
        assert os.path.getsize(ur_path) > 10000

        ur_path_none = generate_ur_chart(None, out_dir)
        assert os.path.exists(ur_path_none)
        assert os.path.getsize(ur_path_none) > 10000

    def test_quantity_charts_generation(self, sample_payload, tmp_path):
        out_dir = str(tmp_path / "charts_qty")
        steel_path, conc_path = generate_quantity_charts(sample_payload.inputs, out_dir)
        assert os.path.exists(steel_path)
        assert os.path.exists(conc_path)
        assert os.path.getsize(steel_path) > 10000
        assert os.path.getsize(conc_path) > 10000
        assert steel_path.endswith("boq_steel.png")
        assert conc_path.endswith("boq_concrete.png")

    def test_quantity_charts_robustness_empty_inputs(self, tmp_path):
        out_dir = str(tmp_path / "charts_qty_empty")
        steel_path, conc_path = generate_quantity_charts({}, out_dir)
        assert os.path.exists(steel_path)
        assert os.path.exists(conc_path)
        assert os.path.getsize(steel_path) > 10000
        assert os.path.getsize(conc_path) > 10000


class TestCompilerDeterminism:
    """Verify End-to-End Two-Pass pdflatex Compilation."""

    def test_generate_report_end_to_end(self, sample_payload, tmp_path):
        out_dir = str(tmp_path / "report_out")
        req = ReportRequest(
            metadata=sample_payload.metadata,
            options=sample_payload.options,
            output_dir=out_dir,
            file_stem="Test_Report"
        )
        result = generate_report(sample_payload, req)

        assert result is not None
        assert os.path.exists(result.pdf_path)
        assert os.path.exists(result.tex_path)
        assert os.path.getsize(result.pdf_path) > 50000

        # Verify TeX buffer content
        with open(result.tex_path, "r", encoding="utf-8") as f:
            tex_content = f.read()

        assert "Vehicular Live Loads (IRC 6:2017)" in tex_content
        assert "Footway and Pedestrian Live Loads (IRC 6 Cl. 206)" in tex_content
        assert "Summary of Element Utilization Ratios" in tex_content
        assert "Structural Steel Quantity Breakdown" in tex_content
        assert r"\endfirsthead" in tex_content
        assert r"\endlastfoot" in tex_content
