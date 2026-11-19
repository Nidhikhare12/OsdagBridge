from matplotlib.backends.backend_pdf import FigureCanvasPdf
from matplotlib.figure import Figure

from .design_summary import governing, verdict


def _save_chart(directory, filename, labels, values, title, ylabel, colors, units, ur=False):
    figure = Figure(figsize=(7.2, 3.8))
    FigureCanvasPdf(figure)
    axis = figure.subplots()
    heights = [value if value is not None else 0 for value in values]
    bars = axis.bar(labels, heights, color=colors, width=0.55)
    axis.set_title(title, fontsize=12, fontweight="bold", pad=10)
    axis.set_ylabel(ylabel)
    axis.set_axisbelow(True)
    axis.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    if ur:
        axis.axhline(1.0, color="#c00000", linestyle="--", linewidth=1.3, label="UR = 1.0")
        axis.legend(loc="upper right", frameon=False, fontsize=9)
    axis.set_ylim(0, max([1.0, *heights]) * 1.25)
    for bar, value, unit in zip(bars, values, units):
        text = "N/A" if value is None else f"{value:.2f}{unit}"
        axis.annotate(text, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                      xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9)
    figure.tight_layout()
    figure.savefig(directory / filename, bbox_inches="tight")
    return f"assets/{filename}"


def utilization_chart(directory, groups):
    maxima = [governing(checks) for checks in groups.values()]
    colors = {"Fail": "#b55353", "Pass": "#6aa84f", "Incomplete": "#9e9e9e",
              "Warning": "#c27c3a", "N/A": "#9e9e9e"}
    return _save_chart(
        directory, "utilization_ratio_summary.pdf",
        ["Steel Plate\nGirders", "Concrete\nDeck Slab", "Cross\nBracing", "End\nDiaphragms"],
        [item.ur if item else None for item in maxima], "Utilization Ratio Summary",
        "Utilization Ratio (Demand / Capacity)",
        [colors[verdict(checks)] for checks in groups.values()], [""] * 4, ur=True,
    )


def materials_charts(directory, quantities):
    def total(key):
        value = quantities.get(key)
        return value if isinstance(value, (int, float)) else None

    bracing = [total(f"bracing_{part}_wt_total") for part in ("top", "bot", "diag")]
    steel = _save_chart(
        directory, "material_steel_quantities.pdf",
        ["Girders", "Cross Bracing", "End Diaphragms"],
        [total("steel_girders_wt_total"), sum(bracing) if None not in bracing else None,
         total("end_diaphragm_wt_total")],
        "Structural Steel Tonnage", "Weight (t)",
        ["#3b6ea8", "#6aa84f", "#c27c3a"], [" t"] * 3,
    )
    concrete_rebar = _save_chart(
        directory, "material_concrete_rebar_quantities.pdf",
        ["Concrete Volume", "Reinforcement Weight\n(Estimate)"],
        [total("concrete_deck_vol_total"), total("rebar_deck_wt_total")],
        "Deck Concrete and Reinforcement", "Quantity (m³ / t)",
        ["#7a9cc6", "#b55353"], [" m³", " t"],
    )
    return steel, concrete_rebar
