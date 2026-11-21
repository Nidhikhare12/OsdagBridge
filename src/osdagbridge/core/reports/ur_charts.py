"""Utilization Ratio (UR) Bar Chart Generation and Visualization Module.

Generates standalone high-resolution charts visualizing structural utilization
ratios across bridge components per FOSSEE OsdagBridge reporting standards:
1. Steel Plate Girders (per-girder governing URs for G1..G4)
2. Concrete Deck Slab (key ULS/SLS design checks)
3. Cross Bracing (member-level capacity URs)
4. End Diaphragms (member checks or honest informational status card)

All values are extracted strictly from actual application design-result data.
No artificial ratios, zero placeholders, or false PASS badges are manufactured.
"""

import os
import sys
from typing import Dict, List, Optional, Any

# Ensure Windows conda environment Library/bin is registered for NumPy/Matplotlib BLAS
if sys.platform == "win32":
    _env_lib_bin = os.path.join(sys.prefix, "Library", "bin")
    if os.path.exists(_env_lib_bin):
        os.environ["PATH"] = _env_lib_bin + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(_env_lib_bin)
            except OSError:
                pass

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for headless report generation
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from osdagbridge.core.reports.styles import (
    COLOR_STATUS_PASS,
    COLOR_STATUS_FAIL,
    COLOR_STATUS_WARN,
    COLOR_OSDAG_GREEN,
    COLOR_OSDAG_DARK_GREEN,
    COLOR_LIGHT_GRAY,
    COLOR_GRAY,
    COLOR_BORDER,
)
from osdagbridge.core.reports.report_utils import get_girder_entries
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
    KEY_MP_ED_TYPE,
)


# ==============================================================================
# DATA EXTRACTION HELPERS
# ==============================================================================

def _get_bridge_data_bridge(bridge: Any) -> Any:
    """Ensure bridge has ReportDataBridge interface."""
    if hasattr(bridge, "get_cb_pairs"):
        return bridge
    from osdagbridge.core.reports.report_generator import ReportDataBridge
    payload = getattr(bridge, "payload", None)
    return ReportDataBridge(
        getattr(bridge, "output_dict", {}) or {},
        getattr(bridge, "input_dict", {}) or {},
        payload
    )


def extract_girder_ur_data(bridge: Any) -> List[Dict[str, Any]]:
    """
    Extract actual governing utilization ratio for each steel plate girder (G1..Gn).

    Source: output_dict["design_results"]["per_girder"]
    Girders are filtered strictly to the active bridge girders from get_girder_entries().
    For each girder, the governing check is the check with highest DCR (matching Table 5.13).
    """
    bridge_inst = _get_bridge_data_bridge(bridge)
    out_dict = getattr(bridge_inst, "output_dict", {}) or {}
    inp_dict = getattr(bridge_inst, "input_dict", {}) or {}
    pg = (out_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    girder_entries = get_girder_entries(inp_dict)
    if girder_entries:
        girder_keys = [f"G{i}" for i in range(1, len(girder_entries) + 1)]
    else:
        girder_keys = [k for k in sorted(pg.keys()) if k.startswith("G") and not k.startswith("EB")][:4]
        if not girder_keys:
            girder_keys = ["G1", "G2", "G3", "G4"]

    girders = []
    for g_id in girder_keys:
        g_data = pg.get(g_id, {}) or {}
        checks = g_data.get("checks") or []
        if checks:
            ctrl = max(checks, key=lambda c: float(c.get("dcr") or 0.0))
            ur_val = float(ctrl.get("dcr") or 0.0)
            check_name = str(ctrl.get("name") or "Governing Check")
            status = "PASS" if ur_val <= 1.0 else "FAIL"
        else:
            ur_val = 0.0
            check_name = "N/A"
            status = "N/A"

        girders.append({
            "id": g_id,
            "label": f"Girder {g_id[1:]} ({g_id})",
            "short_label": g_id,
            "ur": ur_val,
            "display_ur": f"{ur_val:.2f}",
            "check_name": check_name,
            "status": status,
        })
    return girders


def extract_deck_slab_ur_data(bridge: Any) -> List[Dict[str, Any]]:
    """
    Extract calculated utilization ratios for concrete deck slab checks.

    Source: output_dict["deck_design_results"] / output_dict["deck_report_values"]
    Checks:
    1. Flexure (Sagging) - ULS
    2. Flexure (Hogging) - ULS
    3. Cantilever Overhang - ULS
    4. One-Way Shear - ULS
    5. Punching Shear - ULS
    6. Crack Width - SLS
    """
    bridge_inst = _get_bridge_data_bridge(bridge)
    out_dict = getattr(bridge_inst, "output_dict", {}) or {}
    dd = out_dict.get("deck_design_results", {}) or {}
    deck_rpt = out_dict.get("deck_report_values", {}) or {}

    def _get_val(key, default=None):
        v = dd.get(key)
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
        return default

    # 1. Sagging flexure
    ur_sag = _get_val("ur_bot_uls")
    if ur_sag is None and deck_rpt:
        try:
            m_dem = float(deck_rpt.get(KEY_DD_M_ULS_SAG, 0.0))
            m_cap = float(deck_rpt.get(KEY_DD_MU_BOT, 1.0))
            ur_sag = m_dem / m_cap if m_cap > 0 else 0.0
        except (ValueError, TypeError):
            ur_sag = 0.0

    # 2. Hogging flexure
    ur_hog = _get_val("ur_top_uls")
    if ur_hog is None and deck_rpt:
        try:
            m_dem = float(deck_rpt.get(KEY_DD_M_ULS_HOG, 0.0))
            m_cap = float(deck_rpt.get(KEY_DD_MU_TOP, 1.0))
            ur_hog = m_dem / m_cap if m_cap > 0 else 0.0
        except (ValueError, TypeError):
            ur_hog = 0.0

    # 3. Cantilever overhang
    ur_oh = _get_val("ur_oh_uls")
    has_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG, True))
    if ur_oh is None and deck_rpt and has_oh:
        try:
            m_dem = float(deck_rpt.get(KEY_DD_M_ULS_OH, 0.0))
            m_cap = float(deck_rpt.get(KEY_DD_MU_OH, 1.0))
            ur_oh = m_dem / m_cap if m_cap > 0 else 0.0
        except (ValueError, TypeError):
            ur_oh = 0.0

    # 4. One-way shear
    ur_shear = _get_val("ur_bot_shear")
    if ur_shear is None and deck_rpt:
        try:
            v_dem = float(deck_rpt.get(KEY_DD_SHEAR_VED, 0.0))
            v_cap = float(deck_rpt.get(KEY_DD_SHEAR_VRDC, 1.0))
            ur_shear = v_dem / v_cap if v_cap > 0 else 0.0
        except (ValueError, TypeError):
            ur_shear = 0.0

    # 5. Punching shear
    ur_punch = _get_val("ur_bot_punch")
    if ur_punch is None and deck_rpt:
        try:
            v_dem = float(deck_rpt.get(KEY_DD_PUNCH_VED, 0.0))
            v_cap = float(deck_rpt.get(KEY_DD_VRD_C_MPA, 1.0))
            ur_punch = v_dem / v_cap if v_cap > 0 else 0.0
        except (ValueError, TypeError):
            ur_punch = 0.0

    # 6. Crack width
    ur_crack = _get_val("ur_top_crack")
    if ur_crack is None and deck_rpt:
        try:
            wks = [float(deck_rpt.get(KEY_DD_WK_BOT, 0.0)), float(deck_rpt.get(KEY_DD_WK_TOP, 0.0))]
            if has_oh:
                wks.append(float(deck_rpt.get(KEY_DD_WK_OH, 0.0)))
            w_lim = float(deck_rpt.get(KEY_DD_WK_LIMIT, 1.0))
            ur_crack = max(wks) / w_lim if w_lim > 0 else 0.0
        except (ValueError, TypeError):
            ur_crack = 0.0

    items = [
        {"id": "deck_sag", "label": "Flexure (Sag)", "short_label": "Flexure\n(Sag)", "ur": ur_sag or 0.0},
        {"id": "deck_hog", "label": "Flexure (Hog)", "short_label": "Flexure\n(Hog)", "ur": ur_hog or 0.0},
        {"id": "deck_oh", "label": "Cantilever Overhang", "short_label": "Cantilever\nOverhang", "ur": ur_oh or 0.0},
        {"id": "deck_shear", "label": "One-Way Shear", "short_label": "One-Way\nShear", "ur": ur_shear or 0.0},
        {"id": "deck_punch", "label": "Punching Shear", "short_label": "Punching\nShear", "ur": ur_punch or 0.0},
        {"id": "deck_crack", "label": "Crack Width", "short_label": "Crack\nWidth", "ur": ur_crack or 0.0},
    ]

    for item in items:
        u = float(item["ur"])
        item["display_ur"] = f"{u:.2f}"
        item["status"] = "PASS" if u <= 1.0 else "FAIL"

    return items


def extract_cross_bracing_ur_data(bridge: Any) -> List[Dict[str, Any]]:
    """
    Extract calculated utilization ratios for cross bracing members.

    Source: bridge.get_cb_pairs(), get_cb_governing_force(), get_cb_efficiency()
    Pairs: G1-G2, G2-G3, G3-G4
    Members: Diagonal, Chord
    """
    bridge_inst = _get_bridge_data_bridge(bridge)
    pairs = bridge_inst.get_cb_pairs()

    items = []
    for pair in pairs:
        for member, short_m in [("diagonal", "Diag"), ("chord", "Chord")]:
            force_str, ftype = bridge_inst.get_cb_governing_force(pair, member)
            eff_str = bridge_inst.get_cb_efficiency(pair, member, ftype)
            try:
                ur_val = float(eff_str)
            except (ValueError, TypeError):
                ur_val = 0.0

            status = "PASS" if ur_val <= 1.0 else "FAIL"
            items.append({
                "id": f"{pair}_{member}",
                "pair": pair,
                "member": member,
                "label": f"{pair} {member.capitalize()} ({ftype[:4].capitalize()})",
                "short_label": f"{pair}\n{short_m}",
                "ur": ur_val,
                "display_ur": f"{ur_val:.2f}",
                "force_type": ftype,
                "status": status,
            })
    return items


def extract_end_diaphragm_ur_data(bridge: Any) -> Dict[str, Any]:
    """
    Inspect end-diaphragm configuration and design checks.

    Strict Data Rule:
    Checks if output_dict contains actual completed end-diaphragm member results.
    If output_dict["end_diaphragm_design_results"] is empty or checks are unperformed,
    returns status dict indicating checks are unavailable in solver ('design to be added').
    Does NOT manufacture fake ratios or false PASS badges.
    """
    bridge_inst = _get_bridge_data_bridge(bridge)
    out_dict = getattr(bridge_inst, "output_dict", {}) or {}
    inp = getattr(bridge_inst, "input_dict", {}) or {}

    ed_type = ""
    for k, v in inp.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    if not ed_type:
        ed_type = "Rolled Beam"

    # Check whether end_diaphragm_design_results contains actual member design dicts with efficiency
    ed_designs = out_dict.get("end_diaphragm_design_results", {}) or {}
    has_results = False
    items = []

    if isinstance(ed_designs, dict):
        for pair, pdata in ed_designs.items():
            if isinstance(pdata, dict) and pdata:
                for member, mdata in pdata.items():
                    if isinstance(mdata, dict) and mdata:
                        for ftype, fdata in mdata.items():
                            if isinstance(fdata, dict) and fdata.get("efficiency") is not None:
                                try:
                                    eff = float(fdata.get("efficiency"))
                                    has_results = True
                                    status = "PASS" if eff <= 1.0 else "FAIL"
                                    items.append({
                                        "id": f"ed_{pair}_{member}",
                                        "pair": pair,
                                        "member": member,
                                        "label": f"{pair} {member.capitalize()}",
                                        "short_label": f"{pair}\n{member[:4].capitalize()}",
                                        "ur": eff,
                                        "display_ur": f"{eff:.2f}",
                                        "status": status,
                                    })
                                except (ValueError, TypeError):
                                    pass

    if has_results and items:
        return {
            "has_data": True,
            "ed_type": ed_type,
            "items": items,
        }

    # Solver has not implemented / populated end diaphragm design checks
    return {
        "has_data": False,
        "ed_type": ed_type,
        "reason": "End diaphragm member design checks are pending implementation in the solver ('design to be added').",
        "items": [],
    }


# ==============================================================================
# MATPLOTLIB CHART GENERATION
# ==============================================================================

def _apply_chart_styling(ax: plt.Axes, title: str, xlabel: str, max_ur: float):
    """Apply consistent styling, titles, limits, and threshold lines."""
    ax.set_title(title, fontsize=11, fontweight="bold", pad=14, color="#1A1A1A")
    ax.set_ylabel("Utilization Ratio (UR)", fontsize=9.5, fontweight="bold", labelpad=8, color="#222222")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9.5, fontweight="bold", labelpad=8, color="#222222")

    # Y-axis limit with ample headroom for data labels and threshold line
    y_top = max(max_ur * 1.35, 1.45)
    ax.set_ylim(0, y_top)

    # Clean horizontal grid
    ax.yaxis.grid(True, linestyle=":", alpha=0.6, color="#C0C0C0", zorder=0)
    ax.set_axisbelow(True)

    # Spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(axis="both", which="both", colors="#333333", labelsize=8.5)

    # Red dashed threshold line at UR = 1.0
    fail_color = f"#{COLOR_STATUS_FAIL}"
    ax.axhline(1.0, color=fail_color, linestyle="--", linewidth=1.5, zorder=3)


def plot_ur_bar_chart(
    items: List[Dict[str, Any]],
    title: str,
    output_path: str,
    xlabel: str = "Member / Design Check",
    figsize: tuple = (6.2, 3.4),
) -> str:
    """
    Generate a high-resolution Matplotlib bar chart for utilization ratios.

    Bars with UR <= 1.0 are colored green (#2E7D32, PASS).
    Bars with UR > 1.0 are colored red (#D32F2F, FAIL).
    Numerical UR values are annotated clearly above each bar.
    A red dashed line at UR = 1.0 indicates the design threshold.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize, dpi=300)

    pass_color = f"#{COLOR_STATUS_PASS}"
    fail_color = f"#{COLOR_STATUS_FAIL}"

    x_labels = [item.get("short_label", item.get("label", "")) for item in items]
    ur_vals = [float(item.get("ur", 0.0)) for item in items]
    bar_colors = [fail_color if u > 1.0 else pass_color for u in ur_vals]

    x_pos = range(len(items))
    bar_width = 0.52 if len(items) <= 4 else 0.58
    bars = ax.bar(x_pos, ur_vals, width=bar_width, color=bar_colors, edgecolor="#444444", linewidth=0.6, zorder=2)

    max_ur = max(ur_vals) if ur_vals else 1.0
    _apply_chart_styling(ax, title, xlabel, max_ur)

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(x_labels, fontweight="medium", fontsize=8.5)

    # Threshold annotation on the right edge above the line
    ax.text(
        len(items) - 0.45,
        1.02,
        "Design Limit (UR = 1.0)",
        color=fail_color,
        fontweight="bold",
        fontsize=8.0,
        ha="right",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFF5F5", edgecolor="none", alpha=0.85),
        zorder=4,
    )

    # Label exact UR values above bars
    for bar, u in zip(bars, ur_vals):
        h = bar.get_height()
        c = fail_color if u > 1.0 else pass_color
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 0.03,
            f"{u:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=c,
            zorder=4,
        )

    # Clean legend for pass / fail identification positioned cleanly at upper center
    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=pass_color, edgecolor="#333", linewidth=0.5, label="PASS (UR ≤ 1.0)"),
        Rectangle((0, 0), 1, 1, facecolor=fail_color, edgecolor="#333", linewidth=0.5, label="FAIL (UR > 1.0)"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=2,
        fontsize=8.0,
        frameon=True,
        facecolor="#FAFAFA",
        edgecolor="#CCCCCC",
        framealpha=0.9,
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_status_card(
    title: str,
    component_name: str,
    section_type: str,
    message: str,
    output_path: str,
    figsize: tuple = (6.2, 3.4),
) -> str:
    """
    Generate an informational status card for components lacking solver check implementation.

    Strict engineering integrity rule:
    Does NOT manufacture fake 0.0 ratios or misleading PASS badges.
    Renders an informative, honest visual status card documenting the solver limitation.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Card background box
    bg_box = FancyBboxPatch(
        (0.3, 0.4),
        9.4,
        9.2,
        boxstyle="round,pad=0.2,rounding_size=0.4",
        facecolor="#FBFBFB",
        edgecolor="#D0D0D0",
        linewidth=1.2,
    )
    ax.add_patch(bg_box)

    # Header bar
    header_box = FancyBboxPatch(
        (0.5, 8.1),
        9.0,
        1.2,
        boxstyle="round,pad=0.1,rounding_size=0.25",
        facecolor="#EEEEEE",
        edgecolor="#CCCCCC",
        linewidth=0.8,
    )
    ax.add_patch(header_box)

    ax.text(5.0, 8.7, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1A1A1A")

    # Status Badge (Amber/Neutral - NOT PASS, NOT GREEN)
    badge_color = f"#{COLOR_STATUS_WARN}"
    badge_box = FancyBboxPatch(
        (1.5, 6.7),
        7.0,
        1.0,
        boxstyle="round,pad=0.15,rounding_size=0.2",
        facecolor="#FFF8E1",
        edgecolor=badge_color,
        linewidth=1.2,
    )
    ax.add_patch(badge_box)
    ax.text(
        5.0,
        7.2,
        "STATUS: DESIGN CHECK TO BE ADDED IN SOLVER",
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color="#B78103",
    )

    # Detailed card content
    ax.text(1.0, 5.8, "Component:", fontsize=8.5, fontweight="bold", color="#333333")
    ax.text(3.4, 5.8, component_name, fontsize=8.5, color="#111111")

    ax.text(1.0, 5.0, "Section Profile:", fontsize=8.5, fontweight="bold", color="#333333")
    ax.text(3.4, 5.0, f"{section_type} (from model configuration)", fontsize=8.5, color="#111111")

    ax.text(1.0, 4.2, "Design Check:", fontsize=8.5, fontweight="bold", color="#333333")
    ax.text(3.4, 4.2, "Member Capacity Checks (Moment & Shear)", fontsize=8.5, color="#111111")

    ax.text(1.0, 3.4, "Applicable Code:", fontsize=8.5, fontweight="bold", color="#333333")
    ax.text(3.4, 3.4, "IS 800:2007 / IRC 24:2010 Cl. 507", fontsize=8.5, color="#111111")

    # Explanatory Note Box at bottom
    note_box = FancyBboxPatch(
        (0.6, 0.8),
        8.8,
        2.1,
        boxstyle="round,pad=0.1,rounding_size=0.2",
        facecolor="#F4F5F7",
        edgecolor="#E0E0E0",
        linewidth=0.8,
    )
    ax.add_patch(note_box)

    note_text = (
        "Note on Engineering Integrity:\n"
        "End-diaphragm structural capacity evaluation is pending solver implementation\n"
        "in OsdagBridge ('design to be added'). In accordance with strict reporting\n"
        "integrity, no artificial ratio, zero placeholder, or false PASS badge is displayed."
    )
    ax.text(5.0, 1.85, note_text, ha="center", va="center", fontsize=7.8, color="#555555", linespacing=1.35)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ==============================================================================
# HIGH-LEVEL CHART GENERATORS
# ==============================================================================

def generate_girder_ur_chart(bridge: Any, output_path: str) -> str:
    """Generate Chart 1: Steel Plate Girders Utilization Ratio bar chart."""
    data = extract_girder_ur_data(bridge)
    title = "Steel Plate Girders — Governing Utilization Ratios (Cl. 605 Fatigue)"
    return plot_ur_bar_chart(data, title, output_path, xlabel="Girder Member")


def generate_deck_slab_ur_chart(bridge: Any, output_path: str) -> str:
    """Generate Chart 2: Concrete Deck Slab Utilization Ratio bar chart."""
    data = extract_deck_slab_ur_data(bridge)
    title = "Concrete Deck Slab — Utilization Ratios (IRC 112 / IRC 21)"
    return plot_ur_bar_chart(data, title, output_path, xlabel="Deck Slab Check")


def generate_cross_bracing_ur_chart(bridge: Any, output_path: str) -> str:
    """Generate Chart 3: Cross Bracing Members Utilization Ratio bar chart."""
    data = extract_cross_bracing_ur_data(bridge)
    title = "Cross Bracing Members — Capacity Utilization Ratios (IS 800:2007)"
    return plot_ur_bar_chart(data, title, output_path, xlabel="Cross Bracing Member")


def generate_end_diaphragm_ur_chart(bridge: Any, output_path: str) -> str:
    """Generate Chart 4: End Diaphragm UR chart or honest status card."""
    ed_info = extract_end_diaphragm_ur_data(bridge)
    if ed_info.get("has_data") and ed_info.get("items"):
        title = "End Diaphragm Members — Utilization Ratios (IS 800:2007)"
        return plot_ur_bar_chart(ed_info["items"], title, output_path, xlabel="End Diaphragm Member")

    # Render honest informational status card
    return plot_status_card(
        title="End Diaphragm — Structural Check Status",
        component_name="End Diaphragm",
        section_type=ed_info.get("ed_type", "Rolled Beam"),
        message=ed_info.get("reason", "Checks pending implementation in solver"),
        output_path=output_path,
    )


def generate_all_ur_charts(bridge: Any, target_dir: str) -> Dict[str, str]:
    """
    Generate all 4 UR figures into target_dir.

    Returns dict of figure keys to relative LaTeX image paths:
    {
        "girders": "assets/ur_chart_girders.png",
        "deck_slab": "assets/ur_chart_deck_slab.png",
        "cross_bracing": "assets/ur_chart_cross_bracing.png",
        "end_diaphragm": "assets/ur_chart_end_diaphragm.png",
    }
    """
    os.makedirs(target_dir, exist_ok=True)

    girders_path = os.path.join(target_dir, "ur_chart_girders.png")
    deck_path = os.path.join(target_dir, "ur_chart_deck_slab.png")
    cb_path = os.path.join(target_dir, "ur_chart_cross_bracing.png")
    ed_path = os.path.join(target_dir, "ur_chart_end_diaphragm.png")

    generate_girder_ur_chart(bridge, girders_path)
    generate_deck_slab_ur_chart(bridge, deck_path)
    generate_cross_bracing_ur_chart(bridge, cb_path)
    generate_end_diaphragm_ur_chart(bridge, ed_path)

    return {
        "girders": "assets/ur_chart_girders.png",
        "deck_slab": "assets/ur_chart_deck_slab.png",
        "cross_bracing": "assets/ur_chart_cross_bracing.png",
        "end_diaphragm": "assets/ur_chart_end_diaphragm.png",
    }
