"""Material quantity bar charts for structural steel and concrete vs rebar (Requirement R5)."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt

from osdagbridge.core.reports.theme import get_active_theme, Theme
from osdagbridge.core.reports.charts.base import setup_figure, save_chart
from osdagbridge.core.reports.data.quantities import QuantitySummary


def plot_steel_quantities(
    summary: QuantitySummary,
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Generate structural steel tonnage breakdown bar chart (Requirement R5)."""
    t = theme or get_active_theme()
    c = t.chart
    pal = t.palette

    fig, ax = setup_figure(figsize=(8.0, 4.2), dpi=c.dpi, theme=t)

    # Categories to plot
    categories = []
    values = []
    colors = []

    # 1. Plate Girders
    if summary.steel_girders_wt is not None:
        categories.append("Plate Girders")
        values.append(summary.steel_girders_wt)
        colors.append(f"#{pal.brand}")

    # 2. Cross Bracing (Total)
    if summary.bracing_total_wt is not None:
        categories.append("Cross Bracing\n(Top+Bot+Diag)")
        values.append(summary.bracing_total_wt)
        colors.append("#FCC419")  # Amber / Warm Yellow

    # 3. End Diaphragms
    categories.append("End Diaphragm\n(Pending)")
    values.append(summary.end_diaphragm_wt or 0.0)
    colors.append("#CED4DA")  # Light gray

    # 4. Shear Studs
    if summary.shear_studs_wt is not None:
        categories.append("Shear Studs")
        values.append(summary.shear_studs_wt)
        colors.append("#20C997")  # Teal

    x_indices = range(len(categories))
    bars = ax.bar(x_indices, values, color=colors, edgecolor="#212529", linewidth=0.8, width=0.52)

    # Add annotations and handle the "Not computed" case for End Diaphragm
    for i, (bar, val, cat) in enumerate(zip(bars, values, categories)):
        height = bar.get_height()
        if "End Diaphragm" in cat and summary.end_diaphragm_wt is None:
            bar.set_hatch("//")
            bar.set_edgecolor("#868E96")
            ax.annotate(
                "Not computed\n(U8 pending)",
                xy=(bar.get_x() + bar.get_width() / 2, 0.2),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontstyle="italic",
                color="#495057",
            )
        else:
            ax.annotate(
                f"{val:.2f} MT",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    max_v = max(values) if values else 10.0
    ax.set_ylim(0, max(1.0, max_v * 1.18))
    ax.set_ylabel("Weight (Metric Tonnes --- MT)", fontweight="bold")
    ax.set_xticks(list(x_indices))
    ax.set_xticklabels(categories, fontsize=9.5)
    ax.set_title("Structural Steel Tonnage Breakdown", pad=12)

    return save_chart(fig, output_path, dpi=c.dpi)


def plot_concrete_vs_rebar(
    summary: QuantitySummary,
    output_path: str | Path,
    theme: Theme | None = None,
) -> Optional[str]:
    """Generate side-by-side bar charts for concrete volume (m³) and rebar weight (MT) (Requirement R5)."""
    t = theme or get_active_theme()
    c = t.chart
    pal = t.palette

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 4.2), dpi=c.dpi)
    plt.subplots_adjust(wspace=0.32)

    # Apply base styling
    for ax in (ax1, ax2):
        ax.grid(True, linestyle=":", alpha=c.grid_alpha)
        ax.set_axisbelow(True)

    # Left panel: Concrete Volume (m³)
    conc_cats = []
    conc_vals = []
    if summary.concrete_deck_vol is not None:
        conc_cats.append("Deck Slab")
        conc_vals.append(summary.concrete_deck_vol)
    if summary.crash_barrier_vol is not None and summary.crash_barrier_vol > 0:
        conc_cats.append("Crash Barrier")
        conc_vals.append(summary.crash_barrier_vol)
    if not conc_cats:
        conc_cats.append("Deck Slab")
        conc_vals.append(0.0)

    x1 = range(len(conc_cats))
    b1 = ax1.bar(x1, conc_vals, color="#495057", edgecolor="#212529", linewidth=0.8, width=0.45)
    for bar, val in zip(b1, conc_vals):
        ax1.annotate(
            f"{val:.2f} m³",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    ax1.set_ylim(0, max(1.0, max(conc_vals) * 1.18))
    ax1.set_ylabel("Volume (m³)", fontweight="bold")
    ax1.set_xticks(list(x1))
    ax1.set_xticklabels(conc_cats, fontsize=9.5)
    ax1.set_title("Concrete Volume (M40)", pad=10, fontweight="bold")

    # Right panel: Reinforcement Steel Weight (MT)
    rebar_cats = []
    rebar_vals = []
    if summary.rebar_deck_wt is not None:
        rebar_cats.append("Deck Rebar\n(Fe 500)")
        rebar_vals.append(summary.rebar_deck_wt)
    if not rebar_cats:
        rebar_cats.append("Deck Rebar")
        rebar_vals.append(0.0)

    x2 = range(len(rebar_cats))
    b2 = ax2.bar(x2, rebar_vals, color="#1971C2", edgecolor="#212529", linewidth=0.8, width=0.45)
    for bar, val in zip(b2, rebar_vals):
        ax2.annotate(
            f"{val:.2f} MT",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    ax2.set_ylim(0, max(1.0, max(rebar_vals) * 1.18))
    ax2.set_ylabel("Weight (Metric Tonnes --- MT)", fontweight="bold")
    ax2.set_xticks(list(x2))
    ax2.set_xticklabels(rebar_cats, fontsize=9.5)
    ax2.set_title("Reinforcement Steel Weight", pad=10, fontweight="bold")

    return save_chart(fig, output_path, dpi=c.dpi)
