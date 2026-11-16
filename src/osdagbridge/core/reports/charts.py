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

# ---------------------------------------------------------------------------
# Chapter 7: material take-off charts
# ---------------------------------------------------------------------------
_NUM = re.compile(r"-?\d+(?:\.\d+)?")

# (label, input_dict key prefix, material group)
_BOM_ITEMS = [
    ("Girders (steel)",        "steel_girders",  "Structural steel"),
    ("Bracing - top chord",    "bracing_top",    "Structural steel"),
    ("Bracing - bottom chord", "bracing_bot",    "Structural steel"),
    ("Bracing - diagonals",    "bracing_diag",   "Structural steel"),
    ("Shear studs",            "shear_studs",    "Structural steel"),
    ("Reinforcement (Fe 500)", "rebar_deck",     "Reinforcement"),
    ("Deck slab concrete",     "concrete_deck",  "Concrete"),
    ("Crash barrier",          "crash_barrier",  "Concrete"),
]
_GROUP_COLORS = {
    "Structural steel": "#91B014",
    "Reinforcement":    "#4F6B0A",
    "Concrete":         "#B8B8B8",
}


def parse_bom_weights(input_dict):
    """Read the total weight (MT) of each BOM item from the report inputs.

    Returns [(label, group, weight_mt), ...]; items with no numeric weight are skipped.
    """
    out = []
    for label, prefix, group in _BOM_ITEMS:
        m = _NUM.search(str(input_dict.get(prefix + "_wt_total", "")).replace(",", ""))
        if m:
            out.append((label, group, float(m.group())))
    return out


def _draw_material_chart(items, out_path):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    # Panel A: total weight by material group
    groups = {}
    for _, g, w in items:
        groups[g] = groups.get(g, 0.0) + w
    g_names = [g for g in _GROUP_COLORS if groups.get(g, 0) > 0]
    g_vals = [groups[g] for g in g_names]
    total = sum(g_vals)

    fig = Figure(figsize=(7.0, 3.6), dpi=200)
    FigureCanvasAgg(fig)
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    wedges, _ = ax1.pie(
        g_vals, colors=[_GROUP_COLORS[g] for g in g_names], startangle=90,
        counterclock=False, wedgeprops=dict(width=0.42, edgecolor="white"),
    )
    ax1.set_title("Weight by material", fontsize=9)
    ax1.text(0, 0, f"{total:.1f} MT\ntotal", ha="center", va="center", fontsize=8)
    ax1.legend(
        wedges, [f"{g}: {v:.2f} MT ({100 * v / total:.0f}%)" for g, v in zip(g_names, g_vals)],
        loc="upper center", bbox_to_anchor=(0.5, 0.02), fontsize=7, frameon=False,
    )

    # Panel B: steel items only (concrete would dwarf everything else)
    steel = [(l, g, w) for l, g, w in items if g != "Concrete"]
    steel = steel[::-1]                                  # first item at the top
    ys = range(len(steel))
    ax2.barh(ys, [w for _, _, w in steel],
             color=[_GROUP_COLORS[g] for _, g, _ in steel], height=0.65)
    ax2.set_yticks(list(ys))
    ax2.set_yticklabels([l for l, _, _ in steel], fontsize=7.5)
    xmax = max(w for _, _, w in steel) * 1.25
    ax2.set_xlim(0, xmax)
    for y, (_, _, w) in zip(ys, steel):
        ax2.text(w + xmax * 0.01, y, f"{w:.2f}", va="center", fontsize=7.5)
    ax2.set_xlabel("Total weight (MT)", fontsize=8)
    ax2.tick_params(axis="x", labelsize=7.5)
    ax2.set_title("Steel and reinforcement items", fontsize=9)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, format="png")


def material_chart_tex(input_dict, chart_dir):
    """Draw the Chapter 7 material charts and return the LaTeX figure block ('' if no data)."""
    try:
        items = parse_bom_weights(input_dict or {})
        if len(items) < 2 or sum(w for _, _, w in items) <= 0 or not chart_dir:
            return ""
        if not any(g != "Concrete" and w > 0 for _, g, w in items):
            return ""
        out_path = os.path.join(chart_dir, "material_chart.png")
        _draw_material_chart(items, out_path)
        p = out_path.replace("\\", "/")
        return (
            "\n\\begin{figure}[H]\n"
            "\\centering\n"
            "\\includegraphics[width=\\textwidth]{" + p + "}\n"
            "\\caption{Material quantities from Table 7.1: total weight by material (left) "
            "and individual steel and reinforcement items (right).}\n"
            "\\end{figure}\n"
        )
    except Exception:
        logger.exception("Material chart could not be drawn; continuing without it")
        return ""