"""Centralized Theme & Styling System for OsdagBridge LaTeX Report Generator.

Serves as the single source of truth (Requirement R6) for all layout rules,
color palettes, table dimensions, header/footer geometry, and chart styling.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional


@dataclass(frozen=True)
class PageTheme:
    """Document geometry and page margins."""
    paper: str = "a4paper"
    font_size_pt: int = 12
    margin_top_cm: float = 2.54
    margin_bottom_cm: float = 2.80
    margin_left_cm: float = 2.54
    margin_right_cm: float = 2.54
    head_height_pt: float = 20.0
    head_sep_pt: float = 14.0
    foot_skip_pt: float = 38.0
    line_stretch: float = 1.15


@dataclass(frozen=True)
class Palette:
    """Hex color definitions for document elements."""
    brand: str = "91B014"          # Osdag Green (#91B014)
    text_primary: str = "000000"   # Black
    text_muted: str = "555555"     # Dark grey
    rule: str = "91B014"           # Green rule
    rule_light: str = "D3D3D3"     # Light grey grid rules
    table_header_bg: str = "FFFFFF"# Plain white for classic table header
    table_stripe_bg: str = "F7F9F2"# Subtle green/grey tint for striped tables
    status_pass: str = "008000"    # Forest green
    status_fail: str = "CC0000"    # Crimson red
    status_warn: str = "D97706"    # Amber
    threshold_line: str = "CC0000" # Red threshold line


@dataclass(frozen=True)
class Typography:
    """Font sizes and heading formatting."""
    chapter_font_size: str = r"\huge\bfseries"
    section_font_size: str = r"\Large\bfseries"
    subsection_font_size: str = r"\large\bfseries"
    caption_font: str = r"\small\bfseries"
    table_font_size: str = r"\normalsize"
    note_font_size: str = r"\footnotesize"


@dataclass(frozen=True)
class TableTheme:
    """Cell paddings, rule widths, and longtable break parameters."""
    col_sep_pt: float = 6.0
    row_stretch: float = 1.12
    row_pad_pt: float = 6.0
    rule_width_pt: float = 0.5
    min_rows_before_break: int = 5
    continued_label: str = "(continued)"
    continues_label: str = "Continued on next page"
    header_bold: bool = True
    striped: bool = False


@dataclass(frozen=True)
class ColumnPresets:
    """Standardized column width specifications across report chapters."""
    KEY_VALUE: Tuple[str, str] = ("5.5cm", "10.0cm")
    SUMMARY_4COL: Tuple[str, str, str, str] = ("4.0cm", "4.0cm", "4.0cm", "3.5cm")
    DEMAND_9COL: Tuple[str, ...] = (
        "3.2cm", "1.8cm", "1.2cm", "1.4cm", "1.8cm", "1.2cm", "1.4cm", "1.6cm", "1.6cm"
    )
    CHECK_5COL: Tuple[str, str, str, str, str] = ("4.0cm", "4.0cm", "3.5cm", "2.5cm", "1.8cm")
    QUANTITY_8COL: Tuple[str, ...] = (
        "1.0cm", "4.5cm", "3.5cm", "1.5cm", "1.8cm", "1.8cm", "1.8cm"
    )


@dataclass(frozen=True)
class HeaderFooterTheme:
    """Running header and footer formatting templates."""
    rule_height_pt: float = 1.0
    rule_color: str = "91B014"
    footer_text: str = r"Osdag \textbar{} FOSSEE \textbar{} Indian Institute of Technology Bombay"
    sd_note_text: str = r"\footnotesize * Software default value"
    sd_note_reserved_height_pt: float = 12.0


@dataclass(frozen=True)
class ChartTheme:
    """Matplotlib styling for generated figures (R4 and R5)."""
    dpi: int = 200
    figsize_overall: Tuple[float, float] = (8.5, 4.8)
    figsize_quantity: Tuple[float, float] = (8.5, 4.2)
    font_family: str = "sans-serif"
    bar_pass: str = "#2B8A3E"
    bar_fail: str = "#E03131"
    bar_neutral: str = "#91B014"
    bar_secondary: str = "#1971C2"
    threshold_color: str = "#E03131"
    threshold_style: str = "--"
    threshold_width: float = 1.8
    grid_alpha: float = 0.35
    label_size: int = 9
    fail_hatch: str = "///"


@dataclass(frozen=True)
class Theme:
    """Aggregated Theme definition."""
    name: str
    page: PageTheme = field(default_factory=PageTheme)
    palette: Palette = field(default_factory=Palette)
    typography: Typography = field(default_factory=Typography)
    table: TableTheme = field(default_factory=TableTheme)
    columns: ColumnPresets = field(default_factory=ColumnPresets)
    header_footer: HeaderFooterTheme = field(default_factory=HeaderFooterTheme)
    chart: ChartTheme = field(default_factory=ChartTheme)


# Default theme reproducing classic OsdagBridge styling
DEFAULT_THEME = Theme(name="osdag_classic")

# Active theme registry
_ACTIVE_THEME: Theme = DEFAULT_THEME


def get_active_theme() -> Theme:
    """Return the currently active theme."""
    return _ACTIVE_THEME


def set_active_theme(theme_or_name: Theme | str) -> Theme:
    """Set the active theme by instance or registered preset name."""
    global _ACTIVE_THEME
    if isinstance(theme_or_name, Theme):
        _ACTIVE_THEME = theme_or_name
        return _ACTIVE_THEME

    from osdagbridge.core.reports.themes import get_theme
    _ACTIVE_THEME = get_theme(theme_or_name)
    return _ACTIVE_THEME
