# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_ECCENTRICITY,
    KEY_TS_FOOTPATH_WIDTH,
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
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.latex_tables import longtable, note, param_table
from osdagbridge.core.reports.report_utils import _tex, _render_value

# ---------------------------------------------------------------------------
# Live-load vehicle registry (what the UI "Loading -> Live Load" tab offers)
# ---------------------------------------------------------------------------
G = 9.81            # kN per tonne-force (same value the load generator uses)


def _total_kN(fn_name, fallback_tonnes, key="wheel_loads"):
    """Total vehicle load in kN from the IRC 6 helper; falls back to the code
    tonnage when the helper only provides a per-track UDL."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    try:
        data = getattr(IRC6_2017, fn_name)()
        loads = data.get(key)
        if isinstance(loads, (list, tuple)):
            return sum(loads) / 1000.0           # helper works in N
    except Exception:
        pass
    return fallback_tonnes * G


def _sv_total():
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    try:
        return float(IRC6_2017.cl_204_5_1_special_vehicle()["total_load_kN"])
    except Exception:
        return 385.0 * G


# (label, UI key, impact clause, total-load provider, braking key)
def _vehicle_registry():
    return [
        ("Class A",            KEY_LL_IRC_CLASS_A,       "A",  lambda: _total_kN("cl_204_1_ClassA_vehicle", 55.4),            KEY_LL_IRC_CLASS_A),
        ("Class AA (Wheeled)", KEY_LL_IRC_AA_WHEELED,    "AA", lambda: 40.0 * G,                                              KEY_LL_IRC_AA_WHEELED),
        ("Class AA (Tracked)", KEY_LL_IRC_AA_TRACKED,    "AA", lambda: 70.0 * G,                                              KEY_LL_IRC_AA_TRACKED),
        ("Class 70R (Wheeled)", KEY_LL_IRC_70R_WHEELED,  "AA", lambda: _total_kN("cl_204_1_Class70R_vehicle_wheel", 100.0),  KEY_LL_IRC_70R_WHEELED),
        ("Class 70R (Tracked)", KEY_LL_IRC_70R_TRACKED,  "AA", lambda: 70.0 * G,                                              KEY_LL_IRC_70R_TRACKED),
        ("Class 70R (Bogie)",  KEY_LL_IRC_70R_BOGIE,     "AA", lambda: 40.0 * G,                                              KEY_LL_IRC_70R_BOGIE),
        ("Class SV",           KEY_LL_IRC_CLASS_SV,      None, _sv_total, KEY_BL_IRC_CLASS_SV),
        ("Class Fatigue",      KEY_LL_IRC_CLASS_FATIGUE, None, lambda: _total_kN("cl_204_6_fatigue_load", 40.0),              KEY_LL_IRC_CLASS_FATIGUE),
    ]


def _selected(input_dict, key):
    raw = input_dict.get(key)
    return raw is True or str(raw).strip().lower() in ("true", "yes", "1", "checked")


def live_load_vehicle_table(input_dict):
    """Table: one row per vehicle SELECTED in the UI (Additional Inputs ->
    Loading -> Live Load).  Columns follow the expected layout:
    Vehicle | Total Load (kN) | Impact Factor | Braking (Considered? / Value / Eccentricity)."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = None
    try:
        span = float(input_dict.get(KEY_SPAN))
    except (TypeError, ValueError):
        pass
    ecc = input_dict.get(KEY_LL_ECCENTRICITY)
    try:
        ecc_str = f"{float(ecc):.2f}"
    except (TypeError, ValueError):
        ecc_str = "---"

    rows = []
    for label, key, impact_cls, total_fn, brk_key in _vehicle_registry():
        if not _selected(input_dict, key):
            continue
        try:
            total = total_fn()
            total_s = f"{total:,.1f}"
        except Exception:
            total, total_s = None, "---"
        impact_s = "---"
        if span is not None and impact_cls:
            try:
                im = (IRC6_2017.cl_208_2_impact_factor(span) if impact_cls == "A"
                      else IRC6_2017.cl_208_3_impact_factor(span))
                impact_s = f"{1.0 + im:.3f}"
            except Exception:
                pass
        braking = _selected(input_dict, brk_key)
        # IRC 6 Cl. 211.2: braking = 20 % of the first-lane vehicle load
        brk_val = f"{0.20 * total:,.1f}" if (braking and total is not None) else "---"
        brk_ecc = ecc_str if braking else "---"
        rows.append(" & ".join([_tex(label), total_s, impact_s,
                                "Yes" if braking else "No", brk_val, brk_ecc]) + r" \\" + "\n\\hline")

    for c in (input_dict.get(KEY_LL_CUSTOM_VEHICLES) or []):
        name = c.get("name") if isinstance(c, dict) else str(c)
        if name:
            rows.append(" & ".join([_tex(name), "---", "---", "---", "---", "---"]) + r" \\" + "\n\\hline")

    if not rows:
        rows.append(r"\multicolumn{6}{|c|}{No vehicle selected} \\" + "\n\\hline")

    header = (r"\hdrfill & & & \multicolumn{3}{c|}{\hcell{Braking Load}} \\" + "\n"
              r"\cline{4-6}" + "\n"
              r"\hdrfill \hcell{Vehicle} & \hcell{Total Load (kN)} & \hcell{Impact Factor} & "
              r"\hcell{Considered?} & \hcell{Value (kN)} & \hcell{Eccentricity (m)} \\")
    return (longtable("live_vehicle", "Live Loads (LL) --- Vehicles", header, "\n".join(rows),
                      label="tab:live-vehicles")
            + note(r"Vehicles are those selected in the Loading tab of the Additional Inputs. "
                   r"Impact factor $= 1 + IM$ (IRC 6 Cl. 208.2 for Class A, Cl. 208.3 for Class AA/70R; "
                   r"not defined for Class SV / Fatigue). Braking value $= 20\%$ of the vehicle load "
                   r"(IRC 6 Cl. 211.2, first lane); eccentricity is measured from the top of the deck "
                   r"(IRC 6 Cl. 211.3)."))


def live_load_footpath_table(input_dict):
    fp = str(input_dict.get(KEY_FOOTPATH, "")).strip()
    has_fp = fp.lower() not in ("", "none", "no", "n/a")
    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")).strip()
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if not has_fp:
        pressure, ref = "Not applicable", "No footpath provided"
    elif fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            pressure, ref = f"{IRC6_2017.cl_206_1_footway_load():.3f}", r"kN/m$^2$ --- IRC 6 Cl. 206.1"
        except Exception:
            pressure, ref = "---", r"kN/m$^2$ --- IRC 6 Cl. 206.1"
    elif fp_value not in (None, ""):
        pressure, ref = _tex(fp_value), r"kN/m$^2$ --- user defined"
    else:
        pressure, ref = "---", r"kN/m$^2$"
    rows = [
        ("Footpath", _tex(fp) if fp else "---", "Typical section input"),
        ("Footpath width", _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH) if has_fp else "---", "m"),
        ("Footpath live load intensity", pressure, ref),
    ]
    body = "\n".join(r"\textnormal{" + a + "} & " + b + " & " + c + r" \\" + "\n\\hline" for a, b, c in rows)
    return longtable("live_footpath", "Live Loads (LL) --- Footpath", ["Parameter", "Value", "Unit / Reference"],
                     body, label="tab:live-footpath")


def live_load_other_table(input_dict):
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    rows = [
        ("Number of design lanes", _tex(lanes) if lanes not in (None, "") else "---", "IRC 6 Cl. 204.3"),
        ("Centrifugal force", "Not applicable", "Straight alignment (IRC 6 Cl. 209.1 applies to curved spans)"),
    ]
    body = "\n".join(r"\textnormal{" + a + "} & " + b + " & " + c + r" \\" + "\n\\hline" for a, b, c in rows)
    return longtable("live_footpath", "Live Loads (LL) --- Other Parameters", ["Parameter", "Value", "Reference / Remark"],
                     body, label="tab:live-other")


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    rv = lambda key, unit="": _render_value(input_dict, key, unit)
    sup3 = r" kN/m\textsuperscript{3}"
    lc_tbl = longtable("load_combos", "Load Combinations", ["Combination ID", "Load Cases"], lc_rows_str,
                       label="tab:load-combinations")

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{0.6em}
""" + param_table("Dead Load -- Self Weight", [
        ("Steel Self-Weight Applied", rv(KEY_MATERIAL_GIRDER_DENSITY, sup3)),
        ("Concrete Deck Weight", rv(KEY_MATERIAL_DECK_DENSITY, sup3)),
        ("Self-Weight Factor", rv(KEY_PL_SELF_WEIGHT_FACTOR)),
    ]) + param_table("Dead Load for Surfacing (DW)", [
        ("Wearing Course Load", rv(KEY_WC_MATERIAL) + " x " + rv(KEY_WC_THICKNESS, " mm")),
        ("Additional SIDL (Crash Barrier)", rv(KEY_CB_LOAD) + " kN/m per barrier"),
        ("Railing Load", rv(KEY_RL_LOAD_VALUE) + r" kN/m\sdstar{}"),
    ]) + live_load_vehicle_table(input_dict) + live_load_footpath_table(input_dict) + live_load_other_table(input_dict) + param_table("Wind Load (WL) --- per IRC 6", [
        ("Basic Wind Speed, Vb", rv('wind_speed', ' m/s') + " [from Project Location]"),
        ("Terrain Type", rv(KEY_WL_TERRAIN_TYPE)),
        ("Average Exposed Height, H (m)", rv(KEY_WL_AVG_EXPOSED_HEIGHT, ' m')),
        ("Hourly Mean Wind Speed, Vz", rv(KEY_WL_HOURLY_MEAN_WIND, ' m/s') if input_dict.get(KEY_WL_HOURLY_MEAN_WIND) else vz_str),
        ("Hourly Wind Pressure, Pz", rv(KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}') if input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE) else pz_str),
        ("Transverse Wind Force", rv(KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')),
        ("Longitudinal Wind Force", rv(KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')),
        ("Vertical Wind Force", rv(KEY_WL_VERTICAL_WIND_FORCE, ' kN')),
    ]) + param_table("Earthquake Load (EL) --- per IRC 6", [
        ("Seismic Zone", rv('seismic_zone') + " [from Project Location]"),
        ("Zone Factor, Z", rv(KEY_SL_ZONE_FACTOR) or _sl(sl_zone_factor)),
        ("Importance Factor, I", rv(KEY_SL_IMPORTANCE_FACTOR)),
        ("Type of Soil", rv(KEY_SL_SOIL_TYPE)),
        ("Sa/g", rv(KEY_SL_SPECTRAL_COEFF) or _sl(sl_spectral)),
        ("Horizontal Seismic Coefficient, Ah", rv(KEY_SL_HORIZONTAL_COEFF) or _sl(sl_ah)),
        ("Vertical Seismic Coefficient, Av", rv(KEY_SL_VERTICAL_COEFF) or _sl(sl_av)),
        ("Horizontal Seismic Force (longitudinal)", "--- kN"),
        ("Horizontal Seismic Force (transverse)", "--- kN"),
    ]) + param_table("Temperature Load (TL) --- per IRC 6", [
        ("Maximum Shade Temperature", rv('shade_temp_max') + r" $^\circ$C"),
        ("Minimum Shade Temperature", rv('shade_temp_min') + r" $^\circ$C"),
        ("Effective Bridge Temp. Range", (rv(KEY_TL_BRIDGE_TEMP_MIN) or tl_temp_min) + " to " + (rv(KEY_TL_BRIDGE_TEMP_MAX) or tl_temp_max) + r" $^\circ$C"),
        ("Temperature Rise / Fall for Design", "+" + (rv(KEY_TL_TEMP_RISE) or tl_rise) + r" $^\circ$C / $-$" + (rv(KEY_TL_TEMP_FALL) or tl_fall) + r" $^\circ$C"),
    ]) + lc_tbl + note("All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.")
