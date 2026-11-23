"""
Schema-derived "Custom" value rules (Task II) and the CAD girder-spacing
helper (Task I). Pure-Python: no Qt widgets are created.
"""

import pytest

from osdagbridge.core.utils.common import (
    VALUE_CUSTOM, KEY_SUFFIX_MODE, KEY_SUFFIX_VALUE, SCHEMA_ATTR_CUSTOM_FIELDS,
    TYPE_COMBOBOX, TYPE_MODE_LINE, TYPE_ADAPTIVE, TYPE_TEXTBOX,
    KEY_CB_TYPE, KEY_CB_WIDTH, KEY_WC_MATERIAL, KEY_WC_DENSITY, KEY_DESIGN_MODE,
    KEY_MP_GIRDER_DEPTH, KEY_WL_GUST_FACTOR,
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_OVERHANG,
    KEY_TS_NO_OF_GIRDERS, KEY_TS_OVERALL_WIDTH,
)
from osdagbridge.core.bridge_types.plate_girder.custom_value_rules import (
    collect_custom_value_rules, CustomValueRule,
    SELECTOR_FROM_WIDGET, SELECTOR_FROM_INPUT_DICT,
)
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import ADDITIONAL_INPUTS_SCHEMA


@pytest.fixture(scope="module")
def rules():
    return collect_custom_value_rules(ADDITIONAL_INPUTS_SCHEMA)


def test_mode_line_fields_are_discovered(rules):
    assert CustomValueRule(KEY_WL_GUST_FACTOR + KEY_SUFFIX_MODE, SELECTOR_FROM_WIDGET,
                           KEY_WL_GUST_FACTOR + KEY_SUFFIX_VALUE, KEY_WL_GUST_FACTOR) in rules


def test_combobox_custom_fields_are_discovered(rules):
    assert CustomValueRule(KEY_CB_TYPE, SELECTOR_FROM_WIDGET, KEY_CB_WIDTH, KEY_CB_WIDTH) in rules
    assert CustomValueRule(KEY_WC_MATERIAL, SELECTOR_FROM_WIDGET, KEY_WC_DENSITY, KEY_WC_DENSITY) in rules


def test_adaptive_design_mode_fields_are_discovered(rules):
    assert CustomValueRule(KEY_DESIGN_MODE, SELECTOR_FROM_INPUT_DICT,
                           KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_DEPTH) in rules


def test_rules_are_unique(rules):
    assert len(rules) == len(set(rules))


def test_collector_on_minimal_schema():
    schema = {"rows": [{"fields": [
        {"id": "a", "type": TYPE_MODE_LINE, "mode_choices": ["Auto", VALUE_CUSTOM]},
        {"id": "b", "type": TYPE_MODE_LINE, "mode_choices": ["Auto", "Other"]},          # no Custom
        {"id": "c", "type": TYPE_COMBOBOX, "choices": ["X", VALUE_CUSTOM],
         SCHEMA_ATTR_CUSTOM_FIELDS: ["c1", "c2"]},
        {"id": "d", "type": TYPE_ADAPTIVE, "controller": "mode",
         "modes": {VALUE_CUSTOM: {"type": TYPE_TEXTBOX}}},
        {"id": "e", "type": TYPE_ADAPTIVE, "controller": "mode",
         "modes": {VALUE_CUSTOM: {"type": TYPE_COMBOBOX}}},                              # combo: never empty
    ]}]}
    got = collect_custom_value_rules(schema)
    assert [r.value_key for r in got] == ["a" + KEY_SUFFIX_VALUE, "c1", "c2", "d"]


def test_resolve_girder_spacing_keeps_girder_count():
    from osdagbridge.core.bridge_types.plate_girder.defaults import (
        BASIC_INPUT_DICT, solve_extend_basic_input_dict, resolve_girder_spacing,
    )
    d = dict(BASIC_INPUT_DICT)
    d[KEY_CARRIAGEWAY_WIDTH] = 7.5
    d[KEY_SPAN] = 30.0
    solve_extend_basic_input_dict(d)
    n = d[KEY_TS_NO_OF_GIRDERS]
    result = resolve_girder_spacing(d, 2.2)
    assert d[KEY_TS_NO_OF_GIRDERS] == n
    assert d[KEY_TS_GIRDER_SPACING] == pytest.approx(2.2)
    # (n - 1) * spacing + 2 * overhang == overall width
    assert (n - 1) * d[KEY_TS_GIRDER_SPACING] + 2 * d[KEY_TS_DECK_OVERHANG] == \
        pytest.approx(d[KEY_TS_OVERALL_WIDTH], abs=1e-3)
    assert result.deck_overhang == pytest.approx(d[KEY_TS_DECK_OVERHANG])


def test_resolve_girder_spacing_rejects_impossible_layout():
    from osdagbridge.core.bridge_types.plate_girder.defaults import (
        BASIC_INPUT_DICT, solve_extend_basic_input_dict, resolve_girder_spacing,
    )
    d = dict(BASIC_INPUT_DICT)
    d[KEY_CARRIAGEWAY_WIDTH] = 7.5
    d[KEY_SPAN] = 30.0
    solve_extend_basic_input_dict(d)
    before = dict(d)
    with pytest.raises(ValueError):
        resolve_girder_spacing(d, 9.0)          # overhang would be negative
    assert d[KEY_TS_GIRDER_SPACING] == before[KEY_TS_GIRDER_SPACING]   # untouched on failure
