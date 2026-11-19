"""Programmatic charts embedded in the OsdagBridge LaTeX report.

All figures are rendered with matplotlib to PNG bytes and handed to
generate_report via ``payload.figure_data`` / ``fig_paths``.
"""
import io
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import styles as S

def _num(value):
    """Parse a quantity string ('12.34', 'N.A.', '0.00') to float or None."""
    try:
        m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(value))
        return float(m.group(0)) if m else None
    except (TypeError, ValueError):
        return None

def _fig_to_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()

def _style_ax(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

def material_quantity_figures(inputs: dict) -> dict:
    """Return {attr: png_bytes} for Chapter 7 material charts."""
    figs = {}

    def wt(key):
        return _num(inputs.get(key)) or 0.0

    steel_parts = [
        ("Girders", wt("steel_girders_wt_total")),
        ("Cross Bracing (Top)", wt("bracing_top_wt_total")),
        ("Cross Bracing (Bottom)", wt("bracing_bot_wt_total")),
        ("Cross Bracing (Diagonal)", wt("bracing_diag_wt_total")),
        ("End Diaphragms", wt("end_diaphragm_wt_total")),
        ("Shear Studs", wt("shear_studs_wt_total")),
    ]
    steel_parts = [(n, v) for n, v in steel_parts if v > 0]
    if steel_parts:
        names, vals = zip(*steel_parts)
        fig, ax = plt.subplots(figsize=(6.4, 2.6))
        bars = ax.bar(names, vals, color="#91B014")
        ax.set_ylabel("Weight (MT)", fontsize=8)
        ax.set_title("Structural Steel Quantity Breakdown", fontsize=9)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=7)
        _style_ax(ax)
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
        figs["chart_steel_qty"] = _fig_to_png(fig)

    conc_vol = _num(inputs.get("concrete_deck_vol_total")) or 0.0
    rebar_wt = wt("rebar_deck_wt_total")
    if conc_vol > 0 or rebar_wt > 0:
        fig, ax = plt.subplots(figsize=(4.2, 2.6))
        labels = ["Deck Concrete", "Rebar Steel"]
        vals = [conc_vol, rebar_wt]
        colors = ["#4C78A8", "#F58518"]
        bars = ax.bar(labels, vals, color=colors)
        ax.set_ylabel("Quantity", fontsize=8)
        ax.set_title("Concrete Volume (m³) vs Rebar Weight (MT)", fontsize=9)
        for b, v, unit in zip(bars, vals, ["m³", "MT"]):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f} {unit}",
                    ha="center", va="bottom", fontsize=7)
        _style_ax(ax)
        figs["chart_concrete_rebar"] = _fig_to_png(fig)

    return figs

def ur_summary_figure(urs: dict) -> bytes:
    """Bar chart of utilization ratios with UR=1.0 pass/fail threshold."""
    items = [(k, float(v)) for k, v in urs.items()
             if v is not None and str(v) not in ("", "---")]
    if not items:
        return b""
    names, vals = zip(*items)
    colors = ["#91B014" if v <= 1.0 else "#D62728" for v in vals]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    bars = ax.bar(names, vals, color=colors)
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.2,
               label="UR = 1.0 (limit)")
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontsize=8)
    ax.set_title("Overall Design Check Summary — Utilization Ratios",
                 fontsize=9)
    ax.set_ylim(0, max(max(vals) * 1.15, 1.2))
    ax.legend(fontsize=7, loc="upper right")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}",
                ha="center", va="bottom", fontsize=7)
    _style_ax(ax)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    return _fig_to_png(fig)
