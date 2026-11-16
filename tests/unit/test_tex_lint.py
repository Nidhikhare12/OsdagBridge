"""Unit tests for LaTeX source and output linter (tex_lint.py)."""

from pathlib import Path
import pytest

from osdagbridge.core.reports.qa.tex_lint import check_sources, check_tex
from osdagbridge.core.reports.cli import run_report_from_fixture


def test_no_raw_longtables_in_sources():
    """Verify that zero raw \\begin{longtable} directives remain in chapter files."""
    reports_dir = Path(__file__).resolve().parent.parent.parent / "src" / "osdagbridge" / "core" / "reports"
    violations = check_sources(reports_dir)
    longtable_violations = [v for v in violations if v.rule == "R-NO-RAW-LONGTABLE"]
    assert len(longtable_violations) == 0, f"Found raw longtables: {longtable_violations}"


def test_no_raw_colors_in_sources():
    """Verify that zero hardcoded colors (\\definecolor, \\textcolor{red}) exist in chapters."""
    reports_dir = Path(__file__).resolve().parent.parent.parent / "src" / "osdagbridge" / "core" / "reports"
    violations = check_sources(reports_dir)
    color_violations = [v for v in violations if v.rule in ("R-NO-RAW-DEFINECOLOR", "R-NO-RAW-TEXTCOLOR")]
    assert len(color_violations) == 0, f"Found raw colors: {color_violations}"


@pytest.mark.latex
def test_all_generated_tables_have_repeated_headers(tmp_path):
    """Verify that every single table generated in the baseline report contains \\endfirsthead and \\endhead."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "reports"
    baseline_json = fixtures_dir / "baseline_default.json"
    assert baseline_json.is_file(), f"Missing fixture: {baseline_json}"

    res = run_report_from_fixture(str(baseline_json), str(tmp_path))
    assert res.tex_path and Path(res.tex_path).is_file()

    violations = check_tex(res.tex_path)
    assert len(violations) == 0, f"Table header violations found in generated .tex: {violations}"
