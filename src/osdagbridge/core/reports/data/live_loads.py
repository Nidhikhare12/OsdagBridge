"""Extraction and normalization of vehicular live loads and footpath loads (Requirement R3).

Engineering rule for this module: the report layer never invents or estimates a
value. Every number collected here comes from one of three places:

* the user inputs (``input_dict``),
* an existing upstream helper of :class:`IRC6_2017`, or
* nowhere, in which case the field is ``None`` and the report prints ``---``.

Each helper has its own unit convention, so each total below is derived by a
dedicated function that states the conversion it applies.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

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

# The IRC6_2017 vehicle helpers build their loads with the unit constant
# ``t = kN * g`` where ``kN = 1000`` (see utils/codes/keyfile.py), i.e. in
# newtons. This is the divisor that turns those values into kN.
_NEWTONS_PER_KN = 1000.0

# Reasons recorded when a value cannot be printed (shown under the table).
GAP_NO_VEHICLE_DEFINITION = "no vehicle definition in the software's IRC 6 library"
GAP_TRACK_TOTAL_AMBIGUOUS = (
    "the software's track-load definition gives a load per metre and does not state "
    "whether it is per track or per vehicle"
)
GAP_HELPER_FAILED = "the software's vehicle definition could not be evaluated"
GAP_NO_IMPACT_ROUTINE = "no impact-factor routine in the software for this vehicle"
GAP_NO_SPAN = "span not available"
GAP_BRAKING_NOT_EVALUATED = (
    "the software's IRC 6 Cl. 211.2 braking-force routine returned no value"
)
GAP_BRAKING_NO_LANES = "number of traffic lanes not available"
GAP_CUSTOM_TOTAL = "axle loads of the user-defined vehicle do not give a total"
GAP_CUSTOM_IMPACT = "impact factor of a user-defined vehicle is not reported"


@dataclass
class VehicleLoadRow:
    """Standardized representation of an evaluated vehicular live load."""
    name: str
    total_load_kN: Optional[float]
    impact_factor: Optional[float]
    braking_considered: bool
    braking_value_kN: Optional[float]
    braking_eccentricity_m: Optional[float]
    source_clause: str
    total_load_gap: Optional[str] = None
    impact_factor_gap: Optional[str] = None


@dataclass
class FootpathLoad:
    """Footpath live load specification per IRC 6 Cl. 206."""
    mode: str
    intensity_kN_m2: Optional[float]
    count: int
    width_m: Optional[float]
    clause: str = "IRC 6:2017 Cl. 206.1"


@dataclass
class LiveLoadTable:
    """Aggregated live load data container for Chapter 3."""
    vehicles: List[VehicleLoadRow]
    footpath: Optional[FootpathLoad]
    centrifugal_evaluated: bool = False
    lanes_evaluated: Optional[int] = None
    braking_force_kN: Optional[float] = None
    braking_gap: Optional[str] = None


# ---------------------------------------------------------------------------
# Small parsers for raw input values
# ---------------------------------------------------------------------------
def _to_float(value: Any) -> Optional[float]:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_checked(value: Any) -> bool:
    """Checkbox state as stored by the UI (bool, or its text form in a saved file)."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1", "checked")
    return bool(value)


# ---------------------------------------------------------------------------
# Total load per vehicle: one function per upstream helper, explicit units
# ---------------------------------------------------------------------------
def _sum_axle_loads_newton_to_kN(vehicle: Dict[str, Any]) -> float:
    """``wheel_loads`` holds per-axle totals in N; their sum / 1000 is the total in kN.

    Same derivation as ``analyser._vehicle_total_weight_kN`` in the analysis engine.
    """
    return float(sum(vehicle["wheel_loads"])) / _NEWTONS_PER_KN


def _total_class_a_kN() -> float:
    """IRC 6 Cl. 204.1 Class A train: 8 axle loads in N -> kN."""
    return _sum_axle_loads_newton_to_kN(IRC6_2017.cl_204_1_ClassA_vehicle())


def _total_70r_wheeled_kN() -> float:
    """IRC 6 Cl. 204.1 Class 70R wheeled: 7 axle loads in N -> kN."""
    return _sum_axle_loads_newton_to_kN(IRC6_2017.cl_204_1_Class70R_vehicle_wheel())


def _total_special_vehicle_kN() -> float:
    """IRC 6 Cl. 204.5 special vehicle: the helper already returns ``total_load_kN`` in kN."""
    return float(IRC6_2017.cl_204_5_1_special_vehicle()["total_load_kN"])


def _total_fatigue_kN() -> float:
    """IRC 6 Cl. 204.6 fatigue truck: 3 axle loads in N -> kN."""
    return _sum_axle_loads_newton_to_kN(IRC6_2017.cl_204_6_fatigue_load())


def _evaluate(fn: Optional[Callable[[], float]]) -> Optional[float]:
    """Call an upstream-backed derivation; any failure yields ``None`` (prints ``---``)."""
    if fn is None:
        return None
    try:
        return float(fn())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Impact factor (printed as 1 + I, as the analysis engine applies it)
# ---------------------------------------------------------------------------
def _impact_cl_208_2(span_m: float) -> float:
    """IRC 6 Cl. 208.2 (Class A / Class B)."""
    return 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)


def _impact_cl_208_3(span_m: float) -> float:
    """IRC 6 Cl. 208.3 (Class AA and Class 70R)."""
    return 1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)


# ---------------------------------------------------------------------------
# Braking force
# ---------------------------------------------------------------------------
def _braking_force_kN(lanes: Optional[int]) -> tuple[Optional[float], Optional[str]]:
    """Bridge-level braking force from the upstream IRC 6 Cl. 211.2 helper.

    The helper is called exactly as it is. It sums ``wheel_loads`` of the
    vehicle helpers, which are in N, so its result is converted N -> kN.
    If it raises or returns nothing the value is ``None``: this module carries
    no braking formula of its own.
    """
    if lanes is None:
        return None, GAP_BRAKING_NO_LANES
    try:
        force_newton = IRC6_2017.cl_211_2_braking_force(lanes)
    except Exception:
        return None, GAP_BRAKING_NOT_EVALUATED
    value = _to_float(force_newton)
    if value is None:
        return None, GAP_BRAKING_NOT_EVALUATED
    return value / _NEWTONS_PER_KN, None


# Catalogue of the IRC vehicles offered in the Loading tab, in the tab's order:
# (vehicle key, braking key, report name, total-load derivation, reason when the
#  total is unavailable, impact-factor derivation, clause of the vehicle definition)
_VEHICLE_CATALOG = [
    (KEY_LL_IRC_CLASS_A, KEY_BL_IRC_CLASS_A, "Class A",
     _total_class_a_kN, GAP_HELPER_FAILED, _impact_cl_208_2, "IRC 6 Cl. 204.1"),
    # No helper exists for Class AA: the total is not available.
    (KEY_LL_IRC_AA_WHEELED, KEY_BL_IRC_AA_WHEELED, "Class AA (Wheeled)",
     None, GAP_NO_VEHICLE_DEFINITION, _impact_cl_208_3, "IRC 6 Cl. 204.1"),
    (KEY_LL_IRC_AA_TRACKED, KEY_BL_IRC_AA_TRACKED, "Class AA (Tracked)",
     None, GAP_NO_VEHICLE_DEFINITION, _impact_cl_208_3, "IRC 6 Cl. 204.1"),
    (KEY_LL_IRC_70R_WHEELED, KEY_BL_IRC_70R_WHEELED, "Class 70R (Wheeled)",
     _total_70r_wheeled_kN, GAP_HELPER_FAILED, _impact_cl_208_3, "IRC 6 Cl. 204.1"),
    # cl_204_1_Class70R_vehicle_track() returns 'wheel_loads_udl' (load per metre)
    # over x = [0, 4.57] with two track positions in 'z'. It does not say whether
    # the UDL is per track or for the vehicle (the wheeled helpers store per-axle
    # totals that the engine splits over the two 'z' positions), and no analysis
    # code consumes it. The two readings differ by a factor of two, so no total
    # is derived here.
    (KEY_LL_IRC_70R_TRACKED, KEY_BL_IRC_70R_TRACKED, "Class 70R (Tracked)",
     None, GAP_TRACK_TOTAL_AMBIGUOUS, _impact_cl_208_3, "IRC 6 Cl. 204.1"),
    # No helper exists for the 70R bogie.
    (KEY_LL_IRC_70R_BOGIE, KEY_BL_IRC_70R_BOGIE, "Class 70R (Bogie)",
     None, GAP_NO_VEHICLE_DEFINITION, _impact_cl_208_3, "IRC 6 Cl. 204.1"),
    # No upstream routine returns an impact factor for the SV or the fatigue truck.
    (KEY_LL_IRC_CLASS_SV, KEY_BL_IRC_CLASS_SV, "Class SV",
     _total_special_vehicle_kN, GAP_HELPER_FAILED, None, "IRC 6 Cl. 204.5"),
    (KEY_LL_IRC_CLASS_FATIGUE, KEY_BL_IRC_CLASS_FATIGUE, "Class Fatigue",
     _total_fatigue_kN, GAP_HELPER_FAILED, None, "IRC 6 Cl. 204.6"),
]


def _braking_considered(input_dict: Dict[str, Any], ll_key: str, bl_key: str) -> bool:
    """Whether braking is considered for a selected vehicle.

    An explicit ``KEY_BL_*`` checkbox value always decides. The Loading tab only
    has such a checkbox for Class SV; for every other class the application's own
    rule applies (``generate_results_values_builder.BREAKING_LOAD_KEYS``): the
    braking row follows the vehicle selection.
    """
    if bl_key in input_dict:
        return _is_checked(input_dict.get(bl_key))
    if bl_key == KEY_BL_IRC_CLASS_SV:
        return False
    return _is_checked(input_dict.get(ll_key))


def _custom_vehicle_row(custom: Any) -> Optional[VehicleLoadRow]:
    """Row for a user-defined vehicle; only user-entered values are reported."""
    name = custom.get("name") if isinstance(custom, dict) else str(custom)
    if not name:
        return None
    total_kN: Optional[float] = None
    if isinstance(custom, dict) and str(custom.get("vehicle_type", "Wheeled")) == "Wheeled":
        # The custom-vehicle dialog stores the axle loads of a wheeled vehicle in kN.
        loads = [_to_float(v) for v in (custom.get("axle_loads") or [])]
        if loads and all(v is not None for v in loads):
            total_kN = float(sum(loads))
    return VehicleLoadRow(
        name=f"Custom: {name}",
        total_load_kN=total_kN,
        impact_factor=None,
        braking_considered=False,
        braking_value_kN=None,
        braking_eccentricity_m=None,
        source_clause="User defined",
        total_load_gap=None if total_kN is not None else GAP_CUSTOM_TOTAL,
        impact_factor_gap=GAP_CUSTOM_IMPACT,
    )


def _collect_footpath(input_dict: Dict[str, Any]) -> Optional[FootpathLoad]:
    """Footpath live load, or ``None`` when no footpath is configured."""
    count = 0
    raw_count = _to_float(input_dict.get(KEY_TS_NO_OF_FOOTPATHS))
    if raw_count is not None:
        count = int(raw_count)

    footpath_geom = str(input_dict.get(KEY_FOOTPATH, "None")).strip().lower()
    if count <= 0 or footpath_geom == "none":
        return None

    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6")).strip()
    code_mode = mode.lower() in ("as per irc 6", "as per irc6", "automatic")
    if code_mode:
        # Upstream helper returns the Cl. 206.1 footway load already in kN/m2.
        try:
            intensity = _to_float(IRC6_2017.cl_206_1_footway_load())
        except Exception:
            intensity = None
        clause = "IRC 6:2017 Cl. 206.1"
    else:
        # User-defined pressure, reported as entered.
        intensity = _to_float(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
        clause = "User defined"

    return FootpathLoad(
        mode=mode,
        intensity_kN_m2=intensity,
        count=count,
        width_m=_to_float(input_dict.get(KEY_TS_FOOTPATH_WIDTH)),
        clause=clause,
    )


def collect_live_loads(input_dict: Dict[str, Any]) -> LiveLoadTable:
    """Extract and normalize live load data from project input dictionary."""
    span_m = _to_float(input_dict.get(KEY_SPAN))
    if span_m is not None and span_m <= 0:
        span_m = None

    lanes: Optional[int] = None
    raw_lanes = _to_float(input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT))
    if raw_lanes is not None and raw_lanes >= 1:
        lanes = int(raw_lanes)

    braking_kN, braking_gap = _braking_force_kN(lanes)

    # Height of the braking force above the deck top, as entered in the Loading tab.
    eccentricity_m = _to_float(input_dict.get(KEY_BL_ECCENTRICITY))
    if eccentricity_m is None:
        eccentricity_m = _to_float(input_dict.get(KEY_LL_ECCENTRICITY))

    vehicles: List[VehicleLoadRow] = []
    for ll_key, bl_key, name, total_fn, total_gap, impact_fn, clause in _VEHICLE_CATALOG:
        if not _is_checked(input_dict.get(ll_key)):
            continue

        total_kN = _evaluate(total_fn)

        impact: Optional[float] = None
        impact_gap: Optional[str] = None
        if impact_fn is None:
            impact_gap = GAP_NO_IMPACT_ROUTINE
        elif span_m is None:
            impact_gap = GAP_NO_SPAN
        else:
            impact = _evaluate(lambda: impact_fn(span_m))
            if impact is None:
                impact_gap = GAP_NO_IMPACT_ROUTINE
            else:
                impact = round(impact, 3)

        considered = _braking_considered(input_dict, ll_key, bl_key)
        vehicles.append(
            VehicleLoadRow(
                name=name,
                total_load_kN=total_kN,
                impact_factor=impact,
                braking_considered=considered,
                braking_value_kN=braking_kN if considered else None,
                braking_eccentricity_m=eccentricity_m if considered else None,
                source_clause=clause,
                total_load_gap=None if total_kN is not None else total_gap,
                impact_factor_gap=impact_gap,
            )
        )

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES, [])
    if isinstance(custom, list):
        for c in custom:
            row = _custom_vehicle_row(c)
            if row is not None:
                vehicles.append(row)

    return LiveLoadTable(
        vehicles=vehicles,
        footpath=_collect_footpath(input_dict),
        centrifugal_evaluated=False,
        lanes_evaluated=lanes,
        braking_force_kN=braking_kN,
        braking_gap=braking_gap,
    )
