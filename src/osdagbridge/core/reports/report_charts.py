"""Data-driven chart creation for the LaTex report generator."""
from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable


def _number(value: Any) -> float | None:
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(mapping: dict[str, Any], names: Iterable[str]) -> float | None:
    for name in names:
        value = _number(mapping.get(name))
        if value is not None:
            return value
    return None


def utilization_rows(checks: Any) -> list[tuple[str, float]]:
    """Extract labelled utilization ratios from the structured check payload.

    The report receives results from several design engines, so both common
    spellings (``ur``, ``dcr`` and ``utilization_ratio``) are accepted.
    """
    rows: list[tuple[str, float]] = []

    def visit(value: Any, label: str = "") -> None:
        if isinstance(value, dict):
            name = str(value.get("name") or value.get("label") or value.get("member") or value.get("check") or label)
            ratio = _first_number(value, ("utilization_ratio", "utilisation_ratio", "ur", "dcr", "ratio"))
            if ratio is not None and name:
                rows.append((name, ratio))
                return
            for key, child in value.items():
                key_label = str(key).replace("_", " ")
                key_ratio = _number(child)
                if key_ratio is not None and any(token in key_label.lower() for token in ("utilization", "utilisation", "dcr", " ratio", " ur")):
                    rows.append((key_label, key_ratio))
                visit(child, str(key).replace("_", " "))
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, label)

    visit(checks)
    # Keep only useful plotted data and make duplicate labels deterministic.
    unique: dict[str, float] = {}
    for label, ratio in rows:
        if ratio >= 0:
            unique[label] = max(ratio, unique.get(label, 0.0))
    return list(unique.items())[:12]


def material_rows(quantities: dict[str, Any]) -> list[tuple[str, float, str]]:
    """Return real computed material quantities; never substitute sample data."""
    sources = (
        ("Structural steel", "steel_girders_wt_total", "MT"),
        ("Cross bracing", "bracing_top_wt_total", "MT"),
        ("Concrete deck", "concrete_deck_vol_total", "m³"),
        ("Reinforcement", "rebar_deck_wt_total", "MT"),
        ("Shear studs", "shear_studs_wt_total", "MT"),
    )
    return [(label, value, unit) for label, key, unit in sources
            if (value := _number(quantities.get(key))) is not None and value >= 0]


def _save_figure(fig) -> bytes:
    stream = BytesIO()
    fig.savefig(stream, format="png", dpi=180, bbox_inches="tight")
    fig.clear()
    return stream.getvalue()


def build_chart_images(checks: Any, quantities: dict[str, Any]) -> dict[str, bytes]:
    """Build report charts from calculated values and return in-memory PNGs.

    Matplotlib is imported lazily so text-only report generation stays usable
    in lean environments.
    """
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except ImportError:
        return {}

    images: dict[str, bytes] = {}
    ratios = utilization_rows(checks)
    if ratios:
        labels, values = zip(*ratios)
        colors = ["#2E7D32" if value <= 1.0 else "#C62828" for value in values]
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        bars = ax.bar(range(len(values)), values, color=colors)
        ax.axhline(1.0, color="#37474F", linestyle="--", linewidth=1.2, label="Limit (UR = 1.0)")
        ax.set_ylabel("Utilization ratio")
        ax.set_title("Design check utilization summary")
        ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
        ax.legend(loc="upper right")
        ax.set_ylim(0, max(1.15, max(values) * 1.15))
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.2f}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        images["utilization_summary"] = _save_figure(fig)
        plt.close(fig)

    materials = material_rows(quantities)
    if materials:
        labels = [row[0] for row in materials]
        values = [row[1] for row in materials]
        units = [row[2] for row in materials]
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        bars = ax.bar(range(len(values)), values, color="#91B014")
        ax.set_ylabel("Quantity (native unit)")
        ax.set_title("Material quantity summary")
        ax.set_xticks(range(len(labels)), labels, rotation=20, ha="right")
        for bar, value, unit in zip(bars, values, units):
            ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.2f} {unit}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        images["material_quantities"] = _save_figure(fig)
        plt.close(fig)
    return images
