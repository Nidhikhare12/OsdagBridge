"""
Shared chart-generation helpers for OsdagBridge report visualizations.

Requirement 4 (UR summary bar charts, Section 5.5) and Requirement 5
(material quantity bar charts, Chapter 7) both need the same basic shape of
plot — categorical bars, optionally with a threshold reference line — so
that logic lives here once rather than being duplicated in chap5.py and
chap7.py. Chart colors are pulled from styles.py (the single source of
truth for the report's visual identity, per Requirement 6) rather than
hardcoded here.

Both public functions save a PNG to disk and return its path, ready to be
handed straight to report_utils._fig_embed().
"""
from __future__ import annotations

import os
import tempfile
import uuid

import matplotlib
matplotlib.use("Agg")  # headless — report generation has no display
import matplotlib.pyplot as plt

from . import styles

_BAR_COLOR = f"#{styles.COLOR_OSDAG_GREEN_HEX}"
_FAIL_COLOR = "#C0392B"
_THRESHOLD_COLOR = "red"


def _new_fig_path(fig_dir: str | None, name_hint: str) -> str:
    """Build a unique output path for a generated chart image.

    fig_dir defaults to a temp directory when the caller doesn't have (or
    care about) a shared assets folder — report_generator.py can pass its
    own fig_dir here to keep all generated images (pythonOCC renders +
    these charts) in one place if one already exists.
    """
    fig_dir = fig_dir or os.path.join(tempfile.gettempdir(), "osdagbridge_report_figs")
    os.makedirs(fig_dir, exist_ok=True)
    fname = f"{name_hint}_{uuid.uuid4().hex[:8]}.png"
    return os.path.join(fig_dir, fname)


def save_ur_summary_chart(ur_by_category: dict, fig_dir: str | None = None) -> str | None:
    """Bar chart of governing (max) Utilization Ratio per structural
    component, with a red dashed UR=1.0 threshold line.

    ur_by_category: {"Steel Plate Girders": 0.87, "Concrete Deck Slab": 0.62,
                      "Cross Bracing": 1.12, "End Diaphragms": None, ...}
    A None/missing value means no UR could be determined for that category
    (e.g. end diaphragm design not implemented for the selected type) — it
    is still shown on the x-axis but with no bar, rather than silently
    dropped, so the chart's category set stays predictable.

    Returns the saved PNG path, or None if there is nothing plottable
    (every category is None) — callers should skip embedding in that case
    rather than show an empty chart.
    """
    labels = list(ur_by_category.keys())
    values = [ur_by_category[k] for k in labels]

    if all(v is None for v in values):
        return None

    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    plot_vals = [v if v is not None else 0 for v in values]
    colors = [
        (_FAIL_COLOR if (v is not None and v > 1.0) else _BAR_COLOR)
        for v in values
    ]
    bars = ax.bar(labels, plot_vals, color=colors, width=0.55, zorder=3)

    ax.axhline(y=1.0, color=_THRESHOLD_COLOR, linestyle="--", linewidth=1.5,
               zorder=4, label="UR = 1.0 (limit)")

    for bar, v in zip(bars, values):
        label = f"{v:.2f}" if v is not None else "N/A"
        y = bar.get_height() if v is not None else 0.03
        ax.text(bar.get_x() + bar.get_width() / 2, y + 0.02, label,
                ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.set_ylim(0, max([1.3] + [v for v in values if v is not None]) * 1.15)
    ax.set_title("Overall Design Check Summary — Governing UR by Component")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right", fontsize=9)
    fig.tight_layout()

    path = _new_fig_path(fig_dir, "ur_summary")
    fig.savefig(path)
    plt.close(fig)
    return path


def save_material_bar_charts(
    steel_tonnage_by_component: dict,
    concrete_volume_m3: float | None,
    rebar_weight_mt: float | None,
    fig_dir: str | None = None,
) -> dict:
    """Two material-quantity bar charts for Chapter 7:
      1. Structural steel tonnage by component (Girders / Cross Bracing /
         End Diaphragms — whichever of these the caller actually has data
         for; components with no data are omitted rather than shown as 0,
         since a 0 bar would misleadingly suggest "confirmed zero steel"
         rather than "not itemized in this BOM").
      2. Concrete volume (m^3) vs reinforcement steel weight (MT) — two
         different units, so plotted as two separate labelled bars on a
         dual-axis chart rather than force them onto one shared y-axis.

    Returns {"steel_tonnage": path_or_None, "concrete_vs_rebar": path_or_None}.
    """
    result = {"steel_tonnage": None, "concrete_vs_rebar": None}

    # --- Chart 1: steel tonnage by component ---
    steel_items = {k: v for k, v in steel_tonnage_by_component.items() if v is not None}
    if steel_items:
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        labels = list(steel_items.keys())
        values = list(steel_items.values())
        bars = ax.bar(labels, values, color=_BAR_COLOR, width=0.5, zorder=3)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=9)
        ax.set_ylabel("Structural Steel (MT)")
        ax.set_title("Structural Steel Tonnage by Component")
        ax.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
        fig.tight_layout()
        path = _new_fig_path(fig_dir, "steel_tonnage")
        fig.savefig(path)
        plt.close(fig)
        result["steel_tonnage"] = path

    # --- Chart 2: concrete volume vs rebar weight (different units) ---
    if concrete_volume_m3 is not None or rebar_weight_mt is not None:
        fig, ax1 = plt.subplots(figsize=(6, 4), dpi=150)
        ax2 = ax1.twinx()

        cv = concrete_volume_m3 if concrete_volume_m3 is not None else 0
        rw = rebar_weight_mt if rebar_weight_mt is not None else 0

        b1 = ax1.bar([0], [cv], width=0.4, color=_BAR_COLOR, label="Concrete Volume", zorder=3)
        b2 = ax2.bar([1], [rw], width=0.4, color="#4472C4", label="Reinforcement Weight", zorder=3)

        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(["Concrete\n(Deck Slab)", "Reinforcement\nSteel"])
        ax1.set_ylabel(r"Concrete Volume (m$^3$)")
        ax2.set_ylabel("Reinforcement Weight (MT)")
        ax1.set_title("Concrete Volume vs. Reinforcement Steel Weight")

        if concrete_volume_m3 is not None:
            ax1.text(0, cv, f"{cv:.2f} m³", ha="center", va="bottom", fontsize=9)
        if rebar_weight_mt is not None:
            ax2.text(1, rw, f"{rw:.2f} MT", ha="center", va="bottom", fontsize=9)

        fig.tight_layout()
        path = _new_fig_path(fig_dir, "concrete_vs_rebar")
        fig.savefig(path)
        plt.close(fig)
        result["concrete_vs_rebar"] = path

    return result