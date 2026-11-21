# =============================================================================
# OsdagBridge — Report Chart Generation Module (Phase 5 & 6)
# =============================================================================
"""
Centralized chart generation module for OsdagBridge design reports.

All chart styling, dimensions, colors, and dpi are imported directly from
`osdagbridge.core.reports.styles`. Charts are generated using Matplotlib with
the headless 'Agg' backend and saved directly to the designated output directories.
"""

import os
from typing import List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from osdagbridge.core.reports.styles import (
    CHART_DPI,
    CHART_FIGSIZE_WIDE,
    CHART_FIGSIZE_BAR,
    CHART_FIGSIZE_DONUT,
    CHART_COLOR_PRIMARY,
    CHART_COLOR_SECONDARY,
    CHART_COLOR_ACCENT,
    CHART_COLOR_WARN,
    CHART_COLOR_DANGER,
    CHART_COLOR_GRID,
    CHART_GRID_ALPHA,
)
from osdagbridge.core.utils.common import (
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_OH,
    KEY_DD_MU_OH,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_WK_BOT,
    KEY_DD_WK_TOP,
    KEY_DD_WK_OH,
    KEY_DD_WK_LIMIT,
    KEY_DD_HAS_OVERHANG,
)


def _save_figure(fig: plt.Figure, output_dirs: Union[str, List[str]], filename: str) -> str:
    """Save a Matplotlib figure to one or more directories and close it."""
    if isinstance(output_dirs, str):
        output_dirs = [output_dirs]

    for d in output_dirs:
        if d:
            os.makedirs(d, exist_ok=True)
            target = os.path.join(d, filename)
            fig.savefig(target, dpi=CHART_DPI, bbox_inches="tight")

    plt.close(fig)
    return os.path.join("images", filename).replace("\\", "/")


def generate_ur_summary_chart(bridge, output_dirs: Union[str, List[str]]) -> Optional[str]:
    """
    Generate the Section 5.5 Overall Component Utilization Ratio summary bar chart.

    Parameters
    ----------
    bridge : ReportDataBridge
        Data bridge containing inputs, outputs, and design check results.
    output_dirs : Union[str, List[str]]
        Directory or list of directories where the generated chart should be written.

    Returns
    -------
    Optional[str]
        Relative LaTeX path to the generated chart image, or None if no numeric UR data.
    """
    if bridge is None or not getattr(bridge, "output_dict", None):
        return None

    output_dict = bridge.output_dict
    design_results = output_dict.get("design_results", {}) or {}
    pg_522 = design_results.get("per_girder", {}) or {}
    deck_rpt = output_dict.get("deck_report_values", {}) or {}

    checks = []  # List of tuples: (label, ur_float)

    # 1. Girder DCR-engine checks
    def get_dcr(check_ids):
        best = None
        for g, gd in pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr")
                    if d is not None:
                        try:
                            df = float(d)
                            if best is None or df > best:
                                best = df
                        except (ValueError, TypeError):
                            pass
        if best is not None:
            return best
        for g, gd in pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr")
                        if d is not None:
                            try:
                                df = float(d)
                                if best is None or df > best:
                                    best = df
                            except (ValueError, TypeError):
                                pass
        return best

    girder_checks = [
        ("Girder Moment", {1}),
        ("Girder Shear", {2}),
        ("Girder LTB (constr.)", {5}),
        ("Girder Deflection", {13, 14}),
        ("Girder Stress", {11}),
        ("Girder Fatigue", {8, 9}),
        ("Transverse Shear (slab)", {16}),
    ]

    for label, ids in girder_checks:
        ur = get_dcr(ids)
        if ur is not None:
            checks.append((label, float(ur)))

    # 2. Deck slab crack width check
    def dkv(key, default=0.0):
        v = deck_rpt.get(key)
        try:
            return float(v) if v is not None else default
        except (ValueError, TypeError):
            return default

    if deck_rpt:
        wks = [dkv(KEY_DD_WK_BOT), dkv(KEY_DD_WK_TOP)]
        if deck_rpt.get(KEY_DD_HAS_OVERHANG):
            wks.append(dkv(KEY_DD_WK_OH))
        wk_max = max(wks) if wks else 0.0
        wk_lim = dkv(KEY_DD_WK_LIMIT, 0.3)
        if wk_lim > 0:
            checks.append(("Crack Width (slab)", wk_max / wk_lim))

        # 3. Deck slab ULS flexure & shear checks
        deck_pairs = [
            ("Deck Flexure (sagging)", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
            ("Deck Flexure (hogging)", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
            ("Deck Overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH),
            ("Deck Punching Shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
            ("Deck One-Way Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
        ]
        for label, dem_k, cap_k in deck_pairs:
            dem = dkv(dem_k)
            cap = dkv(cap_k)
            if cap > 0:
                checks.append((label, dem / cap))

    # 4. Cross bracing checks
    try:
        pairs = bridge.get_cb_pairs()
        for ftype, lbl in [("compression", "Cross Bracing Comp."), ("tension", "Cross Bracing Tens.")]:
            best_ur = None
            for p in pairs:
                for m in ("diagonal", "chord"):
                    eff = bridge.get_cb_efficiency(p, m, ftype)
                    try:
                        val = float(eff)
                        if best_ur is None or val > best_ur:
                            best_ur = val
                    except (ValueError, TypeError):
                        pass
            if best_ur is not None:
                checks.append((lbl, best_ur))

        # Slenderness
        best_sl = None
        for p in pairs:
            for m in ("diagonal", "chord"):
                s = bridge.get_cb_slenderness(p, m)
                try:
                    sf = float(s)
                    lim = 400.0 if m == "chord" else 250.0
                    r = sf / lim
                    if best_sl is None or r > best_sl:
                        best_sl = r
                except (ValueError, TypeError):
                    pass
        if best_sl is not None:
            checks.append(("Cross Bracing Slenderness", best_sl))
    except Exception:
        pass

    if not checks:
        return None

    # Sort checks from lowest to highest for neat horizontal bar display
    labels = [c[0] for c in checks]
    values = [c[1] for c in checks]

    # Build plot
    fig, ax = plt.subplots(figsize=(7.5, max(4.0, len(checks) * 0.32)))

    y_pos = range(len(labels))
    colors = [CHART_COLOR_DANGER if v > 1.0 else CHART_COLOR_PRIMARY for v in values]

    bars = ax.barh(y_pos, values, color=colors, height=0.6, align="center", edgecolor="none")

    # Code limit line at UR = 1.0
    ax.axvline(1.0, color=CHART_COLOR_DANGER, linestyle="--", linewidth=1.5, label="Code Limit (UR = 1.0)")

    # Value labels on bars
    for bar, val in zip(bars, values):
        width = bar.get_width()
        x_text = width + 0.02
        txt_col = CHART_COLOR_DANGER if val > 1.0 else "#222222"
        ax.text(
            x_text,
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:.2f}",
            va="center",
            ha="left",
            fontsize=8.5,
            fontweight="bold",
            color=txt_col,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.invert_yaxis()  # Top-down reading order

    max_val = max(values) if values else 1.0
    ax.set_xlim(0, max(1.20, max_val * 1.15))
    ax.set_xlabel("Utilization Ratio (Demand / Capacity)", fontsize=9.5, fontweight="bold")
    ax.set_title("Overall Component Utilization Ratios", fontsize=11, fontweight="bold", pad=12)

    ax.grid(axis="x", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.9)

    plt.tight_layout()
    return _save_figure(fig, output_dirs, "chart_ur_summary.png")


def generate_material_quantity_charts(inputs: dict, output_dirs: Union[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate the Chapter 7 Material Quantity Breakdown charts:
      1. Structural Steel Weight Breakdown (MT)
      2. Concrete Volume (m³) vs Rebar Steel Weight (MT)

    Parameters
    ----------
    inputs : dict
        Inputs dictionary containing populated BOQ quantity keys from `calculate_material_quantities`.
    output_dirs : Union[str, List[str]]
        Directory or list of directories where the generated charts should be written.

    Returns
    -------
    Tuple[Optional[str], Optional[str]]
        Tuple of (steel_chart_path, concrete_rebar_chart_path).
    """
    if not inputs:
        return (None, None)

    def _fval(key):
        v = inputs.get(key)
        try:
            return float(v) if v is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    # 1. Structural Steel Breakdown
    girders_wt = _fval("steel_girders_wt_total")
    bracing_top_wt = _fval("bracing_top_wt_total")
    bracing_bot_wt = _fval("bracing_bot_wt_total")
    bracing_diag_wt = _fval("bracing_diag_wt_total")
    cross_bracing_wt = bracing_top_wt + bracing_bot_wt + bracing_diag_wt
    shear_studs_wt = _fval("shear_studs_wt_total")

    steel_items = []
    if girders_wt > 0:
        steel_items.append(("Plate Girders", girders_wt))
    if cross_bracing_wt > 0:
        steel_items.append(("Cross Bracing", cross_bracing_wt))
    if shear_studs_wt > 0:
        steel_items.append(("Shear Connectors", shear_studs_wt))

    steel_chart_path = None
    if steel_items:
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE_BAR)
        categories = [item[0] for item in steel_items]
        tonnages = [item[1] for item in steel_items]
        palette = [CHART_COLOR_PRIMARY, CHART_COLOR_SECONDARY, CHART_COLOR_ACCENT]
        colors = [palette[i % len(palette)] for i in range(len(steel_items))]

        bars = ax.bar(categories, tonnages, color=colors, width=0.45, edgecolor="none")

        total_steel = sum(tonnages)
        for bar, wt in zip(bars, tonnages):
            pct = (wt / total_steel * 100.0) if total_steel > 0 else 0.0
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + (max(tonnages) * 0.02),
                f"{wt:.2f} MT\n({pct:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

        ax.set_ylim(0, max(tonnages) * 1.25)
        ax.set_ylabel("Weight (Metric Tonnes, MT)", fontsize=9.5, fontweight="bold")
        ax.set_title("Structural Steel Weight Breakdown", fontsize=11, fontweight="bold", pad=12)
        ax.grid(axis="y", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID)
        ax.set_axisbelow(True)

        plt.tight_layout()
        steel_chart_path = _save_figure(fig, output_dirs, "chart_steel_breakdown.png")

    # 2. Concrete Volume vs Rebar Weight
    concrete_vol = _fval("concrete_deck_vol_total")
    rebar_wt = _fval("rebar_deck_wt_total")

    concrete_rebar_chart_path = None
    if concrete_vol > 0 or rebar_wt > 0:
        fig, ax1 = plt.subplots(figsize=(6.5, 3.5))

        x_indices = [0, 1]
        labels = [r"Deck Concrete ($m^3$)", "Deck Rebar Steel (MT)"]
        values = [concrete_vol, rebar_wt]
        colors = [CHART_COLOR_SECONDARY, CHART_COLOR_PRIMARY]

        bars = ax1.bar(x_indices, values, color=colors, width=0.45, edgecolor="none")

        for bar, val, unit in zip(bars, values, [r"$m^3$", "MT"]):
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + (max(values) * 0.02),
                f"{val:.2f} {unit}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

        ax1.set_xticks(x_indices)
        ax1.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
        ax1.set_ylim(0, max(values) * 1.25)
        ax1.set_ylabel("Quantity", fontsize=9.5, fontweight="bold")
        ax1.set_title("Deck Slab Materials: Concrete Volume vs Rebar Steel", fontsize=11, fontweight="bold", pad=12)
        ax1.grid(axis="y", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID)
        ax1.set_axisbelow(True)

        plt.tight_layout()
        concrete_rebar_chart_path = _save_figure(fig, output_dirs, "chart_concrete_rebar.png")

    return (steel_chart_path, concrete_rebar_chart_path)
