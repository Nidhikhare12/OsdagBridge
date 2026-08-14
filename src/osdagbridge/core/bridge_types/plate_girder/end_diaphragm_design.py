"""
EndDiaphragmDesign
------------------
Force analysis and member design for bridge End Diaphragms.

Supported End Diaphragm Types:
  1. Cross Bracing (X-type / K-type with Bolted or Welded connection)
  2. Rolled Beam (Transverse rolled section designed with Flexure module)
  3. Welded Beam (Transverse plate girder section designed with PlateGirder module)
"""

from __future__ import annotations

import copy
import json
import math
import time
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from osdagbridge.core.bridge_types.plate_girder.cross_bracing_design import (
    BRACE_K,
    BRACE_X,
    CrossBracingDesign,
)
from osdagbridge.core.utils.common import (
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_WEB_THICKNESS,
)


class EndDiaphragmDesign(CrossBracingDesign):
    """
    Step-wise force analysis and member design for End Diaphragms.

    Inherits X/K cross-bracing geometry and force-resolution math from
    CrossBracingDesign for the "Cross Bracing" End Diaphragm type, while using
    End-Diaphragm-specific UI keys and supporting both Bolted and Welded
    member connection types.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge (design() already called).
    ed_type : str or None
        'Cross Bracing', 'Rolled Beam', or 'Welded Beam'. None → read from
        additional_inputs [KEY_MP_ED_TYPE]; default 'Cross Bracing'.
    brace_type : str or None
        'X' or 'K'. None → read from additional_inputs [KEY_MP_ED_BRACING_TYPE].
    connection_type : str or None
        'Bolted' or 'Welded'. None → read from additional_inputs
        [KEY_MP_ED_BRACING_CONNECTION]; default 'Bolted'.
    top_chord : bool or None
        True if top chord present. None → read from [KEY_MP_ED_TOP_CHORD].
    bottom_chord : bool or None
        True if bottom chord present. None → read from [KEY_MP_ED_BOTTOM_CHORD].
    cb_spacing : float or None
        Panel spacing (m). None → read from inputs.
    depth_ratio : float
        Brace clear height = D × depth_ratio. Default 0.85.
    include_edge_beams : bool
        Include EB1/EB2 edge beams in pair scanning. Default False.
    """

    def __init__(
        self,
        bridge,
        ed_type:         Optional[str]   = None,
        brace_type:      Optional[str]   = None,
        connection_type: Optional[str]   = None,
        top_chord:       Optional[bool]  = None,
        bottom_chord:    Optional[bool]  = None,
        cb_spacing:      Optional[float] = None,
        depth_ratio:     float = 0.85,
        include_edge_beams: bool = False,
    ):
        self.connection_type: str = "Bolted"
        self.ed_type: str = "Cross Bracing"

        # Superclass __init__ calls self._identify_configuration() and self._init_geometry().
        # We pass connection_type=None so the parent passes it through to our override,
        # which reads KEY_MP_ED_BRACING_CONNECTION instead.
        super().__init__(
            bridge=bridge,
            brace_type=brace_type,
            connection_type=None,       # overridden: we read KEY_MP_ED_BRACING_CONNECTION
            top_chord=top_chord,
            bottom_chord=bottom_chord,
            cb_spacing=cb_spacing,
            depth_ratio=depth_ratio,
            include_edge_beams=include_edge_beams,
        )

        # Re-run _identify_configuration with extra ED parameters if passed explicitly
        if ed_type is not None or connection_type is not None:
            self._identify_configuration_ed(ed_type, connection_type)

    def _identify_configuration(
        self,
        brace_type:      Optional[str],
        connection_type: Optional[str],   # ignored — we read KEY_MP_ED_BRACING_CONNECTION
        top_chord:       Optional[bool],
        bottom_chord:    Optional[bool],
    ) -> None:
        """Read End-Diaphragm-specific keys from bridge.additional_inputs."""
        ai = getattr(self.bridge, "additional_inputs", {})

        # ED Type
        raw_ed_type = ai.get(KEY_MP_ED_TYPE) or "Cross Bracing"
        self.ed_type = str(raw_ed_type).strip()

        # Bracing Type
        if brace_type is not None:
            raw_btype = str(brace_type).strip().upper()
        else:
            val = ai.get(KEY_MP_ED_BRACING_TYPE) or "X"
            raw_btype = str(val).strip().upper()

        if "K" in raw_btype:
            self.brace_type = BRACE_K
        else:
            self.brace_type = BRACE_X

        # Connection Type: Bolted / Welded — always from ED-specific key
        raw_conn = ai.get(KEY_MP_ED_BRACING_CONNECTION) or "Bolted"
        self.connection_type = str(raw_conn).strip()

        # Chords
        if top_chord is not None:
            self.top_chord = bool(top_chord)
        else:
            val = ai.get(KEY_MP_ED_TOP_CHORD)
            self.top_chord = str(val).strip().lower() not in ("no", "false", "0")

        if bottom_chord is not None:
            self.bottom_chord = bool(bottom_chord)
        else:
            val = ai.get(KEY_MP_ED_BOTTOM_CHORD)
            self.bottom_chord = str(val).strip().lower() not in ("no", "false", "0")

    def _identify_configuration_ed(
        self,
        ed_type:         Optional[str],
        connection_type: Optional[str],
    ) -> None:
        if ed_type is not None:
            self.ed_type = str(ed_type).strip()
        if connection_type is not None:
            self.connection_type = str(connection_type).strip()

    # =======================================================================
    # MEMBER DESIGNS — Supports both Bolted and Welded connections
    # =======================================================================

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        """
        Run member designs for End Diaphragm.

        Routes to the appropriate design path based on ed_type:
          - 'Rolled Beam'  → run_rolled_member_design() (stub)
          - 'Welded Beam'  → run_welded_member_design() (stub)
          - 'Cross Bracing' → delegates to CrossBracingDesign.run_member_designs(),
            which already branches on self.connection_type (Bolted / Welded).
            The dev-dump filename is overridden here before delegating.
        """
        if self.ed_type == "Rolled Beam":
            return self.run_rolled_member_design(forces_dict, dev)
        elif self.ed_type == "Welded Beam":
            return self.run_welded_member_design(forces_dict, dev)

        # Cross Bracing type — write ED-specific dev dump then delegate to parent.
        if dev:
            out = Path(__file__).parents[5] / "tools" / "enddiaphragm_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[EndDiaphragm] dev dump → {out}")
            # Suppress duplicate dev dump in parent by passing dev=False.
            return super().run_member_designs(forces_dict, dev=False)

        return super().run_member_designs(forces_dict, dev=False)

    # =======================================================================
    # FORCE EXTRACTION & MEMBER DESIGNS FOR ROLLED & WELDED BEAM TYPES
    # =======================================================================

    def compute_ed_beam_forces(self) -> dict[str, dict[str, float | str]]:
        """
        Extract governing shear (Vy in kN) and bending moment (Mz in kNm)
        for end diaphragm members at the bridge supports (x ≈ min_x or x ≈ max_x),
        grouped by girder pair.

        Returns
        -------
        dict ::
            {
                "G1-G2": {
                    "max_Vy_kN": float,
                    "max_Mz_kNm": float,
                    "gov_lc_vy": str,
                    "gov_lc_mz": str,
                },
                ...
            }
        """
        chain_stations = self._build_chain_map()
        if not chain_stations:
            return {}

        # Filter end diaphragm chains at start and end supports (min X and max X)
        x_coords = [st["start_coords"][0] for st in chain_stations if st.get("start_coords")]
        if not x_coords:
            return {}

        min_x = min(x_coords)
        max_x = max(x_coords)
        _tol = 1e-3

        ed_stations = [
            st for st in chain_stations
            if st.get("start_coords") and (
                abs(st["start_coords"][0] - min_x) < _tol or
                abs(st["start_coords"][0] - max_x) < _tol
            )
        ]

        if not ed_stations:
            ed_stations = chain_stations

        all_lcs = [
            lc for lc in self.bridge.result_data.get("loadcases", [])
            if not str(lc).startswith("Envelope")
        ]

        pairs_forces: dict[str, dict] = {}

        for st in ed_stations:
            pair = f"{st['left_girder']}-{st['right_girder']}"
            m_id = st["first_member"]
            p_data = pairs_forces.setdefault(pair, {
                "max_Vy_kN": 0.0,
                "max_Mz_kNm": 0.0,
                "gov_lc_vy": "",
                "gov_lc_mz": "",
            })

            for lc in all_lcs:
                lc_str = str(lc)
                try:
                    f = self.bridge.result_data["forces"][lc_str][m_id]
                except (KeyError, TypeError):
                    continue

                vy_i = abs(float(f.get("Vy_i", 0.0))) / 1e3
                vy_j = abs(float(f.get("Vy_j", 0.0))) / 1e3
                vy_max = max(vy_i, vy_j)

                mz_i = abs(float(f.get("Mz_i", 0.0))) / 1e3
                mz_j = abs(float(f.get("Mz_j", 0.0))) / 1e3

                # NOTE ON Mz EXTRACTION:
                # Each end-diaphragm member between adjacent girders is discretized as a
                # single finite element in the grillage mesh. The FE nodal forces Mz_i and
                # Mz_j are evaluated at the girder support nodes, where bending moment is
                # naturally near-zero (~0 kNm).
                # To capture the governing peak mid-span bending moment demand for a
                # simply-supported transverse beam with uniform/symmetric load distribution
                # (as assumed by Osdag's "Uniform Loading with pinned-pinned support" shape),
                # M_max is computed analytically from statics: M_midspan = (V_max * L) / 4.
                L_m = float(self.s)
                mz_analytical = (vy_max * L_m) / 4.0
                mz_max = max(mz_i, mz_j, mz_analytical)

                if vy_max > p_data["max_Vy_kN"]:
                    p_data["max_Vy_kN"] = round(vy_max, 4)
                    p_data["gov_lc_vy"] = lc_str

                if mz_max > p_data["max_Mz_kNm"]:
                    p_data["max_Mz_kNm"] = round(mz_max, 4)
                    p_data["gov_lc_mz"] = lc_str

        return pairs_forces

    def run_rolled_member_design(self, forces_dict: dict, dev: bool = False) -> dict:
        """
        Run Osdag Flexure (Rolled Beam) member designs for End Diaphragms.
        """
        if dev:
            out = Path(__file__).parents[5] / "tools" / "enddiaphragm_rolled_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[EndDiaphragm Rolled] dev dump → {out}")

        from osdagbridge.core.utils.connect import (
            design_dict_end_diaphragm_rolled,
            design_pool,
            run_calculation,
        )

        ed_forces = self.compute_ed_beam_forces()
        if not ed_forces:
            return {}

        L_mm = round(self.s * 1000)

        jobs: list[tuple[str, dict]] = []
        for pair, pdata in ed_forces.items():
            vy = max(float(pdata.get("max_Vy_kN", 0.0)), 1.0)
            mz = max(float(pdata.get("max_Mz_kNm", 0.0)), 1.0)

            d = copy.deepcopy(design_dict_end_diaphragm_rolled)
            d["Member.Length"] = str(int(L_mm))
            d["Load.Moment"]   = str(round(mz, 3))
            d["Load.Shear"]    = str(round(vy, 3))

            jobs.append((pair, d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM ROLLED BEAM DESIGNS  ({len(jobs)} pair(s))"
            f"  L={L_mm} mm\n"
            f"{sep}"
        )

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))

        t0 = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(run_calculation, job[1]): job[0]
                for job in jobs
            }
            for future, pair in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragm Rolled] SKIP {pair}: {exc}")
                    result = None
                results.setdefault(pair, {})["flexure"] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    def run_welded_member_design(self, forces_dict: dict, dev: bool = False) -> dict:
        """
        Run Osdag PlateGirder (Welded Beam) member designs for End Diaphragms.
        """
        if dev:
            out = Path(__file__).parents[5] / "tools" / "enddiaphragm_welded_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[EndDiaphragm Welded] dev dump → {out}")

        from osdagbridge.core.utils.connect import (
            design_dict_end_diaphragm_welded,
            design_pool,
            run_calculation,
        )

        ed_forces = self.compute_ed_beam_forces()
        if not ed_forces:
            return {}

        L_mm = round(self.s * 1000)

        jobs: list[tuple[str, dict]] = []
        for pair, pdata in ed_forces.items():
            vy = max(float(pdata.get("max_Vy_kN", 0.0)), 1.0)
            mz = max(float(pdata.get("max_Mz_kNm", 0.0)), 1.0)

            d = copy.deepcopy(design_dict_end_diaphragm_welded)
            d["Member.Length"] = str(int(L_mm))
            d["Load.Moment"]   = str(round(mz, 3))
            d["Load.Shear"]    = str(round(vy, 3))

            jobs.append((pair, d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM WELDED BEAM DESIGNS  ({len(jobs)} pair(s))"
            f"  L={L_mm} mm\n"
            f"{sep}"
        )

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))

        t0 = time.perf_counter()
        results: dict = {}

        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(run_calculation, job[1]): job[0]
                for job in jobs
            }
            for future, pair in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [EndDiaphragm Welded] SKIP {pair}: {exc}")
                    result = None
                results.setdefault(pair, {})["flexure"] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results
