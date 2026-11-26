"""Utilization-ratio bar charts for Section 5.5 (built from the Table 5.22 rows)."""
import logging
import os
import re
import tempfile

from osdagbridge.core.reports import styles as S

log = logging.getLogger(__name__)

GROUPS = [
    ("Steel Plate Girders", ("Girder",)),
    ("Concrete Deck Slab", ("Deck", "Transverse Shear (slab)", "Crack Width (slab)")),
    ("Cross Bracing", ("Cross Bracing",)),
    ("End Diaphragms", ("End Diaphragm",)),
]


def _cells(row):
    row = re.sub(r"\s*\\\\(\[[^\]]*\])?\s*(\\hline)?\s*$", "", row.strip())
    return [c.strip() for c in re.split(r"(?<!\\)&", row)]


def _ur(cell):
    m = re.search(r"\d+\.?\d*", cell.replace(r"\textcolor{red}", ""))
    return float(m.group()) if m else None


def collect(rows):
    """[(label, group, ur)] from Table 5.22 row strings; skips rows without a numeric UR."""
    out = []
    for r in rows:
        c = _cells(r)
        if len(c) != 5:
            continue
        label = c[0].replace("\\textbf{", "").replace("}", "").replace("---", "-").strip()
        ur = _ur(c[4])
        if ur is None:
            continue
        for g, prefixes in GROUPS:
            if c[0].strip().startswith(prefixes):
                out.append((label, g, ur))
                break
    return out


def _bar_chart(labels, values, path, rotate=0):
    from matplotlib.figure import Figure
    C = S.CHART
    fig = Figure(figsize=C["figsize"], dpi=C["dpi"])
    ax = fig.subplots()
    colors = [C["fail_color"] if v > 1.0 else C["pass_color"] for v in values]
    bars = ax.bar(range(len(values)), values, color=colors, width=0.6)
    ax.axhline(1.0, color=C["threshold_color"], linestyle=C["threshold_style"],
               linewidth=1.4, label="UR = 1.0")
    ax.set_ylabel("Utilization Ratio")
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, rotation=rotate, ha="right" if rotate else "center", fontsize=7)
    ax.set_ylim(0, max(1.15, max(values) * 1.18))
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=C["dpi"], bbox_inches="tight")


def make_chart_files(rows, outdir):
    """Write PNGs into outdir; return [(path, caption)]."""
    items = collect(rows)
    if not items:
        return []
    files = []
    gov = []
    for g, _p in GROUPS:
        urs = [u for (_l, gg, u) in items if gg == g]
        if urs:
            gov.append((g, max(urs)))
    if gov:
        p = os.path.join(outdir, "ur_by_element.png")
        _bar_chart([g for g, _ in gov], [u for _, u in gov], p)
        files.append((p, "Governing utilization ratio (Demand / Capacity) for each primary element"))
    p = os.path.join(outdir, "ur_by_check.png")
    _bar_chart([l for l, _, _ in items], [u for _, _, u in items], p, rotate=40)
    files.append((p, "Utilization ratio (Demand / Capacity) for every design check"))
    return files


def ur_charts_latex(rows):
    """LaTeX figures for Section 5.5; empty string if nothing can be plotted."""
    try:
        outdir = tempfile.mkdtemp(prefix="osdagcharts")
        out = []
        for path, cap in make_chart_files(rows, outdir):
            out.append(
                "\\needspace{14\\baselineskip}\n\\begin{figure}[H]\n\\centering\n"
                "\\includegraphics[width=" + S.FIGURE_WIDTH + "]{" + path.replace("\\", "/") + "}\n"
                "\\caption{" + cap + "}\n\\end{figure}\n"
            )
        return "\n\\vspace{1em}\n" + "\n".join(out) if out else ""
    except Exception as exc:
        log.warning("UR charts skipped: %s", exc)
        return ""
