"""
Intermediate cross-bracing member design (Osdag jobs).

Force evaluation stays in crossbracingforces.CrossBracingForces.
This module turns a forces_dict + input_dict into Bolted/Welded
Osdag design jobs and nested results.
"""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path

from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION

_DEFAULT_CONNECTION = "Bolted"
_VALID_CONNECTIONS = frozenset({"Bolted", "Welded"})


def _parse_forces_pair(forces_pair: str) -> tuple[str, str] | None:
    """Return the input pair and left-girder index for ``G{i}-G{j}``."""
    parts = str(forces_pair or "").strip().split("-", 1)
    if len(parts) != 2:
        return None

    left, right = (part.strip() for part in parts)
    if not (left.startswith("G") and right.startswith("G")):
        return None
    if not (left[1:].isdigit() and right[1:].isdigit()):
        return None

    return f"{left}{right}", left[1:]


def _normalize_connection(value) -> str:
    """Return a supported connection name, defaulting invalid values to Bolted."""
    text = str(value or "").strip().lower()
    for connection in _VALID_CONNECTIONS:
        if text == connection.lower():
            return connection
    return _DEFAULT_CONNECTION


def _resolve_cb_bracing_connection(
    input_data: dict | None,
    forces_pair: str,
) -> str:
    """Resolve the per-pair intermediate cross-bracing connection choice."""
    if not input_data:
        return _DEFAULT_CONNECTION

    parsed_pair = _parse_forces_pair(forces_pair)
    if parsed_pair is None:
        return _normalize_connection(input_data.get(KEY_MP_CB_BRACING_CONNECTION))

    input_pair, left_idx = parsed_pair
    prefix = f"{KEY_MP_CB_BRACING_CONNECTION}.{input_pair}."
    representative_key = f"{prefix}B{left_idx}M1"
    representative_value = input_data.get(representative_key)
    if representative_value not in (None, "", [], {}):
        return _normalize_connection(representative_value)

    for key, value in input_data.items():
        if key.startswith(prefix) and value not in (None, "", [], {}):
            return _normalize_connection(value)

    return _normalize_connection(input_data.get(KEY_MP_CB_BRACING_CONNECTION))


def _connection_for_pair(pair: str, input_dict: dict | None = None) -> str:
    """Return this intermediate girder pair's Bolted/Welded choice."""
    return _resolve_cb_bracing_connection(input_dict, pair)


def run_member_designs(
    forces_dict: dict,
    input_dict: dict | None = None,
    dev: bool = False,
) -> dict:
    """
    Run Osdag member designs for diagonals and chords.

    Tension and compression are designed separately — a member that sees both
    must satisfy both checks independently. Section selection is left to the user
    since sections cannot be compared programmatically.

    Parameters
    ----------
    forces_dict : dict
        Output of CrossBracingForces.get_design_forces_dict().
    input_dict : dict, optional
        Bridge input dictionary used to resolve Bolted/Welded per pair.
    dev : bool
        If True, dump forces_dict as JSON to tools/crossbracing_forces_dict.json.

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
        out = Path(__file__).parents[5] / "tools" / "crossbracing_forces_dict.json"
        out.write_text(json.dumps(forces_dict, indent=2))
        print(f"[CrossBracing] dev dump → {out}")

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

    # Build a flat job list so all designs run in one parallel batch.
    # Each job tracks (pair, member_type, force_type) for reassembly.
    jobs: list[tuple[str, str, str, dict]] = []

    for pair, vals in forces_dict["pairs"].items():
        connection = _connection_for_pair(pair, input_dict=input_dict)
        if connection == "Welded":
            tension_template = design_dict_tension_welded
            strut_template = design_dict_struts_welded
        else:
            tension_template = design_dict_tension_bolted
            strut_template = design_dict_struts_bolted

        for member, L_mm, t_key, c_key in (
            ("diagonal", L_diag_mm, "diag_tension_kN",  "diag_compression_kN"),
            ("chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
        ):
            if vals.get(t_key) is not None:
                d = copy.deepcopy(tension_template)
                d["Load.Axial"]    = str(float(vals[t_key]))
                d["Member.Length"] = str(L_mm)
                jobs.append((pair, member, "tension", d))

            if vals.get(c_key) is not None:
                d = copy.deepcopy(strut_template)
                d["Load.Axial"]    = str(float(vals[c_key]))
                d["Member.Length"] = str(L_mm)
                jobs.append((pair, member, "compression", d))

    if not jobs:
        return {}

    sep = "-" * 60
    print(
        f"\n{sep}\n"
        f"  CROSS BRACING DESIGNS  ({len(forces_dict['pairs'])} pair(s))"
        f"  diag L={L_diag_mm} mm  chord L={L_chord_mm} mm\n"
        f"{sep}"
    )
    from osdagbridge.core.utils.connect import design_pool, run_calculation

    cpu_count = __import__("os").cpu_count() or 4
    max_workers = min(cpu_count, len(jobs))

    t0 = time.perf_counter()
    results: dict = {}

    # spawn-context pool: forking under the design worker thread deadlocks (see design_pool).
    with design_pool(max_workers) as executor:
        futures = {
            executor.submit(run_calculation, j[3]): j
            for j in jobs
        }
        for future, (pair, member, force_type, _) in futures.items():
            try:
                result = future.result()
            except Exception as exc:
                print(f"  [CrossBracing] SKIP {pair} {member} {force_type}: {exc}")
                result = None
            results.setdefault(pair, {}).setdefault(member, {})[force_type] = result

    print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
    return results
