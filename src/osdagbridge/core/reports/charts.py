# =============================================================================
# OsdagBridge — Report charts
# =============================================================================
#
#   • Utilization-ratio (UR = Demand / Capacity) charts for the four primary
#     elements: steel plate girders, concrete deck slab, cross bracing, end
#     diaphragms  →  embedded in Section 5.5 (Overall Design Check Summary).
#   • Material-quantity charts (structural steel tonnage; concrete volume vs
#     reinforcement weight)  →  embedded in Chapter 7.
#
# Charts are drawn with matplotlib's object-oriented API on the *Agg* canvas
# (no pyplot / GUI backend), so they are safe to create inside the Qt report
# worker thread.  Every chart is auto-saved as a PNG into the temporary
# ``images`` folder of the report build and embedded through
# latex_tables.figure().  All visual constants come from styles.CHART.
#
# NOTHING here recomputes engineering results: URs are read from the already
# computed output_dict entries (the same ones the tables of Chapter 5 use).
# =============================================================================

from __future__ import annotations

import logging
import os
import textwrap
from typing import Dict, List, Optional, Tuple

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from osdagbridge.core.reports import styles as S

logger = logging.getLogger(__name__)

URItem = Tuple[str, float]          # (label, utilization ratio)

# Element keys, in the order they appear in the report
ELEMENTS = [
    ("girder",   "Steel Plate Girders"),
    ("deck",     "Concrete Deck Slab"),
    ("bracing",  "Cross Bracing"),
    ("diaphragm", "End Diaphragms"),
]

_DECK_LABELS = {
    "bot_uls": "Bottom flexure (ULS)", "top_uls": "Top flexure (ULS)",
    "oh_uls": "Overhang flexure (ULS)",
    "bot_sls_c": "Bottom conc. stress", "bot_sls_s": "Bottom rebar stress",
    "top_sls_c": "Top conc. stress", "top_sls_s": "Top rebar stress",
    "oh_sls_c": "Overhang conc. stress", "oh_sls_s": "Overhang rebar stress",
    "bot_crack": "Bottom crack width", "top_crack": "Top crack width",
    "oh_crack": "Overhang crack width",
    "bot_shear": "One-way shear", "bot_punch": "Punching shear",
    "oh_shear": "Overhang shear", "oh_punch": "Overhang punching",
    "composite_trans_shear": "Transverse shear",
    "composite_crack": "Min. reinforcement",
    "composite_conc_stress": "Composite conc. stress",
    "composite_rebar_stress": "Composite rebar stress",
}

_INVALID_UR = 9.0        # backend uses 9.999 as "capacity is zero" sentinel


def _f(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None          # drop NaN


# ---------------------------------------------------------------------------
# DATA COLLECTION  (read-only, from output_dict / bridges)
# ---------------------------------------------------------------------------

def _girder_items(output_dict: dict) -> Tuple[List[URItem], List[URItem]]:
    """(per-girder max UR, per-check max UR across girders)."""
    per_girder = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    by_girder: Dict[str, float] = {}
    by_check: Dict[str, float] = {}
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):                 # edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            d = _f(chk.get("dcr"))
            if d is None:
                continue
            by_girder[str(g)] = max(by_girder.get(str(g), 0.0), d)
            name = str(chk.get("name", "")).strip() or "check"
            by_check[name] = max(by_check.get(name, 0.0), d)
    return list(by_girder.items()), sorted(by_check.items(), key=lambda kv: -kv[1])


def _deck_items(output_dict: dict) -> List[URItem]:
    dd = output_dict.get("deck_design_results", {}) or {}
    items = []
    for k, v in dd.items():
        if not str(k).startswith("ur_"):
            continue
        f = _f(v)
        if f is None or f >= _INVALID_UR or f <= 0.0:
            continue
        key = str(k)[3:]
        items.append((_DECK_LABELS.get(key, key.replace("_", " ").title()), f))
    return items


def _member_items(bridge) -> List[URItem]:
    """Per panel (pair of girders): worst UR of all its members."""
    items: List[URItem] = []
    if bridge is None:
        return items
    for pair in bridge.get_cb_pairs():
        worst = None
        for member in ("diagonal", "chord"):
            for ft in ("tension", "compression"):
                v = _f(bridge.get_cb_efficiency(pair, member, ft))
                if v is not None and (worst is None or v > worst):
                    worst = v
        if worst is not None:
            items.append((pair, worst))
    return items


def collect_ur_data(output_dict: dict, cb_bridge=None, ed_bridge=None) -> Dict[str, dict]:
    """Collect UR data for the four primary elements.

    Returns ``{element: {"title", "governing", "items": [(label, ur)], "by": str}}``.
    Elements without computed results are omitted.
    """
    data: Dict[str, dict] = {}

    g_by_girder, g_by_check = _girder_items(output_dict)
    if g_by_check:
        data["girder"] = {"title": "Steel Plate Girders", "items": g_by_check,
                          "per_girder": g_by_girder, "by": "check"}
    d_items = _deck_items(output_dict)
    if d_items:
        data["deck"] = {"title": "Concrete Deck Slab", "items": d_items, "by": "check"}
    cb_items = _member_items(cb_bridge)
    if cb_items:
        data["bracing"] = {"title": "Cross Bracing", "items": cb_items, "by": "panel"}
    ed_items = _member_items(ed_bridge)
    if ed_items:
        data["diaphragm"] = {"title": "End Diaphragms", "items": ed_items, "by": "panel"}

    for d in data.values():
        d["governing"] = max(v for _, v in d["items"])
    return data


def component_status(ur_data: Dict[str, dict]) -> Dict[str, Optional[bool]]:
    """element -> True (pass) / False (fail) / None (no result)."""
    return {k: (ur_data[k]["governing"] <= S.STATUS["ur_limit"]) if k in ur_data else None
            for k, _ in ELEMENTS}


# ---------------------------------------------------------------------------
# DRAWING HELPERS
# ---------------------------------------------------------------------------

def _new_fig(size):
    fig = Figure(figsize=size, dpi=S.CHART["dpi"])
    FigureCanvasAgg(fig)
    return fig


def _style_axes(ax, ylabel: str = "Utilization Ratio  (Demand / Capacity)"):
    C = S.CHART
    ax.set_ylabel(ylabel, fontsize=C["label_size"], family=C["font_family"])
    ax.tick_params(axis="both", labelsize=C["tick_size"])
    ax.grid(axis="y", alpha=C["grid_alpha"], linestyle=":")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _threshold(ax, with_label: bool = True):
    th = S.CHART["ur_threshold"]
    ax.axhline(th["value"], color=th["color"], linestyle=th["linestyle"],
               linewidth=th["linewidth"], label=th["label"] if with_label else None, zorder=3)


def _bar_colors(values):
    C = S.CHART
    return [C["ur_fail_color"] if v > S.STATUS["ur_limit"] else C["ur_pass_color"] for v in values]


def _annotate(ax, bars, values):
    for rect, v in zip(bars, values):
        ax.annotate(f"{v:.2f}", (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    fontsize=S.CHART["value_label_size"], fontweight="bold")


def _ylim(ax, values):
    top = max(list(values) + [S.CHART["ur_threshold"]["value"]]) * S.CHART["ur_headroom"]
    ax.set_ylim(0, top)


def _pass_fail_legend(ax):
    from matplotlib.patches import Patch
    handles, _ = ax.get_legend_handles_labels()
    handles += [Patch(color=S.CHART["ur_pass_color"], label="Pass  (UR ≤ 1.0)"),
                Patch(color=S.CHART["ur_fail_color"], label="Fail  (UR > 1.0)")]
    ax.legend(handles=handles, loc="upper right", fontsize=S.CHART["tick_size"], framealpha=0.95)


def _wrap(label: str, width: int = 14) -> str:
    return "\n".join(textwrap.wrap(str(label), width=width)) or str(label)


def _save(fig, path: str) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=S.CHART["dpi"], bbox_inches="tight", facecolor="white")
    return path


# ---------------------------------------------------------------------------
# UTILIZATION-RATIO CHARTS
# ---------------------------------------------------------------------------

def ur_overall_chart(ur_data: Dict[str, dict], path: str) -> Optional[str]:
    """One bar per primary element = its governing (maximum) UR."""
    if not ur_data:
        return None
    C = S.CHART
    keys = [k for k, _ in ELEMENTS if k in ur_data]
    labels = [_wrap(ur_data[k]["title"], 12) for k in keys]
    values = [ur_data[k]["governing"] for k in keys]

    fig = _new_fig(C["ur_overall_size"])
    ax = fig.add_subplot(111)
    bars = ax.bar(labels, values, width=C["bar_width"], color=_bar_colors(values),
                  edgecolor="white", zorder=2)
    _threshold(ax)
    _annotate(ax, bars, values)
    _style_axes(ax)
    _ylim(ax, values)
    ax.set_title("Overall Utilization Ratio of Primary Elements (governing check)",
                 fontsize=C["title_size"], fontweight="bold", family=C["font_family"])
    _pass_fail_legend(ax)
    return _save(fig, path)


def ur_detail_chart(ur_data: Dict[str, dict], path: str) -> Optional[str]:
    """2x2 panel: UR of every check / panel of each primary element."""
    if not ur_data:
        return None
    C = S.CHART
    fig = Figure(figsize=(C["ur_detail_size"][0], C["ur_detail_size"][1] * 2.25), dpi=C["dpi"])
    FigureCanvasAgg(fig)
    axes = fig.subplots(2, 2).flatten()
    for ax, (key, title) in zip(axes, ELEMENTS):
        d = ur_data.get(key)
        if not d:
            ax.axis("off")
            ax.text(0.5, 0.5, f"{title}\n(no result available)", ha="center", va="center",
                    fontsize=C["tick_size"], color="#777777", transform=ax.transAxes)
            continue
        items = d["items"]
        labels = [_wrap(l, 11) for l, _ in items]
        values = [v for _, v in items]
        bars = ax.bar(range(len(values)), values, width=C["bar_width"] + 0.1,
                      color=_bar_colors(values), edgecolor="white", zorder=2)
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels(labels, rotation=0 if len(values) <= 5 else 60,
                           ha="center" if len(values) <= 5 else "right",
                           fontsize=C["tick_size"] - 1.5)
        _threshold(ax, with_label=False)
        _annotate(ax, bars, values) if len(values) <= 10 else None
        _style_axes(ax, ylabel="Utilization Ratio")
        _ylim(ax, values)
        ax.set_title(title, fontsize=C["label_size"], fontweight="bold")
    from matplotlib.lines import Line2D
    th = C["ur_threshold"]
    fig.legend(handles=[Line2D([0], [0], color=th["color"], linestyle=th["linestyle"],
                               linewidth=th["linewidth"], label=th["label"])],
               loc="lower center", ncol=1, fontsize=C["tick_size"], frameon=False)
    fig.suptitle("Utilization Ratio of each check / panel", fontsize=C["title_size"],
                 fontweight="bold", family=C["font_family"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(path, dpi=C["dpi"], bbox_inches="tight", facecolor="white")
    return path


# ---------------------------------------------------------------------------
# MATERIAL-QUANTITY CHARTS  (data = Chapter-7 quantity strings in input_dict)
# ---------------------------------------------------------------------------

def _num(inputs: dict, key: str) -> Optional[float]:
    v = inputs.get(key)
    if v in (None, "", "N.A.", "N.A"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def collect_quantity_data(inputs: dict) -> dict:
    """Steel tonnage per member group, concrete volume, rebar weight."""
    bracing = [_num(inputs, k) for k in ("bracing_top_wt_total", "bracing_bot_wt_total",
                                         "bracing_diag_wt_total")]
    bracing_t = sum(x for x in bracing if x is not None) if any(x is not None for x in bracing) else None
    steel = [
        ("Girders", _num(inputs, "steel_girders_wt_total")),
        ("Cross Bracing", bracing_t),
        ("End Diaphragms", _num(inputs, "end_diaphragm_wt_total")),
    ]
    return {
        "steel": [(n, v) for n, v in steel if v is not None],
        "concrete_m3": _num(inputs, "concrete_deck_vol_total"),
        "rebar_mt": _num(inputs, "rebar_deck_wt_total"),
    }


def steel_tonnage_chart(qty: dict, path: str) -> Optional[str]:
    items = qty.get("steel") or []
    if not items:
        return None
    C = S.CHART
    labels = [n for n, _ in items]
    values = [v for _, v in items]
    fig = _new_fig(C["qty_size"])
    ax = fig.add_subplot(111)
    bars = ax.bar(labels, values, width=C["bar_width"], color=C["qty_colors"][:len(values)],
                  edgecolor="white", zorder=2)
    for rect, v in zip(bars, values):
        ax.annotate(f"{v:,.2f} MT", (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    fontsize=C["value_label_size"], fontweight="bold")
    _style_axes(ax, ylabel="Structural steel (MT)")
    ax.set_ylim(0, max(values) * 1.18 if max(values) > 0 else 1)
    total = sum(values)
    ax.set_title(f"Structural Steel Tonnage  (total {total:,.2f} MT)", fontsize=C["title_size"],
                 fontweight="bold", family=C["font_family"])
    return _save(fig, path)


def concrete_rebar_chart(qty: dict, path: str) -> Optional[str]:
    conc, reb = qty.get("concrete_m3"), qty.get("rebar_mt")
    if conc is None and reb is None:
        return None
    C = S.CHART
    fig = _new_fig(C["qty_size"])
    axes = fig.subplots(1, 2)
    panels = [
        (axes[0], conc, "Concrete volume", "Volume (m³)", "m³", C["concrete_color"]),
        (axes[1], reb, "Reinforcement steel", "Weight (MT)", "MT", C["rebar_color"]),
    ]
    for ax, v, name, ylabel, unit, color in panels:
        if v is None:
            ax.axis("off")
            ax.text(0.5, 0.5, f"{name}\n(not available)", ha="center", va="center",
                    transform=ax.transAxes, color="#777777")
            continue
        bar = ax.bar([name], [v], width=0.45, color=color, edgecolor="white", zorder=2)
        ax.annotate(f"{v:,.2f} {unit}", (bar[0].get_x() + bar[0].get_width() / 2, v),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    fontsize=C["value_label_size"], fontweight="bold")
        _style_axes(ax, ylabel=ylabel)
        ax.set_ylim(0, v * 1.18 if v > 0 else 1)
    fig.suptitle("Concrete Volume (m³)  vs  Reinforcement Steel Weight (MT)",
                 fontsize=C["title_size"], fontweight="bold", family=C["font_family"])
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=C["dpi"], bbox_inches="tight", facecolor="white")
    return path


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def build_report_charts(out_dir: str, output_dict: dict, inputs: dict,
                        cb_bridge=None, ed_bridge=None) -> Tuple[Dict[str, str], dict]:
    """Create every chart as a PNG inside *out_dir*.

    Returns ``(paths, ur_data)`` — ``paths`` maps figure names
    ('ur_overall', 'ur_detail', 'qty_steel', 'qty_concrete') to relative-safe
    file paths (only the charts that could be drawn); ``ur_data`` is the
    collected UR data (also used for the dynamic "Key Design Outcomes").
    Failures are logged and never abort report generation.
    """
    os.makedirs(out_dir, exist_ok=True)
    paths: Dict[str, str] = {}
    ur_data: Dict[str, dict] = {}

    def _try(name, fn, *args):
        try:
            p = fn(*args, os.path.join(out_dir, name + ".png"))
            if p:
                paths[name] = p.replace("\\", "/")
        except Exception as exc:                    # chart problems must not kill the PDF
            logger.warning("Chart '%s' skipped: %s", name, exc)

    try:
        ur_data = collect_ur_data(output_dict, cb_bridge, ed_bridge)
    except Exception as exc:
        logger.warning("UR data collection failed: %s", exc)
    _try("ur_overall", ur_overall_chart, ur_data)
    _try("ur_detail", ur_detail_chart, ur_data)

    try:
        qty = collect_quantity_data(inputs)
        _try("qty_steel", steel_tonnage_chart, qty)
        _try("qty_concrete", concrete_rebar_chart, qty)
    except Exception as exc:
        logger.warning("Quantity charts skipped: %s", exc)
    return paths, ur_data
