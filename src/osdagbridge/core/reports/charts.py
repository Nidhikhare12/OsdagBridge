"""Charts derived only from values already presented in the report."""
import math
from pathlib import Path
from .styles import BRAND_GREEN, CHART_DPI, CHART_SIZE


def _quantity(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def material_values(quantities):
    """Return Chapter 7 values in its displayed units; None means unavailable."""
    bracing = [_quantity(quantities.get(f"bracing_{part}_wt_total"))
               for part in ("top", "bot", "diag")]
    return {
        "Girder steel": _quantity(quantities.get("steel_girders_wt_total")),
        "Cross bracing steel": sum(bracing) if all(v is not None for v in bracing) else None,
        "End diaphragm steel": None,  # no matching Chapter 7 quantity
        "Concrete": _quantity(quantities.get("concrete_deck_vol_total")),
        "Reinforcement steel": _quantity(quantities.get("rebar_deck_wt_total")),
    }


def material_chart(quantities, directory):
    """Write a chart if at least one quantity exists; return its path or None."""
    values = material_values(quantities)
    if all(v is None for v in values.values()):
        return None
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    fig = Figure(figsize=CHART_SIZE, constrained_layout=True)
    FigureCanvasAgg(fig)
    groups = [(["Girder steel", "Cross bracing steel", "End diaphragm steel"], "Weight (tonnes)"),
              (["Concrete"], "Volume (m³)"),
              (["Reinforcement steel"], "Weight (tonnes; estimated in BOQ)")]
    for ax, (labels, unit) in zip(fig.subplots(3, 1), groups):
        for index, label in enumerate(labels):
            value = values[label]
            if value is None:
                ax.text(0.02, index, "Not available", va="center", transform=ax.get_yaxis_transform())
            else:
                ax.barh(index, value, color="#" + BRAND_GREEN)
                ax.annotate(f"{value:.2f}", (value, index), xytext=(4, 0), textcoords="offset points", va="center")
        ax.set_yticks(range(len(labels)), labels)
        ax.set_xlabel(unit)
        ax.margins(x=0.2)
    path = Path(directory) / "material_quantities.png"
    fig.savefig(path, dpi=CHART_DPI)
    fig.clear()
    return str(path)


def girder_utilizations(outputs):
    """Worst explicitly recorded DCR per girder, excluding end-bracing entries."""
    results = (outputs.get("design_results") or {}).get("per_girder") or {}
    values = []
    for name, data in results.items():
        if str(name).startswith("EB") or not isinstance(data, dict):
            continue
        checks = [(value, check.get("check_id")) for check in data.get("checks", [])
                  if isinstance(check, dict)
                  for value in [_quantity(check.get("dcr"))] if value is not None]
        if checks:
            value, check_id = max(checks, key=lambda item: item[0])
            values.append((str(name), value, check_id))
    return values


def girder_utilization_chart(outputs, directory):
    values = girder_utilizations(outputs)
    if not values:
        return None
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = Figure(figsize=CHART_SIZE, constrained_layout=True)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    positions = range(len(values))
    ax.bar(positions, [v[1] for v in values], color="#" + BRAND_GREEN)
    ax.axhline(1.0, color="red", linestyle="--", label="UR = 1.0")
    ax.set_ylabel("Utilization Ratio")
    ax.set_xticks(list(positions), [v[0] for v in values], rotation=20, ha="right")
    for i, (_, value, check_id) in enumerate(values):
        ax.annotate(f"{value:.2f} {'PASS' if value <= 1 else 'FAIL'}\ncheck {check_id}",
                    (i, value), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    ax.margins(y=0.25)
    ax.legend()
    path = Path(directory) / "girder_utilization.png"
    fig.savefig(path, dpi=CHART_DPI)
    fig.clear()
    return str(path)
