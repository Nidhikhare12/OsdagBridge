"""
End diaphragm — Rolled Beam simply-supported Osdag design.

Force envelope from end-edge members; Flexure module via connect.py.
Section property population stays in end_diaphragm_design.py.
"""

from __future__ import annotations

import copy
from typing import Any


def envelope_end_diaphragm_vy_mz(
    result_data: dict,
    elements: list[str],
) -> tuple[float, float]:
    """
    Governing |Vy| (kN) and |Mz| (kNm) on end-diaphragm edge elements.

    Per load case / element: max(|Vy_i|, |Vy_j|) and max(|Mz_i|, |Mz_j|).
    Across applicable cases/elements: maximum of those values.
    Skips load cases whose name starts with "Envelope".
    Raw forces in result_data are N / N·m; returns kN / kNm (/1000).
    """
    if not result_data or not elements:
        return 0.0, 0.0

    forces = result_data.get("forces") or {}
    loadcases = result_data.get("loadcases") or []

    vy_max_n = 0.0
    mz_max_nm = 0.0

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
            try:
                vy_i = member_forces.get("Vy_i")
                vy_j = member_forces.get("Vy_j")
                mz_i = member_forces.get("Mz_i")
                mz_j = member_forces.get("Mz_j")
                vy_cand = max(
                    abs(float(vy_i)) if vy_i is not None else 0.0,
                    abs(float(vy_j)) if vy_j is not None else 0.0,
                )
                mz_cand = max(
                    abs(float(mz_i)) if mz_i is not None else 0.0,
                    abs(float(mz_j)) if mz_j is not None else 0.0,
                )
            except (TypeError, ValueError):
                continue
            if vy_cand > vy_max_n:
                vy_max_n = vy_cand
            if mz_cand > mz_max_nm:
                mz_max_nm = mz_cand

    return round(vy_max_n / 1000.0, 3), round(mz_max_nm / 1000.0, 3)


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
    """
    if not section_designation:
        return None
    if vy_kN <= 0.0 or mz_kNm <= 0.0 or span_m <= 0.0:
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
    d["Load.Shear"] = str(float(vy_kN))
    d["Load.Moment"] = str(float(mz_kNm))

    try:
        with design_pool(1) as executor:
            future = executor.submit(run_calculation, d)
            return future.result()
    except Exception as exc:
        print(f"  [EndDiaphragm Rolled] SKIP simply-supported design: {exc}")
        return None
