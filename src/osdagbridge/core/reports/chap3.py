# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for OsdagBridge LaTeX Report Enhancement
# - Separate vehicle live load and footpath live load tables
# - Grouped multi-column Live Loads table matching IRC 6 specification
# - Repeated table headers across all longtables
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
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
from osdagbridge.core.reports.styles import build_longtable_header


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    span = input_dict.get(KEY_SPAN)
    span_m = 0.0
    if span not in (None, ""):
        try:
            span_m = float(span)
        except Exception:
            span_m = 0.0

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = "N/A"
    braking_val_kn = "---"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
            braking_val_kn = f"{braking_force_kN:.2f}"
        except Exception:
            braking_force_str = "N/A"
            braking_val_kn = "---"

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Structure Dynamic Live Loads Table Rows (per UI selections)
    # Matching the exact schema required in the Google Doc specification:
    # Vehicle | Total Load (kN) | Impact Factor | Braking Considered? | Braking Value | Eccentricity
    # ─────────────────────────────────────────────────────────────────────────
    vehicle_rows = []

    # Calculate Impact Factors
    im_a = 0.0
    im_aa = 0.0
    if span_m > 0:
        try:
            im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
            im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
        except Exception:
            pass

    # Check which vehicles were selected in the UI
    has_class_a = bool(input_dict.get(KEY_LL_IRC_CLASS_A))
    has_70r_w   = bool(input_dict.get(KEY_LL_IRC_70R_WHEELED))
    has_70r_t   = bool(input_dict.get(KEY_LL_IRC_70R_TRACKED))
    has_70r_b   = bool(input_dict.get(KEY_LL_IRC_70R_BOGIE))
    has_aa_w    = bool(input_dict.get(KEY_LL_IRC_AA_WHEELED))
    has_aa_t    = bool(input_dict.get(KEY_LL_IRC_AA_TRACKED))
    has_sv      = bool(input_dict.get(KEY_LL_IRC_CLASS_SV))
    has_fatigue = bool(input_dict.get(KEY_LL_IRC_CLASS_FATIGUE))

    # Fallback to standard design vehicles if none checked
    if not any([has_class_a, has_70r_w, has_70r_t, has_70r_b, has_aa_w, has_aa_t, has_sv, has_fatigue]):
        has_class_a = True
        has_70r_w = True

    if has_class_a:
        if_val = f"{1.0 + im_a:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class A & 554 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_70r_w:
        if_val = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class 70R (Wheeled) & 1000 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_70r_t:
        if_val = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class 70R (Tracked) & 700 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_70r_b:
        if_val = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class 70R (Bogie) & 400 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_aa_w:
        if_val = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class AA (Wheeled) & 400 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_aa_t:
        if_val = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.000"
        vehicle_rows.append(
            f"Class AA (Tracked) & 700 & {if_val} & Yes & {braking_val_kn} & 1.20 m \\\\\n\\hline"
        )
    if has_sv:
        vehicle_rows.append(
            f"Class SV (Special Vehicle) & 3850 & 1.000 & No & --- & --- \\\\\n\\hline"
        )
    if has_fatigue:
        vehicle_rows.append(
            f"Class Fatigue & 400 & 1.000 & No & --- & --- \\\\\n\\hline"
        )

    # Custom vehicles
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name', 'Custom') if isinstance(c, dict) else str(c)
            c_load = str(c.get('load', '---')) if isinstance(c, dict) else "---"
            vehicle_rows.append(
                f"{_tex(c_name)} & {_tex(c_load)} & 1.000 & No & --- & --- \\\\\n\\hline"
            )

    vehicle_rows_tex = "\n".join(vehicle_rows)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Footway / Pedestrian Live Load Specification
    # ─────────────────────────────────────────────────────────────────────────
    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH, "---")
    has_footpath = str(input_dict.get(KEY_FOOTPATH, "")).strip().lower() in ("yes", "true", "1")

    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m²"
            fp_clause = "IRC 6:2017 Clause 206.1"
        except Exception:
            fp_str = "4.000 kN/m²"
            fp_clause = "IRC 6:2017 Clause 206.1"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m²"
        fp_clause = "User Specified Intensity"
    else:
        fp_str = "4.000 kN/m² (Default)" if has_footpath else "Not Applicable (No Footpath)"
        fp_clause = "IRC 6:2017 Clause 206.1" if has_footpath else "---"

    fp_status = "Provided and Designed" if has_footpath else "Not Applicable / None"

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Wind Load Analysis (IRC 6 Table 12)
    # ─────────────────────────────────────────────────────────────────────────
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
            if _h and _vb:
                _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
                if not vz_val:
                    vz_val = _res.get("Vz")
                if not pz_val:
                    pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Seismic Analysis (IRC 6 Clause 218)
    # ─────────────────────────────────────────────────────────────────────────
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
            _res  = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                live_load_kN=_live, period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp)
            )
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

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Temperature Load (IRC 6 Clause 215)
    # ─────────────────────────────────────────────────────────────────────────
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

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Load Combinations (IRC 6 Table B.1 to B.4)
    # ─────────────────────────────────────────────────────────────────────────
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
            f"ULS-{i:02d} & {cases} \\\\[6pt]\n\\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d} & {cases} \\\\[6pt]\n\\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    # ─────────────────────────────────────────────────────────────────────────
    # Return Chapter 3 Document Structure
    # ─────────────────────────────────────────────────────────────────────────
    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all gravity, traffic, lateral, environmental, and thermal loads applied to the bridge structure, together with governing load combinations defined in accordance with IRC:6-2017.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load --- Self Weight}} \label{tab:dead-load} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Dead Load --- Self Weight (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
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
\caption{\textbf{Superimposed Dead Load (SIDL) --- Surfacing \& Fixtures}} \label{tab:sidl} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Superimposed Dead Load (SIDL) (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Wearing Course Material / Thickness} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" $\times$ """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Crash Barrier Load} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{3.6cm}|C{2.4cm}|C{2.4cm}|C{2.2cm}|C{2.2cm}|C{2.2cm}|}
\caption{\textbf{Vehicle Live Loads (LL) --- IRC:6-2017 Specification}} \label{tab:live-loads} \\
\hline
\multirow{2}{*}{\textbf{Vehicle}} & \multirow{2}{*}{\textbf{Total Load (kN)}} & \multirow{2}{*}{\textbf{Impact Factor}} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
& & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\
\hline
\endfirsthead
\multicolumn{6}{c}{\small\textit{Vehicle Live Loads (LL) (Continued)}} \\[4pt]
\hline
\multirow{2}{*}{\textbf{Vehicle}} & \multirow{2}{*}{\textbf{Total Load (kN)}} & \multirow{2}{*}{\textbf{Impact Factor}} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
& & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\
\hline
\endhead
\hline
\multicolumn{6}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
""" + vehicle_rows_tex + r"""
\end{longtable}
\noindent\textit{Note: Dynamic vehicles populated as selected in the UI Loading tab. Impact factors calculated per IRC:6-2017 Cl. 208 for steel/composite bridge spans. Longitudinal braking forces applied 1.20 m above road surface per Cl. 211.}

\vspace{1em}
\begin{longtable}{|L{6.0cm}|p{9.5cm}|}
\caption{\textbf{Footway Live Load (Pedestrian Load) --- IRC:6-2017 Cl. 206}} \label{tab:footway-load} \\
\hline
\textbf{Parameter} & \textbf{Design Specification} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Footway Live Load (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Design Specification} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Footway Facility Status} & """ + fp_status + r""" \\[6pt]
\hline
\textnormal{Footpath Width, $w_{fp}$} & """ + _tex(str(fp_width)) + r""" m \\[6pt]
\hline
\textnormal{Design Pedestrian Pressure} & """ + _tex(fp_str) + r""" \\[6pt]
\hline
\textnormal{Reference Code Clause} & """ + fp_clause + r""" \\[6pt]
\hline
\textnormal{Coexistent Traffic Live Load Reduction} & IRC:6-2017 Cl. 206.3 applied where footway is considered together with carriageway live loads. \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- IRC:6-2017 Cl. 209}} \label{tab:wind-load} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Wind Load (WL) (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Basic Wind Speed, $V_b$} & """ + (_render_value(input_dict, 'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, $H$} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, $V_z$} & """ + vz_str + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, $P_z$} & """ + pz_str + r""" \\[6pt]
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
\caption{\textbf{Earthquake Load (EL) --- IRC:6-2017 Cl. 219 \& IRC:SP:114}} \label{tab:seismic-load} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Earthquake Load (EL) (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, 'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, $Z$} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, $I$} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Response Acceleration Coeff., $S_a/g$} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coeff., $A_h$} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coeff., $A_v$} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- IRC:6-2017 Cl. 215}} \label{tab:temp-load} \\
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Temperature Load (TL) (Continued)}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict, 'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Design Temperature Rise / Fall} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations (ULS \& SLS) --- IRC:6-2017 Table B.1--B.4}} \label{tab:load-combos} \\
\hline
\textbf{Combination ID} & \textbf{Factored Load Components} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Load Combinations (Continued)}} \\[4pt]
\hline
\textbf{Combination ID} & \textbf{Factored Load Components} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page...}} \\
\endfoot
\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}
\noindent\textit{Note: All combinations derived from IRC:6-2017 for Ultimate Limit State (ULS) and Serviceability Limit State (SLS).}
"""
