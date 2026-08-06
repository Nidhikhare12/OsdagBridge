"""
cross_bracing_design.py

Independent module for intermediate cross bracing member design in OsdagBridge.
Supports both Bolted and Welded connection types.
"""

import copy
import json
from pathlib import Path
from typing import Any

from osdagbridge.core.utils.common import (
    KEY_MP_CB_BRACING_CONNECTION,
)
from osdagbridge.core.utils.connect import (
    design_dict_struts_bolted,
    design_dict_struts_welded,
    design_dict_tension_bolted,
    design_dict_tension_welded,
    design_pool,
    run_calculation,
)


def design_cross_bracing(
    bridge: Any,
    dev: bool = False,
    connection_type: str | None = None,
) -> dict:
    """
    Run Osdag member designs for intermediate cross-bracing members (diagonals/chords).

    Parameters
    ----------
    bridge : PlateGirderBridge
        The bridge instance containing grillage results and input parameters.
    dev : bool
        If True, dump forces_dict to tools/crossbracing_forces_dict.json.
    connection_type : str | None
        Optional override for connection type ("Bolted" or "Welded").

    Returns
    -------
    dict
        Nested dictionary keyed by pair -> member -> force_type -> Osdag result.
    """
    if not hasattr(bridge, "cross_bracing") or bridge.cross_bracing is None:
        return {}

    forces_dict = bridge.cross_bracing.get_design_forces_dict()
    if not forces_dict or not forces_dict.get("pairs"):
        return {}

    if dev:
        out = Path(__file__).parents[5] / "tools" / "crossbracing_forces_dict.json"
        try:
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[CrossBracing] dev dump → {out}")
        except Exception:
            pass

    geom = forces_dict.get("geometry", {})
    L_diag_mm = round(geom.get("diagonal_length_m", 0) * 1000)
    L_chord_mm = round(geom.get("horiz_proj_m", 0) * 1000)

    jobs: list[tuple[str, str, str, dict]] = []

    for pair, vals in forces_dict["pairs"].items():
        pair_id = pair.replace("-", "")
        conn_key = f"{KEY_MP_CB_BRACING_CONNECTION}.{pair_id}"
        conn_type = str(connection_type or bridge.input_dict.get(conn_key) or bridge.input_dict.get(KEY_MP_CB_BRACING_CONNECTION) or "Bolted").strip()

        is_welded = (conn_type.lower() == "welded")
        t_base_dict = design_dict_tension_welded if is_welded else design_dict_tension_bolted
        c_base_dict = design_dict_struts_welded if is_welded else design_dict_struts_bolted

        for member, L_mm, t_key, c_key in (
            ("diagonal", L_diag_mm, "diag_tension_kN", "diag_compression_kN"),
            ("chord", L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
        ):
            if vals.get(t_key) is not None:
                d = copy.deepcopy(t_base_dict)
                d["Load.Axial"] = str(float(vals[t_key]))
                d["Member.Length"] = str(L_mm)
                jobs.append((pair, member, "tension", d))

            if vals.get(c_key) is not None:
                d = copy.deepcopy(c_base_dict)
                d["Load.Axial"] = str(float(vals[c_key]))
                d["Member.Length"] = str(L_mm)
                jobs.append((pair, member, "compression", d))

    pair_designs: dict[str, dict] = {}
    if not jobs:
        return pair_designs

    cpu_count = __import__("os").cpu_count() or 4
    max_workers = min(cpu_count, len(jobs))
    with design_pool(max_workers) as executor:
        futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
        for future, (p, member, force_type, _) in futures.items():
            try:
                res = future.result()
            except Exception as exc:
                print(f"  [CrossBracing] SKIP {p} {member} {force_type}: {exc}")
                res = None
            pair_designs.setdefault(p, {}).setdefault(member, {})[force_type] = res

    return pair_designs
