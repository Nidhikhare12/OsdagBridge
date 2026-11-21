# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored per FOSSEE Winter Internship Requirements:
# - Split merged Table 3.2 into:
#     (A) Vehicular Live Loads with grouped braking headers via multirow
#     (B) Centrifugal forces (IRC 6 Cl. 212)
#     (C) Footpath live load (IRC 6 Cl. 206)
# - Repeating headers across page breaks (endfirsthead, endhead, endfoot, endlastfoot)
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
from osdagbridge.core.reports.tables import (
    build_vehicle_live_load_table,
    build_centrifugal_force_table,
    build_footway_live_load_table,
    build_longtable,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span) if span not in (None, "") else 24.0
    except (ValueError, TypeError):
        span_m = 24.0

    lanes_val = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    try:
        lanes_count = int(lanes_val) if lanes_val not in (None, "") else 2
    except (ValueError, TypeError):
        lanes_count = 2

    # Vz / Pz - prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _vb_f = float(_vb) if _vb else 33.0
            _h = float(input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT) or 10.0)
            _t = input_dict.get(KEY_WL_TERRAIN_TYPE) or 'Category 2'
            _w_res = IRC6_2017.table_12(_h, _t, _vb_f)
            if not vz_val:
                input_dict[KEY_WL_HOURLY_MEAN_WIND] = f"{_w_res['Vz']:.2f}"
            if not pz_val:
                input_dict[KEY_WL_HOURLY_WIND_PRESSURE] = f"{_w_res['Pz']:.2f}"
        except Exception:
            pass

    # Horizontal and vertical seismic forces (longitudinal and transverse)
    try:
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import (
            calculate_seismic_longitudinal_and_transverse
        )
        seis_forces = calculate_seismic_longitudinal_and_transverse(input_dict)
        h_long = f"{seis_forces.get('horizontal_longitudinal_kN', 0.0):.2f}"
        h_trans = f"{seis_forces.get('horizontal_transverse_kN', 0.0):.2f}"
    except Exception:
        h_long = ""
        h_trans = ""

    t_rise = input_dict.get(KEY_TL_TEMP_RISE)
    t_fall = input_dict.get(KEY_TL_TEMP_FALL)
    if t_rise is not None and t_fall is not None and str(t_rise).strip() != '' and str(t_fall).strip() != '':
        _temp_rf_str = f"+{t_rise} $^\\circ$C / -{t_fall} $^\\circ$C"
    elif t_rise is not None and str(t_rise).strip() != '':
        _temp_rf_str = f"+{t_rise} $^\\circ$C"
    elif t_fall is not None and str(t_fall).strip() != '':
        _temp_rf_str = f"-{t_fall} $^\\circ$C"
    else:
        _temp_rf_str = "-"

    # Load Combinations
    _CASE_NAMES = {
        'dead_load': 'DL',
        'surfacing': 'DW',
        'live_load': 'LL',
        'wind_load': 'WL',
        'seismic_load': 'EL',
        'temperature': 'TL',
    }

    def _fmt_factors(factors_dict):
        parts = []
        for case_key, label in _CASE_NAMES.items():
            val = factors_dict.get(case_key)
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '-'
                rel_s = f"{rel:.2f}" if rel is not None else '-'
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

    # Build Refactored Live Load, Centrifugal, and Footway tables (Requirement 3)
    vehicular_live_load_table = build_vehicle_live_load_table(input_dict, span_m, lanes_count)
    centrifugal_table = build_centrifugal_force_table(input_dict)
    footway_table = build_footway_live_load_table(input_dict)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all permanent, transient, and environmental loads applied to the bridge and the governing load combinations considered for structural analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load - Self Weight (DL)}}\label{tab:dead-load-self-weight} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Dead Load - Self Weight (DL) (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
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
\caption{\textbf{Dead Load for Surfacing and Superimposed Dead Load (DW)}}\label{tab:dead-load-surfacing} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Dead Load for Surfacing and Superimposed Dead Load (DW) (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Wearing Course Load} & """ + ((_render_value(input_dict, KEY_WC_MATERIAL) or 'Concrete') + ', ' + (_render_value(input_dict, KEY_WC_THICKNESS) or '50.0') + ' mm thickness') + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\clearpage
""" + vehicular_live_load_table + r"""

\vspace{1em}
""" + centrifugal_table + r"""

\vspace{1em}
""" + footway_table + r"""

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) - per IRC 6}}\label{tab:wind-load} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Wind Load (WL) - per IRC 6 (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict, 'wind_speed', ' m/s') or _render_value(input_dict, KEY_WL_BASIC_WIND_SPEED, ' m/s') or "-") + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE) or "Category 2") + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m') or "10.0 m") + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s') or "-") + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}') or "-") + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN') or "-") + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN') or "-") + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN') or "-") + r""" \\[6pt]
\hline
\end{longtable}

\clearpage
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) - per IRC 6}}\label{tab:earthquake-load} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Earthquake Load (EL) - per IRC 6 (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, 'seismic_zone') or _render_value(input_dict, KEY_SL_SEISMIC_ZONE) or "-") + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR) or "-") + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR) or "1.2") + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE) or "Type II (Medium)") + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF) or "-") + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF) or "-") + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF) or "-") + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + (f"{h_long} kN" if (h_long and h_long != "0.00") else "-") + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + (f"{h_trans} kN" if (h_trans and h_trans != "0.00") else "-") + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\needspace{7\baselineskip}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) - per IRC 6}}\label{tab:temperature-load} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Temperature Load (TL) - per IRC 6 (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Maximum Shade Temperature} & """ + ((_render_value(input_dict,'shade_temp_max') + r" $^\circ$C") if _render_value(input_dict,'shade_temp_max') else "-") + r""" \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + ((_render_value(input_dict,'shade_temp_min') + r" $^\circ$C") if _render_value(input_dict,'shade_temp_min') else "-") + r""" \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + ((_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) + r" to " + _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX) + r" $^\circ$C") if (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) and _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) else "-") + r""" \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & """ + _temp_rf_str + r""" \\[6pt]
\hline
\end{longtable}

\clearpage
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}\label{tab:load-combinations} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Combination ID} & \textbf{Load Cases} \\*[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Load Combinations (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Combination ID} & \textbf{Load Cases} \\*[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge in accordance with Table B.2 (ULS) and Table B.3 (SLS).}
"""
