# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted and Refactored for OsdagBridge Report Generation
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
)
from osdagbridge.core.reports.report_utils import _render_value, _tex


def ch3_loads(input_dict):
    """Generate Chapter 3: Loads and Load Combinations."""
    # ── 1. Live Load Vehicles Selected ───────────────────────────────────────
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

    # ── 2. Impact Factors & Live Load Parameters per Vehicle ─────────────────
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    span_m = float(span) if span not in (None, "") else 0.0

    im_a = 0.0
    im_aa = 0.0
    try:
        if span_m > 0:
            im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
            im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
    except Exception:
        pass

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT) or 2
    braking_force_kN_str = "N/A"
    try:
        lanes_int = int(lanes)
        bf_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
        braking_force_kN_str = f"{bf_t * 9.81:.2f} kN"
    except Exception:
        braking_force_kN_str = "N/A"

    # Build Vehicle Live Loads rows
    ll_rows = []
    if not vehicles:
        ll_rows.append(r"None Selected & --- & --- & --- & --- \\[6pt]" + "\n\\hline")
    else:
        for v in vehicles:
            v_clean = _tex(v)
            if "Class A" in v:
                v_class = "IRC Class A"
                impact_s = f"{1.0 + im_a:.3f}" if span_m > 0 else "1.234"
                braking_s = braking_force_kN_str
                centrif_s = "Per Cl. 212 (N/A on straight)"
            elif "70R (Tracked)" in v or "AA (Tracked)" in v:
                v_class = "IRC Tracked Heavy"
                impact_s = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.100"
                braking_s = braking_force_kN_str
                centrif_s = "Per Cl. 212 (N/A on straight)"
            elif "70R" in v or "AA" in v or "Bogie" in v:
                v_class = "IRC Wheeled Heavy"
                impact_s = f"{1.0 + im_aa:.3f}" if span_m > 0 else "1.100"
                braking_s = braking_force_kN_str
                centrif_s = "Per Cl. 212 (N/A on straight)"
            elif "Fatigue" in v:
                v_class = "IRC Fatigue Vehicle"
                impact_s = "1.000 (No dynamic factor)"
                braking_s = "---"
                centrif_s = "---"
            elif "SV" in v:
                v_class = "Special Vehicle (SV)"
                impact_s = "1.000"
                braking_s = braking_force_kN_str
                centrif_s = "---"
            else:
                v_class = "Custom Live Load"
                impact_s = "1.000"
                braking_s = "---"
                centrif_s = "---"

            ll_rows.append(
                f"{v_clean} & {v_class} & {impact_s} & {braking_s} & {centrif_s} \\\\[6pt]\n\\hline"
            )
    ll_rows_str = "\n".join(ll_rows)

    # ── 3. Footpath Live Load Parameters ─────────────────────────────────────
    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_p = IRC6_2017.cl_206_1_footway_load()
            fp_intensity = f"{fp_p:.2f} kN/m²"
            fp_governing = "IRC 6:2017 Cl. 206.1"
        except Exception:
            fp_intensity = "4.00 kN/m²"
            fp_governing = "IRC 6:2017 Cl. 206.1"
    elif fp_value not in (None, ""):
        fp_intensity = f"{fp_value} kN/m²"
        fp_governing = "User Defined Input"
    else:
        fp_intensity = "4.00 kN/m²"
        fp_governing = "IRC 6:2017 Cl. 206.1 (Default)"

    fp_rows = [
        r"\textnormal{Footway Design Basis} & " + fp_governing + r" & --- \\[6pt]" + "\n\\hline",
        r"\textnormal{Pedestrian Live Load Intensity} & " + fp_intensity + r" & Uniformly Distributed Pressure \\[6pt]" + "\n\\hline",
        r"\textnormal{Kerb Horizontal Impact Load} & 7.50 kN/m & IRC 6 Cl. 206.3 applied at kerb top \\[6pt]" + "\n\\hline",
        r"\textnormal{Pedestrian Railing Live Load} & 1.50 kN/m & IRC 6 Cl. 206.4 applied at top of railing \\[6pt]" + "\n\\hline",
    ]
    fp_rows_str = "\n".join(fp_rows)

    # ── 4. Wind & Seismic computed values ────────────────────────────────────
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

    # ── 5. Load Combinations ────────────────────────────────────────────────
    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()

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

    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"ULS-{i:02d} & {cases} \\\\[6pt]\n\\hline")
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(f"SLS-{i:02d} & {cases} \\\\[6pt]\n\\hline")
    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all structural and environmental loads applied to the bridge and the code-mandated load combinations considered for analysis and design per IRC 6:2017.

\section{Permanent Dead Loads}
\vspace{0.5em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Dead Load -- Self Weight (Continued)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endhead
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{0.8em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Dead Load for Surfacing (DW) (Continued)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endhead
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\section{Live Loads (LL)}
\label{sec:live-loads}
Vehicular live loads are applied in accordance with IRC 6:2017 according to the carriageway configuration and user selections.

\vspace{0.5em}
\begin{longtable}{|L{4.2cm}|C{3.2cm}|C{2.5cm}|C{2.6cm}|C{3.0cm}|}
\caption{\textbf{Vehicular Live Load Parameters (IRC 6:2017)}} \\
\hline
\textbf{Vehicle Class} & \textbf{Category / Code} & \textbf{Impact Factor} & \textbf{Braking Force} & \textbf{Centrifugal / Transverse} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Vehicular Live Load Parameters (IRC 6:2017) (Continued)}} \\
\hline
\textbf{Vehicle Class} & \textbf{Category / Code} & \textbf{Impact Factor} & \textbf{Braking Force} & \textbf{Centrifugal / Transverse} \\[6pt]
\hline
\endhead
""" + ll_rows_str + r"""
\end{longtable}

\section{Footpath Live Loads}
\label{sec:footpath-loads}
Pedestrian live loads on footpaths, barriers, and railings are separated into Table~\ref{tab:footpath-loads} per IRC 6:2017 Cl. 206.

\vspace{0.5em}
\begin{longtable}{|L{5.5cm}|C{4.0cm}|p{6.0cm}|}
\caption{\textbf{Footpath and Pedestrian Live Loads (IRC 6 Cl. 206)}} \label{tab:footpath-loads} \\
\hline
\textbf{Load Component} & \textbf{Intensity / Value} & \textbf{Remarks / Code Clause} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Footpath and Pedestrian Live Loads (IRC 6 Cl. 206) (Continued)}} \\
\hline
\textbf{Load Component} & \textbf{Intensity / Value} & \textbf{Remarks / Code Clause} \\[6pt]
\hline
\endhead
""" + fp_rows_str + r"""
\end{longtable}

\section{Wind Load (WL) --- per IRC 6:2017}
\vspace{0.5em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load Parameters and Forces}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Wind Load Parameters and Forces (Continued)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
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

\section{Earthquake Load (EL) --- per IRC 6:2017 / IRC SP:114}
\vspace{0.5em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Seismic Design Parameters}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Seismic Design Parameters (Continued)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
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
\end{longtable}

\section{Temperature Load (TL) --- per IRC 6:2017}
\vspace{0.5em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Thermal Expansion and Bridge Temperature Range}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Thermal Expansion and Bridge Temperature Range (Continued)}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
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

\section{Load Combinations}
\vspace{0.5em}
\begin{longtable}{|C{3.0cm}|p{12.5cm}|}
\caption{\textbf{Governing Limit State Load Combinations}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\caption[]{\textbf{Governing Limit State Load Combinations (Continued)}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
