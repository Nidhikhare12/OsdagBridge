"""Matplotlib chart generation for the design report.

Every chart is rendered to a PNG file with the non-interactive ``Agg`` backend
and handed to LaTeX as a normal ``\\includegraphics`` target.  Rendering is
deterministic (fixed size, DPI and colours) so that two runs of the same design
produce byte-comparable figures.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow matplotlib.use)

from osdagbridge.core.reports import styles  # noqa: E402

_log = logging.getLogger(__name__)

_PASS_COLOUR = "#" + styles.UR_PASS_COLOR
_FAIL_COLOUR = "#" + styles.UR_FAIL_COLOR
_THRESHOLD_COLOUR = "#" + styles.UR_FAIL_COLOR
_STEEL_COLOUR = "#4C7FB0"
_CONCRETE_COLOUR = "#8A9A8B"
_REBAR_COLOUR = "#B4703F"

_DPI = 200

# Charts are included at roughly 0.9\textwidth, so the figure size below is
# close to the printed size; this keeps 9-10pt labels legible after scaling.
_RC = {
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
}
plt.rcParams.update(_RC)


def _finish(fig, path: str) -> Optional[str]:
    """Save *fig* to *path*, always close it, and return the path on success."""
    try:
        fig.tight_layout()
        fig.savefig(path, dpi=_DPI, bbox_inches="tight")
        return path
    except Exception as exc:  # pragma: no cover - filesystem/backend failures
        _log.warning("chart export failed for %s: %s", path, exc)
        return None
    finally:
        plt.close(fig)


def _as_float(value) -> Optional[float]:
    """Best-effort float conversion; returns None for N.A./blank values."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Utilisation-ratio summary (Section 5.5)
# ---------------------------------------------------------------------------

def ur_summary_png(rows: Iterable[dict], path: str,
                   threshold: float = 1.0) -> Optional[str]:
    """Column chart of demand/capacity ratios against a capacity line.

    The utilization ratio is on the *y* axis and the capacity limit is a
    horizontal red dashed line, so any bar that pokes above the line is a
    failing check.

    Parameters
    ----------
    rows:
        Iterable of dicts with ``label`` (str) and ``ur`` (float).  Rows whose
        ratio is missing or non-numeric are skipped.
    path:
        Destination PNG path.
    threshold:
        Reference line drawn at this value (1.0 = capacity).
    """
    data = []
    for row in rows or []:
        ur = _as_float(row.get("ur"))
        if ur is None:
            continue
        data.append((str(row.get("label", "")).strip(), ur))

    if not data:
        return None

    # Worst check on the left, least critical on the right.
    data.sort(key=lambda item: item[1], reverse=True)
    labels = [label for label, _ in data]
    values = [value for _, value in data]

    fig, ax = plt.subplots(figsize=(6.6, 3.4))

    colours = [_FAIL_COLOUR if v > threshold else _PASS_COLOUR for v in values]
    positions = range(len(values))
    bars = ax.bar(positions, values, color=colours, width=0.68, zorder=3)

    ax.axhline(threshold, color=_THRESHOLD_COLOUR, linestyle="--",
               linewidth=1.4, zorder=4,
               label=f"Capacity limit (UR = {threshold:.1f})")

    limit = max(max(values) * 1.16, threshold * 1.25)
    ax.set_ylim(0, limit)
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.set_title("Utilization Ratio Summary — All Primary Elements")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, rotation=55, ha="right",
                       rotation_mode="anchor", fontsize=7.2)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values):
        # Vertical numbers keep 17 bars readable without overlapping.
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + limit * 0.012, f"{value:.2f}",
                ha="center", va="bottom", fontsize=6.4, rotation=90, zorder=5)

    ax.legend(loc="upper right", fontsize=8, frameon=False)
    return _finish(fig, path)


# ---------------------------------------------------------------------------
# Material quantities (Chapter 7)
# ---------------------------------------------------------------------------

_STEEL_COMPONENTS = [
    ("Girders", ("steel_girders_wt_total",)),
    ("Cross Bracing", ("bracing_top_wt_total", "bracing_bot_wt_total",
                       "bracing_diag_wt_total")),
    ("End Diaphragms", ("end_diaphragm_wt_total",)),
]


def material_steel_png(quantities: dict, path: str) -> Optional[str]:
    """Bar chart of structural-steel tonnage by component.

    One bar per component group (girders, cross bracing, end diaphragms); a
    group whose sub-keys are all missing is skipped so the chart degrades
    gracefully when the bill of materials has no data for it.
    """
    if not quantities:
        return None

    items = []
    for label, keys in _STEEL_COMPONENTS:
        values = [_as_float(quantities.get(key)) for key in keys]
        values = [value for value in values if value is not None]
        if values:
            items.append((label, sum(values)))

    if not items:
        return None

    items.sort(key=lambda item: item[1])
    labels = [label for label, _ in items]
    values = [value for _, value in items]
    total = sum(values) or 1.0

    height = max(2.0, 0.46 * len(items) + 1.0)
    fig, ax = plt.subplots(figsize=(6.6, height))
    bars = ax.barh(labels, values, color=_STEEL_COLOUR, height=0.6, zorder=3)

    limit = max(values) * 1.55 or 1.0
    ax.set_xlim(0, limit)
    ax.set_xlabel("Weight (MT)")
    ax.set_title("Structural Steel Quantities (IS 2062)")
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8)

    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + limit * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{value:.2f} MT  ({100.0 * value / total:.1f}%)",
                va="center", ha="left", fontsize=8)

    ax.text(0.995, -0.22, f"Total structural steel: {total:.2f} MT",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            style="italic")
    return _finish(fig, path)


def material_concrete_rebar_png(quantities: dict, path: str) -> Optional[str]:
    """Deck concrete volume and reinforcement weight as side-by-side panels.

    The two quantities have unrelated units, so they get independent axes
    instead of a twin-axis chart where equal bar heights would imply equal
    amounts.
    """
    if not quantities:
        return None

    concrete = _as_float(quantities.get("concrete_deck_vol_total"))
    rebar = _as_float(quantities.get("rebar_deck_wt_total"))
    if concrete is None and rebar is None:
        return None

    panels = []
    if concrete is not None:
        panels.append(("Deck concrete", concrete, "Volume (m\u00b3)", _CONCRETE_COLOUR, "{:.2f} m\u00b3"))
    if rebar is not None:
        panels.append(("Deck reinforcement", rebar, "Weight (MT)", _REBAR_COLOUR, "{:.2f} MT"))

    fig, axes = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 2.6),
                             squeeze=False)
    for ax, (title, value, unit, colour, fmt) in zip(axes[0], panels):
        bar = ax.bar([0.0], [value], width=0.42, color=colour, zorder=3)
        ax.set_xticks([0.0])
        ax.set_xticklabels([unit], fontsize=8)
        ax.set_xlim(-0.55, 0.55)
        ax.set_ylim(0, value * 1.22 if value else 1.0)
        ax.set_title(title)
        ax.grid(axis="y", color="#DDDDDD", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.text(bar[0].get_x() + bar[0].get_width() / 2, bar[0].get_height(),
                fmt.format(value), ha="center", va="bottom", fontsize=9)

    return _finish(fig, path)
