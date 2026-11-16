"""Data-driven chart creation for the LaTex report generator."""
from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable
import math
from .styles import BRAND_GREEN, PASS_GREEN, FAIL_RED


def _number(value: Any) -> float | None:
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        number = float(value)
        return number if math.isfinite(number) and not isinstance(value, bool) else None
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


def component_utilizations(outputs):
    """Read the four component result schemas used by the desktop designers.

    Missing/nonfinite values stay unavailable; they never become passing zeros.
    """
    def maximum(values):
        valid = [n for v in values if (n := _number(v)) is not None and n >= 0]
        return max(valid) if valid else None

    girders = (outputs.get('design_results') or {}).get('per_girder') or {}
    girder = maximum(check.get('dcr') for name, data in girders.items()
                     if not str(name).startswith('EB')
                     for check in (data.get('checks') or []))
    deck = maximum(value for key, value in (outputs.get('deck_design_results') or {}).items()
                   if key.startswith('ur_'))
    def bracing(key):
        return maximum(raw.get('Member.efficiency', raw.get('Optimum.UR'))
                       for members in (outputs.get(key) or {}).values()
                       for forces in members.values() for raw in forces.values()
                       if isinstance(raw, dict))
    return [('Steel plate girders', girder), ('Concrete deck slab', deck),
            ('Cross bracing', bracing('crossbracing_design_results')),
            ('End diaphragms', bracing('end_diaphragm_design_results'))]


def _save_figure(fig) -> bytes:
    stream = BytesIO()
    fig.savefig(stream, format="png", dpi=180, bbox_inches="tight")
    fig.clear()
    return stream.getvalue()


def build_chart_images(checks: Any, quantities: dict[str, Any], outputs=None) -> dict[str, bytes]:
    """Build report charts from calculated values and return in-memory PNGs.

    Matplotlib is imported lazily so text-only report generation stays usable
    in lean environments.
    """
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError:
        return {}

    images: dict[str, bytes] = {}
    ratios = component_utilizations(outputs) if outputs is not None else utilization_rows(checks)
    if ratios:
        labels, values = zip(*ratios)
        colors = ['#B0BEC5' if value is None else '#' + (PASS_GREEN if value <= 1.0 else FAIL_RED) for value in values]
        fig = Figure(figsize=(8.5, 4.6))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        bars = ax.bar(range(len(values)), [v or 0 for v in values], color=colors)
        ax.axhline(1.0, color='#' + FAIL_RED, linestyle="--", linewidth=1.2, label="Limit (UR = 1.0)")
        ax.set_ylabel("Utilization ratio")
        ax.set_title("Design check utilization summary")
        ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
        ax.legend(loc="upper right")
        ax.set_ylim(0, max(1.15, max(v or 0 for v in values) * 1.20))
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value or 0, 'Unavailable' if value is None else f"{value:.2f}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        images["utilization_summary"] = _save_figure(fig)

    # Unlike units must not share a quantitative axis. Three panels use their
    # own units and show unavailable quantities explicitly.
    def quantity(key):
        n = _number(quantities.get(key))
        return n if n is not None and n >= 0 else None
    parts = [quantity('bracing_' + name + '_wt_total') for name in ('top', 'bot', 'diag')]
    cb = sum(parts) if all(v is not None for v in parts) else None
    fig = Figure(figsize=(10, 4.3))
    FigureCanvasAgg(fig)
    axes = fig.subplots(1, 3, gridspec_kw={'width_ratios': [2, 1, 1]})
    groups = [(['Girders', 'Cross bracing', 'End diaphragms'],
               [quantity('steel_girders_wt_total'), cb, quantity('end_diaphragms_wt_total')], 'Structural steel (MT)'),
              (['Deck'], [quantity('concrete_deck_vol_total')], 'Concrete volume (m³)'),
              (['Reinforcement'], [quantity('rebar_deck_wt_total')], 'Reinforcement weight (MT)')]
    for ax, (labels, values, title) in zip(axes, groups):
        bars = ax.bar(range(len(values)), [v or 0 for v in values], color='#' + BRAND_GREEN)
        ax.set_title(title, fontsize=9)
        ax.set_xticks(range(len(labels)), labels, rotation=25, ha='right', fontsize=8)
        ax.set_ylim(0, max(1, max(v or 0 for v in values) * 1.25))
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, value or 0,
                    'N/A' if value is None else f'{value:.2f}', ha='center', va='bottom', fontsize=8)
    fig.tight_layout()
    images['material_quantities'] = _save_figure(fig)
    return images
