# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_FOOTPATH,
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
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
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
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    span_m = float(span) if span not in (None, "") else 30.0

    # Traffic Lanes & Carriageway Width
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    try:
        lanes_int = int(lanes) if lanes not in (None, "") else 2
        braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_force_kN = braking_force_t * 9.81
        braking_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} t)"
    except Exception:
        lanes_int = 2
        braking_str = "N/A"

    cw = input_dict.get(KEY_CARRIAGEWAY_WIDTH) or input_dict.get("carriageway_width")
    cw_str = f"{float(cw):.2f} m" if cw not in (None, "") else "N/A"
    lanes_str = str(lanes_int)

    # Table 3.1: Vehicular Live Loads breakdown
    selected_vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
        selected_vehicles.append(("Class A", f"{1.0 + im_a:.3f}"))
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        selected_vehicles.append(("Class 70R (Wheeled)", f"{1.0 + im_aa:.3f}"))
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        selected_vehicles.append(("Class 70R (Tracked)", f"{1.0 + im_aa:.3f}"))
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        selected_vehicles.append(("Class AA (Wheeled)", f"{1.0 + im_aa:.3f}"))
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        selected_vehicles.append(("Class AA (Tracked)", f"{1.0 + im_aa:.3f}"))
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        selected_vehicles.append(("Class SV", "1.000"))
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        selected_vehicles.append(("Class 70R (Bogie)", f"{1.0 + im_aa:.3f}"))
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        selected_vehicles.append(("Class Fatigue", "1.000"))

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name') if isinstance(c, dict) else str(c)
            if c_name:
                selected_vehicles.append((c_name, "1.000"))

    if not selected_vehicles:
        im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
        selected_vehicles.append(("Class A (Design Vehicle)", f"{1.0 + im_a:.3f}"))

    veh_rows = []
    for v_name, v_imp in selected_vehicles:
        veh_rows.append(
            f"\\textnormal{{{_tex(v_name)}}} & {cw_str} & {lanes_str} & {v_imp} & {braking_str} & 0.00 kN (Straight) \\\\[6pt]\n\\hline"
        )
    veh_rows_str = "\n".join(veh_rows)

    # Table 3.2: Footway and Pedestrian Live Loads
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_val_in = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    fp_opt = str(input_dict.get(KEY_FOOTPATH, "")).strip().lower()
    fp_w_in = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
    n_fp_in = input_dict.get(KEY_TS_NO_OF_FOOTPATHS)

    has_footpath = fp_opt in ("single side", "both sides") or (fp_w_in not in (None, "", 0, 0.0, "0", "0.0"))
    if has_footpath and fp_opt != "none":
        try:
            fp_w = float(fp_w_in) if fp_w_in not in (None, "") else 1.5
        except Exception:
            fp_w = 1.5

        try:
            n_fp = int(n_fp_in) if n_fp_in not in (None, "") else (2 if "both" in fp_opt else 1)
        except Exception:
            n_fp = 1

        if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
            try:
                fp_q = float(IRC6_2017.cl_206_1_footway_load())
            except Exception:
                fp_q = 4.905
            fp_intensity_str = f"{fp_q:.3f} kN/m\\textsuperscript{{2}}"
        elif fp_val_in not in (None, ""):
            try:
                fp_q = float(fp_val_in)
                fp_intensity_str = f"{fp_q:.2f} kN/m\\textsuperscript{{2}}"
            except Exception:
                fp_q = 5.0
                fp_intensity_str = f"{fp_val_in} kN/m\\textsuperscript{{2}}"
        else:
            fp_q = 4.905
            fp_intensity_str = f"{fp_q:.3f} kN/m\\textsuperscript{{2}}"

        total_fp_force = fp_q * fp_w * span_m * n_fp
        fp_w_str = f"{fp_w:.2f} m" + (f" ({n_fp} side{'s' if n_fp > 1 else ''})" if n_fp > 1 else "")
        fp_total_str = f"{total_fp_force:.2f} kN"
        fp_red_str = "0.80 (with LL per Cl. 206)"
    else:
        fp_w_str = "0.00 m (None)"
        fp_intensity_str = "0.00 kN/m\\textsuperscript{2}"
        fp_total_str = "0.00 kN"
        fp_red_str = "N/A"

    fp_rows_str = f"\\textnormal{{{fp_w_str}}} & {fp_intensity_str} & {fp_total_str} & {fp_red_str} \\\\[6pt]\n\\hline"

    # Wind Load (WL)
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

    # Earthquake Load (EL)
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
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                                         live_load_kN=_live, period_T=float(_tp) if _tp else None,
                                         damping_percent=float(_damp))
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

    # Temperature Load (TL)
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # Load Combinations
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
    sls_combos = IRC6_2017.sls_combos() if hasattr(IRC6_2017, 'sls_combos') else IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n" + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n" + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|C{3.2cm}|C{2.3cm}|C{1.8cm}|C{2.5cm}|C{2.8cm}|C{2.9cm}|}
\caption{\textbf{Vehicular Live Loads (IRC 6:2017)}}\\
\hline
\textbf{Vehicle Class} & \textbf{Carriageway Width} & \textbf{No. of Lanes} & \textbf{Impact Ratio} & \textbf{Braking Force} & \textbf{Centrifugal Force} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{6}{|l|}{\small\textit{Vehicular Live Loads (IRC 6:2017) (continued from previous page)}} \\
\hline
\textbf{Vehicle Class} & \textbf{Carriageway Width} & \textbf{No. of Lanes} & \textbf{Impact Ratio} & \textbf{Braking Force} & \textbf{Centrifugal Force} \\[6pt]
\hline
\endhead

\hline
\multicolumn{6}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
""" + veh_rows_str + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{3.5cm}|C{4.0cm}|C{4.0cm}|C{4.0cm}|}
\caption{\textbf{Footway and Pedestrian Live Loads (IRC 6 Cl. 206)}}\\
\hline
\textbf{Footpath Width} & \textbf{Design Intensity} & \textbf{Total Vertical Force} & \textbf{Reduction Factor} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{4}{|l|}{\small\textit{Footway and Pedestrian Live Loads (IRC 6 Cl. 206) (continued from previous page)}} \\
\hline
\textbf{Footpath Width} & \textbf{Design Intensity} & \textbf{Total Vertical Force} & \textbf{Reduction Factor} \\[6pt]
\hline
\endhead

\hline
\multicolumn{4}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
""" + fp_rows_str + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Dead Load -- Self Weight (continued from previous page)}} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Dead Load for Surfacing (DW) (continued from previous page)}} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Wind Load (WL) --- per IRC 6 (continued from previous page)}} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict, 'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
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
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}\\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Earthquake Load (EL) --- per IRC 6 (continued from previous page)}} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, 'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Temperature Load (TL) --- per IRC 6 (continued from previous page)}} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
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
\caption{\textbf{Load Combinations}}\\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead

\hline
\multicolumn{2}{|l|}{\small\textit{Load Combinations (continued from previous page)}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{|r|}{\small\textit{Continued on next page\dots}} \\
\hline
\endfoot

\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
