"""Unit tests for layout engine, geometry, and footer non-overlap (Requirement R2)."""

from pathlib import Path
import pytest

from osdagbridge.core.reports.cli import run_report_from_fixture
from osdagbridge.core.reports.qa.pdf_lint import check_footer_overlap


@pytest.mark.latex
def test_t_layout_1_zero_footer_overlap(tmp_path):
    """T-LAYOUT-1: Ensure that the compiled report has zero footer overlap violations across all pages."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "reports"
    baseline_json = fixtures_dir / "baseline_default.json"
    assert baseline_json.is_file(), f"Missing fixture: {baseline_json}"

    res = run_report_from_fixture(str(baseline_json), str(tmp_path))
    assert res.pdf_path and Path(res.pdf_path).is_file()

    violations = check_footer_overlap(res.pdf_path)
    assert len(violations) == 0, f"Found {len(violations)} footer overlap violations: {violations[:5]}"


@pytest.mark.latex
def test_t_layout_2_sd_note_footer_clear(tmp_path):
    """T-LAYOUT-2: Ensure that pages containing software default notes (* Software default value)

    have their notes cleanly placed inside the reserved footer box without encroaching on text block.
    """
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "reports"
    baseline_json = fixtures_dir / "baseline_default.json"
    res = run_report_from_fixture(str(baseline_json), str(tmp_path))
    assert res.pdf_path and Path(res.pdf_path).is_file()

    import pdfplumber
    with pdfplumber.open(res.pdf_path) as pdf:
        sd_pages = []
        for p_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if "* Software default value" in text:
                sd_pages.append(p_idx)

        assert len(sd_pages) > 0, "Expected at least one page with software default note in baseline"

        # Verify that all SD-pages have zero text overlap and proper footer positioning
        violations = check_footer_overlap(res.pdf_path)
        sd_violations = [v for v in violations if v.page in sd_pages]
        assert len(sd_violations) == 0, f"Footer violations on SD-pages: {sd_violations}"
