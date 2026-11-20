"""Matplotlib charts for the report (UR bar chart, material quantities)."""
import os
import tempfile

import matplotlib
matplotlib.use("Agg")          # no GUI window; safe inside the Qt app
import matplotlib.pyplot as plt

GREEN, AMBER, RED = "#91B014", "#E8A317", "#D62728"


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _save(fig, name):
    path = os.path.join(tempfile.mkdtemp(prefix="osdag_chart_"), name)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path.replace("\\", "/")      # LaTeX wants forward slashes


def include_tex(png_path, caption):
    return (
        "\n\\begin{center}\n"
        f"\\includegraphics[width=0.9\\textwidth]{{{png_path}}}\\\\[2pt]\n"
        f"{{\\small\\textit{{{caption}}}}}\n"
        "\\end{center}\n"
    )


def ur_chart(labels, values, title="Utilization Ratios"):
    """Bar chart of UR values with a red dashed limit line at 1.0."""
    pairs = [(l, _num(v)) for l, v in zip(labels, values) if _num(v) is not None]
    if not pairs:
        return None
    names, vals = zip(*pairs)
    colors = [GREEN if v < 0.90 else AMBER if v < 1.0 else RED for v in vals]
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    bars = ax.bar(names, vals, color=colors, width=0.5)
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.3,
               label="UR = 1.0 (limit)")
    ax.set_ylim(0, max(1.15, max(vals) * 1.15))
    ax.set_ylabel("Utilization ratio")
    ax.set_title(title, fontsize=10)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", va="bottom", fontsize=8)
    ax.legend(loc="upper right", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "ur_chart.png")


def material_chart(items, title="Material Quantities (Total Weight)"):
    """items = [(label, total_weight_MT), ...]; skips non-numeric values."""
    pairs = [(l, _num(v)) for l, v in items if _num(v) is not None]
    if not pairs:
        return None
    names, vals = zip(*pairs)
    fig, ax = plt.subplots(figsize=(6.3, 0.45 * len(vals) + 1.2))
    bars = ax.barh(names, vals, color=GREEN)
    ax.invert_yaxis()
    ax.set_xlabel("Total weight (MT)")
    ax.set_title(title, fontsize=10)
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {v:.2f}",
                va="center", fontsize=8)
    ax.set_xlim(0, max(vals) * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "material_chart.png")