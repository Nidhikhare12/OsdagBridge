"""Shared chart building blocks: figure creation, styling, bars, labels, export.

Every visual attribute is read from ``ChartTheme`` (``core/reports/theme.py``).
Figures are built on the object-oriented matplotlib API with an Agg canvas, so
generating a report never touches ``pyplot`` state or the GUI backend of the
desktop application.
"""

from __future__ import annotations

import logging
import re
import textwrap
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Optional, Sequence, Tuple

import matplotlib
from matplotlib import patheffects
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from osdagbridge.core.reports.theme import ChartTheme, Theme, get_active_theme

logger = logging.getLogger(__name__)

# gid tags that identify chart artists (used by the unit tests)
GID_LIMIT_LINE = "ur-limit-line"
GID_NOT_COMPUTED = "not-computed"
GID_VALUE_LABEL = "value-label"
GID_OUTLINE = "bar-outline"

LIMIT_LABEL = "UR = 1.0 limit"
NOT_COMPUTED_TEXT = "Not computed"
NOT_APPLICABLE_TEXT = "Not applicable"

EN_DASH = "–"
POINTS_PER_INCH = 72.0
# Average glyph width of a sans-serif face as a fraction of the font size.
_GLYPH_WIDTH_EM = 0.55


def resolve_theme(theme: Theme | None) -> Theme:
    """Return the explicit theme or the active one."""
    return theme or get_active_theme()


def display_text(text: Any) -> str:
    """Convert a LaTeX-flavoured label into plain chart text (en dash, no ``---``)."""
    s = re.sub(r"\s*-{2,3}\s*", f" {EN_DASH} ", str(text))
    return " ".join(s.replace("~", " ").split())


def wrap_label(text: str, width_in: float, font_pt: float, min_chars: int = 6) -> str:
    """Wrap ``text`` so that it fits a strip ``width_in`` inches wide."""
    glyph_in = _GLYPH_WIDTH_EM * font_pt / POINTS_PER_INCH
    max_chars = max(min_chars, int(width_in / glyph_in))
    lines = textwrap.wrap(text, width=max_chars, break_long_words=False) or [text]
    return "\n".join(lines)


@contextmanager
def chart_style(theme: Theme | None = None) -> Iterator[ChartTheme]:
    """Apply the chart theme for the duration of a build or save (no global side effects)."""
    c = resolve_theme(theme).chart
    rc = {
        "font.family": c.font_family,
        "font.size": c.base_font_size,
        "text.color": c.text_color,
        "axes.labelcolor": c.text_color,
        "axes.edgecolor": c.axis_color,
        "axes.linewidth": c.axis_width,
        "xtick.color": c.axis_color,
        "ytick.color": c.axis_color,
        "xtick.labelcolor": c.text_color,
        "ytick.labelcolor": c.text_color,
        "xtick.labelsize": c.tick_label_size,
        "ytick.labelsize": c.tick_label_size,
        "hatch.linewidth": c.hatch_linewidth,
        "mathtext.default": "regular",
        "figure.autolayout": False,
    }
    with matplotlib.rc_context(rc):
        yield c


def new_figure(
    figsize: Tuple[float, float],
    theme: Theme | None = None,
    ncols: int = 1,
) -> Tuple[Figure, Any]:
    """Create a themed Figure on an Agg canvas; returns ``(fig, ax)`` or ``(fig, axes)``."""
    c = resolve_theme(theme).chart
    fig = Figure(figsize=figsize, dpi=c.dpi, facecolor=c.figure_face)
    FigureCanvasAgg(fig)
    if ncols == 1:
        axes = fig.add_subplot(1, 1, 1)
        style_axes(axes, c)
    else:
        axes = [fig.add_subplot(1, ncols, i + 1) for i in range(ncols)]
        for ax in axes:
            style_axes(ax, c)
        fig.subplots_adjust(wspace=c.panel_wspace)
    return fig, axes


def setup_figure(
    figsize: Tuple[float, float] | None = None,
    dpi: int | None = None,
    theme: Theme | None = None,
) -> Tuple[Figure, Any]:
    """Create a themed single-axes figure (kept for backward compatibility)."""
    c = resolve_theme(theme).chart
    fig, ax = new_figure(figsize or c.figsize_overall, theme=theme)
    if dpi:
        fig.set_dpi(dpi)
    return fig, ax


def style_axes(ax: Any, c: ChartTheme, value_axis: str = "y") -> None:
    """Recessive grid on the value axis only, open top/right frame."""
    ax.set_facecolor(c.figure_face)
    ax.set_axisbelow(True)
    ax.grid(False)
    ax.grid(True, axis=value_axis, color=c.grid_color, alpha=c.grid_alpha,
            linestyle=c.grid_style, linewidth=c.grid_width)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(c.axis_color)
        ax.spines[side].set_linewidth(c.axis_width)
    ax.tick_params(axis="both", colors=c.axis_color, labelcolor=c.text_color,
                   labelsize=c.tick_label_size, width=c.axis_width)
    category_axis = "x" if value_axis == "y" else "y"
    ax.tick_params(axis=value_axis, length=c.tick_length)
    ax.tick_params(axis=category_axis, length=0)


def apply_margins(fig: Figure, margins: Tuple[float, float, float, float]) -> None:
    """Place the axes box from a theme ``(left, right, top, bottom)`` tuple."""
    left, right, top, bottom = margins
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)


def slot_width_in(ax: Any) -> float:
    """Width in inches of one data unit on the category (x) axis."""
    lo, hi = ax.get_xlim()
    return ax.get_position().width * ax.figure.get_figwidth() / abs(hi - lo)


def set_title(ax: Any, text: str, c: ChartTheme) -> None:
    ax.set_title(display_text(text), fontsize=c.title_size, fontweight=c.title_weight,
                 color=c.text_color, pad=c.title_pad)


def set_value_axis_label(ax: Any, text: str, c: ChartTheme, horizontal: bool = False) -> None:
    setter = ax.set_xlabel if horizontal else ax.set_ylabel
    setter(text, fontsize=c.axis_label_size, fontweight=c.axis_label_weight, color=c.text_color)


def value_limit(max_value: float, c: ChartTheme, floor: float = 0.0) -> float:
    """Upper axis limit: ``headroom`` above the tallest bar or ``floor``, whichever is higher."""
    top = max(float(max_value), float(floor))
    if top <= 0.0:
        top = 1.0
    return top * (1.0 + c.headroom)


def draw_bars(
    ax: Any,
    positions: Sequence[float],
    values: Sequence[float],
    colors: Sequence[str],
    c: ChartTheme,
    width: float,
    failing: Sequence[bool] | None = None,
    horizontal: bool = False,
) -> BarContainer:
    """Draw value bars and return their container.

    Failing bars take the fail colour *and* the fail hatch. The hatch is drawn
    in ``fail_hatch_color`` and a separate outline layer restores the common
    bar edge, which keeps the result identical on every matplotlib version.
    """
    failing = list(failing) if failing is not None else [False] * len(values)
    draw = ax.barh if horizontal else ax.bar
    bars = draw(positions, values, width, color=list(colors), linewidth=0, zorder=2)
    for bar, is_fail in zip(bars, failing):
        if is_fail:
            bar.set_facecolor(c.bar_fail)
            bar.set_edgecolor(c.fail_hatch_color)
            bar.set_hatch(c.fail_hatch)
    outline = draw(positions, values, width, color="none", edgecolor=c.bar_edge_color,
                   linewidth=c.bar_edge_width, zorder=3)
    for patch in outline:
        patch.set_gid(GID_OUTLINE)
    return bars


def _halo(c: ChartTheme) -> list:
    return [patheffects.withStroke(linewidth=c.label_halo_width, foreground=c.figure_face)]


def add_value_label(ax: Any, position: float, value: float, text: str, c: ChartTheme,
                    horizontal: bool = False) -> Any:
    """Value label just beyond the end of a bar (above, or to the right for horizontal bars)."""
    if horizontal:
        xy, offset, ha, va = (value, position), (c.label_offset_pt, 0), "left", "center"
    else:
        xy, offset, ha, va = (position, value), (0, c.label_offset_pt), "center", "bottom"
    ann = ax.annotate(text, xy=xy, xytext=offset, textcoords="offset points", ha=ha, va=va,
                      fontsize=c.label_size, fontweight=c.label_weight, color=c.text_color,
                      zorder=7, annotation_clip=False)
    ann.set_path_effects(_halo(c))
    ann.set_gid(GID_VALUE_LABEL)
    return ann


def add_missing_marker(ax: Any, position: float, c: ChartTheme, text: str = NOT_COMPUTED_TEXT,
                       horizontal: bool = False, rotation: float = 0.0) -> Any:
    """Explicit marker for a value that was not computed. Never draws a bar."""
    if horizontal:
        xy, offset, ha, va = (0.0, position), (c.label_offset_pt * 2, 0), "left", "center"
    else:
        xy, offset, ha, va = (position, 0.0), (0, c.label_offset_pt * 2), "center", "bottom"
    ann = ax.annotate(
        text, xy=xy, xytext=offset, textcoords="offset points", ha=ha, va=va, rotation=rotation,
        fontsize=c.annotation_size, fontstyle=c.missing_font_style, color=c.missing_text_color,
        zorder=6, annotation_clip=False,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=c.missing_box_face, edgecolor=c.missing_box_edge,
                  linestyle=c.missing_box_style, linewidth=c.missing_box_width),
    )
    ann.set_gid(GID_NOT_COMPUTED)
    return ann


def add_limit_line(ax: Any, c: ChartTheme, horizontal: bool = False, value: float = 1.0) -> Line2D:
    """Dashed UR = 1.0 reference line in the theme threshold colour."""
    draw = ax.axvline if horizontal else ax.axhline
    line = draw(value, color=c.threshold_color, linestyle=c.threshold_style,
                linewidth=c.threshold_width, label=LIMIT_LABEL, zorder=5)
    line.set_gid(GID_LIMIT_LINE)
    return line


def swatch(color: str, c: ChartTheme, label: str) -> Patch:
    """Legend patch for a plain bar colour."""
    return Patch(facecolor=color, edgecolor=c.bar_edge_color, linewidth=c.bar_edge_width, label=label)


def fail_swatch(c: ChartTheme, label: str) -> Patch:
    """Legend patch for a failing (hatched) bar."""
    return Patch(facecolor=c.bar_fail, edgecolor=c.fail_hatch_color, hatch=c.fail_hatch,
                 linewidth=0, label=label)


def missing_swatch(c: ChartTheme, label: str) -> Patch:
    """Legend patch for the 'not computed' marker."""
    return Patch(facecolor=c.missing_box_face, edgecolor=c.missing_box_edge,
                 linestyle=c.missing_box_style, linewidth=c.missing_box_width, label=label)


def points_to_axes_y(ax: Any, points: float) -> float:
    """Convert a length in points into a fraction of the axes height."""
    height_in = ax.get_position().height * ax.figure.get_figheight()
    return points / POINTS_PER_INCH / height_in


def depth_below_axes_pt(ax: Any, artists: Sequence[Any]) -> float:
    """Distance in points from the bottom of the axes to the lowest of ``artists``."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bottom = ax.get_window_extent(renderer).y0
    lows = [a.get_window_extent(renderer).y0 for a in artists if a.get_visible() and a.get_text()]
    if not lows:
        return 0.0
    return max(0.0, (bottom - min(lows)) * POINTS_PER_INCH / fig.dpi)


def add_legend_below(ax: Any, handles: Sequence[Any], c: ChartTheme, depth_pt: float,
                     ncol: int | None = None) -> Any:
    """Legend outside the axes, ``depth_pt`` below its bottom edge, so it can never cover a bar."""
    y = -points_to_axes_y(ax, depth_pt + c.legend_pad_pt)
    items = list(handles)
    ncol = max(1, min(ncol or len(items), len(items)))
    # matplotlib fills a legend column by column; reorder so it reads row by row
    nrows = -(-len(items) // ncol)
    by_column = [items[r * ncol + col] for col in range(ncol) for r in range(nrows)
                 if r * ncol + col < len(items)]
    legend = ax.legend(
        handles=by_column, loc="upper center", bbox_to_anchor=(0.5, y),
        ncol=ncol, fontsize=c.legend_size, frameon=True,
        framealpha=c.legend_frame_alpha, edgecolor=c.legend_frame_color,
        facecolor=c.figure_face, borderaxespad=0.0, handlelength=1.8, columnspacing=1.4,
    )
    for text in legend.get_texts():
        text.set_color(c.text_color)
    return legend


def save_chart(fig: Figure, output_path: str | Path, dpi: int | None = None,
               theme: Theme | None = None) -> str:
    """Write the figure as a tightly cropped image and release it."""
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with chart_style(theme) as c:
        fig.savefig(str(path), dpi=dpi or c.dpi, bbox_inches="tight", pad_inches=c.save_pad_in,
                    facecolor=c.figure_face)
    fig.clear()
    return str(path)


@dataclass
class ChartOutcome:
    """Result of one guarded chart render."""
    path: Optional[str] = None      # saved image, or None
    failed: bool = False            # True when the plot function raised
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.path) and not self.failed


def render_chart_safely(plot_fn: Callable[..., Optional[str]], data: Any,
                        output_path: str | Path, theme: Theme | None = None) -> ChartOutcome:
    """Run one plot function; a failure is logged and reported, never raised.

    The report builder uses the outcome to print the standard placeholder
    panel in place of a chart that could not be drawn.
    """
    try:
        return ChartOutcome(path=plot_fn(data, output_path, theme=theme))
    except Exception as exc:  # noqa: BLE001 - a chart must never break the report
        logger.warning("Chart %s could not be generated: %s",
                       getattr(plot_fn, "__name__", plot_fn), exc, exc_info=True)
        return ChartOutcome(path=None, failed=True, error=f"{type(exc).__name__}: {exc}")
