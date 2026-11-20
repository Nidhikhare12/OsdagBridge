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
    KEY_WL_VERTICAL_WIND_FORCE,
    KEY_CARRIAGEWAY_WIDTH
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports import styles


def ch3_loads(input_dict):
    # Live load vehicle names mapping
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)

    vehicles_str = ", ".join(vehicles) if vehicles else "None"

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

    # ---- Per-vehicle live load rows (only vehicles selected in the UI) ----
    _G = 9.81
    try:
        _sv_kN = f"{IRC6_2017.cl_204_5_1_special_vehicle()['total_load_kN']:.0f}"
    except Exception:
        _sv_kN = f"{385 * _G:.0f}"

    _VEH = [
        ("Class A", KEY_LL_IRC_CLASS_A, f"{55.4 * _G:.0f}", "A", True),
        ("Class 70R (Wheeled)", KEY_LL_IRC_70R_WHEELED, f"{100 * _G:.0f}", "AA", True),
        ("Class 70R (Tracked)", KEY_LL_IRC_70R_TRACKED, f"{70 * _G:.0f}", "AA", True),
        ("Class AA (Wheeled)", KEY_LL_IRC_AA_WHEELED, f"{40 * _G:.0f}", "AA", True),
        ("Class AA (Tracked)", KEY_LL_IRC_AA_TRACKED, f"{70 * _G:.0f}", "AA", True),
        ("Class SV", KEY_LL_IRC_CLASS_SV, _sv_kN, "AA", False),
        ("Class 70R (Bogie)", KEY_LL_IRC_70R_BOGIE, f"{40 * _G:.0f}", "AA", True),
        ("Class Fatigue", KEY_LL_IRC_CLASS_FATIGUE, f"{40 * _G:.0f}", "AA", False),
    ]

    _braking_kN = None
    try:
        _lanes_val = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
        if _lanes_val in (None, ""):
            _cw = input_dict.get(KEY_CARRIAGEWAY_WIDTH)
            _lanes_val = IRC6_2017.table_6(float(_cw)) if _cw not in (None, "") else None
        if _lanes_val not in (None, ""):
           _braking_kN = IRC6_2017.cl_211_2_braking_force(int(_lanes_val)) / 1000.0
    except Exception:
        _braking_kN = None

    def _impact(kind):
        try:
            s = float(input_dict.get(KEY_SPAN))
            im = (IRC6_2017.cl_208_2_impact_factor(s) if kind == "A"
                  else IRC6_2017.cl_208_3_impact_factor(s))
            return f"{1.0 + im:.3f}"
        except Exception:
            return "N/A"

    # ---- Vehicle rows ----
    veh_rows = []

    selected_vehicles = [
        (label, key, total, kind, braking)
        for label, key, total, kind, braking in _VEH
        if input_dict.get(key)
    ]

    for i, (label, key, total, kind, braking) in enumerate(selected_vehicles):
        yes = braking and _braking_kN is not None

        # Prevent a page break immediately before Class Fatigue
        row_break = (
            r" \\*[2pt]"
            if (
                i + 1 < len(selected_vehicles)
                and selected_vehicles[i + 1][0] == "Class Fatigue"
            )
            else r" \\[2pt]"
        )

        veh_rows.append(
            _tex(label) + " & " + total + " & " + _impact(kind) + " & "
            + ("Yes" if yes else "No") + " & "
            + (f"{_braking_kN:.2f}" if yes else "--") + " & "
            + (styles.BRAKING_ECCENTRICITY_M if yes else "--")
            + row_break + "\n" + r"\hline"
        )

    custom_rows = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom_rows and isinstance(custom_rows, list):
        for c in custom_rows:
            name = c.get('name') if isinstance(c, dict) else c
            if name:
                veh_rows.append(
                    _tex(str(name))
                    + r" & N/A & N/A & N/A & -- & -- \\[2pt]"
                    + "\n" + r"\hline"
                )

    if not veh_rows:
        veh_rows.append(
            r"\multicolumn{6}{|c|}{No vehicle class selected} \\[6pt]"
            + "\n" + r"\hline"
        )

    veh_rows_str = "\n".join(veh_rows)

    # ---- Footpath pressure ----
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m² (IRC 6 Cl. 206.1)"
        except Exception:
            fp_str = "N/A"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m²"
    else:
        fp_str = "N/A"

    fp_table = ""
    if fp_str != "N/A":
        fp_table = (
            r"""
\vspace{1em}
\begin{longtable}{""" + styles.LL_FOOTPATH_COLSPEC + r"""}
\caption{\textbf{Footpath Live Load}}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Reference} \\
\hline
\endfirsthead
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Reference} \\
\hline
\endhead
\textnormal{Footpath Pressure} & """ + _tex(fp_str.split(" (")[0]) + r""" & """
            + (r"IRC 6 Cl. 206.1" if "IRC 6" in fp_str else "User-defined") + r""" \\[6pt]
\hline
\end{longtable}
"""
        )

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
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

    # Format wind values for display.
    # The units are added in the LaTeX table below.
    vz_display = f"{float(vz_val):.2f}" if vz_val not in (None, "") else "N/A"
    pz_display = f"{float(pz_val):.2f}" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {
                "Type I – Rocky or Hard": 1,
                "Type II – Medium Soil": 2,
                "Type III – Soft Soil": 3
            }
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}",
                soil_type=_st,
                dead_load_kN=_dead,
                live_load_kN=_live,
                period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp)
            )
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax), float(_tmin), 'metallic', False
            )
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load': 'DL',
        'surfacing': 'SIDL',
        'live_load': 'LL',
        'wind_load': 'WL',
        'thermal_load': 'TL',
        'vehicle_collision': 'VC',
        'barge_impact': 'BI',
        'floating_bodies': 'FB',
        'seismic': 'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
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

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\clearpage
\begin{longtable}{""" + styles.LL_VEHICLE_COLSPEC + r"""}
\caption{\textbf{Live Loads (LL) --- Vehicles}}\\
\hline
\textbf{Vehicle} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
& & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity (m)} \\
\hline
\endfirsthead
\hline
\textbf{Vehicle} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
& & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity (m)} \\
\hline
\endhead
""" + veh_rows_str + r"""
\end{longtable}
\noindent\textit{Note: Impact factor per IRC 6 Cl. 208.2 (Class A) and Cl. 208.3 (Class AA/70R). Braking force per IRC 6 Cl. 211.2, acting 1.2 m above the road surface. Centrifugal force is not applicable for a straight bridge.}
""" + fp_table + r"""

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict, 'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + vz_display + (r""" m/s""" if vz_display != "N/A" else "") + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + pz_display + (r""" N/m\textsuperscript{2}""" if pz_display != "N/A" else "") + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, 'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + _sl(sl_zone_factor) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + _sl(sl_spectral) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + _sl(sl_ah) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + _sl(sl_av) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & N/A \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & N/A \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}"""