# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored in Phase 3B Task B:
#   - Converted all tables to make_longtable
#   - Split live load table into Vehicle Live Loads & Footpath Live Load
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
    KEY_WL_VERTICAL_WIND_FORCE,
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.helpers import make_longtable
from osdagbridge.core.reports.styles import (
    TABLE_SPEC_TWO_COL,
    TABLE_SPEC_VEHICLE_LL,
    TABLE_SPEC_FOOTPATH_LL,
    TABLE_SPEC_LOAD_COMBOS,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span) if span not in (None, "") else 24.0
    except (ValueError, TypeError):
        span_m = 24.0

    # -------------------------------------------------------------------------
    # 1. Dead Load -- Self Weight Table
    # -------------------------------------------------------------------------
    dl_sw_rows = [
        r"\textnormal{Steel Self-Weight Applied} & " + _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r' kN/m\textsuperscript{3}') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Concrete Deck Weight} & " + _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r' kN/m\textsuperscript{3}') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Self-Weight Factor} & " + _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR) + r" \\[6pt]" + "\n" + r"\hline",
    ]
    table_dl_sw = make_longtable(
        col_spec=TABLE_SPEC_TWO_COL,
        caption="Dead Load -- Self Weight",
        headers=["parameter", "value"],
        rows=dl_sw_rows,
        label="tab:dead-load-sw",
    )

    # -------------------------------------------------------------------------
    # 2. Dead Load for Surfacing (DW) Table
    # -------------------------------------------------------------------------
    dl_dw_rows = [
        r"\textnormal{Wearing Course Load} & " + _render_value(input_dict, KEY_WC_MATERIAL) + r" x " + _render_value(input_dict, KEY_WC_THICKNESS) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Additional SIDL (Crash Barrier)} & " + _render_value(input_dict, KEY_CB_LOAD) + r" kN/m per barrier \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Railing Load} & " + _render_value(input_dict, KEY_RL_LOAD_VALUE) + r" kN/m\sdstar{} \\[6pt]" + "\n" + r"\hline",
    ]
    table_dl_dw = make_longtable(
        col_spec=TABLE_SPEC_TWO_COL,
        caption="Dead Load for Surfacing (DW)",
        headers=["parameter", "value"],
        rows=dl_dw_rows,
        label="tab:dead-load-dw",
    )

    # -------------------------------------------------------------------------
    # 3. Vehicle Live Loads Table (IRC 6 Cl. 208, 211, 209)
    # -------------------------------------------------------------------------
    # Impact Factors per IRC 6 Cl. 208:
    # Cl. 208.2: Class A & B (steel bridges)
    im_class_a = round(9.0 / (13.5 + min(max(span_m, 3.0), 45.0)), 3)
    # Cl. 208.3: Heavy vehicles
    im_tracked = 0.25 if span_m <= 5.0 else 0.10
    im_wheeled = 0.25 if span_m < 23.0 else round(9.0 / (13.5 + min(span_m, 45.0)), 3)

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    try:
        lanes_int = int(lanes) if lanes not in (None, "") else 2
    except (ValueError, TypeError):
        lanes_int = 2

    # Collect selected vehicle rows
    v_rows = []

    def _is_flag_true(k):
        val = input_dict.get(k)
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("true", "yes", "1")

    # Map candidate IRC vehicles: (flag_key, label, impact_str, braking_str)
    candidate_vehicles = [
        (KEY_LL_IRC_CLASS_A, "Class A", f"{1.0 + im_class_a:.3f}", "110.8 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)", f"{1.0 + im_wheeled:.3f}", "200.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)", f"{1.0 + im_tracked:.3f}", "140.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)", f"{1.0 + im_wheeled:.3f}", "80.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)", f"{1.0 + im_tracked:.3f}", "140.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)", f"{1.0 + im_wheeled:.3f}", "80.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_CLASS_SV, "Class SV (Special)", "1.000 (No impact per Cl. 204.5)", "200.0 kN (IRC 6 Cl. 211.2)"),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue", "1.000", "N/A"),
    ]

    for k, name, imp, brk in candidate_vehicles:
        if _is_flag_true(k):
            v_rows.append(
                f"{name} & {imp} & {brk} & N/A (straight bridge) " + r"\\[6pt]" + "\n" + r"\hline"
            )

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            cname = c.get('name') if isinstance(c, dict) else str(c)
            if cname:
                v_rows.append(
                    f"{_tex(cname)} & 1.000 & 200.0 kN & N/A (straight bridge) " + r"\\[6pt]" + "\n" + r"\hline"
                )

    if not v_rows:
        v_rows.append(
            r"\textit{None Selected} & --- & --- & N/A (straight bridge) \\[6pt]" + "\n" + r"\hline"
        )

    table_vehicles = make_longtable(
        col_spec=TABLE_SPEC_VEHICLE_LL,
        caption="Vehicle Live Loads (IRC 6)",
        headers=["Vehicle Class", "Impact Factor (1+IM)", "Braking Load", "Centrifugal Force"],
        rows=v_rows,
        label="tab:vehicle-live-loads",
        note="IRC 6 Cl. 208 for impact, Cl. 211 for longitudinal braking force. Centrifugal force per Cl. 209 is N/A for straight bridges (no horizontal curve radius specified).",
    )

    # -------------------------------------------------------------------------
    # 4. Footpath Live Load Table (Separate table with units and mode)
    # -------------------------------------------------------------------------
    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")).strip()
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

    is_auto = fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic", "")
    mode_str = "Software default" if is_auto else "User-modified"

    if is_auto:
        try:
            fp_intensity = f"{IRC6_2017.cl_206_1_footway_load():.2f}"
        except Exception:
            fp_intensity = "4.00"
    else:
        fp_intensity = f"{float(fp_value):.2f}" if fp_value not in (None, "") else "4.00"

    fp_width = _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, "")

    fp_rows = [
        r"Footway Live Load Intensity & " + fp_intensity + r" & kN/m² & IRC 6 Cl. 206.1 & " + mode_str + r" \\[6pt]" + "\n" + r"\hline",
        r"Footpath Width & " + fp_width + r" & m & IRC 5 Cl. 104.3.6 & User input \\[6pt]" + "\n" + r"\hline",
        r"Kerb Live Load & 5.00 & kN/m & IRC 6 Cl. 206.2 & Software default \\[6pt]" + "\n" + r"\hline",
    ]

    table_footpath = make_longtable(
        col_spec=TABLE_SPEC_FOOTPATH_LL,
        caption="Footpath Live Load Details",
        headers=["Parameter", "Value", "Unit", "Reference", "Source / Mode"],
        rows=fp_rows,
        label="tab:footpath-live-load",
        note="Pedestrian live load intensity per IRC 6 Cl. 206.1 based on effective span. Kerb design load per IRC 6 Cl. 206.2.",
    )

    # -------------------------------------------------------------------------
    # 5. Wind Load (WL) Table
    # -------------------------------------------------------------------------
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

    wl_rows = [
        r"\textnormal{Basic Wind Speed, Vb} & " + _render_value(input_dict, 'wind_speed', ' m/s') + r" [from Project Location] \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Terrain Type} & " + _render_value(input_dict, KEY_WL_TERRAIN_TYPE) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Average Exposed Height, H (m)} & " + _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Hourly Mean Wind Speed, Vz} & " + _render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Hourly Wind Pressure, Pz} & " + _render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r' N/m\textsuperscript{2}') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Transverse Wind Force} & " + _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Longitudinal Wind Force} & " + _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Vertical Wind Force} & " + _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN') + r" \\[6pt]" + "\n" + r"\hline",
    ]
    table_wl = make_longtable(
        col_spec=TABLE_SPEC_TWO_COL,
        caption="Wind Load (WL) --- per IRC 6",
        headers=["parameter", "value"],
        rows=wl_rows,
        label="tab:wind-load",
    )

    # -------------------------------------------------------------------------
    # 6. Earthquake Load (EL) Table
    # -------------------------------------------------------------------------
    el_rows = [
        r"\textnormal{Seismic Zone} & " + _render_value(input_dict, 'seismic_zone') + r" [from Project Location] \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Zone Factor, Z} & " + _render_value(input_dict, KEY_SL_ZONE_FACTOR) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Importance Factor, I} & " + _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Type of Soil} & " + _render_value(input_dict, KEY_SL_SOIL_TYPE) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Sa/g} & " + _render_value(input_dict, KEY_SL_SPECTRAL_COEFF) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Horizontal Seismic Coefficient, Ah} & " + _render_value(input_dict, KEY_SL_HORIZONTAL_COEFF) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Vertical Seismic Coefficient, Av} & " + _render_value(input_dict, KEY_SL_VERTICAL_COEFF) + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Horizontal Seismic Force (longitudinal)} & " + _render_value(input_dict, 'seismic_force_long', ' kN') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Horizontal Seismic Force (transverse)} & " + _render_value(input_dict, 'seismic_force_trans', ' kN') + r" \\[6pt]" + "\n" + r"\hline",
    ]
    table_el = make_longtable(
        col_spec=TABLE_SPEC_TWO_COL,
        caption="Earthquake Load (EL) --- per IRC 6",
        headers=["parameter", "value"],
        rows=el_rows,
        label="tab:earthquake-load",
    )

    # -------------------------------------------------------------------------
    # 7. Temperature Load (TL) Table
    # -------------------------------------------------------------------------
    tl_rows = [
        r"\textnormal{Maximum Shade Temperature} & " + _render_value(input_dict, 'shade_temp_max', r' $^\circ$C') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Minimum Shade Temperature} & " + _render_value(input_dict, 'shade_temp_min', r' $^\circ$C') + r" \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Effective Bridge Temp. Range} & " + _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN) + r" to " + _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX) + r" $^\circ$C \\[6pt]" + "\n" + r"\hline",
        r"\textnormal{Temperature Rise / Fall for Design} & +" + _render_value(input_dict, KEY_TL_TEMP_RISE) + r" $^\circ$C / \textminus{}" + _render_value(input_dict, KEY_TL_TEMP_FALL) + r" $^\circ$C \\[6pt]" + "\n" + r"\hline",
    ]
    table_tl = make_longtable(
        col_spec=TABLE_SPEC_TWO_COL,
        caption="Temperature Load (TL) --- per IRC 6",
        headers=["parameter", "value"],
        rows=tl_rows,
        label="tab:temperature-load",
    )

    # -------------------------------------------------------------------------
    # 8. Load Combinations Table
    # -------------------------------------------------------------------------
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
    sls_combos = IRC6_2017.sls_load_combinations()
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

    table_lc = make_longtable(
        col_spec=TABLE_SPEC_LOAD_COMBOS,
        caption="Load Combinations",
        headers=["Combination ID", "Load Cases"],
        rows=lc_rows,
        label="tab:load-combinations",
        note="All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.",
    )

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
""" + table_dl_sw + r"""

\vspace{1em}
""" + table_dl_dw + r"""

\vspace{1em}
""" + table_vehicles + r"""

\vspace{1em}
""" + table_footpath + r"""

\vspace{1em}
""" + table_wl + r"""

\vspace{1em}
""" + table_el + r"""

\vspace{1em}
""" + table_tl + r"""

\vspace{1em}
""" + table_lc + r"""
"""
