"""Matplotlib charts embedded in the OsdagBridge PDF report.

Charts are drawn only from values the chapters already extracted from the
design output -- nothing is computed or assumed here. Every function writes a
PNG and returns its path, or returns None when there is nothing to plot (the
caller then omits the figure), so a missing value never crashes the report.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Status colours: reserved for PASS / FAIL only and always paired with a text
# label, so the result never depends on colour alone (greyscale print, CVD).
PASS_COLOR = "#0ca30c"
FAIL_COLOR = "#d03b3b"
LIMIT_COLOR = "#d03b3b"
INK = "#1f1f1f"           # values, labels
INK_MUTED = "#5f5f5f"     # axis text, notes
GRID = "#d9d9d9"
NO_DATA_EDGE = "#8a8a8a"

UR_LIMIT = 1.0

# The four structural elements of the Section 5.5 summary, in display order.
UR_ELEMENTS = (
    "Steel Plate Girders",
    "Concrete Deck Slab",
    "Cross Bracing",
    "End Diaphragms",
)


def _pyplot():
    import matplotlib
    matplotlib.use("Agg")  # no display needed (also safe inside the Qt GUI)
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        # Computer Modern, matching the report's LaTeX body text.
        "font.family": "serif",
        "font.serif": ["cmr10", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False,
        "font.size": 9,
        "axes.edgecolor": INK_MUTED,
        "axes.labelcolor": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
    })
    return plt


def governing_by_element(ur_records, elements=UR_ELEMENTS):
    """Overall utilization of each element = its highest UR over all checks.

    An element is only as safe as its most critical check, so the governing
    (maximum) ratio is the element's overall utilization; a FAIL in any one
    check therefore shows as a FAIL for the element.

    ur_records: iterable of (element, check_name, ur).
    Returns {element: (ur, check_name) or None when the element has no UR}.
    """
    out = {e: None for e in elements}
    for element, check, ur in ur_records:
        if element not in out or ur is None:
            continue
        if out[element] is None or ur > out[element][0]:
            out[element] = (float(ur), check)
    return out


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _limit_line(ax, horizontal=True):
    kw = dict(color=LIMIT_COLOR, linestyle=(0, (5, 3)), linewidth=1.3, zorder=4)
    (ax.axhline if horizontal else ax.axvline)(UR_LIMIT, **kw)


def utilization_summary_chart(ur_records, out_path, no_data_text=None):
    """Bar chart of the governing UR of the four structural elements.

    no_data_text: {element: short reason} shown for elements without a UR.
    Returns out_path, or None if no element has a UR.
    """
    gov = governing_by_element(ur_records)
    if not any(gov.values()):
        return None
    no_data_text = no_data_text or {}
    plt = _pyplot()

    values = [g[0] if g else 0.0 for g in gov.values()]
    top = max(1.25, max(values) * 1.22)

    fig, ax = plt.subplots(figsize=(6.4, 3.1), dpi=200)
    _style_axes(ax)
    x = range(len(UR_ELEMENTS))
    for i, element in zip(x, UR_ELEMENTS):
        g = gov[element]
        if g is None:
            # No result is not a zero result: draw an empty dashed outline.
            ax.bar(i, top * 0.18, width=0.56, facecolor="none", edgecolor=NO_DATA_EDGE,
                   linestyle=(0, (3, 2)), linewidth=0.9, zorder=3)
            reason = no_data_text.get(element, "No result")
            ax.text(i, top * 0.18 + top * 0.025, reason, ha="center", va="bottom",
                    fontsize=8.5, color=INK_MUTED, linespacing=1.1, zorder=5)
            continue
        ur, _check = g
        fail = ur > UR_LIMIT
        ax.bar(i, ur, width=0.56, color=FAIL_COLOR if fail else PASS_COLOR,
               hatch="////" if fail else None, edgecolor="white", linewidth=0.0, zorder=3)
        # Labels that would sit on the dashed limit line go just above it.
        label_y = ur + top * 0.02
        if UR_LIMIT - top * 0.12 < ur <= UR_LIMIT:
            label_y = UR_LIMIT + top * 0.025
        ax.text(i, label_y, f"{ur:.2f}\n{'FAIL' if fail else 'PASS'}",
                ha="center", va="bottom", fontsize=9.5, color=INK, fontweight="bold",
                linespacing=1.15, zorder=5,
                bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"))

    _limit_line(ax)
    # Label the limit in the right margin so it never overlaps a bar.
    ax.annotate("UR = 1.0\nlimit", xy=(1.0, UR_LIMIT), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                fontsize=8.5, color=LIMIT_COLOR, linespacing=1.1, annotation_clip=False)

    labels = []
    for element in UR_ELEMENTS:
        g = gov[element]
        labels.append(element + ("\n(" + g[1] + ")" if g else "\n "))
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9.5, color=INK, linespacing=1.3)
    ax.tick_params(axis="x", length=0, pad=6)
    ax.set_xlim(-0.6, len(UR_ELEMENTS) - 0.4)
    ax.set_ylim(0, top)
    ax.set_ylabel("Utilization Ratio (UR)", fontsize=9.5)
    ax.set_xlabel("Structural element (governing check)", color=INK_MUTED, labelpad=6)

    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return out_path


def utilization_detail_chart(ur_records, out_path):
    """Horizontal bars of every individual check, grouped by element."""
    rows = [(e, c, ur) for e in UR_ELEMENTS for (e2, c, ur) in ur_records if e2 == e and ur is not None]
    if not rows:
        return None
    plt = _pyplot()

    # Lay out top-to-bottom with a gap row between element groups.
    ys, labels, vals, group_spans = [], [], [], []
    y = 0.0
    for element in UR_ELEMENTS:
        group = [r for r in rows if r[0] == element]
        if not group:
            continue
        start = y
        for _e, check, ur in group:
            ys.append(y); labels.append(check); vals.append(ur)
            y += 1.0
        group_spans.append((element, start, y - 1.0))
        y += 0.8

    top = max(1.25, max(vals) * 1.15)
    fig_h = 0.9 + 0.24 * len(vals) + 0.2 * len(group_spans)
    fig, ax = plt.subplots(figsize=(6.4, fig_h), dpi=200)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    for yy, ur in zip(ys, vals):
        fail = ur > UR_LIMIT
        ax.barh(yy, ur, height=0.62, color=FAIL_COLOR if fail else PASS_COLOR,
                hatch="////" if fail else None, linewidth=0.0, zorder=3)
        lx = ur + top * 0.01
        if UR_LIMIT - top * 0.08 < ur <= UR_LIMIT:
            lx = UR_LIMIT + top * 0.012   # keep clear of the dashed limit line
        ax.text(lx, yy, f"{ur:.2f}" + ("  FAIL" if fail else ""),
                va="center", ha="left", fontsize=8, color=INK,
                fontweight="bold" if fail else "normal", zorder=5)

    _limit_line(ax, horizontal=False)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8, color=INK)
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.set_xlim(0, top)
    ax.set_xlabel("Utilization Ratio, UR = Demand / Capacity  (dashed line: UR = 1.0 limit)")

    # Element group names in the left margin, above each group.
    for element, y0, _y1 in group_spans:
        ax.annotate(element, xy=(0, y0 - 0.62), xycoords=("axes fraction", "data"),
                    xytext=(-4, 0), textcoords="offset points", ha="right", va="center",
                    fontsize=8, fontweight="bold", color=INK, annotation_clip=False)

    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return out_path


def safe_chart(func, *args, **kwargs):
    """Run a chart function; log and return None on any failure so a plotting
    problem can never stop the report from compiling."""
    try:
        return func(*args, **kwargs)
    except Exception:  # noqa: BLE001 - charts are optional decoration
        logger.exception("Report chart %s failed; figure omitted", getattr(func, "__name__", func))
        return None
