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

    plate_dims = {
        "total_depth_mm": total_depth_mm,
        "web_thickness_mm": web_thickness_mm,
        "top_flange_width_mm": top_flange_width_mm,
        "top_flange_thickness_mm": top_flange_thickness_mm,
        "bottom_flange_width_mm": bottom_flange_width_mm,
        "bottom_flange_thickness_mm": bottom_flange_thickness_mm,
    }
    missing = [name for name, val in plate_dims.items() if float(val or 0.0) <= 0.0]
    if missing:
        print(
            f"  [EndDiaphragm Welded] SKIP plate-girder design: "
            f"incomplete plate dimensions ({', '.join(missing)})"
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


def resolve_welded_plate_dims_mm(
    input_dict: dict | None,
    member_suffix: str = "",
) -> dict[str, float]:
    """
    Resolve ED Welded Beam plate sizes (mm).

    Prefers per-pair ED fields; if blank, falls back to main girder plate
    sizes (stored in metres) so design can proceed when ED plates inherit
    the girder section.
    """
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
        resolve_girder_value,
    )
    from osdagbridge.core.utils.common import (
        KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
        KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
        KEY_MP_ED_TOP_FLANGE_THICKNESS,
        KEY_MP_ED_TOP_FLANGE_WIDTH,
        KEY_MP_ED_TOTAL_DEPTH,
        KEY_MP_ED_WEB_THICKNESS,
        KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
        KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
        KEY_MP_GIRDER_DEPTH,
        KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
        KEY_MP_GIRDER_WEB_THICKNESS,
    )

    inp = input_dict or {}

    def _ed_f(key: str) -> float:
        for k in (f"{key}{member_suffix}", key):
            raw = inp.get(k)
            if raw in (None, "", [], {}):
                continue
            try:
                return float(raw)
            except (TypeError, ValueError):
                continue
        return 0.0

    def _girder_mm(key: str) -> float:
        try:
            raw = resolve_girder_value(inp, key)
        except KeyError:
            return 0.0
        if raw in (None, "", [], {}, "All"):
            return 0.0
        try:
            return float(raw) * 1000.0
        except (TypeError, ValueError):
            return 0.0

    depth = _ed_f(KEY_MP_ED_TOTAL_DEPTH)
    web_t = _ed_f(KEY_MP_ED_WEB_THICKNESS)
    top_w = _ed_f(KEY_MP_ED_TOP_FLANGE_WIDTH)
    top_t = _ed_f(KEY_MP_ED_TOP_FLANGE_THICKNESS)
    bot_w = _ed_f(KEY_MP_ED_BOTTOM_FLANGE_WIDTH)
    bot_t = _ed_f(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS)

    if min(depth, web_t, top_w, top_t, bot_w, bot_t) <= 0.0:
        g_depth = _girder_mm(KEY_MP_GIRDER_DEPTH)
        g_web = _girder_mm(KEY_MP_GIRDER_WEB_THICKNESS)
        g_top_w = _girder_mm(KEY_MP_GIRDER_TOP_FLANGE_WIDTH)
        g_top_t = _girder_mm(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        g_bot_w = _girder_mm(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)
        g_bot_t = _girder_mm(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS)
        if min(g_depth, g_web, g_top_w, g_top_t, g_bot_w, g_bot_t) > 0.0:
            if depth <= 0.0:
                depth = g_depth
            if web_t <= 0.0:
                web_t = g_web
            if top_w <= 0.0:
                top_w = g_top_w
            if top_t <= 0.0:
                top_t = g_top_t
            if bot_w <= 0.0:
                bot_w = g_bot_w
            if bot_t <= 0.0:
                bot_t = g_bot_t
            print(
                "  [EndDiaphragm Welded] using girder plate sizes for "
                f"d={depth:.1f}, tw={web_t:.1f}, bf={top_w:.1f}/{bot_w:.1f}, "
                f"tf={top_t:.1f}/{bot_t:.1f} mm"
            )

    return {
        "total_depth_mm": depth,
        "web_thickness_mm": web_t,
        "top_flange_width_mm": top_w,
        "top_flange_thickness_mm": top_t,
        "bottom_flange_width_mm": bot_w,
        "bottom_flange_thickness_mm": bot_t,
    }
