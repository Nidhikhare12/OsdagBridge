"""Physically dimensioned material take-off for OsdagBridge plate-girder reports.

Only quantities supported by actual section properties, geometry, or design
outputs are reported.  Missing reinforcement schedules are deliberately shown
as unavailable instead of substituting a generic kg/m3 allowance.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING, KEY_TS_DECK_OVERHANG, KEY_MP_GIRDER_DEPTH,
    KEY_DS_STUD_HEAD_DIAMETER, KEY_DS_STUD_HEAD_HEIGHT,
)

logger = logging.getLogger("osdagbridge.core.boq_generator")
STEEL_DENSITY_KG_M3 = 7850.0
GRAVITY_M_S2 = 9.80665
DEFAULT_STEEL_UNIT_WEIGHT_KN_M3 = 76.4
DEFAULT_CONCRETE_UNIT_WEIGHT_KN_M3 = 24.5


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _density_kg_m3(inputs: dict, key: str, default_unit_weight_kn_m3: float) -> float:
    """Convert a supplied unit weight (kN/m³) to mass density (kg/m³)."""
    unit_weight = _number(inputs.get(key), default_unit_weight_kn_m3)
    if unit_weight <= 0:
        unit_weight = default_unit_weight_kn_m3
    return unit_weight * 1000.0 / GRAVITY_M_S2


def _first_number(source: dict, keys, default=0.0) -> float:
    for key in keys:
        if key in source and source[key] not in (None, ""):
            value = _number(source[key], default)
            if value > 0:
                return value
    return default


def resolve_girder_value(source: dict, base_key: str, i: int = 0) -> Any:
    """Resolve per-girder values, with a scalar legacy fallback."""
    for key in (f"{base_key}.G{i + 1}.M1", f"{base_key}.G{i + 1}", base_key,
                f"{base_key}.G1.M1"):
        if key in source and source[key] not in (None, ""):
            return source[key]
    raise KeyError(base_key)


def _section_area_m2(source: dict, prefix: str, pair="G1G2") -> float:
    """Section property A is stored in cm2 by the transverse-member designer."""
    raw = _first_number(source, (f"{prefix}.{pair}.A", f"{prefix}.A"))
    return raw / 10_000.0 if raw > 0 else 0.0


def _enabled(value: Any, default=False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"yes", "true", "1", "enabled", "on"}


def _set_item(q: dict, prefix: str, area_m2: float, length_m: float,
              count: int, description: str, steel_density_kg_m3: float = 7850.0) -> tuple[float, float]:
    if count == 0:
        q.update({f"{prefix}_vol_formula": "Not configured", f"{prefix}_qty": "0",
                  f"{prefix}_vol_total": "0.0000", f"{prefix}_wt_single": "0.00000",
                  f"{prefix}_wt_total": "0.00000"})
        return 0.0, 0.0
    if area_m2 <= 0 or length_m <= 0:
        q.update({f"{prefix}_vol_formula": "N.A.", f"{prefix}_qty": "N.A.",
                  f"{prefix}_vol_total": "N.A.", f"{prefix}_wt_single": "N.A.",
                  f"{prefix}_wt_total": "N.A."})
        return 0.0, 0.0
    single_volume = area_m2 * length_m
    total_volume = single_volume * count
    single_weight_mt = single_volume * steel_density_kg_m3 / 1000.0
    total_weight_mt = total_volume * steel_density_kg_m3 / 1000.0
    q.update({
        f"{prefix}_vol_formula": (f"${area_m2:.6f}\\,\\text{{m}}^2 \\times "
                                  f"{length_m:.3f}\\,\\text{{m}} = {single_volume:.6f}\\,\\text{{m}}^3$"),
        f"{prefix}_qty": str(count),
        f"{prefix}_vol_total": f"{total_volume:.4f}",
        f"{prefix}_wt_single": f"{single_weight_mt:.5f}",
        f"{prefix}_wt_total": f"{total_weight_mt:.5f}",
    })
    return total_volume, total_weight_mt


def _set_multi_item(q: dict, prefix: str, members: list[tuple[float, float, int]],
                    steel_density_kg_m3: float = 7850.0) -> tuple[float, float]:
    """Aggregate pair-specific section areas and member counts."""
    configured_count = sum(max(0, int(count)) for _, _, count in members)
    valid = [(area, length, count) for area, length, count in members
             if area > 0 and length > 0 and count > 0]
    if configured_count == 0:
        return _set_item(q, prefix, 0.0, 0.0, 0, prefix, steel_density_kg_m3)
    if len(valid) != len([m for m in members if m[2] > 0]):
        q.update({f"{prefix}_vol_formula": "N.A.", f"{prefix}_qty": str(configured_count),
                  f"{prefix}_vol_total": "N.A.", f"{prefix}_wt_single": "N.A.",
                  f"{prefix}_wt_total": "N.A."})
        return 0.0, 0.0
    total_volume = sum(area * length * count for area, length, count in valid)
    total_weight = total_volume * steel_density_kg_m3 / 1000.0
    avg_volume = total_volume / configured_count
    avg_weight = total_weight / configured_count
    q.update({f"{prefix}_vol_formula": "Pair-specific section areas x member lengths x member counts",
              f"{prefix}_qty": str(configured_count), f"{prefix}_vol_total": f"{total_volume:.4f}",
              f"{prefix}_wt_single": f"{avg_weight:.5f}", f"{prefix}_wt_total": f"{total_weight:.5f}"})
    return total_volume, total_weight


def calculate_material_quantities(inputs: dict, outputs: dict) -> dict:
    """Calculate report BOQ quantities using supplied design/geometry data.

    Steel weights use section mass where available and area x density otherwise.
    Reinforcement is estimated from the deck designer's bar diameters and
    spacings, with the assumptions and exclusions stated in the report.
    """
    inputs, outputs = inputs or {}, outputs or {}
    q = {}
    for prefix in ("steel_girders", "bracing_top", "bracing_bot", "bracing_diag",
                   "end_diaphragm", "shear_studs", "crash_barrier"):
        q.update({f"{prefix}_vol_formula": "N.A.", f"{prefix}_qty": "N.A.",
                  f"{prefix}_vol_total": "N.A.", f"{prefix}_wt_single": "N.A.",
                  f"{prefix}_wt_total": "N.A."})
    q.update({"concrete_deck_vol_formula": "N.A.", "concrete_deck_qty": "N.A.",
              "concrete_deck_vol_total": "N.A.", "concrete_deck_wt_single": "N.A.",
              "concrete_deck_wt_total": "N.A.", "rebar_deck_vol_formula": "N.A.",
              "rebar_deck_qty": "N.A.", "rebar_deck_vol_total": "N.A.",
              "rebar_deck_wt_single": "N.A.", "rebar_deck_wt_total": "N.A."})

    span = _number(inputs.get(KEY_SPAN))
    try:
        n_girders = int(float(inputs.get(KEY_TS_NO_OF_GIRDERS, 0)))
    except (TypeError, ValueError):
        n_girders = 0
    if span <= 0 or n_girders <= 0:
        return q

    # Deck concrete: dimensions in m, thickness input in mm.
    width = _number(inputs.get("typical_section.overall_bridge_width"))
    thickness_m = _number(inputs.get(KEY_TS_DECK_THICKNESS)) / 1000.0
    girder_spacing = _number(inputs.get(KEY_TS_GIRDER_SPACING))
    concrete_density_kg_m3 = _density_kg_m3(
        inputs, "material.deck.density", DEFAULT_CONCRETE_UNIT_WEIGHT_KN_M3
    )
    if width > 0 and thickness_m > 0:
        volume = span * width * thickness_m
        q.update({"concrete_deck_vol_formula":
                  f"${width:.3f}\\,\\text{{m}} \\times {thickness_m:.3f}\\,\\text{{m}} \\times {span:.3f}\\,\\text{{m}} = {volume:.4f}\\,\\text{{m}}^3$",
                  "concrete_deck_qty": "1", "concrete_deck_vol_total": f"{volume:.4f}",
                  "concrete_deck_wt_single": f"{volume * concrete_density_kg_m3 / 1000.0:.4f}",
                  "concrete_deck_wt_total": f"{volume * concrete_density_kg_m3 / 1000.0:.4f}"})

    # Reinforcement take-off from the deck designer's selected bar diameters
    # and spacings. This is a theoretical straight-bar estimate; anchorage,
    # hooks, laps, chairs and wastage are not included because the design output
    # does not carry a fabrication bar-bending schedule.
    rebar_mt = _first_number(outputs, ("rebar_deck_wt_total", "deck_design_results.rebar_weight_mt",
                                       "deck_design_results.reinforcement_weight_mt"))
    if rebar_mt <= 0:
        deck = outputs.get("deck_design_results") or {}
        def _bar_group(dia_key, spacing_key, total_length_m, multiplicity=1):
            dia = _number(deck.get(dia_key))
            spacing = _number(deck.get(spacing_key))
            if dia <= 0 or spacing <= 0 or not total_length_m or total_length_m[0] <= 0 or total_length_m[1] <= 0:
                return 0.0, 0
            count_per_run = int(math.ceil(total_length_m[0] * 1000.0 / spacing)) + 1
            count = count_per_run * max(1, int(multiplicity))
            length_sum = count * total_length_m[1]
            kg = (math.pi * (dia / 1000.0) ** 2 / 4.0) * length_sum * STEEL_DENSITY_KG_M3
            return kg, count
        rebar_kg = 0.0
        bar_count = 0
        rebar_complete = True
        # Main top/bottom bars run longitudinally and are distributed across
        # the deck width. Distribution bars run transversely and are spaced
        # along the bridge length.
        girder_bays = max(1, n_girders - 1)
        for dia_key, sp_key in (("rebar_bottom_dia", "rebar_bottom_spacing"),
                                ("rebar_top_dia", "rebar_top_spacing")):
            # Main transverse bars are spaced along the bridge length and
            # span one girder bay (transverse girder spacing).
            kg, count = _bar_group(dia_key, sp_key, (span, girder_spacing), girder_bays)
            rebar_kg += kg; bar_count += count
            rebar_complete = rebar_complete and count > 0
        # Longitudinal distribution bars run along the bridge and are spaced
        # across the full deck width.
        kg, count = _bar_group("rebar_long_dia", "rebar_long_spacing", (width, span))
        rebar_kg += kg; bar_count += count
        rebar_complete = rebar_complete and count > 0
        overhang = _number(inputs.get(KEY_TS_DECK_OVERHANG))
        if overhang > 0:
            kg, count = _bar_group("rebar_overhang_dia", "rebar_overhang_spacing",
                                   (span, overhang), 2)
            rebar_kg += kg; bar_count += count
            rebar_complete = rebar_complete and count > 0
        if rebar_complete and rebar_kg > 0:
            rebar_mt = rebar_kg / 1000.0
            q.update({"rebar_deck_qty": str(bar_count),
                      "rebar_deck_vol_formula": "Designed bar diameters and spacings; straight bars",
                      "rebar_deck_vol_total": f"{rebar_kg / STEEL_DENSITY_KG_M3:.5f}",
                      "rebar_deck_wt_single": f"{rebar_mt:.5f}",
                      "rebar_deck_wt_total": f"{rebar_mt:.5f}"})
    if rebar_mt > 0 and q.get("rebar_deck_wt_total", "N.A.") == "N.A.":
        q.update({"rebar_deck_qty": "1", "rebar_deck_vol_formula": "Explicit design reinforcement weight",
                  "rebar_deck_vol_total": f"{rebar_mt * 1000.0 / STEEL_DENSITY_KG_M3:.5f}",
                  "rebar_deck_wt_single": f"{rebar_mt:.5f}",
                  "rebar_deck_wt_total": f"{rebar_mt:.5f}"})

    # Girders: per-girder mass is kg/m; fallback uses calculated section area.
    girder_area = _number(_safe_resolve(inputs,
        "member_properties.girder_details.section_properties.area", 0))
    if girder_area <= 0:
        dims = [_number(_safe_resolve(inputs, k, 0)) for k in (
            "member_properties.girder_details.section_input.web_depth",
            "member_properties.girder_details.section_input.web_thickness",
            "member_properties.girder_details.section_input.top_flange_width",
            "member_properties.girder_details.section_input.top_flange_thickness",
            "member_properties.girder_details.section_input.bottom_flange_width",
            "member_properties.girder_details.section_input.bottom_flange_thickness")]
        if all(v > 0 for v in dims):
            dw, tw, bft, tft, bfb, tfb = dims
            girder_area = (dw * tw + bft * tft + bfb * tfb) / 1e6
    girder_density_kg_m3 = _density_kg_m3(
        inputs, "material.girder.density", DEFAULT_STEEL_UNIT_WEIGHT_KN_M3
    )
    if girder_area > 0:
        total_mass_kg = 0.0
        for i in range(n_girders):
            mass_per_m = _number(_safe_resolve(inputs,
                "member_properties.girder_details.section_properties.mass", i))
            total_mass_kg += mass_per_m * span if mass_per_m > 0 else girder_area * span * girder_density_kg_m3
        total_vol = girder_area * span * n_girders
        q.update({"steel_girders_vol_formula": f"${girder_area:.6f}\\,\\text{{m}}^2 \\times {span:.3f}\\,\\text{{m}}$ per girder",
                  "steel_girders_qty": str(n_girders), "steel_girders_vol_total": f"{total_vol:.4f}",
                  "steel_girders_wt_single": f"{total_mass_kg / n_girders / 1000:.5f}",
                  "steel_girders_wt_total": f"{total_mass_kg / 1000:.5f}"})

    # Intermediate cross-bracing. Aggregate each girder pair independently:
    # the UI permits different section sizes and panel counts in each bay.
    cb_geom = (outputs.get("crossbracing_forces_dict") or {}).get("geometry") or {}
    import re
    pair_pattern = re.compile(r"(?:^|\.)(G\d+G\d+)(?:\.|$)")
    cb_pairs = set()
    for source in (inputs, outputs):
        for key in source:
            if str(key).startswith(("member_properties.cross_bracing_details.",
                                    "transverse_member_design.cb.section_properties.")):
                match = pair_pattern.search(str(key))
                if match:
                    cb_pairs.add(match.group(1))
    if not cb_pairs and n_girders > 1:
        cb_pairs = {f"G{i}G{i+1}" for i in range(1, n_girders)}
    cb_pairs = sorted(cb_pairs, key=lambda pair: int(re.search(r"G(\d+)G", pair).group(1)))
    cb_configured = bool(cb_geom) or bool(cb_pairs and any(
        str(key).startswith("member_properties.cross_bracing_details.")
        for source in (inputs, outputs) for key in source))
    cb_spacing = _number(cb_geom.get("cb_spacing_m")) or _number(inputs.get("member_properties.cross_bracing_details.spacing"))
    default_panels = max(0, int(math.ceil(span / cb_spacing)) - 1) if cb_spacing > 0 else 0
    girder_spacing = _number(inputs.get(KEY_TS_GIRDER_SPACING))
    diag_len = _number(cb_geom.get("diagonal_length_m"))

    def _pair_panel_count(pair):
        prefix = f"member_properties.cross_bracing_details.no_of_cross_bracings.{pair}"
        values = [value for key, value in inputs.items()
                  if str(key).startswith(prefix) and value not in (None, "")]
        return max(0, int(_number(values[0]))) if values else default_panels

    def _pair_enabled(family, pair):
        prefix = f"member_properties.cross_bracing_details.{family}.{pair}."
        return (any(_enabled(value) for source in (inputs, outputs)
                    for key, value in source.items() if str(key).startswith(prefix))
                or _enabled(outputs.get(f"member_properties.cross_bracing_details.{family}",
                                        inputs.get(f"member_properties.cross_bracing_details.{family}"))))

    bracing_density_kg_m3 = _density_kg_m3(
        inputs, "material.cross_bracing.density", DEFAULT_STEEL_UNIT_WEIGHT_KN_M3
    )
    for family, section_name, length_m, multiplier in (
        ("bracing_top", "top_chord", girder_spacing, 1),
        ("bracing_bot", "bottom_chord", girder_spacing, 1),
        ("bracing_diag", "bracing", diag_len, 2),
    ):
        members = []
        for pair in cb_pairs:
            panel_count = _pair_panel_count(pair)
            if family == "bracing_diag":
                count = panel_count * multiplier if cb_configured else 0
            else:
                count = panel_count if _pair_enabled(section_name, pair) else 0
            area = _section_area_m2(outputs, f"transverse_member_design.cb.section_properties.{section_name}", pair)
            if area <= 0 and len(cb_pairs) == 1:
                area = _section_area_m2(outputs, f"transverse_member_design.cb.section_properties.{section_name}")
            members.append((area, length_m, count))
        _set_multi_item(q, family, members, bracing_density_kg_m3)

    # End diaphragms. The end-diaphragm design stage publishes section mass
    # (kg/m) per girder pair. Use its own member geometry: two support frames
    # per adjacent girder pair; X/K diagonal length follows the same 0.85D
    # depth ratio and horizontal projection used by _design_end_diaphragm_members.
    ed_pair_pattern = re.compile(r"(?:^|\.)(G\d+G\d+)(?:\.|$)")
    ed_pairs = set()
    for source in (inputs, outputs):
        for key in source:
            if str(key).startswith("member_properties.end_diaphragm_details."):
                match = ed_pair_pattern.search(str(key))
                if match:
                    ed_pairs.add(match.group(1))
    ed_pairs = sorted(ed_pairs, key=lambda pair: int(re.search(r"G(\d+)G", pair).group(1)))
    ed_configured = bool(ed_pairs)
    ed_steel_density_kg_m3 = _density_kg_m3(
        inputs, "material.end_diaphragm.density", DEFAULT_STEEL_UNIT_WEIGHT_KN_M3
    )
    ed_volume = 0.0
    ed_weight_mt = 0.0
    ed_count = 0
    ed_complete = True
    ed_formula_parts = []
    girder_depth_m = _number(_safe_resolve(inputs, KEY_MP_GIRDER_DEPTH, 0)) / 1000.0
    diaphragm_depth_m = 0.85 * girder_depth_m if girder_depth_m > 0 else 0.0

    for pair in ed_pairs:
        ed_type = str(outputs.get(f"member_properties.end_diaphragm_details.type.{pair}", "")).strip()
        if not ed_type:
            ed_type_keys = [value for key, value in inputs.items()
                            if str(key).startswith(f"member_properties.end_diaphragm_details.type.{pair}.")]
            ed_type = str(ed_type_keys[0]).strip() if ed_type_keys else ""
        if not ed_type:
            continue
        end_count = 2  # start and finish support frames
        if ed_type.lower() == "cross bracing":
            brace_type = str(outputs.get(f"member_properties.end_diaphragm_details.bracing_type.{pair}", ""))
            if not brace_type:
                vals = [value for key, value in inputs.items()
                        if str(key).startswith(f"member_properties.end_diaphragm_details.bracing_type.{pair}.")]
                brace_type = str(vals[0]) if vals else "X"
            horizontal = girder_spacing if brace_type.strip().lower().startswith("x") else girder_spacing / 2.0
            diagonal_length = math.hypot(horizontal, diaphragm_depth_m) if horizontal > 0 and diaphragm_depth_m > 0 else 0.0
            input_mass_keys = [
                key for key in inputs
                if str(key).startswith(
                    f"member_properties.end_diaphragm_details.section_properties.mass.{pair}."
                )
            ]
            input_mass = next(
                (_number(inputs.get(key)) for key in sorted(input_mass_keys)
                 if _number(inputs.get(key)) > 0),
                0.0,
            )
            diag_mass = _first_number(
                outputs, (f"transverse_member_design.ed.section_properties.end_diaphragm.M.{pair}",)
            ) or input_mass
            top_mass = _first_number(
                outputs, (f"transverse_member_design.ed.section_properties.top_chord.M.{pair}",)
            ) or input_mass
            bottom_mass = _first_number(
                outputs, (f"transverse_member_design.ed.section_properties.bottom_chord.M.{pair}",)
            ) or input_mass
            top_enabled = any(_enabled(value) for key, value in inputs.items()
                              if str(key).startswith(f"member_properties.end_diaphragm_details.top_chord.{pair}."))
            bottom_enabled = any(_enabled(value) for key, value in inputs.items()
                                 if str(key).startswith(f"member_properties.end_diaphragm_details.bottom_chord.{pair}."))
            family_data = [(diag_mass, diagonal_length, 2 * end_count, "diagonal")]
            if top_enabled:
                family_data.append((top_mass, girder_spacing, end_count, "top chord"))
            if bottom_enabled:
                family_data.append((bottom_mass, girder_spacing, end_count, "bottom chord"))
            for mass_per_m, length_m, count, label in family_data:
                ed_count += count
                if mass_per_m <= 0 or length_m <= 0:
                    ed_complete = False
                    continue
                total_kg = mass_per_m * length_m * count
                ed_weight_mt += total_kg / 1000.0
                ed_volume += total_kg / ed_steel_density_kg_m3
                ed_formula_parts.append(f"{pair} {label}: {count} x {mass_per_m:.3f} kg/m x {length_m:.3f} m")
        elif ed_type.lower() in {"rolled beam", "welded beam"}:
            mass_per_m = _first_number(outputs, (f"transverse_member_design.ed.section_properties.end_diaphragm.M.{pair}",))
            length_m = _first_number(outputs, (f"transverse_member_design.ed.section_properties.end_diaphragm.L.{pair}",)) or girder_spacing
            ed_count += end_count
            if mass_per_m <= 0 or length_m <= 0:
                ed_complete = False
                continue
            total_kg = mass_per_m * length_m * end_count
            ed_weight_mt += total_kg / 1000.0
            ed_volume += total_kg / ed_steel_density_kg_m3
            ed_formula_parts.append(f"{pair}: {end_count} x {mass_per_m:.3f} kg/m x {length_m:.3f} m")
        else:
            ed_complete = False

    if not ed_configured:
        q.update({"end_diaphragm_vol_formula": "Not configured", "end_diaphragm_qty": "0",
                  "end_diaphragm_vol_total": "0.0000", "end_diaphragm_wt_single": "0.00000",
                  "end_diaphragm_wt_total": "0.00000"})
    elif ed_complete and ed_count > 0:
        q.update({"end_diaphragm_vol_formula": r"$\sum (m_i L_i n_i)/\rho_s$",
                  "end_diaphragm_qty": str(ed_count),
                  "end_diaphragm_vol_total": f"{ed_volume:.5f}",
                  "end_diaphragm_wt_single": f"{ed_weight_mt / ed_count:.6f}",
                  "end_diaphragm_wt_total": f"{ed_weight_mt:.5f}"})
    else:
        q.update({"end_diaphragm_vol_formula": "N.A. — required member mass or geometry unavailable",
                  "end_diaphragm_qty": str(ed_count) if ed_count else "N.A.",
                  "end_diaphragm_vol_total": "N.A.", "end_diaphragm_wt_single": "N.A.",
                  "end_diaphragm_wt_total": "N.A."})

    # Shear studs: use actual longitudinal spacing and studs per section.
    spacing_mm = _number(outputs.get("steeldesign.details.shear.longitudinal_spacing"))
    studs_per_section = int(_number(outputs.get("steeldesign.details.shear.studs_per_section")))
    diameter_mm = _number(outputs.get("steeldesign.details.shear.diameter") or inputs.get("design_options.shear_studs.diameter"))
    height_mm = _number(outputs.get("steeldesign.details.shear.height") or inputs.get("design_options.shear_studs.height"))
    steel_density_kg_m3 = _density_kg_m3(
        inputs, "material.girder.density", DEFAULT_STEEL_UNIT_WEIGHT_KN_M3
    )
    if spacing_mm > 0 and studs_per_section > 0 and diameter_mm > 0 and height_mm > 0:
        n_sections = int(math.ceil(span * 1000.0 / spacing_mm)) + 1
        count = n_girders * studs_per_section * n_sections
        shank_volume = math.pi * (diameter_mm / 2000.0) ** 2 * (height_mm / 1000.0)
        head_diameter_mm = _number(outputs.get("steeldesign.details.shear.head_diameter")
                                   or inputs.get(KEY_DS_STUD_HEAD_DIAMETER))
        head_height_mm = _number(outputs.get("steeldesign.details.shear.head_height")
                                 or inputs.get(KEY_DS_STUD_HEAD_HEIGHT))
        head_volume = (math.pi * (head_diameter_mm / 2000.0) ** 2 * (head_height_mm / 1000.0)
                       if head_diameter_mm > 0 and head_height_mm > 0 else 0.0)
        vol_one = shank_volume + head_volume
        vol_total = vol_one * count
        wt_one = vol_one * STEEL_DENSITY_KG_M3 / 1000.0
        wt_total = vol_total * steel_density_kg_m3 / 1000.0
        q.update({"shear_studs_vol_formula": f"Shank + head volume: {vol_one:.8f} m3 per stud", "shear_studs_qty": str(count),
                  "shear_studs_vol_total": f"{vol_total:.5f}", "shear_studs_wt_single": f"{wt_one:.6f}",
                  "shear_studs_wt_total": f"{wt_total:.5f}"})

    # Crash barrier remains separately identified; it is not structural steel.
    barrier_area_raw = _number(inputs.get("typical_section.crash_barrier.area"), -1.0)
    barrier_type = str(inputs.get("typical_section.crash_barrier.type") or "").strip()
    barrier_density_kg_m3 = _density_kg_m3(
        inputs, "typical_section.crash_barrier.density", 25.0
    )
    # Saved .osi snapshots carry mm²; some live snapshots normalize this
    # field to m². Avoid dividing an already normalized value by 1e6 again.
    if barrier_area_raw > 0 and barrier_type.lower() not in {"none", "not applicable"}:
        barrier_area_m2 = barrier_area_raw / 1e6 if barrier_area_raw > 10.0 else barrier_area_raw
        barrier_vol = barrier_area_m2 * span * 2.0
        barrier_weight_mt = barrier_vol * barrier_density_kg_m3 / 1000.0
        q.update({"crash_barrier_vol_formula": f"{barrier_area_m2:.5f} m2 x {span:.3f} m x 2",
                  "crash_barrier_qty": "2", "crash_barrier_vol_total": f"{barrier_vol:.4f}",
                  "crash_barrier_wt_single": f"{barrier_weight_mt / 2:.4f}",
                  "crash_barrier_wt_total": f"{barrier_weight_mt:.4f}"})
    elif barrier_type:
        barrier_vol = None
        q.update({"crash_barrier_vol_formula": "N.A. — configured barrier area unavailable",
                  "crash_barrier_qty": "2", "crash_barrier_vol_total": "N.A.",
                  "crash_barrier_wt_single": "N.A.", "crash_barrier_wt_total": "N.A."})
    else:
        barrier_vol = 0.0
        q.update({"crash_barrier_vol_formula": "Not configured", "crash_barrier_qty": "0",
                  "crash_barrier_vol_total": "0.0000", "crash_barrier_wt_single": "0.0000",
                  "crash_barrier_wt_total": "0.0000"})

    # Totals consumed by Chapter 7's chart.
    steel_keys = ("steel_girders_wt_total", "bracing_top_wt_total", "bracing_bot_wt_total",
                  "bracing_diag_wt_total", "end_diaphragm_wt_total", "shear_studs_wt_total")
    known_steel = [_number(q.get(k)) for k in steel_keys if q.get(k) not in (None, "N.A.")]
    q["structural_steel_wt_subtotal"] = f"{sum(known_steel):.5f}" if known_steel else "N.A."
    steel_complete = all(q.get(k) not in (None, "N.A.") for k in steel_keys)
    q["structural_steel_wt_total"] = (
        f"{sum(_number(q.get(k)) for k in steel_keys):.5f}" if steel_complete else "N.A."
    )
    deck_concrete_m3 = _number(q.get("concrete_deck_vol_total"))
    if deck_concrete_m3 > 0 and barrier_vol is not None:
        q["concrete_volume_m3"] = f"{deck_concrete_m3 + barrier_vol:.4f}"
    else:
        q["concrete_volume_m3"] = "N.A."
    return q


def _safe_resolve(source: dict, key: str, index: int):
    try:
        return resolve_girder_value(source, key, index)
    except (KeyError, TypeError):
        return None
