"""Headless Matplotlib chart generation for OsdagBridge LaTeX reports.

Generates Section 5.5 Utilization Ratio (UR) summary charts and Chapter 7
Material Take-off breakdown charts using headless Figure and FigureCanvasAgg.
Does not import pyplot or touch global matplotlib state, ensuring complete
isolation from the PySide6 Qt GUI.
"""

import os
from typing import Dict, List, Optional, Sequence, Tuple
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from osdagbridge.core.reports.styles import DEFAULT_THEME, ReportTheme


def generate_ur_chart(
    items: Sequence[Tuple[str, Optional[float]]],
    output_path: str,
    theme: ReportTheme = DEFAULT_THEME,
) -> str:
    """Generate Section 5.5 Utilization Ratio (UR) summary bar chart.

    Renders green bars for passing checks (UR <= 1.0), hatched red bars for failing
    checks (UR > 1.0), and labeled gray indicators for uncalculated checks.
    Includes a distinct dashed red limit line at UR = 1.0.
    """
    labels = [it[0] for it in items]
    raw_values = [it[1] for it in items]

    fig = Figure(figsize=(7.5, 3.2), dpi=theme.chart_dpi)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    y_pos = list(range(len(labels)))
    bar_height = 0.52

    plot_values = []
    colors = []
    hatches = []

    for val in raw_values:
        if val is None or val < 0.0:
            plot_values.append(0.05)
            colors.append("#CBD5E1")
            hatches.append("")
        elif val <= 1.0:
            plot_values.append(val)
            colors.append(theme.osdag_green)
            hatches.append("")
        else:
            plot_values.append(val)
            colors.append(theme.fail_color)
            hatches.append("///")

    bars = ax.barh(y_pos, plot_values, height=bar_height, color=colors, edgecolor=theme.border, linewidth=0.8)

    for bar, hatch in zip(bars, hatches):
        if hatch:
            bar.set_hatch(hatch)

    # Dashed red vertical limit line at UR = 1.0
    ax.axvline(1.0, color=theme.fail_color, linestyle="--", linewidth=1.4, alpha=0.9, label="Design Limit (UR = 1.0)")

    # Data value callouts at bar ends
    max_val = max([v for v in plot_values if v is not None] + [1.2])
    x_limit = max(max_val * 1.18, 1.25)
    ax.set_xlim(0.0, x_limit)

    for idx, (val, plot_val) in enumerate(zip(raw_values, plot_values)):
        if val is None or val < 0.0:
            label_text = "N/A"
            color_text = theme.muted
        else:
            status_text = "SAFE" if val <= 1.0 else "UNSAFE"
            label_text = f"{val:.2f} ({status_text})"
            color_text = theme.osdag_green if val <= 1.0 else theme.fail_color

        ax.text(
            plot_val + 0.03,
            idx,
            label_text,
            va="center",
            ha="left",
            fontsize=8.5,
            fontweight="bold",
            color=color_text,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9.0, fontweight="medium")
    ax.invert_yaxis()  # Highest priority item at top
    ax.set_xlabel("Utilization Ratio (Demand / Capacity)", fontsize=9.0, fontweight="medium", color=theme.primary)
    ax.set_title("Overall Component Design Check Summary (Governing UR)", fontsize=10.0, fontweight="bold", color=theme.primary, pad=10)

    ax.grid(axis="x", linestyle=":", alpha=0.6, color=theme.border)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(theme.border)
    ax.spines["bottom"].set_color(theme.border)

    ax.legend(loc="lower right", frameon=True, framealpha=0.9, facecolor="#FFFFFF", edgecolor=theme.border, fontsize=8.0)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.print_figure(output_path, dpi=theme.chart_dpi)
    return output_path


def generate_material_takeoff_charts(
    steel_by_component: Dict[str, float],
    concrete_m3: float,
    rebar_mt: float,
    output_dir: str,
    theme: ReportTheme = DEFAULT_THEME,
) -> Tuple[str, str]:
    """Generate Chapter 7 Material Take-off breakdown charts.

    Chart 1: Structural steel tonnage breakdown bar chart by component.
    Chart 2: Side-by-side subplots comparing Concrete Volume and Rebar Weight
             with rebar intensity (kg/m3) callout.
    """
    os.makedirs(output_dir, exist_ok=True)
    chart1_path = os.path.join(output_dir, "material_steel_breakdown.png")
    chart2_path = os.path.join(output_dir, "material_concrete_rebar.png")

    # ── Chart 1: Structural Steel Breakdown ──
    fig1 = Figure(figsize=(6.8, 3.2), dpi=theme.chart_dpi)
    canvas1 = FigureCanvasAgg(fig1)
    ax1 = fig1.add_subplot(111)

    labels = list(steel_by_component.keys())
    weights = [float(steel_by_component[k]) for k in labels]
    total_steel = sum(weights)

    palette = [theme.primary, theme.accent, theme.osdag_green, "#0284C7", "#38BDF8"]
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    bars = ax1.bar(labels, weights, width=0.45, color=colors, edgecolor=theme.border, linewidth=0.8)

    y_max = max(weights + [1.0]) * 1.22
    ax1.set_ylim(0.0, y_max)
    ax1.set_ylabel("Weight (Metric Tonnes)", fontsize=8.5, fontweight="medium", color=theme.primary)
    ax1.set_title(f"Structural Steel Breakdown by Component (Total = {total_steel:.2f} MT)", fontsize=9.5, fontweight="bold", color=theme.primary, pad=10)

    for bar, wt in zip(bars, weights):
        pct = (wt / total_steel * 100.0) if total_steel > 0 else 0.0
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + y_max * 0.02,
            f"{wt:.2f} MT\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8.0,
            fontweight="bold",
            color=theme.primary,
        )

    ax1.grid(axis="y", linestyle=":", alpha=0.6, color=theme.border)
    ax1.set_axisbelow(True)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(theme.border)
    ax1.spines["bottom"].set_color(theme.border)
    ax1.tick_params(axis="x", labelsize=8.5)

    fig1.tight_layout()
    canvas1.print_figure(chart1_path, dpi=theme.chart_dpi)

    # ── Chart 2: Concrete Volume vs Rebar Weight ──
    fig2 = Figure(figsize=(6.8, 3.2), dpi=theme.chart_dpi)
    canvas2 = FigureCanvasAgg(fig2)

    ax_c = fig2.add_subplot(121)
    ax_r = fig2.add_subplot(122)

    # Concrete subplot
    bar_c = ax_c.bar(["Deck Concrete"], [concrete_m3], width=0.4, color=theme.osdag_green, edgecolor=theme.border)
    ax_c.set_ylabel("Volume (m³)", fontsize=8.5, fontweight="medium", color=theme.primary)
    ax_c.set_ylim(0.0, max(concrete_m3 * 1.25, 1.0))
    ax_c.text(
        bar_c[0].get_x() + bar_c[0].get_width() / 2.0,
        concrete_m3 + max(concrete_m3 * 0.03, 0.05),
        f"{concrete_m3:.2f} m³",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#587114",
    )
    ax_c.set_title("Concrete Volume", fontsize=9.0, fontweight="bold", color=theme.primary)
    ax_c.grid(axis="y", linestyle=":", alpha=0.6, color=theme.border)
    ax_c.spines["top"].set_visible(False)
    ax_c.spines["right"].set_visible(False)
    ax_c.tick_params(axis="x", labelsize=8.5)

    # Rebar subplot
    bar_r = ax_r.bar(["Rebar Steel"], [rebar_mt], width=0.4, color="#D97706", edgecolor=theme.border)
    ax_r.set_ylabel("Weight (Metric Tonnes)", fontsize=8.5, fontweight="medium", color=theme.primary)
    ax_r.set_ylim(0.0, max(rebar_mt * 1.25, 0.5))
    ax_r.text(
        bar_r[0].get_x() + bar_r[0].get_width() / 2.0,
        rebar_mt + max(rebar_mt * 0.03, 0.02),
        f"{rebar_mt:.2f} MT",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#B45309",
    )
    ax_r.set_title("Reinforcement Steel", fontsize=9.0, fontweight="bold", color=theme.primary)
    ax_r.grid(axis="y", linestyle=":", alpha=0.6, color=theme.border)
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["right"].set_visible(False)
    ax_r.tick_params(axis="x", labelsize=8.5)

    # Steel intensity annotation
    rebar_intensity = (rebar_mt * 1000.0 / concrete_m3) if concrete_m3 > 0 else 0.0
    fig2.suptitle(
        f"Deck Superstructure Material Quantities (Rebar Intensity: {rebar_intensity:.1f} kg/m³)",
        fontsize=9.5,
        fontweight="bold",
        color=theme.primary,
        y=0.98,
    )

    fig2.tight_layout()
    canvas2.print_figure(chart2_path, dpi=theme.chart_dpi)

    return chart1_path, chart2_path
