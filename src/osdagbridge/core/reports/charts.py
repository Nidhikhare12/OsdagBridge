"""Charts for the LaTeX design report.

Charts are drawn with matplotlib's object API (Figure + Agg canvas), not pyplot,
so they never touch the GUI's matplotlib backend and are safe to call from the
report thread. Each helper writes a PNG and returns the LaTeX to embed it, or an
empty string if there is nothing to draw (the report then simply has no chart).
"""
import os
import re
import logging

logger = logging.getLogger(__name__)

PASS_COLOR_HEX = "#91B014"   # Osdag green
FAIL_COLOR_HEX = "#D62728"

_SPLIT_CELLS = re.compile(r"(?<!\\)&")
_RED_WRAP = re.compile(r"^\\textcolor\{red\}\{(.*)\}$")


def parse_ur_rows(rows):
    """Turn Table 5.29 row strings into [(label, ur_float), ...].

    Rows without a numeric UR (placeholders, '---', 'N/A', message rows) are skipped.
    """
    pairs = []
    for row in rows:
        line = row.split("\\\\[", 1)[0]
        cells = [c.strip() for c in _SPLIT_CELLS.split(line)]
        if len(cells) != 5:
            continue
        m = _RED_WRAP.match(cells[4])
        ur_txt = m.group(1) if m else cells[4]
        try:
            ur = float(ur_txt)
        except ValueError:
            continue
        label = cells[0].replace("---", "\u2013").replace("\\&", "&")
        pairs.append((label, ur))
    return pairs


def _draw_ur_chart(pairs, out_path):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.patches import Patch

    n = len(pairs)
    fig = Figure(figsize=(7.0, 0.30 * n + 1.5), dpi=200)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    labels = [p[0] for p in pairs][::-1]            # first row at the top
    vals = [p[1] for p in pairs][::-1]
    colors = [FAIL_COLOR_HEX if v > 1.0 else PASS_COLOR_HEX for v in vals]
    ys = range(n)

    ax.barh(ys, vals, color=colors, height=0.65)
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.0)

    xmax = max(1.15, max(vals) * 1.15)
    ax.set_xlim(0, xmax)
    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Utilization Ratio, UR = demand / capacity", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    for y, v in zip(ys, vals):
        ax.text(v + xmax * 0.008, y, f"{v:.2f}", va="center", fontsize=7.5,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(
        handles=[Patch(color=PASS_COLOR_HEX, label="Pass (UR \u2264 1.0)"),
                 Patch(color=FAIL_COLOR_HEX, label="Fail (UR > 1.0)")],
        loc="lower right", fontsize=8, frameon=False,
    )
    fig.tight_layout()
    fig.savefig(out_path, format="png")


def ur_chart_tex(rows, chart_dir):
    """Draw the UR bar chart for Table 5.29 and return the LaTeX figure block.

    rows       the Table 5.29 row strings
    chart_dir  an existing folder LaTeX can read (the report's temp 'images' folder)
    """
    try:
        pairs = parse_ur_rows(rows)
        if not pairs or not chart_dir:
            return ""
        out_path = os.path.join(chart_dir, "ur_chart.png")
        _draw_ur_chart(pairs, out_path)
        p = out_path.replace("\\", "/")
        return (
            "\n\\begin{figure}[H]\n"
            "\\centering\n"
            "\\includegraphics[width=0.95\\textwidth]{" + p + "}\n"
            "\\caption{Utilization ratio of every design check (bars beyond the dashed line, UR $>$ 1.0, fail).}\n"
            "\\end{figure}\n"
        )
    except Exception:
        logger.exception("UR chart could not be drawn; continuing without it")
        return ""