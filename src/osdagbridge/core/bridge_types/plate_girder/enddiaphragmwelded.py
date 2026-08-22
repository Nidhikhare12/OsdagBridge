r"""
End Diaphragm Welded Beam Module (Task C).

Force extraction (Vy, Mz) and Osdag Plate Girder flexural/welded beam design
for Welded Beam End Diaphragms.
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
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_SYMMETRY,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)


def _calculate_welded_beam(d_base: dict) -> Optional[dict]:
    """
    Execute Plate Girder flexural design in Osdag.
    Tries customized inputs first. If customized inputs fail (e.g. web buckling),
    iterates available web thicknesses and falls back to full optimization (PSO).
    """
    from osdagbridge.core.utils.connect import run_calculation

    # 1. Try customized inputs as configured
    try:
        res = run_calculation(d_base)
        if res and res.get("Optimum.Designation"):
            return res
    except Exception:
        pass

    # 2. Try increasing web thickness while preserving depth and flange sizes
    web_thicknesses = ["12", "14", "16", "18", "20", "22", "25", "28", "32"]
    for tw_str in web_thicknesses:
        d_tw = copy.deepcopy(d_base)
        d_tw["Web.Thickness"] = tw_str
        try:
            res = run_calculation(d_tw)
            if res and res.get("Optimum.Designation"):
                return res
        except Exception:
            pass

    # 3. Fallback to full optimization (PSO) if fixed dimensions fail
    d_opt = copy.deepcopy(d_base)
    d_opt["Total.Design_Type"] = "Optimized"
    d_opt["Total.Depth"] = ""
    d_opt["Web.Thickness"] = "All"
    d_opt["Topflange.Width"] = ""
    d_opt["TopFlange.Thickness"] = "All"
    d_opt["Bottomflange.Width"] = ""
    d_opt["BottomFlange.Thickness"] = "All"
    try:
        res = run_calculation(d_opt)
        if res and res.get("Optimum.Designation"):
            return res
    except Exception:
        pass

    return None

class EndDiaphragmWelded:
    """
    Step-wise force analysis and Osdag Plate Girder design for Welded Beam End Diaphragm.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge instance.
    total_depth : float or None
        Total depth in mm.
    web_thickness : float or None
        Web thickness in mm.
    top_flange_width : float or None
        Width of top flange in mm.
    top_flange_thickness : float or None
        Thickness of top flange in mm.
    bottom_flange_width : float or None
        Width of bottom flange in mm.
    bottom_flange_thickness : float or None
        Thickness of bottom flange in mm.
    symmetry : str or None
        Symmetric or Asymmetric.
    include_edge_beams : bool
        Include edge beams if any. Default False.
    """

    def __init__(
        self,
        bridge,
        total_depth: Optional[float] = None,
        web_thickness: Optional[float] = None,
        top_flange_width: Optional[float] = None,
        top_flange_thickness: Optional[float] = None,
        bottom_flange_width: Optional[float] = None,
        bottom_flange_thickness: Optional[float] = None,
        symmetry: Optional[str] = None,
        include_edge_beams: bool = False,
    ):
        self.bridge = bridge
        self.include_edge_beams = include_edge_beams

        self._identify_configuration(
            total_depth, web_thickness,
            top_flange_width, top_flange_thickness,
            bottom_flange_width, bottom_flange_thickness,
            symmetry
        )
        self._init_geometry()

    def _identify_configuration(
        self,
        total_depth: Optional[float],
        web_thickness: Optional[float],
        top_flange_width: Optional[float],
        top_flange_thickness: Optional[float],
        bottom_flange_width: Optional[float],
        bottom_flange_thickness: Optional[float],
        symmetry: Optional[str],
    ) -> None:
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

        self.total_depth = float(total_depth) if total_depth is not None else (float(_ed_value(KEY_MP_ED_TOTAL_DEPTH) or 1200.0))
        self.web_thickness = float(web_thickness) if web_thickness is not None else (float(_ed_value(KEY_MP_ED_WEB_THICKNESS) or 10.0))
        self.top_flange_width = float(top_flange_width) if top_flange_width is not None else (float(_ed_value(KEY_MP_ED_TOP_FLANGE_WIDTH) or 300.0))
        self.top_flange_thickness = float(top_flange_thickness) if top_flange_thickness is not None else (float(_ed_value(KEY_MP_ED_TOP_FLANGE_THICKNESS) or 16.0))
        self.bottom_flange_width = float(bottom_flange_width) if bottom_flange_width is not None else (float(_ed_value(KEY_MP_ED_BOTTOM_FLANGE_WIDTH) or 300.0))
        self.bottom_flange_thickness = float(bottom_flange_thickness) if bottom_flange_thickness is not None else (float(_ed_value(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS) or 16.0))
        self.symmetry = symmetry or _ed_value(KEY_MP_ED_SYMMETRY) or "Symmetric"

        self.ed_type = "Welded Beam"
        self._ed_value = _ed_value

    def _init_geometry(self) -> None:
        inp = getattr(self.bridge, "input_dict", {}) or {}
        self.s = float(inp.get(KEY_TS_GIRDER_SPACING, 2.0) or 2.0)
        self.L_mm = self.s * 1000.0

    def get_geometry_info(self) -> dict:
        return {
            "ed_type": "Welded Beam",
            "total_depth_mm": round(self.total_depth, 2),
            "web_thickness_mm": round(self.web_thickness, 2),
            "top_flange_width_mm": round(self.top_flange_width, 2),
            "top_flange_thickness_mm": round(self.top_flange_thickness, 2),
            "bottom_flange_width_mm": round(self.bottom_flange_width, 2),
            "bottom_flange_thickness_mm": round(self.bottom_flange_thickness, 2),
            "symmetry": self.symmetry,
            "span_length_mm": round(self.L_mm, 2),
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
            "ed_type":       "Welded Beam",
            "geometry":      self.get_geometry_info(),
            "pairs":         pairs_dict,
        }

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        from osdagbridge.core.utils.connect import (
            design_dict_plate_girder,
            design_pool,
            run_calculation,
        )

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom = forces_dict.get("geometry", {})
        L_mm = float(geom.get("span_length_mm", self.L_mm))

        jobs: list[tuple[str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            vy = float(vals.get("shear_Vy_kN") or 1.0)
            mz = float(vals.get("moment_Mz_kNm") or 1.0)

            d = copy.deepcopy(design_dict_plate_girder)
            d["Member.Length"] = str(round(L_mm))
            d["Load.Moment"] = str(max(round(mz, 3), 1.0))
            d["Load.Shear"] = str(max(round(vy, 3), 1.0))
            
            if self.total_depth and float(self.total_depth) > 0:
                d["Total.Depth"] = str(round(float(self.total_depth)))
                d["Total.Design_Type"] = "Customized"
            if self.web_thickness and float(self.web_thickness) > 0:
                d["Web.Thickness"] = str(round(float(self.web_thickness)))
            if self.top_flange_width and float(self.top_flange_width) > 0:
                d["Topflange.Width"] = str(round(float(self.top_flange_width)))
            if self.top_flange_thickness and float(self.top_flange_thickness) > 0:
                d["TopFlange.Thickness"] = str(round(float(self.top_flange_thickness)))
            if self.bottom_flange_width and float(self.bottom_flange_width) > 0:
                d["Bottomflange.Width"] = str(round(float(self.bottom_flange_width)))
            if self.bottom_flange_thickness and float(self.bottom_flange_thickness) > 0:
                d["BottomFlange.Thickness"] = str(round(float(self.bottom_flange_thickness)))

            jobs.append((pair, "beam", d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM WELDED BEAM DESIGNS ({len(forces_dict['pairs'])} pair(s))\n"
            f"  Span L={L_mm:.1f} mm  Depth={self.total_depth:.1f} mm\n"
            f"{sep}"
        )

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))
        t0 = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(_calculate_welded_beam, j[2]): j
                for j in jobs
            }
            for future, (pair, member_type, _) in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragmWelded] SKIP {pair} {member_type}: {exc}")
                    result = None
                results.setdefault(pair, {})[member_type] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    def print_configuration(self) -> None:
        g = self.get_geometry_info()
        print("\n" + "=" * 70)
        print(" " * 16 + "END DIAPHRAGM WELDED BEAM CONFIGURATION")
        print("=" * 70)
        print(f"  Diaphragm type           : Welded Beam")
        print(f"  Total depth (D)          : {g['total_depth_mm']:.1f} mm")
        print(f"  Web thickness (tw)       : {g['web_thickness_mm']:.1f} mm")
        print(f"  Top flange (B x T)       : {g['top_flange_width_mm']:.1f} x {g['top_flange_thickness_mm']:.1f} mm")
        print(f"  Bottom flange (B x T)    : {g['bottom_flange_width_mm']:.1f} x {g['bottom_flange_thickness_mm']:.1f} mm")
        print(f"  Symmetry                 : {g['symmetry']}")
        print(f"  Span length (L)          : {g['span_length_mm']:.1f} mm")
        print(f"  Girder spacing (s)       : {g['girder_spacing_m']:.4f} m")
        print("=" * 70)

    def print_critical_forces(self, forces_dict: Optional[dict] = None) -> None:
        self.print_configuration()
        df = self.get_critical_forces(forces_dict)
        print("\n" + "=" * 80)
        print(" " * 18 + "END DIAPHRAGM WELDED -- CRITICAL FORCES (Vy, Mz)")
        print("=" * 80)
        if df.empty:
            print("  No critical forces found.")
        else:
            print(df.to_string(index=False))
        print("=" * 80)
