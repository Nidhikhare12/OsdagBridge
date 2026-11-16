"""Extraction and normalization of design check utilization ratios (UR = Demand / Capacity)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from osdagbridge.core.utils.common import (
    KEY_SD_ULS_PER_GIRDER,
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_OH,
    KEY_DD_MU_OH,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_BOT,
    KEY_DD_WK_TOP,
    KEY_DD_WK_OH,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_MP_ED_TYPE,
)
from osdagbridge.core.reports.report_utils import _tex


@dataclass
class URRecord:
    """Standardized utilization record for a single structural design check."""
    element: str          # "Girder", "Deck Slab", "Cross Bracing", "End Diaphragm"
    check_name: str       # e.g. "Girder --- Moment"
    governing_combo: str  # e.g. "ULS 1"
    demand: Optional[float]
    capacity: Optional[float]
    demand_str: str       # formatted display string (e.g. "1526.50 kN-m")
    capacity_str: str     # formatted display string (e.g. "2140.00 kN-m")
    unit: str
    ur: Optional[float]   # numeric ratio (e.g. 0.71)
    status: str           # "PASS", "FAIL", "---", "N/A"
    note: str = ""


@dataclass
class GirderURRecord:
    """Governing utilization summary for an individual plate girder."""
    girder_label: str
    governing_check: str
    governing_combo: str
    ur: float
    status: str


@dataclass
class UtilizationData:
    """Container for all extracted utilization records."""
    records: List[URRecord]
    girder_records: List[GirderURRecord]


def collect_utilization(bridge: Any) -> UtilizationData:
    """Extract and normalize all utilization data from bridge analysis and design results."""
    records: List[URRecord] = []
    girder_records: List[GirderURRecord] = []

    od = bridge.output_dict or {}
    dr = od.get("design_results", {}) or {}
    pg = dr.get("per_girder") or dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}

    # Helper formatters
    def _ur_num(v: Any) -> Optional[float]:
        try:
            return round(float(v), 4)
        except (TypeError, ValueError):
            return None

    def _fmt_ur_str(ur: Optional[float]) -> str:
        if ur is None:
            return "---"
        return f"{ur:.2f}"

    def _vu_str(v: Any, u: str = "") -> str:
        if v in (None, ""):
            return "---"
        try:
            f = float(v)
            s = f"{f:.2f}"
        except (TypeError, ValueError):
            s = str(v)
        u_clean = u.strip()
        return f"{s} {u_clean}" if u_clean else s

    # 1. Girder Checks Extraction
    def _get_girder_gov_lc(g: str, check_ids: set) -> str:
        gd = pg.get(g) or {}
        best = None
        for lc, ld in (gd.get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in (ld.get("checks") or []):
                chk_id = chk.get("id") if chk.get("id") is not None else chk.get("check_id")
                if chk_id in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, lc)
        return _tex(str(best[1]).strip()) if best else "---"

    def _extract_girder_check(check_name: str, check_ids: set, fallback_unit: str = "") -> URRecord:
        best = None  # (dcr, dem, cap, du, cu, g)
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                chk_id = chk.get("check_id") if chk.get("check_id") is not None else chk.get("id")
                if chk_id in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (
                            d,
                            chk.get("demand"),
                            chk.get("capacity"),
                            chk.get("demand_unit") or fallback_unit,
                            chk.get("capacity_unit") or fallback_unit,
                            g,
                        )

        if best is not None:
            d, dem, cap, du, cu, g = best
            gov_lc = _get_girder_gov_lc(g, check_ids)
            d_flt = float(dem) if dem not in (None, "") else None
            c_flt = float(cap) if cap not in (None, "") else None
            ur_val = _ur_num(d)
            st = "PASS" if (ur_val is not None and ur_val <= 1.0) else ("FAIL" if ur_val else "---")
            return URRecord(
                element="Girder",
                check_name=check_name,
                governing_combo=gov_lc,
                demand=d_flt,
                capacity=c_flt,
                demand_str=_vu_str(dem, du),
                capacity_str=_vu_str(cap, cu),
                unit=cu or du or fallback_unit,
                ur=ur_val,
                status=st,
            )

        # Fallback for SLS checks (e.g. deflection)
        best_sls = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for lc, ld in (gd.get("per_lc") or {}).items():
                if str(lc).lower().startswith("envelope"):
                    continue
                for chk in (ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best_sls is None or d > best_sls[0]:
                            best_sls = (d, chk.get("demand"), chk.get("capacity"), lc)

        if best_sls is not None:
            d, dem, cap, lc = best_sls
            d_flt = float(dem) if dem not in (None, "") else None
            c_flt = float(cap) if cap not in (None, "") else None
            ur_val = _ur_num(d)
            st = "PASS" if (ur_val is not None and ur_val <= 1.0) else ("FAIL" if ur_val else "---")
            return URRecord(
                element="Girder",
                check_name=check_name,
                governing_combo=_tex(str(lc).strip()),
                demand=d_flt,
                capacity=c_flt,
                demand_str=_vu_str(dem, fallback_unit),
                capacity_str=_vu_str(cap, fallback_unit),
                unit=fallback_unit,
                ur=ur_val,
                status=st,
            )

        return URRecord(
            element="Girder",
            check_name=check_name,
            governing_combo="---",
            demand=None,
            capacity=None,
            demand_str="---",
            capacity_str="---",
            unit=fallback_unit,
            ur=None,
            status="---",
        )

    records.append(_extract_girder_check("Girder --- Moment", {1}))
    records.append(_extract_girder_check("Girder --- Shear", {2}))
    records.append(_extract_girder_check("Girder --- LTB (constr.)", {5}))
    records.append(_extract_girder_check("Girder --- Deflection", {13, 14}, fallback_unit="mm"))
    records.append(_extract_girder_check("Girder --- Stress", {11}, fallback_unit="MPa"))
    records.append(_extract_girder_check("Girder --- Fatigue", {8, 9}, fallback_unit="MPa"))
    records.append(_extract_girder_check("Transverse Shear (slab)", {16}))

    # 2. Deck Slab Checks Extraction
    dk_rpt = od.get("deck_report_values", {}) or {}
    dk_has = bool(dk_rpt)
    dk_oh = bool(dk_rpt.get(KEY_DD_HAS_OVERHANG))

    def _dkv(k: str) -> float:
        try:
            return float(dk_rpt.get(k) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    deck_combo = (
        r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")
    ) if dk_has else "---"

    # Crack width
    wk_lim = _dkv(KEY_DD_WK_LIMIT)
    dk_gov_wk = max(_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP), _dkv(KEY_DD_WK_OH) if dk_oh else 0.0)
    wk_ur = round(dk_gov_wk / wk_lim, 4) if (dk_has and wk_lim > 0) else None

    # Governing frequent SLS combo
    gov_sls = "Frequent SLS"
    best_sls_freq = None
    for g, gd in pg.items():
        if str(g).startswith("EB"):
            continue
        for lc, ld in (gd.get("per_lc") or {}).items():
            if "frequent" in str(lc).lower():
                d = ld.get("max_dcr") or 0.0
                if best_sls_freq is None or d > best_sls_freq[0]:
                    best_sls_freq = (d, lc)
    if best_sls_freq:
        gov_sls = _tex(str(best_sls_freq[1]).strip())

    records.append(
        URRecord(
            element="Deck Slab",
            check_name="Crack Width (slab)",
            governing_combo=gov_sls if dk_has else "---",
            demand=dk_gov_wk if dk_has else None,
            capacity=wk_lim if dk_has else None,
            demand_str=f"{dk_gov_wk:.3f} mm" if dk_has else "---",
            capacity_str=f"{wk_lim:.3f} mm" if dk_has else "---",
            unit="mm",
            ur=wk_ur,
            status="PASS" if (wk_ur is not None and wk_ur <= 1.0) else ("FAIL" if wk_ur else "---"),
        )
    )

    def _extract_deck_check(check_name: str, dem_k: str, cap_k: str, unit: str, is_oh: bool = False) -> URRecord:
        if not dk_has:
            return URRecord("Deck Slab", check_name, "---", None, None, "---", "---", unit, None, "---")
        if is_oh and not dk_oh:
            return URRecord("Deck Slab", check_name, deck_combo, None, None, "N/A", "N/A", unit, None, "N/A")
        dem = _dkv(dem_k)
        cap = _dkv(cap_k)
        ur_val = round(dem / cap, 4) if cap > 0 else None
        st = "PASS" if (ur_val is not None and ur_val <= 1.0) else ("FAIL" if ur_val else "---")
        return URRecord(
            element="Deck Slab",
            check_name=check_name,
            governing_combo=deck_combo,
            demand=dem,
            capacity=cap,
            demand_str=f"{dem:.2f} {unit}",
            capacity_str=f"{cap:.2f} {unit}",
            unit=unit,
            ur=ur_val,
            status=st,
        )

    records.append(_extract_deck_check("Deck --- Flexure (sagging)", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m"))
    records.append(_extract_deck_check("Deck --- Flexure (hogging)", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m"))
    records.append(_extract_deck_check("Deck --- Cantilever Overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True))
    records.append(_extract_deck_check("Deck --- Punching Shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa"))
    records.append(_extract_deck_check("Deck --- One-Way Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m"))

    # 3. Cross Bracing Checks Extraction
    cb_pairs = bridge.get_cb_pairs() if hasattr(bridge, "get_cb_pairs") else []

    def _extract_cb_force(force_type: str, check_name: str) -> URRecord:
        best = None
        for pair in cb_pairs:
            for member in ("diagonal", "chord"):
                cap = bridge.get_cb_capacity(pair, member, force_type)
                eff = bridge.get_cb_efficiency(pair, member, force_type)
                try:
                    ur = float(eff)
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return URRecord("Cross Bracing", check_name, "---", None, None, "---", "---", "kN", None, "---")
        ur, pair, member, cap = best
        gov = bridge.get_cb_gov_lc(pair, member, force_type) or "---"
        cap_val = float(cap) if cap else None
        dem_val = (cap_val * ur) if cap_val is not None else None
        st = "PASS" if ur <= 1.0 else "FAIL"
        return URRecord(
            element="Cross Bracing",
            check_name=check_name,
            governing_combo=gov,
            demand=dem_val,
            capacity=cap_val,
            demand_str=f"{dem_val:.2f} kN" if dem_val is not None else "---",
            capacity_str=(f"{cap} kN") if cap else "---",
            unit="kN",
            ur=round(ur, 4),
            status=st,
        )

    records.append(_extract_cb_force("compression", "Cross Bracing --- Compression"))
    records.append(_extract_cb_force("tension", "Cross Bracing --- Tension"))

    # Cross bracing slenderness
    best_slnd = None
    for pair in cb_pairs:
        for member in ("diagonal", "chord"):
            s = bridge.get_cb_slenderness(pair, member)
            try:
                sf = float(s)
            except (TypeError, ValueError):
                continue
            lim = 400.0 if member == "chord" else 250.0
            ratio = sf / lim
            if best_slnd is None or ratio > best_slnd[0]:
                best_slnd = (ratio, sf, lim)

    if best_slnd is not None:
        ratio, sf, lim = best_slnd
        records.append(
            URRecord(
                element="Cross Bracing",
                check_name="Cross Bracing --- Slenderness",
                governing_combo="---",
                demand=sf,
                capacity=lim,
                demand_str=f"{sf:.1f}",
                capacity_str=f"{lim:.0f}",
                unit="",
                ur=round(ratio, 4),
                status="PASS" if ratio <= 1.0 else "FAIL",
            )
        )
    else:
        records.append(
            URRecord("Cross Bracing", "Cross Bracing --- Slenderness", "---", None, None, "---", "---", "", None, "---")
        )

    # 4. End Diaphragm Checks Extraction
    ed_type = ""
    for k, v in (bridge.input_dict or {}).items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower()

    if ed_is_cb:
        ed_mom = _extract_cb_force("compression", "End Diaphragm --- Moment")
        ed_mom.element = "End Diaphragm"
        ed_shr = _extract_cb_force("tension", "End Diaphragm --- Shear")
        ed_shr.element = "End Diaphragm"
        records.append(ed_mom)
        records.append(ed_shr)
    else:
        msg = "Rolled / Welded section --- design to be added"
        records.append(URRecord("End Diaphragm", "End Diaphragm --- Moment", "---", None, None, msg, msg, "", None, "N/A", note=msg))
        records.append(URRecord("End Diaphragm", "End Diaphragm --- Shear", "---", None, None, msg, msg, "", None, "N/A", note=msg))

    # 5. Per-Girder Governing UR Extraction
    for g, gd in pg.items():
        if str(g).startswith("EB"):
            continue
        max_ur = 0.0
        gov_chk_name = "Moment"
        gov_lc_name = "---"

        for chk in (gd.get("checks") or []):
            dcr = float(chk.get("dcr") or 0.0)
            if dcr > max_ur:
                max_ur = dcr
                gov_chk_name = chk.get("name") or chk.get("check_name") or str(chk.get("check_id") or "Check")

        for lc, ld in (gd.get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in (ld.get("checks") or []):
                dcr = float(chk.get("dcr") or 0.0)
                if dcr >= max_ur:
                    gov_lc_name = str(lc).strip()

        girder_records.append(
            GirderURRecord(
                girder_label=str(g),
                governing_check=gov_chk_name,
                governing_combo=gov_lc_name,
                ur=round(max_ur, 4),
                status="PASS" if max_ur <= 1.0 else "FAIL",
            )
        )

    return UtilizationData(records=records, girder_records=girder_records)
