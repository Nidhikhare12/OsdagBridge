"""
End diaphragm — Welded Beam plate-girder Osdag design.

Reuses Slice 4 Vy/Mz envelope; PlateGirderWelded via connect.py.
Section property population stays in end_diaphragm_design.py.
"""

from __future__ import annotations

import copy
from typing import Any


def run_plate_girder_design(
    *,
    vy_kN: float,
    mz_kNm: float,
    span_m: float,
    support_width_mm: float,
    total_depth_mm: float,
    web_thickness_mm: float,
    top_flange_width_mm: float,
    top_flange_thickness_mm: float,
    bottom_flange_width_mm: float,
    bottom_flange_thickness_mm: float,
) -> dict[str, Any] | None:
    """
    Run Osdag PLATE GIRDER (Customized) for one ED Welded Beam.

    Member.Length is span_m * 1000 (mm). Returns Osdag output dict, or None on skip/failure.
    """
    # Moment is required; shear may be 0 (live Osdag plate-girder accepts it).
    if mz_kNm <= 0.0 or span_m <= 0.0:
        print(
            f"  [EndDiaphragm Welded] SKIP plate-girder design: "
            f"Vy={vy_kN}, Mz={mz_kNm}, L={span_m}"
        )
        return None
    if support_width_mm <= 0.0:
        print(
            f"  [EndDiaphragm Welded] SKIP plate-girder design: "
            f"Support.Width (bearing length) unavailable or <= 0"
        )
        return None
    if (
        total_depth_mm <= 0.0
        or web_thickness_mm <= 0.0
        or top_flange_width_mm <= 0.0
        or top_flange_thickness_mm <= 0.0
        or bottom_flange_width_mm <= 0.0
        or bottom_flange_thickness_mm <= 0.0
    ):
        print(
            f"  [EndDiaphragm Welded] SKIP plate-girder design: incomplete plate dimensions"
        )
        return None

    from osdagbridge.core.utils.connect import (
        design_dict_plate_girder_welded,
        design_pool,
        run_calculation,
    )

    length_mm = round(float(span_m) * 1000.0, 6)

    d = copy.deepcopy(design_dict_plate_girder_welded)
    d["Total.Design_Type"] = "Customized"
    d["Total.Depth"] = str(float(total_depth_mm))
    d["Web.Thickness"] = str(float(web_thickness_mm))
    d["Topflange.Width"] = str(float(top_flange_width_mm))
    d["TopFlange.Thickness"] = str(float(top_flange_thickness_mm))
    d["Bottomflange.Width"] = str(float(bottom_flange_width_mm))
    d["BottomFlange.Thickness"] = str(float(bottom_flange_thickness_mm))
    d["Member.Length"] = str(length_mm)
    d["Support.Width"] = str(float(support_width_mm))
    d["Load.Shear"] = str(float(max(vy_kN, 0.0)))
    d["Load.Moment"] = str(float(mz_kNm))

    try:
        with design_pool(1) as executor:
            future = executor.submit(run_calculation, d)
            return future.result()
    except Exception as exc:
        print(f"  [EndDiaphragm Welded] SKIP plate-girder design: {exc}")
        return None
