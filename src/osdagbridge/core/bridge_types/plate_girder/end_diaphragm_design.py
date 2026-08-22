"""
end_diaphragm_design.py

Independent module for End Diaphragm design in OsdagBridge.
Supports 3 End Diaphragm types: Cross Bracing (Bolted/Welded), Rolled Beam, and Welded Beam.
"""

import copy
import math
from typing import Any

from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_rolled import (
    design_rolled_end_diaphragm,
)
from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_welded import (
    design_welded_end_diaphragm,
)
from osdagbridge.core.bridge_types.plate_girder.results_data import (
    _extract_osdag_summary,
)
from osdagbridge.core.utils.common import (
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_SYMMETRY,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_TD_ED_BOTTOM_CHORD_PROP_A,
    KEY_TD_ED_BOTTOM_CHORD_PROP_B,
    KEY_TD_ED_BOTTOM_CHORD_PROP_H,
    KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_IZ,
    KEY_TD_ED_BOTTOM_CHORD_PROP_L,
    KEY_TD_ED_BOTTOM_CHORD_PROP_M,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RZ,
    KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
    KEY_TD_ED_BOTTOM_CHORD_PROP_TW,
    KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ,
    KEY_TD_ED_BOTTOM_CHORD_PROP_ZV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ,
    KEY_TD_ED_PROP_A,
    KEY_TD_ED_PROP_B,
    KEY_TD_ED_PROP_H,
    KEY_TD_ED_PROP_IV,
    KEY_TD_ED_PROP_IZ,
    KEY_TD_ED_PROP_L,
    KEY_TD_ED_PROP_M,
    KEY_TD_ED_PROP_RV,
    KEY_TD_ED_PROP_RZ,
    KEY_TD_ED_PROP_TF,
    KEY_TD_ED_PROP_TW,
    KEY_TD_ED_PROP_ZUV,
    KEY_TD_ED_PROP_ZUZ,
    KEY_TD_ED_PROP_ZV,
    KEY_TD_ED_PROP_ZZ,
    KEY_TD_ED_TOP_CHORD_PROP_A,
    KEY_TD_ED_TOP_CHORD_PROP_B,
    KEY_TD_ED_TOP_CHORD_PROP_H,
    KEY_TD_ED_TOP_CHORD_PROP_IV,
    KEY_TD_ED_TOP_CHORD_PROP_IZ,
    KEY_TD_ED_TOP_CHORD_PROP_L,
    KEY_TD_ED_TOP_CHORD_PROP_M,
    KEY_TD_ED_TOP_CHORD_PROP_RV,
    KEY_TD_ED_TOP_CHORD_PROP_RZ,
    KEY_TD_ED_TOP_CHORD_PROP_TF,
    KEY_TD_ED_TOP_CHORD_PROP_TW,
    KEY_TD_ED_TOP_CHORD_PROP_ZUV,
    KEY_TD_ED_TOP_CHORD_PROP_ZUZ,
    KEY_TD_ED_TOP_CHORD_PROP_ZV,
    KEY_TD_ED_TOP_CHORD_PROP_ZZ,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)
from osdagbridge.core.utils.connect import (
    design_dict_struts_bolted,
    design_dict_struts_welded,
    design_dict_tension_bolted,
    design_dict_tension_welded,
    design_pool,
    run_calculation,
)


def design_end_diaphragm(
    bridge: Any,
    ed_type: str | None = None,
    connection_type: str | None = None,
) -> dict:
    """
    Run Osdag member designs for end-diaphragm members (Cross Bracing, Rolled Beam, or Welded Beam).

    Parameters
    ----------
    bridge : PlateGirderBridge
        The bridge instance containing grillage results and input parameters.
    ed_type : str | None
        Optional override for end diaphragm type ("Cross Bracing", "Rolled Beam", or "Welded Beam").
    connection_type : str | None
        Optional override for cross bracing connection type ("Bolted" or "Welded").

    Returns
    -------
    dict
        Nested dictionary keyed by pair -> member -> force_type -> Osdag result.
    """
    if not bridge.result_data or not hasattr(bridge, "grillage_model"):
        print("[EndDiaphragm] No analysis results available — skipping.")
        return {}

    model = bridge.grillage_model.model
    if not model:
        print("[EndDiaphragm] No analysis grillage model available — skipping.")
        return {}

    start_elements = [str(e) for e in model.get_element(member="start_edge", options="elements")]
    end_elements = [str(e) for e in model.get_element(member="end_edge", options="elements")]
    all_edge_elements = start_elements + end_elements

    girders = bridge.result_data.get("girders", {})
    girder_node_sets = {
        g_name: set(g_data.get("nodes", []))
        for g_name, g_data in girders.items()
    }

    def _find_girder(node: str) -> str | None:
        for g_name, node_set in girder_node_sets.items():
            if node in node_set:
                return g_name
        return None

    pair_to_elements: dict[str, list[str]] = {}
    for m in all_edge_elements:
        if m not in bridge.result_data.get("members", {}):
            continue
        n1, n2 = bridge.result_data["members"][m]
        g1 = _find_girder(n1)
        g2 = _find_girder(n2)
        if g1 and g2 and g1 != g2:
            idx1 = girders[g1].get("index", 0)
            idx2 = girders[g2].get("index", 0)
            pair = f"{g1}-{g2}" if idx1 <= idx2 else f"{g2}-{g1}"
            pair_to_elements.setdefault(pair, []).append(m)

    def make_pair_key(key: str, pair_id: str) -> str:
        for pfx in (
            "transverse_member_design.ed.section_properties.end_diaphragm",
            "transverse_member_design.ed.section_properties.top_chord",
            "transverse_member_design.ed.section_properties.bottom_chord",
        ):
            if key.startswith(pfx):
                suffix = key[len(pfx):].lstrip(".")
                return f"{pfx}.{pair_id}.{suffix}"
        pfx = "member_properties.end_diaphragm_details"
        if key.startswith(pfx):
            suffix = key[len(pfx):].lstrip(".")
            return f"{pfx}.{pair_id}.{suffix}"
        return f"{key}.{pair_id}"

    n_girders = int(bridge.input_dict[KEY_TS_NO_OF_GIRDERS])
    pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

    for pair in pairs:
        pair_id = pair.replace("-", "")
        for k in (
            KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
            KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
            KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,
            KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
            KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
            KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,
            KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
        ):
            bridge.output_dict[make_pair_key(k, pair_id)] = None

    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import resolve_girder_value as _gv
    D = float(_gv(bridge.input_dict, KEY_MP_GIRDER_DEPTH))
    h = D * 0.85
    s = float(bridge.input_dict[KEY_TS_GIRDER_SPACING])

    forces_dict: dict[str, dict] = {"pairs": {}}
    pair_designs: dict[str, dict] = {}
    for pair in pairs:
        pair_designs[pair] = {}

    for i, pair in enumerate(pairs, start=1):
        pair_id = pair.replace("-", "")
        _m1 = f".{pair_id}.E{i}M1"
        _m2 = f".{pair_id}.E{i}M2"
        member_suffix = _m1 if bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{_m1}") else _m2
        pair_ed_type = (
            bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{member_suffix}")
            or bridge.input_dict.get(f"{KEY_MP_ED_TYPE}.{pair_id}")
            or ed_type
            or "Cross Bracing"
        )
        if not pair_ed_type:
            continue
        bridge.output_dict[make_pair_key(KEY_MP_ED_TYPE, pair_id)] = pair_ed_type
        pair_designs[pair]["ed_type"] = pair_ed_type

        elements = pair_to_elements.get(pair, [])

        if pair_ed_type == "Cross Bracing":
            bracing_type = bridge.input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{member_suffix}")
            top_chord_enabled = bridge.input_dict.get(f"{KEY_MP_ED_TOP_CHORD}{member_suffix}")
            top_chord_enabled = str(top_chord_enabled).strip().lower() not in ("no", "false", "0")
            bottom_chord_enabled = bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD}{member_suffix}")
            bottom_chord_enabled = str(bottom_chord_enabled).strip().lower() not in ("no", "false", "0")

            bridge.output_dict[make_pair_key(KEY_MP_ED_BRACING_TYPE, pair_id)] = bracing_type
            bridge.output_dict[make_pair_key(KEY_MP_ED_TOP_CHORD, pair_id)] = top_chord_enabled
            bridge.output_dict[make_pair_key(KEY_MP_ED_BOTTOM_CHORD, pair_id)] = bottom_chord_enabled

            horiz_proj = s if bracing_type in ("X", "X-Bracing") else s / 2.0
            L_d = math.sqrt(horiz_proj ** 2 + h ** 2)
            cos_alpha = math.cos(math.atan2(h, horiz_proj))

            diag_tens_max = 0.0
            diag_comp_max = 0.0
            chord_tens_max = 0.0
            chord_comp_max = 0.0
            _tol = 0.005

            for lc in bridge.result_data.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope"):
                    continue
                for m in elements:
                    if lc_str not in bridge.result_data.get("forces", {}) or m not in bridge.result_data["forces"][lc_str]:
                        continue
                    vz_i = bridge.result_data["forces"][lc_str][m].get("Vz_i")
                    if vz_i is None:
                        continue
                    vz_kn = vz_i / 1000.0
                    f_diag = vz_kn / cos_alpha
                    f_chord = vz_kn

                    if f_diag > diag_tens_max:
                        diag_tens_max = f_diag
                    if f_chord > chord_tens_max:
                        chord_tens_max = f_chord
                    if f_diag < diag_comp_max:
                        diag_comp_max = f_diag
                    if f_chord < chord_comp_max:
                        chord_comp_max = f_chord

            pair_forces = {
                "diag_tension_kN": round(diag_tens_max, 3) if diag_tens_max > _tol else None,
                "diag_compression_kN": round(abs(diag_comp_max), 3) if diag_comp_max < -_tol else None,
                "chord_tension_kN": round(chord_tens_max, 3) if chord_tens_max > _tol else None,
                "chord_compression_kN": round(abs(chord_comp_max), 3) if chord_comp_max < -_tol else None,
            }
            forces_dict["pairs"][pair] = pair_forces

            conn_key = f"{KEY_MP_ED_BRACING_CONNECTION}{member_suffix}"
            conn_type = str(connection_type or bridge.input_dict.get(conn_key) or bridge.input_dict.get(KEY_MP_ED_BRACING_CONNECTION) or "Bolted").strip()
            is_welded = (conn_type.lower() == "welded")

            t_base = design_dict_tension_welded if is_welded else design_dict_tension_bolted
            c_base = design_dict_struts_welded if is_welded else design_dict_struts_bolted

            jobs = []
            for member, L_mm, t_k, c_k in (
                ("diagonal", round(L_d * 1000), "diag_tension_kN", "diag_compression_kN"),
                ("chord", round(s * 1000), "chord_tension_kN", "chord_compression_kN"),
            ):
                if pair_forces.get(t_k) is not None:
                    d = copy.deepcopy(t_base)
                    d["Load.Axial"] = str(float(pair_forces[t_k]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))
                if pair_forces.get(c_k) is not None:
                    d = copy.deepcopy(c_base)
                    d["Load.Axial"] = str(float(pair_forces[c_k]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

            if jobs:
                cpu_count = __import__("os").cpu_count() or 4
                max_workers = min(cpu_count, len(jobs))
                with design_pool(max_workers) as executor:
                    futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
                    for future, (p, member, force_type, _) in futures.items():
                        try:
                            res = future.result()
                        except Exception as exc:
                            print(f"  [EndDiaphragm] SKIP {p} {member} {force_type}: {exc}")
                            res = None
                        pair_designs.setdefault(p, {}).setdefault(member, {})[force_type] = res

            # Populate section properties for diagonal / chords
            member_designs = pair_designs.get(pair, {})
            diag_des = ""
            diag_data = member_designs.get("diagonal", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(diag_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    diag_des = str(sec)
                    break
            if not diag_des:
                diag_des = bridge.input_dict.get(f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}{member_suffix}")

            if diag_des:
                bridge.output_dict[make_pair_key(KEY_MP_ED_BRACING_SECTION_DESIGNATION, pair_id)] = diag_des
                diag_details = bridge._query_crossbracing_section(diag_des)
                if diag_details:
                    bridge.output_dict[make_pair_key("member_properties.end_diaphragm_details.diagonal.section_type", pair_id)] = diag_details["type"]
                    leg_h_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_h", pair_id)
                    leg_w_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_w", pair_id)
                    thick_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.thickness", pair_id)
                    bridge.output_dict[leg_h_key] = diag_details.get("H", 0) * 1000.0
                    bridge.output_dict[leg_w_key] = diag_details.get("B", 0) * 1000.0
                    bridge.output_dict[thick_key] = diag_details.get("tw", 0) * 1000.0

                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = diag_details["L"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = diag_details["H"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = diag_details["B"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = diag_details["tw"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = diag_details["tF"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = diag_details["rz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = diag_details["M"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = diag_details["A"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = diag_details["Iz"]

        elif pair_ed_type == "Rolled Beam":
            is_sec_des = (
                bridge.input_dict.get(f"{KEY_MP_ED_IS_SECTION}{member_suffix}")
                or bridge.input_dict.get(f"{KEY_MP_ED_IS_SECTION}.{pair_id}")
                or bridge.input_dict.get(KEY_MP_ED_IS_SECTION)
            )
            if is_sec_des:
                bridge.output_dict[make_pair_key(KEY_MP_ED_IS_SECTION, pair_id)] = is_sec_des
                beam_details = bridge._query_rolled_beam_section(is_sec_des)
                if beam_details:
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = beam_details["H"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = beam_details["B"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = beam_details["tw"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = beam_details["tF"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = beam_details["M"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = beam_details["A"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = beam_details["Iz"]

            # Extract forces
            max_vz = 0.0
            max_my = 0.0
            for lc in bridge.result_data.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope"):
                    continue
                for m in elements:
                    if lc_str not in bridge.result_data.get("forces", {}) or m not in bridge.result_data["forces"][lc_str]:
                        continue
                    f_m = bridge.result_data["forces"][lc_str][m]
                    vz = max(abs(f_m.get("Vz_i") or 0.0), abs(f_m.get("Vz_j") or 0.0)) / 1000.0
                    my = max(abs(f_m.get("My_i") or 0.0), abs(f_m.get("My_j") or 0.0)) / 1000.0
                    if vz > max_vz:
                        max_vz = vz
                    if my > max_my:
                        max_my = my

            print(
                f"[DEBUG Rolled Beam] Dispatching pair {pair!r}: "
                f"is_sec_des={is_sec_des}, span={s}, moment={max_my}, shear={max_vz}"
            )

            try:
                if is_sec_des:
                    res = design_rolled_end_diaphragm(
                        designation=is_sec_des,
                        span_m=s,
                        moment_kNm=max_my,
                        shear_kN=max_vz,
                    )
                    res["moment_kNm"] = max_my
                    res["shear_kN"] = max_vz
                    res["Load.Moment"] = max_my
                    res["Load.Shear"] = max_vz
                    pair_designs[pair]["beam"] = res
                    pair_designs[pair]["moment_kNm"] = max_my
                    pair_designs[pair]["shear_kN"] = max_vz

                    # Post-design validation
                    if res.get("design_status") is False:
                        reason = res.get("design_failure_reason", "unknown")
                        print(
                            f"[DEBUG Rolled Beam] WARNING: Design FAILED for pair {pair!r}. "
                            f"Reason: {reason}"
                        )
                    else:
                        attempt = res.get("design_attempt", "unknown")
                        opt_des = res.get("Optimum.Designation", "?")
                        opt_ur = res.get("Optimum.UR", "?")
                        if attempt == "fallback_list":
                            orig = res.get("original_designation", is_sec_des)
                            print(
                                f"[DEBUG Rolled Beam] Pair {pair!r}: User section '{orig}' "
                                f"was inadequate. Osdag selected '{opt_des}' "
                                f"(UR={opt_ur}) from fallback list."
                            )
                        else:
                            print(
                                f"[DEBUG Rolled Beam] Pair {pair!r}: Design OK with "
                                f"'{opt_des}' (UR={opt_ur})."
                            )
                else:
                    print(f"[DEBUG Rolled Beam] WARNING: is_sec_des is empty for pair {pair!r}")
            except Exception:
                import traceback
                print(f"[DEBUG Rolled Beam] ERROR in design_rolled_end_diaphragm for pair {pair!r}:")
                traceback.print_exc()

        elif pair_ed_type == "Welded Beam":
            depth = float(bridge.input_dict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_TOTAL_DEPTH) or 300.0)
            web_t = float(bridge.input_dict.get(f"{KEY_MP_ED_WEB_THICKNESS}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_WEB_THICKNESS) or 8.0)
            top_w = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_TOP_FLANGE_WIDTH) or 150.0)
            bot_w = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_BOTTOM_FLANGE_WIDTH) or 150.0)
            top_t = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_TOP_FLANGE_THICKNESS) or 10.0)
            bot_t = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{member_suffix}") or bridge.input_dict.get(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS) or 10.0)

            h_w = depth - top_t - bot_t
            a_f1 = top_w * top_t
            a_f2 = bot_w * bot_t
            a_w = h_w * web_t
            a_total = a_f1 + a_f2 + a_w

            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = depth / 1000.0
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = max(top_w, bot_w) / 1000.0
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = web_t / 1000.0
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = max(top_t, bot_t) / 1000.0
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = a_total / 1e6

            # Extract forces
            max_vz = 0.0
            max_my = 0.0
            for lc in bridge.result_data.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope"):
                    continue
                for m in elements:
                    if lc_str not in bridge.result_data.get("forces", {}) or m not in bridge.result_data["forces"][lc_str]:
                        continue
                    f_m = bridge.result_data["forces"][lc_str][m]
                    vz = max(abs(f_m.get("Vz_i") or 0.0), abs(f_m.get("Vz_j") or 0.0)) / 1000.0
                    my = max(abs(f_m.get("My_i") or 0.0), abs(f_m.get("My_j") or 0.0)) / 1000.0
                    if vz > max_vz:
                        max_vz = vz
                    if my > max_my:
                        max_my = my

            print(
                f"[DEBUG Welded Beam] Dispatching pair {pair!r}: "
                f"depth={depth}, web_t={web_t}, top_w={top_w}, top_t={top_t}, "
                f"bot_w={bot_w}, bot_t={bot_t}, span={s}, moment={max_my}, shear={max_vz}"
            )

            try:
                res = design_welded_end_diaphragm(
                    depth_mm=depth,
                    web_thk_mm=web_t,
                    top_width_mm=top_w,
                    top_thk_mm=top_t,
                    bot_width_mm=bot_w,
                    bot_thk_mm=bot_t,
                    span_m=s,
                    moment_kNm=max_my,
                    shear_kN=max_vz,
                )
                res["moment_kNm"] = max_my
                res["shear_kN"] = max_vz
                res["Load.Moment"] = max_my
                res["Load.Shear"] = max_vz
                pair_designs[pair]["beam"] = res
                pair_designs[pair]["moment_kNm"] = max_my
                pair_designs[pair]["shear_kN"] = max_vz
                print(f"[DEBUG Welded Beam] Result stored for pair {pair!r}: {res}")
            except Exception as exc:
                import traceback
                print(f"[DEBUG Welded Beam] ERROR calling design_welded_end_diaphragm for {pair!r}: {exc}")
                traceback.print_exc()

    return pair_designs
