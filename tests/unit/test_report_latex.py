"""Regression tests for the LaTeX emitted by the report generator."""

from pathlib import Path
import re

from osdagbridge.core.reports.report_generator import preamble


REPORTS_DIR = Path(__file__).parents[2] / "src" / "osdagbridge" / "core" / "reports"
CHAPTER_FILES = sorted(REPORTS_DIR.glob("chap*.py"))


def test_preamble_uses_centralized_style_settings_once():
    tex = preamble("Sample Project", "JOB-1", "2026-08-10")

    expected_tokens = (
        r"\usepackage[a4paper, margin=1in]{geometry}",
        r"\usepackage{xcolor}",
        r"\usepackage{array}",
        r"\usepackage{booktabs}",
        r"\usepackage{longtable}",
        r"\usepackage{fancyhdr}",
        r"\definecolor{osdagGreen}{HTML}{91B014}",
        r"\setlength{\tabcolsep}{6pt}",
        r"\renewcommand{\arraystretch}{1.12}",
    )

    for token in expected_tokens:
        assert tex.count(token) == 1, token


def test_every_longtable_continuation_has_a_repeated_header():
    """A continuation header must contain visible table-header LaTeX.

    ``longtable`` does not repeat the first-page header automatically.  An
    empty block between ``\\endfirsthead`` and ``\\endhead`` therefore makes
    later pages lose their column headings.
    """
    pattern = re.compile(r"\\endfirsthead(?P<header>.*?)\\endhead", re.DOTALL)

    for chapter in CHAPTER_FILES:
        source = chapter.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            repeated_header = match.group("header")
            assert r"\hline" in repeated_header, chapter.name
            assert any(marker in repeated_header for marker in (r"\textbf", r"\multicolumn", r"\multirow")), chapter.name


def test_no_longtable_continuation_header_is_empty():
    pattern = re.compile(r"\\endfirsthead\s*\\endhead")
    empty_headers = [
        chapter.name
        for chapter in CHAPTER_FILES
        if pattern.search(chapter.read_text(encoding="utf-8"))
    ]

    assert empty_headers == []
