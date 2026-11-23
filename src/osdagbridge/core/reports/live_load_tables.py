"""Chapter 3 live-load tables: vehicle loads and footway load.

Vehicle and footway loads are reported in two separate tables. Vehicles
follow the selection made in the UI (Additional Inputs, Loading tab), and
every figure comes from the IRC 6 functions of the backend. Anything the
backend cannot supply is shown as a dash instead of being guessed.

Notes on the backend values used here:

* Vehicle functions return wheel loads in newtons (Class A sums to
  543 474 N, i.e. 55.4 t), so totals are divided by 1000 to give kN.
* ``IRC6_2017.cl_211_2_braking_force`` is not used: it raises
  ``UnboundLocalError`` for every lane count and treats newtons as tonnes.
  The braking value is instead 20 % of the vehicle's own total load, the
  first-lane rule of IRC 6 Cl. 211.2.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
)

logger = logging.getLogger(__name__)

BRAKING_FRACTION = 0.20
"""Braking force as a fraction of the train load, IRC 6 Cl. 211.2."""

_NEWTONS_PER_KN = 1000.0
_IRC_FOOTWAY_MODES = ("as per irc 6", "as per irc6", "automatic")
_SAFE_ERRORS = (ValueError, TypeError, KeyError, IndexError, ArithmeticError)


@dataclass(frozen=True)
class VehicleRow:
    """One vehicle of the live-load table; ``None`` means "not available"."""

    name: str
    total_load_kn: float | None
    impact_factor: float | None
    braking_considered: bool | None
    braking_value_kn: float | None
    braking_eccentricity_m: float | None


@dataclass(frozen=True)
class _Kind:
    """What the backend knows about a standard IRC vehicle."""

    total_load_kn: Callable[[], float] | None
    impact: str | None  # "A" (Cl. 208.2), "AA" (Cl. 208.3) or None
    braking: bool | None


def _class_a_kn() -> float:
    loads = IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]
    return sum(loads) / _NEWTONS_PER_KN


def _class_70r_wheeled_kn() -> float:
    loads = IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]
    return sum(loads) / _NEWTONS_PER_KN


def _class_70r_tracked_kn() -> float:
    track = IRC6_2017.cl_204_1_Class70R_vehicle_track()
    length = track["x"][1] - track["x"][0]
    tracks = len(track["z"])
    return track["wheel_loads_udl"] * length * tracks / _NEWTONS_PER_KN


def _special_vehicle_kn() -> float:
    return IRC6_2017.cl_204_5_1_special_vehicle()["total_load_kN"]


# Order follows the UI list. Braking: Class A, 70R and AA are considered,
# Class SV is not (task example table); other classes are not stated.
_STANDARD: tuple[tuple[str, str, _Kind], ...] = (
    (KEY_LL_IRC_CLASS_A, "Class A", _Kind(_class_a_kn, "A", True)),
    (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)",
     _Kind(_class_70r_wheeled_kn, "AA", True)),
    (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)",
     _Kind(_class_70r_tracked_kn, "AA", True)),
    (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)", _Kind(None, "AA", True)),
    (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)", _Kind(None, "AA", True)),
    (KEY_LL_IRC_CLASS_SV, "Class SV", _Kind(_special_vehicle_kn, None, False)),
    (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)", _Kind(None, "AA", None)),
    (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue", _Kind(None, None, None)),
)
_UNKNOWN = _Kind(None, None, None)


def _safe(func: Callable[..., float], *args: float) -> float | None:
    """Call a backend function; return ``None`` on data-related errors.

    Only data errors are caught. Programming errors in the backend (for
    example ``UnboundLocalError``) are deliberately not hidden.
    """
    try:
        return float(func(*args))
    except _SAFE_ERRORS as exc:
        logger.warning("Live-load value unavailable (%s: %s)",
                       type(exc).__name__, exc)
        return None


def _span_m(input_dict: dict) -> float | None:
    span = input_dict.get(KEY_SPAN)
    if span in (None, ""):
        return None
    try:
        return float(span)
    except (TypeError, ValueError):
        return None


def _impact_factor(kind: _Kind, span: float | None) -> float | None:
    if kind.impact is None or span is None:
        return None
    func = (IRC6_2017.cl_208_2_impact_factor if kind.impact == "A"
            else IRC6_2017.cl_208_3_impact_factor)
    fraction = _safe(func, span)
    return None if fraction is None else 1.0 + fraction


def _row(name: str, kind: _Kind, span: float | None) -> VehicleRow:
    total = None if kind.total_load_kn is None else _safe(kind.total_load_kn)
    value = eccentricity = None
    if kind.braking:
        eccentricity = _safe(
            lambda: IRC6_2017.cl_211_3_braking_force_location()["height_m"])
        if total is not None:
            value = BRAKING_FRACTION * total
    return VehicleRow(
        name=name,
        total_load_kn=total,
        impact_factor=_impact_factor(kind, span),
        braking_considered=kind.braking,
        braking_value_kn=value,
        braking_eccentricity_m=eccentricity,
    )


def vehicle_rows(input_dict: dict) -> list[VehicleRow]:
    """Build one row per vehicle selected in the UI, in UI order.

    Args:
        input_dict: The report's input dictionary.

    Returns:
        Standard IRC vehicles first, then custom vehicles.
    """
    span = _span_m(input_dict)
    rows = [_row(label, kind, span)
            for key, label, kind in _STANDARD if input_dict.get(key)]
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for item in custom:
            name = item.get("name") if isinstance(item, dict) else item
            if name and isinstance(name, str):
                rows.append(_row(name, _UNKNOWN, span))
    return rows


def footway_rows(input_dict: dict) -> list[tuple[str, str, str]]:
    """Build ``(parameter, value, unit-or-basis)`` rows for the footway.

    Args:
        input_dict: The report's input dictionary.

    Returns:
        Rows describing the footway load, or an empty list when no footway
        load is defined.
    """
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")).strip()
    stored = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if mode.lower() in _IRC_FOOTWAY_MODES:
        pressure = _safe(IRC6_2017.cl_206_1_footway_load)
        if pressure is not None:
            return [("Footway live load intensity", f"{pressure:.3f}",
                     r"kN/m\textsuperscript{2}"),
                    ("Basis", "IRC 6", "Cl. 206.1")]
    elif stored not in (None, ""):
        return [("Footway live load intensity", _tex(stored),
                 r"kN/m\textsuperscript{2}"),
                ("Basis", "User defined", "--")]
    return []


def _number(value: float | None, decimals: int) -> str:
    if value is None:
        return styles.LOAD_TABLES.placeholder
    return f"{value:.{decimals}f}"


def _yes_no(value: bool | None) -> str:
    if value is None:
        return styles.LOAD_TABLES.placeholder
    return "Yes" if value else "No"


def vehicle_table(rows: list[VehicleRow]) -> str:
    """Return the LaTeX of the vehicle live-load table.

    Args:
        rows: Output of ``vehicle_rows``.

    Returns:
        A ``longtable`` with a two-row header (Braking Load spans three
        columns). ``normalize_longtables`` repeats both header rows.
    """
    style = styles.LOAD_TABLES
    gap = r"\\[\rowgap]"
    if rows:
        body = "".join(
            f"{_tex(r.name)} & {_number(r.total_load_kn, 1)} & "
            f"{_number(r.impact_factor, 3)} & "
            f"{_yes_no(r.braking_considered)} & "
            f"{_number(r.braking_value_kn, 1)} & "
            f"{_number(r.braking_eccentricity_m, 2)} {gap}\n\\hline\n"
            for r in rows)
    else:
        body = (r"\multicolumn{6}{|c|}{No live-load vehicle selected} "
                + gap + "\n\\hline\n")
    return (
        r"\begin{longtable}{" + style.vehicle_columns + "}\n"
        r"\caption{\textbf{Live Loads (LL) --- Vehicles (IRC 6)}}" "\n"
        r"\hline" "\n"
        r"\textbf{Vehicle} & \textbf{Total Load (kN)} & "
        r"\textbf{Impact Factor} & "
        r"\multicolumn{3}{c|}{\textbf{Braking Load}} \\" "\n"
        r"\cline{4-6}" "\n"
        r" & & & \textbf{Considered?} & \textbf{Value (kN)} & "
        r"\textbf{Eccentricity (m)} \\" "\n"
        r"\hline" "\n" + body + r"\end{longtable}" "\n"
        r"\noindent{\footnotesize\textit{Total load: sum of axle loads "
        r"(IRC 6 Cl. 204). Impact factor: 1 + impact fraction (Cl. 208). "
        r"Braking value: 20\,\% of the vehicle load (Cl. 211.2); "
        r"eccentricity: height of the braking force above the carriageway "
        r"(Cl. 211.3). Centrifugal force: not considered in the current "
        r"analysis. A dash (--) means the value is not available.}}" "\n"
    )


def footway_table(rows: list[tuple[str, str, str]]) -> str:
    """Return the LaTeX of the footway live-load table.

    Args:
        rows: Output of ``footway_rows``.

    Returns:
        A ``longtable`` with Parameter, Value and Unit/Basis columns.
    """
    style = styles.LOAD_TABLES
    gap = r"\\[\rowgap]"
    if rows:
        body = "".join(f"{_tex(p)} & {v} & {u} {gap}\n\\hline\n"
                       for p, v, u in rows)
    else:
        body = (r"Footway live load & Not applicable & "
                f"{style.placeholder} {gap}\n\\hline\n")
    return (
        r"\begin{longtable}{" + style.footway_columns + "}\n"
        r"\caption{\textbf{Live Loads (LL) --- Footway}}" "\n"
        r"\hline" "\n"
        r"\textbf{Parameter} & \textbf{Value} & \textbf{Unit / Basis} \\" "\n"
        r"\hline" "\n" + body + r"\end{longtable}" "\n"
    )


def live_load_tables(input_dict: dict) -> str:
    """Return the LaTeX for both live-load tables.

    Args:
        input_dict: The report's input dictionary.

    Returns:
        Vehicle table followed by footway table.
    """
    return (vehicle_table(vehicle_rows(input_dict))
            + "\n\\vspace{1em}\n"
            + footway_table(footway_rows(input_dict)))
