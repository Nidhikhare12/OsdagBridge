"""Single source of truth for the design report's visual style.

Page geometry, table layout and colours used by the LaTeX preamble are
defined here once. ``report_generator.preamble`` reads these values at call
time, so changing one value restyles the whole report.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageStyle:
    """Page geometry (LaTeX ``geometry`` package options)."""

    paper: str = "a4paper"
    margin: str = "1in"
    footskip: str = "40pt"

    @property
    def geometry_options(self) -> str:
        """Return the option string for ``\\usepackage[...]{geometry}``."""
        return (f"{self.paper}, margin={self.margin}, "
                f"footskip={self.footskip}")


@dataclass(frozen=True)
class TableStyle:
    """Table padding, row height and rule thickness."""

    tabcolsep: str = "6pt"
    arraystretch: str = "1.12"
    longtable_pre: str = "0pt"
    longtable_post: str = "6pt"
    rule_width: str = "0.5pt"
    extra_row_height: str = "0.6pt"
    needspace_lines: int = 5
    row_gap: str = "6pt"
    row_gap_wide: str = "8pt"
    row_gap_tight: str = "3pt"
    row_gap_label: str = "2pt"
    column_unit: str = "1cm"


@dataclass(frozen=True)
class LoadTableStyle:
    """Layout of the Chapter 3 live-load tables.

    Widths are multiples of ``TableStyle.column_unit`` (``\\colunit`` in
    LaTeX) and are chosen so six padded columns fit the 1 in text block.
    """

    vehicle_columns: str = (
        r"|L{3.0\colunit}|C{1.8\colunit}|C{1.8\colunit}|C{2.3\colunit}"
        r"|C{2.0\colunit}|C{2.4\colunit}|")
    footway_columns: str = r"|L{5.5\colunit}|C{3.5\colunit}|L{6.5\colunit}|"
    placeholder: str = "--"


@dataclass(frozen=True)
class ChartStyle:
    """Matplotlib settings for the report charts (items 4 and 5)."""

    width_in: float = 6.3
    height_in: float = 3.4
    dpi: int = 200
    font_family: tuple[str, ...] = (
        "Latin Modern Roman", "CMU Serif", "DejaVu Serif")
    font_size: float = 9.0
    title_size: float = 10.5
    bar_width: float = 0.55
    value_headroom: float = 0.18
    ur_limit: float = 1.0
    pass_color: str = "#0072B2"
    fail_color: str = "#E69F00"
    limit_color: str = "#D62728"
    steel_color: str = "#4D6D8F"
    concrete_color: str = "#8C8C8C"
    rebar_color: str = "#B5651D"
    edge_color: str = "#222222"
    grid_color: str = "#BBBBBB"
    fail_hatch: str = "//"
    latex_width: str = r"0.92\textwidth"


@dataclass(frozen=True)
class Palette:
    """Brand colours as six-digit HTML hex (no leading ``#``)."""

    osdag_green: str = "91B014"


PAGE = PageStyle()
TABLE = TableStyle()
LOAD_TABLES = LoadTableStyle()
CHARTS = ChartStyle()
PALETTE = Palette()
