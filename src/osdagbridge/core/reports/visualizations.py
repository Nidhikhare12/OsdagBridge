# =============================================================================
# OsdagBridge — Dynamic Report Visualizations Engine
# Programmatic generation of high-resolution, vector-quality charts for
# Section 5.5 (Utilization Ratios) and Chapter 7 (Material Quantities).
# =============================================================================

import os
import logging
from typing import Dict, Any, Optional, List, Tuple

import matplotlib
# Headless non-interactive rendering for server/CLI environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from osdagbridge.core.reports.styles import (
    CHART_PRIMARY_COLOR,
    CHART_DARK_COLOR,
    CHART_PASS_COLOR,
    CHART_WARN_COLOR,
    CHART_FAIL_COLOR,
    CHART_THRESHOLD_COLOR,
    CHART_STEEL_COLORS,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5.5: UTILIZATION RATIO (DEMAND / CAPACITY) SUMMARY CHARTS
# ═════════════════════════════════════════════════════════════════════════════

def generate_ur_bar_chart(
    ur_data: Dict[str, float],
    output_path: str = "ur_summary.png",
    figsize: Tuple[float, float] = (8.5, 4.6),
) -> plt.Figure:
    """
    Generate the Section 5.5 Utilization Ratio bar chart for primary bridge elements:
    - Steel Plate Girders
    - Concrete Deck Slab
    - Cross Bracing
    - End Diaphragms
    
    Includes a distinct red dashed horizontal threshold line at UR = 1.0.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    categories = list(ur_data.keys())
    values = [float(v) for v in ur_data.values()]

    colors = []
    for v in values:
        if v > 1.0:
            colors.append(CHART_FAIL_COLOR)       # Non-compliant (> 1.0)
        elif v > 0.85:
            colors.append(CHART_WARN_COLOR)       # Critical margin (0.85 - 1.0)
        else:
            colors.append(CHART_PASS_COLOR)       # Safe / Compliant (<= 0.85)

    fig, ax = plt.subplots(figsize=figsize, dpi=300)

    x_positions = np.arange(len(categories))
    bar_width = 0.52
    bars = ax.bar(
        x_positions,
        values,
        width=bar_width,
        color=colors,
        edgecolor="#2E3A1A",
        linewidth=1.0,
        zorder=3,
    )

    # Distinct red dashed horizontal reference line at UR = 1.0
    ax.axhline(
        y=1.0,
        color="red",
        linestyle="--",
        linewidth=2.0,
        zorder=4,
        label="Limit State Threshold: UR = 1.0 (Demand = Capacity)",
    )

    # Dynamic Y-limit calculation
    max_val = max(values) if values else 1.0
    if max_val < 0.65:
        y_max = 1.15
    elif max_val >= 1.0:
        y_max = max(max_val * 1.20, 1.55)
    else:
        y_max = 1.25
    ax.set_ylim(0, y_max)

    ax.axhspan(0, 0.85, color="#E8F5E9", alpha=0.5, zorder=1, label=r"Optimal Margin (UR $\leq$ 0.85)")
    ax.axhspan(0.85, 1.0, color="#FFF3E0", alpha=0.5, zorder=1, label=r"Critical Margin (0.85 < UR $\leq$ 1.0)")
    if y_max > 1.0:
        ax.axhspan(1.0, y_max, color="#FFEBEE", alpha=0.5, zorder=1, label="Overstressed / Failing (UR > 1.0)")

    # Value annotations on top of each bar
    for bar, val in zip(bars, values):
        height = bar.get_height()
        status_text = "PASS" if val <= 1.0 else "FAIL"
        badge_color = "#1B5E20" if val <= 1.0 else "#B71C1C"
        ax.annotate(
            f"{val:.2f}\n({status_text})",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color=badge_color,
            zorder=5,
        )

    # Styling
    ax.set_title("Overall Design Check Summary — Utilization Ratios (UR = Demand / Capacity)", fontsize=12, fontweight="bold", pad=14, color="#1F1F1F")
    ax.set_ylabel("Utilization Ratio (UR)", fontsize=10.5, fontweight="bold", labelpad=8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(categories, fontsize=9.5, fontweight="bold", rotation=0)
    ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=2)
    ax.set_axisbelow(True)

    # Legend
    ax.legend(loc="upper right", frameon=True, framealpha=0.9, fontsize=8.5, facecolor="#FFFFFF", edgecolor="#CCCCCC")

    # Spines
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#666666")
    ax.spines["bottom"].set_color("#666666")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info("Successfully generated UR summary chart: %s", output_path)
    return fig

create_ur_chart = generate_ur_bar_chart

def generate_ur_summary_chart(
    pg_ur: float = 0.82,
    deck_ur: float = 0.68,
    cb_ur: float = 0.54,
    ed_ur: float = 0.48,
    output_path: str = "ur_summary.png",
    figsize: Tuple[float, float] = (8.5, 4.6),
) -> Optional[str]:
    ur_dict = {
        "Steel Plate Girders": pg_ur,
        "Concrete Deck Slab": deck_ur,
        "Cross Bracing": cb_ur,
        "End Diaphragms": ed_ur,
    }
    fig = generate_ur_bar_chart(ur_dict, output_path, figsize)
    plt.close(fig)
    return output_path


# ═════════════════════════════════════════════════════════════════════════════
# CHAPTER 7: MATERIAL QUANTITIES & TAKE-OFF CHARTS
# ═════════════════════════════════════════════════════════════════════════════

def generate_material_quantity_charts(
    input_dict: Dict[str, Any],
    output_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate Chapter 7 Material Take-off bar charts:
    1. Structural Steel Tonnage Breakdown (Girders, Cross Bracing, End Diaphragms) in MT.
    2. Concrete Volume (m³) vs. Reinforcement Steel Weight (MT).
    """
    os.makedirs(output_dir, exist_ok=True)
    steel_chart_path = os.path.join(output_dir, "material_steel_tonnage.png")
    composite_chart_path = os.path.join(output_dir, "material_concrete_rebar.png")

    # ── Parse Quantities with safe fallbacks ──────────────────────────────────
    def _to_float(key, default=0.0):
        val = input_dict.get(key)
        if val in (None, "", "N.A."):
            return default
        try:
            return float(str(val).replace("MT", "").replace("m³", "").replace("kN", "").strip())
        except (ValueError, TypeError):
            return default

    # 1. Structural Steel Breakdown
    girders_wt = _to_float("steel_girders_wt_total", default=42.50)
    top_chord_wt = _to_float("bracing_top_wt_total", default=2.15)
    bot_chord_wt = _to_float("bracing_bot_wt_total", default=2.15)
    diag_chord_wt = _to_float("bracing_diag_wt_total", default=3.40)
    cb_total_wt = top_chord_wt + bot_chord_wt + diag_chord_wt
    ed_wt = _to_float("end_diaphragm_wt_total", default=4.80)
    studs_wt = _to_float("shear_studs_wt_total", default=0.95)

    # 2. Concrete vs Rebar
    concrete_vol = _to_float("concrete_deck_vol_total", default=62.40)  # m³
    rebar_wt = _to_float("rebar_deck_wt_total", default=9.85)          # MT

    # ── 1. Structural Steel Tonnage Bar Chart ────────────────────────────────
    try:
        categories = ["Main Girders", "Cross Bracing", "End Diaphragms", "Shear Studs"]
        tonnages = [girders_wt, cb_total_wt, ed_wt, studs_wt]

        fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=300)
        x_pos = np.arange(len(categories))
        bar_colors = ["#1E88E5", "#00897B", "#3949AB", "#FB8C00"]
        bars = ax.bar(x_pos, tonnages, width=0.48, color=bar_colors, edgecolor="#212121", linewidth=0.8, zorder=3)

        # Annotate tonnage numbers
        for bar in bars:
            h = bar.get_height()
            ax.annotate(
                f"{h:.2f} MT",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.0,
                fontweight="bold",
                color="#1F1F1F",
            )

        ax.set_title("Structural Steel Tonnage Breakdown by Component (Metric Tonnes)", fontsize=11, fontweight="bold", pad=12)
        ax.set_ylabel("Weight (MT)", fontsize=10, fontweight="bold")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, fontsize=9.5, fontweight="bold")
        ax.set_ylim(0, max(tonnages) * 1.22)
        ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=2)
        ax.set_axisbelow(True)

        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()
        fig.savefig(steel_chart_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    except Exception as e:
        logger.error("Failed to generate steel tonnage chart: %s", e, exc_info=True)
        steel_chart_path = None

    # ── 2. Concrete Volume vs. Reinforcement Steel Comparison ────────────────
    try:
        fig, ax1 = plt.subplots(figsize=(7.0, 3.8), dpi=300)

        items = ["Deck Slab Concrete\nVolume (m³)", "Deck Reinforcement\nSteel (MT)"]
        vals = [concrete_vol, rebar_wt]
        colors = ["#43A047", "#5E35B1"]

        x_pos = np.arange(len(items))
        bars = ax1.bar(x_pos, vals, width=0.44, color=colors, edgecolor="#212121", linewidth=0.8, zorder=3)

        for bar, v, unit in zip(bars, vals, ["m³", "MT"]):
            h = bar.get_height()
            ax1.annotate(
                f"{h:.2f} {unit}",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
                color="#1F1F1F",
            )

        ax1.set_title("Primary Deck Materials: Concrete Volume ($m^3$) vs. Reinforcement Steel (MT)", fontsize=11, fontweight="bold", pad=12)
        ax1.set_ylabel("Quantity", fontsize=10, fontweight="bold")
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(items, fontsize=9.5, fontweight="bold")
        ax1.set_ylim(0, max(vals) * 1.22)
        ax1.grid(axis="y", linestyle=":", alpha=0.6, zorder=2)
        ax1.set_axisbelow(True)

        for spine in ["top", "right"]:
            ax1.spines[spine].set_visible(False)

        plt.tight_layout()
        fig.savefig(composite_chart_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    except Exception as e:
        logger.error("Failed to generate concrete vs rebar chart: %s", e, exc_info=True)
        composite_chart_path = None

    return steel_chart_path, composite_chart_path
