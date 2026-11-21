"""Programmatic chart generation for the OsdagBridge design report.

All figures are rendered with Matplotlib (Agg backend), written as temporary
PNG assets during report assembly and embedded with
:func:`osdagbridge.core.reports.styles.figure_block`.  Colours and typography
come exclusively from :mod:`styles`.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import styles  # noqa: E402


def _save(fig: "plt.Figure", asset_dir: str, name: str) -> str:
    os.makedirs(asset_dir, exist_ok=True)
    path = os.path.join(asset_dir, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _style() -> None:
    plt.rcParams.update(styles.matplotlib_rc())


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def utilization_ratio_figure(
    ratios: List[Tuple[str, float]],
    asset_dir: str,
) -> str:
    """Create the Utilization Ratio bar chart for Section 5.5.

    ``ratios`` is a list of ``(element_name, UR)`` pairs.  A distinct red
    dashed reference line is drawn at UR = 1.0 and bars are coloured by pass
    (green) / fail (red) state.
    """
    _style()
    labels = [name for name, _ in ratios]
    values = [max(0.0, _number(ur)) for _, ur in ratios]
    colors = [
        styles.COLOR_UR_PASS if ur <= 1.0 else styles.COLOR_UR_FAIL
        for ur in values
    ]

    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    bars = ax.bar(labels, values, color=colors, width=0.55, zorder=3)
    ax.axhline(
        1.0,
        color=styles.COLOR_THRESHOLD_RED,
        linestyle="--",
        linewidth=1.6,
        label="UR limit = 1.0",
        zorder=4,
    )
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.set_title("Overall Utilization Ratio by Primary Element")
    ax.set_ylim(0.0, max(1.25, max(values, default=1.0) * 1.18))
    ax.tick_params(axis="x", rotation=18)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            value + 0.02,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=styles.COLOR_TEXT,
        )
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()

    path = _save(fig, asset_dir, "ur_summary.png")
    return styles.figure_block(
        path,
        r"Utilization Ratio (UR) of primary bridge elements. "
        r"Bars above the red dashed line ($\mathrm{UR}>1.0$) fail the check.",
        "fig:ur-summary",
    )


def material_quantity_figure(inputs: Dict[str, object], asset_dir: str) -> str:
    """Create the Chapter 7 material-quantity charts.

    Left panel: structural steel tonnage by component.  Right panel:
    concrete volume (m\³) versus reinforcement steel weight (MT) on twin axes.
    """
    _style()

    steel = _number(inputs.get("steel_girders_wt_total"))
    bracing = sum(
        _number(inputs.get(key))
        for key in (
            "bracing_top_wt_total",
            "bracing_bot_wt_total",
            "bracing_diag_wt_total",
            "steel_bracing_wt_total",
        )
    )
    # End-diaphragm quantities are not yet emitted by the BOQ engine; the bar
    # is still shown so the summary is complete and easy to extend.
    diaphragm = _number(inputs.get("end_diaphragm_wt_total"))
    concrete = _number(inputs.get("concrete_deck_vol_total"))
    rebar = _number(inputs.get("rebar_deck_wt_total"))

    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.0))

    def _bar_panel(ax, labels, values, color, title, ylabel, fmt="{:.2f}"):
        bars = ax.bar(labels, values, color=color, width=0.55, zorder=3)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0.0, max(values + [1.0]) * 1.20)
        ax.tick_params(axis="x", labelsize=8)
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                value + max(values + [1.0]) * 0.025,
                fmt.format(value),
                ha="center", va="bottom", fontsize=8, color=styles.COLOR_TEXT,
            )

    steel_labels = ["Plate\nGirders", "Cross\nBracing", "End\nDiaphragms"]
    _bar_panel(axes[0], steel_labels, [steel, bracing, diaphragm],
               styles.COLOR_STEEL, "Structural Steel", "Mass (MT)", "{:.1f}")
    _bar_panel(axes[1], ["Deck Slab"], [concrete],
               styles.COLOR_CONCRETE, "Concrete Volume", "Volume (m$^3$)")
    _bar_panel(axes[2], ["Deck Rebar"], [rebar],
               styles.COLOR_REBAR, "Reinforcement", "Mass (MT)")

    fig.tight_layout()
    path = _save(fig, asset_dir, "material_quantities.png")
    return styles.figure_block(
        path,
        r"Material quantity summary from the Bill of Materials: structural "
        r"steel tonnage by component, concrete volume and reinforcement weight.",
        "fig:material-quantities",
    )
