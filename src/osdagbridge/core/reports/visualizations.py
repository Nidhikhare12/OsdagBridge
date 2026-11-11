"""Report charts from verified numeric records; no GUI backend changes."""
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from .report_data import numeric, quantity_records
from .styles import CHART_PASS_COLOR, CHART_FAIL_COLOR, CHART_THRESHOLD_COLOR, CHART_STEEL_COLORS


def _figure(figsize):
    fig = Figure(figsize=figsize, dpi=300, constrained_layout=True)
    FigureCanvasAgg(fig)
    return fig


def _bars(ax, labels, values, unit, *, utilization=False):
    valid = []
    for index, value in enumerate(values):
        value = numeric(value)
        if value is None or value < 0:
            ax.text(index, 0.04, "Not available", transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=8, rotation=0)
            continue
        valid.append(value)
        color = (CHART_PASS_COLOR if value <= 1 else CHART_FAIL_COLOR) if utilization else CHART_STEEL_COLORS[index % len(CHART_STEEL_COLORS)]
        ax.bar(index, value, width=0.5, color=color,
               hatch="//" if utilization and value > 1 else None)
        label = f"{value:.3f}" if utilization else f"{value:.2f} {unit}"
        if utilization:
            label += "\n" + ("PASS" if value <= 1 else "FAIL")
        ax.annotate(label, (index, value), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=9)
    ax.set_xticks(range(len(labels)), labels, fontsize=8)
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(0, max([1.0 if utilization else 0.1] + valid) * 1.30)
    ax.set_ylabel(unit)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    if utilization:
        ax.axhline(1, color=CHART_THRESHOLD_COLOR, linestyle="--", label="UR = 1.0")
        ax.legend(loc="upper left", fontsize=8)


def generate_ur_bar_chart(ur_data, output_path="ur_summary.png", figsize=(8.5, 4.6)):
    fig = _figure(figsize)
    ax = fig.subplots()
    _bars(ax, list(ur_data), list(ur_data.values()), "Utilization Ratio - Demand / Capacity", utilization=True)
    ax.set_title("Governing utilization by component")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=300)
    return fig


create_ur_chart = generate_ur_bar_chart


def generate_ur_summary_chart(pg_ur=None, deck_ur=None, cb_ur=None, ed_ur=None,
                              output_path="ur_summary.png", figsize=(8.5, 4.6)):
    generate_ur_bar_chart(dict(zip(
        ["Steel Plate Girders", "Concrete Deck Slab", "Cross Bracing", "End Diaphragms"],
        [pg_ur, deck_ur, cb_ur, ed_ur])), output_path, figsize)
    return output_path


def generate_material_quantity_charts(input_dict, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    records = quantity_records(input_dict)
    steel_path = os.path.join(output_dir, "material_steel_tonnage.png")
    deck_path = os.path.join(output_dir, "material_concrete_rebar.png")
    fig = _figure((7.5, 3.8))
    ax = fig.subplots()
    _bars(ax, [r.component for r in records[:3]], [r.value for r in records[:3]], "MT")
    ax.set_title("Structural steel quantities")
    fig.savefig(steel_path, dpi=300)
    fig = _figure((7.5, 3.8))
    axes = fig.subplots(1, 2)
    for ax, record in zip(axes, records[3:]):
        _bars(ax, [record.component], [record.value], record.unit)
        ax.set_title(record.component)
    fig.suptitle("Deck materials (reinforcement estimate: 120 kg/m³ of concrete)", fontsize=10)
    fig.savefig(deck_path, dpi=300)
    return steel_path, deck_path
