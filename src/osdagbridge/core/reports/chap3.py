# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
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

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.styles import COL_PARAM, ROW_SKIP, VSPACE_TABLE, lt_begin, lt_end

_IRC_VEHICLES = (
    (KEY_LL_IRC_CLASS_A,       "Class A",              "IRC 6 Cl. 204"),
    (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)",  "IRC 6 Cl. 204"),
    (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)",  "IRC 6 Cl. 204"),
    (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",   "IRC 6 Cl. 204"),
    (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",   "IRC 6 Cl. 204"),
    (KEY_LL_IRC_CLASS_SV,      "Class SV",             "IRC 6 Cl. 204"),
    (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",    "IRC 6 Cl. 204"),
    (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",        "IRC 6 Cl. 204"),
)


def _kv_table(caption, rows, colspec=COL_PARAM,
              header=r"\textbf{parameter} & \textbf{value} \\"):
    """Two-or-more-column longtable from (cell, ...) tuples."""
    body = []
    for row in rows:
        body.append(" & ".join(row) + ROW_SKIP + "\n\\hline")
    return (
        VSPACE_TABLE + "\n"
        + lt_begin(colspec, caption, header)
        + "\n".join(body) + "\n"
        + lt_end()
    )


def ch3_loads(input_dict):
    # Selected IRC vehicles only — used to build Table (a) dynamically.
    vehicles = []
    for key, name, _clause in _IRC_VEHICLES:
        if input_dict.get(key):
            vehicles.append(name)

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = ""
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or 
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or 
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or 
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")
            
            if factors:
                impact_factor_str = ", ".join(factors)
            else:
                impact_factor_str = "N/A"
        except Exception:
            impact_factor_str = "N/A"
    else:
        impact_factor_str = "N/A"

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = ""
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
        except Exception:
            braking_force_str = "N/A"
    else:
        braking_force_str = "N/A"

    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")

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

    # Footpath pressure: honour IRC-automatic mode instead of dumping an empty
    # custom-value cell (fp_str was previously computed and unused).
    fp_mode_disp = str(fp_mode).strip() or "---"
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_pressure = f"{IRC6_2017.cl_206_1_footway_load():.3f}"
        except Exception:
            fp_pressure = "N/A"
        fp_ref = "IRC 6 Cl. 206.1"
    elif fp_value not in (None, ""):
        fp_pressure = str(fp_value)
        fp_ref = "User-defined"
    else:
        fp_pressure = "N/A"
        fp_ref = "---"

    veh_rows = []
    if vehicles:
        for name in vehicles:
            clause = next((c for k, n, c in _IRC_VEHICLES if n == name), "IRC 6")
            veh_rows.append((
                r"\textnormal{" + _tex(name) + r"}",
                "Included",
                "---",
                clause,
            ))
    else:
        veh_rows.append((r"\textnormal{Vehicles considered}", "None", "---", "---"))
    veh_rows.append((
        r"\textnormal{Impact Factor}",
        _tex(impact_factor_str),
        "---",
        "IRC 6 Cl. 208",
    ))
    veh_rows.append((
        r"\textnormal{Braking Load}",
        _tex(braking_force_str),
        "kN",
        "IRC 6 Cl. 211.2",
    ))

    fp_rows = [(
        r"\textnormal{Footway live load}",
        _tex(fp_mode_disp),
        _tex(fp_pressure),
        r"kN/m\textsuperscript{2}",
        _tex(fp_ref),
    )]

    return (
        r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

"""
        + _kv_table("Dead Load -- Self Weight", [
            (r"\textnormal{Steel Self-Weight Applied}",
             _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r" kN/m\textsuperscript{3}")),
            (r"\textnormal{Concrete Deck Weight}",
             _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r" kN/m\textsuperscript{3}")),
            (r"\textnormal{Self-Weight Factor}",
             _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)),
        ])
        + "\n"
        + _kv_table("Dead Load for Surfacing (DW)", [
            (r"\textnormal{Wearing Course Load}",
             _render_value(input_dict, KEY_WC_MATERIAL) + " x "
             + _render_value(input_dict, KEY_WC_THICKNESS)),
            (r"\textnormal{Additional SIDL (Crash Barrier)}",
             _render_value(input_dict, KEY_CB_LOAD) + r" kN/m per barrier"),
            (r"\textnormal{Railing Load}",
             _render_value(input_dict, KEY_RL_LOAD_VALUE) + r" kN/m\sdstar{}"),
        ])
        + "\n"
        + _kv_table(
            "Vehicle Live Loads (LL)",
            veh_rows,
            colspec=r"|L{4.6cm}|L{4.4cm}|C{1.8cm}|p{4.0cm}|",
            header=r"\textbf{Parameter} & \textbf{Value} & \textbf{Unit} & \textbf{Reference} \\",
        )
        + "\n"
        + _kv_table(
            "Footpath Live Loads",
            fp_rows,
            colspec=r"|L{3.6cm}|L{3.0cm}|C{2.2cm}|C{2.2cm}|p{3.6cm}|",
            header=(
                r"\textbf{Parameter} & \textbf{Mode} & \textbf{Pressure} & "
                r"\textbf{Unit} & \textbf{Reference} \\"
            ),
        )
        + "\n"
        + _kv_table("Wind Load (WL) --- per IRC 6", [
            (r"\textnormal{Basic Wind Speed, Vb}",
             _render_value(input_dict, 'wind_speed', ' m/s') + r" [from Project Location]"),
            (r"\textnormal{Terrain Type}",
             _render_value(input_dict, KEY_WL_TERRAIN_TYPE)),
            (r"\textnormal{Average Exposed Height, H (m)}",
             _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')),
            (r"\textnormal{Hourly Mean Wind Speed, Vz}",
             _render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')),
            (r"\textnormal{Hourly Wind Pressure, Pz}",
             _render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}')),
            (r"\textnormal{Transverse Wind Force}",
             _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')),
            (r"\textnormal{Longitudinal Wind Force}",
             _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')),
            (r"\textnormal{Vertical Wind Force}",
             _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')),
        ])
        + "\n"
        + _kv_table("Earthquake Load (EL) --- per IRC 6", [
            (r"\textnormal{Seismic Zone}",
             _render_value(input_dict, 'seismic_zone') + r" [from Project Location]"),
            (r"\textnormal{Zone Factor, Z}",
             _render_value(input_dict, KEY_SL_ZONE_FACTOR)),
            (r"\textnormal{Importance Factor, I}",
             _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)),
            (r"\textnormal{Type of Soil}",
             _render_value(input_dict, KEY_SL_SOIL_TYPE)),
            (r"\textnormal{Sa/g}",
             _render_value(input_dict, KEY_SL_SPECTRAL_COEFF)),
            (r"\textnormal{Horizontal Seismic Coefficient, Ah}",
             _render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)),
            (r"\textnormal{Vertical Seismic Coefficient, Av}",
             _render_value(input_dict, KEY_SL_VERTICAL_COEFF)),
            (r"\textnormal{Horizontal Seismic Force (longitudinal)}", "kN"),
            (r"\textnormal{Horizontal Seismic Force (transverse)}", "kN"),
        ])
        + "\n"
        + _kv_table("Temperature Load (TL) --- per IRC 6", [
            (r"\textnormal{Maximum Shade Temperature}",
             _render_value(input_dict, 'shade_temp_max') + r" $^\circ$C"),
            (r"\textnormal{Minimum Shade Temperature}",
             _render_value(input_dict, 'shade_temp_min') + r" $^\circ$C"),
            (r"\textnormal{Effective Bridge Temp. Range}",
             _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) + r" to "
             + _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX) + r" $^\circ$C"),
            (r"\textnormal{Temperature Rise / Fall for Design}",
             r"+" + _render_value(input_dict, KEY_TL_TEMP_RISE)
             + r" $^\circ$C / \textminus{}"
             + _render_value(input_dict, KEY_TL_TEMP_FALL) + r" $^\circ$C"),
        ])
        + "\n"
        + VSPACE_TABLE + "\n"
        + lt_begin(
            r"|C{4.0cm}|p{11.5cm}|",
            "Load Combinations",
            r"\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]",
        )
        + lc_rows_str + "\n"
        + lt_end()
        + r"""

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
    )


