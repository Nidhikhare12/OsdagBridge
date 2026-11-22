"""Extraction and normalization of material quantities (Requirement R5)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class QuantitySummary:
    """Normalized structural material quantities."""
    # Structural Steel (MT)
    steel_girders_wt: Optional[float]
    bracing_top_wt: Optional[float]
    bracing_bot_wt: Optional[float]
    bracing_diag_wt: Optional[float]
    bracing_total_wt: Optional[float]
    end_diaphragm_wt: Optional[float]  # None (U8: not computed in upstream)
    shear_studs_wt: Optional[float]

    # Concrete (m³) & Reinforcement (MT)
    concrete_deck_vol: Optional[float]
    concrete_deck_wt: Optional[float]
    rebar_deck_wt: Optional[float]
    crash_barrier_vol: Optional[float]
    crash_barrier_wt: Optional[float]


def _parse_val(val: Any) -> Optional[float]:
    """Parse numeric quantity value, converting 'N.A.', None or empty strings to None."""
    if val in (None, "", "N.A.", "N/A", "---"):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def collect_quantities(input_dict: Dict[str, Any]) -> QuantitySummary:
    """Extract and parse material quantities from input_dict."""
    inp = input_dict or {}

    girders_wt = _parse_val(inp.get("steel_girders_wt_total"))
    top_wt = _parse_val(inp.get("bracing_top_wt_total"))
    bot_wt = _parse_val(inp.get("bracing_bot_wt_total"))
    diag_wt = _parse_val(inp.get("bracing_diag_wt_total"))

    # Calculate total cross bracing weight if components exist
    bracing_components = [w for w in (top_wt, bot_wt, diag_wt) if w is not None]
    bracing_total = round(sum(bracing_components), 4) if bracing_components else None

    # End Diaphragms have no quantity source in upstream (unknown U8)
    end_diaphragm_wt = _parse_val(inp.get("end_diaphragm_wt_total"))

    studs_wt = _parse_val(inp.get("shear_studs_wt_total"))

    concrete_vol = _parse_val(inp.get("concrete_deck_vol_total"))
    concrete_wt = _parse_val(inp.get("concrete_deck_wt_total"))
    rebar_wt = _parse_val(inp.get("rebar_deck_wt_total"))
    barrier_vol = _parse_val(inp.get("crash_barrier_vol_total"))
    barrier_wt = _parse_val(inp.get("crash_barrier_wt_total"))

    return QuantitySummary(
        steel_girders_wt=girders_wt,
        bracing_top_wt=top_wt,
        bracing_bot_wt=bot_wt,
        bracing_diag_wt=diag_wt,
        bracing_total_wt=bracing_total,
        end_diaphragm_wt=end_diaphragm_wt,
        shear_studs_wt=studs_wt,
        concrete_deck_vol=concrete_vol,
        concrete_deck_wt=concrete_wt,
        rebar_deck_wt=rebar_wt,
        crash_barrier_vol=barrier_vol,
        crash_barrier_wt=barrier_wt,
    )
