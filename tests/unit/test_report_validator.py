"""Tests for report validation utilities."""

from pathlib import Path
from osdagbridge.core.reports.report_validator import validate_chapters
from osdagbridge.core.reports.report_validator import (
    validate_pdf,
    validate_tex_structure,
)


def test_validate_tex_structure_pass(tmp_path):
    tex = tmp_path / "report.tex"

    tex.write_text(
        r"""
        \begin{document}
        Test Report
        \begin{longtable}
        Data
        \end{longtable}
        \begin{figure}
        Image
        \end{figure}
        \end{document}
        """,
        encoding="utf-8",
    )

    result = validate_tex_structure(tex)

    assert result.passed
    assert result.errors == []


def test_validate_tex_structure_detects_missing_end(tmp_path):
    tex = tmp_path / "broken.tex"

    tex.write_text(
        r"""
        \begin{document}
        Broken
        """,
        encoding="utf-8",
    )

    result = validate_tex_structure(tex)

    assert not result.passed
    assert len(result.errors) > 0


def test_validate_pdf_missing_file(tmp_path):
    pdf = Path(tmp_path) / "missing.pdf"

    result = validate_pdf(pdf)

    assert not result.passed
    assert "does not exist" in result.errors[0]
def test_validate_chapters_detects_missing_sections(tmp_path):
    tex = tmp_path / "report.tex"

    tex.write_text(
        r"""
        \chapter{Chapter 1}
        \chapter{Chapter 2}
        """,
        encoding="utf-8",
    )

    result = validate_chapters(tex)

    assert not result.passed
    assert len(result.errors) > 0
