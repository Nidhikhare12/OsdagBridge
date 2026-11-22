# =============================================================================
# Programmatic Matplotlib charts for the design report.
# Uses the Agg backend so PDF generation never needs a display.
# Values are passed in by the chapter modules — nothing is invented here.
# =============================================================================

from __future__ import annotations

import os
import re

from osdagbridge.core.reports.styles import (
    CHART_DPI,
    MPL_FAIL,
    MPL_NA,
    MPL_PASS,
    MPL_THRESHOLD,
    OSDAGE_GREEN_HEX,
)


def _plt():
    """Lazy Agg backend — report chapters still import if matplotlib is absent."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _to_float(value):
    """Coerce a report cell (number, '12.3', 'N.A.', None) to float or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return None
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    if s.upper() in {"N.A.", "NA", "N/A", "---", "NONE"}:
        return None
    s = s.replace(",", "")
    # Strip a trailing unit token ("12.30 MT", "8.1 m^3", LaTeX leftovers).
    s = re.sub(r"[^0-9eE.+-]+$", "", s).strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
        if not m:
            return None
        try:
            return float(m.group(0))
        except (TypeError, ValueError):
            return None


def _save(fig, out_path, plt):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=CHART_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path.replace("\\", "/")


def render_ur_summary_chart(ur_by_member, out_path):
    """Horizontal UR bars for the four Section 5.5 member families.

    Parameters
    ----------
    ur_by_member : dict[str, float | None]
        Keys expected:
          ``Steel Plate Girders``, ``Concrete Deck Slab``,
          ``Cross Bracing``, ``End Diaphragms``.
        Missing / None values are drawn grey and labelled n/a.
    """
    labels = [
        "Steel Plate Girders",
        "Concrete Deck Slab",
        "Cross Bracing",
        "End Diaphragms",
    ]
    values = [_to_float(ur_by_member.get(k)) for k in labels]
    colors = []
    display = []
    for v in values:
        if v is None:
            colors.append(MPL_NA)
            display.append(0.0)
        elif v > 1.0:
            colors.append(MPL_FAIL)
            display.append(v)
        else:
            colors.append(MPL_PASS)
            display.append(v)

    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ypos = list(range(len(labels) - 1, -1, -1))  # first label at the top
    ax.barh(ypos, display, color=colors,
            edgecolor="#333333", linewidth=0.4, height=0.62)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.axvline(1.0, color=MPL_THRESHOLD, linestyle="--", linewidth=1.2,
               label="UR = 1.0")
    xmax = max([1.15] + display + [1.0])
    ax.set_xlim(0.0, xmax * 1.08 if xmax > 0 else 1.2)
    ax.set_xlabel("Utilization Ratio (Demand / Capacity)")
    ax.set_title("Overall Design Check Summary — Governing UR")
    for y, v in zip(ypos, values):
        if v is None:
            ax.text(0.02, y, "n/a", va="center", ha="left", fontsize=8,
                    color="#555555")
        else:
            ax.text(v + 0.02, y, f"{v:.2f}", va="center", ha="left", fontsize=8)
    ax.legend(frameon=False, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, out_path, plt)


def render_quantity_charts(input_dict, out_dir):
    """Bar charts for Chapter 7 quantities. Skips non-numeric / N.A. values.

    Returns
    -------
    dict
        ``steel`` → PNG path (or None), ``deck`` → PNG path (or None).
    """
    os.makedirs(out_dir, exist_ok=True)
    steel_items = [
        ("Girders", "steel_girders_wt_total"),
        ("Bracing\nTop Chord", "bracing_top_wt_total"),
        ("Bracing\nBottom Chord", "bracing_bot_wt_total"),
        ("Bracing\nDiagonal", "bracing_diag_wt_total"),
    ]
    deck_items = [
        ("Concrete deck\n(m$^3$)", "concrete_deck_vol_total"),
        ("Rebar\n(MT)", "rebar_deck_wt_total"),
    ]

    paths = {"steel": None, "deck": None}

    steel_labels, steel_vals = [], []
    for lab, key in steel_items:
        v = _to_float(input_dict.get(key))
        if v is None:
            continue
        steel_labels.append(lab)
        steel_vals.append(v)
    if steel_labels:
        plt = _plt()
        fig, ax = plt.subplots(figsize=(7.2, 3.4))
        ax.bar(steel_labels, steel_vals, color=f"#{OSDAGE_GREEN_HEX}",
               edgecolor="#333333", linewidth=0.4)
        ax.set_ylabel("Weight (MT)")
        ax.set_title("Structural Steel Quantities")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for i, v in enumerate(steel_vals):
            ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        paths["steel"] = _save(fig, os.path.join(out_dir, "qty_steel.png"), plt)

    deck_labels, deck_vals, deck_units = [], [], []
    conc = _to_float(input_dict.get("concrete_deck_vol_total"))
    rebar = _to_float(input_dict.get("rebar_deck_wt_total"))
    if conc is not None:
        deck_labels.append("Concrete deck")
        deck_vals.append(conc)
        deck_units.append("m³")
    if rebar is not None:
        deck_labels.append("Reinforcement steel")
        deck_vals.append(rebar)
        deck_units.append("MT")
    if deck_labels:
        plt = _plt()
        fig, ax = plt.subplots(figsize=(6.2, 3.4))
        colors = [f"#{OSDAGE_GREEN_HEX}", "#4C6A80"][:len(deck_labels)]
        ax.bar(deck_labels, deck_vals, color=colors,
               edgecolor="#333333", linewidth=0.4)
        ax.set_ylabel("Quantity")
        ax.set_title("Deck Concrete and Reinforcement")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for i, (v, u) in enumerate(zip(deck_vals, deck_units)):
            ax.text(i, v, f"{v:.2f} {u}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        paths["deck"] = _save(fig, os.path.join(out_dir, "qty_deck.png"), plt)

    return paths
