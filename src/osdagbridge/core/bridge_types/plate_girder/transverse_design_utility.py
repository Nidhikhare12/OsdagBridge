import copy
import math
import sqlite3
import re
from pathlib import Path
from typing import Optional

from osdagbridge.core.utils.common import (
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_BOTTOM_CHORD,
    KEY_MP_CB_BRACING_CONNECTION,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_TYPE,
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
    KEY_MP_ED_BRACING_CONNECTION,
)
from osdagbridge.core.utils.connect import (
    design_pool,
    run_calculation,
    design_dict_struts_bolted,
    design_dict_tension_bolted,
    design_dict_struts_welded,
    design_dict_tension_welded,
)

_DB_PATH = Path(__file__).parents[4] / "desktop" / "ui" / "widgets" / "Intg_osdag.sqlite"

def resolve_girder_value(input_dict: dict, key: str) -> str:
    """Helper to resolve a girder properties key which might be suffixed or scalar."""
    if key in input_dict:
        return str(input_dict[key])
    # Scan for a suffixed key, e.g. key.G1G2.B1M1
    for k, v in input_dict.items():
        if k.startswith(key):
            return str(v)
    return ""

class TransverseMemberDesignUtility:
    """
    Stateless utility containing clean, decoupled functions for intermediate
    cross bracing and end diaphragm designs.
    """

    @staticmethod
    def resolve_bracing_forces(
        result_data: dict,
        input_dict: dict,
        additional_inputs: dict,
        pair_elements: Optional[dict] = None,
        depth_ratio: float = 0.85,
        include_edge_beams: bool = False
    ) -> dict:
        """
        Resolves axial forces for diagonals and chords.
        If pair_elements is provided, it resolves forces for those specific elements (for End Diaphragms).
        Otherwise, it parses result_data["crossbracings"] for intermediate cross bracing.
        """
        if not result_data:
            return {}

        # 1. Geometry resolution
        D = float(resolve_girder_value(input_dict, KEY_MP_GIRDER_DEPTH) or 0.0)
        h = D * depth_ratio
        s = float(input_dict[KEY_TS_GIRDER_SPACING])

        # 2. Determine brace configuration
        brace_type = "X"
        top_chord = True
        bottom_chord = True

        if pair_elements is not None:
            # For End Diaphragms, read configuration from the first available member suffix
            # since end-diaphragm config is stored per pair in input_dict.
            # We can scan the input_dict to find a matching pair key
            n_girders = int(input_dict[KEY_TS_NO_OF_GIRDERS])
            pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]
            for i, p in enumerate(pairs, start=1):
                p_id = p.replace("-", "")
                suffix = f".{p_id}.E{i}M1"
                type_val = input_dict.get(f"{KEY_MP_ED_TYPE}{suffix}")
                if not type_val:
                    suffix = f".{p_id}.E{i}M2"
                    type_val = input_dict.get(f"{KEY_MP_ED_TYPE}{suffix}")
                if type_val == "Cross Bracing":
                    btype_val = input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{suffix}")
                    if btype_val:
                        brace_type = "K" if "K" in str(btype_val) else "X"
                    tc_val = input_dict.get(f"{KEY_MP_ED_TOP_CHORD}{suffix}")
                    if tc_val is not None:
                        top_chord = str(tc_val).strip().lower() not in ("no", "false", "0")
                    bc_val = input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD}{suffix}")
                    if bc_val is not None:
                        bottom_chord = str(bc_val).strip().lower() not in ("no", "false", "0")
                    break
        else:
            # For Intermediate Cross Bracing, read from additional_inputs
            bt = additional_inputs.get(KEY_MP_CB_TYPE)
            if bt:
                brace_type = "K" if "K" in str(bt) else "X"
            else:
                brace_type = "K" if "K" in str(additional_inputs.get(KEY_MP_CB_BRACING_SECTION_TYPE, "")).upper() else "X"
            
            tc_val = additional_inputs.get(KEY_MP_CB_TOP_CHORD)
            if tc_val is not None:
                top_chord = str(tc_val).strip().lower() not in ("no", "false", "0")
            bc_val = additional_inputs.get(KEY_MP_CB_BOTTOM_CHORD)
            if bc_val is not None:
                bottom_chord = str(bc_val).strip().lower() not in ("no", "false", "0")

        cb_spacing = 3.0
        if pair_elements is None:
            cb_spacing = float(additional_inputs.get(KEY_MP_CB_SPACING) or 3.0)

        horiz_proj = s if brace_type == "X" else s / 2.0
        L_d = math.sqrt(horiz_proj ** 2 + h ** 2)
        cos_alpha = math.cos(math.atan2(h, horiz_proj))

        _tol = 0.005
        _eq_tol = 1e-3
        pairs_forces = {}

        if pair_elements is not None:
            # End Diaphragms: elements mapped per pair
            for pair, elements in pair_elements.items():
                diag_tens_max = 0.0
                diag_comp_max = 0.0
                chord_tens_max = 0.0
                chord_comp_max = 0.0
                diag_tens_lc = None
                diag_comp_lc = None
                chord_tens_lc = None
                chord_comp_lc = None

                for lc in result_data.get("loadcases", []):
                    lc_str = str(lc)
                    if lc_str.startswith("Envelope"):
                        continue
                    for m in elements:
                        if lc_str not in result_data.get("forces", {}) or m not in result_data["forces"][lc_str]:
                            continue
                        vz_i = result_data["forces"][lc_str][m].get("Vz_i")
                        if vz_i is None:
                            continue
                        vz_kn = float(vz_i) / 1000.0
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

                pairs_forces[pair] = {
                    "diag_tension_kN":          round(diag_tens_max,       3) if diag_tens_max  > _tol else None,
                    "diag_tension_gov_lc":      diag_tens_lc if diag_tens_max  > _tol else None,
                    "diag_compression_kN":      round(abs(diag_comp_max),  3) if diag_comp_max  < -_tol else None,
                    "diag_compression_gov_lc":  diag_comp_lc if diag_comp_max  < -_tol else None,
                    "chord_tension_kN":         round(tens_chord if 'tens_chord' in locals() else chord_tens_max, 3) if chord_tens_max > _tol else None,
                    "chord_tension_gov_lc":     chord_tens_lc if chord_tens_max > _tol else None,
                    "chord_compression_kN":     round(abs(chord_comp_max), 3) if chord_comp_max < -_tol else None,
                    "chord_compression_gov_lc": chord_comp_lc if chord_comp_max < -_tol else None,
                }
        else:
            # Intermediate Cross Bracing: parse chains
            cb_chains = result_data.get("crossbracings", [])
            chain_stations = []
            for chain in cb_chains:
                mems = chain.get("members", [])
                if not mems:
                    continue
                left_g = chain.get("left_girder")
                right_g = chain.get("right_girder")
                if left_g is None or right_g is None:
                    continue
                chain_stations.append({
                    "first_member": str(mems[0]),
                    "last_member":  str(mems[-1]),
                    "left_girder":  left_g,
                    "right_girder": right_g,
                })

            raw_rows = []
            for lc in result_data.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope"):
                    continue
                for st in chain_stations:
                    if not include_edge_beams:
                        if st["left_girder"] in ("EB1", "EB2") or st["right_girder"] in ("EB1", "EB2"):
                            continue
                    
                    try:
                        vz_l = float(result_data["forces"][lc_str][st["first_member"]]["Vz_i"])
                        vz_r = float(result_data["forces"][lc_str][st["last_member"]]["Vz_j"])
                    except (KeyError, TypeError, ValueError):
                        continue

                    vz_l_kn = vz_l / 1000.0
                    vz_r_kn = vz_r / 1000.0

                    f_diag = vz_l_kn / cos_alpha
                    f_chord = vz_l_kn

                    raw_rows.append({
                        "LoadCase":    lc_str,
                        "Girder Pair": f"{st['left_girder']}-{st['right_girder']}",
                        "F_diag":      f_diag,
                        "F_chord":     f_chord,
                    })

            # Group by girder pair to find critical values
            import collections
            by_pair = collections.defaultdict(list)
            for r in raw_rows:
                by_pair[r["Girder Pair"]].append(r)

            for pair, grp in by_pair.items():
                tens_diag = max(0.0, max(r["F_diag"] for r in grp))
                comp_diag = min(0.0, min(r["F_diag"] for r in grp))
                tens_chord = max(0.0, max(r["F_chord"] for r in grp))
                comp_chord = min(0.0, min(r["F_chord"] for r in grp))

                # Identify governing LCs
                lc_td = next((r["LoadCase"] for r in grp if abs(r["F_diag"] - tens_diag) < 1e-5), None)
                lc_cd = next((r["LoadCase"] for r in grp if abs(r["F_diag"] - comp_diag) < 1e-5), None)
                lc_tc = next((r["LoadCase"] for r in grp if abs(r["F_chord"] - tens_chord) < 1e-5), None)
                lc_cc = next((r["LoadCase"] for r in grp if abs(r["F_chord"] - comp_chord) < 1e-5), None)

                pairs_forces[pair] = {
                    "diag_tension_kN":          round(tens_diag,       3) if tens_diag  > _tol else None,
                    "diag_tension_gov_lc":      lc_td if tens_diag  > _tol else None,
                    "diag_compression_kN":      round(abs(comp_diag),  3) if comp_diag  < -_tol else None,
                    "diag_compression_gov_lc":  lc_cd if comp_diag  < -_tol else None,
                    "chord_tension_kN":         round(tens_chord,      3) if tens_chord > _tol else None,
                    "chord_tension_gov_lc":     lc_tc if tens_chord > _tol else None,
                    "chord_compression_kN":     round(abs(comp_chord), 3) if comp_chord < -_tol else None,
                    "chord_compression_gov_lc": lc_cc if comp_chord < -_tol else None,
                }

        return {
            "brace_type":   brace_type,
            "top_chord":    top_chord,
            "bottom_chord": bottom_chord,
            "geometry": {
                "brace_type":        brace_type,
                "top_chord":         top_chord,
                "bottom_chord":      bottom_chord,
                "girder_spacing_m":  round(s, 4),
                "brace_height_m":    round(h, 4),
                "girder_depth_m":    round(D, 4),
                "diagonal_length_m": round(L_d, 4),
                "horiz_proj_m":      round(horiz_proj, 4),
                "alpha_deg":         round(math.degrees(math.atan2(h, horiz_proj)), 2),
                "cb_spacing_m":      round(cb_spacing, 3),
                "depth_ratio":       depth_ratio,
            },
            "pairs": pairs_forces,
        }

    @staticmethod
    def resolve_beam_forces(result_data: dict, elements: list[str]) -> dict:
        """
        Scans the given grillage elements across all non-envelope loadcases to find the
        maximum absolute vertical bending moment Mz and vertical shear force Vy for a beam diaphragm.
        """
        mz_max = 0.0
        vy_max = 0.0
        mz_lc = None
        vy_lc = None

        for lc in result_data.get("loadcases", []):
            lc_str = str(lc)
            if lc_str.startswith("Envelope"):
                continue
            for m in elements:
                if lc_str not in result_data.get("forces", {}) or m not in result_data["forces"][lc_str]:
                    continue
                forces = result_data["forces"][lc_str][m]
                for end in ("_i", "_j"):
                    mz_val = forces.get(f"Mz{end}")
                    vy_val = forces.get(f"Vy{end}")
                    if mz_val is not None:
                        mz_abs = abs(float(mz_val)) / 1000.0
                        if mz_abs > mz_max:
                            mz_max = mz_abs
                            mz_lc = lc_str
                    if vy_val is not None:
                        vy_abs = abs(float(vy_val)) / 1000.0
                        if vy_abs > vy_max:
                            vy_max = vy_abs
                            vy_lc = lc_str

        return {
            "moment_kNm": max(0.1, round(mz_max, 3)),
            "moment_gov_lc": mz_lc,
            "shear_kN": max(0.1, round(vy_max, 3)),
            "shear_gov_lc": vy_lc,
        }

    @staticmethod
    def run_bracing_designs(forces_dict: dict, ai: dict, connection_key: str) -> dict:
        """
        Launches parallel Osdag design processes (Tension/Compression, Bolted/Welded)
        for bracing members (diagonals and chords) using connect.design_pool.
        """
        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom = forces_dict.get("geometry", {})
        L_diag_mm = round(geom.get("diagonal_length_m", 0) * 1000)
        L_chord_mm = round(geom.get("horiz_proj_m", 0) * 1000)

        jobs = []
        for pair, vals in forces_dict["pairs"].items():
            pair_id = pair.replace("-", "")
            
            # Resolve connection type for this pair
            import re
            m = re.match(r"G(\d+)G(\d+)", pair_id)
            if m:
                g_idx = m.group(1)
                suffix = f".{pair_id}.B{g_idx}M1"
            else:
                m_ed = re.match(r"G(\d+)G", pair_id)
                g_idx = m_ed.group(1) if m_ed else "1"
                suffix = f".{pair_id}.E{g_idx}M1"
            
            pair_conn_key = connection_key + suffix
            pair_conn = ai.get(pair_conn_key)
            if pair_conn is None and "end_diaphragm" in connection_key:
                suffix2 = f".{pair_id}.E{g_idx}M2"
                pair_conn = ai.get(connection_key + suffix2)
            
            if pair_conn is None:
                pair_conn = ai.get(connection_key, "Bolted")
            is_welded = str(pair_conn).strip() == "Welded"

            for member, L_mm, t_key, c_key in (
                ("diagonal", L_diag_mm, "diag_tension_kN", "diag_compression_kN"),
                ("chord", L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
            ):
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(design_dict_tension_welded if is_welded else design_dict_tension_bolted)
                    d["Load.Axial"] = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(design_dict_struts_welded if is_welded else design_dict_struts_bolted)
                    d["Load.Axial"] = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        pair_designs = {}
        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))
        with design_pool(max_workers) as executor:
            futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
            for future, (p, member, force_type, _) in futures.items():
                try:
                    res = future.result()
                except Exception as exc:
                    print(f"  [TransverseDesignUtility] SKIP {p} {member} {force_type}: {exc}")
                    res = None
                pair_designs.setdefault(p, {}).setdefault(member, {})[force_type] = res

        return pair_designs

    @staticmethod
    def run_rolled_beam_design(s: float, forces_dict: dict, material: str) -> dict:
        """
        Runs Osdag Flexure member design to select the optimum rolled beam section.
        """
        from osdagbridge.core.utils.connect import design_dict_flexure, run_calculation
        d = copy.deepcopy(design_dict_flexure)
        d["Member.Length"] = str(float(s))
        d["Load.Moment"] = str(float(forces_dict["moment_kNm"]))
        d["Load.Shear"] = str(float(forces_dict["shear_kN"]))
        if material:
            d["Material"] = material
            d["Member.Material"] = material
        try:
            res = run_calculation(d)
            return res
        except Exception as e:
            print(f"  [TransverseDesignUtility] Rolled beam design failed: {e}")
            return {}

    @staticmethod
    def run_welded_beam_design(
        s: float,
        depth: float,
        web_t: float,
        top_w: float,
        top_t: float,
        bot_w: float,
        bot_t: float,
        forces_dict: dict,
        material: str
    ) -> dict:
        """
        Runs Osdag PlateGirderWelded design check to verify the capacity and safety of the customized welded beam section.
        """
        from osdagbridge.core.utils.connect import design_dict_plate_girder_welded, run_calculation
        d = copy.deepcopy(design_dict_plate_girder_welded)
        d["Total.Depth"] = str(int(depth))
        d["Web.Thickness"] = str(int(web_t))
        d["Topflange.Width"] = str(int(top_w))
        d["TopFlange.Thickness"] = str(int(top_t))
        d["Bottomflange.Width"] = str(int(bot_w))
        d["BottomFlange.Thickness"] = str(int(bot_t))
        d["Member.Length"] = str(int(s * 1000))
        d["Load.Moment"] = str(float(forces_dict["moment_kNm"]))
        d["Load.Shear"] = str(float(forces_dict["shear_kN"]))
        d["Deflection.Max"] = float(s * 1000)
        if material:
            d["Material"] = material
        try:
            res = run_calculation(d)
            return res
        except Exception as e:
            print(f"  [TransverseDesignUtility] Welded beam design failed: {e}")
            return {}
