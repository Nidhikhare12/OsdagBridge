"""Report charts: utilization ratios (Section 5.5) and quantities (Ch. 7).

The charts are built from the *same values the report tables print*: the
rows of Table 5.22 and the Bill of Materials dictionary. Values arrive as
formatted text (``"1.05"``, ``"N.A."``, ``\\textcolor{red}{1.05}``), so this
module parses them defensively and draws "n/a" for anything missing instead
of inventing a number.

Figures are created with ``matplotlib.figure.Figure`` and never ``pyplot``:
there is no global backend or figure registry, so rendering is safe inside
the Qt desktop application. Styling comes from ``styles.CHARTS``. Rendering
failures are logged and never abort report generation.
"""

from __future__ import annotations

import logging
import math
import os
import re
import textwrap
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from matplotlib import rc_context
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_utils import _fig_embed

logger = logging.getLogger(__name__)

ELEMENT_ORDER = (
    "Steel Plate Girders",
    "Concrete Deck Slab",
    "Cross Bracing",
    "End Diaphragms",
)
"""Primary elements of the Section 5.5 chart, in display order."""

UR_FILE = "ur_summary.png"
STEEL_FILE = "steel_tonnage.png"
CONCRETE_REBAR_FILE = "concrete_rebar.png"

_FIRST_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def parse_number(value: object) -> float | None:
    """Parse a quantity that may be a number, a string or ``"N.A."``.

    Args:
        value: Raw value from the report data.

    Returns:
        A finite float, or ``None`` when the value is missing or invalid.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        try:
            number = float(str(value).strip().replace(",", ""))
        except ValueError:
            return None
    return number if math.isfinite(number) else None


def parse_ur(text: object) -> float | None:
    """Extract a utilization ratio from a table cell.

    Table 5.22 prints URs as ``0.85`` or ``\\textcolor{red}{1.05}``; missing
    values are ``---``.

    Args:
        text: Cell text.

    Returns:
        The ratio, or ``None`` when the cell holds no number.
    """
    if text is None:
        return None
    match = _FIRST_NUMBER.search(str(text))
    return None if match is None else float(match.group())


def element_for_label(label: str) -> str | None:
    """Map a Table 5.22 row label to one of the four primary elements.

    Args:
        label: Row label such as ``Girder --- Moment``.

    Returns:
        The element name, or ``None`` for an unrecognised label.
    """
    text = label.strip().lower()
    if text.startswith("girder"):
        return "Steel Plate Girders"
    if text.startswith("deck") or "(slab)" in text:
        return "Concrete Deck Slab"
    if text.startswith("cross bracing"):
        return "Cross Bracing"
    if text.startswith("end diaphragm"):
        return "End Diaphragms"
    return None


def element_urs(
    rows: Iterable[tuple[str, str | None]],
) -> dict[str, float | None]:
    """Reduce check rows to the governing (highest) UR per element.

    Args:
        rows: ``(row label, UR cell text)`` pairs from Table 5.22.

    Returns:
        One entry per element in ``ELEMENT_ORDER``; ``None`` when the
        element has no numeric UR.
    """
    result: dict[str, float | None] = dict.fromkeys(ELEMENT_ORDER)
    for label, cell in rows:
        element = element_for_label(label)
        ratio = parse_ur(cell)
        if element is None or ratio is None:
            continue
        current = result[element]
        result[element] = ratio if current is None else max(current, ratio)
    return result


@dataclass(frozen=True)
class MaterialQuantities:
    """Chapter 7 totals; ``None`` means "not available"."""

    girders_t: float | None
    bracing_t: float | None
    end_diaphragm_t: float | None
    concrete_m3: float | None
    rebar_mt: float | None


def _non_negative(value: object) -> float | None:
    number = parse_number(value)
    return number if number is not None and number >= 0.0 else None


def material_quantities(bom: Mapping[str, object]) -> MaterialQuantities:
    """Read the quantities charted in Chapter 7 from the BOM dictionary.

    Cross bracing uses ``steel_bracing_wt_total`` when present, otherwise
    the sum of the top, bottom and diagonal chords (all three required).
    The BOM has no end-diaphragm quantity, so that value is always ``None``.

    Args:
        bom: Report input dictionary holding the ``*_total`` strings.

    Returns:
        A ``MaterialQuantities``.
    """
    bracing = _non_negative(bom.get("steel_bracing_wt_total"))
    if bracing is None:
        parts = [_non_negative(bom.get(f"bracing_{kind}_wt_total"))
                 for kind in ("top", "bot", "diag")]
        if all(part is not None for part in parts):
            bracing = float(sum(p for p in parts if p is not None))
    return MaterialQuantities(
        girders_t=_non_negative(bom.get("steel_girders_wt_total")),
        bracing_t=bracing,
        end_diaphragm_t=None,
        concrete_m3=_non_negative(bom.get("concrete_deck_vol_total")),
        rebar_mt=_non_negative(bom.get("rebar_deck_wt_total")),
    )


def _rc() -> dict[Any, Any]:
    style = styles.CHARTS
    return {
        "font.family": "serif",
        "font.serif": list(style.font_family),
        "mathtext.fontset": "cm",
        "font.size": style.font_size,
        "axes.titlesize": style.title_size,
        "axes.edgecolor": style.edge_color,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
    }


def _new_figure() -> Figure:
    style = styles.CHARTS
    return Figure(figsize=(style.width_in, style.height_in),
                  layout="constrained")


def _wrap(label: str) -> str:
    return textwrap.fill(label, width=14)


def _value_axis(ax: Axes, upper: float) -> None:
    style = styles.CHARTS
    ax.set_ylim(0.0, upper)
    ax.yaxis.grid(True, color=style.grid_color, linewidth=0.5, alpha=0.6)


def _mark_unavailable(ax: Axes, x: float, upper: float) -> None:
    ax.text(x, upper * 0.03, "n/a", ha="center", va="bottom",
            style="italic", color="#555555")


def _save(fig: Figure, directory: str | os.PathLike[str],
          name: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    fig.savefig(path, dpi=styles.CHARTS.dpi, format="png")
    return os.fspath(path).replace("\\", "/")


def render_ur_chart(
    urs: Mapping[str, float | None],
    directory: str | os.PathLike[str],
) -> str | None:
    """Draw the utilization-ratio bar chart with the UR = 1.0 limit line.

    Passing bars are solid; failing bars are hatched, so the meaning
    survives grayscale printing. A bar whose label rounds to 1.00 but whose
    UR exceeds 1.0 is marked ``*``.

    Args:
        urs: Governing UR per element (``None`` = not available).
        directory: Folder to write the PNG into.

    Returns:
        The image path, or ``None`` when no element has a UR.
    """
    if not any(value is not None for value in urs.values()):
        return None
    style = styles.CHARTS
    names = [name for name in ELEMENT_ORDER if name in urs]
    values = [urs[name] for name in names]
    peak = max((v for v in values if v is not None), default=0.0)
    upper = max(style.ur_limit, peak) * (1.0 + style.value_headroom)

    with rc_context(_rc()):
        fig = _new_figure()
        ax = fig.add_subplot()
        conflict = False
        for index, value in enumerate(values):
            if value is None:
                _mark_unavailable(ax, index, upper)
                continue
            failing = value > style.ur_limit
            bar = ax.bar(
                index, value, width=style.bar_width,
                color=style.fail_color if failing else style.pass_color,
                edgecolor=style.edge_color, linewidth=0.8,
                hatch=style.fail_hatch if failing else None)
            label = f"{value:.2f}"
            if failing and float(label) <= style.ur_limit:
                label += "*"
                conflict = True
            ax.bar_label(bar, labels=[label], padding=3)
        ax.axhline(style.ur_limit, color=style.limit_color,
                   linestyle="--", linewidth=1.5, zorder=3)
        ax.set_xticks(range(len(names)), [_wrap(n) for n in names])
        ax.set_xlabel("Structural element")
        ax.set_ylabel("Utilization ratio, UR (-)\nUR = Demand / Capacity")
        ax.set_title("Overall Design Check: Governing Utilization Ratio")
        _value_axis(ax, upper)

        handles: list[Patch | Line2D] = [
            Patch(facecolor=style.pass_color, edgecolor=style.edge_color,
                  label=r"Pass (UR $\leq$ 1.0)"),
            Patch(facecolor=style.fail_color, edgecolor=style.edge_color,
                  hatch=style.fail_hatch, label=r"Fail (UR $>$ 1.0)"),
            Line2D([0], [0], color=style.limit_color, linestyle="--",
                   linewidth=1.5, label="Limit, UR = 1.0"),
        ]
        if conflict:
            handles.append(Line2D([], [], linestyle="", label=(
                "* UR slightly above 1.0; shown rounded, check fails")))
        if any(v is None for v in values):
            handles.append(Line2D([], [], linestyle="", label=(
                "n/a: no value available in the report data")))
        fig.legend(handles=handles, loc="outside lower center",
                   ncol=3 if len(handles) == 3 else 2, frameon=False)
        return _save(fig, directory, UR_FILE)


def render_steel_chart(
    quantities: MaterialQuantities,
    directory: str | os.PathLike[str],
) -> str | None:
    """Draw structural steel tonnage per member group.

    Args:
        quantities: Parsed Chapter 7 quantities.
        directory: Folder to write the PNG into.

    Returns:
        The image path, or ``None`` when no steel quantity is available.
    """
    style = styles.CHARTS
    names = ["Girders", "Cross Bracing", "End Diaphragms"]
    values = [quantities.girders_t, quantities.bracing_t,
              quantities.end_diaphragm_t]
    if all(v is None for v in values):
        return None
    peak = max((v for v in values if v is not None), default=0.0)
    upper = peak * (1.0 + style.value_headroom) if peak > 0.0 else 1.0
    total = sum(v for v in values if v is not None)

    with rc_context(_rc()):
        fig = _new_figure()
        ax = fig.add_subplot()
        for index, value in enumerate(values):
            if value is None:
                _mark_unavailable(ax, index, upper)
                continue
            bar = ax.bar(index, value, width=style.bar_width,
                         color=style.steel_color,
                         edgecolor=style.edge_color, linewidth=0.8)
            ax.bar_label(bar, labels=[f"{value:.2f} t"], padding=3)
        ax.set_xticks(range(len(names)), [_wrap(n) for n in names])
        ax.set_xlabel("Structural member group")
        ax.set_ylabel("Structural steel mass (t)")
        ax.set_title("Material Take-off: Structural Steel Tonnage")
        _value_axis(ax, upper)
        handles: list[Patch | Line2D] = [Patch(
            facecolor=style.steel_color, edgecolor=style.edge_color,
            label=f"Structural steel (total listed = {total:.2f} t)")]
        if any(v is None for v in values):
            handles.append(Line2D([], [], linestyle="", label=(
                "n/a: not available in the bill of materials")))
        fig.legend(handles=handles, loc="outside lower center", ncol=1,
                   frameon=False)
        return _save(fig, directory, STEEL_FILE)


def render_concrete_rebar_chart(
    quantities: MaterialQuantities,
    directory: str | os.PathLike[str],
) -> str | None:
    """Draw concrete volume (m^3) beside reinforcement weight (MT).

    Two panels with separate axes, because the units and scales differ.

    Args:
        quantities: Parsed Chapter 7 quantities.
        directory: Folder to write the PNG into.

    Returns:
        The image path, or ``None`` when neither quantity is available.
    """
    style = styles.CHARTS
    panels = (
        ("Concrete", quantities.concrete_m3, style.concrete_color,
         r"Concrete volume (m$^{3}$)", r"m$^{3}$"),
        ("Reinforcement", quantities.rebar_mt, style.rebar_color,
         "Reinforcement weight (MT)", "MT"),
    )
    if all(panel[1] is None for panel in panels):
        return None

    with rc_context(_rc()):
        fig = _new_figure()
        axes = fig.subplots(1, len(panels))
        handles: list[Patch | Line2D] = []
        for ax, (tick, value, color, ylabel, unit) in zip(
                axes, panels, strict=True):
            upper = (value * (1.0 + style.value_headroom)
                     if value else 1.0)
            if value is None:
                _mark_unavailable(ax, 0, upper)
            else:
                bar = ax.bar(0, value, width=0.5, color=color,
                             edgecolor=style.edge_color, linewidth=0.8)
                ax.bar_label(bar, labels=[f"{value:.2f} {unit}"],
                             padding=3)
                handles.append(Patch(facecolor=color,
                                     edgecolor=style.edge_color,
                                     label=ylabel))
            ax.set_xticks([0], [tick])
            ax.set_xlim(-0.8, 0.8)
            ax.set_ylabel(ylabel)
            _value_axis(ax, upper)
        fig.suptitle("Material Take-off:\nConcrete Volume vs "
                     "Reinforcement Steel Weight",
                     fontsize=style.title_size)
        if handles:
            fig.legend(handles=handles, loc="outside lower center",
                       ncol=2, frameon=False)
        return _save(fig, directory, CONCRETE_REBAR_FILE)


def _embed(path: str | None, caption: str) -> str:
    if path is None:
        return ""
    return "\n" + _fig_embed(path, caption, width=styles.CHARTS.latex_width)


def ur_summary_latex(
    rows: Iterable[tuple[str, str | None]],
    chart_dir: str | os.PathLike[str] | None,
) -> str:
    """Return the Section 5.5 figure, or ``""`` when no chart is possible.

    Args:
        rows: ``(row label, UR cell text)`` pairs of Table 5.22.
        chart_dir: Folder for the image, or ``None`` to skip charts.

    Returns:
        LaTeX for the figure, or an empty string.
    """
    if chart_dir is None:
        return ""
    try:
        path = render_ur_chart(element_urs(rows), chart_dir)
    except Exception:  # charts must never abort the report
        logger.exception("UR chart could not be drawn")
        return ""
    return _embed(path, (
        "Governing utilization ratio (UR = Demand / Capacity) of each "
        "primary element, taken from the table above. The dashed line "
        "marks UR = 1.0."))


def material_charts_latex(
    bom: Mapping[str, object],
    chart_dir: str | os.PathLike[str] | None,
) -> str:
    """Return the Chapter 7 figures, or ``""`` when no chart is possible.

    Args:
        bom: Report input dictionary holding the quantity strings.
        chart_dir: Folder for the images, or ``None`` to skip charts.

    Returns:
        LaTeX for up to two figures, or an empty string.
    """
    if chart_dir is None:
        return ""
    try:
        quantities = material_quantities(bom)
        steel = render_steel_chart(quantities, chart_dir)
        concrete = render_concrete_rebar_chart(quantities, chart_dir)
    except Exception:  # charts must never abort the report
        logger.exception("Material charts could not be drawn")
        return ""
    return (_embed(steel, "Structural steel quantities by member group, "
                          "from Table 7.1.")
            + _embed(concrete, "Concrete volume and reinforcement steel "
                               "weight of the deck slab, from Table 7.1."))
