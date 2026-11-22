"""Theme presets for OsdagBridge Report Generator."""

from dataclasses import replace
from osdagbridge.core.reports.theme import (
    Theme, DEFAULT_THEME, Palette, HeaderFooterTheme, ChartTheme
)

# 1. Classic Osdag Theme (Default)
OSDAG_CLASSIC = DEFAULT_THEME

# 2. Print Monochrome Theme (Black and white ink friendly)
PRINT_MONO = Theme(
    name="print_mono",
    palette=Palette(
        brand="000000",
        rule="000000",
        rule_light="888888",
        status_pass="000000",
        status_fail="000000",
        status_warn="555555",
        threshold_line="000000",
    ),
    header_footer=HeaderFooterTheme(
        rule_color="000000",
    ),
    chart=ChartTheme(
        # Greyscale only. Elements are told apart by their group label and a
        # light/dark alternation; a failing bar is white with a dense black
        # cross-hatch, so pass/fail never depends on colour.
        bar_pass="#555555",
        bar_fail="#FFFFFF",
        bar_neutral="#777777",
        bar_secondary="#AAAAAA",
        bar_edge_color="#000000",
        fail_hatch="xxxx",
        fail_hatch_color="#000000",
        element_girder="#4D4D4D",
        element_deck="#B3B3B3",
        element_bracing="#737373",
        element_diaphragm="#D9D9D9",
        element_studs="#999999",
        concrete_color="#B3B3B3",
        rebar_color="#4D4D4D",
        threshold_color="#000000",
        text_color="#000000",
        muted_text_color="#404040",
        axis_color="#000000",
        grid_color="#808080",
        group_bracket_color="#000000",
        missing_text_color="#404040",
        missing_box_face="#FFFFFF",
        missing_box_edge="#000000",
        legend_frame_color="#808080",
    ),
)

# 3. Accessible Theme (Deuteranopia/Protanopia color-blind safe)
ACCESSIBLE = Theme(
    name="accessible",
    palette=Palette(
        brand="0072B2",          # Okabe-Ito Blue
        rule="0072B2",
        rule_light="CCCCCC",
        status_pass="009E73",    # Bluish Green
        status_fail="D55E00",    # Vermilion
        status_warn="E69F00",    # Orange
        threshold_line="D55E00",
    ),
    header_footer=HeaderFooterTheme(
        rule_color="0072B2",
    ),
    chart=ChartTheme(
        # Okabe-Ito hues, ordered so that neighbouring element groups stay
        # distinguishable under protanopia / deuteranopia.
        bar_pass="#009E73",
        bar_fail="#D55E00",
        bar_neutral="#0072B2",
        bar_secondary="#56B4E9",
        fail_hatch="///",
        fail_hatch_color="#FFFFFF",
        element_girder="#0072B2",
        element_deck="#009E73",
        element_bracing="#E69F00",
        element_diaphragm="#CC79A7",
        element_studs="#56B4E9",
        concrete_color="#868E96",
        rebar_color="#0072B2",
        threshold_color="#D55E00",
    ),
)

_THEME_REGISTRY = {
    "osdag_classic": OSDAG_CLASSIC,
    "print_mono": PRINT_MONO,
    "accessible": ACCESSIBLE,
}


def get_theme(name: str) -> Theme:
    """Retrieve theme preset by name."""
    clean_name = name.lower().strip()
    if clean_name not in _THEME_REGISTRY:
        raise KeyError(
            f"Unknown theme '{name}'. Available presets: {list(_THEME_REGISTRY.keys())}"
        )
    return _THEME_REGISTRY[clean_name]


def list_themes() -> list[str]:
    """Return available preset names."""
    return list(_THEME_REGISTRY.keys())
