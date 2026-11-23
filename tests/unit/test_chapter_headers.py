"""Every longtable in the chapters repeats its header (task item 1)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.latex_tables import normalize_longtables
from osdagbridge.core.reports.report_generator import (
    ReportDataBridge,
    preamble,
)
from osdagbridge.core.utils import common as keys

OUTPUT = {"design_results": {"per_girder": {"G1": {"checks": [
    {"check_id": 1, "dcr": 0.74, "demand": 1200.0, "capacity": 1620.0,
     "demand_unit": "kN-m", "capacity_unit": "kN-m"}], "per_lc": {}}}}}


@pytest.fixture(scope="module")
def chapter5() -> str:
    return normalize_longtables(
        ch5_design_checks({}, ReportDataBridge(OUTPUT, {}, None)))


def _tables(tex: str) -> list[str]:
    parts = tex.split(r"\begin{longtable}")[1:]
    return [part.split(r"\end{longtable}")[0] for part in parts]


@pytest.mark.parametrize("name,build", [
    ("chapter 3", lambda: ch3_loads({keys.KEY_SPAN: "30",
                                     keys.KEY_LL_IRC_CLASS_A: True})),
    ("chapter 7", lambda: ch7_quantities({})),
])
def test_every_table_repeats_its_header(name: str, build) -> None:
    tables = _tables(normalize_longtables(build()))
    assert tables
    assert all(r"\endfirsthead" in t and r"\endhead" in t for t in tables), name


def test_chapter_5_every_table_repeats_its_header(chapter5: str) -> None:
    tables = _tables(chapter5)
    assert len(tables) >= 25
    missing = [t[:80] for t in tables
               if r"\endfirsthead" not in t or r"\endhead" not in t]
    assert missing == []


@pytest.mark.parametrize("caption,header", [
    ("Stiffener Design Summary",
     r"\textbf{Girder} & \textbf{Parameter} & \textbf{Value}"),
    ("Deck Slab --- Loading and Geometry",
     r"\textbf{Parameter} & \textbf{Value}"),
])
def test_explicit_headers_are_written_in_the_source(
        chapter5: str, caption: str, header: str) -> None:
    table = next(t for t in _tables(chapter5) if caption in t)
    assert table.count(header) == 2            # first head + repeated head
    assert table.index(r"\caption") < table.index(r"\endfirsthead")
    assert table.count(r"\caption") == 1       # caption is never repeated


needs_tools = pytest.mark.skipif(
    any(shutil.which(t) is None for t in ("pdflatex", "pdftotext")),
    reason="pdflatex and pdftotext are required")


@needs_tools
@pytest.mark.parametrize("caption,marker", [
    ("Stiffener Design Summary", "Girder"),
    ("Deck Slab --- Loading and Geometry", "Parameter"),
])
def test_explicit_header_repeats_after_a_real_page_break(
        chapter5: str, tmp_path: Path, caption: str, marker: str) -> None:
    table = next(t for t in _tables(chapter5) if caption in t)
    body = r"\begin{longtable}" + table + r"\end{longtable}"
    for filler in range(14, 46, 2):
        text = "".join(f"\\noindent Filler {i}.\\par\n" for i in range(filler))
        tex = preamble("T", "J", "d") + text + body + "\n\\end{document}\n"
        (tmp_path / "doc.tex").write_text(tex, encoding="utf-8")
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "doc.tex"],
                           cwd=tmp_path, capture_output=True, check=False)
        pdf = (tmp_path / "doc.pdf")
        out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True,
                             text=True, check=True).stdout
        if "(continued)" in out:
            assert out.count(marker) >= 2, "header missing after the break"
            log = (tmp_path / "doc.log").read_text(errors="ignore")
            assert not any(ln.startswith("!") for ln in log.splitlines())
            return
    pytest.fail("could not force a page break to test the header")
