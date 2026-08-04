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

        # Superclass __init__ calls self._identify_configuration() and self._init_geometry()
        super().__init__(
            bridge=bridge,
            brace_type=brace_type,
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
        brace_type:   Optional[str],
        top_chord:    Optional[bool],
        bottom_chord: Optional[bool],
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

        # Connection Type: Bolted / Welded
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

        Supports both Bolted and Welded connections for Cross Bracing, as well
        as stub calls for Rolled and Welded beam types.
        """
        if self.ed_type == "Rolled Beam":
            return self.run_rolled_member_design(forces_dict, dev)
        elif self.ed_type == "Welded Beam":
            return self.run_welded_member_design(forces_dict, dev)

        # Default: "Cross Bracing" type
        if dev:
            out = Path(__file__).parents[5] / "tools" / "enddiaphragm_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[EndDiaphragm] dev dump → {out}")

        from osdagbridge.core.utils.connect import (
            design_dict_struts_bolted,
            design_dict_struts_welded,
            design_dict_tension_bolted,
            design_dict_tension_welded,
        )

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom       = forces_dict.get("geometry", {})
        L_diag_mm  = round(geom.get("diagonal_length_m", 0) * 1000)
        L_chord_mm = round(geom.get("horiz_proj_m",      0) * 1000)

        is_welded = (self.connection_type.lower() == "welded")
        t_dict = design_dict_tension_welded if is_welded else design_dict_tension_bolted
        c_dict = design_dict_struts_welded if is_welded else design_dict_struts_bolted

        jobs: list[tuple[str, str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            for member, L_mm, t_key, c_key in (
                ("diagonal", L_diag_mm, "diag_tension_kN",  "diag_compression_kN"),
                ("chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
            ):
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(t_dict)
                    d["Load.Axial"]    = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(c_dict)
                    d["Load.Axial"]    = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        conn_str = "WELDED" if is_welded else "BOLTED"
        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  END DIAPHRAGM DESIGNS ({conn_str})  ({len(forces_dict['pairs'])} pair(s))"
            f"  diag L={L_diag_mm} mm  chord L={L_chord_mm} mm\n"
            f"{sep}"
        )
        from osdagbridge.core.utils.connect import design_pool, run_calculation

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
    # STUB METHODS FOR ROLLED & WELDED BEAM TYPES (To be implemented in later task)
    # =======================================================================

    def run_rolled_member_design(self, forces_dict: dict, dev: bool = False) -> dict:
        raise NotImplementedError(
            "Rolled/Welded end diaphragm force extraction — implemented in a later task"
        )

    def run_welded_member_design(self, forces_dict: dict, dev: bool = False) -> dict:
        raise NotImplementedError(
            "Rolled/Welded end diaphragm force extraction — implemented in a later task"
        )
