"""Material quantity bar charts for Chapter 7 (Requirement R5).

The charts plot exactly the numbers of ``data/quantities.py``
(``collect_quantities``). A quantity the bill of materials does not provide is
drawn as an explicit "Not computed" marker, never as a bar.

``build_*_figure`` returns the matplotlib Figure (for inspection in tests);
``plot_*`` builds, saves and returns the path of the image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from matplotlib.figure import Figure

from osdagbridge.core.reports.charts.base import (
    add_missing_marker,
    add_value_label,
    apply_margins,
    chart_style,
    draw_bars,
    new_figure,
    resolve_theme,
    save_chart,
    set_title,
    set_value_axis_label,
    value_limit,
)
from osdagbridge.core.reports.data.quantities import QuantitySummary
from osdagbridge.core.reports.theme import ChartTheme, Theme

UNIT_TONNE = "MT"
UNIT_VOLUME = "m$^{3}$"          # mathtext superscript

STEEL_TITLE = "Structural Steel Tonnage"
STEEL_AXIS_LABEL = f"Steel Weight ({UNIT_TONNE})"
CONCRETE_TITLE = "Concrete Volume"
CONCRETE_AXIS_LABEL = f"Volume ({UNIT_VOLUME})"
REBAR_TITLE = "Reinforcement Steel Weight"
REBAR_AXIS_LABEL = f"Weight ({UNIT_TONNE})"

LABEL_GIRDERS = "Plate Girders"
LABEL_BRACING = "Cross Bracing\n(top + bottom + diagonal)"
LABEL_DIAPHRAGMS = "End Diaphragms"
LABEL_STUDS = "Shear Studs"
LABEL_DECK = "Deck Slab"
LABEL_BARRIER = "Crash Barrier"
LABEL_REBAR = "Deck Slab Reinforcement"

# One category of a quantity chart: (axis label, value or None, bar colour)
Category = Tuple[str, Optional[float], str]


def format_quantity(value: float) -> str:
    """Two decimals, or three when the third one is significant (0.158 stays 0.158)."""
    text = f"{value:.3f}"
    return text[:-1] if text.endswith("0") else text


def steel_categories(summary: QuantitySummary, c: ChartTheme) -> List[Category]:
    """Plate girders, cross bracing and end diaphragms always; shear studs when the BOQ has them."""
    categories: List[Category] = [
        (LABEL_GIRDERS, summary.steel_girders_wt, c.element_girder),
        (LABEL_BRACING, summary.bracing_total_wt, c.element_bracing),
        (LABEL_DIAPHRAGMS, summary.end_diaphragm_wt, c.element_diaphragm),
    ]
    if summary.shear_studs_wt is not None:
        categories.append((LABEL_STUDS, summary.shear_studs_wt, c.element_studs))
    return categories


def concrete_categories(summary: QuantitySummary, c: ChartTheme) -> List[Category]:
    categories: List[Category] = [(LABEL_DECK, summary.concrete_deck_vol, c.concrete_color)]
    if summary.crash_barrier_vol is not None and summary.crash_barrier_vol > 0:
        categories.append((LABEL_BARRIER, summary.crash_barrier_vol, c.concrete_color))
    return categories


def rebar_categories(summary: QuantitySummary, c: ChartTheme) -> List[Category]:
    return [(LABEL_REBAR, summary.rebar_deck_wt, c.rebar_color)]


def _draw_quantity_panel(ax: Any, categories: Sequence[Category], unit: str, c: ChartTheme,
                         title: str, axis_label: str) -> None:
    """One bar per category with its value and unit above it."""
    positions = [float(i) for i in range(len(categories))]
    drawn = [(p, cat) for p, cat in zip(positions, categories) if cat[1] is not None]

    bars = draw_bars(ax, [p for p, _cat in drawn], [float(cat[1]) for _p, cat in drawn],
                     [cat[2] for _p, cat in drawn], c, c.bar_width_quantity)
    for bar, (p, (label, value, _color)) in zip(bars, drawn):
        bar.set_gid("quantity:" + label.split("\n")[0])
        add_value_label(ax, p, float(value), f"{format_quantity(float(value))} {unit}", c)
    for p, (_label, value, _color) in zip(positions, categories):
        if value is None:
            add_missing_marker(ax, p, c)

    extra = max(0.0, (c.min_category_slots - len(categories)) / 2.0)
    ax.set_xlim(-0.5 - extra, len(categories) - 0.5 + extra)
    ax.set_ylim(0.0, value_limit(max((float(cat[1]) for _p, cat in drawn), default=0.0), c))
    ax.set_xticks(positions)
    ax.set_xticklabels([label for label, _value, _color in categories], fontsize=c.tick_label_size)
    set_value_axis_label(ax, axis_label, c)
    set_title(ax, title, c)


def build_steel_quantities_figure(
    summary: QuantitySummary,
    theme: Theme | None = None,
) -> Figure:
    """Structural steel tonnage by element."""
    t = resolve_theme(theme)
    with chart_style(t) as c:
        fig, ax = new_figure(c.figsize_steel, theme=t)
        apply_margins(fig, c.margins_quantity)
        _draw_quantity_panel(ax, steel_categories(summary, c), UNIT_TONNE, c,
                             STEEL_TITLE, STEEL_AXIS_LABEL)
    return fig


def build_concrete_vs_rebar_figure(
    summary: QuantitySummary,
    theme: Theme | None = None,
) -> Figure:
    """Concrete volume and reinforcement weight as two panels, each with its own axis and unit."""
    t = resolve_theme(theme)
    with chart_style(t) as c:
        fig, (ax_concrete, ax_rebar) = new_figure(c.figsize_quantity, theme=t, ncols=2)
        apply_margins(fig, c.margins_quantity)
        _draw_quantity_panel(ax_concrete, concrete_categories(summary, c), UNIT_VOLUME, c,
                             CONCRETE_TITLE, CONCRETE_AXIS_LABEL)
        _draw_quantity_panel(ax_rebar, rebar_categories(summary, c), UNIT_TONNE, c,
                             REBAR_TITLE, REBAR_AXIS_LABEL)
    return fig


def plot_steel_quantities(
    summary: QuantitySummary,
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Save the structural steel tonnage chart and return the image path."""
    fig = build_steel_quantities_figure(summary, theme=theme)
    return save_chart(fig, output_path, theme=theme)


def plot_concrete_vs_rebar(
    summary: QuantitySummary,
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Save the concrete volume / reinforcement weight chart and return the image path."""
    fig = build_concrete_vs_rebar_figure(summary, theme=theme)
    return save_chart(fig, output_path, theme=theme)
