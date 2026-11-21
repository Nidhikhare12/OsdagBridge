import io
import math
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _number(value):
    """Extract a numeric quantity; return None for N.A./invalid values."""
    if value is None:
        return None

    match = re.search(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        str(value).replace(",", "")
    )
    if not match:
        return None

    try:
        result = float(match.group(0))
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _png_bytes(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def build_quantity_charts(input_dict):
    """Build charts only from quantities already calculated by BOQ."""
    charts = {}

    # Chart 1: Structural and reinforcement steel tonnage (MT)
    steel_items = [
        ("Girders", "steel_girders_wt_total"),
        ("Top bracing", "bracing_top_wt_total"),
        ("Bottom bracing", "bracing_bot_wt_total"),
        ("Diagonal bracing", "bracing_diag_wt_total"),
        ("Reinforcement", "rebar_deck_wt_total"),
    ]

    labels = []
    values = []

    for label, key in steel_items:
        value = _number(input_dict.get(key))
        if value is not None:
            labels.append(label)
            values.append(value)

    if values:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        bars = ax.bar(labels, values)
        ax.set_title("Steel Quantity Distribution")
        ax.set_ylabel("Weight (MT)")
        ax.set_xlabel("Structural component")
        ax.tick_params(axis="x", labelrotation=15)
        ax.grid(axis="y", linestyle=":", alpha=0.5)

        for bar, value in zip(bars, values):
            ax.annotate(
                f"{value:.3f}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )

        fig.tight_layout()
        charts["quantity_steel_tonnage"] = _png_bytes(fig)

    # Chart 2: Concrete volume (m3) vs reinforcement weight (MT)
    concrete = _number(input_dict.get("concrete_deck_vol_total"))
    rebar = _number(input_dict.get("rebar_deck_wt_total"))

    if concrete is not None or rebar is not None:
        fig, ax1 = plt.subplots(figsize=(7, 4.2))

        if concrete is not None:
            ax1.bar(
                ["Concrete deck"],
                [concrete],
                width=0.4,
                label="Concrete volume",
            )
            ax1.set_ylabel("Concrete volume (m³)")
            ax1.annotate(
                f"{concrete:.3f} m³",
                (0, concrete),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
            )

        if rebar is not None:
            ax2 = ax1.twinx()
            ax2.plot(
                ["Concrete deck"],
                [rebar],
                marker="o",
                linewidth=2,
                label="Reinforcement weight",
            )
            ax2.set_ylabel("Reinforcement weight (MT)")
            ax2.annotate(
                f"{rebar:.3f} MT",
                (0, rebar),
                xytext=(8, 8),
                textcoords="offset points",
            )

        ax1.set_title("Concrete Volume and Reinforcement Weight")
        ax1.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        charts["quantity_concrete_reinforcement"] = _png_bytes(fig)

    return charts
