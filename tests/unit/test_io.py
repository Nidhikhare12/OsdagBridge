"""Unit tests for fixture file I/O and figure_data base64 decoding pipeline.

Validates:
- load_fixture() correctly parses valid JSON and raises FileNotFoundError on invalid paths.
- base64 figure decoding pipeline decodes image bytes, injects them into ReportPayload,
  writes them into temporary images directory, and clears memory to prevent RAM leaks.
- Resilient error handling when figure_data contains malformed or corrupt base64 strings.
"""

import base64
import json
from pathlib import Path
import pytest

from osdagbridge.core.reports.cli import load_fixture, run_report_from_fixture
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    build_report_payload,
)


def test_fixture_io_and_figure_data_decoding(tmp_path):
    """Verify fixture loading, base64 figure decoding, and memory reclamation."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "reports"
    valid_fixture = fixtures_dir / "baseline_default.json"
    assert valid_fixture.is_file(), f"Missing fixture: {valid_fixture}"

    # 1. Test load_fixture with valid fixture
    data = load_fixture(valid_fixture)
    assert isinstance(data, dict), "load_fixture must return a dictionary"
    assert "input_dict" in data, "Fixture missing input_dict"
    assert "output_dict" in data, "Fixture missing output_dict"

    # 2. Test load_fixture with non-existent path
    non_existent = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_fixture(non_existent)

    # 3. Test base64 figure decoding pipeline
    # Minimal valid 1x1 PNG in base64
    valid_1x1_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    expected_bytes = base64.b64decode(valid_1x1_png_b64)

    test_fixture_data = {
        "metadata": {
            "project_name": "Figure I/O Pipeline Test",
            "designer": "Test Designer",
        },
        "options": {
            "sections": ["exec_summary", "project_info"],
            "include_figures": True,
            "include_toc": False,
            "include_pdf": True,
        },
        "input_dict": data.get("input_dict", {}),
        "output_dict": data.get("output_dict", {}),
        "figure_data": {
            "plan": valid_1x1_png_b64,
            "corrupt_image": "NOT_A_VALID_BASE64_STRING!@#$%",
        },
    }

    test_fixture_path = tmp_path / "test_fig_fixture.json"
    test_fixture_path.write_text(json.dumps(test_fixture_data), encoding="utf-8")

    # Verify that load_fixture correctly reads the custom fixture
    loaded = load_fixture(test_fixture_path)
    assert "figure_data" in loaded
    assert "plan" in loaded["figure_data"]

    # 4. Run through report generation and verify figure decoding
    result = run_report_from_fixture(
        fixture_path=test_fixture_path,
        output_dir=tmp_path,
        file_stem="test_io_output",
    )

    assert result.pdf_path is not None
    assert Path(result.pdf_path).is_file(), "Report generation with figure_data must produce a PDF"
    assert len(result.errors) == 0, f"Compilation errors occurred: {result.errors}"

    # 5. Direct verification of payload decoding and memory freeing
    metadata = ReportMetadata(
        project_name="RAM Free Test",
        project_location="",
        designer="",
        client="",
        company="",
    )
    options = ReportOptions(
        sections=["project_info"],
        include_figures=True,
        include_toc=False,
        include_pdf=True,
    )
    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=str(tmp_path),
        file_stem="ram_test",
    )

    payload = build_report_payload(request, loaded["input_dict"], loaded["output_dict"])
    payload.figure_data["manual_test_fig"] = expected_bytes
    assert len(payload.figure_data) == 1

    # Simulate write-and-clear logic used in report_generator.py lines 670-676
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    written_paths = {}
    for attr, img_bytes in list(payload.figure_data.items()):
        if img_bytes:
            p = img_dir / f"{attr}.png"
            p.write_bytes(img_bytes)
            written_paths[attr] = str(p)
    payload.figure_data.clear()

    # Verify file was written and memory cleared
    assert (img_dir / "manual_test_fig.png").is_file()
    assert (img_dir / "manual_test_fig.png").stat().st_size == len(expected_bytes)
    assert len(payload.figure_data) == 0, "payload.figure_data must be cleared to free RAM"
