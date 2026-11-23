"""Tests for ``latex_tables.normalize_longtables``."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from osdagbridge.core.reports.latex_tables import (
    _column_count,
    normalize_longtables,
)

CAPTIONED = (
    r"\begin{longtable}{|L{5.5cm}|p{10.0cm}|}" "\n"
    r"\caption{\textbf{Dead Load -- Self Weight}}" "\n"
    r"\hline" "\n"
    r"\textbf{parameter} & \textbf{value} \\" "\n"
    r"\hline" "\n"
    r"density & 25 \\" "\n"
    r"\end{longtable}"
)
UNCAPTIONED = (
    r"\begin{longtable}{|L{4cm}|C{3cm}|}" "\n"
    r"\hline" "\n"
    r"\textbf{Item} & \textbf{Qty} \\" "\n"
    r"\hline" "\n"
    r"steel & 12 \\" "\n"
    r"\end{longtable}"
)
HEADER_ROW = r"\textbf{parameter} & \textbf{value} \\"


class TestCaptionAndHeader:
    def test_caption_is_terminated(self) -> None:
        out = normalize_longtables(CAPTIONED)
        assert r"\caption{\textbf{Dead Load -- Self Weight}}\\" in out

    def test_caption_is_not_repeated_or_reordered(self) -> None:
        out = normalize_longtables(CAPTIONED)
        assert out.count(r"\caption") == 1
        assert (out.index(r"\caption") < out.index(HEADER_ROW)
                < out.index(r"\endfirsthead") < out.rindex(HEADER_ROW)
                < out.index(r"\endhead") < out.index("density"))

    def test_header_row_appears_in_both_heads(self) -> None:
        assert normalize_longtables(CAPTIONED).count(HEADER_ROW) == 2

    def test_continued_label_spans_all_columns(self) -> None:
        out = normalize_longtables(CAPTIONED)
        assert r"\multicolumn{2}{l}{\small\textit{\tablename~" in out

    def test_table_without_caption_gets_header_but_no_label(self) -> None:
        out = normalize_longtables(UNCAPTIONED)
        assert r"\endfirsthead" in out and r"\endhead" in out
        assert r"\multicolumn" not in out
        assert out.count(r"\textbf{Item} & \textbf{Qty} \\") == 2

    def test_body_rows_stay_after_endhead(self) -> None:
        out = normalize_longtables(CAPTIONED)
        assert out.endswith("density & 25 \\\\\n" r"\end{longtable}")


class TestSafety:
    def test_idempotent(self) -> None:
        once = normalize_longtables(CAPTIONED + "\n" + UNCAPTIONED)
        assert normalize_longtables(once) == once

    def test_existing_endhead_is_untouched(self) -> None:
        table = CAPTIONED.replace(
            "density", r"\endhead" "\ndensity")
        assert normalize_longtables(table) == table

    def test_non_header_first_row_only_gets_caption_fix(self) -> None:
        table = (r"\begin{longtable}{|l|l|}" "\n"
                 r"\caption{Plain}" "\n"
                 r"\hline" "\n"
                 r"\textnormal{Effective span} & 30 \\" "\n"
                 r"\hline" "\n"
                 r"\end{longtable}")
        out = normalize_longtables(table)
        assert r"\caption{Plain}\\" in out
        assert r"\endhead" not in out

    def test_text_outside_tables_is_unchanged(self) -> None:
        text = "intro\n" + CAPTIONED + "\noutro \\textbf{x}\n"
        out = normalize_longtables(text)
        assert out.startswith("intro\n")
        assert out.endswith(r"\end{longtable}" "\noutro \\textbf{x}\n")

    def test_multiple_tables(self) -> None:
        out = normalize_longtables(CAPTIONED + "\n" + UNCAPTIONED)
        assert out.count(r"\endhead") == 2

    def test_no_tables_returns_input(self) -> None:
        assert normalize_longtables("plain text") == "plain text"

    def test_malformed_table_is_skipped_not_fatal(self) -> None:
        broken = (r"\begin{longtable}{|l|l|}" "\n"
                  r"\caption{unbalanced" "\n"
                  r"\hline" "\n"
                  r"\end{longtable}")
        out = normalize_longtables(broken)
        assert out.endswith(broken)
        assert out.startswith(r"\needspace")

    def test_headerless_table_gets_a_needspace_guard(self) -> None:
        table = (r"\begin{longtable}{|l|l|}" "\n"
                 r"\hline" "\n"
                 r"\textnormal{Effective span} & 30 \\" "\n"
                 r"\hline" "\n"
                 r"\end{longtable}")
        out = normalize_longtables(table)
        assert out.startswith(r"\needspace{5\baselineskip}")
        assert normalize_longtables(out) == out

    def test_repeating_header_tables_get_no_guard(self) -> None:
        assert r"\needspace" not in normalize_longtables(CAPTIONED)

    def test_empty_string(self) -> None:
        assert normalize_longtables("") == ""


@pytest.mark.parametrize("spec,expected", [
    (r"|l|c|r|", 3),
    (r"|L{5.5cm}|p{10.0cm}|", 2),
    (r"|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|"
     r">{\centering\arraybackslash}p{1.6cm}|", 5),
    (r"@{}lll@{}", 3),
    ("", 0),
])
def test_column_count(spec: str, expected: int) -> None:
    assert _column_count(spec) == expected


needs_latex = pytest.mark.skipif(
    shutil.which("pdflatex") is None, reason="pdflatex not installed")
needs_poppler = pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("pdftotext", "pdfinfo")),
    reason="poppler-utils (pdftotext, pdfinfo) not installed")


def _latex_errors(tex: str, folder: Path) -> int:
    """Compile ``tex`` twice and return the number of LaTeX errors."""
    source = folder / "doc.tex"
    source.write_text(tex, encoding="utf-8")
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", source.name],
            cwd=folder, capture_output=True, check=False)
    log = (folder / "doc.log").read_text(encoding="utf-8", errors="ignore")
    return sum(1 for line in log.splitlines() if line.startswith("!"))


@needs_latex
def test_real_chapters_compile_cleanly_only_after_normalizing(
        tmp_path: Path) -> None:
    from osdagbridge.core.reports.chap3 import ch3_loads
    from osdagbridge.core.reports.chap7 import ch7_quantities
    from osdagbridge.core.reports.report_generator import preamble

    body = ch3_loads({}) + "\n" + ch7_quantities({})
    head = preamble("Test", "J1", "14 Nov 2026")
    end = "\n\\end{document}\n"

    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    assert _latex_errors(head + body + end, before) > 0
    assert _latex_errors(head + normalize_longtables(body) + end, after) == 0


@needs_latex
@needs_poppler
def test_header_repeats_on_every_page(tmp_path: Path) -> None:
    from osdagbridge.core.reports.report_generator import preamble

    rows = "\n".join(rf"G{i} & member {i} \\[6pt]" for i in range(1, 90))
    table = (
        r"\begin{longtable}{|C{2cm}|L{6cm}|}" "\n"
        r"\caption{\textbf{Long}}" "\n"
        r"\hline" "\n"
        r"\textbf{IDHEADER} & \textbf{MEMBERHEADER} \\" "\n"
        r"\hline" "\n" + rows + "\n" r"\end{longtable}"
    )
    tex = (preamble("T", "J", "d") + normalize_longtables(table)
           + "\n\\end{document}\n")
    assert _latex_errors(tex, tmp_path) == 0
    pages = int(subprocess.run(
        ["pdfinfo", str(tmp_path / "doc.pdf")], capture_output=True,
        text=True, check=True).stdout.split("Pages:")[1].split()[0])
    assert pages >= 2
    for number in range(1, pages + 1):
        text = subprocess.run(
            ["pdftotext", "-f", str(number), "-l", str(number),
             str(tmp_path / "doc.pdf"), "-"],
            capture_output=True, text=True, check=True).stdout
        assert "IDHEADER" in text, f"header missing on page {number}"
