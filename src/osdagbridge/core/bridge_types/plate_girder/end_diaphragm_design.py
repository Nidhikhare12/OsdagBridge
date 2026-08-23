"""
EndDiaphragmForces
------------------
Standalone force analysis and Osdag design dispatch for End Diaphragm
members configured as Cross Bracing (X-type or K-type).

Design isolation guarantee
--------------------------
This module reads **only** ``KEY_MP_ED_*`` input keys.  It never reads
``KEY_MP_CB_*`` keys, and it never calls ``CrossBracingForces`` or
``TransverseMemberDesignUtility``.  Changes to the intermediate cross-bracing
pipeline cannot silently affect end-diaphragm results.

Force extraction
----------------
Forces come from the edge (support) transverse elements that were pre-mapped to
girder pairs by ``_design_end_diaphragm_members`` in ``plategirderbridge.py``.
The ``pair_to_elements`` dict  (``{pair: [member_ids]}``) is passed in at
construction time so this class stays stateless with respect to the grillage
model.

The force resolution logic mirrors ``CrossBracingForces`` but operates on the
supplied element list rather than the ``crossbracings`` chain map:

  F_diag  =  Vz_i / cos(alpha)
  F_chord =  Vz_i

where ``alpha = atan2(h, horiz_proj)`` and ``h = D * depth_ratio``.

Usage
-----
    ed = EndDiaphragmForces(bridge=pgb, pair_to_elements=pair_map)
    forces = ed.resolve_ed_forces()
    designs = ed.run_ed_bracing_designs(forces)
"""

from __future__ import annotations

import copy
import math
import re
import time
from typing import Optional

from osdagbridge.core.utils.common import (
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_BRACE_X = "X"
_BRACE_K = "K"
_TOL_KN  = 5e-3   # 5 N — forces below this are treated as zero


def _resolve_girder_value(input_dict: dict, key: str) -> str:
    """Return the value for *key* tolerating per-girder suffixed keys."""
    if key in input_dict:
        return str(input_dict[key])
    for k, v in input_dict.items():
        if k.startswith(key):
            return str(v)
    return ""


# ===========================================================================
class EndDiaphragmForces:
    """
    Force analysis and Osdag design dispatcher for End Diaphragm Cross
    Bracing configuration.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge (``design()`` already called).
    pair_to_elements : dict[str, list[str]]
        Mapping of girder-pair label (e.g. ``"G1-G2"``) to the list of
        transverse member IDs at the support edge for that pair.
        Computed by ``_design_end_diaphragm_members`` from the grillage model.
    depth_ratio : float
        Clear brace height = D × depth_ratio.  Default 0.85 (same as CB).
    """

    def __init__(
        self,
        bridge,
        pair_to_elements: dict[str, list[str]],
        depth_ratio: float = 0.85,
    ) -> None:
        self.bridge           = bridge
        self.pair_to_elements = pair_to_elements
        self.depth_ratio      = depth_ratio

        # Geometry (shared across all pairs; per-pair brace config below)
        inp        = bridge.input_dict
        self.D     = float(_resolve_girder_value(inp, KEY_MP_GIRDER_DEPTH))
        self.h     = self.D * depth_ratio
        self.s     = float(inp[KEY_TS_GIRDER_SPACING])
        self.tf_top = float(_resolve_girder_value(inp, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS) or 0)
        self.tf_bot = float(_resolve_girder_value(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) or 0)

    # =======================================================================
    # Per-pair brace configuration (reads only ED keys)
    # =======================================================================

    def _ed_config_for_pair(self, pair_id: str, girder_idx: str) -> dict:
        """
        Return the ED brace configuration for one pair.

        Reads ``KEY_MP_ED_BRACING_TYPE``, ``KEY_MP_ED_TOP_CHORD``,
        ``KEY_MP_ED_BOTTOM_CHORD``, and ``KEY_MP_ED_BRACING_CONNECTION``
        from ``bridge.input_dict`` using the per-pair suffix.
        Falls back gracefully to safe defaults.  No CB key is ever read.
        """
        inp = self.bridge.input_dict

        btype_raw = None
        conn_raw  = None
        tc_raw    = None
        bc_raw    = None
        for m_idx in ("M1", "M2"):
            suffix = f".{pair_id}.E{girder_idx}{m_idx}"
            if not btype_raw:
                btype_raw = inp.get(f"{KEY_MP_ED_BRACING_TYPE}{suffix}")
            if not conn_raw:
                conn_raw  = inp.get(f"{KEY_MP_ED_BRACING_CONNECTION}{suffix}")
            if not tc_raw:
                tc_raw    = inp.get(f"{KEY_MP_ED_TOP_CHORD}{suffix}")
            if not bc_raw:
                bc_raw    = inp.get(f"{KEY_MP_ED_BOTTOM_CHORD}{suffix}")

        btype_raw = btype_raw or inp.get(KEY_MP_ED_BRACING_TYPE, "X")
        conn_raw  = conn_raw  or inp.get(KEY_MP_ED_BRACING_CONNECTION, "Bolted")
        tc_raw    = tc_raw    or inp.get(KEY_MP_ED_TOP_CHORD, "Yes")
        bc_raw    = bc_raw    or inp.get(KEY_MP_ED_BOTTOM_CHORD, "Yes")

        brace_type  = _BRACE_K if "K" in str(btype_raw or "").upper() else _BRACE_X
        connection  = str(conn_raw or "Bolted").strip()
        top_chord   = str(tc_raw  or "Yes").strip().lower() not in ("no", "false", "0")
        bot_chord   = str(bc_raw  or "Yes").strip().lower() not in ("no", "false", "0")

        horiz_proj  = self.s if brace_type == _BRACE_X else self.s / 2.0
        L_d         = math.sqrt(horiz_proj ** 2 + self.h ** 2)
        alpha_rad   = math.atan2(self.h, horiz_proj)
        cos_alpha   = math.cos(alpha_rad)

        return {
            "brace_type":  brace_type,
            "connection":  connection,
            "top_chord":   top_chord,
            "bot_chord":   bot_chord,
            "horiz_proj":  horiz_proj,
            "L_d":         L_d,
            "alpha_deg":   math.degrees(alpha_rad),
            "cos_alpha":   cos_alpha,
        }

    # =======================================================================
    # Force resolution
    # =======================================================================

    def resolve_ed_forces(self) -> dict:
        """
        Scan edge elements for each girder pair and resolve diagonal / chord
        forces from grillage ``Vz_i`` values.

        Returns
        -------
        dict — same schema as ``CrossBracingForces.get_design_forces_dict()``:
            {
                "brace_type": str,
                "top_chord":  bool,
                "bottom_chord": bool,
                "geometry":   {...},
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN":          float|None,
                        "diag_tension_gov_lc":      str|None,
                        "diag_compression_kN":      float|None,
                        "diag_compression_gov_lc":  str|None,
                        "chord_tension_kN":         float|None,
                        "chord_tension_gov_lc":     str|None,
                        "chord_compression_kN":     float|None,
                        "chord_compression_gov_lc": str|None,
                    },
                    ...
                },
            }
        """
        rd      = self.bridge.result_data
        all_lcs = [
            str(lc) for lc in rd.get("loadcases", [])
            if not str(lc).startswith("Envelope")
        ]

        # Representative config for geometry summary (use first pair)
        first_pair_id = list(self.pair_to_elements.keys())[0].replace("-", "") if self.pair_to_elements else "G1G2"
        m0 = re.match(r"G(\d+)G", first_pair_id)
        g0 = m0.group(1) if m0 else "1"
        rep_cfg = self._ed_config_for_pair(first_pair_id, g0)

        pairs_out: dict = {}

        for pair, elements in self.pair_to_elements.items():
            if not elements:
                continue

            pair_id = pair.replace("-", "")
            m = re.match(r"G(\d+)G", pair_id)
            g_idx = m.group(1) if m else "1"
            cfg = self._ed_config_for_pair(pair_id, g_idx)
            cos_alpha = cfg["cos_alpha"]
            if cos_alpha < 1e-9:
                cos_alpha = 1.0  # degenerate geometry guard

            diag_tens_max = 0.0;  diag_tens_lc  = None
            diag_comp_max = 0.0;  diag_comp_lc  = None
            chord_tens_max = 0.0; chord_tens_lc = None
            chord_comp_max = 0.0; chord_comp_lc = None

            for lc_str in all_lcs:
                forces_lc = rd.get("forces", {}).get(lc_str, {})
                for mem in elements:
                    mem_forces = forces_lc.get(str(mem))
                    if not mem_forces:
                        continue
                    v_val = mem_forces.get("Vz_i")
                    if v_val is None or abs(float(v_val)) < 1e-6:
                        v_val = mem_forces.get("Vy_i")
                    if v_val is None or abs(float(v_val)) < 1e-6:
                        v_val = mem_forces.get("Vx_i")
                    if v_val is None:
                        continue
                    vz_kn   = float(v_val) / 1000.0
                    f_diag  = vz_kn / cos_alpha
                    f_chord = vz_kn

                    if f_diag  > diag_tens_max:  diag_tens_max  = f_diag;  diag_tens_lc  = lc_str
                    if f_diag  < diag_comp_max:  diag_comp_max  = f_diag;  diag_comp_lc  = lc_str
                    if f_chord > chord_tens_max: chord_tens_max = f_chord; chord_tens_lc = lc_str
                    if f_chord < chord_comp_max: chord_comp_max = f_chord; chord_comp_lc = lc_str

            pairs_out[pair] = {
                "diag_tension_kN":          round(diag_tens_max,        3) if diag_tens_max  >  _TOL_KN else None,
                "diag_tension_gov_lc":      diag_tens_lc                   if diag_tens_max  >  _TOL_KN else None,
                "diag_compression_kN":      round(abs(diag_comp_max),   3) if diag_comp_max  < -_TOL_KN else None,
                "diag_compression_gov_lc":  diag_comp_lc                   if diag_comp_max  < -_TOL_KN else None,
                "chord_tension_kN":         round(chord_tens_max,       3) if chord_tens_max >  _TOL_KN else None,
                "chord_tension_gov_lc":     chord_tens_lc                  if chord_tens_max >  _TOL_KN else None,
                "chord_compression_kN":     round(abs(chord_comp_max),  3) if chord_comp_max < -_TOL_KN else None,
                "chord_compression_gov_lc": chord_comp_lc                  if chord_comp_max < -_TOL_KN else None,
            }

        return {
            "brace_type":   rep_cfg["brace_type"],
            "top_chord":    rep_cfg["top_chord"],
            "bottom_chord": rep_cfg["bot_chord"],
            "geometry": {
                "brace_type":        rep_cfg["brace_type"],
                "top_chord":         rep_cfg["top_chord"],
                "bottom_chord":      rep_cfg["bot_chord"],
                "girder_spacing_m":  round(self.s, 4),
                "brace_height_m":    round(self.h, 4),
                "girder_depth_m":    round(self.D, 4),
                "diagonal_length_m": round(rep_cfg["L_d"], 4),
                "horiz_proj_m":      round(rep_cfg["horiz_proj"], 4),
                "alpha_deg":         round(rep_cfg["alpha_deg"], 2),
                "cb_spacing_m":      round(self.s, 3),  # spacing == girder spacing for ED
                "depth_ratio":       self.depth_ratio,
            },
            "pairs": pairs_out,
        }

    # =======================================================================
    # Osdag design dispatch
    # =======================================================================

    def run_ed_bracing_designs(self, forces_dict: dict) -> dict:
        """
        Run parallel Osdag member designs for End Diaphragm diagonals and
        chords.  Connection type (Bolted / Welded) is read from
        ``KEY_MP_ED_BRACING_CONNECTION`` per-pair — never from the CB key.

        Parameters
        ----------
        forces_dict : dict
            Output of :meth:`resolve_ed_forces`.

        Returns
        -------
        dict — same shape as ``CrossBracingForces.run_member_designs()``:
            { "G1-G2": { "diagonal": {...}, "chord": {...} }, ... }
        """
        from osdagbridge.core.utils.connect import (
            design_pool,
            run_calculation,
            design_dict_struts_bolted,
            design_dict_tension_bolted,
            design_dict_struts_welded,
            design_dict_tension_welded,
        )

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom       = forces_dict.get("geometry", {})
        L_diag_mm  = round(geom.get("diagonal_length_m", 0) * 1000)
        L_chord_mm = round(geom.get("horiz_proj_m",      0) * 1000)

        # Build job list
        jobs: list[tuple[str, str, str, dict]] = []
        inp = self.bridge.input_dict

        for pair, vals in forces_dict["pairs"].items():
            pair_id = pair.replace("-", "")
            m = re.match(r"G(\d+)G", pair_id)
            g_idx = m.group(1) if m else "1"

            # Connection type — ED-specific key only
            conn_val = None
            for m_idx in ("M1", "M2"):
                suffix = f".{pair_id}.E{g_idx}{m_idx}"
                c = inp.get(f"{KEY_MP_ED_BRACING_CONNECTION}{suffix}")
                if c:
                    conn_val = c
                    break
            if not conn_val:
                conn_val = inp.get(KEY_MP_ED_BRACING_CONNECTION, "Bolted")

            is_welded = str(conn_val).strip() == "Welded"

            for member, L_mm, t_key, c_key in (
                ("diagonal", L_diag_mm,  "diag_tension_kN",  "diag_compression_kN"),
                ("chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
            ):
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(
                        design_dict_tension_welded if is_welded else design_dict_tension_bolted
                    )
                    d["Load.Axial"]    = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(
                        design_dict_struts_welded if is_welded else design_dict_struts_bolted
                    )
                    d["Load.Axial"]    = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        sep = "-" * 70
        n_pairs = len(forces_dict["pairs"])
        conn_label = "Welded" if any(
            str(inp.get(KEY_MP_ED_BRACING_CONNECTION, "Bolted")).strip() == "Welded"
            for _ in [None]
        ) else "Bolted/Mixed"
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM — Cross Bracing Designs  ({n_pairs} pair(s))\n"
            f"  diag L={L_diag_mm} mm  chord L={L_chord_mm} mm\n"
            f"{sep}"
        )

        cpu_count   = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))
        t0          = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
            for future, (pair, member, force_type, _) in futures.items():
                try:
                    res = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragm] SKIP {pair} {member} {force_type}: {exc}")
                    res = None
                results.setdefault(pair, {}).setdefault(member, {})[force_type] = res

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    # =======================================================================
    # Diagnostics
    # =======================================================================

    def print_ed_results(self, results: dict, forces_dict: dict) -> None:
        """Print a formatted summary of End Diaphragm design results."""
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        sep = "=" * 75
        print(f"\n{sep}")
        print(" " * 18 + "END DIAPHRAGM — CROSS BRACING DESIGN RESULTS")
        print(sep)
        for pair, members in results.items():
            print(f"  Pair : {pair}")
            for member, force_types in members.items():
                for force_type, raw in force_types.items():
                    s = _extract_osdag_summary(raw or {})
                    sec  = s.get("section",       "—")
                    cap  = s.get("capacity_kN")
                    eff  = s.get("efficiency")
                    slnd = s.get("slenderness")
                    cfg  = self._ed_config_for_pair(
                        pair.replace("-", ""),
                        re.match(r"G(\d+)G", pair.replace("-", "")).group(1)
                        if re.match(r"G(\d+)G", pair.replace("-", "")) else "1"
                    )
                    tag = cfg["connection"]
                    cap_str  = f"{cap:.1f} kN"  if cap  is not None else "—"
                    eff_str  = f"{eff:.2f}"     if eff  is not None else "—"
                    slnd_str = f"λ={slnd:.1f}"  if slnd is not None else ""
                    force_val = (forces_dict.get("pairs", {}).get(pair, {})
                                 .get(f"{member.replace('diagonal','diag').replace('chord','chord')}_{force_type}_kN"))
                    fv_str = f"{force_val:.3f} kN" if force_val is not None else "—"
                    print(
                        f"    {member:8s} [{force_type:11s} {fv_str:>10s}]"
                        f"  →  {sec}   cap={cap_str}  eff={eff_str}  {slnd_str}  {tag}"
                    )
        print(sep)
