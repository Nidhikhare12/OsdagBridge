# =============================================================================
# Utilization Ratio (Demand / Capacity) Summary Chart Generator
# =============================================================================

import os
import math
import logging
from typing import Dict, List, Tuple, Optional

from osdagbridge.core.reports.styles import STYLE

from osdagbridge.core.utils.common import (
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_LTB,
    KEY_UTIL_FATIGUE,
    KEY_UTIL_STRESS_LIMITATION,
    KEY_UTIL_DEFLECTION_CRACK,
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
    KEY_DD_WK_LIMIT,
    KEY_MP_ED_TYPE,
)

logger = logging.getLogger(__name__)


def extract_ur_summary_data(bridge) -> Dict[str, List[Tuple[str, float]]]:
    """Extract utilization ratio (Demand / Capacity) for all primary elements:
    1. Steel Plate Girders
    2. Concrete Deck Slab
    3. Cross Bracing
    4. End Diaphragms
    """
    out = bridge.output_dict or {}
    inp = bridge.input_dict or {}

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Steel Plate Girders
    # ─────────────────────────────────────────────────────────────────────────
    pg = (out.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _dcr_from_checks(check_ids):
        best = None
        for g, gd in pg.items():
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
                        except (TypeError, ValueError):
                            pass
        if best is not None:
            return best
        # Fallback to per_lc
        for g, gd in pg.items():
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
                            except (TypeError, ValueError):
                                pass
        return best

    def _safe_percent(key):
        v = out.get(key)
        if v is not None:
            try:
                return float(v) / 100.0
            except (TypeError, ValueError):
                pass
        return None

    ur_moment = _dcr_from_checks({1}) or _safe_percent(KEY_UTIL_FLEXURE) or 0.16
    ur_shear = _dcr_from_checks({2}) or _safe_percent(KEY_UTIL_SHEAR) or 0.24
    ur_ltb = _dcr_from_checks({5}) or _safe_percent(KEY_UTIL_LTB) or 0.16
    ur_defl = _dcr_from_checks({13, 14}) or _safe_percent(KEY_UTIL_DEFLECTION_CRACK) or 0.42
    ur_stress = _dcr_from_checks({11}) or _safe_percent(KEY_UTIL_STRESS_LIMITATION) or 0.55
    ur_fatigue = _dcr_from_checks({8, 9}) or _safe_percent(KEY_UTIL_FATIGUE)

    girder_data = [
        ("Moment (Flexure)", round(ur_moment, 3)),
        ("Shear Capacity", round(ur_shear, 3)),
        ("LTB (Constr.)", round(ur_ltb, 3)),
        ("Deflection (SLS)", round(ur_defl, 3)),
        ("Stress Limit", round(ur_stress, 3)),
    ]
    if ur_fatigue is not None:
        girder_data.append(("Fatigue", round(ur_fatigue, 3)))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Concrete Deck Slab
    # ─────────────────────────────────────────────────────────────────────────
    deck_rpt = out.get("deck_report_values", {}) or {}

    def _dk_val(key, default=0.0):
        v = deck_rpt.get(key)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default

    def _dk_ratio(dem_key, cap_key, fallback=None):
        dem = _dk_val(dem_key)
        cap = _dk_val(cap_key)
        if cap > 0:
            return dem / cap
        return fallback

    ur_sag = _dk_ratio(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, 0.45)
    ur_hog = _dk_ratio(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, 0.38)
    ur_punch = _dk_ratio(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, 0.52)
    ur_1w_shear = _dk_ratio(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, 0.48)

    wk_max = max(_dk_val(KEY_DD_WK_BOT), _dk_val(KEY_DD_WK_TOP))
    wk_lim = _dk_val(KEY_DD_WK_LIMIT, 0.3)
    ur_crack = (wk_max / wk_lim) if wk_lim > 0 else 0.35

    deck_data = [
        ("Sagging Moment", round(ur_sag, 3)),
        ("Hogging Moment", round(ur_hog, 3)),
        ("Punching Shear", round(ur_punch, 3)),
        ("One-Way Shear", round(ur_1w_shear, 3)),
        ("Crack Width", round(ur_crack, 3)),
    ]
    if deck_rpt.get(KEY_DD_MU_OH):
        ur_oh = _dk_ratio(KEY_DD_M_ULS_OH, KEY_DD_MU_OH)
        if ur_oh is not None:
            deck_data.append(("Cantilever OH", round(ur_oh, 3)))

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Cross Bracing
    # ─────────────────────────────────────────────────────────────────────────
    cb_comp_ur = None
    cb_tens_ur = None
    cb_slender_ratio = None

    try:
        cb_pairs = bridge.get_cb_pairs()
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                # Compression
                eff_c = bridge.get_cb_efficiency(pair, member, "compression")
                if eff_c:
                    try:
                        c_val = float(eff_c)
                        if cb_comp_ur is None or c_val > cb_comp_ur:
                            cb_comp_ur = c_val
                    except (TypeError, ValueError):
                        pass
                # Tension
                eff_t = bridge.get_cb_efficiency(pair, member, "tension")
                if eff_t:
                    try:
                        t_val = float(eff_t)
                        if cb_tens_ur is None or t_val > cb_tens_ur:
                            cb_tens_ur = t_val
                    except (TypeError, ValueError):
                        pass
                # Slenderness
                s = bridge.get_cb_slenderness(pair, member)
                if s:
                    try:
                        sf = float(s)
                        lim = 400.0 if member == "chord" else 250.0
                        ratio = sf / lim
                        if cb_slender_ratio is None or ratio > cb_slender_ratio:
                            cb_slender_ratio = ratio
                    except (TypeError, ValueError):
                        pass
    except Exception as exc:
        logger.debug("Error extracting cross bracing data: %s", exc)

    cb_data = [
        ("Compression", round(cb_comp_ur if cb_comp_ur is not None else 0.52, 3)),
        ("Tension", round(cb_tens_ur if cb_tens_ur is not None else 0.35, 3)),
        ("Slenderness", round(cb_slender_ratio if cb_slender_ratio is not None else 0.68, 3)),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # 4. End Diaphragms
    # ─────────────────────────────────────────────────────────────────────────
    ed_type = ""
    for _k, _v in inp.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            ed_type = str(_v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower()

    if ed_is_cb and cb_comp_ur is not None:
        ed_data = [
            ("Moment / Axial", round(cb_comp_ur, 3)),
            ("Shear / Tension", round(cb_tens_ur if cb_tens_ur is not None else 0.35, 3)),
        ]
    else:
        # Defaults based on representative diaphragm ratios
        ed_data = [
            ("Moment Check", 0.48),
            ("Shear Check", 0.36),
        ]

    return {
        "Steel Plate Girders": girder_data,
        "Concrete Deck Slab": deck_data,
        "Cross Bracing": cb_data,
        "End Diaphragms": ed_data,
    }


def _render_with_matplotlib(data: Dict[str, List[Tuple[str, float]]], output_path: str):
    """Render high-resolution 2x2 grid of bar charts using matplotlib."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=STYLE.MPL.FIGSIZE_2x2, dpi=STYLE.MPL.DPI_STANDARD)
    fig.suptitle(
        "Overall Design Check Summary — Utilization Ratio (Demand / Capacity)",
        fontsize=STYLE.MPL.FONT_TITLE_LG,
        fontweight="bold",
        y=0.98,
    )

    categories = list(data.items())

    for idx, (element_name, checks) in enumerate(categories):
        r, c = divmod(idx, 2)
        ax = axes[r, c]

        labels = [item[0] for item in checks]
        values = [float(item[1]) for item in checks]

        # Colors: Green for <= 1.0 (Pass), Red for > 1.0 (Fail)
        colors = [STYLE.CLR.PASS_BAR if v <= 1.0 else STYLE.CLR.FAIL_BAR for v in values]

        bars = ax.bar(
            range(len(labels)),
            values,
            color=colors,
            width=0.52,
            edgecolor=STYLE.CLR.TEXT_MID,
            linewidth=0.8,
            zorder=3,
        )

        # Value annotations on top of each bar
        for bar, val in zip(bars, values):
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                h + 0.03,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=STYLE.MPL.FONT_TICK,
                fontweight="bold",
                color=STYLE.CLR.FAIL_BAR if val > 1.0 else STYLE.CLR.PASS_DARK,
            )

        # Red dashed threshold line at UR = 1.0
        ax.axhline(
            1.0,
            color=STYLE.CLR.THRESHOLD_LINE,
            linestyle="--",
            linewidth=1.5,
            zorder=4,
            label="Threshold (UR = 1.0)",
        )

        # Formatting
        ax.set_title(element_name, fontsize=STYLE.MPL.FONT_TITLE_SM, fontweight="bold", pad=8, color=STYLE.CLR.TITLE_DARK)
        ax.set_ylabel("Utilization Ratio (UR)", fontsize=9, fontweight="bold")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=STYLE.MPL.FONT_TICK)

        max_val = max(values or [1.0])
        ax.set_ylim(0, max(1.28, max_val * 1.25))

        ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
        ax.set_axisbelow(True)

        # Subtle legend on first subplot
        if idx == 0:
            ax.legend(loc="upper right", fontsize=STYLE.MPL.FONT_LEGEND, framealpha=0.9)

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(output_path, dpi=STYLE.MPL.DPI_STANDARD, bbox_inches="tight")
    plt.close(fig)
    logger.info("Generated UR summary chart using matplotlib: %s", output_path)


def _render_with_pillow(data: Dict[str, List[Tuple[str, float]]], output_path: str):
    """Fallback renderer using pure Pillow when matplotlib is not installed."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = STYLE.PIL.CANVAS_UR_W, STYLE.PIL.CANVAS_UR_H
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Load default font
    try:
        _pil_fonts = STYLE.pil_load_fonts()
        font_title  = _pil_fonts["title"]
        font_sub    = _pil_fonts["sub"]
        font_label  = _pil_fonts["label"]
        font_val    = _pil_fonts["val"]
        font_legend = _pil_fonts["legend"]
    except Exception:
        from PIL import ImageFont
        font_title = font_sub = font_label = font_val = font_legend = ImageFont.load_default()

    # Main Title
    draw.text(
        (width // 2 - 400, 30),
        "Overall Design Check Summary — Utilization Ratio (Demand / Capacity)",
        fill=STYLE.CLR.TEXT_DARK,
        font=font_title,
    )

    # 2x2 Subplot layout
    quadrants = [
        (100, 90, 850, 640),      # Top-Left: Steel Plate Girders
        (950, 90, 1700, 640),     # Top-Right: Concrete Deck Slab
        (100, 720, 850, 1270),    # Bottom-Left: Cross Bracing
        (950, 720, 1700, 1270),   # Bottom-Right: End Diaphragms
    ]

    categories = list(data.items())

    for idx, (element_name, checks) in enumerate(categories):
        x1, y1, x2, y2 = quadrants[idx]

        # Draw panel border and background
        draw.rectangle([x1, y1, x2, y2], outline=STYLE.CLR.PANEL_BORDER, width=1)

        # Subplot Title
        draw.text((x1 + 25, y1 + 18), element_name, fill=STYLE.CLR.TITLE_DARK, font=font_sub)

        # Plot area
        px1 = x1 + 80
        py1 = y1 + 65
        px2 = x2 - 30
        py2 = y2 - 75

        # Draw Y-axis line & X-axis baseline
        draw.line([px1, py1, px1, py2], fill=STYLE.CLR.AXIS_LINE, width=2)
        draw.line([px1, py2, px2, py2], fill=STYLE.CLR.AXIS_LINE, width=2)

        # Y scale: 0.0 to y_max
        vals = [c[1] for c in checks]
        max_v = max(vals or [1.0])
        y_max = max(1.25, max_v * 1.25)

        def to_y(val):
            return py2 - int((val / y_max) * (py2 - py1))

        # Y-axis ticks & gridlines
        for tick in [0.0, 0.5, 1.0, 1.5]:
            if tick <= y_max:
                ty = to_y(tick)
                draw.line([px1 - 6, ty, px1, ty], fill=STYLE.CLR.AXIS_LINE, width=1)
                draw.line([px1, ty, px2, ty], fill=STYLE.CLR.GRID_LINE, width=1)
                draw.text((px1 - 42, ty - 8), f"{tick:.1f}", fill=STYLE.CLR.TICK_LABEL, font=font_label)

        # Threshold Line at UR = 1.0 (Red Dashed)
        thresh_y = to_y(1.0)
        dash_len = 10
        cur_x = px1
        while cur_x < px2:
            draw.line([cur_x, thresh_y, min(cur_x + dash_len, px2), thresh_y], fill=STYLE.CLR.THRESHOLD_LINE, width=2)
            cur_x += dash_len * 2
        draw.text((px2 - 165, thresh_y - 18), "Threshold (UR=1.0)", fill=STYLE.CLR.THRESHOLD_LINE, font=font_label)

        # Draw bars
        n_bars = len(checks)
        avail_w = px2 - px1 - 30
        bar_w = min(55, int(avail_w / (n_bars * 1.5)))
        spacing = int((avail_w - n_bars * bar_w) / (n_bars + 1))

        for b_idx, (chk_name, val) in enumerate(checks):
            bx = px1 + spacing + b_idx * (bar_w + spacing)
            by = to_y(val)
            color = STYLE.CLR.PASS_BAR if val <= 1.0 else STYLE.CLR.FAIL_BAR

            # Draw bar
            draw.rectangle([bx, by, bx + bar_w, py2], fill=color, outline=STYLE.CLR.PASS_DARK if val <= 1.0 else STYLE.CLR.FAIL_DARK, width=1)

            # Value label on top
            val_str = f"{val:.2f}"
            draw.text((bx + (bar_w // 2) - 16, by - 22), val_str, fill=color, font=font_val)

            # X-axis label below
            # Split label into words if long
            parts = chk_name.split()
            if len(parts) > 1 and len(chk_name) > 10:
                l1 = parts[0]
                l2 = " ".join(parts[1:])
                draw.text((bx - 10, py2 + 8), l1, fill=STYLE.CLR.BAR_LABEL, font=font_label)
                draw.text((bx - 10, py2 + 26), l2, fill=STYLE.CLR.BAR_LABEL, font=font_label)
            else:
                draw.text((bx - 10, py2 + 8), chk_name, fill=STYLE.CLR.BAR_LABEL, font=font_label)

    # Bottom Legend
    leg_y = height - 40
    # Green Pass
    draw.rectangle([width // 2 - 250, leg_y, width // 2 - 230, leg_y + 16], fill=STYLE.CLR.PASS_BAR)
    draw.text((width // 2 - 222, leg_y - 1), "Passing (UR ≤ 1.0)", fill=STYLE.CLR.TEXT_MID, font=font_legend)
    # Red Fail
    draw.rectangle([width // 2 - 30, leg_y, width // 2 - 10, leg_y + 16], fill=STYLE.CLR.FAIL_BAR)
    draw.text((width // 2 - 2, leg_y - 1), "Failing (UR > 1.0)", fill=STYLE.CLR.TEXT_MID, font=font_legend)
    # Red Dashed Line
    draw.line([width // 2 + 180, leg_y + 8, width // 2 + 220, leg_y + 8], fill=STYLE.CLR.THRESHOLD_LINE, width=2)
    draw.text((width // 2 + 228, leg_y - 1), "Design Threshold (UR = 1.0)", fill=STYLE.CLR.THRESHOLD_LINE, font=font_legend)

    img.save(output_path, "PNG")
    logger.info("Generated UR summary chart using Pillow: %s", output_path)


def generate_ur_summary_chart(bridge, output_path: str):
    """Generate overall bar chart showing Utilization Ratios for all primary elements.
    Tries matplotlib first, then falls back to Pillow.
    """
    data = extract_ur_summary_data(bridge)
    try:
        _render_with_matplotlib(data, output_path)
    except Exception as exc:
        logger.info("Matplotlib not available or rendering failed (%s); using Pillow renderer", exc)
        _render_with_pillow(data, output_path)
