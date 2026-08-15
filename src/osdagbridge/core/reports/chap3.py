# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for OsdagBridge LaTeX Report Enhancements:
#   - LongTable repeated headers across page breaks (\endfirsthead / \endhead)
#   - Separate Vehicle Live Loads and Footpath Live Loads tables
#   - Structural parameters, unit columns, and UI vehicle selection integration
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
    KEY_TS_FOOTPATH_WIDTH
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.styles import make_longtable_header, TABLE_CONFIG
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    span_m = float(span) if span not in (None, "") else 24.0

    # ── 1. Calculate vehicle live load properties per selected UI vehicles ────
    selected_vehicles = []
    
    # Impact Factors
    im_a_val = 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)
    im_aa_val = 1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)
    
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT, 2)
    try:
        lanes_int = int(lanes)
    except (ValueError, TypeError):
        lanes_int = 2
    braking_kN = IRC6_2017.cl_211_2_braking_force(lanes_int) * 9.81

    # Vehicle rows build
    v_rows = []
    if input_dict.get(KEY_LL_IRC_CLASS_A, True):  # Default Class A on if not set
        v_rows.append(
            f"Class A & 114.0 & {im_a_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.1 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        v_rows.append(
            f"Class 70R (Wheeled) & 170.0 & {im_aa_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.2 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        v_rows.append(
            f"Class 70R (Tracked) & 350.0 (Track) & {im_aa_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.2 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        v_rows.append(
            f"Class AA (Wheeled) & 200.0 & {im_aa_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.3 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        v_rows.append(
            f"Class AA (Tracked) & 350.0 (Track) & {im_aa_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.3 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        v_rows.append(
            f"Class SV & 400.0 & 1.000 & {braking_kN:.2f} & IRC:6-2017 Annex A \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        v_rows.append(
            f"Class 70R (Bogie) & 200.0 & {im_aa_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.2 \\\\\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        v_rows.append(
            f"Class Fatigue & 114.0 & 1.000 & N/A & IRC:6-2017 Cl. 204.4 \\\\\n\\hline"
        )
        
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get('name') if isinstance(c, dict) else str(c)
            v_rows.append(
                f"{_tex(name)} & Custom & 1.000 & N/A & User Defined \\\\\n\\hline"
            )

    if not v_rows:  # Fallback if no vehicle checked
        v_rows.append(
            f"Class A & 114.0 & {im_a_val:.3f} & {braking_kN:.2f} & IRC:6-2017 Cl. 204.1 \\\\\n\\hline"
        )
    vehicle_table_body = "\n".join(v_rows)

    # ── 2. Footway Live Load Parameters ──────────────────────────────────────
    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH, 1.5)

    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic", ""):
        try:
            fp_intensity = IRC6_2017.cl_206_1_footway_load()
            fp_ref = "IRC:6-2017 Cl. 206.1 (Auto)"
        except Exception:
            fp_intensity = 5.0
            fp_ref = "IRC:6-2017 Cl. 206.1"
    elif fp_value not in (None, ""):
        fp_intensity = float(fp_value)
        fp_ref = "User Defined Input"
    else:
        fp_intensity = 5.0
        fp_ref = "IRC:6-2017 Cl. 206.1"

    try:
        fp_w_float = float(fp_width)
    except (ValueError, TypeError):
        fp_w_float = 1.5

    fp_linear_load = fp_intensity * fp_w_float

    # ── 3. Wind Load Parameters ──────────────────────────────────────────────
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed', 47)
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT, 10)
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

    # ── 4. Seismic Load Parameters ───────────────────────────────────────────
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone', '3')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z, "III")
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

    # ── 5. Temperature Load Parameters ───────────────────────────────────────
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

    # ── 6. Load Combinations Table ───────────────────────────────────────────
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
        lc_rows.append(f"ULS-{i:02d} & {cases} \\\\[6pt]\n\\hline")
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"SLS-{i:02d} & {cases} \\\\[6pt]\n\\hline")

    lc_rows_str = "\n".join(lc_rows)

    # ── Table Headers using styles.py LongTable Header Generator ──────────────
    hdr_t3_1 = make_longtable_header("Dead Load --- Self Weight", ["Parameter", "Value"], "|L{5.5cm}|p{10.0cm}|")
    hdr_t3_2 = make_longtable_header("Dead Load for Surfacing (DW)", ["Parameter", "Value"], "|L{5.5cm}|p{10.0cm}|")
    hdr_t3_3a = make_longtable_header("Vehicle Live Loads (LL) --- IRC:6-2017", ["Vehicle Class", "Max Axle/Track (kN)", "Impact Factor", "Braking Force (kN)", "Code Reference"], "|L{3.2cm}|C{3.2cm}|C{2.5cm}|C{2.8cm}|L{3.5cm}|")
    hdr_t3_3b = make_longtable_header("Footway & Pedestrian Live Loads", ["Parameter", "Value", "Unit", "Code Reference"], "|L{4.5cm}|C{3.0cm}|C{2.5cm}|L{5.2cm}|")
    hdr_t3_4 = make_longtable_header("Wind Load (WL) --- per IRC 6", ["Parameter", "Value"], "|L{5.5cm}|p{10.0cm}|")
    hdr_t3_5 = make_longtable_header("Earthquake Load (EL) --- per IRC 6", ["Parameter", "Value"], "|L{5.5cm}|p{10.0cm}|")
    hdr_t3_6 = make_longtable_header("Temperature Load (TL) --- per IRC 6", ["Parameter", "Value"], "|L{5.5cm}|p{10.0cm}|")
    hdr_t3_7 = make_longtable_header("Load Combinations", ["Combination ID", "Load Cases"], "|C{3.5cm}|p{12.0cm}|")

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all environmental, gravity, vehicle live loads, footway live loads, and design load combinations applied to the bridge per IRC 6:2017.

\vspace{1em}
""" + hdr_t3_1 + r"""
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR, '')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + hdr_t3_2 + r"""
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD, ' kN/m per barrier')) + r""" \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE, ' kN/m')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + hdr_t3_3a + f"""
{vehicle_table_body}
\\end{{longtable}}

\\vspace{{1em}}
""" + hdr_t3_3b + f"""
\\textnormal{{Footpath Pressure Intensity}} & {fp_intensity:.3f} & kN/m\\textsuperscript{{2}} & {fp_ref} \\\\[6pt]
\\hline
\\textnormal{{Effective Footpath Width}} & {fp_w_float:.2f} & m & IRC:6-2017 Cl. 206.1 \\\\[6pt]
\\hline
\\textnormal{{Total Footpath Linear Load}} & {fp_linear_load:.3f} & kN/m & Computed (Intensity $\\times$ Width) \\\\[6pt]
\\hline
\\end{{longtable}}

\\vspace{{1em}}
""" + hdr_t3_4 + r"""
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
""" + hdr_t3_5 + r"""
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
\end{longtable}

\vspace{1em}
""" + hdr_t3_6 + r"""
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
""" + hdr_t3_7 + f"""
{lc_rows_str}
\\end{{longtable}}

\\noindent\\textit{{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}}
"""
