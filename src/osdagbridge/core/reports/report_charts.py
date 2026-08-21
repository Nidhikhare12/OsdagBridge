"""Generate temporary charts embedded in the design report."""

from __future__ import annotations

import os
from collections.abc import Mapping

from PIL import Image, ImageDraw, ImageFont

from osdagbridge.core.reports.styles import (
    FAIL_RED,
    GRID_GREY,
    OSDAG_GREEN,
    PASS_GREEN,
    TEXT_GREY,
)
from osdagbridge.core.utils.common import (
    KEY_DD_HAS_OVERHANG,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_VED,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
)


def _number(value):
    try:
        result = float(value)
        return result if result >= 0 else abs(result)
    except (TypeError, ValueError):
        return None


def _ratio(demand, capacity):
    demand_f, capacity_f = _number(demand), _number(capacity)
    if demand_f is None or capacity_f in (None, 0.0):
        return None
    return demand_f / capacity_f


def _safe_name(label: str, limit: int = 24) -> str:
    label = str(label).replace("_", " ").replace("-", "-")
    return label if len(label) <= limit else label[: limit - 3] + "..."


def _girder_utilization(output_dict: dict) -> list[tuple[str, float]]:
    per_girder = (output_dict.get("design_results") or {}).get("per_girder") or {}
    data = []
    for girder, details in sorted(per_girder.items()):
        if str(girder).startswith("EB"):
            continue
        values = []
        max_dcr = _number((details or {}).get("max_dcr"))
        if max_dcr is not None:
            values.append(max_dcr)
        for check in (details or {}).get("checks") or []:
            dcr = _number((check or {}).get("dcr"))
            if dcr is not None:
                values.append(dcr)
        for lc_data in ((details or {}).get("per_lc") or {}).values():
            for check in (lc_data or {}).get("checks") or []:
                dcr = _number((check or {}).get("dcr"))
                if dcr is not None:
                    values.append(dcr)
        if values:
            data.append((str(girder), max(values)))
    return data


def _deck_utilization(output_dict: dict) -> list[tuple[str, float]]:
    deck = output_dict.get("deck_report_values") or {}
    candidates = [
        ("Sagging flexure", _ratio(deck.get(KEY_DD_M_ULS_SAG), deck.get(KEY_DD_MU_BOT))),
        ("Hogging flexure", _ratio(deck.get(KEY_DD_M_ULS_HOG), deck.get(KEY_DD_MU_TOP))),
        ("Punching shear", _ratio(deck.get(KEY_DD_PUNCH_VED), deck.get(KEY_DD_VRD_C_MPA))),
        ("One-way shear", _ratio(deck.get(KEY_DD_SHEAR_VED), deck.get(KEY_DD_SHEAR_VRDC))),
    ]
    if deck.get(KEY_DD_HAS_OVERHANG):
        candidates.append(("Overhang flexure", _ratio(deck.get(KEY_DD_M_ULS_OH), deck.get(KEY_DD_MU_OH))))
    crack_values = [_number(deck.get(KEY_DD_WK_BOT)), _number(deck.get(KEY_DD_WK_TOP))]
    if deck.get(KEY_DD_HAS_OVERHANG):
        crack_values.append(_number(deck.get(KEY_DD_WK_OH)))
    crack_values = [value for value in crack_values if value is not None]
    crack_limit = _number(deck.get(KEY_DD_WK_LIMIT))
    if crack_values and crack_limit:
        candidates.append(("Crack width", max(crack_values) / crack_limit))
    return [(label, value) for label, value in candidates if value is not None]


def _efficiency_records(value, path=()):
    """Yield labelled efficiency/DCR values from nested Osdag result data."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower()
            if (normalized in {"efficiency", "utilization", "utilization_ratio", "dcr", "max_dcr"}
                    or normalized.endswith(".efficiency") or normalized.endswith(".ur")):
                number = _number(child)
                if number is not None:
                    yield path, number
            else:
                yield from _efficiency_records(child, path + (key_text,))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value, start=1):
            yield from _efficiency_records(child, path + (str(index),))


def _member_utilization(output_dict: dict, result_key: str) -> list[tuple[str, float]]:
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    grouped = {}
    results = output_dict.get(result_key) or {}
    for pair, pair_results in results.items():
        if not isinstance(pair_results, Mapping):
            continue
        for member, member_results in pair_results.items():
            if not isinstance(member_results, Mapping):
                continue
            for force_type, raw_result in member_results.items():
                if not isinstance(raw_result, Mapping):
                    continue
                efficiency = _number(_extract_osdag_summary(raw_result).get("efficiency"))
                if efficiency is not None:
                    label = f"{pair} / {member}"
                    grouped[label] = max(efficiency, grouped.get(label, 0.0))
    if not grouped:
        for path, value in _efficiency_records(results):
            # Pair and member names are the most useful compact chart identity.
            useful = [part for part in path if part.lower() not in {"checks", "result", "results"}]
            label = " / ".join(useful[-3:]) or "Governing"
            grouped[label] = max(value, grouped.get(label, 0.0))
    return [(_safe_name(label), value) for label, value in sorted(grouped.items())]


def collect_utilization_data(output_dict: dict) -> dict[str, list[tuple[str, float]]]:
    """Collect UR values for each primary bridge component."""
    return {
        "Steel Plate Girders": _girder_utilization(output_dict),
        "Concrete Deck Slab": _deck_utilization(output_dict),
        "Cross Bracing": _member_utilization(output_dict, "crossbracing_design_results"),
        "End Diaphragms": _member_utilization(output_dict, "end_diaphragm_design_results"),
    }


def _font(size: int, bold: bool = False):
    names = ("arialbd.ttf", "Arial Bold.ttf") if bold else ("arial.ttf", "Arial.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _dashed_line(draw, xy, fill, width=3, dash=12, gap=8):
    x1, y, x2, _ = xy
    x = x1
    while x < x2:
        draw.line((x, y, min(x + dash, x2), y), fill=fill, width=width)
        x += dash + gap


def _draw_panel(draw, box, title: str, records: list[tuple[str, float]]):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, outline=GRID_GREY, width=2, fill="white")
    draw.text(((x0 + x1) / 2, y0 + 12), title, anchor="ma", font=_font(25, True), fill=TEXT_GREY)
    plot = (x0 + 72, y0 + 55, x1 - 24, y1 - 86)
    px0, py0, px1, py1 = plot
    values = [value for _, value in records]
    draw.text((px0, py0 - 5), "Utilization Ratio", anchor="lb",
              font=_font(16, True), fill=TEXT_GREY)
    ymax = max(1.25, (max(values) * 1.18 if values else 1.25))
    for tick in range(6):
        value = ymax * tick / 5
        y = py1 - (py1 - py0) * tick / 5
        draw.line((px0, y, px1, y), fill=GRID_GREY, width=1)
        draw.text((px0 - 10, y), f"{value:.1f}", anchor="rm", font=_font(17), fill=TEXT_GREY)
    limit_y = py1 - (py1 - py0) / ymax
    _dashed_line(draw, (px0, limit_y, px1, limit_y), FAIL_RED, width=3)
    draw.text((px1 - 4, limit_y - 5), "UR = 1.0", anchor="rb", font=_font(17, True), fill=FAIL_RED)
    draw.line((px0, py0, px0, py1), fill=TEXT_GREY, width=2)
    draw.line((px0, py1, px1, py1), fill=TEXT_GREY, width=2)
    if not records:
        draw.text(((px0 + px1) / 2, (py0 + py1) / 2), "No design results available",
                  anchor="mm", font=_font(20), fill=TEXT_GREY)
        return
    count = len(records)
    slot = (px1 - px0) / count
    bar_width = min(62, slot * 0.62)
    for index, (label, value) in enumerate(records):
        cx = px0 + slot * (index + 0.5)
        top = py1 - (py1 - py0) * value / ymax
        colour = PASS_GREEN if value <= 1.0 else FAIL_RED
        draw.rectangle((cx - bar_width / 2, top, cx + bar_width / 2, py1), fill=colour)
        draw.text((cx, top - 6), f"{value:.2f}", anchor="mb", font=_font(17, True), fill=TEXT_GREY)
        draw.text((cx, py1 + 10), _safe_name(label, 18), anchor="ma", font=_font(15), fill=TEXT_GREY)


def _draw_quantity_panel(draw, box, title: str, records: list[tuple[str, float]]):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, outline=GRID_GREY, width=2, fill="white")
    draw.text(((x0 + x1) / 2, y0 + 14), title, anchor="ma", font=_font(27, True), fill=TEXT_GREY)
    px0, py0, px1, py1 = x0 + 84, y0 + 70, x1 - 30, y1 - 88
    values = [value for _, value in records]
    ymax = max(max(values, default=0.0) * 1.2, 1.0)
    for tick in range(6):
        value = ymax * tick / 5
        y = py1 - (py1 - py0) * tick / 5
        draw.line((px0, y, px1, y), fill=GRID_GREY, width=1)
        draw.text((px0 - 10, y), f"{value:.1f}", anchor="rm", font=_font(18), fill=TEXT_GREY)
    draw.line((px0, py0, px0, py1), fill=TEXT_GREY, width=2)
    draw.line((px0, py1, px1, py1), fill=TEXT_GREY, width=2)
    count = max(len(records), 1)
    slot = (px1 - px0) / count
    colours = (OSDAG_GREEN, PASS_GREEN, "#547AA5")
    for index, (label, value) in enumerate(records):
        cx = px0 + slot * (index + 0.5)
        top = py1 - (py1 - py0) * value / ymax
        width = min(145, slot * 0.56)
        draw.rectangle((cx - width / 2, top, cx + width / 2, py1), fill=colours[index % len(colours)])
        draw.text((cx, top - 8), f"{value:.2f}", anchor="mb", font=_font(21, True), fill=TEXT_GREY)
        draw.text((cx, py1 + 12), _safe_name(label, 22), anchor="ma", font=_font(19), fill=TEXT_GREY)


def generate_utilization_chart(output_dict: dict, output_dir: str) -> str:
    """Create the four-panel overall utilization summary chart."""
    data = collect_utilization_data(output_dict)
    path = os.path.join(output_dir, "utilization_summary.png")
    image = Image.new("RGB", (1800, 1300), "white")
    draw = ImageDraw.Draw(image)
    draw.text((900, 25), "Overall Utilization Ratio Summary", anchor="ma",
              font=_font(36, True), fill=TEXT_GREY)
    boxes = ((80, 80, 890, 650), (910, 80, 1720, 650),
             (80, 680, 890, 1250), (910, 680, 1720, 1250))
    for box, (title, records) in zip(boxes, data.items()):
        _draw_panel(draw, box, title, records)
    image.save(path, format="PNG", optimize=True)
    return path.replace("\\", "/")


def _quantity(input_dict: dict, key: str) -> float:
    return _number(input_dict.get(key)) or 0.0


def generate_material_charts(input_dict: dict, output_dir: str) -> dict[str, str]:
    """Create structural-steel and deck-material quantity charts."""
    steel_path = os.path.join(output_dir, "steel_quantities.png")
    deck_path = os.path.join(output_dir, "deck_material_quantities.png")

    steel = {
        "Girders": _quantity(input_dict, "steel_girders_wt_total"),
        "Cross Bracing": sum(_quantity(input_dict, key) for key in (
            "bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total"
        )),
        "End Diaphragms": _quantity(input_dict, "end_diaphragm_wt_total"),
    }
    image = Image.new("RGB", (1500, 760), "white")
    draw = ImageDraw.Draw(image)
    _draw_quantity_panel(draw, (55, 45, 1445, 710), "Structural Steel Quantity (MT)", list(steel.items()))
    image.save(steel_path, format="PNG", optimize=True)

    concrete = _quantity(input_dict, "concrete_deck_vol_total")
    reinforcement = _quantity(input_dict, "rebar_deck_wt_total")
    image = Image.new("RGB", (1500, 760), "white")
    draw = ImageDraw.Draw(image)
    _draw_quantity_panel(draw, (55, 45, 725, 710), "Concrete Deck Volume (m3)", [("Concrete", concrete)])
    _draw_quantity_panel(draw, (775, 45, 1445, 710), "Reinforcement Steel Weight (MT)", [("Reinforcement", reinforcement)])
    image.save(deck_path, format="PNG", optimize=True)

    return {
        "steel_quantities": steel_path.replace("\\", "/"),
        "deck_material_quantities": deck_path.replace("\\", "/"),
    }
