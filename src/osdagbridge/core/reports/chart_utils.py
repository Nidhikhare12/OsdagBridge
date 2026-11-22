"""
OsdagBridge Report Generator — Chart & Data Visualization Utilities
Programmatic generation of Utilization Ratio (Demand/Capacity) and
Material Take-Off charts for insertion into the design calculation report.
"""

import os
import tempfile
from typing import Dict, Tuple, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for report compilation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .styles import (
    COLOR_PASS_GREEN,
    COLOR_FAIL_RED,
    COLOR_STEEL_GIRDER,
    COLOR_STEEL_BRACING,
    COLOR_STEEL_DIAPHRAGM,
    COLOR_CONCRETE,
    COLOR_REBAR,
    CHART_CONFIG,
)


def generate_ur_summary_chart(ur_dict: Dict[str, float], output_dir: Optional[str] = None) -> str:
    """
    Generate an Overall Utilization Ratio (UR = Demand / Capacity) summary bar chart.
    Primary components included:
      - Steel Plate Girders
      - Concrete Deck Slab
      - Cross Bracing
      - End Diaphragms
    
    Includes a distinct red dashed horizontal reference line at UR = 1.0 to visually
    distinguish passing checks (UR <= 1.0) vs failing checks (UR > 1.0).
    """
    # Clean keys and filter valid floats
    labels = []
    values = []
    colors = []

    for name, val in ur_dict.items():
        if val is None or val == "" or str(val).strip() in ("---", "N/A", "N.A."):
            continue
        try:
            fval = float(val)
        except (ValueError, TypeError):
            continue
        labels.append(name)
        values.append(fval)
        # Color coding: Green if safe, Red if over limit
        if fval <= CHART_CONFIG["ur_limit"]:
            colors.append(COLOR_PASS_GREEN)
        else:
            colors.append(COLOR_FAIL_RED)

    if not values:
        # Fallback dummy display if no data
        labels = ["Plate Girders", "Deck Slab", "Cross Bracing", "End Diaphragms"]
        values = [0.0, 0.0, 0.0, 0.0]
        colors = [COLOR_PASS_GREEN] * 4

    fig, ax = plt.subplots(
        figsize=(CHART_CONFIG["fig_width"], CHART_CONFIG["fig_height"]),
        dpi=CHART_CONFIG["dpi"]
    )

    x_pos = range(len(labels))
    bars = ax.bar(
        x_pos,
        values,
        color=colors,
        width=CHART_CONFIG["bar_width"],
        edgecolor="#2D3748",
        linewidth=0.75,
        zorder=3
    )

    # Reference limit line at UR = 1.0 (Red dashed line)
    ax.axhline(
        y=CHART_CONFIG["ur_limit"],
        color=COLOR_FAIL_RED,
        linestyle="--",
        linewidth=1.8,
        label=f"Design Limit ($UR = {CHART_CONFIG['ur_limit']:.1f}$)",
        zorder=4
    )

    # Label values on top of each bar
    max_val = max(values) if values else 1.0
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(
            f"{val:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=CHART_CONFIG["tick_size"],
            fontweight="bold"
        )

    # Axis properties
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=CHART_CONFIG["tick_size"], rotation=0)
    ax.set_ylabel("Utilization Ratio ($UR = Demand / Capacity$)", fontsize=CHART_CONFIG["label_size"])
    ax.set_title("Overall Design Check Summary — Utilization Ratios", fontsize=CHART_CONFIG["title_size"], fontweight="bold", pad=12)
    ax.set_ylim(0, max(1.2, max_val * 1.22))
    ax.grid(axis="y", linestyle=":", alpha=CHART_CONFIG["grid_alpha"], zorder=0)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#718096")
    ax.spines["bottom"].set_color("#718096")

    # Legend
    pass_patch = mpatches.Patch(facecolor=COLOR_PASS_GREEN, edgecolor="#2D3748", label=r"Passing ($UR \leq 1.0$)")
    fail_patch = mpatches.Patch(facecolor=COLOR_FAIL_RED, edgecolor="#2D3748", label=r"Failing ($UR > 1.0$)")
    limit_line = plt.Line2D([0], [0], color=COLOR_FAIL_RED, linestyle="--", linewidth=1.8, label=r"Threshold ($UR = 1.0$)")
    ax.legend(handles=[pass_patch, fail_patch, limit_line], loc="upper right", fontsize=CHART_CONFIG["tick_size"], framealpha=0.9)

    plt.tight_layout()

    # Save image
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        img_path = os.path.join(output_dir, "ur_summary_chart.png")
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img_path = tmp.name
        tmp.close()

    fig.savefig(img_path, dpi=CHART_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return img_path


def generate_steel_tonnage_chart(steel_data: Dict[str, float], output_dir: Optional[str] = None) -> str:
    """
    Generate bar chart summarizing structural steel tonnage breakdown
    (Girders, Cross Bracing, End Diaphragms) in Metric Tons (MT).
    """
    labels = list(steel_data.keys())
    values = [float(v) if v not in (None, "") else 0.0 for v in steel_data.values()]
    colors = [COLOR_STEEL_GIRDER, COLOR_STEEL_BRACING, COLOR_STEEL_DIAPHRAGM][:len(labels)]
    while len(colors) < len(labels):
        colors.append(COLOR_STEEL_GIRDER)

    fig, ax = plt.subplots(
        figsize=(CHART_CONFIG["fig_width"], 3.4),
        dpi=CHART_CONFIG["dpi"]
    )

    x_pos = range(len(labels))
    bars = ax.bar(
        x_pos,
        values,
        color=colors,
        width=CHART_CONFIG["bar_width"],
        edgecolor="#2D3748",
        linewidth=0.75,
        zorder=3
    )

    max_val = max(values) if values else 1.0
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(
            f"{val:.2f} MT",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=CHART_CONFIG["tick_size"],
            fontweight="bold"
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=CHART_CONFIG["tick_size"])
    ax.set_ylabel("Weight (Metric Tons, MT)", fontsize=CHART_CONFIG["label_size"])
    ax.set_title("Structural Steel Tonnage Breakdown by Component", fontsize=CHART_CONFIG["title_size"], fontweight="bold", pad=10)
    ax.set_ylim(0, max_val * 1.25 if max_val > 0 else 10.0)
    ax.grid(axis="y", linestyle=":", alpha=CHART_CONFIG["grid_alpha"], zorder=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#718096")
    ax.spines["bottom"].set_color("#718096")

    plt.tight_layout()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        img_path = os.path.join(output_dir, "steel_tonnage_chart.png")
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img_path = tmp.name
        tmp.close()

    fig.savefig(img_path, dpi=CHART_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return img_path


def generate_concrete_vs_rebar_chart(concrete_vol_m3: float, rebar_wt_mt: float, output_dir: Optional[str] = None) -> str:
    """
    Generate bar chart comparing Concrete volume (m^3) vs Reinforcement Steel weight (MT).
    """
    categories = ["Concrete Volume ($m^3$)", "Reinforcement Steel (MT)"]
    values = [float(concrete_vol_m3), float(rebar_wt_mt)]
    colors = [COLOR_CONCRETE, COLOR_REBAR]

    fig, ax = plt.subplots(
        figsize=(CHART_CONFIG["fig_width"], 3.4),
        dpi=CHART_CONFIG["dpi"]
    )

    x_pos = range(len(categories))
    bars = ax.bar(
        x_pos,
        values,
        color=colors,
        width=0.4,
        edgecolor="#2D3748",
        linewidth=0.75,
        zorder=3
    )

    max_val = max(values) if values else 1.0
    units = ["m³", "MT"]
    for bar, val, u in zip(bars, values, units):
        height = bar.get_height()
        ax.annotate(
            f"{val:.2f} {u}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=CHART_CONFIG["tick_size"],
            fontweight="bold"
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=CHART_CONFIG["tick_size"], fontweight="bold")
    ax.set_ylabel("Quantity", fontsize=CHART_CONFIG["label_size"])
    ax.set_title("Deck Slab Materials: Concrete Volume vs. Reinforcement Steel Weight", fontsize=CHART_CONFIG["title_size"], fontweight="bold", pad=10)
    ax.set_ylim(0, max_val * 1.25 if max_val > 0 else 10.0)
    ax.grid(axis="y", linestyle=":", alpha=CHART_CONFIG["grid_alpha"], zorder=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#718096")
    ax.spines["bottom"].set_color("#718096")

    plt.tight_layout()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        img_path = os.path.join(output_dir, "concrete_rebar_chart.png")
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img_path = tmp.name
        tmp.close()

    fig.savefig(img_path, dpi=CHART_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return img_path
