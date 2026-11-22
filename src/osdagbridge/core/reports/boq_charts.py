# =============================================================================
# Material Quantity Summary Bar Charts Generator (Chapter 7)
# =============================================================================

from __future__ import annotations

import os
import math
import logging
from typing import Dict, List, Tuple, Optional, Any

from osdagbridge.core.reports.styles import STYLE

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_MASS,
    KEY_MP_ED_SECTIONAL_AREA,
    KEY_TD_ED_PROP_M,
    KEY_TD_ED_PROP_A,
)

logger = logging.getLogger(__name__)


def _to_float(val: Any, default: float = 0.0) -> float:
    """Safely convert strings or numbers (stripping units) to float."""
    if val is None:
        return default
    try:
        s = str(val).strip().replace("MT", "").replace("m³", "").replace("m^3", "").replace("kN", "").replace(",", "")
        return float(s)
    except (ValueError, TypeError):
        return default


def extract_boq_data(input_dict: dict, output_dict: Optional[dict] = None) -> Dict[str, Any]:
    """Extract structural steel tonnage breakdown and concrete vs. rebar quantities.
    
    Returns
    -------
    dict with:
      - steel_breakdown: list of (item_name, weight_mt)
      - steel_total_mt: float
      - concrete_volume_m3: float
      - concrete_deck_m3: float
      - concrete_barrier_m3: float
      - rebar_weight_mt: float
      - rebar_ratio_kg_m3: float
    """
    inp = input_dict or {}
    out = output_dict or {}

    span = _to_float(inp.get(KEY_SPAN), 30.0)
    n_girders = int(_to_float(inp.get(KEY_TS_NO_OF_GIRDERS), 2))
    spacing = _to_float(inp.get(KEY_TS_GIRDER_SPACING), 2.5)

    # 1. Structural Steel Girders
    girder_wt = _to_float(inp.get("steel_girders_wt_total"))
    if girder_wt <= 0.0:
        # Fallback estimation based on span and girders
        girder_wt = round(n_girders * span * 0.45, 2)  # ~450 kg/m per girder

    # 2. Cross Bracing
    cb_top = _to_float(inp.get("bracing_top_wt_total"))
    cb_bot = _to_float(inp.get("bracing_bot_wt_total"))
    cb_diag = _to_float(inp.get("bracing_diag_wt_total"))
    cb_wt = cb_top + cb_bot + cb_diag
    if cb_wt <= 0.0:
        cb_wt = _to_float(inp.get("steel_bracing_wt_total"))
    if cb_wt <= 0.0:
        # Fallback estimation
        n_panels = max(2, round(span / 5.0) - 1)
        cb_wt = round((n_girders - 1) * n_panels * 0.40, 2)

    # 3. End Diaphragms
    ed_wt = _to_float(inp.get("end_diaphragm_wt_total"))
    if ed_wt <= 0.0:
        # Calculate from end diaphragm properties or proportional to cross bracing
        n_bays_ends = 2 * max(1, (n_girders - 1))
        ed_mass = _to_float(out.get(KEY_TD_ED_PROP_M) or inp.get(KEY_MP_ED_MASS))
        ed_area_cm2 = _to_float(out.get(KEY_TD_ED_PROP_A) or inp.get(KEY_MP_ED_SECTIONAL_AREA))
        
        if ed_mass > 0.0:
            ed_wt = round(n_bays_ends * spacing * ed_mass / 1000.0, 2)
        elif ed_area_cm2 > 0.0:
            ed_wt = round(n_bays_ends * spacing * (ed_area_cm2 / 10000.0) * 7.85, 2)
        elif cb_wt > 0.0:
            # 2 end lines proportional to intermediate bracing
            n_panels = max(2, round(span / 5.0) - 1)
            ed_wt = round(2.0 * (cb_wt / n_panels), 2)
        else:
            ed_wt = round(n_bays_ends * spacing * 0.075, 2)

    total_steel = round(girder_wt + cb_wt + ed_wt, 2)

    # 4. Concrete Deck & Crash Barrier
    conc_deck = _to_float(inp.get("concrete_deck_vol_total"))
    if conc_deck <= 0.0:
        width = _to_float(inp.get("typical_section.overall_bridge_width"), 8.5)
        thick = _to_float(inp.get(KEY_TS_DECK_THICKNESS), 250.0) / 1000.0
        conc_deck = round(span * width * thick, 2)

    conc_barrier = _to_float(inp.get("crash_barrier_vol_total"))
    total_concrete = round(conc_deck + conc_barrier, 2)

    # 5. Reinforcement Steel
    rebar_wt = _to_float(inp.get("rebar_deck_wt_total"))
    if rebar_wt <= 0.0:
        rebar_wt = round(total_concrete * 0.120, 2)  # 120 kg/m3

    rebar_ratio = round((rebar_wt * 1000.0) / total_concrete, 1) if total_concrete > 0 else 120.0

    return {
        "steel_breakdown": [
            ("Girders", round(girder_wt, 2)),
            ("Cross Bracing", round(cb_wt, 2)),
            ("End Diaphragms", round(ed_wt, 2)),
        ],
        "steel_total_mt": total_steel,
        "concrete_volume_m3": total_concrete,
        "concrete_deck_m3": round(conc_deck, 2),
        "concrete_barrier_m3": round(conc_barrier, 2),
        "rebar_weight_mt": round(rebar_wt, 2),
        "rebar_ratio_kg_m3": rebar_ratio,
    }


def _render_with_matplotlib(data: Dict[str, Any], summary_path: str, steel_path: Optional[str] = None, conc_rebar_path: Optional[str] = None):
    """Render high-resolution material quantity bar charts using matplotlib."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steel_items = data["steel_breakdown"]
    total_steel = data["steel_total_mt"]
    conc_vol = data["concrete_volume_m3"]
    rebar_wt = data["rebar_weight_mt"]
    rebar_ratio = data["rebar_ratio_kg_m3"]

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Combined 2-Panel Summary Figure
    # ─────────────────────────────────────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=STYLE.MPL.FIGSIZE_1x2, dpi=STYLE.MPL.DPI_HIGH)

    # Left: Structural Steel Tonnage
    names1 = [item[0] for item in steel_items]
    vals1 = [item[1] for item in steel_items]
    colors1 = [STYLE.CLR.STEEL_GIRDER, STYLE.CLR.STEEL_CB, STYLE.CLR.STEEL_ED]
    edgecolors1 = [STYLE.CLR.STEEL_GIRDER_E, STYLE.CLR.STEEL_CB_E, STYLE.CLR.STEEL_ED_E]

    y_max1 = max(vals1) * 1.25 if vals1 and max(vals1) > 0 else 10.0
    bars1 = ax1.bar(names1, vals1, color=colors1, edgecolor=edgecolors1, linewidth=1.5, width=0.55, zorder=3)
    ax1.set_ylim(0, y_max1)
    ax1.set_ylabel("Weight (Metric Tonnes - MT)", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold", color=STYLE.CLR.TEXT_MID)
    ax1.set_title("Structural Steel Tonnage Breakdown", fontsize=STYLE.MPL.FONT_TITLE_LG, fontweight="bold", pad=12, color=STYLE.CLR.TITLE_DARK)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax1.set_axisbelow(True)

    # Annotate bar values
    for b in bars1:
        h = b.get_height()
        ax1.annotate(
            f"{h:.2f} MT",
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=STYLE.MPL.FONT_ANNOT_LG,
            fontweight="bold",
            color=STYLE.CLR.TEXT_DARK,
        )

    # Total steel banner badge
    ax1.text(
        0.03, 0.94,
        f"Total Steel: {total_steel:.2f} MT",
        transform=ax1.transAxes,
        fontsize=STYLE.MPL.FONT_ANNOT_LG,
        fontweight="bold",
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor=STYLE.CLR.BADGE_STEEL_BG, edgecolor=STYLE.CLR.BADGE_STEEL_BD, alpha=0.9),
    )

    # Right: Concrete Volume vs. Reinforcement Steel
    names2 = ["Concrete Volume\n(m³)", "Reinforcement\n(MT)"]
    vals2 = [conc_vol, rebar_wt]
    colors2 = [STYLE.CLR.CONCRETE_BAR, STYLE.CLR.REBAR_BAR]
    edgecolors2 = [STYLE.CLR.CONCRETE_EDGE, STYLE.CLR.REBAR_EDGE]

    y_max2 = max(vals2) * 1.25 if vals2 and max(vals2) > 0 else 10.0
    bars2 = ax2.bar(names2, vals2, color=colors2, edgecolor=edgecolors2, linewidth=1.5, width=0.48, zorder=3)
    ax2.set_ylim(0, y_max2)
    ax2.set_ylabel("Quantity (m³ / MT)", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold", color=STYLE.CLR.TEXT_MID)
    ax2.set_title("Concrete Volume vs. Reinforcement Steel", fontsize=STYLE.MPL.FONT_TITLE_LG, fontweight="bold", pad=12, color=STYLE.CLR.TITLE_DARK)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax2.set_axisbelow(True)

    # Annotate bar values
    units = ["m³", "MT"]
    for idx, b in enumerate(bars2):
        h = b.get_height()
        ax2.annotate(
            f"{h:.2f} {units[idx]}",
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=STYLE.MPL.FONT_ANNOT_LG,
            fontweight="bold",
            color=STYLE.CLR.TEXT_DARK,
        )

    # Rebar ratio badge
    ax2.text(
        0.03, 0.94,
        f"Rebar Ratio: {rebar_ratio:.1f} kg/m³",
        transform=ax2.transAxes,
        fontsize=STYLE.MPL.FONT_ANNOT_LG,
        fontweight="bold",
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor=STYLE.CLR.BADGE_REBAR_BG, edgecolor=STYLE.CLR.BADGE_REBAR_BD, alpha=0.9),
    )

    plt.tight_layout(pad=2.5)
    fig.savefig(summary_path, dpi=STYLE.MPL.DPI_HIGH, bbox_inches="tight")
    plt.close(fig)
    logger.info("Generated combined BOQ summary chart using matplotlib: %s", summary_path)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Individual Figures (if paths provided)
    # ─────────────────────────────────────────────────────────────────────────
    if steel_path:
        fig_s, ax_s = plt.subplots(figsize=STYLE.MPL.FIGSIZE_1x1, dpi=STYLE.MPL.DPI_HIGH)
        bars_s = ax_s.bar(names1, vals1, color=colors1, edgecolor=edgecolors1, linewidth=1.5, width=0.55, zorder=3)
        ax_s.set_ylim(0, y_max1)
        ax_s.set_ylabel("Weight (Metric Tonnes - MT)", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold")
        ax_s.set_title("Structural Steel Tonnage Breakdown", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold", pad=12)
        ax_s.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        ax_s.set_axisbelow(True)
        for b in bars_s:
            h = b.get_height()
            ax_s.annotate(f"{h:.2f} MT", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=STYLE.MPL.FONT_LEGEND, fontweight="bold")
        plt.tight_layout()
        fig_s.savefig(steel_path, dpi=STYLE.MPL.DPI_HIGH, bbox_inches="tight")
        plt.close(fig_s)

    if conc_rebar_path:
        fig_c, ax_c = plt.subplots(figsize=(6, 5), dpi=STYLE.MPL.DPI_HIGH)
        bars_c = ax_c.bar(names2, vals2, color=colors2, edgecolor=edgecolors2, linewidth=1.5, width=0.48, zorder=3)
        ax_c.set_ylim(0, y_max2)
        ax_c.set_ylabel("Quantity (m³ / MT)", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold")
        ax_c.set_title("Concrete Volume vs. Reinforcement Steel", fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold", pad=12)
        ax_c.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        ax_c.set_axisbelow(True)
        for idx, b in enumerate(bars_c):
            h = b.get_height()
            ax_c.annotate(f"{h:.2f} {units[idx]}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=STYLE.MPL.FONT_LEGEND, fontweight="bold")
        plt.tight_layout()
        fig_c.savefig(conc_rebar_path, dpi=STYLE.MPL.DPI_HIGH, bbox_inches="tight")
        plt.close(fig_c)


def _render_with_pillow(data: Dict[str, Any], summary_path: str, steel_path: Optional[str] = None, conc_rebar_path: Optional[str] = None):
    """Fallback renderer using pure Pillow when matplotlib is not installed."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = STYLE.PIL.CANVAS_BOQ_W, STYLE.PIL.CANVAS_BOQ_H
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        _pil_fonts = STYLE.pil_load_fonts()
        font_title = _pil_fonts["title"]
        font_sub   = _pil_fonts["sub"]
        font_label = _pil_fonts["label"]
        font_val   = _pil_fonts["val"]
        font_badge = _pil_fonts["label"]   # badge uses label size
    except Exception:
        from PIL import ImageFont
        font_title = font_sub = font_label = font_val = font_badge = ImageFont.load_default()

    steel_items = data["steel_breakdown"]
    total_steel = data["steel_total_mt"]
    conc_vol = data["concrete_volume_m3"]
    rebar_wt = data["rebar_weight_mt"]
    rebar_ratio = data["rebar_ratio_kg_m3"]

    # ─────────────────────────────────────────────────────────────────────────
    # Panel 1: Left (Structural Steel Tonnage)
    # ─────────────────────────────────────────────────────────────────────────
    p1_x1, p1_y1, p1_x2, p1_y2 = 60, 40, 710, 560
    draw.rectangle([p1_x1, p1_y1, p1_x2, p1_y2], outline=STYLE.CLR.PANEL_BORDER, width=1)
    draw.text((p1_x1 + 25, p1_y1 + 18), "Structural Steel Tonnage Breakdown", fill=STYLE.CLR.TITLE_DARK, font=font_title)

    # Total steel badge
    badge_text1 = f"Total Steel: {total_steel:.2f} MT"
    draw.rectangle([p1_x2 - 210, p1_y1 + 16, p1_x2 - 25, p1_y1 + 42], fill=STYLE.CLR.BADGE_STEEL_BG, outline=STYLE.CLR.BADGE_STEEL_BD, width=1)
    draw.text((p1_x2 - 200, p1_y1 + 21), badge_text1, fill=STYLE.CLR.STEEL_GIRDER_E, font=font_badge)

    # Plot axes area
    ax1_x1, ax1_y1, ax1_x2, ax1_y2 = p1_x1 + 75, p1_y1 + 75, p1_x2 - 35, p1_y2 - 60
    draw.line([ax1_x1, ax1_y1, ax1_x1, ax1_y2], fill=STYLE.CLR.AXIS_LINE, width=2)
    draw.line([ax1_x1, ax1_y2, ax1_x2, ax1_y2], fill=STYLE.CLR.AXIS_LINE, width=2)

    s_vals = [item[1] for item in steel_items]
    max_val1 = max(s_vals) * 1.25 if s_vals and max(s_vals) > 0 else 10.0

    # Gridlines and ticks
    for i in range(5):
        frac = i / 4.0
        val = frac * max_val1
        y = ax1_y2 - int(frac * (ax1_y2 - ax1_y1))
        draw.line([ax1_x1, y, ax1_x2, y], fill=STYLE.CLR.GRID_LINE, width=1)
        draw.text((p1_x1 + 15, y - 8), f"{val:.1f}", fill=STYLE.CLR.TICK_LABEL, font=font_label)

    # Draw bars
    bar_w1 = 80
    n_bars1 = len(steel_items)
    gap1 = (ax1_x2 - ax1_x1 - n_bars1 * bar_w1) // (n_bars1 + 1)
    colors1 = [STYLE.CLR.STEEL_GIRDER, STYLE.CLR.STEEL_CB, STYLE.CLR.STEEL_ED]
    outlines1 = [STYLE.CLR.STEEL_GIRDER_E, STYLE.CLR.STEEL_CB_E, STYLE.CLR.STEEL_ED_E]

    for idx, (name, val) in enumerate(steel_items):
        bx = ax1_x1 + gap1 + idx * (bar_w1 + gap1)
        h_px = int((val / max_val1) * (ax1_y2 - ax1_y1))
        by = ax1_y2 - h_px
        draw.rectangle([bx, by, bx + bar_w1, ax1_y2], fill=colors1[idx % len(colors1)], outline=outlines1[idx % len(outlines1)], width=2)
        # Value on top
        draw.text((bx + bar_w1 // 2 - 28, by - 24), f"{val:.2f} MT", fill=STYLE.CLR.TEXT_DARK, font=font_val)
        # Label below
        draw.text((bx + bar_w1 // 2 - 32, ax1_y2 + 12), name, fill=STYLE.CLR.TEXT_MID, font=font_label)

    # ─────────────────────────────────────────────────────────────────────────
    # Panel 2: Right (Concrete Volume vs Reinforcement Steel)
    # ─────────────────────────────────────────────────────────────────────────
    p2_x1, p2_y1, p2_x2, p2_y2 = 780, 40, 1430, 560
    draw.rectangle([p2_x1, p2_y1, p2_x2, p2_y2], outline=STYLE.CLR.PANEL_BORDER, width=1)
    draw.text((p2_x1 + 25, p2_y1 + 18), "Concrete Volume vs. Reinforcement", fill=STYLE.CLR.TITLE_DARK, font=font_title)

    # Rebar ratio badge
    badge_text2 = f"Rebar Ratio: {rebar_ratio:.1f} kg/m³"
    draw.rectangle([p2_x2 - 225, p2_y1 + 16, p2_x2 - 25, p2_y1 + 42], fill=STYLE.CLR.BADGE_REBAR_BG, outline=STYLE.CLR.BADGE_REBAR_BD, width=1)
    draw.text((p2_x2 - 215, p2_y1 + 21), badge_text2, fill=STYLE.CLR.REBAR_EDGE, font=font_badge)

    # Plot axes area
    ax2_x1, ax2_y1, ax2_x2, ax2_y2 = p2_x1 + 75, p2_y1 + 75, p2_x2 - 35, p2_y2 - 60
    draw.line([ax2_x1, ax2_y1, ax2_x1, ax2_y2], fill=STYLE.CLR.AXIS_LINE, width=2)
    draw.line([ax2_x1, ax2_y2, ax2_x2, ax2_y2], fill=STYLE.CLR.AXIS_LINE, width=2)

    c_vals = [conc_vol, rebar_wt]
    max_val2 = max(c_vals) * 1.25 if c_vals and max(c_vals) > 0 else 10.0

    # Gridlines and ticks
    for i in range(5):
        frac = i / 4.0
        val = frac * max_val2
        y = ax2_y2 - int(frac * (ax2_y2 - ax2_y1))
        draw.line([ax2_x1, y, ax2_x2, y], fill=STYLE.CLR.GRID_LINE, width=1)
        draw.text((p2_x1 + 15, y - 8), f"{val:.1f}", fill=STYLE.CLR.TICK_LABEL, font=font_label)

    # Draw bars
    bar_w2 = 110
    n_bars2 = 2
    gap2 = (ax2_x2 - ax2_x1 - n_bars2 * bar_w2) // (n_bars2 + 1)
    colors2 = [STYLE.CLR.CONCRETE_BAR, STYLE.CLR.REBAR_BAR]
    outlines2 = [STYLE.CLR.CONCRETE_EDGE, STYLE.CLR.REBAR_EDGE]
    c_labels = ["Concrete (m³)", "Rebar (MT)"]
    c_units = ["m³", "MT"]

    for idx, (label, val) in enumerate(zip(c_labels, c_vals)):
        bx = ax2_x1 + gap2 + idx * (bar_w2 + gap2)
        h_px = int((val / max_val2) * (ax2_y2 - ax2_y1))
        by = ax2_y2 - h_px
        draw.rectangle([bx, by, bx + bar_w2, ax2_y2], fill=colors2[idx], outline=outlines2[idx], width=2)
        # Value on top
        draw.text((bx + bar_w2 // 2 - 32, by - 24), f"{val:.2f} {c_units[idx]}", fill=STYLE.CLR.TEXT_DARK, font=font_val)
        # Label below
        draw.text((bx + bar_w2 // 2 - 40, ax2_y2 + 12), label, fill=STYLE.CLR.TEXT_MID, font=font_label)

    # Save summary
    img.save(summary_path, "PNG")
    logger.info("Generated combined BOQ summary chart using Pillow: %s", summary_path)

    # Crop individual images if paths requested
    if steel_path:
        img_s = img.crop((p1_x1 - 10, p1_y1 - 10, p1_x2 + 10, p1_y2 + 10))
        img_s.save(steel_path, "PNG")

    if conc_rebar_path:
        img_c = img.crop((p2_x1 - 10, p2_y1 - 10, p2_x2 + 10, p2_y2 + 10))
        img_c.save(conc_rebar_path, "PNG")


def generate_boq_summary_charts(input_dict: dict, output_dir_or_path: str, output_dict: Optional[dict] = None) -> Dict[str, str]:
    """Generate BOQ summary bar charts:
    - Structural steel tonnage breakdown (Girders, Cross Bracing, End Diaphragms)
    - Concrete volume (m3) vs. Reinforcement steel weight (MT)
    
    Returns
    -------
    dict with file paths: {'summary': ..., 'steel': ..., 'concrete_rebar': ...}
    """
    if os.path.isdir(output_dir_or_path):
        summary_path = os.path.join(output_dir_or_path, "boq_summary.png")
        steel_path = os.path.join(output_dir_or_path, "boq_steel_tonnage.png")
        conc_rebar_path = os.path.join(output_dir_or_path, "boq_concrete_vs_rebar.png")
    else:
        summary_path = output_dir_or_path
        base_dir = os.path.dirname(output_dir_or_path)
        steel_path = os.path.join(base_dir, "boq_steel_tonnage.png")
        conc_rebar_path = os.path.join(base_dir, "boq_concrete_vs_rebar.png")

    data = extract_boq_data(input_dict, output_dict)

    try:
        _render_with_matplotlib(data, summary_path, steel_path, conc_rebar_path)
    except Exception as exc:
        logger.info("Matplotlib renderer unavailable or failed (%s); using Pillow renderer", exc)
        _render_with_pillow(data, summary_path, steel_path, conc_rebar_path)

    return {
        "summary": summary_path,
        "steel": steel_path,
        "concrete_rebar": conc_rebar_path,
    }
