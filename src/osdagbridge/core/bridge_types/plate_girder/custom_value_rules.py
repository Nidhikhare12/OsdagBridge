"""
"Custom" value requirements for the Additional Inputs dialog.

When a selector (combobox / mode combo / design-mode controller) is set to
``VALUE_CUSTOM`` the user must supply the value(s) it unlocks. The rules are
derived from ``ADDITIONAL_INPUTS_SCHEMA`` so no parameter key or label is
hard-coded here:

* ``TYPE_MODE_LINE`` fields whose ``mode_choices`` contain ``VALUE_CUSTOM``
  -> selector ``<id>.mode`` unlocks the line edit ``<id>.value``.
* ``TYPE_ADAPTIVE`` fields whose ``VALUE_CUSTOM`` mode is a textbox
  -> the controller key (e.g. ``KEY_DESIGN_MODE``) unlocks the field ``<id>``.
* ``TYPE_COMBOBOX`` fields with ``VALUE_CUSTOM`` among their choices and a
  ``SCHEMA_ATTR_CUSTOM_FIELDS`` list -> the combobox unlocks those keys.
"""

from dataclasses import dataclass
from typing import Iterator

from osdagbridge.core.utils.common import (
    TYPE_ADAPTIVE,
    TYPE_COMBOBOX,
    TYPE_MODE_LINE,
    TYPE_TEXTBOX,
    VALUE_CUSTOM,
    KEY_SUFFIX_MODE,
    KEY_SUFFIX_VALUE,
    SCHEMA_ATTR_CUSTOM_FIELDS,
)

# Where the selector's current value is read from.
SELECTOR_FROM_WIDGET = "widget"            # a QComboBox in the dialog
SELECTOR_FROM_INPUT_DICT = "input_dict"    # a key in working_input_dict (no widget in dialog)


@dataclass(frozen=True)
class CustomValueRule:
    selector_key: str      # object name / dict key of the selector
    selector_source: str   # SELECTOR_FROM_WIDGET | SELECTOR_FROM_INPUT_DICT
    value_key: str         # object name of the input that must not be empty
    label_key: str         # field id whose "<id>_label" QLabel names the parameter


def _iter_field_defs(node) -> Iterator[dict]:
    """Yield every field definition (dict with "id" and "type") in a schema tree."""
    if isinstance(node, dict):
        if "id" in node and "type" in node:
            yield node
        for value in node.values():
            yield from _iter_field_defs(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from _iter_field_defs(item)


def collect_custom_value_rules(schema) -> list[CustomValueRule]:
    rules: list[CustomValueRule] = []
    seen = set()

    def _add(rule):
        if rule not in seen:
            seen.add(rule)
            rules.append(rule)

    for field in _iter_field_defs(schema):
        ftype = field.get("type")
        field_id = field.get("id") or ""
        if not field_id:
            continue

        if ftype == TYPE_MODE_LINE and VALUE_CUSTOM in (field.get("mode_choices") or []):
            _add(CustomValueRule(
                selector_key=field_id + KEY_SUFFIX_MODE,
                selector_source=SELECTOR_FROM_WIDGET,
                value_key=field_id + KEY_SUFFIX_VALUE,
                label_key=field_id,
            ))

        elif ftype == TYPE_ADAPTIVE:
            custom_mode = (field.get("modes") or {}).get(VALUE_CUSTOM) or {}
            if custom_mode.get("type") == TYPE_TEXTBOX and field.get("controller"):
                _add(CustomValueRule(
                    selector_key=field["controller"],
                    selector_source=SELECTOR_FROM_INPUT_DICT,
                    value_key=field_id,
                    label_key=field_id,
                ))

        elif ftype == TYPE_COMBOBOX and VALUE_CUSTOM in (field.get("choices") or []):
            for value_key in field.get(SCHEMA_ATTR_CUSTOM_FIELDS) or []:
                _add(CustomValueRule(
                    selector_key=field_id,
                    selector_source=SELECTOR_FROM_WIDGET,
                    value_key=value_key,
                    label_key=value_key,
                ))

    return rules
