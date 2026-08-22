r"""
End Diaphragm Force Extraction and Osdag Design Pipeline (Task B).

Step-wise force extraction and member design for End Diaphragms
(Cross Bracing type), connecting to the Osdag CLI pipeline for both
Bolted and Welded tension members and compression struts.

Structural Model
----------------
End diaphragms are located at the bridge support ends (start_edge and end_edge
grillage elements). For cross-bracing diaphragms between each girder pair (G_i, G_{i+1}):

  X-type:
    G_i --- top chord ------- G_(i+1)   y = h
     |  \                   /  |
     |    \               /    |
     |      \           /      |
     |        \       /        |
     |          \   /          |
     |            X            |
     |          /   \          |
     |        /       \        |
     |      /           \      |
     |    /               \    |
     |  /                   \  |
    G_i --- bottom chord ---- G_(i+1)   y = 0

  K-type:
    G_i --- top chord ------- G_(i+1)   y = h
     |  \                   /  |
     |    \               /    |
     |      \           /      |
     |        \       /        |
     |          \   /          |
     |            V            |        y = 0 (apex at bottom)
     |         s/2   s/2       |
    G_i --- bottom chord ---- G_(i+1)

Force resolution
----------------
Global vertical shear Vz from support-edge elements:
  F_diag  = Vz / cos(alpha)   (kN)
  F_chord = Vz                (kN)
"""

from __future__ import annotations

import copy
import json
import math
import re
import time
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from osdagbridge.core.utils.common import (
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_BRACING_SECTION,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_SYMMETRY,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)

BRACE_X = "X"
BRACE_K = "K"


def _calculate_rolled_beam(d_base: dict, is_section: Optional[str]) -> Optional[dict]:
    from osdagbridge.core.utils.connect import run_calculation
    from osdagbridge.core.bridge_types.plate_girder.defaults import get_is_section_list

    candidates = []
    if is_section and is_section not in ("All", "Customized", "", "Auto-optimize", "None"):
        selected = copy.deepcopy(d_base)
        selected["Member.Designation"] = [is_section]
        candidates.append(selected)
    fallback = copy.deepcopy(d_base)
    fallback["Member.Designation"] = get_is_section_list()
    candidates.append(fallback)

    for design in candidates:
        try:
            result = run_calculation(design)
            if result and result.get("Optimum.Designation"):
                return result
        except Exception:
            continue
    return None


def _calculate_welded_beam(d_base: dict) -> Optional[dict]:
    from osdagbridge.core.utils.connect import run_calculation

    candidates = [copy.deepcopy(d_base)]
    for thickness in ("12", "14", "16", "18", "20", "22", "25", "28", "32"):
        design = copy.deepcopy(d_base)
        design["Web.Thickness"] = thickness
        candidates.append(design)
    optimized = copy.deepcopy(d_base)
    optimized.update({
        "Total.Design_Type": "Optimized",
        "Total.Depth": "",
        "Web.Thickness": "All",
        "Topflange.Width": "",
        "TopFlange.Thickness": "All",
        "Bottomflange.Width": "",
        "BottomFlange.Thickness": "All",
    })
    candidates.append(optimized)

    for design in candidates:
        try:
            result = run_calculation(design)
            if result and result.get("Optimum.Designation"):
                return result
        except Exception:
            continue
    return None


class _BeamEndDiaphragm:
    """Shared force extraction and envelope logic for beam end diaphragms."""

    ed_type = "Beam"

    def __init__(self, bridge, include_edge_beams: bool = False):
        self.bridge = bridge
        self.include_edge_beams = include_edge_beams
        self._identify_beam_configuration()
        self._init_beam_geometry()

    def _read_ed_value(self, base_key: str):
        ai = getattr(self.bridge, "additional_inputs", {}) or {}
        inp = getattr(self.bridge, "input_dict", {}) or {}
        for values in (ai, inp):
            if not isinstance(values, dict):
                continue
            if base_key in values and values[base_key] is not None:
                return values[base_key]
            for key, value in values.items():
                if value is None:
                    continue
                if re.match(rf"^{re.escape(base_key)}\.G\d+G\d+\.E\d+M[12]$", str(key)):
                    return value
                if re.match(rf"^{re.escape(base_key)}\.G\d+G\d+$", str(key)):
                    return value
        return None

    def _identify_beam_configuration(self) -> None:
        self._ed_value = self._read_ed_value

    def _init_beam_geometry(self) -> None:
        inp = getattr(self.bridge, "input_dict", {}) or {}
        self.s = float(inp.get(KEY_TS_GIRDER_SPACING, 2.0) or 2.0)

    def _map_edge_elements(self) -> dict[str, list[str]]:
        rd = getattr(self.bridge, "result_data", {}) or {}
        girders = rd.get("girders", {})
        node_to_girder = {
            node: name
            for name, data in girders.items()
            for node in data.get("nodes", [])
        }
        model = getattr(getattr(self.bridge, "grillage_model", None), "model", None)
        elements: list[str] = []
        if model and hasattr(model, "get_element"):
            try:
                elements = [
                    str(element)
                    for edge in ("start_edge", "end_edge")
                    for element in model.get_element(member=edge, options="elements")
                ]
            except Exception:
                elements = []
        if not elements:
            elements = [
                str(member)
                for member, nodes in rd.get("members", {}).items()
                if len(nodes) == 2
                and node_to_girder.get(nodes[0])
                and node_to_girder.get(nodes[1])
                and node_to_girder[nodes[0]] != node_to_girder[nodes[1]]
            ]

        pair_to_elements: dict[str, list[str]] = {}
        for element in elements:
            nodes = rd.get("members", {}).get(element)
            if not nodes or len(nodes) != 2:
                continue
            left = node_to_girder.get(nodes[0])
            right = node_to_girder.get(nodes[1])
            if not left or not right or left == right:
                continue
            if not self.include_edge_beams and (left.startswith("EB") or right.startswith("EB")):
                continue
            indices = (girders.get(left, {}).get("index", 0), girders.get(right, {}).get("index", 0))
            pair = f"{left}-{right}" if indices[0] <= indices[1] else f"{right}-{left}"
            pair_to_elements.setdefault(pair, []).append(element)
        return pair_to_elements

    def compute_panel_forces(self, load_case_filter: Optional[str] = None) -> pd.DataFrame:
        rd = getattr(self.bridge, "result_data", {}) or {}
        forces_data = rd.get("forces", {})
        rows = []
        for load_case in rd.get("loadcases", []):
            load_case = str(load_case)
            if load_case.startswith("Envelope") or load_case not in forces_data:
                continue
            if load_case_filter and load_case_filter not in load_case:
                continue
            pair_to_elements = self._map_edge_elements()
            for pair, elements in pair_to_elements.items():
                for element in elements:
                    force = forces_data[load_case].get(element, {})
                    vy_i, vy_j = force.get("Vy_i"), force.get("Vy_j")
                    mz_i, mz_j = force.get("Mz_i"), force.get("Mz_j")
                    rows.append({
                        "LoadCase": load_case,
                        "Girder Pair": pair,
                        "Member": element,
                        "Vy_i (kN)": round(float(vy_i) / 1000, 4) if vy_i is not None else None,
                        "Vy_j (kN)": round(float(vy_j) / 1000, 4) if vy_j is not None else None,
                        "Mz_i (kNm)": round(float(mz_i) / 1000, 4) if mz_i is not None else None,
                        "Mz_j (kNm)": round(float(mz_j) / 1000, 4) if mz_j is not None else None,
                        "Vy_max (kN)": max(abs(float(vy_i or 0)), abs(float(vy_j or 0))) / 1000,
                        "Mz_max (kNm)": max(abs(float(mz_i or 0)), abs(float(mz_j or 0))) / 1000,
                    })
        columns = ["LoadCase", "Girder Pair", "Member", "Vy_i (kN)", "Vy_j (kN)", "Mz_i (kNm)", "Mz_j (kNm)", "Vy_max (kN)", "Mz_max (kNm)"]
        return pd.DataFrame(rows, columns=columns)

    def get_design_forces_dict(self) -> dict:
        rd = getattr(self.bridge, "result_data", {}) or {}
        forces_data = rd.get("forces", {})
        inp = getattr(self.bridge, "input_dict", {}) or {}
        n_girders = int(inp.get(KEY_TS_NO_OF_GIRDERS, 2) or 2)
        pairs = {f"G{i}-G{i + 1}": {} for i in range(1, n_girders)}
        pair_to_elements = self._map_edge_elements()
        for pair in pairs:
            vy_max = mz_max = 0.0
            vy_lc = mz_lc = None
            for load_case in rd.get("loadcases", []):
                load_case = str(load_case)
                if load_case.startswith("Envelope") or load_case not in forces_data:
                    continue
                for element in pair_to_elements.get(pair, []):
                    force = forces_data[load_case].get(element, {})
                    vy = max(abs(float(force.get("Vy_i") or 0)), abs(float(force.get("Vy_j") or 0))) / 1000
                    mz = max(abs(float(force.get("Mz_i") or 0)), abs(float(force.get("Mz_j") or 0))) / 1000
                    if vy > vy_max:
                        vy_max, vy_lc = vy, load_case
                    if mz > mz_max:
                        mz_max, mz_lc = mz, load_case
            pairs[pair] = {
                "shear_Vy_kN": round(vy_max, 3) if vy_max > 0.005 else 1.0,
                "shear_Vy_gov_lc": vy_lc or "Manual/Default",
                "moment_Mz_kNm": round(mz_max, 3) if mz_max > 0.005 else 1.0,
                "moment_Mz_gov_lc": mz_lc or "Manual/Default",
            }
        return {"ed_type": self.ed_type, "geometry": self.get_geometry_info(), "pairs": pairs}

    def get_critical_forces(self, forces_dict: Optional[dict] = None) -> pd.DataFrame:
        forces_dict = forces_dict or self.get_design_forces_dict()
        return pd.DataFrame([
            {
                "Girder Pair": pair,
                "Vy (kN)": values.get("shear_Vy_kN"),
                "Vy Gov. LC": values.get("shear_Vy_gov_lc"),
                "Mz (kNm)": values.get("moment_Mz_kNm"),
                "Mz Gov. LC": values.get("moment_Mz_gov_lc"),
            }
            for pair, values in forces_dict.get("pairs", {}).items()
        ])


class EndDiaphragmRolled(_BeamEndDiaphragm):
    ed_type = "Rolled Beam"

    def __init__(self, bridge, is_section: Optional[str] = None, include_edge_beams: bool = False):
        self.is_section = str(is_section).strip() if is_section is not None else None
        super().__init__(bridge, include_edge_beams)
        if self.is_section is None:
            raw_section = self._ed_value(KEY_MP_ED_IS_SECTION)
            self.is_section = str(raw_section).strip() if raw_section else None

    def get_geometry_info(self) -> dict:
        return {
            "ed_type": self.ed_type,
            "is_section": self.is_section,
            "span_length_m": round(self.s, 4),
            "girder_spacing_m": round(self.s, 4),
        }

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        from osdagbridge.core.utils.connect import design_dict_simply_supported, design_pool
        from osdagbridge.core.bridge_types.plate_girder.defaults import get_is_section_list
        jobs = []
        for pair, values in forces_dict.get("pairs", {}).items():
            design = copy.deepcopy(design_dict_simply_supported)
            design.update({
                "Member.Length": str(round(self.s, 3)),
                "Load.Moment": str(max(round(float(values.get("moment_Mz_kNm") or 1), 3), 1.0)),
                "Load.Shear": str(max(round(float(values.get("shear_Vy_kN") or 1), 3), 1.0)),
            })
            jobs.append((pair, design))
        if not jobs:
            return {}
        results = {}
        with design_pool(min(__import__("os").cpu_count() or 4, len(jobs))) as executor:
            futures = {}
            for pair, design in jobs:
                if self.is_section and self.is_section not in ("All", "Customized", "", "Auto-optimize", "None"):
                    design["Member.Designation"] = [self.is_section]
                else:
                    design["Member.Designation"] = get_is_section_list()
                futures[executor.submit(_calculate_rolled_beam, design, self.is_section)] = pair
            for future, pair in futures.items():
                try:
                    results.setdefault(pair, {})["beam"] = future.result()
                except Exception:
                    results.setdefault(pair, {})["beam"] = None
        return results

    def get_design_forces_dict(self) -> dict:
        forces = super().get_design_forces_dict()
        forces["is_section"] = self.is_section
        return forces


class EndDiaphragmWelded(_BeamEndDiaphragm):
    ed_type = "Welded Beam"

    def __init__(self, bridge, total_depth: Optional[float] = None, web_thickness: Optional[float] = None,
                 top_flange_width: Optional[float] = None, top_flange_thickness: Optional[float] = None,
                 bottom_flange_width: Optional[float] = None, bottom_flange_thickness: Optional[float] = None,
                 symmetry: Optional[str] = None, include_edge_beams: bool = False):
        self.total_depth = total_depth
        self.web_thickness = web_thickness
        self.top_flange_width = top_flange_width
        self.top_flange_thickness = top_flange_thickness
        self.bottom_flange_width = bottom_flange_width
        self.bottom_flange_thickness = bottom_flange_thickness
        self.symmetry = symmetry
        super().__init__(bridge, include_edge_beams)
        for name, key, default in (
            ("total_depth", KEY_MP_ED_TOTAL_DEPTH, 1200.0),
            ("web_thickness", KEY_MP_ED_WEB_THICKNESS, 10.0),
            ("top_flange_width", KEY_MP_ED_TOP_FLANGE_WIDTH, 300.0),
            ("top_flange_thickness", KEY_MP_ED_TOP_FLANGE_THICKNESS, 16.0),
            ("bottom_flange_width", KEY_MP_ED_BOTTOM_FLANGE_WIDTH, 300.0),
            ("bottom_flange_thickness", KEY_MP_ED_BOTTOM_FLANGE_THICKNESS, 16.0),
        ):
            value = getattr(self, name)
            setattr(self, name, float(value if value is not None else (self._ed_value(key) or default)))
        self.symmetry = self.symmetry or self._ed_value(KEY_MP_ED_SYMMETRY) or "Symmetric"
        self.L_mm = self.s * 1000.0

    def get_geometry_info(self) -> dict:
        return {
            "ed_type": self.ed_type,
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

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        from osdagbridge.core.utils.connect import design_dict_plate_girder, design_pool
        jobs = []
        for pair, values in forces_dict.get("pairs", {}).items():
            design = copy.deepcopy(design_dict_plate_girder)
            design.update({
                "Member.Length": str(round(self.L_mm)),
                "Load.Moment": str(max(round(float(values.get("moment_Mz_kNm") or 1), 3), 1.0)),
                "Load.Shear": str(max(round(float(values.get("shear_Vy_kN") or 1), 3), 1.0)),
                "Total.Depth": str(round(self.total_depth)),
                "Total.Design_Type": "Customized",
                "Web.Thickness": str(round(self.web_thickness)),
                "Topflange.Width": str(round(self.top_flange_width)),
                "TopFlange.Thickness": str(round(self.top_flange_thickness)),
                "Bottomflange.Width": str(round(self.bottom_flange_width)),
                "BottomFlange.Thickness": str(round(self.bottom_flange_thickness)),
            })
            jobs.append((pair, design))
        if not jobs:
            return {}
        results = {}
        with design_pool(min(__import__("os").cpu_count() or 4, len(jobs))) as executor:
            futures = {executor.submit(_calculate_welded_beam, design): pair for pair, design in jobs}
            for future, pair in futures.items():
                try:
                    results.setdefault(pair, {})["beam"] = future.result()
                except Exception:
                    results.setdefault(pair, {})["beam"] = None
        return results


class EndDiaphragmForces:
    """
    Step-wise force analysis and Osdag member design for End Diaphragm.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge instance.
    brace_type : str or None
        'X' or 'K'. None -> read from bridge inputs.
    connection_type : str or None
        'Bolted' or 'Welded'. None -> read from bridge inputs.
    top_chord : bool or None
        True if top chord connects girders. None -> read from bridge inputs.
    bottom_chord : bool or None
        True if bottom chord connects girders. None -> read from bridge inputs.
    depth_ratio : float
        End diaphragm height ratio D * depth_ratio. Default 0.85.
    include_edge_beams : bool
        Include EB1/EB2 edge beams. Default False.
    """

    def __init__(
        self,
        bridge,
        brace_type:      Optional[str]   = None,
        connection_type: Optional[str]   = None,
        top_chord:       Optional[bool]  = None,
        bottom_chord:    Optional[bool]  = None,
        depth_ratio:     float = 0.85,
        include_edge_beams: bool = False,
    ):
        self.bridge = bridge
        self.depth_ratio = depth_ratio
        self.include_edge_beams = include_edge_beams

        self._identify_configuration(brace_type, connection_type, top_chord, bottom_chord)
        self._init_geometry()

    # =======================================================================
    # STEP 1 -- IDENTIFY END DIAPHRAGM CONFIGURATION
    # =======================================================================

    def _identify_configuration(
        self,
        brace_type:      Optional[str],
        connection_type: Optional[str],
        top_chord:       Optional[bool],
        bottom_chord:    Optional[bool],
    ) -> None:
        ai = getattr(self.bridge, "additional_inputs", {}) or {}
        inp = getattr(self.bridge, "input_dict", {}) or {}

        def _ed_value(base_key: str):
            """Resolve an end-diaphragm UI value from legacy or per-pair keys."""
            for d in (ai, inp):
                if not d or not isinstance(d, dict):
                    continue
                if base_key in d and d[base_key] is not None:
                    return d[base_key]
                # Match per-pair format e.g. .G1G2.E1M1 or .G1G2.E1M2
                pattern = rf"^{re.escape(base_key)}\.G\d+G\d+\.E\d+M[12]$"
                for key, value in d.items():
                    if value is not None and re.match(pattern, str(key)):
                        return value
                # Match .G1G2 format
                pattern_pair = rf"^{re.escape(base_key)}\.G\d+G\d+$"
                for key, value in d.items():
                    if value is not None and re.match(pattern_pair, str(key)):
                        return value
            return None

        # 1. Connection Type (Bolted / Welded)
        if connection_type is not None:
            self.connection_type = str(connection_type).strip().title()
        else:
            conn = _ed_value(KEY_MP_ED_BRACING_CONNECTION)
            self.connection_type = str(conn or "Bolted").strip().title()
        if self.connection_type not in ("Bolted", "Welded"):
            self.connection_type = "Bolted"

        # 2. Bracing Type (X / K)
        if brace_type is not None:
            raw = str(brace_type).strip().upper()
        else:
            raw = str(_ed_value(KEY_MP_ED_BRACING_TYPE) or "").strip().upper()

        if raw.startswith(f"{BRACE_X}-") or raw == BRACE_X:
            raw = BRACE_X
        elif raw.startswith(f"{BRACE_K}-") or raw == BRACE_K:
            raw = BRACE_K
        else:
            raw = BRACE_X
        self.brace_type: str = raw

        # 3. Chords
        if top_chord is not None:
            self.top_chord = bool(top_chord)
        else:
            val = _ed_value(KEY_MP_ED_TOP_CHORD)
            self.top_chord = str(val).strip().lower() not in ("no", "false", "0")

        if bottom_chord is not None:
            self.bottom_chord = bool(bottom_chord)
        else:
            val = _ed_value(KEY_MP_ED_BOTTOM_CHORD)
            self.bottom_chord = str(val).strip().lower() not in ("no", "false", "0")

        self._ed_value = _ed_value

    # =======================================================================
    # STEP 2 -- GEOMETRY
    # =======================================================================

    def _init_geometry(self) -> None:
        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_girder_value as _gv,
        )
        inp = getattr(self.bridge, "input_dict", {}) or {}
        self.D = float(_gv(inp, KEY_MP_GIRDER_DEPTH) or 1.5)
        self.tf_top = float(_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS) or 0.02)
        self.tf_bot = float(_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) or 0.02)
        self.h = self.D * self.depth_ratio
        self.s = float(inp.get(KEY_TS_GIRDER_SPACING, 2.0) or 2.0)

        if self.brace_type == BRACE_X:
            self.horiz_proj = self.s
        else:
            self.horiz_proj = self.s / 2.0

        self.L_d = math.sqrt(self.horiz_proj ** 2 + self.h ** 2)
        self.alpha_rad = math.atan2(self.h, self.horiz_proj)
        self.cos_alpha = math.cos(self.alpha_rad)

    def get_geometry_info(self) -> dict:
        return {
            "brace_type":        self.brace_type,
            "connection_type":   self.connection_type,
            "top_chord":         self.top_chord,
            "bottom_chord":      self.bottom_chord,
            "girder_spacing_m":  round(self.s, 4),
            "brace_height_m":    round(self.h, 4),
            "girder_depth_m":    round(self.D, 4),
            "diagonal_length_m": round(self.L_d, 4),
            "horiz_proj_m":      round(self.horiz_proj, 4),
            "alpha_deg":         round(math.degrees(self.alpha_rad), 2),
            "depth_ratio":       self.depth_ratio,
        }

    # =======================================================================
    # STEP 3 -- MAP SUPPORT EDGE ELEMENTS TO GIRDER PAIRS
    # =======================================================================

    def _map_edge_elements(self) -> dict[str, list[str]]:
        """
        Map support element IDs (start and end edges) to adjacent girder pairs.
        Returns { 'G1-G2': ['101', '102'], ... }
        """
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

        # Fetch edge elements from grillage model if available
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

        # If not retrieved from model, scan members connecting start/end nodes
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

    # =======================================================================
    # STEP 4 -- FORCE EXTRACTION & ENVELOPES
    # =======================================================================

    def compute_panel_forces(self, load_case_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Full force table for end diaphragm edge elements.
        """
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
                    vz_i = elem_forces.get("Vz_i")
                    vz_j = elem_forces.get("Vz_j")
                    if vz_i is None:
                        continue
                    vz_kn = float(vz_i) / 1000.0
                    f_diag = vz_kn / self.cos_alpha if abs(self.cos_alpha) > 1e-9 else 0.0
                    f_chord = vz_kn
                    rows.append({
                        "LoadCase":    lc_str,
                        "Girder Pair": pair,
                        "Member":      m,
                        "Vz_i (kN)":   round(vz_kn, 4),
                        "Vz_j (kN)":   round(float(vz_j)/1000.0, 4) if vz_j is not None else None,
                        "F_diag (kN)": round(f_diag, 4),
                        "F_chord (kN)": round(f_chord, 4),
                    })

        cols = ["LoadCase", "Girder Pair", "Member", "Vz_i (kN)", "Vz_j (kN)", "F_diag (kN)", "F_chord (kN)"]
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

    def get_critical_forces(self, forces_dict: Optional[dict] = None) -> pd.DataFrame:
        """
        Critical governing forces per girder pair.
        """
        if forces_dict is None:
            forces_dict = self.get_design_forces_dict()
        rows = []
        for pair, vals in forces_dict.get("pairs", {}).items():
            rows.append({
                "Girder Pair": pair,
                "Diag. Tension (kN)": vals.get("diag_tension_kN"),
                "Diag. Tens. Gov. LC": vals.get("diag_tension_gov_lc"),
                "Diag. Comp. (kN)": vals.get("diag_compression_kN"),
                "Diag. Comp. Gov. LC": vals.get("diag_compression_gov_lc"),
                "Chord Tension (kN)": vals.get("chord_tension_kN"),
                "Chord Tens. Gov. LC": vals.get("chord_tension_gov_lc"),
                "Chord Comp. (kN)": vals.get("chord_compression_kN"),
                "Chord Comp. Gov. LC": vals.get("chord_compression_gov_lc"),
            })
        return pd.DataFrame(rows)

    def get_design_forces_dict(self) -> dict:
        """
        Envelope forces per girder pair formatted for Osdag member design.
        """
        rd = getattr(self.bridge, "result_data", {}) or {}
        pair_to_elements = self._map_edge_elements()
        forces_data = rd.get("forces", {})
        inp = getattr(self.bridge, "input_dict", {}) or {}

        # Resolve pairs from input_dict if available
        n_girders = int(inp.get(KEY_TS_NO_OF_GIRDERS, 2) or 2)
        all_pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        pairs_dict: dict = {}
        _tol = 0.005

        for pair in all_pairs:
            elements = pair_to_elements.get(pair, [])
            diag_tens_max = 0.0
            diag_comp_max = 0.0
            chord_tens_max = 0.0
            chord_comp_max = 0.0
            diag_tens_lc = None
            diag_comp_lc = None
            chord_tens_lc = None
            chord_comp_lc = None

            for lc in rd.get("loadcases", []):
                lc_str = str(lc)
                if lc_str.startswith("Envelope") or lc_str not in forces_data:
                    continue
                for m in elements:
                    if m not in forces_data[lc_str]:
                        continue
                    vz_i = forces_data[lc_str][m].get("Vz_i")
                    if vz_i is None:
                        continue
                    vz_kn = float(vz_i) / 1000.0
                    f_diag = vz_kn / self.cos_alpha if abs(self.cos_alpha) > 1e-9 else 0.0
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

            pairs_dict[pair] = {
                "diag_tension_kN": round(diag_tens_max, 3) if diag_tens_max > _tol else None,
                "diag_tension_gov_lc": diag_tens_lc if diag_tens_max > _tol else None,
                "diag_compression_kN": round(abs(diag_comp_max), 3) if diag_comp_max < -_tol else None,
                "diag_compression_gov_lc": diag_comp_lc if diag_comp_max < -_tol else None,
                "chord_tension_kN": round(chord_tens_max, 3) if chord_tens_max > _tol else None,
                "chord_tension_gov_lc": chord_tens_lc if chord_tens_max > _tol else None,
                "chord_compression_kN": round(abs(chord_comp_max), 3) if chord_comp_max < -_tol else None,
                "chord_compression_gov_lc": chord_comp_lc if chord_comp_max < -_tol else None,
            }

        return {
            "brace_type":      self.brace_type,
            "connection_type": self.connection_type,
            "top_chord":       self.top_chord,
            "bottom_chord":    self.bottom_chord,
            "geometry":        self.get_geometry_info(),
            "pairs":           pairs_dict,
        }

    # =======================================================================
    # STEP 5 -- RUN OSDAG MEMBER DESIGNS
    # =======================================================================

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        """
        Run Osdag member designs for end diaphragm diagonals and chords.
        Supports both Bolted and Welded modules for tension members and compression struts.

        Parameters
        ----------
        forces_dict : dict
            Output of get_design_forces_dict().
        dev : bool
            If True, dumps forces_dict to tools/enddiaphragm_forces_dict.json.

        Returns
        -------
        dict::

            {
                "G1-G2": {
                    "diagonal": {"tension": result_or_None, "compression": result_or_None},
                    "chord":    {"tension": result_or_None, "compression": result_or_None},
                },
                ...
            }
        """
        if dev:
            out = Path(__file__).parents[5] / "tools" / "enddiaphragm_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[EndDiaphragm] dev dump -> {out}")

        from osdagbridge.core.utils.connect import (
            design_dict_struts_bolted,
            design_dict_tension_bolted,
            design_dict_struts_welded,
            design_dict_tension_welded,
            design_pool,
            run_calculation,
        )

        if self.connection_type == "Welded":
            tension_design = design_dict_tension_welded
            compression_design = design_dict_struts_welded
        else:
            tension_design = design_dict_tension_bolted
            compression_design = design_dict_struts_bolted

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom = forces_dict.get("geometry", {})
        L_diag_mm = round(geom.get("diagonal_length_m", self.L_d) * 1000)
        L_chord_mm = round(geom.get("girder_spacing_m", self.s) * 1000)

        jobs: list[tuple[str, str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            for member, L_mm, t_key, c_key in (
                ("diagonal", L_diag_mm, "diag_tension_kN", "diag_compression_kN"),
                ("chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
            ):
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(tension_design)
                    d["Load.Axial"] = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(compression_design)
                    d["Load.Axial"] = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM DESIGNS ({len(forces_dict['pairs'])} pair(s)) [{self.connection_type}]\n"
            f"  diag L={L_diag_mm} mm  chord L={L_chord_mm} mm\n"
            f"{sep}"
        )

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))
        t0 = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(run_calculation, j[3]): j
                for j in jobs
            }
            for future, (pair, member, force_type, _) in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragm] SKIP {pair} {member} {force_type}: {exc}")
                    result = None
                results.setdefault(pair, {}).setdefault(member, {})[force_type] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    # =======================================================================
    # PRINT / REPORT METHODS
    # =======================================================================

    def print_configuration(self) -> None:
        g = self.get_geometry_info()
        print("\n" + "=" * 70)
        print(" " * 18 + "END DIAPHRAGM CONFIGURATION & GEOMETRY")
        print("=" * 70)
        print(f"  Brace type               : {g['brace_type']}-type")
        print(f"  Connection type          : {self.connection_type}")
        print(f"  Top chord                : {'Yes' if g['top_chord'] else 'No'}")
        print(f"  Bottom chord             : {'Yes' if g['bottom_chord'] else 'No'}")
        print("-" * 70)
        print(f"  Girder spacing (s)       : {g['girder_spacing_m']:.4f} m")
        print(f"  Girder depth (D)         : {g['girder_depth_m']:.4f} m")
        print(f"  Diaphragm clear height(h): {g['brace_height_m']:.4f} m  (depth_ratio = {g['depth_ratio']})")
        if g["brace_type"] == BRACE_K:
            print(f"  Diag. horiz. projection  : {g['horiz_proj_m']:.4f} m  (= s/2)")
        print(f"  Diagonal length          : {g['diagonal_length_m']:.4f} m")
        print(f"  Diagonal angle (alpha)   : {g['alpha_deg']:.2f} deg from horizontal")
        print("=" * 70)

    def print_critical_forces(self, forces_dict: Optional[dict] = None) -> None:
        self.print_configuration()
        df = self.get_critical_forces(forces_dict)
        print("\n" + "=" * 95)
        print(" " * 22 + "END DIAPHRAGM -- CRITICAL DESIGN FORCES")
        print("=" * 95)
        if df.empty:
            print("  No critical forces -- Vz not in dataset or no load cases found.")
        else:
            print(df.to_string(index=False))
        print("=" * 95)
