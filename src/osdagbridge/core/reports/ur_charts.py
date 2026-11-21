
"""Generate utilization-ratio (UR) summary charts for Chapter 5."""

from io import BytesIO
import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from osdagbridge.core.bridge_types.plate_girder.results_data import (
    _extract_osdag_summary,
)


UR_LIMIT = 1.0

CHARTS = {
    "ur_steel_girders": "Steel Plate Girders",
    "ur_deck_slab": "Concrete Deck Slab",
    "ur_cross_bracing": "Cross Bracing",
    "ur_end_diaphragms": "End Diaphragms",
}


def _number(value):
    """Return a finite numeric value, or None if unavailable."""
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _make_chart(title, labels, values):
    """Create one UR bar chart and return its PNG bytes."""
    fig, ax = plt.subplots(figsize=(10, 4.8))

    if not values:
        ax.text(
            0.5, 0.5,
            "UR data not available",
            ha="center", va="center",
            transform=ax.transAxes,
            fontsize=12,
        )
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        bar_colors = [
            "#2E8B57" if value <= UR_LIMIT else "#D9534F"
            for value in values
        ]

        positions = range(len(values))
        ax.bar(positions, values, color=bar_colors, width=0.65)

        ax.set_xticks(list(positions))
        ax.set_xticklabels(labels, rotation=30, ha="right")

        for position, value in enumerate(values):
            ax.text(
                position,
                value,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        ax.axhline(
            y=UR_LIMIT,
            color="red",
            linestyle="--",
            linewidth=1.5,
            label="UR = 1.0 (limit)",
        )
        ax.legend(loc="upper right")
        ax.set_ylabel("Utilization Ratio (UR)")
        ax.set_ylim(bottom=0)

    ax.set_title(title)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    return buffer.getvalue()


def _girder_data(output_dict):
    design = output_dict.get("design_results", {}) or {}
    per_girder = design.get("per_girder", {}) or {}

    labels, values = [], []

    for name, result in per_girder.items():
        if str(name).upper().startswith("EB"):
            continue

        if not isinstance(result, dict):
            continue

        ur = _number(result.get("max_dcr"))
        if ur is not None:
            labels.append(str(name))
            values.append(ur)

    return labels, values


def _deck_data(output_dict):
    deck = output_dict.get("deck_design_results", {}) or {}

    if not isinstance(deck, dict):
        return [], []

    labels, values = [], []

    for key, raw_value in deck.items():
        if not str(key).startswith("ur_"):
            continue

        ur = _number(raw_value)
        if ur is not None:
            label = str(key)[3:].replace("_", " ").title()
            labels.append(label)
            values.append(ur)

    return labels, values


def _member_data(results):
    """Extract one governing UR per physical member."""
    labels, values = [], []

    if not isinstance(results, dict):
        return labels, values

    for pair, members in results.items():
        if not isinstance(members, dict):
            continue

        for member, force_results in members.items():
            if not isinstance(force_results, dict):
                continue

            member_urs = []

            for force_type, raw_result in force_results.items():
                if not isinstance(raw_result, dict):
                    continue

                summary = _extract_osdag_summary(raw_result) or {}
                ur = _number(summary.get("efficiency"))

                if ur is not None:
                    member_urs.append(ur)

            if member_urs:
                labels.append(f"{pair}\n{member}")
                values.append(max(member_urs))

    return labels, values


def build_ur_charts(output_dict):
    """
    Build all four Chapter 5 UR charts.

    Returns:
        Dictionary mapping chart names to PNG image bytes.
    """
    output_dict = output_dict or {}

    chart_data = {
        "ur_steel_girders": _girder_data(output_dict),
        "ur_deck_slab": _deck_data(output_dict),
        "ur_cross_bracing": _member_data(
            output_dict.get("crossbracing_design_results", {})
        ),
        "ur_end_diaphragms": _member_data(
            output_dict.get("end_diaphragm_design_results", {})
        ),
    }

    return {
        key: _make_chart(CHARTS[key], labels, values)
        for key, (labels, values) in chart_data.items()
    }
