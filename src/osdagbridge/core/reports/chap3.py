# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
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
    KEY_TS_FOOTPATH_THICKNESS,
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
    KEY_WL_VERTICAL_WIND_FORCE,
)

from osdagbridge.core.reports.report_utils import (
    _tex,
    _render_value,
    make_longtable_header,
)


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Carriageway Live Loads — Vehicle Configuration & Impact Factors
    # ─────────────────────────────────────────────────────────────────────────
    span = input_dict.get(KEY_SPAN)
    span_m = None
    if span not in (None, ""):
        try:
            span_m = float(span)
        except (ValueError, TypeError):
            span_m = None

    # Standard IRC vehicles definition:
    # (key, display_name, vehicle_type, reference_code, analysed_in_fe)
    standard_vehicles = [
        (KEY_LL_IRC_CLASS_A,       "Class A",                    "wheeled", "IRC:6 Cl. 208.2",  True),
        (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)",        "wheeled", "IRC:6 Cl. 208.3",  True),
        (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)",        "tracked", "IRC:6 Cl. 208.3",  False),
        (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",         "wheeled", "IRC:6 Cl. 208.3",  False),
        (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",         "tracked", "IRC:6 Cl. 208.3",  False),
        (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",          "wheeled", "IRC:6 Cl. 208.3",  False),
        (KEY_LL_IRC_CLASS_SV,      "Class SV (Special Vehicle)", "special", "IRC:6 Cl. 204.5.2",False),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",              "fatigue", "IRC:6 Cl. 204.6",  False),
    ]

    veh_rows = []
    for key, name, v_type, ref_code, in_fe in standard_vehicles:
        # Check if selected in UI
        is_selected = bool(input_dict.get(key, False))

        if is_selected:
            sel_str = "Yes"
            if span_m is not None and span_m > 0:
                if v_type == "wheeled":
                    if key == KEY_LL_IRC_CLASS_A:
                        im = IRC6_2017.cl_208_2_impact_factor(span_m)
                    else:
                        # Wheeled vehicles per IRC 6 Cl. 208.3:
                        # 25% for span < 23 m; curve 9.0/(13.5+span) for 23 m <= span <= 45 m; 9/(13.5+45) for > 45 m
                        if span_m < 23.0:
                            im = 0.250
                        elif span_m <= 45.0:
                            im = round(9.0 / (13.5 + span_m), 3)
                        else:
                            im = round(9.0 / (13.5 + 45.0), 3)
                elif v_type == "tracked":
                    # Tracked vehicles per IRC 6 Cl. 208.3:
                    # 25% for span < 5 m; 10% for 5 m <= span <= 45 m; curve for > 45 m
                    if span_m < 5.0:
                        im = 0.250
                    elif span_m <= 45.0:
                        im = 0.100
                    else:
                        im = round(9.0 / (13.5 + 45.0), 3)
                elif v_type in ("special", "fatigue"):
                    # Nil impact allowance per IRC 6 Cl. 204.5.2 and Cl. 204.6
                    im = 0.000
                else:
                    im = 0.000

                allowance_str = f"{im:.3f}"
                multiplier_str = f"{1.0 + im:.3f}"
            else:
                allowance_str = "N/A"
                multiplier_str = "N/A"

            if in_fe:
                status_str = r"Analysed in FE Model"
            elif v_type == "fatigue":
                status_str = r"Fatigue Checks (SLS)"
            else:
                status_str = r"Excluded from FE Model"

            remarks_str = ref_code
        else:
            sel_str = "No"
            allowance_str = "--"
            multiplier_str = "--"
            status_str = r"Excluded from Analysis"
            remarks_str = r"Unselected in UI"

        veh_rows.append(
            r"\textnormal{" + _tex(name) + r"} & "
            + _tex(sel_str) + r" & "
            + _tex(allowance_str) + r" & "
            + _tex(multiplier_str) + r" & "
            + status_str + r" & "
            + _tex(remarks_str) + r""" \\[6pt]
\hline"""
        )

    # Custom vehicles if present in input_dict
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name', 'Custom Vehicle') if isinstance(c, dict) else str(c)
            veh_rows.append(
                r"\textnormal{" + _tex(c_name) + r"} & Yes & N/A & N/A & Excluded from FE Model & User-defined \\[6pt]" + "\n" + r"\hline"
            )

    veh_rows_str = "\n".join(veh_rows)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Centrifugal and Braking Actions Documentation
    # ─────────────────────────────────────────────────────────────────────────
    align_val = input_dict.get('alignment') or input_dict.get('bridge_alignment')
    align_str = str(align_val).strip().lower() if align_val is not None else ""

    radius = (
        input_dict.get('radius_of_curvature')
        or input_dict.get('horizontal_radius')
        or input_dict.get('curvature_radius')
    )
    if radius not in (None, ""):
        try:
            r_val = float(radius)
            if r_val > 0:
                centrifugal_str = (
                    f"Curved alignment noted in inputs (R = {r_val:.1f} m); "
                    f"see IRC 6 Cl. 212.1 for centrifugal force requirements. "
                    f"Note: grillage model uses straight geometry; centrifugal force not applied in structural analysis."
                )
            else:
                centrifugal_str = "N/A (Invalid radius R <= 0 specified per IRC 6 Cl. 212)"
        except (ValueError, TypeError):
            centrifugal_str = "N/A (Invalid radius format specified per IRC 6 Cl. 212)"
    elif align_str in ("straight", "tangent"):
        centrifugal_str = "N/A (Straight Alignment per IRC 6, Clause 212.1)"
    elif align_str in ("curved", "curve"):
        centrifugal_str = (
            "Curved alignment noted in inputs (radius not specified); "
            "see IRC 6 Cl. 212.1 for centrifugal force requirements. "
            "Note: grillage model uses straight geometry; centrifugal force not applied in structural analysis."
        )
    elif align_str != "":
        centrifugal_str = f"N/A (Alignment '{align_val}' not recognized per IRC 6 Cl. 212)"
    else:
        centrifugal_str = "N/A (Alignment unknown / not specified in inputs per IRC 6 Cl. 212)"

    bl_sv = input_dict.get(KEY_BL_IRC_CLASS_SV)
    bl_sv_str = "Included" if bl_sv else "Excluded"
    ecc = input_dict.get(KEY_LL_ECCENTRICITY)
    if ecc not in (None, ""):
        try:
            ecc_str = f"{float(ecc):.2f} m"
        except (ValueError, TypeError):
            ecc_str = f"{ecc} m"
    else:
        ecc_str = "1.20 m"

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Footway Live Load Parameters
    # ─────────────────────────────────────────────────────────────────────────
    footpath_cfg = str(input_dict.get(KEY_FOOTPATH, 'None')).strip()
    has_footpath = footpath_cfg.lower() not in ('none', '', '0')

    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, 'As per IRC 6')).strip()
    fp_custom_val = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

    if not has_footpath:
        fp_status_display = "None (No footway provided on typical section)"
        fp_width_display = "N/A"
        fp_mode_display = "N/A"
        fp_pressure_display = "N/A"
    else:
        fp_status_display = footpath_cfg
        width_val = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
        fp_width_display = f"{float(width_val):.2f} m" if width_val not in (None, "") else "1.50 m"

        if fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic", ""):
            fp_mode_display = "As per IRC 6 Cl. 206.1"
            try:
                irc_fp = IRC6_2017.cl_206_1_footway_load()
                fp_pressure_display = f"{irc_fp:.3f} kN/m\\textsuperscript{{2}} (500 kg/m\\textsuperscript{{2}})"
            except Exception:
                fp_pressure_display = "4.905 kN/m\\textsuperscript{2} (500 kg/m\\textsuperscript{2})"
        elif fp_custom_val not in (None, ""):
            fp_mode_display = "User-defined Custom Pressure"
            fp_pressure_display = f"{float(fp_custom_val):.3f} kN/m\\textsuperscript{{2}}"
        else:
            fp_mode_display = "As per IRC 6 Cl. 206.1"
            fp_pressure_display = "4.905 kN/m\\textsuperscript{2} (500 kg/m\\textsuperscript{2})"

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Wind, Seismic, Temperature & Load Combinations
    # ─────────────────────────────────────────────────────────────────────────
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
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

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

    wc_mat = _render_value(input_dict, KEY_WC_MATERIAL) or _render_value(input_dict, "wearing_coat_type")
    wc_thk = _render_value(input_dict, KEY_WC_THICKNESS, " mm") or _render_value(input_dict, "wearing_coat_thickness", " mm")
    if wc_mat and wc_thk:
        wc_load_display = f"{wc_mat} ({wc_thk})"
    elif wc_mat:
        wc_load_display = wc_mat
    elif wc_thk:
        wc_load_display = wc_thk
    else:
        wc_load_display = "---"

    cb_load = _render_value(input_dict, KEY_CB_LOAD) or _render_value(input_dict, "crash_barrier_load")
    cb_load_display = f"{cb_load} kN/m per barrier" if cb_load else "---"

    rl_load = _render_value(input_dict, KEY_RL_LOAD_VALUE) or _render_value(input_dict, "railing_load")
    rl_load_display = f"{rl_load} kN/m\\sdstar{{}}" if rl_load else "---"

    max_shade = _render_value(input_dict, 'shade_temp_max')
    max_shade_display = f"{max_shade} $^\\circ$C" if max_shade else "---"
    min_shade = _render_value(input_dict, 'shade_temp_min')
    min_shade_display = f"{min_shade} $^\\circ$C" if min_shade else "---"

    bt_min = _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)
    bt_max = _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)
    if bt_min and bt_max:
        eff_range_display = f"{bt_min} to {bt_max} $^\\circ$C"
    elif bt_min:
        eff_range_display = f"{bt_min} $^\\circ$C"
    elif bt_max:
        eff_range_display = f"{bt_max} $^\\circ$C"
    else:
        eff_range_display = "---"

    tr = _render_value(input_dict, KEY_TL_TEMP_RISE)
    tf = _render_value(input_dict, KEY_TL_TEMP_FALL)
    if tr and tf:
        rise_fall_display = f"+{tr} $^\\circ$C / \\textminus{{}}{tf} $^\\circ$C"
    elif tr:
        rise_fall_display = f"+{tr} $^\\circ$C"
    elif tf:
        rise_fall_display = f"\\textminus{{}}{tf} $^\\circ$C"
    else:
        rise_fall_display = "---"

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Dead Load -- Self Weight}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}') or "---") + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}') or "---") + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR) or "---") + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Dead Load for Surfacing (DW)}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Wearing Course Load} & """ + wc_load_display + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + cb_load_display + r""" \\[6pt]
\hline
\textnormal{Railing Load} & """ + rl_load_display + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{3.6cm}|C{1.8cm}|C{2.2cm}|C{2.2cm}|p{3.2cm}|p{2.4cm}|",
    caption=r"\textbf{Carriageway Live Loads (IRC 6)}",
    header_row=r"\textbf{Vehicle Class} & \textbf{UI Selected} & \textbf{Impact Allowance ($i$)} & \textbf{Impact Factor ($1+i$)} & \textbf{Analysis Status} & \textbf{Remarks}",
) + veh_rows_str + r"""
\end{longtable}

\vspace{0.4em}
\noindent\textbf{Longitudinal Braking Force (IRC 6 Cl. 211):} Braking force acts longitudinally along the roadway at a height of """ + ecc_str + r""" above the deck surface (bearing/substructure action). While evaluated for bearing reaction and pier design per IRC 6 Cl. 211.2, longitudinal braking forces are not applied to the superstructure vertical grillage model. Class SV braking opt-in: \textbf{""" + bl_sv_str + r"""}.

\vspace{0.4em}
\noindent\textbf{Centrifugal Force (IRC 6 Cl. 212):} \textbf{""" + _tex(centrifugal_str) + r"""}.

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Footway Live Loads (FL)}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Footway Configuration} & """ + _tex(fp_status_display) + r""" \\[6pt]
\hline
\textnormal{Clear Footway Width} & """ + _tex(fp_width_display) + r""" \\[6pt]
\hline
\textnormal{Loading Mode} & """ + _tex(fp_mode_display) + r""" \\[6pt]
\hline
\textnormal{Design Live Load Pressure} & """ + fp_pressure_display + r""" \\[6pt]
\hline
\textnormal{Pressure Unit} & kN/m\textsuperscript{2} \\[6pt]
\hline
\textnormal{Reference Code} & IRC:6-2017 Clause 206.1 \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Wind Load (WL) --- per IRC 6}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s') or "---") + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE) or "---") + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m') or "---") + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s') or "---") + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}') or "---") + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN') or "---") + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN') or "---") + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN') or "---") + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Earthquake Load (EL) --- per IRC 6}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone') or "---") + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR) or "---") + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR) or "---") + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE) or "---") + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF) or "---") + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF) or "---") + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF) or "---") + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & --- \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & --- \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|L{5.5cm}|p{10.0cm}|",
    caption=r"\textbf{Temperature Load (TL) --- per IRC 6}",
    header_row=r"\textbf{Parameter} & \textbf{Value}",
) + r"""\textnormal{Maximum Shade Temperature} & """ + max_shade_display + r""" \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + min_shade_display + r""" \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + eff_range_display + r""" \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & """ + rise_fall_display + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
""" + make_longtable_header(
    col_spec=r"|C{4.0cm}|p{11.5cm}|",
    caption=r"\textbf{Load Combinations}",
    header_row=r"\textbf{Combination ID} & \textbf{Load Cases}",
) + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
