# =============================================================================
# OsdagBridge — Report Chart Generators (report_charts.py)
# Programmatic generation of Utilization Ratio and BOQ visualizations.
# =============================================================================

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for headless environments
import matplotlib.pyplot as plt
from typing import Dict, Any

from osdagbridge.core.reports.styles import COLORS, apply_report_chart_style


def generate_overall_ur_chart(ur_dict: Dict[str, float], output_path: str) -> str:
    """
    Generate an overall Utilization Ratio (UR = Demand / Capacity) bar chart
    for primary bridge structural components with a threshold line at UR = 1.0.

    Requirements addressed:
      - Primary components: Steel Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms
      - Y-Axis: Utilization Ratio (UR)
      - Red dashed reference line at UR = 1.0
      - Color-coded bars: Green (UR <= 1.0), Red (UR > 1.0)
    """
    labels = list(ur_dict.keys())
    values = [max(0.0, float(ur_dict[k])) for k in labels]

    fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=300)

    # Color code bars based on safety check: Pass (<= 1.0) or Fail (> 1.0)
    bar_colors = [COLORS["fail"] if v > 1.0 else COLORS["primary"] for v in values]

    bars = ax.bar(labels, values, color=bar_colors, width=0.48, zorder=3, edgecolor=COLORS["dark_text"], linewidth=0.6)

    # Reference limit line at UR = 1.0
    ax.axhline(1.0, color=COLORS["fail"], linestyle="--", linewidth=1.5, zorder=4,
               label=r"Capacity Limit ($UR = 1.0$)")

    # Add numeric annotations above bars
    max_val = max(values) if values else 1.0
    for bar, val in zip(bars, values):
        y_pos = bar.get_height()
        status_text = f"{val:.2f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            y_pos + 0.03,
            status_text,
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color=COLORS["fail"] if val > 1.0 else COLORS["dark_text"]
        )

    apply_report_chart_style(
        ax,
        title="Overall Structural Utilization Ratio (Demand / Capacity)",
        xlabel="Structural Component",
        ylabel="Utilization Ratio (UR)"
    )

    y_upper = max(1.25, max_val * 1.22)
    ax.set_ylim(0.0, y_upper)
    ax.legend(loc="upper right", frameon=True, fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def generate_steel_tonnage_chart(quantities: Dict[str, Any], output_path: str) -> str:
    """
    Generate a structural steel tonnage breakdown bar chart for Chapter 7.
    """
    def _parse(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    girders_wt = _parse(quantities.get("steel_girders_wt_total"))
    top_chord_wt = _parse(quantities.get("bracing_top_wt_total"))
    bot_chord_wt = _parse(quantities.get("bracing_bot_wt_total"))
    diag_wt = _parse(quantities.get("bracing_diag_wt_total"))
    cb_total = top_chord_wt + bot_chord_wt + diag_wt
    ed_total = _parse(quantities.get("diaphragm_wt_total", 0.0))
    studs_wt = _parse(quantities.get("shear_studs_wt_total"))

    items = {
        "Plate Girders": max(0.1, girders_wt),
        "Cross Bracing": max(0.05, cb_total),
        "End Diaphragms": max(0.05, ed_total if ed_total > 0 else (cb_total * 0.4)),
        "Shear Studs": max(0.01, studs_wt),
    }

    labels = list(items.keys())
    values = list(items.values())

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=300)
    palette = [COLORS["primary"], COLORS["secondary"], COLORS["accent"], "#64748B"]

    bars = ax.bar(labels, values, color=palette, width=0.45, zorder=3, edgecolor=COLORS["dark_text"], linewidth=0.6)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + (max(values) * 0.02),
            f"{val:.2f} MT",
            ha="center",
            va="bottom",
            fontsize=9.0,
            fontweight="bold",
            color=COLORS["dark_text"]
        )

    apply_report_chart_style(
        ax,
        title="Structural Steel Breakdown by Subsystem (Metric Tonnes)",
        xlabel="Subsystem / Component",
        ylabel="Total Weight (MT)"
    )

    ax.set_ylim(0.0, max(values) * 1.18 if values else 10.0)
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def generate_material_comparison_chart(quantities: Dict[str, Any], output_path: str) -> str:
    """
    Generate a comparison chart of Concrete Volume (m³) vs. Reinforcement Rebar Weight (MT)
    and Structural Steel Tonnage (MT) for Chapter 7.
    """
    def _parse(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    conc_vol = _parse(quantities.get("concrete_deck_vol_total"))
    rebar_wt = _parse(quantities.get("rebar_deck_wt_total"))
    steel_wt = _parse(quantities.get("steel_girders_wt_total"))

    labels = ["Concrete Deck (m³)", "Rebar Fe 500 (MT)", "Structural Steel (MT)"]
    values = [max(0.1, conc_vol), max(0.1, rebar_wt), max(0.1, steel_wt)]
    bar_colors = [COLORS["secondary"], "#F59E0B", COLORS["primary"]]

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=300)
    bars = ax.bar(labels, values, color=bar_colors, width=0.42, zorder=3, edgecolor=COLORS["dark_text"], linewidth=0.6)

    for bar, val, lbl in zip(bars, values, labels):
        unit = " m³" if "m³" in lbl else " MT"
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + (max(values) * 0.02),
            f"{val:.2f}{unit}",
            ha="center",
            va="bottom",
            fontsize=9.0,
            fontweight="bold",
            color=COLORS["dark_text"]
        )

    apply_report_chart_style(
        ax,
        title="Primary Construction Material Quantities Summary",
        xlabel="Material / Component",
        ylabel="Quantity"
    )

    ax.set_ylim(0.0, max(values) * 1.18 if values else 10.0)
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path
