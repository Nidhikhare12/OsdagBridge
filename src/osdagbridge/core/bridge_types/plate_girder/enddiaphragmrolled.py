r"""
End Diaphragm Rolled Beam Module (Task C).

Force extraction (Vy, Mz) and Osdag Simply Supported flexural member design
for Rolled Beam End Diaphragms.
"""

from __future__ import annotations

import copy
import json
import math
import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from osdagbridge.core.utils.common import (
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TYPE,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)


def _calculate_rolled_beam(d_base: dict, is_section: Optional[str]) -> Optional[dict]:
    """
    Execute Simply Supported flexural design in Osdag.
    First tries the user-selected section if specified.
    If specified section fails (or if auto-select / 'All'), falls back to searching
    all available rolled sections in the IS database.
    """
    from osdagbridge.core.utils.connect import run_calculation
    from osdagbridge.core.bridge_types.plate_girder.defaults import get_is_section_list

    # 1. Try specified section first if a specific section was selected
    if is_section and is_section not in ("All", "Customized", "", "Auto-optimize", "None"):
        d_spec = copy.deepcopy(d_base)
        d_spec["Member.Designation"] = [is_section]
        try:
            res = run_calculation(d_spec)
            if res and res.get("Optimum.Designation"):
                return res
        except Exception:
            pass

    # 2. Fallback: Search all available rolled sections
    d_all = copy.deepcopy(d_base)
    d_all["Member.Designation"] = get_is_section_list()
    try:
        res = run_calculation(d_all)
        if res and res.get("Optimum.Designation"):
            return res
    except Exception:
        pass

    return None

class EndDiaphragmRolled:
    """
    Step-wise force analysis and Osdag Simply Supported design for Rolled End Diaphragm.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge instance.
    is_section : str or None
        Specific IS section designation or None.
    include_edge_beams : bool
        Include edge beams if any. Default False.
    """

    def __init__(
        self,
        bridge,
        is_section: Optional[str] = None,
        include_edge_beams: bool = False,
    ):
        self.bridge = bridge
        self.include_edge_beams = include_edge_beams

        self._identify_configuration(is_section)
        self._init_geometry()

    def _identify_configuration(self, is_section: Optional[str]) -> None:
        ai = getattr(self.bridge, "additional_inputs", {}) or {}
        inp = getattr(self.bridge, "input_dict", {}) or {}

        def _ed_value(base_key: str):
            for d in (ai, inp):
                if not d or not isinstance(d, dict):
                    continue
                if base_key in d and d[base_key] is not None:
                    return d[base_key]
                pattern = rf"^{re.escape(base_key)}\.G\d+G\d+\.E\d+M[12]$"
                for key, value in d.items():
                    if value is not None and re.match(pattern, str(key)):
                        return value
                pattern_pair = rf"^{re.escape(base_key)}\.G\d+G\d+$"
                for key, value in d.items():
                    if value is not None and re.match(pattern_pair, str(key)):
                        return value
            return None

        if is_section is not None:
            self.is_section = str(is_section).strip()
        else:
            raw_sec = _ed_value(KEY_MP_ED_IS_SECTION)
            self.is_section = str(raw_sec).strip() if raw_sec else None

        self.ed_type = "Rolled Beam"
        self._ed_value = _ed_value

    def _init_geometry(self) -> None:
        inp = getattr(self.bridge, "input_dict", {}) or {}
        self.s = float(inp.get(KEY_TS_GIRDER_SPACING, 2.0) or 2.0)
        self.L_m = self.s

    def get_geometry_info(self) -> dict:
        return {
            "ed_type": "Rolled Beam",
            "is_section": self.is_section,
            "span_length_m": round(self.L_m, 4),
            "girder_spacing_m": round(self.s, 4),
        }

    def _map_edge_elements(self) -> dict[str, list[str]]:
        rd = getattr(self.bridge, "result_data", {}) or {}
        girders = rd.get("girders", {})
        girder_node_sets = {
            g_name: set(g_data.get("nodes", []))
            for g_name, g_data in girders.items()
        }

        def _find_girder(node) -> str | None:
            for g_name, node_set in girder_node_sets.items():
                if node in node_set:
                    return g_name
            return None

        all_edge_elements: list[str] = []
        grillage_model = getattr(self.bridge, "grillage_model", None)
        model = getattr(grillage_model, "model", None)
        if model and hasattr(model, "get_element"):
            try:
                start_elements = [str(e) for e in model.get_element(member="start_edge", options="elements")]
                end_elements = [str(e) for e in model.get_element(member="end_edge", options="elements")]
                all_edge_elements = start_elements + end_elements
            except Exception:
                all_edge_elements = []

        if not all_edge_elements:
            members = rd.get("members", {})
            for m_id, nodes in members.items():
                if len(nodes) == 2:
                    g1, g2 = _find_girder(nodes[0]), _find_girder(nodes[1])
                    if g1 and g2 and g1 != g2:
                        all_edge_elements.append(str(m_id))

        pair_to_elements: dict[str, list[str]] = {}
        for m in all_edge_elements:
            if m not in rd.get("members", {}):
                continue
            n1, n2 = rd["members"][m]
            g1 = _find_girder(n1)
            g2 = _find_girder(n2)
            if g1 and g2 and g1 != g2:
                if not self.include_edge_beams and (g1.startswith("EB") or g2.startswith("EB")):
                    continue
                idx1 = girders.get(g1, {}).get("index", 0)
                idx2 = girders.get(g2, {}).get("index", 0)
                pair = f"{g1}-{g2}" if idx1 <= idx2 else f"{g2}-{g1}"
                pair_to_elements.setdefault(pair, []).append(str(m))

        return pair_to_elements

    def compute_panel_forces(self, load_case_filter: Optional[str] = None) -> pd.DataFrame:
        rd = getattr(self.bridge, "result_data", {}) or {}
        forces_data = rd.get("forces", {})
        pair_to_elements = self._map_edge_elements()

        all_lcs = [
            lc for lc in rd.get("loadcases", [])
            if not str(lc).startswith("Envelope")
        ]
        if load_case_filter:
            all_lcs = [lc for lc in all_lcs if load_case_filter in str(lc)]

        rows = []
        for lc in all_lcs:
            lc_str = str(lc)
            if lc_str not in forces_data:
                continue
            for pair, elements in pair_to_elements.items():
                for m in elements:
                    elem_forces = forces_data[lc_str].get(m, {})
                    vy_i = elem_forces.get("Vy_i")
                    vy_j = elem_forces.get("Vy_j")
                    mz_i = elem_forces.get("Mz_i")
                    mz_j = elem_forces.get("Mz_j")

                    vy_kn = max(abs(float(vy_i or 0.0)), abs(float(vy_j or 0.0))) / 1000.0
                    mz_knm = max(abs(float(mz_i or 0.0)), abs(float(mz_j or 0.0))) / 1000.0

                    rows.append({
                        "LoadCase":     lc_str,
                        "Girder Pair":  pair,
                        "Member":       m,
                        "Vy_i (kN)":    round(float(vy_i)/1000.0, 4) if vy_i is not None else None,
                        "Vy_j (kN)":    round(float(vy_j)/1000.0, 4) if vy_j is not None else None,
                        "Mz_i (kNm)":   round(float(mz_i)/1000.0, 4) if mz_i is not None else None,
                        "Mz_j (kNm)":   round(float(mz_j)/1000.0, 4) if mz_j is not None else None,
                        "Vy_max (kN)":  round(vy_kn, 4),
                        "Mz_max (kNm)": round(mz_knm, 4),
                    })

        cols = ["LoadCase", "Girder Pair", "Member", "Vy_i (kN)", "Vy_j (kN)", "Mz_i (kNm)", "Mz_j (kNm)", "Vy_max (kN)", "Mz_max (kNm)"]
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

    def get_critical_forces(self, forces_dict: Optional[dict] = None) -> pd.DataFrame:
        if forces_dict is None:
            forces_dict = self.get_design_forces_dict()
        rows = []
        for pair, vals in forces_dict.get("pairs", {}).items():
            rows.append({
                "Girder Pair":      pair,
                "Vy (kN)":          vals.get("shear_Vy_kN"),
                "Vy Gov. LC":       vals.get("shear_Vy_gov_lc"),
                "Mz (kNm)":         vals.get("moment_Mz_kNm"),
                "Mz Gov. LC":       vals.get("moment_Mz_gov_lc"),
            })
        return pd.DataFrame(rows)

    def get_design_forces_dict(self) -> dict:
        rd = getattr(self.bridge, "result_data", {}) or {}
        pair_to_elements = self._map_edge_elements()
        forces_data = rd.get("forces", {})
        inp = getattr(self.bridge, "input_dict", {}) or {}

        n_girders = int(inp.get(KEY_TS_NO_OF_GIRDERS, 2) or 2)
        all_pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        pairs_dict: dict = {}
        _tol = 0.005

        for pair in all_pairs:
            elements = pair_to_elements.get(pair, [])
            vy_max = 0.0
            mz_max = 0.0
            vy_lc = None
            mz_lc = None

            for lc in rd.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope") or lc_str not in forces_data:
                    continue
                for m in elements:
                    if m not in forces_data[lc_str]:
                        continue
                    elem_f = forces_data[lc_str][m]
                    vy_i = elem_f.get("Vy_i")
                    vy_j = elem_f.get("Vy_j")
                    mz_i = elem_f.get("Mz_i")
                    mz_j = elem_f.get("Mz_j")

                    cur_vy = max(abs(float(vy_i or 0.0)), abs(float(vy_j or 0.0))) / 1000.0
                    cur_mz = max(abs(float(mz_i or 0.0)), abs(float(mz_j or 0.0))) / 1000.0

                    if cur_vy > vy_max:
                        vy_max = cur_vy
                        vy_lc = lc_str
                    if cur_mz > mz_max:
                        mz_max = cur_mz
                        mz_lc = lc_str

            pairs_dict[pair] = {
                "shear_Vy_kN":      round(vy_max, 3) if vy_max > _tol else 1.0,
                "shear_Vy_gov_lc":  vy_lc or "Manual/Default",
                "moment_Mz_kNm":    round(mz_max, 3) if mz_max > _tol else 1.0,
                "moment_Mz_gov_lc": mz_lc or "Manual/Default",
            }

        return {
            "ed_type":       "Rolled Beam",
            "is_section":    self.is_section,
            "geometry":      self.get_geometry_info(),
            "pairs":         pairs_dict,
        }

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        from osdagbridge.core.utils.connect import (
            design_dict_simply_supported,
            design_pool,
            run_calculation,
        )

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom = forces_dict.get("geometry", {})
        L_m = float(geom.get("span_length_m", self.L_m))

        jobs: list[tuple[str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            vy = float(vals.get("shear_Vy_kN") or 1.0)
            mz = float(vals.get("moment_Mz_kNm") or 1.0)

            d = copy.deepcopy(design_dict_simply_supported)
            d["Member.Length"] = str(round(L_m, 3))
            d["Load.Moment"] = str(max(round(mz, 3), 1.0))
            d["Load.Shear"] = str(max(round(vy, 3), 1.0))
            jobs.append((pair, "beam", d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM ROLLED BEAM DESIGNS ({len(forces_dict['pairs'])} pair(s))\n"
            f"  Span L={L_m:.3f} m\n"
            f"{sep}"
        )

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))
        t0 = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(_calculate_rolled_beam, j[2], self.is_section): j
                for j in jobs
            }
            for future, (pair, member_type, _) in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragmRolled] SKIP {pair} {member_type}: {exc}")
                    result = None
                results.setdefault(pair, {})[member_type] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    def print_configuration(self) -> None:
        g = self.get_geometry_info()
        print("\n" + "=" * 70)
        print(" " * 16 + "END DIAPHRAGM ROLLED BEAM CONFIGURATION")
        print("=" * 70)
        print(f"  Diaphragm type           : Rolled Beam")
        print(f"  IS Section designation   : {g.get('is_section') or 'Auto-optimize'}")
        print(f"  Span length (L)          : {g['span_length_m']:.4f} m")
        print(f"  Girder spacing (s)       : {g['girder_spacing_m']:.4f} m")
        print("=" * 70)

    def print_critical_forces(self, forces_dict: Optional[dict] = None) -> None:
        self.print_configuration()
        df = self.get_critical_forces(forces_dict)
        print("\n" + "=" * 80)
        print(" " * 18 + "END DIAPHRAGM ROLLED -- CRITICAL FORCES (Vy, Mz)")
        print("=" * 80)
        if df.empty:
            print("  No critical forces found.")
        else:
            print(df.to_string(index=False))
        print("=" * 80)
