import os
import shutil
import subprocess
from pathlib import Path

import pytest

from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_generator import preamble
from osdagbridge.core.reports.styles import TABLE_LAYOUT, fit_table_columns

ROOT = Path(__file__).resolve().parents[2]


def test_quantity_table_has_one_header_template_and_balanced_group():
    tex = ch7_quantities({"steel_girders_wt_total": "12.5"})
    assert tex.count(r"\ReportTableHeader{") == 1
    assert tex.index(r"\caption{") < tex.index(r"\ReportTableHeader{") < tex.index("12.5")
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup") == 1
    assert "estimated" in tex.lower()


def test_girder_summary_caption_precedes_its_single_repeating_header():
    source = (ROOT / "src/osdagbridge/core/reports/chap5.py").read_text(encoding="utf-8")
    table = source.split(r"\caption{\textbf{Girder Design Summary", 1)[1].split(r"\end{longtable}", 1)[0]
    assert table.count(r"\ReportTableHeader{") == 1
    assert table.count(r"\textbf{Controlling LC / Combination}") == 1
    assert TABLE_LAYOUT.count(r"#1\hline\endfirsthead") == 1
    assert TABLE_LAYOUT.count(r"#1\hline\endhead") == 1


def test_multipage_member_rows_compile_with_repeated_header_and_footer_clearance(tmp_path):
    compiler = os.environ.get("OSDAG_PDFLATEX") or shutil.which("pdflatex")
    pdf_python = os.environ.get("OSDAG_PDF_PYTHON")
    if not (compiler and pdf_python):
        pytest.skip("Set OSDAG_PDFLATEX and OSDAG_PDF_PYTHON (Python with PyMuPDF).")

    rows = "\n".join(rf"G4 & MEMBER{i:02d} & {i}.75 \\[18pt]\hline" for i in range(48))
    table = (r"""
\begin{longtable}{|C{4cm}|L{7cm}|R{5cm}|}
\caption{PAGINATIONREGRESSION}\\
\ReportTableHeader{\textbf{GIRDERHEADER} & \textbf{CHECKHEADER} & \textbf{URHEADER}\\}
""" + rows + "\n" + r"\end{longtable}")
    tex = fit_table_columns(preamble("Pagination", "", "") + r"\pagestyle{main}" + table)
    assert r"\dimexpr" in tex
    (tmp_path / "pagination.tex").write_text(tex + r"\end{document}", encoding="utf-8")
    for _ in range(2):
        result = subprocess.run([compiler, "-interaction=nonstopmode", "-halt-on-error", "pagination.tex"],
                                cwd=tmp_path, capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stdout[-4000:]

    script = """
import fitz
doc = fitz.open('pagination.pdf')
assert len(doc) >= 3
assert sum(page.get_text().count('PAGINATIONREGRESSION') for page in doc) == 1
all_words = []
for page in doc:
    text = page.get_text()
    assert text.count('GIRDERHEADER') == 1
    footer = page.search_for('FOSSEE')[0]
    for word in page.get_text('words'):
        if word[4] == 'G4' or word[4].startswith('MEMBER'):
            assert 65 < word[0] < word[2] < page.rect.width - 65
            assert word[3] < footer.y0 - 8
        all_words.append(word[4])
assert all_words.count('G4') == 48
for i in range(48):
    assert all_words.count(f'MEMBER{i:02d}') == 1
    assert all_words.count(f'{i}.75') == 1
"""
    subprocess.run([pdf_python, "-c", script], cwd=tmp_path, check=True, timeout=30)
