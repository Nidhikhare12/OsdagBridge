"""Tests that the report preamble is driven by ``styles``."""

from __future__ import annotations

import dataclasses

import pytest

from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_generator import preamble


def _preamble() -> str:
    return preamble("Bridge", "JOB-1", "14 Nov 2026")


def test_default_values_appear_in_preamble() -> None:
    tex = _preamble()
    assert r"\usepackage[a4paper, margin=1in, footskip=40pt]{geometry}" in tex
    assert r"\setlength{\tabcolsep}{6pt}" in tex
    assert r"\renewcommand{\arraystretch}{1.12}" in tex
    assert r"\definecolor{osdagGreen}{HTML}{91B014}" in tex


def test_changing_table_style_restyles_preamble(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        styles, "TABLE",
        dataclasses.replace(styles.TABLE, tabcolsep="9pt",
                            arraystretch="1.5"))
    tex = _preamble()
    assert r"\setlength{\tabcolsep}{9pt}" in tex
    assert r"\renewcommand{\arraystretch}{1.5}" in tex
    assert r"\setlength{\tabcolsep}{6pt}" not in tex


def test_changing_page_style_restyles_geometry(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        styles, "PAGE", dataclasses.replace(styles.PAGE, margin="2cm"))
    assert "margin=2cm" in _preamble()


def test_changing_palette_restyles_colour(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        styles, "PALETTE", dataclasses.replace(styles.PALETTE,
                                               osdag_green="123456"))
    assert r"{HTML}{123456}" in _preamble()


def test_styles_are_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        styles.TABLE.tabcolsep = "1pt"  # type: ignore[misc]


def test_row_gap_and_column_unit_are_defined_from_styles(
        monkeypatch: pytest.MonkeyPatch) -> None:
    tex = _preamble()
    assert r"\newlength{\rowgap}\setlength{\rowgap}{6pt}" in tex
    assert r"\newlength{\colunit}\setlength{\colunit}{1cm}" in tex
    monkeypatch.setattr(
        styles, "TABLE",
        dataclasses.replace(styles.TABLE, row_gap="9pt", column_unit="0.9cm"))
    tex = _preamble()
    assert r"\setlength{\rowgap}{9pt}" in tex
    assert r"\setlength{\colunit}{0.9cm}" in tex


def test_chapters_contain_no_hardcoded_row_gaps_or_column_widths() -> None:
    """Guard: layout values must come from styles.py, not chapter strings."""
    import re
    from pathlib import Path

    folder = Path(styles.__file__).parent
    gap = re.compile(r"\\\\\[\d+(?:\.\d+)?pt\]")
    width = re.compile(r"[LCRpmbX]\{\d+(?:\.\d+)?cm\}")
    offenders = []
    for path in sorted(folder.glob("chap*.py")):
        text = path.read_text(encoding="utf-8")
        offenders += [path.name for _ in gap.findall(text)]
        offenders += [path.name for _ in width.findall(text)]
    assert offenders == []
