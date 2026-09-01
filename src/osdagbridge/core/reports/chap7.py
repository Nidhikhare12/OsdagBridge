from osdagbridge.core.boq.boq_generator import _fmt_math, _fmt_small
from osdagbridge.core.reports.report_utils import _fig_embed, render_report_table
from osdagbridge.core.utils.common import (
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_SPAN,
    KEY_TD_CB_BOTTOM_CHORD_PROP_A,
    KEY_TD_CB_PROP_A,
    KEY_TD_CB_TOP_CHORD_PROP_A,
    KEY_TS_NO_OF_GIRDERS,
)


_STEEL_DENSITY_T_PER_M3 = 7.85


def _is_blank(value):
    return value in ("", None, "N.A.", "NA", "None", "---")


def _num(value):
    if _is_blank(value):
        return None
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _truth(value):
    if isinstance(value, bool):
        return value
    if _is_blank(value):
        return None
    text = str(value).strip().lower()
    if text in {"yes", "true", "1"}:
        return True
    if text in {"no", "false", "0"}:
        return False
    return None


def _girder_value(input_dict, base_key, girder_index):
    for key in (f"{base_key}.G{girder_index}.M1", base_key, f"{base_key}.G1.M1"):
        value = input_dict.get(key)
        if not _is_blank(value):
            return value
    return None


def _fmt_qty(prefix, single_vol, qty, total_vol):
    wt_single = single_vol * _STEEL_DENSITY_T_PER_M3
    wt_total = total_vol * _STEEL_DENSITY_T_PER_M3
    return {
        f"{prefix}_vol_formula": f"${_fmt_math(single_vol, 6)}\\text{{ m}}^3 \\times {qty} = {_fmt_math(total_vol, 5)}\\text{{ m}}^3$",
        f"{prefix}_qty": str(qty),
        f"{prefix}_vol_total": _fmt_small(total_vol),
        f"{prefix}_wt_single": _fmt_small(wt_single, 4),
        f"{prefix}_wt_total": _fmt_small(wt_total),
    }


def _fmt_bracing(prefix, area, length, qty, total_vol):
    wt_single = area * length * _STEEL_DENSITY_T_PER_M3
    wt_total = total_vol * _STEEL_DENSITY_T_PER_M3
    return {
        f"{prefix}_vol_formula": f"${_fmt_math(area, 5)}\\text{{ m}}^2 \\times {_fmt_math(length, 2)}\\text{{ m}} = {_fmt_math(area * length, 5)}\\text{{ m}}^3$",
        f"{prefix}_qty": str(qty),
        f"{prefix}_vol_total": _fmt_small(total_vol),
        f"{prefix}_wt_single": _fmt_small(wt_single, 4),
        f"{prefix}_wt_total": _fmt_small(wt_total),
    }


def _derive_cross_bracing_quantities(output_dict):
    cb_forces = (output_dict or {}).get("crossbracing_forces_dict", {}) or {}
    geometry = cb_forces.get("geometry", {}) or {}
    pairs = list((cb_forces.get("pairs", {}) or {}).keys())
    if not pairs:
        return {}

    def _member(prefix, area_key, length_key, enabled_map=None, qty_factor=1):
        total_qty = 0
        total_vol = 0.0
        first_area = first_length = None
        for pair in pairs:
            enabled = True if enabled_map is None else _truth((enabled_map or {}).get(pair))
            if enabled is None:
                return {}
            if not enabled:
                continue
            pair_id = pair.replace("-", "")
            area_cm2 = _num(output_dict.get(f"{area_key}.{pair_id}"))
            geom = geometry.get(pair, {}) or {}
            length = _num(geom.get(length_key))
            panels = _num(geom.get("no_of_cross_bracings"))
            if area_cm2 is None or length is None or panels is None:
                return {}
            area = area_cm2 / 10000.0
            qty = int(panels) * qty_factor
            total_qty += qty
            total_vol += area * length * qty
            first_area = area if first_area is None else first_area
            first_length = length if first_length is None else first_length
        return _fmt_bracing(prefix, first_area, first_length, total_qty, total_vol) if total_qty else {}

    values = {}
    values.update(_member("bracing_top", KEY_TD_CB_TOP_CHORD_PROP_A, "girder_spacing_m", cb_forces.get("top_chord")))
    values.update(_member("bracing_bot", KEY_TD_CB_BOTTOM_CHORD_PROP_A, "girder_spacing_m", cb_forces.get("bottom_chord")))
    values.update(_member("bracing_diag", KEY_TD_CB_PROP_A, "diagonal_length_m", qty_factor=2))
    return values


def _derive_stiffener_quantities(input_dict):
    span = _num(input_dict.get(KEY_SPAN))
    n_girders = _num(input_dict.get(KEY_TS_NO_OF_GIRDERS))
    if span is None or n_girders is None:
        return {}

    total_qty = 0
    total_vol = 0.0
    for gi in range(1, int(n_girders) + 1):
        depth = _num(_girder_value(input_dict, KEY_MP_GIRDER_DEPTH, gi))
        bearing_count = _num(_girder_value(input_dict, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, gi))
        bearing_t = _num(_girder_value(input_dict, KEY_MP_STIFFENER_BEARING_THICKNESS, gi))
        bearing_w = _num(_girder_value(input_dict, KEY_MP_STIFFENER_BEARING_OUTSTAND, gi))
        if depth is not None and bearing_count is not None and bearing_t is not None and bearing_w is not None:
            qty = int(bearing_count) * 2
            total_qty += qty
            total_vol += qty * depth * bearing_t * bearing_w / 1e9

        if _truth(_girder_value(input_dict, KEY_MP_STIFFENER_INTERMEDIATE, gi)):
            spacing = _num(_girder_value(input_dict, KEY_MP_STIFFENER_INTERMEDIATE_SPACING, gi))
            int_t = _num(_girder_value(input_dict, KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, gi))
            int_w = _num(_girder_value(input_dict, KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, gi))
            if depth is None or spacing is None or int_t is None or int_w is None:
                return {}
            qty = max(0, int((span * 1000.0) / spacing) - 1) * 2
            total_qty += qty
            total_vol += qty * depth * int_t * int_w / 1e9
    return _fmt_qty("stiffeners", total_vol / total_qty, total_qty, total_vol) if total_qty and total_vol else {}


def ch7_derived_quantities(input_dict, output_dict):
    values = {}
    values.update(_derive_cross_bracing_quantities(output_dict or {}))
    values.update(_derive_stiffener_quantities(input_dict or {}))
    return values


def _wrap_multiply(value):
    text = str(value)
    times = r"\allowbreak{}\times\allowbreak{}" if "$" in text else r"\allowbreak{}$\times$\allowbreak{}"
    return text.replace(r"\times", r"\allowbreak{}\times\allowbreak{}").replace("×", times).replace(" x ", f" {times} ")


def _qty_header(text):
    return r"\parbox[t][1.75cm][c]{\linewidth}{\centering " + text + "}"


def ch7_quantities(input_dict, output_dict=None, chart_paths=None):
    if chart_paths is None and isinstance(output_dict, dict) and (
            "steel" in output_dict or "concrete_rebar" in output_dict):
        chart_paths, output_dict = output_dict, None
    input_dict = {**input_dict, **ch7_derived_quantities(input_dict, output_dict or {})}
    chart_paths = chart_paths or {}
    chart_figures = ""
    if chart_paths:
        chart_figures = (
            "\n\\vspace{1em}\n"
            + _fig_embed(chart_paths.get("steel"),
                         "Structural Steel Tonnage Summary",
                         width=r"0.82\textwidth", numbered=True)
            + "\n\\vspace{0.5em}\n"
            + _fig_embed(chart_paths.get("concrete_rebar"),
                         "Concrete Volume and Reinforcement Steel Summary",
                         width=r"0.82\textwidth", numbered=True)
        )
    rows = [
        ["1", "Structural Steel (IS 2062) for Girders", _wrap_multiply(input_dict.get("steel_girders_vol_formula", "N.A.")), input_dict.get("steel_girders_qty", "N.A."), input_dict.get("steel_girders_vol_total", "N.A."), input_dict.get("steel_girders_wt_single", "N.A."), input_dict.get("steel_girders_wt_total", "N.A.")],
        ["2(a)", "Cross Bracing - Top Chord", _wrap_multiply(input_dict.get("bracing_top_vol_formula", "N.A.")), input_dict.get("bracing_top_qty", "N.A."), input_dict.get("bracing_top_vol_total", "N.A."), input_dict.get("bracing_top_wt_single", "N.A."), input_dict.get("bracing_top_wt_total", "N.A.")],
        ["2(b)", "Cross Bracing - Bottom Chord", _wrap_multiply(input_dict.get("bracing_bot_vol_formula", "N.A.")), input_dict.get("bracing_bot_qty", "N.A."), input_dict.get("bracing_bot_vol_total", "N.A."), input_dict.get("bracing_bot_wt_single", "N.A."), input_dict.get("bracing_bot_wt_total", "N.A.")],
        ["2(c)", "Cross Bracing - Diagonal Chord", _wrap_multiply(input_dict.get("bracing_diag_vol_formula", "N.A.")), input_dict.get("bracing_diag_qty", "N.A."), input_dict.get("bracing_diag_vol_total", "N.A."), input_dict.get("bracing_diag_wt_single", "N.A."), input_dict.get("bracing_diag_wt_total", "N.A.")],
        ["3", "Stiffeners", _wrap_multiply(input_dict.get("stiffeners_vol_formula", "N.A.")), input_dict.get("stiffeners_qty", "N.A."), input_dict.get("stiffeners_vol_total", "N.A."), input_dict.get("stiffeners_wt_single", "N.A."), input_dict.get("stiffeners_wt_total", "N.A.")],
        ["4", "Connections", _wrap_multiply(input_dict.get("connections_vol_formula", "N.A.")), input_dict.get("connections_qty", "N.A."), input_dict.get("connections_vol_total", "N.A."), input_dict.get("connections_wt_single", "N.A."), input_dict.get("connections_wt_total", "N.A.")],
        ["5", "Concrete (M40) for Deck Slab", _wrap_multiply(input_dict.get("concrete_deck_vol_formula", "N.A.")), input_dict.get("concrete_deck_qty", "N.A."), input_dict.get("concrete_deck_vol_total", "N.A."), input_dict.get("concrete_deck_wt_single", "N.A."), input_dict.get("concrete_deck_wt_total", "N.A.")],
        ["6", "Reinforcement Steel (Fe 500)", _wrap_multiply(input_dict.get("rebar_deck_vol_formula", "N.A.")), input_dict.get("rebar_deck_qty", "N.A."), input_dict.get("rebar_deck_vol_total", "N.A."), input_dict.get("rebar_deck_wt_single", "N.A."), input_dict.get("rebar_deck_wt_total", "N.A.")],
        ["7", "Shear Stud Connectors", _wrap_multiply(input_dict.get("shear_studs_vol_formula", "N.A.")), input_dict.get("shear_studs_qty", "N.A."), input_dict.get("shear_studs_vol_total", "N.A."), input_dict.get("shear_studs_wt_single", "N.A."), input_dict.get("shear_studs_wt_total", "N.A.")],
        ["8", "Crash Barrier", _wrap_multiply(input_dict.get("crash_barrier_vol_formula", "N.A.")), input_dict.get("crash_barrier_qty", "N.A."), input_dict.get("crash_barrier_vol_total", "N.A."), input_dict.get("crash_barrier_wt_single", "N.A."), input_dict.get("crash_barrier_wt_total", "N.A.")],
    ]
    return r"""
\chapter{Bill of Materials}
\label{ch:material-takeoff}
""" + render_report_table(
        "Bill of Materials for Superstructure", rows,
        header_rows=[[_qty_header("S.N."), _qty_header(r"Item\\Description"),
                      _qty_header("Volume"), _qty_header("Quantity"),
                      _qty_header(r"Total\\Volume\\(m$^3$)"),
                      _qty_header(r"Weight\\(t)"), _qty_header(r"Total\\Weight\\(t)")]],
        widths=[1.0, 3.8, 2.5, 2.1, 1.8, 1.7, 1.8],
        align=["C", "L", "C", "C", "C", "C", "C"],
        longtable=True, escape=False) + chart_figures


