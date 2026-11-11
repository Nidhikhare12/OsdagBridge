# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored with separate Vehicular and Footway Live Load tables,
# PyLaTeX LongTable repeating headers, and engineering parameter columns.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_FOOTPATH,
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

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.report_data import selected, numeric
from osdagbridge.core.reports.styles import TABCOLSEP, ARRAYSTRETCH

def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    span = input_dict.get(KEY_SPAN)
    span_m = None
    if span not in (None, ""):
        try:
            span_m = float(span)
        except Exception:
            span_m = None

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    lanes_int = None
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
        except Exception:
            lanes_int = None

    # Calculate standard braking force per IRC 6 Cl. 211
    try:
        braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_force_kN = braking_force_t * 9.81
    except Exception:
        braking_force_kN = None

    # Impact factors per IRC 6 Cl. 208
    try:
        im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
        impact_a_str = f"{1.0 + im_a:.3f}"
    except Exception:
        impact_a_str = "Not available"

    try:
        im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        impact_heavy_str = f"{1.0 + im_aa:.3f}"
    except Exception:
        impact_heavy_str = "Not available"

    # ── 1. Vehicular Live Load Rows ──────────────────────────────────────────
    # Check each vehicle explicitly based on UI input_dict selection
    vehicle_rows = []
    
    if selected(input_dict.get(KEY_LL_IRC_CLASS_A)):
        vehicle_rows.append(
            r"IRC Class A & " + impact_a_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_70R_WHEELED)):
        vehicle_rows.append(
            r"IRC Class 70R (Wheeled) & " + impact_heavy_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_70R_TRACKED)):
        vehicle_rows.append(
            r"IRC Class 70R (Tracked) & " + impact_heavy_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_AA_WHEELED)):
        vehicle_rows.append(
            r"IRC Class AA (Wheeled) & " + impact_heavy_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_AA_TRACKED)):
        vehicle_rows.append(
            r"IRC Class AA (Tracked) & " + impact_heavy_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_CLASS_SV)):
        vehicle_rows.append(
            r"IRC Special Vehicle (Class SV) & Not available & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_70R_BOGIE)):
        vehicle_rows.append(
            r"IRC Class 70R (Bogie) & " + impact_heavy_str + r" & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )
    if selected(input_dict.get(KEY_LL_IRC_CLASS_FATIGUE)):
        vehicle_rows.append(
            r"IRC Fatigue Vehicle & Not available & -- & -- & Selected per IRC 6 Cl. 204 \\" + "\n" + r"\hline"
        )

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get('name', 'Custom Vehicle') if isinstance(c, dict) else str(c)
            vehicle_rows.append(
                _tex(name) + r" & Not available & " + (f"{braking_force_kN:.2f}" if braking_force_kN is not None else "Not available") + r" & Not available & Custom User Vehicle \\" + "\n" + r"\hline"
            )

    if not vehicle_rows:
        vehicle_rows_str = r"No Vehicular Live Load & Not applicable & Not applicable & Not applicable & Not Selected in UI \\" + "\n" + r"\hline"
    else:
        vehicle_rows_str = "\n".join(vehicle_rows)

    # ── 2. Footway Live Load Parameters ──────────────────────────────────────
    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")).strip()
    fp_value = numeric(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
    if fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_value = numeric(IRC6_2017.cl_206_1_footway_load())
        except Exception:
            fp_value = None
    footpath_type = str(input_dict.get(KEY_FOOTPATH, "")).strip().lower()
    width = numeric(input_dict.get(KEY_TS_FOOTPATH_WIDTH))
    if footpath_type in ("none", "no", "0"):
        fp_intensity = fp_width_str = fp_linear_kN_m = "Not applicable"
    else:
        fp_intensity = f"{fp_value:.2f}" if fp_value is not None else "Not available"
        fp_width_str = f"{width:.2f} per side" if width is not None else "Not available"
        fp_linear_kN_m = f"{fp_value * width:.2f} per side" if fp_value is not None and width is not None else "Not available"

    # Vz / Pz Wind
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

    # Table 3.5 Seismic
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

    # Table 3.7: Load Combinations
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
\label{ch:loads}

This chapter summarizes all dead, live, environmental, and thermal loads applied to the bridge structure, together with the design limit state load combinations specified in IRC 6:2017.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight Parameters}} \label{tab:dead_load} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
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
\caption{\textbf{Dead Load for Surfacing (DW) \& Superimposed Dead Loads}} \label{tab:surfacing_load} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
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
% ── Table 3.3a: Vehicular Live Loads (Separated PyLaTeX LongTable) ──────────
\begin{longtable}{|L{4.2cm}|C{2.4cm}|C{2.8cm}|C{2.8cm}|L{3.3cm}|}
\caption{\textbf{Vehicular Live Load Specifications (IRC 6:2017)}} \label{tab:vehicular_ll} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Vehicle Class} & \textbf{Impact multiplier (1 + IF)} & \textbf{Braking Load (kN)} & \textbf{Centrifugal Force (kN)} & \textbf{Selection Status} \\
\hline
\endfirsthead

\multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Vehicle Class} & \textbf{Impact multiplier (1 + IF)} & \textbf{Braking Load (kN)} & \textbf{Centrifugal Force (kN)} & \textbf{Selection Status} \\
\hline
\endhead

\hline
\multicolumn{5}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

""" + vehicle_rows_str + r"""
\end{longtable}

\vspace{1em}
% ── Table 3.3b: Footway / Pedestrian Live Load (Separated Table) ───────────
\begin{longtable}{|L{5.5cm}|C{3.0cm}|C{2.5cm}|L{4.5cm}|}
\caption{\textbf{Footway / Footpath Live Load Parameters (IRC 6 Cl. 206)}} \label{tab:footway_ll} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value} & \textbf{Unit} & \textbf{IRC Reference / Description} \\
\hline
\endfirsthead

\multicolumn{4}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value} & \textbf{Unit} & \textbf{IRC Reference / Description} \\
\hline
\endhead

\hline
\multicolumn{4}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

Applied Pedestrian Live Load Intensity & """ + fp_intensity + r""" & kN/m\textsuperscript{2} & """ + _tex(fp_mode or "Mode not supplied") + r""" \\
\hline
Footpath Effective Width & """ + fp_width_str + r""" & m & Pedestrian Walkway Width \\
\hline
Uniform Linear Footpath Force & """ + fp_linear_kN_m + r""" & kN/m & Linear grillage line load \\
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}} \label{tab:wind_load} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
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
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}} \label{tab:seismic_load} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
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
\textnormal{Horizontal Seismic Force (longitudinal)} & Not available \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & Not available \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}} \label{tab:temp_load} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Parameter} & \textbf{Design Value / Specification} \\
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}} \label{tab:load_combos} \\
\hline
\rowcolor{tableHeaderBg} \textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead

\multicolumn{2}{c}{{\bfseries \tablename\ \thetable{} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{tableHeaderBg} \textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead

\hline
\multicolumn{2}{r}{{\footnotesize \textit{Continued on next page\ldots}}} \\
\endfoot

\hline
\endlastfoot

""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
