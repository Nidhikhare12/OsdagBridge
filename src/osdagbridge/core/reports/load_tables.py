"""Presentation-only tables for the UI-selected live loads."""
from .report_utils import _tex
from .styles import repeating_longtable_header
from osdagbridge.core.utils import common as keys
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def selected(value):
    return value is True or value == 1 or str(value).strip().lower() in {'yes', 'true', '1', 'checked'}


def live_load_tables(inputs):
    vehicle_keys = (
        ('KEY_LL_IRC_CLASS_A', 'Class A'), ('KEY_LL_IRC_70R_WHEELED', 'Class 70R (Wheeled)'),
        ('KEY_LL_IRC_70R_TRACKED', 'Class 70R (Tracked)'), ('KEY_LL_IRC_AA_WHEELED', 'Class AA (Wheeled)'),
        ('KEY_LL_IRC_AA_TRACKED', 'Class AA (Tracked)'), ('KEY_LL_IRC_CLASS_SV', 'Class SV'),
        ('KEY_LL_IRC_70R_BOGIE', 'Class 70R (Bogie)'), ('KEY_LL_IRC_CLASS_FATIGUE', 'Class Fatigue'))
    vehicles = [label for key, label in vehicle_keys if selected(inputs.get(getattr(keys, key)))]
    for vehicle in inputs.get(keys.KEY_LL_CUSTOM_VEHICLES) or []:
        if isinstance(vehicle, dict) and selected(vehicle.get('included', True)) and vehicle.get('name'):
            vehicles.append(str(vehicle['name']))
        elif isinstance(vehicle, str):
            vehicles.append(vehicle)
    factors = []
    try:
        span = float(inputs[keys.KEY_SPAN])
        if 'Class A' in vehicles:
            factors.append(f'Class A: {1 + IRC6_2017.cl_208_2_impact_factor(span):.3f}')
        if any('70R' in v or 'Class AA' in v for v in vehicles):
            factors.append(f'Class AA/70R: {1 + IRC6_2017.cl_208_3_impact_factor(span):.3f}')
    except (KeyError, TypeError, ValueError):
        pass
    try:
        braking = f'{IRC6_2017.cl_211_2_braking_force(int(inputs[keys.KEY_WC_LD_LANE_TABLE_COUNT])) * 9.81:.2f}'
    except (KeyError, TypeError, ValueError):
        braking = 'Unavailable'
    mode = inputs.get(keys.KEY_LL_FOOTPATH_PRESSURE_MODE, 'Not specified')
    value = inputs.get(keys.KEY_LL_FOOTPATH_PRESSURE_VALUE, 'Unavailable')
    if str(mode).lower().replace(' ', '') in {'automatic', 'asperirc6'}:
        value = IRC6_2017.cl_206_1_footway_load()
    if str(inputs.get(keys.KEY_FOOTPATH, '')).strip().lower() in {'none', 'no'}:
        mode, value = 'No footway', 'Not applicable'
    def table(title, rows):
        body = '\n'.join(' & '.join((_tex(label), _tex(value), unit)) + r' \\ \hline' for label, value, unit in rows)
        return (r'\begin{longtable}{|L{5cm}|L{8cm}|L{2cm}|}' + '\n' +
                r'\caption{\textbf{' + title + r'}}\\' + '\n' +
                repeating_longtable_header(r'\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\', columns=3) +
                body + '\n' + r'\end{longtable}')
    return table('Vehicle Live Loads (LL)', [
        ('Vehicles selected in the design UI', ', '.join(vehicles) or 'None selected', '--'),
        ('Dynamic multiplier (1 + impact factor)', '; '.join(factors) or 'Unavailable', '--'),
        ('Braking load (IRC 6)', braking if vehicles else 'Not applicable', 'kN'),
        ('Centrifugal force', 'Not supplied by the current analysis output', 'kN'),
    ]) + '\n' + table('Footway Live Load (LL)', [
        ('Footway loading mode', mode, '--'),
        ('Footway live-load intensity', value, r'kN/m$^2$'),
        ('Reference', 'IRC 6:2017, Clause 206.1', '--'),
    ])
