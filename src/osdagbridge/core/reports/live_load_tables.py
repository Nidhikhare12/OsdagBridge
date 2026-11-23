"""Separate vehicle live-load table and footpath live-load table (Chapter 3)."""
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_LL_CUSTOM_VEHICLES, KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE, KEY_LL_IRC_70R_BOGIE, KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_IRC_CLASS_SV,
)

BRAKING_FACTOR = 0.20   # same factor used in IRC6_2017.cl_211_2_braking_force
DASH = "--"


def _fmt(v, nd=2):
    return DASH if v is None else f"{v:.{nd}f}"


def _totals():
    """Total vehicle loads in kN, taken from the software's IRC 6 functions."""
    t = {}
    try:
        t["A"] = sum(IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]) / 1000.0
    except Exception:
        pass
    try:
        t["70RW"] = sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) / 1000.0
    except Exception:
        pass
    try:
        d = IRC6_2017.cl_204_1_Class70R_vehicle_track()
        length = d["x"][1] - d["x"][0]
        t["70RT"] = d["wheel_loads_udl"] * length * len(d["z"]) / 1000.0
    except Exception:
        pass
    try:
        t["SV"] = float(IRC6_2017.cl_204_5_1_special_vehicle()["total_load_kN"])
    except Exception:
        pass
    return t


def _selected_vehicles(d):
    """(label, key, impact_kind, braking) for every vehicle ticked in the UI.
    braking: True / False / None (None = no data -> dash)."""
    rows = []
    spec = [
        (KEY_LL_IRC_CLASS_A,       "Class A",             "A",    "A",   "A",  True),
        (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)", "70RW", "AA",  "70R", True),
        (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)", "70RT", "AA",  "70R", True),
        (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",  "AAW",  "AA",  None, None),
        (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",  "AAT",  "AA",  None, None),
        (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",   "70RB", "AA",  None, None),
        (KEY_LL_IRC_CLASS_SV,      "Class SV",            "SV",   None,  None, False),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",       "FAT",  None,  None, None),
    ]
    for ui_key, label, tkey, impact, _g, braking in spec:
        if d.get(ui_key):
            rows.append((label, tkey, impact, braking))
    custom = d.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get("name") if isinstance(c, dict) else c
            if name:
                rows.append((str(name), None, None, None))
    return rows


def _impact(d, kind):
    try:
        span = float(d.get(KEY_SPAN))
        if kind == "A":
            return 1.0 + IRC6_2017.cl_208_2_impact_factor(span)
        if kind == "AA":
            return 1.0 + IRC6_2017.cl_208_3_impact_factor(span)
    except Exception:
        pass
    return None


def _vehicle_table(d):
    totals = _totals()
    ecc = None
    try:
        ecc = IRC6_2017.cl_211_3_braking_force_location()["height_m"]
    except Exception:
        pass
    body = []
    for label, tkey, impact_kind, braking in _selected_vehicles(d):
        total = totals.get(tkey) if tkey else None
        im = _impact(d, impact_kind) if impact_kind else None
        if braking is True and total is not None:
            cons, val, e = "Yes", _fmt(BRAKING_FACTOR * total), _fmt(ecc, 1)
        elif braking is False:
            cons, val, e = "No", DASH, DASH
        else:
            cons, val, e = DASH, DASH, DASH
        body.append(" & ".join([_tex(label), _fmt(total, 1), _fmt(im, 3), cons, val, e]) + r" \\[4pt]" + "\n\\hline")
    if not body:
        body.append(r"\multicolumn{6}{|c|}{No vehicle selected} \\" + "\n\\hline")
    head = (r"\hline" "\n"
            r"\textbf{Vehicle} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & "
            r"\multicolumn{3}{c|}{\textbf{Braking Load}} \\" "\n"
            r"\cline{4-6}" "\n"
            r" & & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity (m)} \\" "\n"
            r"\hline" "\n")
    return (r"\begin{longtable}{|L{3.9cm}|C{2.4cm}|C{2.3cm}|C{2.3cm}|C{2.2cm}|C{2.5cm}|}" "\n"
            r"\caption{\textbf{Live Loads (LL) --- Vehicles}}\\" "\n"
            + head + r"\endfirsthead" "\n" + head + r"\endhead" "\n"
            + "\n".join(body) + "\n" + r"\end{longtable}")


def _footpath_table(d):
    mode = str(d.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "") or "").strip()
    val = d.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    pressure, src = DASH, DASH
    if mode.lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            pressure, src = f"{IRC6_2017.cl_206_1_footway_load():.3f}", "IRC 6 Cl. 206.1"
        except Exception:
            pass
    elif val not in (None, ""):
        pressure, src = _tex(val), "User input"
    return (r"\begin{longtable}{|L{6.0cm}|C{3.5cm}|C{2.5cm}|C{3.3cm}|}" "\n"
            r"\caption{\textbf{Live Loads (LL) --- Footpath}}\\" "\n"
            r"\hline \textbf{Parameter} & \textbf{Value} & \textbf{Unit} & \textbf{Source} \\ \hline" "\n"
            r"\endfirsthead" "\n"
            r"\hline \textbf{Parameter} & \textbf{Value} & \textbf{Unit} & \textbf{Source} \\ \hline" "\n"
            r"\endhead" "\n"
            r"Footpath Live Load (pressure) & " + pressure + r" & kN/m\textsuperscript{2} & " + src + r" \\[4pt]" "\n"
            r"\hline" "\n"
            r"\end{longtable}")


def live_load_tables(input_dict):
    return (_vehicle_table(input_dict) + "\n\n\\vspace{1em}\n" + _footpath_table(input_dict))
