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
    paper_width_cm: float = 21.0   # A4; must agree with ``paper``

    @property
    def text_width_cm(self) -> float:
        """Width of the text block: paper width minus left and right margins."""
        return self.paper_width_cm - self.margin_left_cm - self.margin_right_cm

    @property
    def text_width_pt(self) -> float:
        """Text block width in TeX points (72.27 pt per inch)."""
        return self.text_width_cm * 72.27 / 2.54


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
    table_font_size_dense: str = r"\small"   # one step smaller, for tables with many columns
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
    # Fit-to-text-block rules (tables are never wider than the text block)
    dense_min_cols: int = 7            # from this many columns the dense font and padding apply
    dense_col_sep_pt: float = 3.0      # \tabcolsep inside dense tables
    max_bare_cols: int = 4             # above this, bare l/c/r columns get a fixed width
    # Space reserved before a longtable so its first head is never orphaned
    # (counted in \baselineskip units)
    needspace_caption_lines: int = 2
    needspace_lines_per_header_row: int = 2
    needspace_min_body_rows: int = 4
    needspace_foot_lines: int = 1


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
    # Running header: left = project name, right = "job no. <separator> date".
    # Footer: left = footer_text, centre = report version, right = page_label.
    font: str = r"\footnotesize"
    header_left_max_chars: int = 60        # project name is cut with an ellipsis above this
    header_job_max_chars: int = 24
    header_date_max_chars: int = 20
    footer_center_max_chars: int = 30      # report version / revision
    header_separator: str = r"\ \textperiodcentered\ "
    ellipsis: str = r"\ldots{}"
    min_gap: str = r"\quad"                # smallest gap between two parts of one line
    page_label: str = r"Page \thepage\ of \pageref{LastPage}"


@dataclass(frozen=True)
class ChartTheme:
    """Matplotlib styling for generated figures (R4 and R5).

    Single source of truth for every colour, size, line style and hatch used
    by ``core/reports/charts``; the chart modules contain no literals.
    """
    # --- Raster output and figure sizes (inches) ---
    dpi: int = 200
    figsize_overall: Tuple[float, float] = (8.5, 4.4)
    figsize_girder: Tuple[float, float] = (7.5, 4.0)
    figsize_girder_horizontal: Tuple[float, float] = (7.5, 1.7)  # height grows per girder
    girder_row_height_in: float = 0.34
    figsize_steel: Tuple[float, float] = (7.5, 4.0)
    figsize_quantity: Tuple[float, float] = (8.5, 4.0)
    panel_wspace: float = 0.34
    # Axes box inside the figure as (left, right, top, bottom) figure fractions
    margins_overall: Tuple[float, float, float, float] = (0.08, 0.985, 0.90, 0.12)
    margins_girder: Tuple[float, float, float, float] = (0.10, 0.98, 0.90, 0.12)
    margins_girder_horizontal: Tuple[float, float, float, float] = (0.10, 0.70, 0.90, 0.14)
    margins_quantity: Tuple[float, float, float, float] = (0.10, 0.98, 0.90, 0.12)
    figure_face: str = "#FFFFFF"
    save_pad_in: float = 0.08

    # --- Fonts ---
    font_family: str = "sans-serif"
    base_font_size: float = 10.0
    title_size: float = 12.0
    title_weight: str = "bold"
    title_pad: float = 10.0
    axis_label_size: float = 10.0
    axis_label_weight: str = "bold"
    tick_label_size: float = 9.0
    label_size: int = 9                 # value label above / beside a bar
    label_weight: str = "bold"
    label_offset_pt: float = 3.0
    label_halo_width: float = 2.5       # figure-coloured outline so a line never strikes through a label
    group_label_size: float = 9.5
    annotation_size: float = 8.0        # governing-check and "not computed" text
    legend_size: float = 8.5
    tick_rotation: float = 38.0

    # --- Ink ---
    text_color: str = "#212529"
    muted_text_color: str = "#5C636A"
    axis_color: str = "#495057"
    axis_width: float = 0.8
    tick_length: float = 3.0
    grid_color: str = "#ADB5BD"
    grid_alpha: float = 0.35
    grid_style: str = ":"
    grid_width: float = 0.6

    # --- Bars ---
    bar_pass: str = "#2B8A3E"
    bar_fail: str = "#E03131"
    bar_neutral: str = "#91B014"
    bar_secondary: str = "#1971C2"
    bar_edge_color: str = "#212529"
    bar_edge_width: float = 0.8
    bar_width: float = 0.66             # overall UR chart
    bar_width_girder: float = 0.56      # per-girder chart
    bar_width_quantity: float = 0.50    # Chapter 7 charts
    min_category_slots: float = 2.6     # keeps a lone bar slim instead of filling its panel
    headroom: float = 0.12              # free space above the tallest bar / limit line
    fail_hatch: str = "///"
    fail_hatch_color: str = "#FFFFFF"
    hatch_linewidth: float = 1.0

    # --- One colour per structural element (same colour in every chart) ---
    element_girder: str = "#91B014"
    element_deck: str = "#2A78D6"
    element_bracing: str = "#EDA100"
    element_diaphragm: str = "#6250D6"
    element_studs: str = "#1BAF7A"
    concrete_color: str = "#868E96"
    rebar_color: str = "#1971C2"

    # --- UR = 1.0 limit line ---
    threshold_color: str = "#E03131"
    threshold_style: str = "--"
    threshold_width: float = 1.8

    # --- Element grouping under the x axis (overall UR chart) ---
    group_gap: float = 0.7              # extra bar slots between two element groups
    group_bracket_color: str = "#495057"
    group_bracket_width: float = 1.0
    group_bracket_pad_pt: float = 6.0
    group_bracket_tick_pt: float = 4.0

    # --- "Not computed" marker (never a bar) ---
    missing_text_color: str = "#5C636A"
    missing_box_face: str = "#F1F3F5"
    missing_box_edge: str = "#868E96"
    missing_box_style: str = "--"
    missing_box_width: float = 0.8
    missing_font_style: str = "italic"

    # --- Per-girder chart ---
    horizontal_above: int = 8           # more girders than this -> horizontal bars
    label_fill: float = 0.92            # share of a bar slot a wrapped label may occupy

    # --- Legend ---
    legend_frame_color: str = "#CED4DA"
    legend_frame_alpha: float = 0.95
    legend_pad_pt: float = 8.0


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
