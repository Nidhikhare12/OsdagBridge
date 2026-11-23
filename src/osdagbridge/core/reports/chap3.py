
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
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_TS_FOOTPATH_WIDTH,
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
)

from osdagbridge.core.reports.report_utils import _tex, _render_value


def ch3_loads(input_dict):
    def _selected(value):
        return value is True or str(value).strip().lower() in {"yes", "true", "1", "checked", "on"}

    # -------------------------------------------------------------------------
    # Vehicle live loads
    # -------------------------------------------------------------------------

    vehicles = []

    if _selected(input_dict.get(KEY_LL_IRC_CLASS_A)):
        vehicles.append("Class A")

    if _selected(input_dict.get(KEY_LL_IRC_70R_WHEELED)):
        vehicles.append("Class 70R (Wheeled)")

    if _selected(input_dict.get(KEY_LL_IRC_70R_TRACKED)):
        vehicles.append("Class 70R (Tracked)")

    if _selected(input_dict.get(KEY_LL_IRC_AA_WHEELED)):
        vehicles.append("Class AA (Wheeled)")

    if _selected(input_dict.get(KEY_LL_IRC_AA_TRACKED)):
        vehicles.append("Class AA (Tracked)")

    if _selected(input_dict.get(KEY_LL_IRC_CLASS_SV)):
        vehicles.append("Class SV")

    if _selected(input_dict.get(KEY_LL_IRC_70R_BOGIE)):
        vehicles.append("Class 70R (Bogie)")

    if _selected(input_dict.get(KEY_LL_IRC_CLASS_FATIGUE)):
        vehicles.append("Class Fatigue")

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)

    if custom and isinstance(custom, list):
        for vehicle in custom:
            if isinstance(vehicle, dict) and vehicle.get("name"):
                vehicles.append(vehicle["name"])
            elif isinstance(vehicle, str):
                vehicles.append(vehicle)

    vehicles_str = ", ".join(vehicles) if vehicles else "None"

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # -------------------------------------------------------------------------
    # Impact factor
    # -------------------------------------------------------------------------

    span = input_dict.get(KEY_SPAN)
    impact_factor_str = "N/A"

    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []

            if _selected(input_dict.get(KEY_LL_IRC_CLASS_A)):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")

            is_wheeled_heavy = (
                _selected(input_dict.get(KEY_LL_IRC_70R_WHEELED))
                or _selected(input_dict.get(KEY_LL_IRC_AA_WHEELED))
                or _selected(input_dict.get(KEY_LL_IRC_70R_BOGIE))
            )

            is_tracked_heavy = (
                _selected(input_dict.get(KEY_LL_IRC_70R_TRACKED))
                or _selected(input_dict.get(KEY_LL_IRC_AA_TRACKED))
            )

            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")

            impact_factor_str = ", ".join(factors) if factors else "N/A"

        except Exception:
            impact_factor_str = "N/A"

    # -------------------------------------------------------------------------
    # Braking force
    # -------------------------------------------------------------------------

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = "N/A"
    braking_force_unit = "—"

    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81

            braking_force_str = f"{braking_force_kN:.2f}"
            braking_force_unit = f"kN ({braking_force_t:.2f} tonnes)"

        except Exception:
            braking_force_str = "N/A"

    # -------------------------------------------------------------------------
    # Footpath live load
    # -------------------------------------------------------------------------

    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    try:
        footpath_count = int(float(input_dict.get(KEY_TS_NO_OF_FOOTPATHS, 0) or 0))
    except (TypeError, ValueError):
        footpath_count = 0
    footpath_width = 0.0
    try:
        footpath_width = float(input_dict.get(KEY_TS_FOOTPATH_WIDTH, 0) or 0)
    except (TypeError, ValueError):
        pass
    footpath_configured = footpath_count > 0 and footpath_width > 0

    fp_mode_normalized = str(fp_mode).strip().lower()

    if not footpath_configured:
        fp_str = "Not applicable — no footpath configured"
        fp_mode_str = "Not applicable"
    elif fp_mode_normalized in (
        "as per irc 6",
        "as per irc6",
        "automatic",
    ):
        try:
            fp_load = IRC6_2017.cl_206_1_footway_load()
            fp_str = f"{fp_load:.3f} (IRC 6 Cl. 206.1)"

        except Exception:
            fp_str = "N/A"

    elif fp_value not in (None, ""):
        fp_str = str(fp_value)

    else:
        fp_str = "N/A"

    if footpath_configured:
        fp_mode_str = str(fp_mode).strip() if fp_mode not in (None, "") else "N/A"
        fp_unit = r" kN/m\textsuperscript{2}"
    else:
        fp_unit = ""

    # -------------------------------------------------------------------------
    # Wind load values
    # Prefer stored computed values; fall back to IRC 6 Table 12.
    # -------------------------------------------------------------------------

    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)

    if not vz_val or not pz_val:
        try:
            _vb = (
                input_dict.get(KEY_WL_BASIC_WIND_SPEED)
                or input_dict.get("wind_speed")
            )

            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)

            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(
                str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(),
                "plain",
            )

            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))

            if not vz_val:
                vz_val = _res.get("Vz")

            if not pz_val:
                pz_val = _res.get("Pz")

        except Exception:
            pass

    def _format_number(value, decimals=2):
        """Format a numeric value safely for report output."""
        if value in (None, ""):
            return "N/A"

        try:
            return f"{float(value):.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)

    vz_str = (
        f"{_format_number(vz_val)} m/s"
        if vz_val not in (None, "")
        else "N/A"
    )

    pz_str = (
        f"{_format_number(pz_val)} N/m^2"
        if pz_val not in (None, "")
        else "N/A"
    )

    # -------------------------------------------------------------------------
    # Seismic load values
    # Prefer stored computed values; fall back to IRC 6 Clause 218.5.1.
    # -------------------------------------------------------------------------

    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)

    if not sl_ah or not sl_zone_factor:
        try:
            _zone = (
                input_dict.get(KEY_SL_SEISMIC_ZONE)
                or input_dict.get("seismic_zone")
            )

            _zmap = {
                "1": "I",
                "2": "II",
                "3": "III",
                "4": "IV",
                "5": "V",
            }

            _z = str(_zone).strip().upper()

            if _z.isdigit():
                _z = _zmap.get(_z)

            _smap = {
                "Type I – Rocky or Hard": 1,
                "Type II – Medium Soil": 2,
                "Type III – Soft Soil": 3,
            }

            _st = _smap.get(
                str(input_dict.get(KEY_SL_SOIL_TYPE, "")),
                1,
            )

            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"

            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)

            _dead = (
                float(_dl_v)
                if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom"
                and _dl_v
                else 0.0
            )

            _live = (
                float(_ll_v)
                if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom"
                and _ll_v
                else 0.0
            )

            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}",
                soil_type=_st,
                dead_load_kN=_dead,
                live_load_kN=_live,
                period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp),
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

    def _sl(value, unit=""):
        """Format seismic values with their units."""
        if value in (None, ""):
            return "N/A"

        try:
            return f"{float(value):.4f}{unit}"
        except (TypeError, ValueError):
            return f"{value}{unit}"

    # -------------------------------------------------------------------------
    # Temperature load values
    # Compute effective bridge temperature range from shade temperatures.
    # -------------------------------------------------------------------------

    tl_temp_min = "N/A"
    tl_temp_max = "N/A"
    tl_rise = "N/A"
    tl_fall = "N/A"

    try:
        _tmax = (
            input_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
            or input_dict.get("shade_temp_max")
        )

        _tmin = (
            input_dict.get(KEY_TL_LOWEST_MIN_TEMP)
            or input_dict.get("shade_temp_min")
        )

        if _tmax not in (None, "") and _tmin not in (None, ""):
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax),
                float(_tmin),
                "metallic",
                False,
            )

            _bt_min = _res.get("T_min", 0)
            _bt_max = _res.get("T_max", 0)

            _mean = (_bt_max + _bt_min) / 2.0

            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"

    except Exception:
        pass

    # Use stored bridge temperature values if available.
    bridge_temp_min = input_dict.get(KEY_TL_BRIDGE_TEMP_MIN)
    bridge_temp_max = input_dict.get(KEY_TL_BRIDGE_TEMP_MAX)

    if bridge_temp_min in (None, ""):
        bridge_temp_min = tl_temp_min

    if bridge_temp_max in (None, ""):
        bridge_temp_max = tl_temp_max

    temperature_rise = input_dict.get(KEY_TL_TEMP_RISE)

    if temperature_rise in (None, ""):
        temperature_rise = tl_rise

    temperature_fall = input_dict.get(KEY_TL_TEMP_FALL)

    if temperature_fall in (None, ""):
        temperature_fall = tl_fall

    # -------------------------------------------------------------------------
    # Table 3.7: Load Combinations
    # Dynamically generated from IRC 6.
    # -------------------------------------------------------------------------

    _LOAD_LABEL_MAP = {
        "dead_load": "DL",
        "surfacing": "SIDL",
        "live_load": "LL",
        "wind_load": "WL",
        "thermal_load": "TL",
        "vehicle_collision": "VC",
        "barge_impact": "BI",
        "floating_bodies": "FB",
        "seismic": "EQ",
    }

    def _fmt_factors(factors):
        """Format a factors dictionary into a compact load-case string."""
        parts = []

        for load, value in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())

            if isinstance(value, dict):
                add = value.get("adding")
                rel = value.get("relieving")

                add_s = f"{add:.2f}" if add is not None else "--"
                rel_s = f"{rel:.2f}" if rel is not None else "--"

                parts.append(f"{label}({add_s}/{rel_s})")

            else:
                if value is None:
                    continue

                parts.append(f"{label}({value:.2f})")

        return " + ".join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()

    lc_rows = []

    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo["factors"])

        lc_rows.append(
            f"ULS-{i:02d}"
            + r" & "
            + _tex(cases)
            + r" \\[6pt]"
            + "\n"
            + r"\hline"
        )

    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo["factors"])

        lc_rows.append(
            f"SLS-{i:02d}"
            + r" & "
            + _tex(cases)
            + r" \\[6pt]"
            + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    # -------------------------------------------------------------------------
    # Chapter 3 report output
    # -------------------------------------------------------------------------

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.0cm}|p{9.7cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Steel Self-Weight Applied} & """ + _render_value(
        input_dict,
        KEY_MATERIAL_GIRDER_DENSITY,
        r" kN/m\textsuperscript{3}",
    ) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + _render_value(
        input_dict,
        KEY_MATERIAL_DECK_DENSITY,
        r" kN/m\textsuperscript{3}",
    ) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + _render_value(
        input_dict,
        KEY_PL_SELF_WEIGHT_FACTOR,
    ) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.0cm}|p{9.7cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Wearing Course Load} & """ + _render_value(
        input_dict,
        KEY_WC_MATERIAL,
    ) + r""" x """ + _render_value(
        input_dict,
        KEY_WC_THICKNESS,
    ) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + _render_value(
        input_dict,
        KEY_CB_LOAD,
    ) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + _render_value(
        input_dict,
        KEY_RL_LOAD_VALUE,
    ) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|L{4.4cm}|p{6.7cm}|p{3.0cm}|}
\caption{\textbf{Vehicle Live Loads (LL)}}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\
\hline
\endhead
\textnormal{Vehicles Considered} & """ + _tex(vehicles_str) + r""" & --- \\[6pt]
\hline
\textnormal{Impact Factor (IRC 6)} & """ + _tex(impact_factor_str) + r""" & Dimensionless \\[6pt]
\hline
\textnormal{Braking Load (IRC 6)} & """ + _tex(braking_force_str) + r""" & """ + _tex(braking_force_unit) + r""" \\[6pt]
\hline
\textnormal{Centrifugal Force} & Not available in supplied project-analysis outputs & kN \\[6pt]
\hline
\end{longtable}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|L{4.4cm}|p{6.7cm}|p{3.0cm}|}
\caption{\textbf{Footpath Live Loads}}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\
\hline
\endfirsthead
\multicolumn{3}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\
\hline
\endhead
\textnormal{Footpath Loading Mode} & """ + _tex(fp_mode_str) + r""" & --- \\[6pt]
\hline
\textnormal{Footpath Load Intensity} & """ + _tex(fp_str) + r""" & """ + (r"kN/m\textsuperscript{2}" if footpath_configured else "---") + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{No footpath load is applied: the supplied input has no footpath configured and specifies zero footpath width and count. The IRC footpath pressure mode is therefore not used.}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|L{5.0cm}|p{9.7cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Basic Wind Speed, Vb} & """ + (
        _render_value(input_dict, "wind_speed", " m/s")
        or _render_value(input_dict, KEY_WL_BASIC_WIND_SPEED, " m/s")
        or "Not available in project-location data"
    ) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + _render_value(
        input_dict,
        KEY_WL_TERRAIN_TYPE,
    ) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + _render_value(
        input_dict,
        KEY_WL_AVG_EXPOSED_HEIGHT,
        " m",
    ) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + _tex(vz_str) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + _tex(pz_str) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")
        or r"Not available in stored analysis results") + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")
        or r"Not available in stored analysis results") + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, " kN")
        or r"Not available in stored analysis results") + r""" \\[6pt]
\hline
\end{longtable}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|L{5.0cm}|p{9.7cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Seismic Zone} & """ + _render_value(
        input_dict,
        "seismic_zone",
    ) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + _tex(_sl(sl_zone_factor)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + _render_value(
        input_dict,
        KEY_SL_IMPORTANCE_FACTOR,
    ) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + _render_value(
        input_dict,
        KEY_SL_SOIL_TYPE,
    ) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + _tex(_sl(sl_spectral)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + _tex(_sl(sl_ah)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + _tex(_sl(sl_av)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & Not calculated by the current analysis module \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & Not calculated by the current analysis module \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Seismic zone and coefficient parameters are reported from the available input data. Resultant longitudinal and transverse seismic forces are not currently exposed by the bridge analysis output, so no force values have been inferred.}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|L{5.0cm}|p{9.7cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\endhead
\textnormal{Maximum Shade Temperature} & """ + _render_value(
        input_dict,
        "shade_temp_max",
    ) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + _render_value(
        input_dict,
        "shade_temp_min",
    ) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + _tex(_format_number(bridge_temp_min)) + r""" to """ + _tex(
        _format_number(bridge_temp_max)
    ) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + _tex(
        _format_number(temperature_rise)
    ) + r""" $^\circ$C / \textminus{}""" + _tex(
        _format_number(temperature_fall)
    ) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\ReportTopicBreak
\vspace{1em}
\begin{longtable}{|C{3.6cm}|p{10.8cm}|}
\caption{\textbf{Load Combinations}}\\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\tablename\ \thetable{} -- continued from previous page}\\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
