"""
Pre-save validation of "Custom" inputs in the Additional Inputs dialog.

The rules are derived from ADDITIONAL_INPUTS_SCHEMA itself, so no parameter
names are hard-coded here. Every widget is looked up by its schema id, i.e. the
central KEY_* constant from osdagbridge.core.utils.common.

Three Custom patterns exist in the schema:

1. TYPE_MODE_LINE  - a mode combo ("<id>.mode") + a value line-edit ("<id>.value").
                     Custom selected  ->  the value line-edit must not be empty.
2. TYPE_ADAPTIVE   - a QStackedWidget whose page is chosen by a controller key
                     (e.g. KEY_DESIGN_MODE). In Custom mode the page is a
                     line-edit that must not be empty.
3. TYPE_COMBOBOX   - a type combo whose choices include Custom (Crash Barrier,
                     Median, Railing, Wearing Course ...). Custom selected  ->
                     every text box of the same sub-tab that the dialog has
                     enabled for user entry must not be empty.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field

from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QTabWidget, QStackedWidget

from osdagbridge.core.utils.common import (
    TYPE_MODE_LINE, TYPE_ADAPTIVE, TYPE_COMBOBOX, TYPE_TEXTBOX,
    KEY_ADD_CUSTOM_OPTION, KEY_ADD_MSG_CUSTOM_EMPTY,
)

_HTML_TAG = re.compile(r"<[^>]+>")


def clean_label(text: str) -> str:
    """'Width of Top Flange, t<sub>fw</sub> (mm):' -> 'Width of Top Flange, tfw (mm)'"""
    return _HTML_TAG.sub("", str(text or "")).strip().rstrip(":").strip()


@dataclass
class CustomRule:
    kind: str                     # "mode_line" | "adaptive" | "combo"
    field_id: str                 # schema id (central KEY_*)
    label: str                    # human readable parameter name
    tab_path: tuple               # e.g. ("Typical Section Details", "Crash Barrier")
    controller: str = ""          # adaptive: controller key
    dependents: list = dc_field(default_factory=list)   # combo: [(textbox_id, label), ...]

    @property
    def display_name(self) -> str:
        return f"{' > '.join(self.tab_path)} > {self.label}" if self.tab_path else self.label


def _custom_in(options) -> bool:
    return KEY_ADD_CUSTOM_OPTION in (options or [])


def build_custom_rules(schema) -> list[CustomRule]:
    """Walk ADDITIONAL_INPUTS_SCHEMA and return every Custom-capable field."""
    rules: list[CustomRule] = []

    def walk(node, path: tuple, group: list | None):
        if isinstance(node, list):
            for item in node:
                walk(item, path, group)
            return
        if not isinstance(node, dict):
            return

        # Tab / sub-tab title contributes to the human-readable path
        title = node.get("label") or node.get("title")
        if title and ("schema" in node or ("rows" in node and "id" in node)):
            if not path or path[-1] != clean_label(title):
                path = path + (clean_label(title),)

        # A dict with "rows" (or "sections") is a field group (a sub-tab / card)
        if "rows" in node:
            group_fields: list[dict] = []
            walk(node["rows"], path, group_fields)
            _rules_for_group(group_fields, path, rules)
            for k, v in node.items():
                if k != "rows":
                    walk(v, path, group)
            return

        # A field definition
        if "id" in node and "type" in node and group is not None:
            group.append(node)
            return   # adaptive "modes" are inspected by _rules_for_group

        for v in node.values():
            walk(v, path, group)

    walk(schema, (), None)
    return rules


def _rules_for_group(fields: list[dict], path: tuple, out: list[CustomRule]) -> None:
    textboxes = [
        (f["id"], clean_label(f.get("label")))
        for f in fields if f.get("type") == TYPE_TEXTBOX
    ]
    for f in fields:
        ftype, fid, label = f.get("type"), f.get("id"), clean_label(f.get("label"))
        if ftype == TYPE_MODE_LINE and _custom_in(f.get("mode_choices")):
            out.append(CustomRule("mode_line", fid, label, path))
        elif ftype == TYPE_ADAPTIVE:
            custom_def = (f.get("modes") or {}).get(KEY_ADD_CUSTOM_OPTION)
            if custom_def and custom_def.get("type") == TYPE_TEXTBOX:
                out.append(CustomRule("adaptive", fid, label, path, controller=f.get("controller", "")))
        elif ftype == TYPE_COMBOBOX and _custom_in(f.get("choices")):
            out.append(CustomRule("combo", fid, label, path, dependents=list(textboxes)))


# ── Runtime checks ────────────────────────────────────────────────────────────

def is_in_active_tab(widget: QWidget, root: QWidget) -> bool:
    """False if any enclosing QTabWidget page of `widget` is a disabled tab."""
    w = widget
    while w is not None and w is not root:
        parent = w.parentWidget()
        if isinstance(parent, QStackedWidget) and isinstance(parent.parentWidget(), QTabWidget):
            tabs = parent.parentWidget()
            idx = tabs.indexOf(w)
            if idx != -1 and not tabs.isTabEnabled(idx):
                return False
        w = parent
    return True


def _is_user_editable(w: QWidget | None, root: QWidget) -> bool:
    return (
        w is not None
        and w.isEnabled()
        and not w.isHidden()
        and not (isinstance(w, QLineEdit) and w.isReadOnly())
        and is_in_active_tab(w, root)
    )


def find_empty_custom_fields(dialog, rules: list[CustomRule]) -> list[str]:
    """Return display names of Custom parameters whose value box is empty."""
    from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import AdaptiveWidget

    missing: list[str] = []
    seen: set[str] = set()

    def report(widget_id: str, name: str):
        if widget_id not in seen:
            seen.add(widget_id)
            missing.append(name)

    for rule in rules:
        if rule.kind == "mode_line":
            mode = dialog.findChild(QComboBox, rule.field_id + ".mode")
            value = dialog.findChild(QLineEdit, rule.field_id + ".value")
            if (mode and value and is_in_active_tab(mode, dialog) and mode.isEnabled()
                    and mode.currentText() == KEY_ADD_CUSTOM_OPTION
                    and not value.text().strip()):
                report(rule.field_id, rule.display_name)

        elif rule.kind == "adaptive":
            if str(dialog.working_input_dict.get(rule.controller, "")).strip() != KEY_ADD_CUSTOM_OPTION:
                continue
            adaptive = dialog.findChild(AdaptiveWidget, rule.field_id)
            if adaptive is None:
                continue
            page = adaptive.currentWidget()
            if (isinstance(page, QLineEdit) and _is_user_editable(page, dialog)
                    and not adaptive.isHidden() and not page.text().strip()):
                report(rule.field_id, rule.display_name)

        elif rule.kind == "combo":
            combo = dialog.findChild(QComboBox, rule.field_id)
            if not (combo and is_in_active_tab(combo, dialog)
                    and combo.currentText() == KEY_ADD_CUSTOM_OPTION):
                continue
            for dep_id, dep_label in rule.dependents:
                w = dialog.findChild(QLineEdit, dep_id)
                if _is_user_editable(w, dialog) and not w.text().strip():
                    name = f"{' > '.join(rule.tab_path)} > {dep_label}" if rule.tab_path else dep_label
                    report(dep_id, name)
    return missing


def format_missing_message(names: list[str]) -> str:
    return "\n".join(KEY_ADD_MSG_CUSTOM_EMPTY.format(n) for n in names)
