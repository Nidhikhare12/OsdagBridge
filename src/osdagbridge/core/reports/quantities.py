# =============================================================================
# OsdagBridge — Chapter 7 helper: end-diaphragm steel quantity
# =============================================================================
#
# core/boq/boq_generator.py produces the BOM rows for girders, cross bracing,
# deck, rebar, studs and crash barriers, but has no row for the end diaphragms
# — although Chapter 7 must chart "Structural Steel tonnage (Girders, Cross
# Bracing, End Diaphragms)".  This module adds that row using ONLY values the
# design stage already stored (section areas of the designed ED members, girder
# spacing and depth).  It mirrors the geometry the designer used
# (PlateGirderBridge._design_end_diaphragm_members): chord length = girder
# spacing, diagonal length = sqrt(s^2 + (0.85 D)^2).
# =============================================================================

from __future__ import annotations

import logging
import math
from typing import Dict

from osdagbridge.core.utils.common import (
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)

logger = logging.getLogger(__name__)

STEEL_DENSITY_MT_PER_M3 = 7.85
_PREFIX = "transverse_member_design.ed.section_properties"

_KEYS = ("end_diaphragm_vol_formula", "end_diaphragm_qty", "end_diaphragm_vol_total",
         "end_diaphragm_wt_single", "end_diaphragm_wt_total")


def _na() -> Dict[str, str]:
    return {k: "N.A." for k in _KEYS}


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def end_diaphragm_quantities(inputs: dict, outputs: dict) -> Dict[str, str]:
    """Return the Chapter-7 BOM fields of the end-diaphragm row (strings)."""
    try:
        n = int(float(inputs.get(KEY_TS_NO_OF_GIRDERS) or 0))
        s = _f(inputs.get(KEY_TS_GIRDER_SPACING))
        depth = _f(inputs.get(f"{KEY_MP_GIRDER_DEPTH}.G1.M1") or inputs.get(KEY_MP_GIRDER_DEPTH))
        if n < 2 or not s or not depth:
            return _na()
        if depth > 20.0:                       # stored in mm -> m
            depth /= 1000.0
        diag_len = math.hypot(s, 0.85 * depth)

        vol_one_end = 0.0                      # m3 of steel in ONE end diaphragm line
        bays = 0
        for i in range(1, n):
            pid = f"G{i}G{i+1}"
            a_diag = _f(outputs.get(f"{_PREFIX}.end_diaphragm.{pid}.A"))
            a_top = _f(outputs.get(f"{_PREFIX}.top_chord.{pid}.A"))
            a_bot = _f(outputs.get(f"{_PREFIX}.bottom_chord.{pid}.A"))
            if a_diag is None and a_top is None and a_bot is None:
                continue
            bays += 1
            vol_one_end += ((a_top or 0.0) * s + (a_bot or 0.0) * s
                            + 2.0 * (a_diag or 0.0) * diag_len) / 1e4   # cm2 * m -> m3
        if bays == 0:
            return _na()

        total_vol = 2.0 * vol_one_end          # two supports
        wt_total = total_vol * STEEL_DENSITY_MT_PER_M3
        qty = 2 * bays
        wt_single = wt_total / qty
        return {
            "end_diaphragm_vol_formula": (
                rf"$\Sigma(A_{{chords}}\,s + 2A_{{diag}}\,L_d)$, $s={s:.2f}$ m, $L_d={diag_len:.2f}$ m"),
            "end_diaphragm_qty": str(qty),
            "end_diaphragm_vol_total": f"{total_vol:.2f}",
            "end_diaphragm_wt_single": f"{wt_single:.4f}",
            "end_diaphragm_wt_total": f"{wt_total:.2f}",
        }
    except Exception as exc:                   # never break the report
        logger.warning("End-diaphragm quantity skipped: %s", exc)
        return _na()
