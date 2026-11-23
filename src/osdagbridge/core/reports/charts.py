# =============================================================================
# OsdagBridge — Dynamic Engineering Report Charts Generator
#
# Generates dynamic, publication-grade Matplotlib charts:
# 1. Utilization Ratio (UR = Demand / Capacity) Charts with UR=1.0 threshold:
#    - Steel Plate Girders
#    - Concrete Deck Slab
#    - Cross Bracing
#    - End Diaphragms
# 2. Material Quantity Charts (using actual Chapter 7 BOM quantities):
#    - Structural Steel Tonnage Breakdown (Girders, Cross Bracing, End Diaphragms)
#    - Concrete Volume (m³) and Reinforcement Steel Weight (MT)
#
# Uses actual design results only. Never hardcodes invented numbers.
# =============================================================================

import os
import logging
import math
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from osdagbridge.core.reports.styles import (
    COLOR_OSDAG_GREEN,
    COLOR_OSDAG_GREEN_DARK,
    COLOR_PASS,
    COLOR_FAIL,
    COLOR_THRESHOLD,
    COLOR_BORDER,
    COLOR_GRID,
    CHART_PALETTE,
    configure_plot_style
)

logger = logging.getLogger(__name__)


def _draw_ur_bar_chart(
    items: list[tuple[str, float]],
    title: str,
    output_path: str,
    xlabel: str = "Utilization Ratio (Demand / Capacity)"
) -> Optional[str]:
    """
    Draw a horizontal bar chart of Utilization Ratios with a red dashed line at UR=1.0.
    items: list of (check_label, ur_value)
    """
    if not items:
        return None

    configure_plot_style()
    labels = [it[0] for it in items]
    values = [float(it[1]) for it in items]
    if not all(math.isfinite(v) and v >= 0 for v in values):
        logger.warning("Skipping chart with invalid utilization values")
        return None

    # Dynamic height based on number of items
    fig_height = max(2.8, len(items) * 0.45 + 1.0)
    fig, ax = plt.subplots(figsize=(7.2, fig_height), dpi=300)

    y_pos = range(len(labels))
    colors = [COLOR_FAIL if v > 1.0 else COLOR_OSDAG_GREEN for v in values]

    bars = ax.barh(y_pos, values, color=colors, edgecolor=COLOR_BORDER, height=0.55, zorder=3)

    # Red dashed threshold line at UR = 1.0
    ax.axvline(
        1.0,
        color=COLOR_THRESHOLD,
        linestyle='--',
        linewidth=1.8,
        label='UR = 1.0 (Limit)',
        zorder=4
    )

    # Set x limits with comfortable padding
    max_val = max(values) if values else 1.0
    x_limit = max(1.15, max_val * 1.15)
    ax.set_xlim(0, x_limit)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9.0)
    ax.invert_yaxis()  # top-down order
    ax.set_xlabel(xlabel, fontsize=9.5, fontweight='bold', labelpad=6)
    ax.set_title(title, fontsize=10.5, fontweight='bold', pad=10, color="#1A252F")

    # Add numeric labels at end of bars
    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        text_color = COLOR_FAIL if val > 1.0 else "#2C3E50"
        ax.text(
            x_pos + (x_limit * 0.015),
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:.3f}",
            va='center',
            ha='left',
            fontsize=8.5,
            fontweight='bold',
            color=text_color
        )

    ax.grid(axis='x', linestyle='--', alpha=0.5, color=COLOR_GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc='lower right', frameon=True, facecolor='white', edgecolor=COLOR_BORDER, fontsize=8.5)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


# =============================================================================
# 1. UTILIZATION RATIO CHARTS GENERATOR
# =============================================================================
def generate_ur_charts(
    output_dict: dict,
    input_dict: dict,
    bridge: Any,
    out_dir: str
) -> Dict[str, str]:
    """
    Generate dynamic utilization ratio charts for:
    - Steel Plate Girders
    - Concrete Deck Slab
    - Cross Bracing
    - End Diaphragms
    Returns dict mapping chart key to file path.
    """
    chart_paths = {}

    # ─────────────────────────────────────────────────────────────────────────
    # A. Steel Plate Girders
    # ─────────────────────────────────────────────────────────────────────────
    try:
        girder_items = []
        design_results = output_dict.get("design_results", {})
        checks = design_results.get("checks", [])
        
        # If checks list exists in design_results
        if checks:
            for chk in checks:
                cid = chk.get("check_id")
                desc = chk.get("description") or f"Check {cid}"
                dcr = chk.get("dcr")
                if dcr is not None:
                    # Short clean label
                    lbl = desc.split("(")[0].strip()
                    girder_items.append((lbl, float(dcr)))
        
        # Fallback to category_urs or direct checking keys
        if not girder_items:
            cat_urs = design_results.get("category_urs", {})
            cat_map = [
                ("Flexure / Moment", "flexure"),
                ("Shear Resistance", "shear"),
                ("Lateral Torsional Buckling", "ltb"),
                ("Live Load Deflection", "deflection"),
                ("Service Stress", "stress"),
                ("Fatigue Range", "fatigue"),
                ("Web / Bearing Buckling", "stiffener"),
            ]
            for label, key in cat_map:
                val = cat_urs.get(key)
                if val is not None:
                    girder_items.append((label, float(val)))

        if not girder_items:
            # Fallback to key checks from output_dict
            f_ur = output_dict.get("steeldesign.dcr.flexure")
            s_ur = output_dict.get("steeldesign.dcr.shear")
            l_ur = output_dict.get("steeldesign.dcr.ltb")
            d_ur = output_dict.get("steeldesign.dcr.deflection")
            for lbl, v in [("Moment (Flexure)", f_ur), ("Shear Capacity", s_ur), ("LTB (Construction)", l_ur), ("Deflection", d_ur)]:
                if v is not None:
                    try:
                        girder_items.append((lbl, float(v)))
                    except Exception:
                        pass

        if girder_items:
            p = os.path.join(out_dir, "ur_chart_girders.png")
            if _draw_ur_bar_chart(girder_items, "Steel Plate Girder — Utilization Ratios", p):
                chart_paths["ur_girders"] = p
    except Exception as exc:
        logger.warning("Error generating girder UR chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # B. Concrete Deck Slab
    # ─────────────────────────────────────────────────────────────────────────
    try:
        from osdagbridge.core.utils.common import (
            KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT,
            KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP,
            KEY_DD_M_ULS_OH,  KEY_DD_MU_OH,
            KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA,
            KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
            KEY_DD_WK_LIMIT,  KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH,
            KEY_SD_TS_VL,     KEY_SD_TS_VRD,
        )
        dkv = output_dict.get("deck_report_values", {})
        deck_items = []

        def _add_dk(lbl, dem_k, cap_k):
            dem = dkv.get(dem_k)
            cap = dkv.get(cap_k)
            if dem is not None and cap is not None:
                try:
                    c_f = float(cap)
                    d_f = float(dem)
                    if c_f > 0:
                        deck_items.append((lbl, d_f / c_f))
                except Exception:
                    pass

        _add_dk("Flexure: Sagging Moment", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT)
        _add_dk("Flexure: Hogging Moment", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP)
        _add_dk("Cantilever Overhang",     KEY_DD_M_ULS_OH,  KEY_DD_MU_OH)
        _add_dk("Punching Shear",         KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA)
        _add_dk("One-Way Shear",          KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC)
        _add_dk("Transverse Shear",       KEY_SD_TS_VL,     KEY_SD_TS_VRD)

        # Crack width check
        wk_lim = dkv.get(KEY_DD_WK_LIMIT)
        wk_vals = [float(dkv[k]) for k in (KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH) if dkv.get(k) is not None]
        if wk_lim is not None and wk_vals:
            try:
                max_wk = max(wk_vals)
                lim_f = float(wk_lim)
                if lim_f > 0:
                    deck_items.append(("Crack Width (SLS)", max_wk / lim_f))
            except Exception:
                pass

        if deck_items:
            p = os.path.join(out_dir, "ur_chart_deck.png")
            if _draw_ur_bar_chart(deck_items, "Concrete Deck Slab — Utilization Ratios", p):
                chart_paths["ur_deck"] = p
    except Exception as exc:
        logger.warning("Error generating deck slab UR chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # C. Cross Bracing
    # ─────────────────────────────────────────────────────────────────────────
    try:
        cb_items = []
        if bridge is not None and hasattr(bridge, "get_cb_pairs"):
            pairs = bridge.get_cb_pairs()
            # Find governing efficiencies across all pairs
            best_diag_c = 0.0
            best_diag_t = 0.0
            best_chord_c = 0.0
            best_chord_t = 0.0
            best_diag_sl = 0.0
            best_chord_sl = 0.0

            for pair in pairs:
                for ft, var_c, var_t in [("compression", "best_diag_c", "best_diag_t")]:
                    eff = bridge.get_cb_efficiency(pair, "diagonal", "compression")
                    if eff:
                        best_diag_c = max(best_diag_c, float(eff))
                    eff_t = bridge.get_cb_efficiency(pair, "diagonal", "tension")
                    if eff_t:
                        best_diag_t = max(best_diag_t, float(eff_t))

                    eff_cc = bridge.get_cb_efficiency(pair, "chord", "compression")
                    if eff_cc:
                        best_chord_c = max(best_chord_c, float(eff_cc))
                    eff_ct = bridge.get_cb_efficiency(pair, "chord", "tension")
                    if eff_ct:
                        best_chord_t = max(best_chord_t, float(eff_ct))

                    s_d = bridge.get_cb_slenderness(pair, "diagonal")
                    if s_d:
                        best_diag_sl = max(best_diag_sl, float(s_d) / 250.0)
                    s_c = bridge.get_cb_slenderness(pair, "chord")
                    if s_c:
                        best_chord_sl = max(best_chord_sl, float(s_c) / 400.0)

            if best_diag_c > 0:
                cb_items.append(("Diagonal — Compression", best_diag_c))
            if best_diag_t > 0:
                cb_items.append(("Diagonal — Tension", best_diag_t))
            if best_chord_c > 0:
                cb_items.append(("Chord — Compression", best_chord_c))
            if best_chord_t > 0:
                cb_items.append(("Chord — Tension", best_chord_t))
            if best_diag_sl > 0:
                cb_items.append(("Diagonal — Slenderness (λ/250)", best_diag_sl))
            if best_chord_sl > 0:
                cb_items.append(("Chord — Slenderness (λ/400)", best_chord_sl))

        if cb_items:
            p = os.path.join(out_dir, "ur_chart_crossbracing.png")
            if _draw_ur_bar_chart(cb_items, "Cross Bracing — Utilization Ratios", p):
                chart_paths["ur_crossbracing"] = p
    except Exception as exc:
        logger.warning("Error generating cross bracing UR chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # D. End Diaphragms
    # ─────────────────────────────────────────────────────────────────────────
    try:
        ed_items = []
        # Check if end diaphragm results exist
        ed_results = output_dict.get("enddiaphragm_design_results", {})
        if ed_results and bridge is not None:
            # End diaphragm is designed as bracing or beam
            ed_pairs = sorted(ed_results.keys())
            max_eff_c = 0.0
            max_eff_t = 0.0
            max_eff_chord_c = 0.0
            max_eff_chord_t = 0.0
            for pair, pdata in ed_results.items():
                if isinstance(pdata, dict):
                    diag = pdata.get("diagonal", {})
                    c_eff = (diag.get("compression") or {}).get("efficiency")
                    t_eff = (diag.get("tension") or {}).get("efficiency")
                    if c_eff is not None:
                        max_eff_c = max(max_eff_c, float(c_eff))
                    if t_eff is not None:
                        max_eff_t = max(max_eff_t, float(t_eff))

                    chord = pdata.get("chord", {})
                    cc_eff = (chord.get("compression") or {}).get("efficiency")
                    ct_eff = (chord.get("tension") or {}).get("efficiency")
                    if cc_eff is not None:
                        max_eff_chord_c = max(max_eff_chord_c, float(cc_eff))
                    if ct_eff is not None:
                        max_eff_chord_t = max(max_eff_chord_t, float(ct_eff))

            if max_eff_c > 0:
                ed_items.append(("End Diaphragm: Diag. Compression", max_eff_c))
            if max_eff_t > 0:
                ed_items.append(("End Diaphragm: Diag. Tension", max_eff_t))
            if max_eff_chord_c > 0:
                ed_items.append(("End Diaphragm: Chord Compression", max_eff_chord_c))
            if max_eff_chord_t > 0:
                ed_items.append(("End Diaphragm: Chord Tension", max_eff_chord_t))

        if ed_items:
            p = os.path.join(out_dir, "ur_chart_diaphragms.png")
            if _draw_ur_bar_chart(ed_items, "End Diaphragms — Utilization Ratios", p):
                chart_paths["ur_diaphragms"] = p
    except Exception as exc:
        logger.warning("Error generating end diaphragm UR chart: %s", exc)

    return chart_paths


# =============================================================================
# 2. MATERIAL QUANTITY CHARTS GENERATOR
# =============================================================================
def generate_quantity_charts(
    quantities: dict,
    out_dir: str
) -> Dict[str, str]:
    """
    Generate dynamic material quantity charts for Chapter 7:
    1. Structural Steel Tonnage Breakdown (Girders, Cross Bracing, End Diaphragms) in MT
    2. Concrete Volume (m³) and Reinforcement Steel Weight (MT)
    Returns dict mapping chart key to file path.
    """
    chart_paths = {}
    configure_plot_style()

    def _safe_float(val, default=0.0):
        if val in (None, "", "N.A."):
            return default
        try:
            return float(str(val).replace(",", "").strip())
        except Exception:
            return default

    # ─────────────────────────────────────────────────────────────────────────
    # A. Structural Steel Tonnage Breakdown
    # ─────────────────────────────────────────────────────────────────────────
    try:
        wt_girders = _safe_float(quantities.get("steel_girders_wt_total"))
        wt_top = _safe_float(quantities.get("bracing_top_wt_total"))
        wt_bot = _safe_float(quantities.get("bracing_bot_wt_total"))
        wt_diag = _safe_float(quantities.get("bracing_diag_wt_total"))
        wt_bracing = wt_top + wt_bot + wt_diag
        wt_ed = _safe_float(quantities.get("steel_ed_wt_total"))
        raw_steel = [quantities.get(k) for k in (
            "steel_girders_wt_total", "bracing_top_wt_total", "bracing_bot_wt_total",
            "bracing_diag_wt_total", "steel_ed_wt_total")]
        steel_data_complete = all(v not in (None, "", "N.A.") for v in raw_steel)

        steel_labels = ["Steel Girders", "Cross Bracing", "End Diaphragms"]
        steel_tonnages = [wt_girders, wt_bracing, wt_ed]
        total_steel = sum(steel_tonnages)

        if steel_data_complete and total_steel > 0:
            fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=300)
            colors = [COLOR_OSDAG_GREEN, "#2980B9", "#8E44AD"]
            bars = ax.bar(steel_labels, steel_tonnages, color=colors, edgecolor=COLOR_BORDER, width=0.48, zorder=3)

            ax.set_ylabel("Structural Steel Weight (MT)", fontsize=9.5, fontweight="bold", labelpad=6)
            ax.set_title(f"Structural Steel Tonnage Breakdown (Total: {total_steel:.2f} MT)", fontsize=10.5, fontweight="bold", pad=10)
            ax.set_ylim(0, max(steel_tonnages) * 1.22)
            ax.grid(axis='y', linestyle='--', alpha=0.5, color=COLOR_GRID, zorder=0)
            ax.set_axisbelow(True)

            # Value labels on bars
            for bar, val in zip(bars, steel_tonnages):
                pct = (val / total_steel) * 100.0 if total_steel > 0 else 0.0
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + (max(steel_tonnages) * 0.03),
                    f"{val:.2f} MT\n({pct:.1f}%)",
                    ha='center',
                    va='bottom',
                    fontsize=8.5,
                    fontweight='bold',
                    color="#2C3E50"
                )

            plt.tight_layout()
            p1 = os.path.join(out_dir, "material_steel_tonnage.png")
            fig.savefig(p1, dpi=300, bbox_inches='tight')
            plt.close(fig)
            chart_paths["steel_tonnage"] = p1
    except Exception as exc:
        logger.warning("Error generating steel tonnage chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # B. Concrete volume and reinforcement weight (separate axes/units)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        deck_raw = quantities.get("concrete_deck_vol_total")
        barrier_raw = quantities.get("crash_barrier_vol_total")
        rebar_raw = quantities.get("rebar_deck_wt_total")
        concrete_items = []
        if deck_raw not in (None, "", "N.A."):
            concrete_items.append(("Concrete Deck", _safe_float(deck_raw)))
        if barrier_raw not in (None, "", "N.A."):
            concrete_items.append(("Crash Barrier", _safe_float(barrier_raw)))
        rebar_value = _safe_float(rebar_raw) if rebar_raw not in (None, "", "N.A.") else None

        if concrete_items or rebar_value is not None:
            fig, (ax_conc, ax_rebar) = plt.subplots(1, 2, figsize=(7.2, 3.5), dpi=300)
            if concrete_items:
                labels = [item[0] for item in concrete_items]
                values = [item[1] for item in concrete_items]
                bars = ax_conc.bar(labels, values, color=CHART_PALETTE[:len(values)],
                                   edgecolor=COLOR_BORDER, width=0.52, zorder=3)
                ax_conc.set_ylabel("Concrete Volume (m³)", fontsize=9, fontweight="bold")
                ax_conc.set_title("Concrete", fontsize=10, fontweight="bold")
                ax_conc.grid(axis="y", linestyle="--", alpha=0.5, color=COLOR_GRID, zorder=0)
                ax_conc.set_axisbelow(True)
                for bar, val in zip(bars, values):
                    ax_conc.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                 f"{val:.2f} m³", ha="center", va="bottom", fontsize=8)
            else:
                ax_conc.set_visible(False)
            if rebar_value is not None:
                bars = ax_rebar.bar(["Reinforcement"], [rebar_value], color=[CHART_PALETTE[3]],
                                    edgecolor=COLOR_BORDER, width=0.52, zorder=3)
                ax_rebar.set_ylabel("Reinforcement Steel Weight (MT)", fontsize=9, fontweight="bold")
                ax_rebar.set_title("Reinforcement Steel", fontsize=10, fontweight="bold")
                ax_rebar.grid(axis="y", linestyle="--", alpha=0.5, color=COLOR_GRID, zorder=0)
                ax_rebar.set_axisbelow(True)
                ax_rebar.text(bars[0].get_x() + bars[0].get_width()/2, bars[0].get_height(),
                              f"{rebar_value:.2f} MT", ha="center", va="bottom", fontsize=8)
            else:
                ax_rebar.set_visible(False)
            fig.suptitle("Concrete and Reinforcement Quantities", fontsize=10.5, fontweight="bold")
            plt.tight_layout()
            p2 = os.path.join(out_dir, "material_concrete_rebar.png")
            fig.savefig(p2, dpi=300, bbox_inches="tight")
            plt.close(fig)
            chart_paths["materials_summary"] = p2
    except Exception as exc:
        logger.warning("Error generating concrete/rebar quantity chart: %s", exc)

    return chart_paths
