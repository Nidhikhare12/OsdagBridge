from osdagbridge.core.reports.styles import STYLE
# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
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
    span = input_dict.get(KEY_SPAN) or input_dict.get('span') or input_dict.get('geometry.span')
    span_m = None
    if span not in (None, ""):
        try:
            span_m = float(span)
        except Exception:
            span_m = None

    # --- Per-vehicle data for the structured Live Load table ---
    # Each entry: (key, label, total_load_kN_str, is_class_a_impact, is_aa_impact, braking_yes)
    _VEHICLE_SPECS = [
        (KEY_LL_IRC_CLASS_A,       "Class A",             "543.5",                 True,  False, True),
        (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)", "981.0",                 False, True,  True),
        (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)", "686.7 (75.1 kN/m UDL)", False, True,  True),
        (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",   "392.4",                 False, True,  True),
        (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",  "686.7",                 False, True,  True),
        (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",  "686.7",                 False, True,  True),
        (KEY_LL_IRC_CLASS_SV,      "Class SV",            "Annex B (Special)",     False, False, False),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",       "392.4",                 False, False, False),
    ]

    # Compute impact factors (computed once per span)
    _im_a_str   = "N/A"
    _im_aa_str  = "N/A"
    if span_m is not None:
        try:
            im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
            _im_a_str = f"{1.0 + im_a:.3f}"
        except Exception:
            pass
        try:
            im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
            _im_aa_str = f"{1.0 + im_aa:.3f}"
        except Exception:
            pass

    # Braking force (single value for all lanes, shared across vehicles)
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT) or input_dict.get('number_of_lanes') or input_dict.get('lanes') or 2
    _braking_kN_str = "N/A"
    _braking_t_str  = "N/A"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t   = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN  = braking_force_t * 9.81
            _braking_kN_str   = f"{braking_force_kN:.2f}"
            _braking_t_str    = f"{braking_force_t:.2f} t"
        except Exception:
            pass

    # Build per-vehicle rows for the LL table
    # Columns: Vehicle | Total Load (kN) | Impact Factor | Braking Considered? | Braking Value (kN) | Braking Eccentricity
    _braking_loc_m = "1.2 m above road"  # IRC 6 Cl.211.3: braking acts 1.2 m above roadway
    _ll_rows = []
    for key, label, total_load, is_a_if, is_aa_if, braking_yes in _VEHICLE_SPECS:
        if not input_dict.get(key):
            continue
        if key == KEY_LL_IRC_CLASS_SV:
            braking_yes = bool(input_dict.get(KEY_BL_IRC_CLASS_SV, False))
        _if_str = _im_a_str if is_a_if else (_im_aa_str if is_aa_if else "N/A")
        _br_yes = "Yes" if braking_yes else "No"
        _br_val = _braking_kN_str if braking_yes else "---"
        _br_ecc = _braking_loc_m if braking_yes else "---"
        _ll_rows.append(
            r"\textnormal{" + label + r"} & \textnormal{" + total_load + r"} & "
            + _if_str + r" & " + _br_yes + r" & " + _br_val + r" & \textnormal{" + _br_ecc + r"} \\[6pt]" + "\n"
            + r"\hline"
        )

    # Custom vehicles (no formula for load/impact — show as "Custom")
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            lbl = c.get('name', 'Custom') if isinstance(c, dict) else str(c)
            _ll_rows.append(
                r"\textnormal{" + lbl + r"} & Custom & N/A & Yes & " + _braking_kN_str + r" & \textnormal{" + _braking_loc_m + r"} \\[6pt]" + "\n"
                + r"\hline"
            )

    if not _ll_rows:
        _ll_rows.append(
            r"\multicolumn{6}{|c|}{\textnormal{No live load vehicles selected}} \\[6pt]" + "\n"
            + r"\hline"
        )

    _ll_rows_str = "\n".join(_ll_rows)

    # Backward-compatible strings still used by other places
    impact_factor_str = ", ".join(
        ([f"Class A: {_im_a_str}"] if _im_a_str != "N/A" and input_dict.get(KEY_LL_IRC_CLASS_A) else []) +
        ([f"Class AA/70R: {_im_aa_str}"] if _im_aa_str != "N/A" and any(
            input_dict.get(k) for k in [KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_70R_TRACKED,
                                         KEY_LL_IRC_AA_WHEELED, KEY_LL_IRC_AA_TRACKED,
                                         KEY_LL_IRC_70R_BOGIE]) else [])
    ) or "N/A"
    braking_force_str = f"{_braking_kN_str} kN ({_braking_t_str})" if _braking_kN_str != "N/A" else "N/A"

    # Footpath / Footway load
    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    _fp_mode_str = str(fp_mode).strip()
    if _fp_mode_str.lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            _fp_kN = IRC6_2017.cl_206_1_footway_load()
            fp_str = f"{_fp_kN:.3f} kN/m\\textsuperscript{{2}}"
            _fp_clause = "IRC 6 Cl.~206.1"
        except Exception:
            fp_str = "N/A"
            _fp_clause = "IRC 6 Cl.~206.1"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m\\textsuperscript{{2}}"
        _fp_clause = "User-defined"
    else:
        fp_str = "N/A"
        _fp_clause = "---"

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

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{3.2cm}|C{2.5cm}|C{2.2cm}|C{2.0cm}|C{2.2cm}|L{3.3cm}|}
\caption{\textbf{Vehicle Live Loads (LL) --- per IRC 6}}\\
\hline
\multirow{2}{*}{\textbf{Vehicle}} & \multirow{2}{*}{\makecell{\textbf{Total Load}\\\textbf{(kN)}}} & \multirow{2}{*}{\makecell{\textbf{Impact}\\\textbf{Factor}}} & \multicolumn{3}{c|}{\textbf{Braking Load (IRC 6 Cl.~211)}} \\*[2pt]
\cline{4-6}
 &  &  & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\[4pt]
\hline
\endfirsthead
\hline
\multirow{2}{*}{\textbf{Vehicle}} & \multirow{2}{*}{\makecell{\textbf{Total Load}\\\textbf{(kN)}}} & \multirow{2}{*}{\makecell{\textbf{Impact}\\\textbf{Factor}}} & \multicolumn{3}{c|}{\textbf{Braking Load (IRC 6 Cl.~211)}} \\*[2pt]
\cline{4-6}
 &  &  & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\[4pt]
\hline
\endhead
""" + _ll_rows_str + r"""
\end{longtable}
\noindent\textit{Note: Centrifugal forces are zero for straight bridge alignment (IRC 6 Cl.~212). Impact factors per IRC 6 Cl.~208. Braking force acts 1.2\,m above road level (IRC 6 Cl.~211.3). Span\,=\,} """ + (f"{span_m:.1f}" if span_m is not None else "N/A") + r"""\,m.

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|C{3.5cm}|p{5.5cm}|}
\caption{\textbf{Footpath / Footway Live Load --- per IRC 6}}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Reference} \\[4pt]
\hline
\endfirsthead
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Reference} \\[4pt]
\hline
\endhead
\textnormal{Footway Intensity} & """ + fp_str + r""" & """ + _fp_clause + r""" \\[6pt]
\hline
\textnormal{Mode} & \textnormal{""" + (str(fp_mode).strip() if fp_mode else "N/A") + r"""} & --- \\[6pt]
\hline
\end{longtable}

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
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

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
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
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\hline
\end{longtable}

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

""" + STYLE.lt_needspace_tex() + r"""
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}\\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


