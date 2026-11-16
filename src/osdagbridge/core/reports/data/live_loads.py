"""Extraction and normalization of vehicular live loads and footpath loads (Requirement R3)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_FOOTPATH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_BL_IRC_CLASS_A,
    KEY_BL_IRC_70R_WHEELED,
    KEY_BL_IRC_70R_TRACKED,
    KEY_BL_IRC_AA_WHEELED,
    KEY_BL_IRC_AA_TRACKED,
    KEY_BL_IRC_70R_BOGIE,
    KEY_BL_IRC_CLASS_SV,
    KEY_BL_IRC_CLASS_FATIGUE,
    KEY_BL_ECCENTRICITY,
    KEY_LL_ECCENTRICITY,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


@dataclass
class VehicleLoadRow:
    """Standardized representation of an evaluated vehicular live load."""
    name: str
    total_load_kN: Optional[float]
    impact_factor: Optional[float]
    braking_considered: bool
    braking_value_kN: Optional[float]
    braking_eccentricity: Optional[str]
    source_clause: str


@dataclass
class FootpathLoad:
    """Footpath live load specification per IRC 6 Cl. 206."""
    mode: str
    intensity_kN_m2: Optional[float]
    count: int
    width_m: float
    clause: str = "IRC 6 Cl. 206.1"


@dataclass
class LiveLoadTable:
    """Aggregated live load data container for Chapter 3."""
    vehicles: List[VehicleLoadRow]
    footpath: Optional[FootpathLoad]
    centrifugal_evaluated: bool = False
    lanes_evaluated: int = 2


def collect_live_loads(input_dict: Dict[str, Any]) -> LiveLoadTable:
    """Extract and normalize live load data from project input dictionary."""
    # Determine span length for impact factor evaluation
    span = input_dict.get(KEY_SPAN)
    span_m: Optional[float] = None
    if span not in (None, ""):
        try:
            span_m = float(span)
        except (TypeError, ValueError):
            span_m = None

    # Determine number of design traffic lanes for braking force calculation
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    lanes_int = 2
    if lanes not in (None, ""):
        try:
            lanes_int = max(1, int(lanes))
        except (TypeError, ValueError):
            lanes_int = 2

    braking_kN: Optional[float] = None
    try:
        braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_kN = round(braking_force_t * 9.81, 2)
    except Exception:
        # Fallback when upstream cl_211_2_braking_force raises UnboundLocalError on lanes <= 2
        try:
            w_a = sum(IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"])
            b1 = 0.20 * (w_a / 9810.0) if lanes_int >= 1 else 0.0
            b2 = 0.05 * (sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) / 9810.0) if lanes_int > 2 else 0.0
            braking_force_t = b1 + b2
            braking_kN = round(braking_force_t * 9.81, 2)
        except Exception:
            braking_kN = None

    eccentricity_raw = input_dict.get(KEY_BL_ECCENTRICITY) or input_dict.get(KEY_LL_ECCENTRICITY)
    eccentricity_str = str(eccentricity_raw) if eccentricity_raw else "1.2 m"

    # Known standard IRC vehicle definitions and mapping
    vehicle_catalog = [
        (
            KEY_LL_IRC_CLASS_A,
            KEY_BL_IRC_CLASS_A,
            "IRC Class A",
            543.5,  # 55.4 tonnes * 9.81 = 543.5 kN
            (1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_70R_WHEELED,
            KEY_BL_IRC_70R_WHEELED,
            "IRC Class 70R (Wheeled)",
            981.0,  # 100 tonnes * 9.81 = 981.0 kN
            (1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_70R_TRACKED,
            KEY_BL_IRC_70R_TRACKED,
            "IRC Class 70R (Tracked)",
            686.7,  # 70 tonnes * 9.81 = 686.7 kN
            (1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_70R_BOGIE,
            KEY_BL_IRC_70R_BOGIE,
            "IRC Class 70R (Bogie)",
            392.4,  # 40 tonnes * 9.81 = 392.4 kN
            (1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_AA_WHEELED,
            KEY_BL_IRC_AA_WHEELED,
            "IRC Class AA (Wheeled)",
            392.4,  # 40 tonnes * 9.81 = 392.4 kN
            (1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_AA_TRACKED,
            KEY_BL_IRC_AA_TRACKED,
            "IRC Class AA (Tracked)",
            686.7,  # 70 tonnes * 9.81 = 686.7 kN
            (1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)) if span_m else None,
            "IRC 6 Cl. 204.1",
        ),
        (
            KEY_LL_IRC_CLASS_SV,
            KEY_BL_IRC_CLASS_SV,
            "IRC Special Vehicle (SV)",
            3776.9,  # 385 tonnes * 9.81 = 3776.9 kN
            1.0,  # No dynamic impact for SV per IRC 6 Cl. 208
            "IRC 6 Cl. 204.5",
        ),
        (
            KEY_LL_IRC_CLASS_FATIGUE,
            KEY_BL_IRC_CLASS_FATIGUE,
            "IRC Fatigue Vehicle",
            392.4,  # 40 tonnes * 9.81 = 392.4 kN
            1.0,
            "IRC 6 Cl. 204.6",
        ),
    ]

    selected_vehicles: List[VehicleLoadRow] = []

    for ll_key, bl_key, name, total_kN, if_val, clause in vehicle_catalog:
        if bool(input_dict.get(ll_key, False)):
            is_braking = bool(input_dict.get(bl_key, False))
            selected_vehicles.append(
                VehicleLoadRow(
                    name=name,
                    total_load_kN=total_kN,
                    impact_factor=round(if_val, 3) if if_val is not None else None,
                    braking_considered=is_braking,
                    braking_value_kN=braking_kN if is_braking else None,
                    braking_eccentricity=eccentricity_str if is_braking else None,
                    source_clause=clause,
                )
            )

    # Process custom vehicles
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES, [])
    if isinstance(custom, list):
        for c in custom:
            c_name = c.get("name") if isinstance(c, dict) else str(c)
            if not c_name:
                continue
            total_axle_kN = None
            if isinstance(c, dict) and "axles" in c:
                try:
                    total_axle_kN = sum(float(a.get("load", 0)) for a in c["axles"])
                except Exception:
                    pass
            selected_vehicles.append(
                VehicleLoadRow(
                    name=f"Custom: {c_name}",
                    total_load_kN=total_axle_kN,
                    impact_factor=None,
                    braking_considered=False,
                    braking_value_kN=None,
                    braking_eccentricity=None,
                    source_clause="User Defined",
                )
            )

    # Footpath load processing
    no_of_footpaths = 0
    raw_n_fp = input_dict.get(KEY_TS_NO_OF_FOOTPATHS)
    if raw_n_fp not in (None, ""):
        try:
            no_of_footpaths = int(raw_n_fp)
        except (TypeError, ValueError):
            no_of_footpaths = 0

    footpath_geom = str(input_dict.get(KEY_FOOTPATH, "None")).strip().lower()
    has_footpath = (no_of_footpaths > 0) and (footpath_geom != "none")

    footpath_obj: Optional[FootpathLoad] = None
    if has_footpath:
        fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6")).strip()
        fp_val_raw = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)
        fp_intensity: Optional[float] = None

        if fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic"):
            try:
                fp_intensity = round(float(IRC6_2017.cl_206_1_footway_load()), 3)
            except Exception:
                fp_intensity = 5.0
        elif fp_val_raw not in (None, ""):
            try:
                fp_intensity = float(fp_val_raw)
            except (TypeError, ValueError):
                fp_intensity = None

        fp_width = 0.0
        raw_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
        if raw_width not in (None, ""):
            try:
                fp_width = float(raw_width)
            except (TypeError, ValueError):
                fp_width = 0.0

        footpath_obj = FootpathLoad(
            mode=fp_mode,
            intensity_kN_m2=fp_intensity,
            count=no_of_footpaths,
            width_m=fp_width,
            clause="IRC 6 Cl. 206.1",
        )

    return LiveLoadTable(
        vehicles=selected_vehicles,
        footpath=footpath_obj,
        centrifugal_evaluated=False,
        lanes_evaluated=lanes_int,
    )
