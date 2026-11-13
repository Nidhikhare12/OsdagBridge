"""Charts backed only by report payload/design-result values."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ratio(value: Any) -> float | None:
    if not isinstance(value, Mapping):
        return None
    for key in ("utilization_ratio", "utilisation_ratio", "dcr", "efficiency", "ur"):
        result = _number(value.get(key))
        if result is not None:
            return result
    demand, capacity = _number(value.get("demand")), _number(value.get("capacity"))
    return demand / capacity if demand is not None and capacity and capacity > 0 else None


def _max_ratio(value: Any) -> float | None:
    if isinstance(value, Mapping):
        own = _ratio(value)
        nested = [_max_ratio(v) for v in value.values()]
        values = [v for v in [own, *nested] if v is not None]
        return max(values) if values else None
    if isinstance(value, (list, tuple)):
        values = [_max_ratio(v) for v in value]
        values = [v for v in values if v is not None]
        return max(values) if values else None
    return None


def utilization_ratios(output_dict: Mapping[str, Any]) -> dict[str, float]:
    """Extract, never fabricate, component utilisation ratios from result blobs."""
    results = output_dict.get("design_results", {}) or {}
    ratios: dict[str, float] = {}
    girder = _max_ratio(results.get("per_girder"))
    deck = _max_ratio(output_dict.get("deck_design_results"))
    bracing = _max_ratio(output_dict.get("crossbracing_design_results"))
    diaphragm = _max_ratio(output_dict.get("end_diaphragm_design_results"))
    for label, value in (("Steel Plate Girders", girder), ("Concrete Deck Slab", deck),
                         ("Cross Bracing", bracing), ("End Diaphragms", diaphragm)):
        if value is not None:
            ratios[label] = value
    return ratios


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:  # dependency error is actionable, not hidden
        raise RuntimeError("Matplotlib is required to generate report charts.") from exc


def utilization_chart(output_dict: Mapping[str, Any], destination: Path) -> Path | None:
    ratios = utilization_ratios(output_dict)
    if not ratios:
        return None
    plt = _plt()
    destination.parent.mkdir(parents=True, exist_ok=True)
    labels, values = list(ratios), list(ratios.values())
    fig, axis = plt.subplots(figsize=(8.2, 4.4), constrained_layout=True)
    colors = ["#2E6F95" if value <= 1.0 else "#B3261E" for value in values]
    bars = axis.bar(labels, values, color=colors, edgecolor="#0B2E4F")
    axis.axhline(1.0, color="#B3261E", linestyle="--", linewidth=1.5, label="UR = 1.0 limit")
    axis.set_ylabel("Utilization Ratio (Demand / Capacity)")
    axis.set_ylim(0, max(1.15, max(values) * 1.18))
    axis.tick_params(axis="x", rotation=15)
    axis.legend(frameon=False, loc="upper left")
    for bar, value in zip(bars, values):
        axis.annotate(f"{value:.2f}", (bar.get_x() + bar.get_width() / 2, value),
                      ha="center", va="bottom", fontsize=9)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return destination


def material_charts(quantities: Mapping[str, Any], destination: Path) -> tuple[Path | None, Path | None]:
    """Create Chapter 7 charts only for numeric material take-off values."""
    plt = _plt()
    destination.mkdir(parents=True, exist_ok=True)
    steel = {
        "Girders": _number(quantities.get("steel_girders_wt_total")),
        "Cross bracing": sum(v for v in (_number(quantities.get("bracing_top_wt_total")),
                                           _number(quantities.get("bracing_bot_wt_total")),
                                           _number(quantities.get("bracing_diag_wt_total"))) if v is not None),
    }
    concrete = {"Concrete (m³)": _number(quantities.get("concrete_deck_vol_total")),
                "Reinforcement (MT)": _number(quantities.get("rebar_deck_wt_total"))}

    def save(values: Mapping[str, float | None], path: Path, ylabel: str) -> Path | None:
        clean = {k: v for k, v in values.items() if v is not None}
        if not clean:
            return None
        fig, ax = plt.subplots(figsize=(6.8, 3.8), constrained_layout=True)
        bars = ax.bar(clean.keys(), clean.values(), color="#2E6F95", edgecolor="#0B2E4F")
        ax.set_ylabel(ylabel)
        for bar, value in zip(bars, clean.values()):
            ax.annotate(f"{value:.2f}", (bar.get_x() + bar.get_width()/2, value), ha="center", va="bottom")
        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        return path
    return (save(steel, destination / "structural_steel_quantities.png", "Quantity (MT)"),
            save(concrete, destination / "concrete_reinforcement_quantities.png", "Quantity (units shown in labels)"))
