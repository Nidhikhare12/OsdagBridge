"""Live-load tables for Chapter 3.

Table 3.3 follows the layout given in the FOSSEE task brief: one row per vehicle
selected in the Loading tab, with total load, impact factor and braking-load
columns. Values come from the existing IRC 6 vehicle definitions and the
analysis settings; this module performs no new structural calculation.
"""
import contextlib
import io
import math

from .report_utils import _tex
from .styles import report_section
from osdagbridge.core.utils.common import (
    KEY_FOOTPATH, KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_BL_IRC_CLASS_SV, KEY_LL_ECCENTRICITY, KEY_LL_CUSTOM_VEHICLES, KEY_SPAN,
    KEY_LL_IRC_CLASS_A, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED, KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE, KEY_LL_IRC_CLASS_FATIGUE,
)

NOT_AVAILABLE = 'N/A'


def selected(value):
    """Accept GUI booleans and serialized checkbox values without truthy 'False'."""
    return value is True or value == 1 or str(value).strip().lower() in {'true', 'yes', 'on', 'checked'}


def _number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


# ── Total vehicle load from the IRC 6 definitions used by the analysis ──────────
def _irc():
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    return IRC6_2017


def _quiet(function):
    """Some IRC helpers print a summary table; keep report generation silent."""
    with contextlib.redirect_stdout(io.StringIO()):
        return function()


def _sum_wheel_loads_kN(definition):
    # IRC6_2017 wheel loads use the keyfile unit system (N), as in
    # analyser._vehicle_total_weight_kN.
    from osdagbridge.core.utils.codes.keyfile import kN
    return sum(definition()['wheel_loads']) / kN


def _class_70r_tracked_kN():
    from osdagbridge.core.utils.codes.keyfile import kN
    track = _irc().cl_204_1_Class70R_vehicle_track()
    length = max(track['x']) - min(track['x'])
    return track['wheel_loads_udl'] * length * len(track['z']) / kN


def _special_vehicle_kN():
    return _quiet(_irc().cl_204_5_1_special_vehicle)['total_load_kN']


# (input key, label, total-load function or None when no definition exists,
#  IRC 6 impact clause, braking rule). Order follows the Loading tab. Braking
#  follows the app's own rule (Additional Inputs summary): a vehicle's braking
#  load is considered when the vehicle is selected; Class SV has its own opt-in.
IRC_VEHICLES = (
    (KEY_LL_IRC_CLASS_A, 'Class A', lambda: _sum_wheel_loads_kN(_irc().cl_204_1_ClassA_vehicle), '208.2', 'live'),
    (KEY_LL_IRC_70R_WHEELED, 'Class 70R (Wheeled)', lambda: _sum_wheel_loads_kN(_irc().cl_204_1_Class70R_vehicle_wheel), '208.3', 'live'),
    (KEY_LL_IRC_70R_TRACKED, 'Class 70R (Tracked)', _class_70r_tracked_kN, '208.3', 'live'),
    (KEY_LL_IRC_AA_WHEELED, 'Class AA (Wheeled)', None, '208.3', 'live'),
    (KEY_LL_IRC_AA_TRACKED, 'Class AA (Tracked)', None, '208.3', 'live'),
    (KEY_LL_IRC_CLASS_SV, 'Class SV', _special_vehicle_kN, None, 'sv'),
    (KEY_LL_IRC_70R_BOGIE, 'Class 70R (Bogie)', None, '208.3', 'live'),
    (KEY_LL_IRC_CLASS_FATIGUE, 'Class Fatigue', lambda: _sum_wheel_loads_kN(_irc().cl_204_6_fatigue_load), None, 'live'),
)


def _safe_total(function):
    if function is None:
        return None
    try:
        return _number(function())
    except Exception:
        return None


def impact_factor(inputs, clause):
    """1 + IM for a vehicle class per IRC 6 Cl. 208.2 (Class A) or 208.3 (70R / AA).

    Deck design uses these per-class values; the grillage analysis applies the
    Cl. 208.3 value to every vehicle load case (stated in the table notes).
    """
    span = _number(inputs.get(KEY_SPAN))
    if clause is None or not span or span <= 0:
        return None
    try:
        im = {'208.2': _irc().cl_208_2_impact_factor, '208.3': _irc().cl_208_3_impact_factor}[clause](span)
    except Exception:
        return None
    return 1.0 + im


BRAKING_FRACTION = 0.20  # IRC 6 Cl. 211.2: 20 % of the first train load in one lane


def braking_force(total_kN):
    """Braking force of one vehicle (first train) per IRC 6 Cl. 211.2."""
    return None if total_kN is None else BRAKING_FRACTION * total_kN


def vehicle_rows(inputs):
    """One dict per selected vehicle: name, total_kN, impact, braking, braking_kN, eccentricity."""
    eccentricity = _number(inputs.get(KEY_LL_ECCENTRICITY))
    sv_braking = selected(inputs.get(KEY_BL_IRC_CLASS_SV))
    rows = []
    for key, label, total, clause, rule in IRC_VEHICLES:
        if not selected(inputs.get(key)):
            continue
        braking = {'live': True, 'sv': sv_braking}[rule]
        total_kN = _safe_total(total)
        rows.append({'name': label, 'total_kN': total_kN, 'impact': impact_factor(inputs, clause),
                     'braking': braking, 'braking_kN': braking_force(total_kN) if braking else None,
                     'eccentricity': eccentricity if braking else None})
    for vehicle in inputs.get(KEY_LL_CUSTOM_VEHICLES) or []:
        if isinstance(vehicle, str):
            vehicle = {'name': vehicle}
        if not isinstance(vehicle, dict) or not vehicle.get('name'):
            continue
        loads = [_number(v) for v in vehicle.get('axle_loads') or []]
        im = _number(vehicle.get('impact_factor'))
        total_kN = sum(loads) if loads and None not in loads else None
        rows.append({'name': str(vehicle['name']), 'total_kN': total_kN,
                     'impact': 1.0 + im if im is not None else None,
                     'braking': True, 'braking_kN': braking_force(total_kN), 'eccentricity': eccentricity})
    return rows


def _fmt(value, digits):
    return NOT_AVAILABLE if value is None else f'{value:.{digits}f}'


def _vehicle_table(rows):
    head = (r'\hline' + '\n'
            r'\textbf{Vehicle} & \textbf{Total Load} & \textbf{Impact Factor}'
            r' & \multicolumn{3}{c|}{\textbf{Braking Load}} \\' + '\n'
            r'\cline{4-6}' + '\n'
            r' & \textbf{(kN)} & \textbf{(1 + IM)} & \textbf{Considered?}'
            r' & \textbf{Value (kN)} & \textbf{Eccentricity (m)} \\' + '\n'
            r'\hline' + '\n')
    if rows:
        body = '\n'.join(
            ' & '.join([_tex(r['name']), _fmt(r['total_kN'], 1), _fmt(r['impact'], 3),
                        'Yes' if r['braking'] else 'No',
                        _fmt(r['braking_kN'], 1) if r['braking'] else '--',
                        _fmt(r['eccentricity'], 2) if r['braking'] else '--']) + r' \\' + '\n' + r'\hline'
            for r in rows)
    else:
        body = r'\multicolumn{6}{|c|}{None selected} \\' + '\n' + r'\hline'
    return (r'\begin{longtable}{|L{3.4cm}|C{2.0cm}|C{2.2cm}|C{2.5cm}|C{2.2cm}|C{2.6cm}|}' + '\n'
            + r'\caption{\textbf{Vehicle Live Loads (LL)}}\\' + '\n' + head
            + r'\endfirsthead' + '\n' + head + r'\endhead' + '\n'
            + body + '\n' + r'\end{longtable}')


def _parameter_table(caption, rows):
    header = (r'\hline' + '\n' + r'\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\'
              + '\n' + r'\hline' + '\n')
    return (r'\begin{longtable}{|L{4.0cm}|L{9.0cm}|C{2.0cm}|}' + '\n'
            + r'\caption{\textbf{' + caption + r'}}\\' + '\n' + header
            + r'\endfirsthead' + '\n' + header + r'\endhead' + '\n'
            + '\n'.join(_tex(label) + ' & ' + _tex(value) + ' & ' + unit + r' \\'
                        + '\n' + r'\hline' for label, value, unit in rows)
            + '\n' + r'\end{longtable}')


def _vehicle_notes(inputs, rows):
    grillage = impact_factor(inputs, '208.3')
    notes = [
        'Total load is the unfactored vehicle load from the IRC 6 vehicle definitions; '
        'N/A means the current code has no definition for that vehicle.',
        'Impact factor per IRC 6 Cl. 208.2 (Class A) and Cl. 208.3 (Class 70R / AA), '
        'as used in deck design; custom vehicles use their own value. N/A: no impact '
        'factor is defined for that vehicle in the current code.'
        + (f' The grillage analysis applies {grillage:.3f} (Cl. 208.3) to all vehicle '
           'load cases.' if grillage else ''),
        'Braking: considered for every selected vehicle, except Class SV, which has its own '
        'option in the Loading tab. Value is 20% of the vehicle load (IRC 6 Cl. 211.2, first '
        'train in one lane), acting at the eccentricity from top of deck given in the Loading '
        'tab (IRC 6 Cl. 211.3: 1.2 m). The current grillage analysis does not include a '
        'braking load case.',
        'Centrifugal force (IRC 6 Cl. 212): not applicable; the inputs define a straight '
        'bridge with no horizontal curvature.',
        'Live-load analysis cases place Class A and Class 70R (Wheeled) vehicles per '
        'IRC 6 Table 6; other selected vehicles are listed as selected.',
    ]
    return (r'\noindent\textit{Notes:}' + '\n' + r'\begin{itemize}[leftmargin=*,itemsep=0pt,topsep=2pt]' + '\n'
            + '\n'.join(r'\item \textit{' + _tex(n) + '}' for n in notes) + '\n' + r'\end{itemize}')


@report_section
def live_load_tables(inputs):
    """Vehicle table (brief layout) and footway table, built from the report inputs."""
    rows = vehicle_rows(inputs)
    footpath = str(inputs.get(KEY_FOOTPATH, '')).strip()
    if footpath.lower() in {'none', 'no', 'false', '0'}:
        footway_rows = [('Footway configuration', 'None', '--'),
                        ('Footway live load', 'Not applicable', r'kN/m$^2$')]
    else:
        mode = str(inputs.get(KEY_LL_FOOTPATH_PRESSURE_MODE, ''))
        pressure = inputs.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)
        if mode.strip().lower() in {'as per irc 6', 'as per irc6', 'automatic'}:
            pressure = _irc().cl_206_1_footway_load()
        footway_rows = [('Footway configuration', footpath or 'Not supplied', '--'),
                        ('Pressure mode', mode or 'Not supplied', '--'),
                        ('Footway live load', pressure if pressure not in ('', None) else 'N/A', r'kN/m$^2$')]
    return (_vehicle_table(rows) + '\n' + _vehicle_notes(inputs, rows) + '\n'
            + r'\ReportTableGap' + '\n' + _parameter_table('Footway Live Loads', footway_rows))
