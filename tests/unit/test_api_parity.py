"""Tests T-API and T-PARITY: Guarantee interface compatibility and calculation integrity."""

import inspect
import re
from pathlib import Path
import pytest

from osdagbridge.core import reports
from osdagbridge.core.reports import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportFigures,
    ReportPayload,
    ReportResult,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.reports import chap1, chap2, chap3, chap4, chap5, chap6, chap7, chap8, chap9, executive_summary
from osdagbridge.core.reports.cli import run_report_from_fixture


def test_t_api_exports():
    """T-API: Verify public exports of osdagbridge.core.reports remain unchanged."""
    expected_exports = [
        "ReportMetadata", "ReportOptions", "ReportRequest",
        "ReportFigures", "ReportPayload", "ReportResult",
        "build_report_payload", "generate_report",
    ]
    assert reports.__all__ == expected_exports
    for name in expected_exports:
        assert hasattr(reports, name)


def test_t_api_signatures():
    """T-API: Verify that orchestrator and chapter function signatures match baseline."""
    expected_signatures = {
        (reports, "generate_report"): ["payload", "request"],
        (reports, "build_report_payload"): ["request", "input_dict", "output_dict"],
        (executive_summary, "executive_summary"): ["input_dict", "output_dict", "fig_paths"],
        (chap1, "ch1_project_info"): ["m"],
        (chap2, "ch2_input_parameters"): ["m", "input_dict", "output_dict"],
        (chap3, "ch3_loads"): ["input_dict"],
        (chap4, "ch4_analysis"): ["asum", "fig_paths", "bridge", "span_m"],
        (chap5, "ch5_design_checks"): ["checks_data", "bridge"],
        (chap6, "ch6_drawings"): ["fig_paths"],
        (chap7, "ch7_quantities"): ["input_dict"],
        (chap8, "ch8_design_log"): ["log_entries", "input_dict"],
        (chap9, "references"): [],
    }

    for (mod, fn_name), expected_params in expected_signatures.items():
        assert hasattr(mod, fn_name), f"Missing function {fn_name} in {mod.__name__}"
        fn = getattr(mod, fn_name)
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert params == expected_params, f"Signature mismatch for {fn_name}: {params} != {expected_params}"


@pytest.mark.latex
def test_t_parity_baseline(tmp_path, fixtures_dir):
    """T-PARITY: Ensure that all numerical tokens and table captions from Report_Before.tex

    appear faithfully in newly generated reports, preserving all calculation outputs.
    """
    baseline_tex = Path("C:/Users/prana/Desktop/FOSSEE/deliverables/Report_Before.tex")
    if not baseline_tex.is_file():
        pytest.skip("Baseline Report_Before.tex not found")

    fixture_path = fixtures_dir / "baseline_default.json"
    result = run_report_from_fixture(
        fixture_path=fixture_path,
        output_dir=tmp_path,
        file_stem="parity_check",
    )

    assert result.tex_path and Path(result.tex_path).is_file()
    assert result.pdf_path and Path(result.pdf_path).is_file()

    with open(baseline_tex, "r", encoding="utf-8") as f:
        baseline_content = f.read()

    with open(result.tex_path, "r", encoding="utf-8") as f:
        new_content = f.read()

    # Extract all numerical tokens (e.g., 1526.502, 304.968, 460.01)
    num_pattern = re.compile(r"\b\d+\.\d+\b")
    baseline_nums = set(num_pattern.findall(baseline_content))
    new_nums = set(num_pattern.findall(new_content))

    # Reviewed allowlist of intended changes per PLAN.md section 7 (T-PARITY):
    # '7.1': Table 7.1 raw uncaptioned text replaced by LaTeX longtable caption
    parity_allowlist = {"7.1"}

    missing_nums = baseline_nums - new_nums - parity_allowlist
    assert not missing_nums, f"Numeric values changed or missing from report: {missing_nums}"

    # Extract all table captions
    caption_pattern = re.compile(r"\\caption\{([^}]+)\}")
    baseline_captions = set(caption_pattern.findall(baseline_content))
    new_captions = set(caption_pattern.findall(new_content))

    missing_captions = baseline_captions - new_captions
    assert not missing_captions, f"Captions changed or missing: {missing_captions}"
