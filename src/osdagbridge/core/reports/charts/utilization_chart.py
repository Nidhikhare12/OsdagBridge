"""Utilization Ratio summary bar charts with threshold line (Requirement R4)."""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import matplotlib.pyplot as plt

from osdagbridge.core.reports.data.utilization import URRecord, GirderURRecord
from osdagbridge.core.reports.charts.base import setup_figure, save_chart
from osdagbridge.core.reports.theme import get_active_theme, Theme


def plot_overall_utilization(
    records: List[URRecord],
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Generate overall utilization ratio bar chart grouped by structural element (Requirement R4)."""
    t = theme or get_active_theme()
    c = t.chart
    pal = t.palette

    # Filter records that have evaluated numeric URs
    plottable = [r for r in records if r.ur is not None and r.ur > 0.0]
    if not plottable:
        return None

    fig, ax = setup_figure(figsize=c.figsize_overall, dpi=c.dpi, theme=t)

    # Element color map
    element_colors = {
        "Girder": f"#{pal.brand}",
        "Deck Slab": "#339AF0",        # Distinct Blue
        "Cross Bracing": "#FCC419",     # Distinct Amber/Yellow
        "End Diaphragm": "#845EF7",     # Distinct Purple
    }

    labels = []
    values = []
    bar_colors = []
    hatches = []

    for r in plottable:
        # Shorten check label for horizontal axis readability
        short_label = r.check_name.replace("Girder --- ", "").replace("Deck --- ", "").replace("Cross Bracing --- ", "CB ").replace("End Diaphragm --- ", "ED ")
        labels.append(short_label)
        values.append(r.ur)

        if r.ur > 1.0:
            bar_colors.append(c.bar_fail)
            hatches.append("//")
        else:
            base_col = element_colors.get(r.element, f"#{pal.brand}")
            bar_colors.append(base_col)
            hatches.append("")

    x_indices = range(len(plottable))
    bars = ax.bar(x_indices, values, color=bar_colors, edgecolor="#212529", linewidth=0.8, width=0.62)

    # Apply hatching for failing checks
    for bar, hatch in zip(bars, hatches):
        if hatch:
            bar.set_hatch(hatch)

    # Add red dashed threshold line at UR = 1.0
    thresh_line = ax.axhline(
        y=1.0,
        color=c.threshold_color,
        linestyle=c.threshold_style,
        linewidth=1.8,
        label="UR = 1.0 limit",
        zorder=5,
    )

    # Value labels on top of each bar
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(
            f"{val:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=c.label_size,
            fontweight="bold",
        )

    max_ur = max(values) if values else 1.0
    ax.set_ylim(0, max(1.25, max_ur * 1.18))
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontweight="bold")
    ax.set_xticks(list(x_indices))
    ax.set_xticklabels(labels, rotation=42, ha="right", fontsize=9)
    ax.set_title("Overall Design Check Summary --- Utilization Ratios", pad=12)

    # Custom legend for element groups and threshold limit
    legend_handles = [thresh_line]
    legend_labels = ["UR = 1.0 limit"]

    for elem, col in element_colors.items():
        if any(r.element == elem for r in plottable):
            legend_handles.append(plt.Rectangle((0, 0), 1, 1, color=col, ec="#212529", lw=0.8))
            legend_labels.append(elem)

    ax.legend(
        legend_handles,
        legend_labels,
        loc="upper right",
        framealpha=0.9,
        edgecolor="#cccccc",
        fontsize=9,
    )

    return save_chart(fig, output_path, dpi=c.dpi)


def plot_girder_utilization(
    girder_records: List[GirderURRecord],
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Generate governing utilization ratio bar chart per plate girder (Requirement R4)."""
    t = theme or get_active_theme()
    c = t.chart
    pal = t.palette

    if not girder_records:
        return None

    fig, ax = setup_figure(figsize=(7.5, 4.0), dpi=c.dpi, theme=t)

    labels = [g.girder_label for g in girder_records]
    values = [g.ur for g in girder_records]
    bar_colors = [c.bar_fail if ur > 1.0 else f"#{pal.brand}" for ur in values]
    hatches = ["//" if ur > 1.0 else "" for ur in values]

    x_indices = range(len(girder_records))
    bars = ax.bar(x_indices, values, color=bar_colors, edgecolor="#212529", linewidth=0.8, width=0.5)

    for bar, hatch in zip(bars, hatches):
        if hatch:
            bar.set_hatch(hatch)

    ax.axhline(
        y=1.0,
        color=c.threshold_color,
        linestyle=c.threshold_style,
        linewidth=1.8,
        label="UR = 1.0 limit",
        zorder=5,
    )

    for bar, val, g in zip(bars, values, girder_records):
        height = bar.get_height()
        ax.annotate(
            f"{val:.2f}\n({g.governing_check})",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    max_ur = max(values) if values else 1.0
    ax.set_ylim(0, max(1.25, max_ur * 1.25))
    ax.set_ylabel("Governing Utilization Ratio", fontweight="bold")
    ax.set_xticks(list(x_indices))
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_title("Plate Girder Governing Utilization Ratios", pad=12)
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="#cccccc")

    return save_chart(fig, output_path, dpi=c.dpi)
