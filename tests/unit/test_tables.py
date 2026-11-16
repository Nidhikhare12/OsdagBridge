"""Unit tests for ReportTable, KeyValueTable, SimpleTable (Requirement R1, T-TABLE-1, T-TABLE-2)."""

import pytest
from pathlib import Path
import tempfile
import subprocess
import os

from osdagbridge.core.reports.latex.tables import ReportTable, KeyValueTable, SimpleTable
from osdagbridge.core.reports.latex.document import build_preamble
from osdagbridge.core.reports.latex.compile import compile_tex
from osdagbridge.core.reports.qa.pdf_lint import check_header_repeat


def test_table_structure_and_order():
    """Verify T-TABLE-1: table contains \\endfirsthead, \\endhead, \\endfoot, \\endlastfoot in order."""
    tbl = ReportTable(
        columns=2,
        caption="Sample Table",
        label="tab:sample",
        header_rows=[["Parameter", "Value"]],
    )
    tbl.add_row(["Span", "24.0 m"])
    tbl.add_row(["Girders", "4"])
    out = tbl.dumps()

    # Assert presence
    assert r"\caption{Sample Table}\label{tab:sample}\\" in out
    assert r"\endfirsthead" in out
    assert r"\endhead" in out
    assert r"\endfoot" in out
    assert r"\endlastfoot" in out

    # Assert correct structural ordering
    pos_cap = out.index(r"\caption{Sample Table}")
    pos_firsthead = out.index(r"\endfirsthead")
    pos_head = out.index(r"\endhead")
    pos_foot = out.index(r"\endfoot")
    pos_lastfoot = out.index(r"\endlastfoot")
    pos_body = out.index(r"Span&24.0 m")

    assert pos_cap < pos_firsthead < pos_head < pos_foot < pos_lastfoot < pos_body


def test_table_column_count_validation():
    """Verify T-TABLE-1: column count validation raises ValueError on ragged row."""
    tbl = ReportTable(columns=3, caption="Validation Test", header_rows=[["A", "B", "C"]])

    # Adding valid 3-cell row succeeds
    tbl.add_row(["1", "2", "3"])

    # Adding 2-cell or 4-cell row raises ValueError
    with pytest.raises(ValueError, match="Row has 2 cells, expected 3"):
        tbl.add_row(["1", "2"])

    with pytest.raises(ValueError, match="Row has 4 cells, expected 3"):
        tbl.add_row(["1", "2", "3", "4"])


def test_key_value_table():
    """Verify KeyValueTable builder convenience wrapper."""
    kv = KeyValueTable(
        caption="KV Test",
        rows=[("Length", "10 m"), ("Width", "5 m")],
    )
    out = kv.dumps()
    assert r"\caption{KV Test}" in out
    assert r"\endfirsthead" in out
    assert "Length&10 m" in out
    assert "Width&5 m" in out


def test_simple_table():
    """Verify SimpleTable non-breaking tabular builder."""
    st = SimpleTable(col_spec="|l|r|", rows=[["Item", "Cost"], ["Steel", "1000"]])
    out = st.dumps()
    assert r"\begin{tabular}{|l|r|}" in out
    assert "Item & Cost \\" in out
    assert "Steel & 1000 \\" in out
    assert r"\end{tabular}" in out


@pytest.mark.latex
def test_200_row_table_header_repeat():
    """Verify T-TABLE-2: A 200-row table compiles and headers repeat across pages."""
    tbl = ReportTable(
        columns=2,
        caption="Multi-Page Load Demands",
        header_rows=[["Member ID", "Bending Moment (kNm)"]],
    )
    for i in range(1, 201):
        tbl.add_row([f"M_{i}", f"{1000 + i * 5:.2f}"])

    tex_content = "\n".join([
        build_preamble("Stress Test", "JOB-200", "2026-11-16"),
        tbl.dumps(),
        r"\end{document}",
    ])

    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, "test_table.tex")
        pdf_path = os.path.join(tmp_dir, "test_table.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Run pdflatex via compiler discovery
        success = compile_tex(tex_path)
        assert success and os.path.exists(pdf_path), "pdflatex compilation failed"

        # Verify header repeat across pages using check_header_repeat
        violations = check_header_repeat(pdf_path, expected_header_text="Member ID")
        assert len(violations) == 0, f"Header repeat violations: {violations}"
