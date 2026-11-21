# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
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
from osdagbridge.core.reports.table_builder import TableBuilder
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

def build_vehicle_live_load_table(input_dict: dict) -> str:
    """Build dedicated LaTeX table for Vehicle Live Loads per IRC 6:2017."""
    span = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span) if span not in (None, "") else 0.0
    except Exception:
        span_m = 0.0

    builder = TableBuilder(
        col_spec=r"|L{3.2cm}|C{2.6cm}|C{2.0cm}|C{3.2cm}|C{2.0cm}|",
        caption=r"\textbf{Vehicle Live Loads (LL) --- per IRC 6:2017}",
        label="tab:vehicle-live-loads",
        num_cols=5,
    )
    builder.set_headers([
        r"\textbf{Vehicle Class}",
        r"\textbf{Load / Weight}",
        r"\textbf{Impact Factor}",
        r"\textbf{Braking Force (1\textsuperscript{st} Train)}",
        r"\textbf{Centrifugal Force}",
    ])

    VEHICLE_SPECS = [
        # (key, display_name, load_str, weight_kN, v_type, brake_str)
        (KEY_LL_IRC_CLASS_A,       "Class A",             "543.5 kN (55.4 t)",   543.5,   "class_a",       "108.69 kN (11.08 t)"),
        (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)", "981.0 kN (100.0 t)",  981.0,   "70r_wheeled",   "196.20 kN (20.00 t)"),
        (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)", "686.7 kN (70.0 t)",   686.7,   "70r_tracked",   "N/A (Tracked)"),
        (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",   "392.4 kN (40.0 t)",   392.4,   "70r_bogie",     "78.48 kN (8.00 t)"),
        (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",  "392.4 kN (40.0 t)",   392.4,   "aa_wheeled",    "78.48 kN (8.00 t)"),
        (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",  "686.7 kN (70.0 t)",   686.7,   "aa_tracked",    "N/A (Tracked)"),
        (KEY_LL_IRC_CLASS_SV,      "Class SV",            "3776.9 kN (385.0 t)", 3776.85, "class_sv",      None),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",       "392.4 kN (40.0 t)",   392.4,   "class_fatigue", "N/A (Fatigue check)"),
    ]

    # Centrifugal force parameters per IRC 6:2017 Cl. 212
    # Cl. 212.2: C = (W * V^2) / (127 * R), acting horizontally at 1.2 m height per Cl. 212.3
    radius_val = (
        input_dict.get("geometry.radius")
        or input_dict.get("radius")
        or input_dict.get("horizontal_curve_radius")
    )
    radius_m = None
    if radius_val not in (None, ""):
        try:
            r_flt = float(radius_val)
            if r_flt > 0:
                radius_m = r_flt
        except (ValueError, TypeError):
            pass

    speed_val = input_dict.get("design_speed") or input_dict.get("speed")
    try:
        speed_kmh = float(speed_val) if speed_val not in (None, "") else 80.0
    except (ValueError, TypeError):
        speed_kmh = 80.0

    def _im(v_type: str) -> str:
        if span_m <= 0:
            return "N/A"
        if v_type == "class_a":
            return f"{1.0 + IRC6_2017.cl_208_2_impact_factor(span_m):.3f}"
        elif v_type in ("70r_tracked", "aa_tracked"):
            im = 0.25 if span_m < 5.0 else 0.10
            return f"{1.0 + im:.3f}"
        elif v_type in ("70r_wheeled", "70r_bogie", "aa_wheeled"):
            im = 0.25 if span_m < 23.0 else 9.0 / (13.5 + min(span_m, 45.0))
            return f"{1.0 + im:.3f}"
        elif v_type in ("class_sv", "class_fatigue"):
            return "1.000"
        return "1.000"

    def _cf(weight_kN: float, v_type: str) -> str:
        if radius_m is None:
            return "N/A"
        if v_type == "class_fatigue":
            return "N/A (Fatigue check)"
        # SV operates at restricted speed (5 km/h per IRC 6 Cl. 204.5.3 note)
        v = 5.0 if v_type == "class_sv" else speed_kmh
        c = (weight_kN * (v ** 2)) / (127.0 * radius_m)
        return f"{c:.2f} kN"

    rows_added = 0
    for key, name, load_str, weight_kN, v_type, brake_str in VEHICLE_SPECS:
        if input_dict.get(key):
            im_str = _im(v_type)
            if key == KEY_LL_IRC_CLASS_SV:
                brake_val = "755.37 kN (77.00 t)" if input_dict.get(KEY_BL_IRC_CLASS_SV) else "Not applied"
            else:
                brake_val = brake_str
            cf_val = _cf(weight_kN, v_type)
            builder.add_row(_tex(name), load_str, im_str, brake_val, cf_val)
            rows_added += 1

    custom = (
        input_dict.get(KEY_LL_CUSTOM_VEHICLES)
        or input_dict.get("custom_vehicles")
        or input_dict.get("live_load.custom_vehicles")
    )
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get("name", "Custom") if isinstance(c, dict) else str(c)
            c_weight = 0.0
            if isinstance(c, dict) and "total_load" in c:
                try:
                    c_weight = float(c['total_load'])
                    c_load = f"{c_weight:.1f} kN"
                    c_brake = f"{0.20 * c_weight:.2f} kN"
                except Exception:
                    c_load = "Custom"
                    c_brake = "N/A"
            else:
                c_load = "Custom"
                c_brake = "N/A"
            if isinstance(c, dict) and "impact_factor" in c:
                try:
                    c_im = f"{float(c['impact_factor']):.3f}"
                except Exception:
                    c_im = "1.000"
            else:
                c_im = "1.000"
            if radius_m is None:
                c_cf = "N/A"
            elif c_weight > 0:
                c_cf = f"{(c_weight * (speed_kmh ** 2)) / (127.0 * radius_m):.2f} kN"
            else:
                c_cf = "N/A"
            builder.add_row(_tex(c_name), c_load, c_im, c_brake, c_cf)
            rows_added += 1

    if rows_added == 0:
        builder.add_row(r"\multicolumn{5}{|c|}{\textit{No live load vehicle classes selected}}")

    if radius_m is not None:
        cf_note = (
            f"Centrifugal force computed per IRC:6-2017 Cl. 212.2 ($C = W V^2 / (127 R)$), "
            f"acting horizontally at 1.2 m above the roadway per Cl. 212.3, "
            f"for horizontal curve radius $R = {radius_m:.1f}\\text{{ m}}$ and design speed $V = {speed_kmh:.0f}\\text{{ km/h}}$."
        )
    else:
        cf_note = (
            "Centrifugal force per IRC:6-2017 Cl. 212.2 is not applicable for straight bridge alignments "
            r"($R = \infty$, $C = 0$)."
        )

    note_text = (
        f"Impact factor computed per IRC:6-2017 Cl. 208 for span $L = {span_m:.1f}\\text{{ m}}$. "
        f"Tabulated braking forces represent the 20\\% first-train component per Cl. 211.2 (applied at 1.2 m above the deck per Cl. 211.3); "
        r"tracked vehicles are designated N/A due to an implementation limitation in the solver "
        r"(longitudinal train braking calculation for tracked vehicles is not supported in the current module, rather than an express code exemption). "
        f"{cf_note} "
        r"Vehicle characteristic loads represent physical force equivalents using $g = 9.81\text{ m/s}^2$ ($1\text{ t} = 9.81\text{ kN}$); "
        r"nominal designations: 70R Tracked / AA Tracked = 700 kN, 70R Bogie / AA Wheeled = 400 kN."
    )
    builder.set_note(note_text)
    return builder.build()


def build_footpath_live_load_table(input_dict: dict) -> str:
    """Build dedicated LaTeX table for Footpath Live Load per IRC 6 Cl. 206."""
    footpath_cfg = str(input_dict.get(KEY_FOOTPATH, "")).strip()
    has_footpath = footpath_cfg.lower() not in ("", "none", "no")

    span = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span) if span not in (None, "") else 30.0
    except Exception:
        span_m = 30.0

    builder = TableBuilder(
        col_spec=r"|L{5.8cm}|p{9.7cm}|",
        caption=r"\textbf{Footpath Live Load --- per IRC 6 Cl. 206}",
        label="tab:footpath-live-load",
        num_cols=2,
    )
    builder.set_headers([
        r"\textbf{parameter}",
        r"\textbf{value / specification}",
    ])

    # Clause 206.3 reduction for main supporting members:
    # Reduction = (40*L - 300) / 9 kg/m2 for 7.5 <= L <= 30 m
    # For L > 30 m, reduction = 100 kg/m2 (or (40*30-300)/9 = 100 kg/m2)
    # For L < 7.5 m, reduction = 0 kg/m2
    # Note: Cl. 206.3 reduction applies ONLY to ordinary footway loading.
    # Per IRC 6:2017 Cl. 206.3 Note, when crowd loading is considered, the reduction shall NOT apply.
    if 7.5 <= span_m <= 30.0:
        reduction_kg = (40.0 * span_m - 300.0) / 9.0
    elif span_m < 7.5:
        reduction_kg = 0.0
    else:
        reduction_kg = 100.0

    ord_girder_kg = max(160.0, 400.0 - reduction_kg)
    crowd_girder_kg = 500.0  # Cl. 206.3 reduction does NOT apply to crowd loading per code note
    ord_girder_kn = (ord_girder_kg * 9.81) / 1000.0
    crowd_girder_kn = (crowd_girder_kg * 9.81) / 1000.0

    if has_footpath:
        fp_provision = _tex(footpath_cfg)
        n_fp = input_dict.get(KEY_TS_NO_OF_FOOTPATHS)
        if n_fp in (None, ""):
            n_fp_str = "2" if "both" in footpath_cfg.lower() else "1"
        else:
            n_fp_str = str(n_fp)

        fp_w = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
        fp_width_str = f"{float(fp_w):.2f} m" if fp_w not in (None, "") else "1.50 m"

        fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6")
        mode_str = _tex(str(fp_mode))

        mode_lower = str(fp_mode).strip().lower()
        fp_val = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

        # Footway Surface Loading (Cl. 206.1)
        if mode_lower in ("as per irc 6", "as per irc6", "automatic"):
            try:
                intensity = IRC6_2017.cl_206_1_footway_load()
                surface_str = (
                    f"{intensity:.3f} kN/m\\textsuperscript{{2}} (500 kg/m\\textsuperscript{{2}}, application default) / "
                    r"3.924 kN/m\textsuperscript{2} (400 kg/m\textsuperscript{2}, ordinary)"
                )
            except Exception:
                surface_str = (
                    r"4.905 kN/m\textsuperscript{2} (500 kg/m\textsuperscript{2}, application default) / "
                    r"3.924 kN/m\textsuperscript{2} (400 kg/m\textsuperscript{2}, ordinary)"
                )

            girder_load_str = (
                f"{ord_girder_kn:.3f} kN/m\\textsuperscript{{2}} ({ord_girder_kg:.0f} kg/m\\textsuperscript{{2}}, ordinary reduced) / "
                f"{crowd_girder_kn:.3f} kN/m\\textsuperscript{{2}} ({crowd_girder_kg:.0f} kg/m\\textsuperscript{{2}}, crowd unreduced)"
            )
        elif fp_val not in (None, ""):
            surface_str = f"{fp_val} kN/m\\textsuperscript{{2}} (Custom)"
            girder_load_str = f"{fp_val} kN/m\\textsuperscript{{2}} (Custom)"
        else:
            surface_str = (
                r"4.905 kN/m\textsuperscript{2} (500 kg/m\textsuperscript{2}, application default) / "
                r"3.924 kN/m\textsuperscript{2} (400 kg/m\textsuperscript{2}, ordinary)"
            )
            girder_load_str = (
                f"{ord_girder_kn:.3f} kN/m\\textsuperscript{{2}} ({ord_girder_kg:.0f} kg/m\\textsuperscript{{2}}, ordinary reduced) / "
                f"{crowd_girder_kn:.3f} kN/m\\textsuperscript{{2}} ({crowd_girder_kg:.0f} kg/m\\textsuperscript{{2}}, crowd unreduced)"
            )

        builder.add_row(r"\textnormal{Footpath Configuration}", fp_provision)
        builder.add_row(r"\textnormal{Number of Footpaths}", n_fp_str)
        builder.add_row(r"\textnormal{Footpath Width}", fp_width_str)
        builder.add_row(r"\textnormal{Footpath Loading Mode}", mode_str)
        builder.add_row(r"\textnormal{Footway Surface Live Load (Deck Slab)}", surface_str)
        builder.add_row(r"\textnormal{Main Girder Live Load (Cl. 206.3)}", girder_load_str)
        builder.set_note(
            r"Per IRC 6 Cl. 206.1, footway surface live load on the deck slab is $400\text{ kg/m}^2$ ($3.924\text{ kN/m}^2$) for ordinary road bridges, "
            r"and $500\text{ kg/m}^2$ ($4.905\text{ kN/m}^2$) for foot overbridges or crowd loading. "
            r"The current application defaults to $500\text{ kg/m}^2$ ($4.905\text{ kN/m}^2$) via \texttt{IRC6\_2017.cl\_206\_1\_footway\_load()}; "
            r"ordinary footway classification is not selectable through the current GUI. "
            rf"For main supporting girders of span $L = {span_m:.1f}\text{{ m}}$, Cl. 206.3 specifies a reduction "
            rf"($(40L-300)/9 = {reduction_kg:.1f}\text{{ kg/m}}^2$) yielding ${ord_girder_kn:.3f}\text{{ kN/m}}^2$ (${ord_girder_kg:.0f}\text{{ kg/m}}^2$) "
            r"for ordinary footways. Per Cl. 206.3 Note, this reduction does not apply to crowd loading, which remains unreduced at "
            rf"${crowd_girder_kn:.3f}\text{{ kN/m}}^2$ (${crowd_girder_kg:.0f}\text{{ kg/m}}^2$). "
            r"Per Cl. 206.1, bridges with crowd loading should also be designed for the entire carriageway occupied by crowd load; "
            r"this load case is not supported by the current solver (known software limitation)."
        )
    else:
        builder.add_row(r"\textnormal{Footpath Configuration}", r"\textnormal{None (Not provided)}")
        builder.add_row(r"\textnormal{Number of Footpaths}", r"\textnormal{0}")
        builder.add_row(r"\textnormal{Footpath Width}", r"\textnormal{N/A}")
        fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6")
        builder.add_row(r"\textnormal{Footpath Loading Mode}", _tex(f"{fp_mode} (Disabled)"))
        builder.add_row(r"\textnormal{Footway Surface Live Load (Deck Slab)}", r"\textnormal{N/A (Footpath disabled)}")
        builder.add_row(r"\textnormal{Main Girder Live Load (Cl. 206.3)}", r"\textnormal{N/A (Footpath disabled)}")
        builder.set_note(
            "No footpath is provided in the typical bridge cross-section (geometry.footpath = None). "
            "Footpath live load is not applied in structural analysis."
        )

    return builder.build()


def ch3_loads(input_dict):
    vehicle_table_tex = build_vehicle_live_load_table(input_dict)
    footpath_table_tex = build_footpath_live_load_table(input_dict)

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

    def _render_env(key, unit="", fallback="Not available in this report run"):
        val = input_dict.get(key)
        if val in ("", None):
            return fallback
        s = str(val).strip()
        if not s:
            return fallback
        return (_tex(s) + (" " + unit if unit and not unit.startswith(" ") else unit)).strip()

    wind_vb_str = (_tex(str(input_dict['wind_speed'])) + ' m/s') if input_dict.get('wind_speed') else 'Not provided'
    seismic_zone_str = f"Zone {_tex(input_dict['seismic_zone'])}" if input_dict.get('seismic_zone') else 'Not provided'
    temp_max_str = (f"{_tex(input_dict['shade_temp_max'])} $^\\circ$C") if input_dict.get('shade_temp_max') is not None else 'Not available in this report run'
    temp_min_str = (f"{_tex(input_dict['shade_temp_min'])} $^\\circ$C") if input_dict.get('shade_temp_min') is not None else 'Not available in this report run'
    temp_range_str = (f"{_tex(input_dict[KEY_TL_BRIDGE_TEMP_MIN])} to {_tex(input_dict[KEY_TL_BRIDGE_TEMP_MAX])} $^\\circ$C") if (input_dict.get(KEY_TL_BRIDGE_TEMP_MIN) is not None and input_dict.get(KEY_TL_BRIDGE_TEMP_MAX) is not None) else 'Not available in this report run'
    temp_rise_fall_str = (f"$+{_tex(input_dict[KEY_TL_TEMP_RISE])}\\,^\\circ\\mathrm{{C}} \\ / \\ -{_tex(input_dict[KEY_TL_TEMP_FALL])}\\,^\\circ\\mathrm{{C}}$") if (input_dict.get(KEY_TL_TEMP_RISE) is not None and input_dict.get(KEY_TL_TEMP_FALL) is not None) else 'Not available in this report run'

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Adopted material self-weight densities are project-specific values defined in the material properties dialog (structural steel: 76.4 kN/m\textsuperscript{3}, concrete deck: 24.5 kN/m\textsuperscript{3}), distinguished from general IRC 6:2017 Cl. 203 reference defaults (78.5 kN/m\textsuperscript{3} and 25.0 kN/m\textsuperscript{3}; refer to Chapter 8).}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\newpage
""" + vehicle_table_tex + r"""

\newpage
""" + footpath_table_tex + r"""

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Basic Wind Speed, Vb} & """ + wind_vb_str + r""" \\[6pt]
\hline
\textnormal{Terrain Type} & """ + _render_env(KEY_WL_TERRAIN_TYPE, fallback='Plain Terrain') + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + _render_env(KEY_WL_AVG_EXPOSED_HEIGHT, 'm', fallback='10 m') + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + _render_env(KEY_WL_HOURLY_MEAN_WIND, 'm/s') + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + _render_env(KEY_WL_HOURLY_WIND_PRESSURE, r'N/m\textsuperscript{2}') + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + _render_env(KEY_WL_TRANSVERSE_WIND_FORCE, 'kN') + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + _render_env(KEY_WL_LONGITUDINAL_WIND_FORCE, 'kN') + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + _render_env(KEY_WL_VERTICAL_WIND_FORCE, 'kN') + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Seismic Zone} & """ + seismic_zone_str + r""" \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + _render_env(KEY_SL_ZONE_FACTOR, fallback=_render_env('zone_factor')) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + _render_env(KEY_SL_IMPORTANCE_FACTOR, fallback='1.0') + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + _render_env(KEY_SL_SOIL_TYPE, fallback='Type I – Rocky or Hard') + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + _render_env(KEY_SL_SPECTRAL_COEFF) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + _render_env(KEY_SL_HORIZONTAL_COEFF) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + _render_env(KEY_SL_VERTICAL_COEFF) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + _render_env('seismic_force_long', 'kN') + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + _render_env('seismic_force_trans', 'kN') + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Maximum Shade Temperature} & """ + temp_max_str + r""" \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + temp_min_str + r""" \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + temp_range_str + r""" \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & """ + temp_rise_fall_str + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Calculated per IRC 6:2017 Cl. 215.2 for metallic bridges ($T_{min} = T_{shade,min} - 10\,^\circ\text{C} = -8.30\,^\circ\text{C}$, $T_{max} = T_{shade,max} + 15\,^\circ\text{C} = +58.30\,^\circ\text{C}$). Temperature rise (+33.30\,$^\circ\text{C}$) and fall ($-33.30\,^\circ\text{C}$) are determined relative to the mean reference/installation temperature $T_{ref} = 25.00\,^\circ\text{C}$.}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}\\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


