"""Integration test for Plate Girder Report Generation API.

Verifies end-to-end report payload assembly, metadata mapping, analysis summary
extraction, LaTeX generation, multi-pass compilation, and non-empty PDF emission.
"""

from pathlib import Path
import json
import pytest

from osdagbridge.core.reports import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportResult,
    build_report_payload,
    generate_report,
)


@pytest.mark.latex
def test_plate_girder_report_api_integration(tmp_path):
    """Verify that build_report_payload and generate_report execute end-to-end

    producing a valid, non-empty PDF document (> 100 KB) with clean compilation.
    """
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    assert fixture_path.is_file(), f"Fixture file not found: {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_data = json.load(f)

    input_dict = fixture_data.get("input_dict", {})
    output_dict = fixture_data.get("output_dict", {})

    # Ensure design checks list is populated in output_dict for payload validation
    if "design_checks" not in output_dict or not output_dict["design_checks"]:
        output_dict["design_checks"] = [
            {"element": "Girder G1", "check": "Flexural Bending", "ur": 0.68, "status": "PASS"},
            {"element": "Deck Slab", "check": "Transverse Bending", "ur": 0.42, "status": "PASS"},
        ]

    # Instantiate Metadata, Options, and Request
    metadata = ReportMetadata(
        project_name="Plate Girder Bridge Integration Test",
        project_location="Mumbai, Maharashtra",
        designer="Er. Pranav Chaudhari",
        reviewer="Dr. Structural Reviewer",
        client="Ministry of Road Transport and Highways",
        company="FOSSEE IIT Bombay",
        job_number="OB-INT-2026",
    )

    options = ReportOptions(
        sections=[
            "exec_summary", "project_info", "input_parameters", "loads",
            "analysis", "design_checks", "drawings", "quantities",
            "standards", "design_log_window", "references",
        ],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
        theme="osdag_classic",
        include_utilization_charts=True,
        include_quantity_charts=True,
    )

    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=str(tmp_path),
        file_stem="plate_girder_api_test",
    )

    # 1. Verify build_report_payload
    payload = build_report_payload(request, input_dict, output_dict)
    assert payload is not None
    assert payload.metadata.project_name == "Plate Girder Bridge Integration Test"
    assert payload.metadata.designer == "Er. Pranav Chaudhari"
    assert payload.metadata.job_number == "OB-INT-2026"
    assert bool(payload.analysis_summary), "Analysis summary should be extracted from output_dict"
    assert len(payload.design_checks) >= 2, "Design checks list should be populated"

    # 2. Verify generate_report
    result = generate_report(payload, request)
    assert isinstance(result, ReportResult)
    assert result.pdf_path is not None, "generate_report must return a valid pdf_path"
    assert result.tex_path is not None, "generate_report must return a valid tex_path"

    pdf_file = Path(result.pdf_path)
    tex_file = Path(result.tex_path)

    assert pdf_file.is_file(), f"Generated PDF file does not exist on disk: {pdf_file}"
    assert tex_file.is_file(), f"Generated TeX file does not exist on disk: {tex_file}"

    assert result.passes >= 2, f"LaTeX compiler ran {result.passes} passes; expected >= 2 for cross-referencing"
    assert len(result.errors) == 0, f"LaTeX compilation reported errors: {result.errors}"

    pdf_size_bytes = pdf_file.stat().st_size
    assert pdf_size_bytes > 100 * 1024, f"Generated PDF is unexpectedly small ({pdf_size_bytes} bytes; expected > 100 KB)"
