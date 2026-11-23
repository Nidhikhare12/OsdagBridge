# =============================================================================
# Chapter 3: Loads and Load Combinations
#
# Generates comprehensive loading definitions per IRC 6:2017:
# - Table 3.1: Dead Load — Self Weight
# - Table 3.2: Dead Load for Surfacing (SIDL/DW)
# - Table 3.3: Vehicle Live Loads (LL) — Separate table with vehicle classes,
#              impact factors, braking load, braking eccentricity, and centrifugal forces
# - Table 3.4: Footway / Footpath Live Load (FL) — Separate table with mode,
#              intensity, footpath width, and kerb loads
# - Table 3.5: Wind Load (WL) per IRC 6
# - Table 3.6: Earthquake Load (EL) per IRC 6
# - Table 3.7: Temperature Load (TL) per IRC 6
# - Table 3.8: Load Combinations (ULS and SLS) with repeated longtable headers
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
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
    KEY_BL_IRC_CLASS_SV,
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
from osdagbridge.core.reports.styles import format_longtable
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def ch3_loads(input_dict):
    # ── 1. Live Load Vehicles & Classes ──────────────────────────────────────
    vehicle_rows = []
    selected_vehicles = []

    def _check_v(key, name, code_ref):
        val = input_dict.get(key)
        is_sel = val is True or str(val).strip().lower() in ("true", "yes", "1", "checked")
        status = "Selected" if is_sel else "Not Considered"
        if is_sel:
            selected_vehicles.append(name)
        vehicle_rows.append((name, code_ref, status))

    _check_v(KEY_LL_IRC_CLASS_A, "IRC Class A", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_70R_WHEELED, "IRC Class 70R (Wheeled)", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_70R_TRACKED, "IRC Class 70R (Tracked)", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_AA_WHEELED, "IRC Class AA (Wheeled)", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_AA_TRACKED, "IRC Class AA (Tracked)", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_70R_BOGIE, "IRC Class 70R (Bogie)", "IRC 6 Cl. 204.1")
    _check_v(KEY_LL_IRC_CLASS_SV, "IRC Class SV (Special Vehicle)", "IRC 6 Cl. 204.5")
    _check_v(KEY_LL_IRC_CLASS_FATIGUE, "IRC Class Fatigue", "IRC 6 Cl. 204.6")

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            cname = c.get('name') if isinstance(c, dict) else str(c)
            if cname:
                selected_vehicles.append(cname)
                vehicle_rows.append((f"Custom: {cname}", "User-Defined", "Selected"))

    vehicles_summary_str = ", ".join(selected_vehicles) if selected_vehicles else "None Selected"

    # ── 2. Impact Factor (IRC 6 Cl. 208) ────────────────────────────────────
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = "N/A"
    impact_details = []
    if span not in (None, ""):
        try:
            span_m = float(span)
            if any("Class A" in v for v in selected_vehicles):
                # IRC 6 Cl. 208.3 for steel/composite bridge: 9.0 / (13.5 + L)
                # or Cl. 208.2 for concrete deck: 4.5 / (6.0 + L)
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                impact_details.append(f"Class A: {1.0 + im_a:.3f} (fractional impact I = {im_a:.3f})")
            if any("70R" in v or "AA" in v for v in selected_vehicles):
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                impact_details.append(f"Class 70R / AA: {1.0 + im_aa:.3f} (fractional impact I = {im_aa:.3f})")
            if impact_details:
                impact_factor_str = "; ".join(impact_details)
            else:
                impact_factor_str = "Not applicable: no vehicle class selected"
        except Exception:
            impact_factor_str = "N/A"

    # ── 3. Braking Load (IRC 6 Cl. 211.2) ────────────────────────────────────
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = "N/A"
    try:
        if not selected_vehicles or lanes in (None, ""):
            raise ValueError("Vehicle selection or design lane count is unavailable")
        lanes_int = int(lanes)
        braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_force_kN = braking_force_t * 9.81
        braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes) for {lanes_int} lane(s)"
    except Exception:
        braking_force_str = "N/A"

    # Eccentricity of braking force
    ecc_val = input_dict.get(KEY_LL_ECCENTRICITY)
    ecc_str = f"{float(ecc_val):.2f} m above road deck" if ecc_val not in (None, "") else "Not available in supplied design inputs"

    # ── 4. Centrifugal Force (IRC 6 Cl. 212) ─────────────────────────────────
    # C = W * V^2 / (127 * R) in kN.
    # Where R is radius of horizontal curvature in metres.
    # For straight bridge alignment, R = infinity, C = 0.00 kN.
    centrifugal_str = "Not applicable / not available from supplied alignment and vehicle inputs"
    radius_val = input_dict.get("horizontal_radius_m") or input_dict.get("curvature_radius")
    speed_val = input_dict.get("design_speed_kmh")
    vehicle_weight = input_dict.get("selected_vehicle_weight_tonnes")
    if radius_val not in (None, "") and speed_val not in (None, "") and vehicle_weight not in (None, ""):
        try:
            r_m, speed_kmh, w_tonnes = float(radius_val), float(speed_val), float(vehicle_weight)
            if r_m > 0 and speed_kmh >= 0 and w_tonnes >= 0:
                c_kn = (w_tonnes * (speed_kmh ** 2)) / (127.0 * r_m) * 9.81
                centrifugal_str = f"{c_kn:.2f} kN (R = {r_m:.1f} m, V = {speed_kmh:.0f} km/h; vehicle weight from selected input)"
        except (TypeError, ValueError):
            pass

    # ── 5. Footway / Footpath Load (IRC 6 Cl. 206.1) ─────────────────────────
    footpath_type = str(input_dict.get(KEY_FOOTPATH, "None")).strip()
    has_footpath = footpath_type.lower() not in ("none", "", "no", "false")
    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH, "Not available")
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "Not specified")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

    if has_footpath:
        if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
            try:
                # IRC 6 Cl. 206.1 footway load intensity
                if span in (None, ""):
                    raise ValueError("Bridge span is unavailable")
                span_f = float(span)
                if span_f <= 7.5:
                    fp_intensity = 5.0
                elif span_f >= 30.0:
                    fp_intensity = 4.0
                else:
                    fp_intensity = 5.0 - ((span_f - 7.5) / 22.5) * 1.0
                fp_intensity_str = f"{fp_intensity:.3f} kN/m$^2$ (IRC 6 Cl. 206.1 for L = {span_f:.1f} m)"
            except Exception:
                fp_intensity_str = "Not available: required span/input missing"
        elif fp_value not in (None, ""):
            fp_intensity_str = f"{float(fp_value):.3f} kN/m$^2$ (User-Defined)"
        else:
            fp_intensity_str = "Not available: no footway intensity supplied"
    else:
        fp_intensity_str = "0.00 kN/m$^2$ (No footway configured on bridge)"

    # Kerb and barrier loads
    kerb_load_str = "5.00 kN/m along top of kerb (IRC 6 Cl. 206.2)" if has_footpath else "N/A"

    # ── 6. Wind Load (WL) per IRC 6 ──────────────────────────────────────────
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

    # ── 7. Seismic Load (EL) per IRC 6 ───────────────────────────────────────
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
            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}",
                soil_type=_st,
                dead_load_kN=0.0,
                live_load_kN=0.0,
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
                sl_av = round(_res.get("Ah", 0) * 2.0 / 3.0, 4)
        except Exception:
            pass

    # ── 8. Temperature Load (TL) per IRC 6 ───────────────────────────────────
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

    # ── 9. Load Combinations (ULS & SLS) ────────────────────────────────────
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
        lc_rows.append(f"ULS-{i:02d} & {cases} \\\\[4pt]\n\\hline")
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"SLS-{i:02d} & {cases} \\\\[4pt]\n\\hline")

    lc_rows_str = "\n".join(lc_rows)

    # ── Table Building using format_longtable ─────────────────────────────────
    # Table 3.1: Dead Load - Self Weight
    t31_body = rf"""
\textnormal{{Steel Girder Material Density}} & {(_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m$^3$'))} \\[4pt]
\hline
\textnormal{{Concrete Deck Slab Density}} & {(_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m$^3$'))} \\[4pt]
\hline
\textnormal{{Self-Weight Multiplier Factor}} & {(_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR))} \\[4pt]
\hline
"""
    t31_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Dead Load --- Self Weight",
        header_rows=r"\textbf{Parameter} & \textbf{Value / Specification}",
        body_rows=t31_body,
        ncols=2,
        label="tab:dl-self-weight"
    )

    # Table 3.2: Surfacing (SIDL/DW)
    t32_body = rf"""
\textnormal{{Wearing Course Material \& Thickness}} & {(_render_value(input_dict, KEY_WC_MATERIAL))} $\times$ {(_render_value(input_dict, KEY_WC_THICKNESS, ' mm'))} \\[4pt]
\hline
\textnormal{{Crash Barrier SIDL}} & {(_render_value(input_dict, KEY_CB_LOAD))} kN/m per barrier \\[4pt]
\hline
\textnormal{{Railing Load}} & {(_render_value(input_dict, KEY_RL_LOAD_VALUE))} kN/m\sdstar{{}} \\[4pt]
\hline
"""
    t32_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Dead Load for Surfacing (DW / SIDL)",
        header_rows=r"\textbf{Parameter} & \textbf{Value / Specification}",
        body_rows=t32_body,
        ncols=2,
        label="tab:dl-surfacing"
    )

    # Table 3.3: Vehicle Live Loads (LL) - Requirement 3
    t33_rows = [
        rf"\textnormal{{Vehicles Selected for Design}} & {_tex(vehicles_summary_str)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Traffic Lanes Considered}} & {lanes} Design Lane(s) \\[4pt]",
        r"\hline",
        rf"\textnormal{{Impact Factor ($1 + I$)}} & {_tex(impact_factor_str)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Braking Force ($F_{{br}}$)}} & {_tex(braking_force_str)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Braking Force Line of Action}} & {_tex(ecc_str)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Centrifugal Force ($F_{{cf}}$)}} & {_tex(centrifugal_str)} \\[4pt]",
        r"\hline"
    ]
    t33_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Vehicle Live Loads (LL) --- per IRC 6:2017",
        header_rows=r"\textbf{Vehicle Load Parameter} & \textbf{Design Value \& Code Reference}",
        body_rows="\n".join(t33_rows),
        ncols=2,
        label="tab:vehicle-live-load",
        note="Note: Vehicle classes and braking forces derived in accordance with IRC 6 Cl. 204, Cl. 208, Cl. 211 and Cl. 212."
    )

    # Table 3.4: Footway / Footpath Live Load (FL) - Requirement 3
    t34_rows = [
        rf"\textnormal{{Footpath Configuration}} & {_tex(footpath_type)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Footpath Width}} & {_tex(str(fp_width))} m \\[4pt]",
        r"\hline",
        rf"\textnormal{{Footpath Load Mode}} & {_tex(str(fp_mode))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Footway Uniform Live Load Intensity}} & {fp_intensity_str} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Kerb Horizontal Collision Load}} & {_tex(kerb_load_str)} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Pedestrian Load Application Status}} & {_tex('Applied in Analysis' if has_footpath else 'Excluded (No Footpath)')} \\[4pt]",
        r"\hline"
    ]
    t34_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Footway and Pedestrian Live Load (FL) --- per IRC 6 Cl. 206",
        header_rows=r"\textbf{Footway Parameter} & \textbf{Design Value \& Provision}",
        body_rows="\n".join(t34_rows),
        ncols=2,
        label="tab:footway-load",
        note="Note: Footway live load intensity evaluated per IRC 6 Cl. 206.1 based on effective bridge span."
    )

    # Table 3.5: Wind Load (WL)
    t35_rows = [
        rf"\textnormal{{Basic Wind Speed, $V_b$}} & {(_render_value(input_dict, 'wind_speed', ' m/s'))} [Project Location] \\[4pt]",
        r"\hline",
        rf"\textnormal{{Terrain Type}} & {(_render_value(input_dict, KEY_WL_TERRAIN_TYPE))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Average Exposed Height, $H$}} & {(_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m'))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Hourly Mean Wind Speed, $V_z$}} & {(_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s'))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Hourly Wind Pressure, $P_z$}} & {(_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m$^2$'))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Transverse Wind Force}} & {(_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN'))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Longitudinal Wind Force}} & {(_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN'))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Vertical Wind Force}} & {(_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN'))} \\[4pt]",
        r"\hline"
    ]
    t35_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Wind Load (WL) --- per IRC 6 Cl. 209",
        header_rows=r"\textbf{Wind Load Parameter} & \textbf{Value / Calculation}",
        body_rows="\n".join(t35_rows),
        ncols=2,
        label="tab:wind-load"
    )

    # Table 3.6: Earthquake Load (EL)
    t36_rows = [
        rf"\textnormal{{Seismic Zone}} & {(_render_value(input_dict, 'seismic_zone'))} [Project Location] \\[4pt]",
        r"\hline",
        rf"\textnormal{{Zone Factor, $Z$}} & {(_render_value(input_dict, KEY_SL_ZONE_FACTOR))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Importance Factor, $I$}} & {(_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Type of Soil}} & {(_render_value(input_dict, KEY_SL_SOIL_TYPE))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Spectral Acceleration Ratio, $S_a/g$}} & {(_render_value(input_dict, KEY_SL_SPECTRAL_COEFF))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Horizontal Seismic Coeff., $A_h$}} & {(_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF))} \\[4pt]",
        r"\hline",
        rf"\textnormal{{Vertical Seismic Coeff., $A_v$}} & {(_render_value(input_dict, KEY_SL_VERTICAL_COEFF))} \\[4pt]",
        r"\hline"
    ]
    t36_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Earthquake Load (EL) --- per IRC 6 Cl. 218",
        header_rows=r"\textbf{Seismic Parameter} & \textbf{Value / Coefficient}",
        body_rows="\n".join(t36_rows),
        ncols=2,
        label="tab:seismic-load"
    )

    # Table 3.7: Temperature Load (TL)
    t37_rows = [
        rf"\textnormal{{Maximum Shade Temperature}} & {(_render_value(input_dict, 'shade_temp_max'))} $^\circ$C \\[4pt]",
        r"\hline",
        rf"\textnormal{{Minimum Shade Temperature}} & {(_render_value(input_dict, 'shade_temp_min'))} $^\circ$C \\[4pt]",
        r"\hline",
        rf"\textnormal{{Effective Bridge Temp. Range}} & {(_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN))} to {(_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX))} $^\circ$C \\[4pt]",
        r"\hline",
        rf"\textnormal{{Design Temperature Rise / Fall}} & +{(_render_value(input_dict, KEY_TL_TEMP_RISE))} $^\circ$C / \textminus{{}}{(_render_value(input_dict, KEY_TL_TEMP_FALL))} $^\circ$C \\[4pt]",
        r"\hline"
    ]
    t37_tex = format_longtable(
        col_spec=r"|L{6.0cm}|p{9.5cm}|",
        caption="Temperature Load (TL) --- per IRC 6 Cl. 215",
        header_rows=r"\textbf{Thermal Parameter} & \textbf{Value / Range}",
        body_rows="\n".join(t37_rows),
        ncols=2,
        label="tab:temp-load"
    )

    # Table 3.8: Load Combinations
    t38_tex = format_longtable(
        col_spec=r"|C{3.5cm}|p{12.0cm}|",
        caption="Design Load Combinations (ULS and SLS) --- per IRC 6:2017",
        header_rows=r"\textbf{Combination ID} & \textbf{Factored Load Cases}",
        body_rows=lc_rows_str,
        ncols=2,
        label="tab:load-combinations",
        note="Note: All combinations dynamically evaluated in accordance with IRC 6 Table B.2 (ULS) and Table B.3 (SLS)."
    )

    return rf"""
\chapter{{Loads and Load Combinations}}
\label{{ch:loads}}

This chapter provides the complete specification of all structural design loads and design load combinations applied to the bridge in accordance with IRC 6:2017.

\vspace{{0.5em}}
{t31_tex}

\vspace{{0.5em}}
{t32_tex}

\vspace{{0.5em}}
{t33_tex}

\vspace{{0.5em}}
{t34_tex}

\vspace{{0.5em}}
{t35_tex}

\vspace{{0.5em}}
{t36_tex}

\vspace{{0.5em}}
{t37_tex}

\vspace{{0.5em}}
{t38_tex}
"""
