"""Utilisation-ratio bar charts for the Design Checks summary.

Renders one bar chart per member group (girders, deck slab, cross bracing,
end diaphragms) from the same demand/capacity ratios shown in the Section 5.5
summary table, with a red dashed reference line at UR = 1.0. Charts are
rendered headless with the Agg backend and embedded as figures.
"""

from . import styles

# Brand green for bars (matches osdagGreen), red for the UR = 1.0 limit line.
_BAR_COLOR = "#" + styles.COLOR_BRAND
_LIMIT_COLOR = styles.COLOR_FAIL


def render_ur_bars(title, points, out_path):
    """Render one UR bar chart.

    points is a list of (label, ur) pairs with numeric ur. Returns True when
    the figure was written, False when there is nothing to plot.
    """
    return render_bar_chart(
        title, points, "Utilisation Ratio (Demand / Capacity)", out_path,
        limit=(1.0, "UR = 1.0"), min_top=1.25)


def render_bar_chart(title, points, ylabel, out_path, limit=None,
                     min_top=0.0, value_fmt="{:.2f}"):
    """Render a labelled bar chart with an optional dashed limit line.

    points is a list of (label, value) pairs with numeric value; limit is a
    (y, legend label) pair drawn as a red dashed line, or None. Returns True
    when the figure was written, False when there is nothing to plot.
    """
    import math
    pts = [(lbl, float(v) if v is not None else None) for lbl, v in points]
    pts = [(lbl, v if v is not None and math.isfinite(v) else None)
           for lbl, v in pts]
    if not pts:
        return False

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [p[0] for p in pts]
    values = [p[1] if p[1] is not None else 0.0 for p in pts]

    fig_w = max(6.5, 0.9 * len(pts) + 2.5)
    fig, ax = plt.subplots(figsize=(fig_w, 3.6), dpi=200)

    bars = ax.bar(range(len(pts)), values, width=0.55, color=_BAR_COLOR,
                  edgecolor="black", linewidth=0.6, zorder=3)

    if limit is not None:
        ax.axhline(limit[0], color=_LIMIT_COLOR, linestyle="--", linewidth=1.4,
                   zorder=4, label=limit[1])

    top = max(min_top, max(values) * 1.18, (limit[0] * 1.18 if limit else 0.0))
    ax.set_ylim(0.0, top)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, fontweight="bold")

    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.tick_params(axis="y", labelsize=8)

    for rect, (_, raw) in zip(bars, pts):
        v = raw if raw is not None else 0.0
        if raw is None:
            rect.set_visible(False)
        ax.text(rect.get_x() + rect.get_width() / 2.0, v + top * 0.015,
                value_fmt.format(v) if raw is not None else "N/A", ha="center", va="bottom", fontsize=8)

    ax.grid(axis="y", color="0.85", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    if limit is not None:
        ax.legend(loc="upper left", fontsize=8, frameon=False)

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return True
