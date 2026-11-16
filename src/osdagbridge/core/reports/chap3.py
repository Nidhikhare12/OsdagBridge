# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
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
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_DENSITY,
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
from osdagbridge.core.reports.latex.text import vspace
from osdagbridge.core.reports.data.live_loads import collect_live_loads

from osdagbridge.core.reports.theme import get_active_theme

# Printed wherever the software has no value for a cell (never a bare unit).
_DASH = "---"
_NOT_APPLICABLE = "N/A"


def _value(source_dict, key, unit=""):
    """Value followed by its unit, or ``---`` when the value is missing."""
    return _render_value(source_dict, key, unit) or _DASH


def _missing(source_dict, *keys):
    """True when none of the keys holds a value."""
    return all(source_dict.get(k) in ("", None) for k in keys)


def _number(value, spec):
    return format(value, spec) if value is not None else _DASH


def _name_list(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def _vehicle_live_load_table(ll_data):
    """Table "Vehicular Live Loads" (Requirement R3): one row per vehicle selected
    in the Loading tab, two-level header with the Braking Load group."""
    size = get_active_theme().typography.note_font_size
    widths = (
        ("L", "2.5cm"), ("C", "1.4cm"), ("C", "1.3cm"), ("C", "2.2cm"),
        ("C", "1.1cm"), ("C", "2.15cm"), ("C", "2.05cm"),
    )
    columns = "|" + "|".join(f">{{{size}}}{kind}{{{w}}}" for kind, w in widths) + "|"

    def _head(*lines):
        cell = r"\\".join(rf"\textbf{{{ln}}}" for ln in lines)
        return rf"\multirow{{2}}{{*}}{{\makecell{{{cell}}}}}"

    header = "\n".join([
        r"\hline",
        " & ".join([
            _head("Vehicle"),
            _head("Total", "Load", "(kN)"),
            _head("Impact", "Factor"),
            rf"\multicolumn{{3}}{{c|}}{{{size}\textbf{{Braking Load}}}}",
            _head("Centrifugal", "Force", "(kN)"),
        ]) + r" \\",
        r"\cline{4-6}",
        r" & & & \textbf{Considered?} & \makecell{\textbf{Value}\\\textbf{(kN)}}"
        r" & \makecell{\textbf{Eccentricity}\\\textbf{(m)}} & \\",
        r"\hline",
    ])

    table = ReportTable(
        columns=columns,
        caption=r"\textbf{Vehicular Live Loads --- per IRC 6:2017}",
        header_tex=header,
    )
    for v in ll_data.vehicles:
        if v.braking_considered:
            braking = ["Yes", _number(v.braking_value_kN, ".2f"), _number(v.braking_eccentricity_m, "g")]
        else:
            braking = ["No", _NOT_APPLICABLE, _NOT_APPLICABLE]
        table.add_row([
            _tex(v.name),
            _number(v.total_load_kN, ".2f"),
            _number(v.impact_factor, ".3f"),
            *braking,
            _NOT_APPLICABLE,
        ])
    if not ll_data.vehicles:
        table.add_span_row("No vehicle is selected in the Loading tab.")
    return table


def _vehicle_live_load_note(ll_data):
    """Sources of the printed values and a plain list of the cells left as ``---``."""
    gaps = []
    by_reason = {}
    for v in ll_data.vehicles:
        if v.total_load_kN is None:
            by_reason.setdefault(v.total_load_gap or "not available", []).append(v.name)
    for reason, names in by_reason.items():
        gaps.append(f"Total Load of {_name_list(names)} ({reason})")
    by_reason = {}
    for v in ll_data.vehicles:
        if v.impact_factor is None:
            by_reason.setdefault(v.impact_factor_gap or "not available", []).append(v.name)
    for reason, names in by_reason.items():
        gaps.append(f"Impact Factor of {_name_list(names)} ({reason})")
    considered = [v for v in ll_data.vehicles if v.braking_considered]
    if considered and ll_data.braking_force_kN is None:
        gaps.append(f"Braking Load value ({ll_data.braking_gap or 'not available'})")
    if considered and any(v.braking_eccentricity_m is None for v in considered):
        gaps.append("Braking Load eccentricity (not entered in the Loading tab)")

    notes = [
        "Vehicles are those selected in the Loading tab of the Additional Inputs.",
        "Total Load is the sum of the axle loads of the vehicle as defined in the software "
        "(IRC 6:2017 Cl. 204.1 for Class A and Class 70R wheeled, Cl. 204.5 for Class SV, "
        "Cl. 204.6 for the fatigue vehicle).",
        "Impact Factor is $1 + I$, with $I$ from Cl. 208.2 for Class A and from Cl. 208.3 "
        "for Class AA and Class 70R.",
        "Braking Load: ``Considered?'' and the eccentricity (height of the braking force above "
        "the top of the deck, Cl. 211.3) are the Loading tab inputs"
        + ("; the value is the Cl. 211.2 force for the bridge, the same in every row."
           if ll_data.braking_force_kN is not None else "."),
    ]
    if gaps:
        notes.append(
            f"A cell showing {_DASH} is a value the software does not compute: "
            + "; ".join(_tex(g) for g in gaps) + "."
        )
    notes.append(
        f"Centrifugal forces are not evaluated (straight alignment assumed), so that column "
        f"reads {_NOT_APPLICABLE}."
    )
    body = " ".join(f"({i}) {text}" for i, text in enumerate(notes, start=1))
    return rf"\noindent{{{get_active_theme().typography.note_font_size}\textit{{Notes: {body}}}\par}}"


def _footpath_live_load_table(ll_data):
    """Table "Footpath Live Load" (Requirement R3): always emitted."""
    fp = ll_data.footpath
    if fp is None:
        rows = [("Footpath", "Not provided in this configuration")]
    else:
        rows = [
            (r"Footpath Live Load Intensity (kN/m\textsuperscript{2})", _number(fp.intensity_kN_m2, "g")),
            ("Number of Footpaths", f"{fp.count}"),
            ("Footpath Width (m)", _number(fp.width_m, "g")),
            ("Pressure Mode", _tex(fp.mode) if fp.mode else _DASH),
            ("Clause", _tex(fp.clause)),
        ]
    return KeyValueTable(
        caption=r"\textbf{Footpath Live Load --- per IRC 6:2017}",
        preset=("5.5cm", "10.0cm"),
        headers=("Parameter", "Value"),
        rows=rows,
    )


def ch3_loads(input_dict):
    theme = get_active_theme()
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

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
        headers=("Parameter", "Value"),
        rows=[
            ("Steel Self-Weight Applied", _value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r" kN/m\textsuperscript{3}")),
            ("Concrete Deck Weight", _value(input_dict, KEY_MATERIAL_DECK_DENSITY, r" kN/m\textsuperscript{3}")),
            ("Self-Weight Factor", _value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)),
        ],
    )

    # 2. Dead Load Surfacing
    # The wearing-course load itself is not an engine output; the inputs that
    # define it are printed with their units (density in kN/m3, thickness in mm).
    if _missing(input_dict, KEY_WC_MATERIAL, KEY_WC_DENSITY, KEY_WC_THICKNESS):
        wearing_course = _DASH
    else:
        wc_density = _value(input_dict, KEY_WC_DENSITY, r" kN/m\textsuperscript{3}")
        wc_thickness = _value(input_dict, KEY_WC_THICKNESS, " mm")
        wearing_course = (
            f"{_value(input_dict, KEY_WC_MATERIAL)}: density {wc_density}, thickness {wc_thickness}"
        )
    t_dw = KeyValueTable(
        caption=r"\textbf{Dead Load for Surfacing (DW)}",
        preset=("5.5cm", "10.0cm"),
        headers=("Parameter", "Value"),
        rows=[
            ("Wearing Course Load", wearing_course),
            ("Additional SIDL (Crash Barrier)", _value(input_dict, KEY_CB_LOAD, " kN/m per barrier")),
            ("Railing Load", _value(input_dict, KEY_RL_LOAD_VALUE, r" kN/m\sdstar{}")),
        ],
    )

    # 3. Vehicular Live Loads and 4. Footpath Live Load (Requirement R3)
    ll_data = collect_live_loads(input_dict)
    t_veh = _vehicle_live_load_table(ll_data)
    veh_note = _vehicle_live_load_note(ll_data)
    t_fp = _footpath_live_load_table(ll_data)

    # 5. Wind Load
    t_wl = KeyValueTable(
        caption=r"\textbf{Wind Load (WL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("Parameter", "Value"),
        rows=[
            ("Basic Wind Speed, Vb", _value(input_dict, 'wind_speed', ' m/s [from Project Location]')),
            ("Terrain Type", _value(input_dict, KEY_WL_TERRAIN_TYPE)),
            ("Average Exposed Height, H (m)", _value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, " m")),
            ("Hourly Mean Wind Speed, Vz", _value(input_dict, KEY_WL_HOURLY_MEAN_WIND, " m/s")),
            ("Hourly Wind Pressure, Pz", _value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r" N/m\textsuperscript{2}")),
            ("Transverse Wind Force", _value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")),
            ("Longitudinal Wind Force", _value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")),
            ("Vertical Wind Force", _value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, " kN")),
        ],
    )

    # 6. Earthquake Load
    t_el = KeyValueTable(
        caption=r"\textbf{Earthquake Load (EL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("Parameter", "Value"),
        rows=[
            ("Seismic Zone", _value(input_dict, 'seismic_zone', ' [from Project Location]')),
            ("Zone Factor, Z", _value(input_dict, KEY_SL_ZONE_FACTOR)),
            ("Importance Factor, I", _value(input_dict, KEY_SL_IMPORTANCE_FACTOR)),
            ("Type of Soil", _value(input_dict, KEY_SL_SOIL_TYPE)),
            ("Sa/g", _value(input_dict, KEY_SL_SPECTRAL_COEFF)),
            ("Horizontal Seismic Coefficient, Ah", _value(input_dict, KEY_SL_HORIZONTAL_COEFF)),
            ("Vertical Seismic Coefficient, Av", _value(input_dict, KEY_SL_VERTICAL_COEFF)),
            # The seismic forces are not available to the report layer: no value, no unit.
            ("Horizontal Seismic Force (longitudinal)", _DASH),
            ("Horizontal Seismic Force (transverse)", _DASH),
        ],
    )

    # 7. Temperature Load
    deg_c = r" $^\circ$C"
    if _missing(input_dict, KEY_TL_BRIDGE_TEMP_MIN, KEY_TL_BRIDGE_TEMP_MAX):
        bridge_temp_range = _DASH
    else:
        bridge_temp_range = (
            f"{_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN, deg_c)} to "
            f"{_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX, deg_c)}"
        )
    if _missing(input_dict, KEY_TL_TEMP_RISE, KEY_TL_TEMP_FALL):
        temp_rise_fall = _DASH
    else:
        rise = _render_value(input_dict, KEY_TL_TEMP_RISE, deg_c)
        fall = _render_value(input_dict, KEY_TL_TEMP_FALL, deg_c)
        temp_rise_fall = (
            (f"+{rise}" if rise else _DASH) + " / "
            + (rf"\textminus{{}}{fall}" if fall else _DASH)
        )
    t_tl = KeyValueTable(
        caption=r"\textbf{Temperature Load (TL) --- per IRC 6}",
        preset=("5.5cm", "10.0cm"),
        headers=("Parameter", "Value"),
        rows=[
            ("Maximum Shade Temperature", _value(input_dict, 'shade_temp_max', deg_c)),
            ("Minimum Shade Temperature", _value(input_dict, 'shade_temp_min', deg_c)),
            ("Effective Bridge Temp. Range", bridge_temp_range),
            ("Temperature Rise / Fall for Design", temp_rise_fall),
        ],
    )

    # 8. Load Combinations
    t_combos = ReportTable(
        columns=theme.columns.CH3_COMBOS_2COL,
        caption=r"\textbf{Load Combinations}",
        header_rows=[["Combination ID", "Load Cases"]],
    )
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        t_combos.add_row([f"ULS-{i:02d}", cases])
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        t_combos.add_row([f"SLS-{i:02d}", cases])

    sp = vspace(theme.spacing.space_md)
    return rf"""
\chapter{{Loads and Load Combinations}}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

{sp}
{t_sw.dumps()}

{sp}
{t_dw.dumps()}

{sp}
{t_veh.dumps()}

{veh_note}

{sp}
{t_fp.dumps()}

{sp}
{t_wl.dumps()}

{sp}
{t_el.dumps()}

{sp}
{t_tl.dumps()}

{sp}
{t_combos.dumps()}

\noindent\textit{{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}}
"""


