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
    """Save a Matplotlib figure to one or more directories as both vector PDF and raster PNG."""
    if isinstance(output_dirs, str):
        output_dirs = [output_dirs]

    base_name = os.path.splitext(filename)[0]

    for d in output_dirs:
        if d:
            os.makedirs(d, exist_ok=True)
            # 1. Vector PDF (sharp at all zoom levels)
            pdf_target = os.path.join(d, f"{base_name}.pdf")
            fig.savefig(pdf_target, bbox_inches="tight")
            # 2. Raster PNG fallback
            png_target = os.path.join(d, f"{base_name}.png")
            fig.savefig(png_target, dpi=CHART_DPI, bbox_inches="tight")

    plt.close(fig)
    return os.path.join("images", f"{base_name}.pdf").replace("\\", "/")


def generate_ur_summary_chart(bridge, output_dirs: Union[str, List[str]]) -> Tuple[Optional[str], str]:
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
    Tuple[Optional[str], str]
        (Relative LaTeX path to chart PDF, missing_data_note).
    """
    if bridge is None or not getattr(bridge, "output_dict", None):
        return (None, "")

    output_dict = bridge.output_dict
    design_results = output_dict.get("design_results", {}) or {}
    pg_522 = design_results.get("per_girder", {}) or {}
    deck_rpt = output_dict.get("deck_report_values", {}) or {}

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

    grp_girders = []
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
            grp_girders.append((label, float(ur)))

    # 2. Deck slab checks
    grp_deck = []
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
            grp_deck.append(("Crack Width (slab)", wk_max / wk_lim))

        deck_pairs = [
            ("Deck Sagging Flexure", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
            ("Deck Hogging Flexure", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
            ("Deck Cantilever OH", KEY_DD_M_ULS_OH, KEY_DD_MU_OH),
            ("Deck Punching Shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
            ("Deck One-Way Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
        ]
        for label, dem_k, cap_k in deck_pairs:
            dem = dkv(dem_k)
            cap = dkv(cap_k)
            if cap > 0:
                grp_deck.append((label, dem / cap))

    # 3. Cross bracing checks
    grp_cb = []
    try:
        cb_pairs = bridge.get_cb_pairs()
        for ftype, lbl in [("compression", "Cross Bracing Comp."), ("tension", "Cross Bracing Tens.")]:
            best_ur = None
            for p in cb_pairs:
                for m in ("diagonal", "chord"):
                    eff = bridge.get_cb_efficiency(p, m, ftype)
                    try:
                        val = float(eff)
                        if best_ur is None or val > best_ur:
                            best_ur = val
                    except (ValueError, TypeError):
                        pass
            if best_ur is not None:
                grp_cb.append((lbl, best_ur))

        best_sl = None
        for p in cb_pairs:
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
            grp_cb.append(("Cross Bracing Slender.", best_sl))
    except Exception:
        pass

    # 4. End Diaphragm checks
    grp_ed = []
    try:
        ed_pairs = bridge.get_ed_pairs()
        for ftype, lbl in [("compression", "End Diaphragm Comp."), ("tension", "End Diaphragm Tens.")]:
            best_ur = None
            for p in ed_pairs:
                for m in ("diagonal", "chord"):
                    eff = bridge.get_ed_efficiency(p, m, ftype)
                    try:
                        val = float(eff)
                        if best_ur is None or val > best_ur:
                            best_ur = val
                    except (ValueError, TypeError):
                        pass
            if best_ur is not None:
                grp_ed.append((lbl, best_ur))

        best_sl = None
        for p in ed_pairs:
            for m in ("diagonal", "chord"):
                s = bridge.get_ed_slenderness(p, m)
                try:
                    sf = float(s)
                    lim = 400.0 if m == "chord" else 250.0
                    r = sf / lim
                    if best_sl is None or r > best_sl:
                        best_sl = r
                except (ValueError, TypeError):
                    pass
        if best_sl is not None:
            grp_ed.append(("End Diaphragm Slender.", best_sl))
    except Exception:
        pass

    # Track missing groups
    missing_groups = []
    if not grp_girders:
        missing_groups.append("Plate Girders")
    if not grp_deck:
        missing_groups.append("Deck Slab")
    if not grp_cb:
        missing_groups.append("Cross Bracing")
    if not grp_ed:
        missing_groups.append("End Diaphragms")

    missing_note = ""
    if missing_groups:
        missing_note = f"Data not available for: {', '.join(missing_groups)}"

    # If no checks at all
    all_groups = [
        ("Plate Girders", grp_girders, CHART_COLOR_PRIMARY),
        ("Concrete Deck Slab", grp_deck, CHART_COLOR_SECONDARY),
        ("Cross Bracing", grp_cb, CHART_COLOR_ACCENT),
        ("End Diaphragms", grp_ed, "#E67E22"),
    ]
    total_checks = sum(len(g[1]) for g in all_groups)
    if total_checks == 0:
        return (None, missing_note)

    # Build vertical grouped bar plot
    fig, ax = plt.subplots(figsize=(10.0, 5.2))

    all_x = []
    all_labels = []
    all_vals = []
    all_colors = []

    current_x = 0.0
    group_centers = []
    divider_xs = []

    for idx, (grp_name, grp_items, grp_color) in enumerate(all_groups):
        if not grp_items:
            continue
        start_x = current_x
        for label, val in grp_items:
            all_x.append(current_x)
            all_labels.append(label)
            all_vals.append(val)
            col = CHART_COLOR_DANGER if val > 1.0 else grp_color
            all_colors.append(col)
            current_x += 1.0
        end_x = current_x - 1.0
        group_centers.append(((start_x + end_x) / 2.0, grp_name, grp_color))

        # Divider after group
        if idx < len(all_groups) - 1:
            divider_x = current_x - 0.5 + 0.2
            divider_xs.append(divider_x)
            current_x += 0.6  # Gap between groups

    bars = ax.bar(all_x, all_vals, color=all_colors, width=0.62, edgecolor="none", zorder=3)

    # Red dashed code limit line at UR = 1.0
    ax.axhline(1.0, color=CHART_COLOR_DANGER, linestyle="--", linewidth=1.5, zorder=4, label="Code Limit (UR = 1.0)")

    # Vertical group divider lines
    for dx in divider_xs:
        ax.axvline(dx, color="#CCCCCC", linestyle=":", linewidth=1.2, zorder=2)

    # Top group headers (placed cleanly at top with ample clearance)
    max_val = max(all_vals) if all_vals else 1.0
    top_limit = max(1.22, max_val * 1.15)
    header_y = top_limit * 0.93
    for cx, gname, gcol in group_centers:
        ax.text(cx, header_y, gname, ha="center", va="center", fontsize=8.5, fontweight="bold", color=gcol, zorder=5)

    # Value labels with collision prevention
    for x, val, bar in zip(all_x, all_vals, bars):
        if 0.88 <= val <= 1.02:
            # Place inside the bar to prevent collision with UR = 1.0 line
            ax.text(
                x,
                val - 0.08,
                f"{val:.2f}",
                ha="center",
                va="top",
                fontsize=7.5,
                fontweight="bold",
                color="white",
                zorder=6,
            )
        else:
            txt_col = CHART_COLOR_DANGER if val > 1.0 else "#222222"
            ax.text(
                x,
                val + 0.02,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
                color=txt_col,
                zorder=6,
            )

    ax.set_xticks(all_x)
    ax.set_xticklabels(all_labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0, top_limit)
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontsize=9.5, fontweight="bold")
    ax.set_title("Overall Component Utilization Ratios", fontsize=11, fontweight="bold", pad=12)

    ax.grid(axis="y", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID, zorder=1)
    ax.set_axisbelow(True)

    # Custom legend moved below plot so no title or bar is covered
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor=CHART_COLOR_PRIMARY, label="Plate Girders"),
        Patch(facecolor=CHART_COLOR_SECONDARY, label="Deck Slab"),
        Patch(facecolor=CHART_COLOR_ACCENT, label="Cross Bracing"),
        Patch(facecolor="#E67E22", label="End Diaphragms"),
        Line2D([0], [0], color=CHART_COLOR_DANGER, linestyle="--", linewidth=1.5, label="Code Limit (UR = 1.0)"),
    ]
    if any(v > 1.0 for v in all_vals):
        legend_elements.append(Patch(facecolor=CHART_COLOR_DANGER, label="UR > 1.0 (Fail)"))

    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.32),
        ncol=5 if len(legend_elements) <= 5 else 3,
        fontsize=8.0,
        frameon=True,
        framealpha=0.95,
        edgecolor="#CCCCCC",
    )

    plt.tight_layout()
    chart_path = _save_figure(fig, output_dirs, "chart_ur_summary.pdf")
    return (chart_path, missing_note)


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

    # 1. Structural Steel Breakdown (Plate Girders, Cross Bracing, End Diaphragms)
    girders_wt = _fval("steel_girders_wt_total")
    bracing_top_wt = _fval("bracing_top_wt_total")
    bracing_bot_wt = _fval("bracing_bot_wt_total")
    bracing_diag_wt = _fval("bracing_diag_wt_total")
    cross_bracing_wt = bracing_top_wt + bracing_bot_wt + bracing_diag_wt
    ed_wt = _fval("steel_ed_wt_total")

    steel_items = [
        ("Plate\nGirders", girders_wt),
        ("Cross\nBracing", cross_bracing_wt),
        ("End\nDiaphragms", ed_wt),
    ]

    steel_chart_path = None
    if any(wt > 0 for _, wt in steel_items):
        fig, ax = plt.subplots(figsize=(4.0, 3.0))
        categories = [item[0] for item in steel_items]
        tonnages = [item[1] for item in steel_items]
        colors = [CHART_COLOR_PRIMARY, CHART_COLOR_SECONDARY, "#E67E22"]

        bars = ax.bar(categories, tonnages, color=colors, width=0.55, edgecolor="none", zorder=3)

        total_steel = sum(tonnages)
        max_tonnage = max(tonnages) if tonnages else 1.0
        for bar, wt in zip(bars, tonnages):
            if wt > 0:
                pct = (wt / total_steel * 100.0) if total_steel > 0 else 0.0
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + (max_tonnage * 0.02),
                    f"{wt:.2f} MT\n({pct:.1f}%)",
                    ha="center",
                    va="bottom",
                    fontsize=10.5,
                    fontweight="bold",
                    zorder=5,
                )
            else:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    max_tonnage * 0.02,
                    "N.A.",
                    ha="center",
                    va="bottom",
                    fontsize=10.5,
                    fontweight="bold",
                    color="#888888",
                    zorder=5,
                )

        ax.set_ylim(0, max_tonnage * 1.45)
        ax.set_ylabel("Weight (MT)", fontsize=11.5, fontweight="bold")
        ax.set_title("Structural Steel Breakdown", fontsize=12.5, fontweight="bold", pad=12)
        ax.tick_params(axis="x", labelsize=10.5)
        ax.tick_params(axis="y", labelsize=10.0)
        ax.grid(axis="y", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID, zorder=1)
        ax.set_axisbelow(True)

        plt.tight_layout()
        steel_chart_path = _save_figure(fig, output_dirs, "chart_steel_breakdown.pdf")

    # 2. Concrete Volume vs Rebar Weight
    concrete_vol = _fval("concrete_deck_vol_total")
    rebar_wt = _fval("rebar_deck_wt_total")

    concrete_rebar_chart_path = None
    if concrete_vol > 0 or rebar_wt > 0:
        fig, ax1 = plt.subplots(figsize=(4.0, 3.0))

        x_indices = [0, 1]
        labels = [r"Deck Concrete" + "\n" + r"($m^3$)", "Deck Rebar\n(MT)"]
        values = [concrete_vol, rebar_wt]
        colors = [CHART_COLOR_SECONDARY, CHART_COLOR_PRIMARY]

        bars = ax1.bar(x_indices, values, color=colors, width=0.50, edgecolor="none", zorder=3)

        max_val = max(values) if values else 1.0
        for bar, val, unit in zip(bars, values, [r"$m^3$", "MT"]):
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + (max_val * 0.02),
                f"{val:.2f} {unit}",
                ha="center",
                va="bottom",
                fontsize=11.0,
                fontweight="bold",
                zorder=5,
            )

        ax1.set_xticks(x_indices)
        ax1.set_xticklabels(labels, fontsize=10.5, fontweight="bold")
        ax1.set_ylim(0, max_val * 1.35)
        ax1.set_ylabel("Quantity", fontsize=11.5, fontweight="bold")
        ax1.set_title("Deck Slab Materials", fontsize=12.5, fontweight="bold", pad=12)
        ax1.tick_params(axis="y", labelsize=10.0)
        ax1.grid(axis="y", linestyle=":", alpha=CHART_GRID_ALPHA, color=CHART_COLOR_GRID, zorder=1)
        ax1.set_axisbelow(True)

        plt.tight_layout()
        concrete_rebar_chart_path = _save_figure(fig, output_dirs, "chart_concrete_rebar.pdf")

    return (steel_chart_path, concrete_rebar_chart_path)

