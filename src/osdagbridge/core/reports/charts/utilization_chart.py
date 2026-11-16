"""Utilization Ratio bar charts for Section 5.5 (Requirement R4).

Both charts plot exactly the records produced by ``data/utilization.py``:
the same objects that fill the Section 5.5 table. A record without a UR is
drawn as an explicit "Not computed" marker, never as a bar.

``build_*_figure`` returns the matplotlib Figure (for inspection in tests);
``plot_*`` builds, saves and returns the path of the image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from osdagbridge.core.reports.charts.base import (
    LIMIT_LABEL,
    NOT_APPLICABLE_TEXT,
    NOT_COMPUTED_TEXT,
    add_legend_below,
    add_limit_line,
    apply_margins,
    add_missing_marker,
    add_value_label,
    chart_style,
    depth_below_axes_pt,
    display_text,
    draw_bars,
    fail_swatch,
    missing_swatch,
    new_figure,
    points_to_axes_y,
    resolve_theme,
    save_chart,
    set_title,
    set_value_axis_label,
    slot_width_in,
    style_axes,
    swatch,
    value_limit,
    wrap_label,
)
from osdagbridge.core.reports.data.utilization import GirderURRecord, URRecord
from osdagbridge.core.reports.theme import ChartTheme, Theme

UR_LIMIT = 1.0
UR_AXIS_LABEL = "Utilization Ratio (Demand / Capacity)"
GIRDER_AXIS_LABEL = "Governing Utilization Ratio (Demand / Capacity)"
GIRDER_AXIS_LABEL_WRAPPED = "Governing Utilization Ratio\n(Demand / Capacity)"
OVERALL_TITLE = "Overall Design Check Summary -- Utilization Ratios"
GIRDER_TITLE = "Governing Utilization Ratio per Plate Girder"
GOVERNING_CHECK_HEADER = "Governing check"
PASS_LABEL = "UR ≤ 1.0 (pass)"
FAIL_LABEL = "UR > 1.0 (fail)"

GID_GROUP_LABEL = "element-group-label"
GID_GROUP_BRACKET = "element-group-bracket"
GID_GOVERNING_CHECK = "governing-check-label"

# (record.element, title printed under the x axis, ChartTheme colour field)
ELEMENT_GROUPS: Tuple[Tuple[str, str, str], ...] = (
    ("Girder", "Steel Plate Girders", "element_girder"),
    ("Deck Slab", "Concrete Deck Slab", "element_deck"),
    ("Cross Bracing", "Cross Bracing", "element_bracing"),
    ("End Diaphragm", "End Diaphragms", "element_diaphragm"),
)


def format_ur(ur: float) -> str:
    """UR text: the same two-decimal format as the Section 5.5 table."""
    return f"{ur:.2f}"


def is_failing(ur: Optional[float]) -> bool:
    return ur is not None and ur > UR_LIMIT


def element_color(c: ChartTheme, element: str) -> str:
    """Theme colour of a structural element (neutral for an unknown element)."""
    for key, _title, attr in ELEMENT_GROUPS:
        if key == element:
            return getattr(c, attr)
    return c.bar_neutral


def group_records(records: Sequence[URRecord]) -> List[Tuple[str, str, List[URRecord]]]:
    """Group records by element in the task order; record order inside a group is kept."""
    groups: List[Tuple[str, str, List[URRecord]]] = []
    known = [key for key, _t, _a in ELEMENT_GROUPS]
    for key, title, _attr in ELEMENT_GROUPS:
        members = [r for r in records if r.element == key]
        if members:
            groups.append((key, title, members))
    for r in records:
        if r.element not in known:
            for key, _title, members in groups:
                if key == r.element:
                    members.append(r)
                    break
            else:
                groups.append((r.element, display_text(r.element), [r]))
    return groups


def short_check_label(record: URRecord) -> str:
    """Tick label of a check: the element prefix is dropped (the group label carries it)."""
    return display_text(str(record.check_name).split(" --- ")[-1])


def _missing_text(record: URRecord) -> str:
    if record.status == "N/A" and not record.note:
        return NOT_APPLICABLE_TEXT
    return NOT_COMPUTED_TEXT


def _limit_handle(c: ChartTheme) -> Line2D:
    return Line2D([0], [0], color=c.threshold_color, linestyle=c.threshold_style,
                  linewidth=c.threshold_width, label=LIMIT_LABEL)


def build_overall_utilization_figure(
    records: Sequence[URRecord],
    theme: Theme | None = None,
) -> Optional[Figure]:
    """One bar per design check, grouped under the four structural elements."""
    if not records:
        return None
    t = resolve_theme(theme)
    groups = group_records(records)

    with chart_style(t) as c:
        fig, ax = new_figure(c.figsize_overall, theme=t)
        apply_margins(fig, c.margins_overall)

        positions: List[float] = []
        spans: List[Tuple[str, float, float]] = []   # (title, first position, last position)
        ordered: List[URRecord] = []
        x = 0.0
        for index, (_key, title, members) in enumerate(groups):
            if index:
                x += c.group_gap
            first = x
            for r in members:
                positions.append(x)
                ordered.append(r)
                x += 1.0
            spans.append((title, first, x - 1.0))

        plotted = [(p, r) for p, r in zip(positions, ordered) if r.ur is not None]
        missing = [(p, r) for p, r in zip(positions, ordered) if r.ur is None]

        bar_positions = [p for p, _r in plotted]
        values = [float(r.ur) for _p, r in plotted]
        colors = [element_color(c, r.element) for _p, r in plotted]
        failing = [is_failing(r.ur) for _p, r in plotted]

        bars = draw_bars(ax, bar_positions, values, colors, c, c.bar_width, failing=failing)
        for bar, (_p, r) in zip(bars, plotted):
            bar.set_gid(f"ur:{r.check_name}")
        for p, r in plotted:
            add_value_label(ax, p, float(r.ur), format_ur(r.ur), c)
        for p, r in missing:
            add_missing_marker(ax, p, c, text=_missing_text(r), rotation=90.0)

        add_limit_line(ax, c)

        ax.set_xlim(positions[0] - 0.5 - c.bar_width / 2, positions[-1] + 0.5 + c.bar_width / 2)
        ax.set_ylim(0.0, value_limit(max(values, default=0.0), c, floor=UR_LIMIT))
        set_value_axis_label(ax, UR_AXIS_LABEL, c)
        set_title(ax, OVERALL_TITLE, c)

        ax.set_xticks(positions)
        ax.set_xticklabels([short_check_label(r) for r in ordered], rotation=c.tick_rotation,
                           ha="right", rotation_mode="anchor", fontsize=c.tick_label_size)

        # Element brackets and names under the tick labels
        depth = depth_below_axes_pt(ax, ax.get_xticklabels())
        y_line = -points_to_axes_y(ax, depth + c.group_bracket_pad_pt)
        y_tick = y_line + points_to_axes_y(ax, c.group_bracket_tick_pt)
        y_text = y_line - points_to_axes_y(ax, c.label_offset_pt + c.group_label_size)
        slot_in = slot_width_in(ax)
        group_labels = []
        for title, first, last in spans:
            x0, x1 = first - c.bar_width / 2, last + c.bar_width / 2
            bracket = Line2D([x0, x0, x1, x1], [y_tick, y_line, y_line, y_tick],
                             transform=ax.get_xaxis_transform(), color=c.group_bracket_color,
                             linewidth=c.group_bracket_width, clip_on=False)
            bracket.set_gid(GID_GROUP_BRACKET)
            ax.add_artist(bracket)
            width_in = (last - first + 1.0 + c.group_gap) * slot_in
            label = ax.text((x0 + x1) / 2, y_text, wrap_label(title, width_in, c.group_label_size),
                            transform=ax.get_xaxis_transform(), ha="center", va="baseline",
                            fontsize=c.group_label_size, fontweight=c.axis_label_weight,
                            color=c.text_color, clip_on=False, linespacing=1.1)
            label.set_gid(GID_GROUP_LABEL)
            group_labels.append(label)

        handles: List[Any] = [
            swatch(element_color(c, key), c, title) for key, title, _members in groups
        ]
        handles.append(fail_swatch(c, FAIL_LABEL))
        handles.append(_limit_handle(c))
        if missing:
            kinds = sorted({_missing_text(r) for _p, r in missing})
            handles.append(missing_swatch(c, " / ".join(kinds)))
        add_legend_below(ax, handles, c, depth_below_axes_pt(ax, group_labels), ncol=len(groups))
    return fig


def _build_girder_vertical(girder_records: Sequence[GirderURRecord], t: Theme, c: ChartTheme) -> Figure:
    n = len(girder_records)
    fig, ax = new_figure(c.figsize_girder, theme=t)
    apply_margins(fig, c.margins_girder)

    positions = [float(i) for i in range(n)]
    values = [float(g.ur) for g in girder_records]
    failing = [is_failing(v) for v in values]
    bars = draw_bars(ax, positions, values, [c.element_girder] * n, c, c.bar_width_girder, failing=failing)
    for bar, g, p, v in zip(bars, girder_records, positions, values):
        bar.set_gid(f"girder:{g.girder_label}")
        add_value_label(ax, p, v, format_ur(v), c)

    add_limit_line(ax, c)
    ax.set_xlim(-0.5 - c.bar_width_girder / 2, n - 0.5 + c.bar_width_girder / 2)
    ax.set_ylim(0.0, value_limit(max(values, default=0.0), c, floor=UR_LIMIT))
    set_value_axis_label(ax, GIRDER_AXIS_LABEL_WRAPPED, c)
    set_title(ax, GIRDER_TITLE, c)
    ax.set_xticks(positions)
    ax.set_xticklabels([display_text(g.girder_label) for g in girder_records],
                       fontsize=c.axis_label_size, fontweight=c.axis_label_weight)

    # Governing check wrapped under each girder name, inside that girder's own slot
    depth = depth_below_axes_pt(ax, ax.get_xticklabels())
    y_text = -points_to_axes_y(ax, depth + c.label_offset_pt + c.annotation_size)
    slot_in = slot_width_in(ax)
    check_labels = []
    for p, g in zip(positions, girder_records):
        text = wrap_label(display_text(g.governing_check), slot_in * c.label_fill, c.annotation_size)
        label = ax.text(p, y_text, text, transform=ax.get_xaxis_transform(), ha="center", va="baseline",
                        fontsize=c.annotation_size, color=c.muted_text_color, clip_on=False,
                        linespacing=1.15)
        label.set_gid(GID_GOVERNING_CHECK)
        check_labels.append(label)

    handles = [swatch(c.element_girder, c, PASS_LABEL), fail_swatch(c, FAIL_LABEL), _limit_handle(c)]
    add_legend_below(ax, handles, c, depth_below_axes_pt(ax, check_labels))
    return fig


def _build_girder_horizontal(girder_records: Sequence[GirderURRecord], t: Theme, c: ChartTheme) -> Figure:
    n = len(girder_records)
    width, base_height = c.figsize_girder_horizontal
    fig, ax = new_figure((width, base_height + n * c.girder_row_height_in), theme=t)
    style_axes(ax, c, value_axis="x")
    apply_margins(fig, c.margins_girder_horizontal)

    positions = [float(i) for i in range(n)]
    values = [float(g.ur) for g in girder_records]
    failing = [is_failing(v) for v in values]
    bars = draw_bars(ax, positions, values, [c.element_girder] * n, c, c.bar_width_girder,
                     failing=failing, horizontal=True)
    for bar, g, p, v in zip(bars, girder_records, positions, values):
        bar.set_gid(f"girder:{g.girder_label}")
        add_value_label(ax, p, v, format_ur(v), c, horizontal=True)

    add_limit_line(ax, c, horizontal=True)
    ax.set_ylim(n - 0.5 + c.bar_width_girder / 2, -0.5 - c.bar_width_girder / 2)   # first girder on top
    ax.set_xlim(0.0, value_limit(max(values, default=0.0), c, floor=UR_LIMIT))
    set_value_axis_label(ax, GIRDER_AXIS_LABEL, c, horizontal=True)
    set_title(ax, GIRDER_TITLE, c)
    ax.set_yticks(positions)
    ax.set_yticklabels([display_text(g.girder_label) for g in girder_records],
                       fontsize=c.tick_label_size, fontweight=c.axis_label_weight)

    # Governing check in its own column to the right of the plot area
    column = dict(xytext=(c.legend_pad_pt, 0), textcoords="offset points", ha="left",
                  annotation_clip=False)
    header = ax.annotate(GOVERNING_CHECK_HEADER, xy=(1.0, 1.0), xycoords="axes fraction", va="bottom",
                         fontsize=c.annotation_size, fontweight=c.axis_label_weight,
                         color=c.text_color, **column)
    header.set_gid(GID_GOVERNING_CHECK + "-header")
    for p, g in zip(positions, girder_records):
        label = ax.annotate(display_text(g.governing_check), xy=(1.0, p),
                            xycoords=ax.get_yaxis_transform(), va="center",
                            fontsize=c.annotation_size, color=c.muted_text_color, **column)
        label.set_gid(GID_GOVERNING_CHECK)

    handles = [swatch(c.element_girder, c, PASS_LABEL), fail_swatch(c, FAIL_LABEL), _limit_handle(c)]
    add_legend_below(ax, handles, c, depth_below_axes_pt(ax, [ax.xaxis.label]))
    return fig


def build_girder_utilization_figure(
    girder_records: Sequence[GirderURRecord],
    theme: Theme | None = None,
) -> Optional[Figure]:
    """Governing UR of every plate girder; horizontal bars above ``horizontal_above`` girders."""
    if not girder_records:
        return None
    t = resolve_theme(theme)
    with chart_style(t) as c:
        if len(girder_records) > c.horizontal_above:
            return _build_girder_horizontal(girder_records, t, c)
        return _build_girder_vertical(girder_records, t, c)


def plot_overall_utilization(
    records: List[URRecord],
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Save the overall utilization chart; returns the image path, or None when there are no records."""
    fig = build_overall_utilization_figure(records, theme=theme)
    if fig is None:
        return None
    return save_chart(fig, output_path, theme=theme)


def plot_girder_utilization(
    girder_records: List[GirderURRecord],
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Save the per-girder governing utilization chart; returns the image path, or None without girders."""
    fig = build_girder_utilization_figure(girder_records, theme=theme)
    if fig is None:
        return None
    return save_chart(fig, output_path, theme=theme)
