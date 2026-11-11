"""Read-only adapters for existing design results. Never fill missing results with zero."""
from dataclasses import dataclass
from math import isfinite
from osdagbridge.core.utils import common as K

COMPONENTS = ('Steel plate girders', 'Concrete deck slab', 'Cross bracing', 'End diaphragms')


def numeric(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if isfinite(result) else None
    except (ValueError, TypeError):
        return None


def selected(value):
    # Qt.Checked is 2; serialized UI values may also be booleans or strings.
    return str(value).strip().lower() in {'true', 'yes', '1', '2', 'checked'}


@dataclass(frozen=True)
class CheckRecord:
    component: str
    member: str
    check: str
    demand: float | None = None
    capacity: float | None = None
    demand_unit: str = ''
    capacity_unit: str = ''
    ur: float | None = None
    load_case: str = 'Not available'
    source: str = ''
    availability: str = 'Available'

    @property
    def status(self):
        if self.ur is None:
            return self.availability if self.availability != 'Available' else 'Not available'
        return 'PASS' if self.ur <= 1 else 'FAIL'


@dataclass(frozen=True)
class QuantityRecord:
    component: str
    value: float | None
    unit: str
    source: str
    estimated: bool = False


def utilization(demand=None, capacity=None, ratio=None, *, percent=False):
    cap = numeric(capacity)
    if capacity is not None and (cap is None or cap <= 0):
        return None
    value = numeric(ratio)
    if value is not None:
        value = value / 100 if percent else value
    elif numeric(demand) is not None and cap is not None:
        value = abs(numeric(demand)) / cap
    return value if value is not None and value >= 0 else None


def osdag_summary(result):
    """Same field mapping as results_data, without importing the analysis solver."""
    def first(*keys):
        return next((result[k] for k in keys if result.get(k) is not None), None)
    return dict(section=first('section_size.designation', 'Optimum.Designation'),
                capacity_kN=first('Member.tension_capacity', 'Design.Strength'),
                efficiency=first('Member.efficiency', 'Optimum.UR'),
                slenderness=result.get('Member.Slenderness'),
                connection='Welded' if 'Weld.Type' in result else 'Bolted')


def check_records(outputs, inputs):
    records = []
    pg = (outputs.get('design_results') or {}).get('per_girder') or {}
    for member, data in pg.items():
        if str(member).startswith('EB'):
            continue
        # Retain envelope and per-LC checks; each record keeps its own demand/capacity.
        sources = [('Envelope', data.get('checks') or [])]
        sources += [(lc, ld.get('checks') or []) for lc, ld in (data.get('per_lc') or {}).items()
                    if not str(lc).lower().startswith('envelope')]
        for lc, checks in sources:
            for chk in checks:
                if str(chk.get('status', '')).upper() in {'INFO', 'N/A', 'NOT APPLICABLE'}:
                    continue
                cid = chk.get('check_id', chk.get('id'))
                component = COMPONENTS[1] if cid == 16 else COMPONENTS[0]
                ur = utilization(chk.get('demand'), chk.get('capacity'), chk.get('dcr'))
                records.append(CheckRecord(component, str(member), str(chk.get('name') or f'Check {cid}'),
                    numeric(chk.get('demand')), numeric(chk.get('capacity')),
                    chk.get('demand_unit') or '', chk.get('capacity_unit') or '', ur,
                    str(lc), 'design_results.per_girder'))
    # Explicit legacy percentage mapping, used only when detailed results are absent.
    if not pg:
        for key, name in [('KEY_UTIL_FLEXURE', 'Flexure'), ('KEY_UTIL_SHEAR', 'Shear')]:
            value = outputs.get(getattr(K, key))
            if value is not None:
                records.append(CheckRecord(COMPONENTS[0], 'Overall', name,
                    ur=utilization(ratio=value, percent=True), source=key + ' (percent)'))
    deck = outputs.get('deck_report_values') or {}
    deck_checks = [
        ('Flexure sagging', 'KEY_DD_M_ULS_SAG', 'KEY_DD_MU_BOT', 'kN-m/m'),
        ('Flexure hogging', 'KEY_DD_M_ULS_HOG', 'KEY_DD_MU_TOP', 'kN-m/m'),
        ('Overhang', 'KEY_DD_M_ULS_OH', 'KEY_DD_MU_OH', 'kN-m/m'),
        ('Punching shear', 'KEY_DD_PUNCH_VED', 'KEY_DD_VRD_C_MPA', 'MPa'),
        ('One-way shear', 'KEY_DD_SHEAR_VED', 'KEY_DD_SHEAR_VRDC', 'kN/m'),
        ('Crack width bottom', 'KEY_DD_WK_BOT', 'KEY_DD_WK_LIMIT', 'mm'),
        ('Crack width top', 'KEY_DD_WK_TOP', 'KEY_DD_WK_LIMIT', 'mm'),
        ('Crack width overhang', 'KEY_DD_WK_OH', 'KEY_DD_WK_LIMIT', 'mm')]
    for name, dk, ck, unit in deck_checks:
        if 'overhang' in name.lower() and not selected(deck.get(K.KEY_DD_HAS_OVERHANG)):
            continue
        dem, cap = numeric(deck.get(getattr(K, dk))), numeric(deck.get(getattr(K, ck)))
        records.append(CheckRecord(COMPONENTS[1], 'Deck', name, dem, cap, unit, unit,
            utilization(dem, cap), 'Frequent SLS' if 'Crack' in name else 'Basic ULS', 'deck_report_values'))
    forces = (outputs.get('crossbracing_forces_dict') or {}).get('pairs') or {}
    for pair, members in (outputs.get('crossbracing_design_results') or {}).items():
        for member in ('diagonal', 'chord'):
            for kind in ('tension', 'compression'):
                summary = osdag_summary((members.get(member) or {}).get(kind) or {})
                prefix = 'diag' if member == 'diagonal' else 'chord'
                force = (forces.get(pair) or {}).get(f'{prefix}_{kind}_kN')
                cap = summary.get('capacity_kN')
                records.append(CheckRecord(COMPONENTS[2], f'{pair} {member}', kind,
                    numeric(force), numeric(cap), 'kN', 'kN', utilization(force, cap, summary.get('efficiency')),
                    str((forces.get(pair) or {}).get(f'{prefix}_{kind}_gov_lc') or 'Not available'),
                    'crossbracing_design_results'))
    for component in COMPONENTS:
        if not any(r.component == component for r in records):
            records.append(CheckRecord(component, '-', 'Backend result unavailable', availability='Not available'))
    return records


def governing_checks(records):
    result = []
    for component in COMPONENTS:
        candidates = [r for r in records if r.component == component and r.ur is not None]
        result.append(max(candidates, key=lambda r: (r.ur, r.load_case != "Envelope")) if candidates else
                      CheckRecord(component, '-', 'Backend result unavailable', availability='Not available'))
    return result


def quantity_records(quantities):
    def value(key):
        v = numeric(quantities.get(key))
        return v if v is not None and v >= 0 else None
    parts = [value(f'bracing_{part}_wt_total') for part in ('top', 'bot', 'diag')]
    return [QuantityRecord(COMPONENTS[0], value('steel_girders_wt_total'), 'MT', 'steel_girders_wt_total'),
            QuantityRecord(COMPONENTS[2], sum(parts) if all(p is not None for p in parts) else None, 'MT', 'Sum of top, bottom and diagonal totals'),
            QuantityRecord(COMPONENTS[3], None, 'MT', 'Backend quantity unavailable'),
            QuantityRecord('Concrete', value('concrete_deck_vol_total'), 'm³', 'concrete_deck_vol_total'),
            QuantityRecord('Reinforcement', value('rebar_deck_wt_total'), 'MT', '120 kg/m³ of concrete', True)]
