"""Charts derived only from values already presented in the report."""
import re
from pathlib import Path
from textwrap import fill
from .styles import BRAND_GREEN, CHART_DPI, CHART_SIZE
from .utilization import component_checks, governing, nonnegative as _quantity, outcome
from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS


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
        ax.set_ylim(-0.5, len(labels) - 0.5)
        ax.set_xlabel(unit)
        ax.margins(x=0.2)
    path = Path(directory) / "material_quantities.png"
    fig.savefig(path, dpi=CHART_DPI)
    fig.clear()
    return str(path)


def girder_utilizations(outputs, inputs=None):
    """Worst explicitly recorded DCR per girder, excluding end-bracing entries."""
    results = (outputs.get("design_results") or {}).get("per_girder") or {}
    try:
        count = int((inputs or {}).get(KEY_TS_NO_OF_GIRDERS))
        count = count if count > 0 else None
    except (TypeError, ValueError):
        count = None
    values = []
    for name, data in results.items():
        if str(name).startswith("EB") or not isinstance(data, dict):
            continue
        match = re.fullmatch(r"G(\d+)", str(name))
        if count is not None and (not match or not 1 <= int(match.group(1)) <= count):
            continue
        checks = [(value, check.get("check_id")) for check in data.get("checks", [])
                  if isinstance(check, dict)
                  for value in [_quantity(check.get("dcr"))] if value is not None]
        if checks:
            value, check_id = max(checks, key=lambda item: item[0])
            values.append((str(name), value, check_id))
    return values


def girder_utilization_chart(outputs, directory, inputs=None):
    """Plot governing computed ratios across all four design components."""
    components = component_checks(outputs, inputs or {})
    if not any(components.values()):
        return None
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = Figure(figsize=CHART_SIZE, constrained_layout=True)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    rows = [(label, governing(checks), outcome(checks)) for label, checks in components.items()]
    limits = [check.ratio for _, check, _ in rows if check]
    scale = max(1.0, *limits)
    ax.set_xlim(0, scale * 1.3)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.axvline(1.0, color="red", linestyle="--", label="UR = 1.0")
    ax.set_xlabel("Reported utilization ratio")
    labels = []
    for i, (component, check, status) in enumerate(rows):
        if check is None:
            labels.append(component)
            ax.text(0.02, i, "Not available", transform=ax.get_yaxis_transform(), va="center")
            continue
        detail = " ".join(part for part in (check.member, check.label) if part)
        labels.append(component + "\n" + fill(detail, 27))
        ax.barh(i, check.ratio, height=0.52, color="#" + BRAND_GREEN)
        ax.text(scale * 1.035, i, f"{check.ratio:.3f}  {status}", va="center", fontsize=9)
    ax.set_yticks(range(len(rows)), labels)
    ax.legend(loc="lower right")
    path = Path(directory) / "component_utilization.png"
    fig.savefig(path, dpi=CHART_DPI)
    fig.clear()
    return str(path)
