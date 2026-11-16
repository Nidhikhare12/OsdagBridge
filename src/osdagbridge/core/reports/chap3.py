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
from osdagbridge.core.reports.latex.tables import ReportTable, KeyValueTable
from osdagbridge.core.reports.data.live_loads import collect_live_loads

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
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m² (IRC 6 Cl. 206.1)"
        except Exception:
            fp_str = "N/A"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m²"
    else:
        fp_str = "N/A"

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

    # 1. Dead Load - Self Weight
    t_sw = KeyValueTable(
        caption=r"\textbf{Dead Load -- Self Weight}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            ("Steel Self-Weight Applied", _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r" kN/m\textsuperscript{3}")),
            ("Concrete Deck Weight", _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r" kN/m\textsuperscript{3}")),
            ("Self-Weight Factor", _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)),
        ],
    )

    # 2. Dead Load Surfacing
    t_dw = KeyValueTable(
        caption=r"\textbf{Dead Load for Surfacing (DW)}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            ("Wearing Course Load", f"{_render_value(input_dict, KEY_WC_MATERIAL)} x {_render_value(input_dict, KEY_WC_THICKNESS)}"),
            ("Additional SIDL (Crash Barrier)", f"{_render_value(input_dict, KEY_CB_LOAD)} kN/m per barrier"),
            ("Railing Load", f"{_render_value(input_dict, KEY_RL_LOAD_VALUE)} kN/m\\sdstar{{}}"),
        ],
    )

    ll_data = collect_live_loads(input_dict)

    # 3. Vehicular Live Loads (Requirement R3)
    header_veh = r"""\hline
\multirow{2}{*}{\textbf{Vehicle Class}} & \multirow{2}{*}{\makecell{\textbf{Total Load}\\\textbf{(kN)}}} & \multirow{2}{*}{\makecell{\textbf{Impact Factor}\\\textbf{($1+IF$)}}} & \multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
 & & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\
\hline"""

    t_veh = ReportTable(
        columns=r"|L{4.2cm}|C{2.3cm}|C{2.4cm}|C{2.0cm}|C{2.2cm}|C{2.5cm}|",
        caption=r"\textbf{Vehicular Live Loads --- per IRC 6:2017}",
        header_tex=header_veh,
    )
    for v in ll_data.vehicles:
        tot_s = f"{v.total_load_kN:.1f}" if v.total_load_kN is not None else "---"
        if_s = f"{v.impact_factor:.3f}" if v.impact_factor is not None else "---"
        br_s = "YES" if v.braking_considered else "NO"
        br_v = f"{v.braking_value_kN:.2f}" if v.braking_value_kN is not None else "---"
        br_e = _tex(v.braking_eccentricity) if v.braking_eccentricity else "---"
        t_veh.add_row([_tex(v.name), tot_s, if_s, br_s, br_v, br_e])

    # 4. Footpath Live Load (Requirement R3)
    if ll_data.footpath is not None:
        int_str = f"{ll_data.footpath.intensity_kN_m2:.3f} kN/m²" if ll_data.footpath.intensity_kN_m2 is not None else "---"
        t_fp = KeyValueTable(
            caption=r"\textbf{Footpath Live Load --- per IRC 6:2017 Cl. 206}",
            preset=("5.5cm", "10.0cm"),
            headers=("Parameter", "Design Value"),
            rows=[
                ("Footway Loading Intensity", int_str),
                ("Footpath Calculation Mode", _tex(ll_data.footpath.mode)),
                ("Number of Footpaths", f"{ll_data.footpath.count}"),
                ("Footpath Width", f"{ll_data.footpath.width_m:.2f} m"),
                ("Governing Clause", _tex(ll_data.footpath.clause)),
            ],
        )
        fp_block = t_fp.dumps() + "\n"
    else:
        fp_block = r"""\noindent\textit{Note: Footpath is not provided for this bridge configuration (IRC 6:2017 Cl. 206 footway loading is not applicable).}

\vspace{0.8em}
"""

    # 4. Wind Load
    t_wl = KeyValueTable(
        caption=r"\textbf{Wind Load (WL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            ("Basic Wind Speed, Vb", f"{_render_value(input_dict, 'wind_speed', ' m/s')} [from Project Location]"),
            ("Terrain Type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE)),
            ("Average Exposed Height, H (m)", _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, " m")),
            ("Hourly Mean Wind Speed, Vz", _render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, " m/s")),
            ("Hourly Wind Pressure, Pz", _render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r" N/m\textsuperscript{2}")),
            ("Transverse Wind Force", _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")),
            ("Longitudinal Wind Force", _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")),
            ("Vertical Wind Force", _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, " kN")),
        ],
    )

    # 5. Earthquake Load
    t_el = KeyValueTable(
        caption=r"\textbf{Earthquake Load (EL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            ("Seismic Zone", f"{_render_value(input_dict, 'seismic_zone')} [from Project Location]"),
            ("Zone Factor, Z", _render_value(input_dict, KEY_SL_ZONE_FACTOR)),
            ("Importance Factor, I", _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)),
            ("Type of Soil", _render_value(input_dict, KEY_SL_SOIL_TYPE)),
            ("Sa/g", _render_value(input_dict, KEY_SL_SPECTRAL_COEFF)),
            ("Horizontal Seismic Coefficient, Ah", _render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)),
            ("Vertical Seismic Coefficient, Av", _render_value(input_dict, KEY_SL_VERTICAL_COEFF)),
            ("Horizontal Seismic Force (longitudinal)", " kN"),
            ("Horizontal Seismic Force (transverse)", " kN"),
        ],
    )

    # 6. Temperature Load
    t_tl = KeyValueTable(
        caption=r"\textbf{Temperature Load (TL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            ("Maximum Shade Temperature", f"{_render_value(input_dict, 'shade_temp_max')} $^\\circ$C"),
            ("Minimum Shade Temperature", f"{_render_value(input_dict, 'shade_temp_min')} $^\\circ$C"),
            ("Effective Bridge Temp. Range", f"{_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)} to {_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)} $^\\circ$C"),
            ("Temperature Rise / Fall for Design", f"+{_render_value(input_dict, KEY_TL_TEMP_RISE)} $^\\circ$C / \\textminus{{}}{_render_value(input_dict, KEY_TL_TEMP_FALL)} $^\\circ$C"),
        ],
    )

    # 7. Load Combinations
    t_combos = ReportTable(
        columns="|C{4.0cm}|L{11.5cm}|",
        caption=r"\textbf{Load Combinations}",
        header_rows=[["Combination ID", "Load Cases"]],
    )
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        t_combos.add_row([f"ULS-{i:02d}", cases])
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        t_combos.add_row([f"SLS-{i:02d}", cases])

    return rf"""
\chapter{{Loads and Load Combinations}}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{{1em}}
{t_sw.dumps()}

\vspace{{1em}}
{t_dw.dumps()}

\vspace{{1em}}
{t_veh.dumps()}

\noindent\textit{{Note: Live load parameters per IRC 6:2017 Cl. 204. Centrifugal forces not evaluated (straight alignment assumed).}}

\vspace{{1em}}
{fp_block}

\vspace{{1em}}
{t_wl.dumps()}

\vspace{{1em}}
{t_el.dumps()}

\vspace{{1em}}
{t_tl.dumps()}

\vspace{{1em}}
{t_combos.dumps()}

\noindent\textit{{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}}
"""


