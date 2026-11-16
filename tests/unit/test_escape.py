"""Test T-ESC-1: Verify LaTeX escaping behavior and non-ASCII character normalization."""

import pytest
from osdagbridge.core.reports.latex.escape import tex
from osdagbridge.core.reports.report_utils import _tex


def test_tex_escaping_characters():
    """Verify standard special characters are escaped."""
    raw = "Bridge & Structure #1 % 50$ {test} ~ ^ _ :"
    escaped = tex(raw)

    assert r"\&" in escaped
    assert r"\#" in escaped
    assert r"\%" in escaped
    assert r"\$" in escaped
    assert r"\{" in escaped
    assert r"\}" in escaped
    assert r"\_\allowbreak{}" in escaped
    assert r":\allowbreak{}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\^{}" in escaped


def test_tex_glyph_normalization():
    """Verify engineering glyphs (angles, times) are normalized for pdflatex."""
    assert tex("∠ 100 × 100 × 10") == "L 100 x 100 x 10"
    assert tex("ⅹ") == "x"


def test_tex_compatibility_shim():
    """Verify report_utils._tex is identical to latex.escape.tex."""
    sample = "Girder_1: span 30m & load 100kN"
    assert _tex(sample) == tex(sample)
