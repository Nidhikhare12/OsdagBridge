"""
End diaphragm member design.

Implementation moved from PlateGirderBridge._design_end_diaphragm_members.
Force/geometry evaluation for ED Cross Bracing is inline here (not CrossBracingForces).
"""

from __future__ import annotations


def design_end_diaphragm_members(bridge) -> dict:
    """
    Run Osdag member designs for end-diaphragm bracing members (diagonals/chords)
    if type is "Cross Bracing", or calculate and populate section properties if
    type is "Rolled Beam" or "Welded Beam".

    Parameters
    ----------
    bridge : PlateGirderBridge
        Bridge instance providing input_dict, result_data, output_dict, and helpers.

    Returns
    -------
    dict — nested by pair → member → force_type → Osdag result.
    """
    import copy
    import math
    import sqlite3
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import resolve_girder_value as _gv
    from osdagbridge.core.utils.common import (
        KEY_TS_NO_OF_GIRDERS,
        KEY_TS_GIRDER_SPACING,
        KEY_MP_GIRDER_DEPTH,
        KEY_MP_ED_TYPE,
        KEY_MP_ED_BRACING_TYPE,
        KEY_MP_ED_BRACING_CONNECTION,
        KEY_MP_ED_BRACING_SECTION_DESIGNATION,
        KEY_MP_ED_TOP_CHORD,
        KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
        KEY_MP_ED_BOTTOM_CHORD,
        KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
        KEY_MP_ED_IS_SECTION,
        KEY_MP_ED_SYMMETRY,
        KEY_MP_ED_TOTAL_DEPTH,
        KEY_MP_ED_WEB_THICKNESS,
        KEY_MP_ED_TOP_FLANGE_WIDTH,
        KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
        KEY_MP_ED_TOP_FLANGE_THICKNESS,
        KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
        KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
        KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
        KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,
        KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
        KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
        KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,
        KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
        KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
        KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
    )
    


    if not bridge.result_data:
        print("[EndDiaphragm] No analysis results available — skipping.")
        return {}

    model = bridge.grillage_model.model
    if not model:
        print("[EndDiaphragm] No analysis grillage model available — skipping.")
        return {}

    # 1. Map support element IDs (start and end edges) to adjacent girder pairs
    start_elements = [str(e) for e in model.get_element(member="start_edge", options="elements")]
    end_elements = [str(e) for e in model.get_element(member="end_edge", options="elements")]
    all_edge_elements = start_elements + end_elements

    girders = bridge.result_data.get("girders", {})
    girder_node_sets = {
        g_name: set(g_data.get("nodes", []))
        for g_name, g_data in girders.items()
    }

    def _find_girder(node) -> str | None:
        for g_name, node_set in girder_node_sets.items():
            if node in node_set:
                return g_name
        return None

    pair_to_elements = {}
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

    # 2. Key mapping function for end diaphragm details
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

    # 3. Resolve possible intermediate girder pairs
    n_girders = int(bridge.input_dict[KEY_TS_NO_OF_GIRDERS])
    pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

    # Initialize output keys to None
    for pair in pairs:
        pair_id = pair.replace("-", "")
        
        # Diagonal/bracing
        for k in (
            KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
            KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
            KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,
        ):
            bridge.output_dict[make_pair_key(k, pair_id)] = None

        # Top chord
        for k in (
            KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
            KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
            KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,
        ):
            bridge.output_dict[make_pair_key(k, pair_id)] = None

        # Bottom chord
        for k in (
            KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
        ):
            bridge.output_dict[make_pair_key(k, pair_id)] = None

    # 4. Sizing and Geometry
    D = float(_gv(bridge.input_dict, KEY_MP_GIRDER_DEPTH))
    h = D * 0.85  # Default depth ratio
    s = float(bridge.input_dict[KEY_TS_GIRDER_SPACING])

    # 5. Process design results and queries
    forces_dict = {"pairs": {}}
    pair_designs = {}
    for pair in pairs:
        pair_designs[pair] = {}

    for i, pair in enumerate(pairs, start=1):
        pair_id = pair.replace("-", "")
        # M1 = start end, M2 = finish end. Both share the same design config
        # within a pair, so read from whichever slot has data.
        _m1 = f".{pair_id}.E{i}M1"
        _m2 = f".{pair_id}.E{i}M2"
        member_suffix = _m1 if bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{_m1}") else _m2

        ed_type = bridge.input_dict.get(f"{KEY_MP_ED_TYPE}{member_suffix}") or ""
        if not ed_type:
            continue   # no data for this pair, skip cleanly
        bridge.output_dict[make_pair_key(KEY_MP_ED_TYPE, pair_id)] = ed_type
        
        # -- CASE A: CROSS BRACING DIAPHRAGM --
        if ed_type == "Cross Bracing":
            bracing_type = bridge.input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{member_suffix}")
            top_chord_enabled = bridge.input_dict.get(f"{KEY_MP_ED_TOP_CHORD}{member_suffix}")
            top_chord_enabled = str(top_chord_enabled).strip().lower() not in ("no", "false", "0")
            bottom_chord_enabled = bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD}{member_suffix}")
            bottom_chord_enabled = str(bottom_chord_enabled).strip().lower() not in ("no", "false", "0")

            bridge.output_dict[make_pair_key(KEY_MP_ED_BRACING_TYPE, pair_id)] = bracing_type
            bridge.output_dict[make_pair_key(KEY_MP_ED_TOP_CHORD, pair_id)] = top_chord_enabled
            bridge.output_dict[make_pair_key(KEY_MP_ED_BOTTOM_CHORD, pair_id)] = bottom_chord_enabled

            # Compute Diagonal length
            horiz_proj = s if bracing_type in ("X", "X-Bracing") else s / 2.0
            L_d = math.sqrt(horiz_proj ** 2 + h ** 2)
            cos_alpha = math.cos(math.atan2(h, horiz_proj))

            # Collect envelope forces over both ends and all load cases
            elements = pair_to_elements.get(pair, [])
            diag_tens_max = 0.0
            diag_comp_max = 0.0
            chord_tens_max = 0.0
            chord_comp_max = 0.0
            diag_tens_lc = None
            diag_comp_lc = None
            chord_tens_lc = None
            chord_comp_lc = None
            _tol = 0.005

            for lc in bridge.result_data["loadcases"]:
                lc_str = str(lc)
                # Envelope pseudo cases copy the governing combination's values;
                # skip them so they can't steal the governing-LC label here.
                if lc_str.startswith("Envelope"):
                    continue
                for m in elements:
                    if lc_str not in bridge.result_data["forces"] or m not in bridge.result_data["forces"][lc_str]:
                        continue
                    vz_i = bridge.result_data["forces"][lc_str][m].get("Vz_i")
                    if vz_i is None:
                        continue
                    vz_kn = vz_i / 1000.0
                    f_diag = vz_kn / cos_alpha
                    f_chord = vz_kn

                    if f_diag > diag_tens_max:
                        diag_tens_max = f_diag
                        diag_tens_lc = lc_str
                    if f_chord > chord_tens_max:
                        chord_tens_max = f_chord
                        chord_tens_lc = lc_str
                    if f_diag < diag_comp_max:
                        diag_comp_max = f_diag
                        diag_comp_lc = lc_str
                    if f_chord < chord_comp_max:
                        chord_comp_max = f_chord
                        chord_comp_lc = lc_str

            pair_forces = {
                "diag_tension_kN": round(diag_tens_max, 3) if diag_tens_max > _tol else None,
                "diag_tension_gov_lc": diag_tens_lc if diag_tens_max > _tol else None,
                "diag_compression_kN": round(abs(diag_comp_max), 3) if diag_comp_max < -_tol else None,
                "diag_compression_gov_lc": diag_comp_lc if diag_comp_max < -_tol else None,
                "chord_tension_kN": round(chord_tens_max, 3) if chord_tens_max > _tol else None,
                "chord_tension_gov_lc": chord_tens_lc if chord_tens_max > _tol else None,
                "chord_compression_kN": round(abs(chord_comp_max), 3) if chord_comp_max < -_tol else None,
                "chord_compression_gov_lc": chord_comp_lc if chord_comp_max < -_tol else None,
            }
            forces_dict["pairs"][pair] = pair_forces

            # Run Osdag design checks
            from osdagbridge.core.utils.connect import (
                design_dict_struts_bolted,
                design_dict_struts_welded,
                design_dict_tension_bolted,
                design_dict_tension_welded,
                design_pool,
                run_calculation,
            )
            # Same rule as intermediate CB: only "Welded" selects welded templates;
            # missing / blank / invalid / "Bolted" → bolted.
            _conn = str(
                bridge.input_dict.get(f"{KEY_MP_ED_BRACING_CONNECTION}{member_suffix}")
                or ""
            ).strip().lower()
            if _conn == "welded":
                tension_template = design_dict_tension_welded
                strut_template = design_dict_struts_welded
            else:
                tension_template = design_dict_tension_bolted
                strut_template = design_dict_struts_bolted

            jobs = []
            for member, L_mm, t_key, c_key in (
                ("diagonal", round(L_d * 1000), "diag_tension_kN", "diag_compression_kN"),
                ("chord", round(s * 1000), "chord_tension_kN", "chord_compression_kN"),
            ):
                if pair_forces.get(t_key) is not None:
                    d = copy.deepcopy(tension_template)
                    d["Load.Axial"] = str(float(pair_forces[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))
                if pair_forces.get(c_key) is not None:
                    d = copy.deepcopy(strut_template)
                    d["Load.Axial"] = str(float(pair_forces[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

            if jobs:
                cpu_count = __import__("os").cpu_count() or 4
                max_workers = min(cpu_count, len(jobs))
                # spawn-context pool: forking under the design worker thread
                # deadlocks (see connect.design_pool).
                with design_pool(max_workers) as executor:
                    futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
                    for future, (p, member, force_type, _) in futures.items():
                        try:
                            res = future.result()
                        except Exception as exc:
                            print(f"  [EndDiaphragm] SKIP {p} {member} {force_type}: {exc}")
                            res = None
                        pair_designs.setdefault(p, {}).setdefault(member, {})[force_type] = res

            # Fetch selected designations
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

            chord_des = ""
            chord_data = member_designs.get("chord", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(chord_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    chord_des = str(sec)
                    break

            top_chord_des = chord_des if chord_des else bridge.input_dict.get(f"{KEY_MP_ED_TOP_CHORD_SECTION_DESIG}{member_suffix}")
            bottom_chord_des = chord_des if chord_des else bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG}{member_suffix}")

            # Populate diagonal properties
            if diag_des:
                bridge.output_dict[make_pair_key(KEY_MP_ED_BRACING_SECTION_DESIGNATION, pair_id)] = diag_des
                diag_details = bridge._query_crossbracing_section(diag_des)
                if diag_details:
                    bridge.output_dict[make_pair_key("member_properties.end_diaphragm_details.diagonal.section_type", pair_id)] = diag_details["type"]
                    
                    leg_h_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_h", pair_id)
                    leg_w_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_w", pair_id)
                    thick_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.thickness", pair_id)
                    if diag_details["type"] == "ANGLE":
                        bridge.output_dict[leg_h_key] = diag_details["H"] * 1000.0
                        bridge.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        bridge.output_dict[thick_key] = diag_details["tw"] * 1000.0
                    elif diag_details["type"] == "CHANNEL":
                        bridge.output_dict[leg_h_key] = diag_details["L"] * 1000.0
                        bridge.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        bridge.output_dict[thick_key] = diag_details["tw"] * 1000.0

                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = diag_details["L"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = diag_details["H"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = diag_details["B"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = diag_details["tw"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = diag_details["tF"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = diag_details["rz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = diag_details["M"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = diag_details["A"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = diag_details["Iz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = diag_details["Iv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = diag_details["rv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = diag_details["Zz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = diag_details["Zv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = diag_details["Zuz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = diag_details["Zuv"]

            # Populate chords
            if top_chord_enabled and top_chord_des:
                bridge.output_dict[make_pair_key(KEY_MP_ED_TOP_CHORD_SECTION_DESIG, pair_id)] = top_chord_des
                chord_details = bridge._query_crossbracing_section(top_chord_des)
                if chord_details:
                    bridge.output_dict[make_pair_key("member_properties.end_diaphragm_details.top_chord.section_type", pair_id)] = chord_details["type"]
                    tc_h_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.leg_h", pair_id)
                    tc_w_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.leg_w", pair_id)
                    tc_t_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.thickness", pair_id)
                    if chord_details["type"] == "ANGLE":
                        bridge.output_dict[tc_h_key] = chord_details["H"] * 1000.0
                        bridge.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                        bridge.output_dict[tc_t_key] = chord_details["tw"] * 1000.0
                    elif chord_details["type"] == "CHANNEL":
                        bridge.output_dict[tc_h_key] = chord_details["L"] * 1000.0
                        bridge.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                        bridge.output_dict[tc_t_key] = chord_details["tw"] * 1000.0

                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_L, pair_id)] = chord_details["L"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_H, pair_id)] = chord_details["H"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_B, pair_id)] = chord_details["B"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_M, pair_id)] = chord_details["M"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_A, pair_id)] = chord_details["A"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

            if bottom_chord_enabled and bottom_chord_des:
                bridge.output_dict[make_pair_key(KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG, pair_id)] = bottom_chord_des
                chord_details = bridge._query_crossbracing_section(bottom_chord_des)
                if chord_details:
                    bridge.output_dict[make_pair_key("member_properties.end_diaphragm_details.bottom_chord.section_type", pair_id)] = chord_details["type"]
                    bc_h_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.leg_h", pair_id)
                    bc_w_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.leg_w", pair_id)
                    bc_t_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.thickness", pair_id)
                    if chord_details["type"] == "ANGLE":
                        bridge.output_dict[bc_h_key] = chord_details["H"] * 1000.0
                        bridge.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                        bridge.output_dict[bc_t_key] = chord_details["tw"] * 1000.0
                    elif chord_details["type"] == "CHANNEL":
                        bridge.output_dict[bc_h_key] = chord_details["L"] * 1000.0
                        bridge.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                        bridge.output_dict[bc_t_key] = chord_details["tw"] * 1000.0

                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_L, pair_id)] = chord_details["L"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_H, pair_id)] = chord_details["H"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_B, pair_id)] = chord_details["B"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_M, pair_id)] = chord_details["M"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_A, pair_id)] = chord_details["A"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

        # -- CASE B: ROLLED BEAM DIAPHRAGM --
        elif ed_type == "Rolled Beam":
            from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_rolled_design import (
                envelope_end_diaphragm_vy_mz,
                run_simply_supported_design,
            )

            is_sec_des = bridge.input_dict.get(f"{KEY_MP_ED_IS_SECTION}{member_suffix}")
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
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = beam_details["Iv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = beam_details["rz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = beam_details["rv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = beam_details["Zz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = beam_details["Zv"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = beam_details["Zuz"]
                    bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = beam_details["Zuv"]

                elements = pair_to_elements.get(pair, [])
                vy_kN, mz_kNm = envelope_end_diaphragm_vy_mz(bridge.result_data, elements)
                forces_dict["pairs"][pair] = {
                    "Vy_kN": vy_kN if vy_kN > 0 else None,
                    "Mz_kNm": mz_kNm if mz_kNm > 0 else None,
                }
                osdag_result = run_simply_supported_design(
                    vy_kN=vy_kN,
                    mz_kNm=mz_kNm,
                    span_m=s,
                    section_designation=str(is_sec_des),
                )
                pair_designs.setdefault(pair, {})["simply_supported"] = osdag_result

        # -- CASE C: WELDED BEAM DIAPHRAGM --
        elif ed_type == "Welded Beam":
            depth = float(bridge.input_dict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{member_suffix}") or 0.0)
            web_t = float(bridge.input_dict.get(f"{KEY_MP_ED_WEB_THICKNESS}{member_suffix}") or 0.0)
            top_w = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{member_suffix}") or 0.0)
            bot_w = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{member_suffix}") or 0.0)
            top_t = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{member_suffix}") or 0.0)
            bot_t = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{member_suffix}") or 0.0)
            
            if depth > 0:
                h_w = depth - top_t - bot_t
                a_f1 = top_w * top_t
                a_f2 = bot_w * bot_t
                a_w = h_w * web_t
                a_total = a_f1 + a_f2 + a_w

                y_f2 = bot_t / 2.0
                y_w = bot_t + h_w / 2.0
                y_f1 = depth - top_t / 2.0
                y_c = (a_f2 * y_f2 + a_w * y_w + a_f1 * y_f1) / a_total

                i_z = (1.0 / 12.0) * bot_w * (bot_t ** 3) + a_f2 * ((y_c - y_f2) ** 2) + \
                    (1.0 / 12.0) * web_t * (h_w ** 3) + a_w * ((y_c - y_w) ** 2) + \
                    (1.0 / 12.0) * top_w * (top_t ** 3) + a_f1 * ((y_c - y_f1) ** 2)

                i_y = (1.0 / 12.0) * bot_t * (bot_w ** 3) + \
                    (1.0 / 12.0) * h_w * (web_t ** 3) + \
                    (1.0 / 12.0) * top_t * (top_w ** 3)

                r_z = math.sqrt(i_z / a_total)
                r_y = math.sqrt(i_y / a_total)

                z_z = i_z / max(y_c, depth - y_c)
                z_y = i_y / max(top_w / 2.0, bot_w / 2.0)

                if abs(a_f2 - a_f1) < 1e-3:
                    z_pz = top_w * top_t * (depth - top_t) + 0.25 * web_t * ((depth - 2.0 * top_t) ** 2)
                else:
                    y_p = bot_t + (a_total / 2.0 - a_f2) / web_t
                    z_pz = a_f2 * (y_p - bot_t / 2.0) + 0.5 * web_t * ((y_p - bot_t) ** 2) + \
                        a_f1 * (depth - y_p - top_t / 2.0) + 0.5 * web_t * ((depth - y_p - top_t) ** 2)

                z_py = 0.25 * top_t * (top_w ** 2) + 0.25 * bot_t * (bot_w ** 2) + 0.25 * h_w * (web_t ** 2)
                mass = a_total * 0.00785

                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = depth / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = top_w / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = web_t / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = top_t / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = mass
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = a_total / 100.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = i_z / 10000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = i_y / 10000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = r_z / 10.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = r_y / 10.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = z_z / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = z_y / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = z_pz / 1000.0
                bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = z_py / 1000.0

    if forces_dict.get("pairs"):
        bridge._print_enddiaphragm_design_results(forces_dict, pair_designs)
    
    bridge.output_dict["end_diaphragm_forces_dict"] = forces_dict
    bridge.end_diaphragm_design_results = pair_designs
    return pair_designs
