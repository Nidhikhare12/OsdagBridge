"""Test T-THEME-1: Verify theme dataclasses, immutability, and presets."""

from dataclasses import FrozenInstanceError
import pytest

from osdagbridge.core.reports.theme import (
    PageTheme, Palette, TableTheme, Theme, DEFAULT_THEME, get_active_theme, set_active_theme
)
from osdagbridge.core.reports.themes import get_theme, list_themes
from osdagbridge.core.reports.latex.document import build_preamble


def test_theme_immutability():
    """Verify that Theme and its sub-components are strictly immutable (frozen)."""
    theme = get_active_theme()

    with pytest.raises(FrozenInstanceError):
        theme.name = "new_name"

    with pytest.raises(FrozenInstanceError):
        theme.palette.brand = "FF0000"

    with pytest.raises(FrozenInstanceError):
        theme.page.font_size_pt = 14

    with pytest.raises(FrozenInstanceError):
        theme.table.row_stretch = 1.5


def test_theme_presets():
    """Verify all theme presets are registered and distinct."""
    themes = list_themes()
    assert "osdag_classic" in themes
    assert "print_mono" in themes
    assert "accessible" in themes

    classic = get_theme("osdag_classic")
    mono = get_theme("print_mono")
    accessible = get_theme("accessible")

    assert classic.palette.brand == "91B014"
    assert mono.palette.brand == "000000"
    assert accessible.palette.brand == "0072B2"

    with pytest.raises(KeyError):
        get_theme("non_existent_theme")


def test_theme_switcher():
    """Verify set_active_theme works with string and Theme objects."""
    set_active_theme("print_mono")
    assert get_active_theme().name == "print_mono"

    set_active_theme("osdag_classic")
    assert get_active_theme().name == "osdag_classic"


def test_preamble_theme_propagation():
    """Verify T-THEME-2: preamble built from modified theme contains modified values."""
    classic_tex = build_preamble("Proj", "Job", "Date", theme=get_theme("osdag_classic"))
    assert "91B014" in classic_tex
    assert "000000" not in classic_tex or "definecolor{osdagBrand}{HTML}{91B014}" in classic_tex

    mono_tex = build_preamble("Proj", "Job", "Date", theme=get_theme("print_mono"))
    assert "definecolor{osdagBrand}{HTML}{000000}" in mono_tex
    assert "91B014" not in mono_tex

