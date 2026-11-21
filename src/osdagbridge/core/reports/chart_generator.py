"""Programmatic chart generator for OsdagBridge design reports.

Generates:
1. Utilization Ratio (UR) summary charts for Section 5.5:
   - Steel Plate Girders
   - Concrete Deck Slab
   - Cross Bracing
   - End Diaphragms
   - Marked with red dashed threshold line at UR = 1.0.
   - Clear identification of PASS, FAIL, and NOT CALCULATED.
2. Material quantity charts for Chapter 7:
   - Structural steel tonnage breakdown by component (MT).
   - Separate concrete volume (m³) and reinforcement steel weight (MT) visualizations
     to prevent misleading comparisons across different physical units.
"""

import os
import logging
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .styles import (
    COLOR_OSDAG_GREEN,
    COLOR_PASS,
    COLOR_FAIL,
    COLOR_THRESHOLD,
    COLOR_UNAVAILABLE,
    COLOR_ACCENT,
    COLOR_GRID,
    CHART_DPI,
    CHART_FIGSIZE_SUMMARY,
    CHART_FIGSIZE_WIDE,
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
)

logger = logging.getLogger(__name__)


def generate_ur_charts(bridge: Any, output_dir: str) -> Dict[str, str]:
    """Programmatically generate Utilization Ratio charts for Section 5.5.
    
    Generates a high-resolution 4-panel figure covering:
    - Steel Plate Girders (per-girder controlling check UR)
    - Concrete Deck Slab (flexure sagging/hogging, overhang, punching, crack width)
    - Cross Bracing (compression, tension, slenderness)
    - End Diaphragms (compression, tension, slenderness)
    """
    os.makedirs(output_dir, exist_ok=True)
    chart_filename = "ur_summary_chart.png"
    chart_path = os.path.join(output_dir, chart_filename)

    # ── 1. Gather Girder UR data ──────────────────────────────────────────
    dr = bridge.output_dict.get("design_results", {}) or {}
    pg = dr.get("per_girder", {}) or {}
    girder_labels = []
    girder_urs = []

    for k in sorted(pg.keys()):
        if str(k).startswith("EB"):
            continue
        g_data = pg.get(k, {}) or {}
        checks = g_data.get("checks") or []
        if checks:
            ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
            dcr = ctrl.get("dcr")
            girder_labels.append(f"{k}\n({ctrl.get('name', 'Check')[:10]})")
            girder_urs.append(float(dcr) if dcr is not None else None)
        else:
            girder_labels.append(str(k))
            girder_urs.append(None)

    if not girder_labels:
        girder_labels = ["G1", "G2"]
        girder_urs = [None, None]

    # ── 2. Gather Deck Slab UR data ───────────────────────────────────────
    deck_rpt = bridge.output_dict.get("deck_report", {}) or {}
    
    def _calc_deck_ur(demand_key, cap_key):
        try:
            d = float(deck_rpt.get(demand_key, 0) or 0)
            c = float(deck_rpt.get(cap_key, 0) or 0)
            if c > 0 and d > 0:
                return round(d / c, 3)
        except (TypeError, ValueError):
            pass
        return None

    def _calc_deck_wk():
        try:
            wks = [
                float(deck_rpt.get(KEY_DD_WK_BOT, 0) or 0),
                float(deck_rpt.get(KEY_DD_WK_TOP, 0) or 0),
                float(deck_rpt.get(KEY_DD_WK_OH, 0) or 0),
            ]
            gov_wk = max(wks)
            lim_wk = float(deck_rpt.get(KEY_DD_WK_LIMIT, 0) or 0)
            if lim_wk > 0 and gov_wk > 0:
                return round(gov_wk / lim_wk, 3)
        except (TypeError, ValueError):
            pass
        return None

    deck_labels = ["Flexure\n(Sagging)", "Flexure\n(Hogging)", "Cantilever\nOverhang", "Punching\nShear", "Crack\nWidth"]
    deck_urs = [
        _calc_deck_ur(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
        _calc_deck_ur(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
        _calc_deck_ur(KEY_DD_M_ULS_OH,  KEY_DD_MU_OH),
        _calc_deck_ur(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
        _calc_deck_wk(),
    ]

    # ── 3. Gather Cross Bracing UR data ───────────────────────────────────
    cb_labels = ["Compression", "Tension", "Slenderness"]
    cb_pairs = getattr(bridge, 'get_cb_pairs', lambda: [])()
    cb_comp_ur = None
    cb_tens_ur = None
    cb_slen_ur = None
    if cb_pairs:
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                c_eff = bridge.get_cb_efficiency(pair, member, "compression")
                if c_eff is not None:
                    try:
                        cb_comp_ur = max(cb_comp_ur or 0.0, float(c_eff))
                    except (ValueError, TypeError):
                        pass
                t_eff = bridge.get_cb_efficiency(pair, member, "tension")
                if t_eff is not None:
                    try:
                        cb_tens_ur = max(cb_tens_ur or 0.0, float(t_eff))
                    except (ValueError, TypeError):
                        pass
                s = bridge.get_cb_slenderness(pair, member)
                if s is not None:
                    try:
                        lim = 400.0 if member == "chord" else 250.0
                        ratio = float(s) / lim
                        cb_slen_ur = max(cb_slen_ur or 0.0, ratio)
                    except (ValueError, TypeError):
                        pass
    cb_urs = [cb_comp_ur, cb_tens_ur, cb_slen_ur]

    # ── 4. Gather End Diaphragm UR data ───────────────────────────────────
    ed_labels = ["Compression", "Tension", "Slenderness"]
    ed_pairs = getattr(bridge, 'get_ed_pairs', lambda: [])()
    ed_comp_ur = None
    ed_tens_ur = None
    ed_slen_ur = None
    if ed_pairs:
        for pair in ed_pairs:
            for member in ("diagonal", "chord"):
                c_eff = bridge.get_ed_efficiency(pair, member, "compression")
                if c_eff is not None:
                    try:
                        ed_comp_ur = max(ed_comp_ur or 0.0, float(c_eff))
                    except (ValueError, TypeError):
                        pass
                t_eff = bridge.get_ed_efficiency(pair, member, "tension")
                if t_eff is not None:
                    try:
                        ed_tens_ur = max(ed_tens_ur or 0.0, float(t_eff))
                    except (ValueError, TypeError):
                        pass
                s = bridge.get_ed_slenderness(pair, member)
                if s is not None:
                    try:
                        lim = 400.0 if member == "chord" else 250.0
                        ratio = float(s) / lim
                        ed_slen_ur = max(ed_slen_ur or 0.0, ratio)
                    except (ValueError, TypeError):
                        pass
    ed_urs = [ed_comp_ur, ed_tens_ur, ed_slen_ur]

    # ── Plotting 2x2 Subplots ─────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=CHART_FIGSIZE_SUMMARY, dpi=CHART_DPI)
    panels = [
        (axes[0, 0], "Steel Plate Girders", girder_labels, girder_urs),
        (axes[0, 1], "Concrete Deck Slab", deck_labels, deck_urs),
        (axes[1, 0], "Cross Bracing", cb_labels, cb_urs),
        (axes[1, 1], "End Diaphragms", ed_labels, ed_urs),
    ]

    for ax, title, labels, values in panels:
        x_pos = list(range(len(labels)))
        max_val = 1.0

        for idx, (lbl, val) in enumerate(zip(labels, values)):
            if val is not None:
                max_val = max(max_val, val)
                if val <= 1.0:
                    bar_color = COLOR_PASS
                    status_text = f"{val:.2f}\n(PASS)"
                else:
                    bar_color = COLOR_FAIL
                    status_text = f"{val:.2f}\n(FAIL)"

                ax.bar(idx, val, color=bar_color, width=0.55, edgecolor="black", linewidth=0.7)
                ax.text(idx, val + 0.05, status_text, ha='center', va='bottom', fontsize=8, fontweight='bold', color=bar_color)
            else:
                # Missing / unavailable check: draw distinct hatched placeholder, NOT zero or pass
                ax.bar(idx, 0.08, color="#f0f0f0", hatch='///', edgecolor=COLOR_UNAVAILABLE, width=0.55, linewidth=0.8)
                ax.text(idx, 0.12, "NOT\nCALCULATED", ha='center', va='bottom', fontsize=7.5, fontstyle='italic', color="#555555")

        # Formatting
        ax.axhline(1.0, color=COLOR_THRESHOLD, linestyle='--', linewidth=1.2, label='Limit (UR = 1.0)')
        ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
        ax.set_ylabel("Utilization Ratio", fontsize=9)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylim(0, max(1.4, max_val * 1.35))
        ax.grid(axis='y', linestyle=':', color=COLOR_GRID, alpha=0.7)
        ax.legend(loc='upper right', fontsize=8, framealpha=0.85)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=CHART_DPI, bbox_inches='tight')
    plt.close(fig)

    return {"ur_summary": chart_path}


def generate_material_quantity_charts(inputs: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """Programmatically generate BOQ Material Quantity charts for Chapter 7.
    
    Generates:
    1. Structural steel tonnage breakdown (MT) by component.
    2. Deck materials summary with separate subplots for Concrete Volume (m³)
       and Reinforcement Steel Weight (MT) to strictly avoid misleading comparisons.
    """
    os.makedirs(output_dir, exist_ok=True)
    steel_path = os.path.join(output_dir, "steel_tonnage_breakdown.png")
    deck_mat_path = os.path.join(output_dir, "materials_deck_summary.png")

    # ── 1. Structural Steel Tonnage Breakdown ──────────────────────────────
    def _parse_val(k):
        try:
            v = inputs.get(k)
            if v not in (None, "", "N.A."):
                return float(v)
        except (ValueError, TypeError):
            pass
        return 0.0

    wt_girders = _parse_val("steel_girders_wt_total")
    wt_cb_top  = _parse_val("bracing_top_wt_total")
    wt_cb_bot  = _parse_val("bracing_bot_wt_total")
    wt_cb_diag = _parse_val("bracing_diag_wt_total")
    wt_cb_all  = wt_cb_top + wt_cb_bot + wt_cb_diag
    wt_ed      = _parse_val("end_diaphragm_wt_total")
    wt_studs   = _parse_val("shear_studs_wt_total")

    steel_items = [
        ("Plate Girders", wt_girders),
        ("Cross Bracing", wt_cb_all),
        ("End Diaphragms", wt_ed),
        ("Shear Studs", wt_studs),
    ]

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_WIDE, dpi=CHART_DPI)
    names = [item[0] for item in steel_items]
    weights = [item[1] for item in steel_items]
    x_pos = range(len(names))

    bars = ax.bar(x_pos, weights, color=COLOR_ACCENT, width=0.55, edgecolor="black", linewidth=0.7)

    for bar, wt in zip(bars, weights):
        if wt > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, wt + max(weights) * 0.02,
                    f"{wt:.2f} MT", ha='center', va='bottom', fontsize=9, fontweight='bold')
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, max(weights) * 0.02 if weights and max(weights) > 0 else 0.5,
                    "N.A. / 0.0", ha='center', va='bottom', fontsize=8, fontstyle='italic', color="#666666")

    total_steel = sum(weights)
    ax.set_title(f"Structural Steel Take-off by Component (Total = {total_steel:.2f} MT)", fontsize=11, fontweight='bold', pad=10)
    ax.set_ylabel("Weight (MT)", fontsize=10)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, fontsize=9.5)
    ax.set_ylim(0, max(weights) * 1.25 if weights and max(weights) > 0 else 10)
    ax.grid(axis='y', linestyle=':', color=COLOR_GRID, alpha=0.7)

    plt.tight_layout()
    plt.savefig(steel_path, dpi=CHART_DPI, bbox_inches='tight')
    plt.close(fig)

    # ── 2. Deck Materials: Separate Concrete (m³) & Rebar (MT) Visualizations ───
    vol_concrete = _parse_val("concrete_deck_vol_total")
    wt_rebar     = _parse_val("rebar_deck_wt_total")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=CHART_FIGSIZE_WIDE, dpi=CHART_DPI)

    # Left subplot: Concrete Volume (m³)
    bar1 = ax1.bar(["Deck Slab\nConcrete"], [vol_concrete], color="#ff7f0e", width=0.45, edgecolor="black", linewidth=0.7)
    if vol_concrete > 0:
        ax1.text(0, vol_concrete + vol_concrete * 0.03, f"{vol_concrete:.2f} m³", ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    ax1.set_title("Concrete Material Volume", fontsize=10.5, fontweight='bold', pad=8)
    ax1.set_ylabel("Volume (m³)", fontsize=10)
    ax1.set_ylim(0, vol_concrete * 1.25 if vol_concrete > 0 else 10)
    ax1.grid(axis='y', linestyle=':', color=COLOR_GRID, alpha=0.7)

    # Right subplot: Reinforcement Steel Weight (MT)
    bar2 = ax2.bar(["Deck Slab\nRebar (Fe 500)"], [wt_rebar], color="#2ca02c", width=0.45, edgecolor="black", linewidth=0.7)
    if wt_rebar > 0:
        ax2.text(0, wt_rebar + wt_rebar * 0.03, f"{wt_rebar:.2f} MT", ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    ax2.set_title("Reinforcement Steel Weight", fontsize=10.5, fontweight='bold', pad=8)
    ax2.set_ylabel("Weight (MT)", fontsize=10)
    ax2.set_ylim(0, wt_rebar * 1.25 if wt_rebar > 0 else 5)
    ax2.grid(axis='y', linestyle=':', color=COLOR_GRID, alpha=0.7)

    plt.tight_layout()
    plt.savefig(deck_mat_path, dpi=CHART_DPI, bbox_inches='tight')
    plt.close(fig)

    return {
        "boq_steel_tonnage": steel_path,
        "boq_materials": deck_mat_path,
    }
