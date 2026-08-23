"""
End diaphragm — Rolled Beam simply-supported Osdag design.

Force envelope from end-edge members; Flexure module via connect.py.
Section property population stays in end_diaphragm_design.py.
"""

from __future__ import annotations

import copy
from typing import Any


def _max_abs_components(member_forces: dict, *keys: str) -> float:
    """Largest |value| among present force keys; missing keys ignored."""
    best = 0.0
    for key in keys:
        raw = member_forces.get(key)
        if raw is None:
            continue
        try:
            best = max(best, abs(float(raw)))
        except (TypeError, ValueError):
            continue
    return best


def envelope_end_diaphragm_vy_mz(
    result_data: dict,
    elements: list[str],
) -> tuple[float, float]:
    """
    Governing design shear (kN) and moment (kNm) on end-diaphragm edge elements.

    Assignment maps these into Osdag as Vy / Mz. On transverse ED members the
    grillage local axes often put the useful shear in Vz and flexure in My
    (same pattern as ED Cross Bracing, which already reads Vz). So per end we
    take::

        shear  = max(|Vy_i|, |Vy_j|, |Vz_i|, |Vz_j|)
        moment = max(|Mz_i|, |Mz_j|, |My_i|, |My_j|)

    Across applicable cases/elements: maximum of those values.
    Skips load cases whose name starts with "Envelope".
    Raw forces in result_data are N / N·m; returns kN / kNm (/1000).
    """
    if not result_data or not elements:
        return 0.0, 0.0

    forces = result_data.get("forces") or {}
    loadcases = result_data.get("loadcases") or []

    shear_max_n = 0.0
    moment_max_nm = 0.0

    for lc in loadcases:
        lc_str = str(lc)
        if lc_str.startswith("Envelope"):
            continue
        lc_forces = forces.get(lc_str)
        if not lc_forces:
            continue
        for m in elements:
            member_forces = lc_forces.get(str(m))
            if not member_forces:
                continue
            shear_cand = _max_abs_components(
                member_forces, "Vy_i", "Vy_j", "Vz_i", "Vz_j"
            )
            moment_cand = _max_abs_components(
                member_forces, "Mz_i", "Mz_j", "My_i", "My_j"
            )
            if shear_cand > shear_max_n:
                shear_max_n = shear_cand
            if moment_cand > moment_max_nm:
                moment_max_nm = moment_cand

    return round(shear_max_n / 1000.0, 3), round(moment_max_nm / 1000.0, 3)


def resolve_ed_flexure_demands(
    vy_kN: float,
    mz_kNm: float,
    span_m: float,
) -> tuple[float, float]:
    """
    Ensure Osdag flexure/plate-girder jobs get a usable moment.

    If analysis moment components are all ~0 but shear and span exist, estimate
    mid-span moment for a simply-supported member under UDL-equivalent demand:
    M = V·L/4. Live ED runs have shown Vy (or Vz) with Mz=My=0 on edge members.
    """
    shear = float(vy_kN or 0.0)
    moment = float(mz_kNm or 0.0)
    span = float(span_m or 0.0)
    if moment > 0.0 or shear <= 0.0 or span <= 0.0:
        return shear, moment
    moment_est = round(shear * span / 4.0, 3)
    print(
        f"  [EndDiaphragm] analysis My/Mz~0 with V={shear} kN; "
        f"using SS estimate M=V*L/4={moment_est} kNm (L={span} m)"
    )
    return shear, moment_est


def run_simply_supported_design(
    *,
    vy_kN: float,
    mz_kNm: float,
    span_m: float,
    section_designation: str,
) -> dict[str, Any] | None:
    """
    Run Osdag Flexure (simply supported) for one ED Rolled Beam.

    Returns the Osdag output dict, or None on skip/failure.
    Moment is required; shear may be 0 (Osdag flexure accepts it).
    """
    if not section_designation:
        return None
    if mz_kNm <= 0.0 or span_m <= 0.0:
        print(
            f"  [EndDiaphragm Rolled] SKIP simply-supported design: "
            f"Vy={vy_kN}, Mz={mz_kNm}, L={span_m}"
        )
        return None

    from osdagbridge.core.utils.connect import (
        design_dict_flexure_simply_supported,
        design_pool,
        run_calculation,
    )

    d = copy.deepcopy(design_dict_flexure_simply_supported)
    d["Member.Designation"] = [str(section_designation)]
    d["Member.Length"] = str(span_m)
    d["Load.Shear"] = str(float(max(vy_kN, 0.0)))
    d["Load.Moment"] = str(float(mz_kNm))

    try:
        with design_pool(1) as executor:
            future = executor.submit(run_calculation, d)
            return future.result()
    except Exception as exc:
        print(f"  [EndDiaphragm Rolled] SKIP simply-supported design: {exc}")
        return None
