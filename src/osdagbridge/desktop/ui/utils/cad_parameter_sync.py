"""
CAD -> input synchronisation for double-click label editing (2D CAD).

The 2D CAD widgets only *request* a change (``parameter_edit_requested``).
This controller is the single place that

  1. validates the requested value with the project's own validators
     (``BridgeInputValidator`` + the girder layout solver),
  2. writes it to the template page's input dictionary - which is both the
     basic-input dictionary and the store the Additional Inputs dialog is
     seeded from - and to the matching Basic Inputs widget, and
  3. triggers the CAD redraw.

Invalid values are rejected (the previous value is kept) and the reason is
shown in the standard Osdag warning dialog and the log.
"""

from PySide6.QtWidgets import QLineEdit

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
)
from osdagbridge.core.utils.logger import bridge_logger
from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    solve_extend_basic_input_dict,
    resolve_girder_spacing,
)
from osdagbridge.desktop.ui.docks.cad_label_editor import CAD_EDITABLE_PARAMETERS
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType


# Parameters owned by a Basic Inputs (input dock) widget: routed through the
# dock so its own validation/required-field bookkeeping runs unchanged.
_BASIC_INPUT_KEYS = (KEY_SPAN, KEY_CARRIAGEWAY_WIDTH)

# Basic inputs the layout solver (solve_extend_basic_input_dict) needs before
# girder spacing / deck thickness can be applied.
_LAYOUT_PREREQUISITES = (KEY_SPAN, KEY_CARRIAGEWAY_WIDTH)

# The CAD-editable additional inputs. solve_extend_basic_input_dict
# re-defaults all additional inputs whenever a required basic input changes;
# a value of these keys that the user set (on the CAD or in the Additional
# Inputs dialog) is kept across that re-default, re-validated against the new
# layout, instead of being silently discarded.
_PINNABLE_KEYS = (KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS)


class CADParameterSync:
    """Validates and applies parameter edits coming from the 2D CAD."""

    def __init__(self, page):
        self.page = page
        self.validator = BridgeInputValidator()
        # Values of _PINNABLE_KEYS as the layout solver last wrote them. A
        # different current value was set by the user (CAD or dialog).
        self._solved = {}

    # ── public API ───────────────────────────────────────────────────────
    def can_edit(self):
        """Guard used by the CAD before opening an editor -> (allowed, reason)."""
        dock = self.page.input_dock
        if dock is None:
            return False, "Inputs are not ready yet."
        if getattr(self.page, "_design_running", False) or not dock.isEnabled():
            return False, "Analysis is running - wait for it to finish before editing."
        if getattr(dock, "is_locked", False):
            return False, "🔒 Inputs are locked. Unlock the input dock to edit."
        return True, ""

    def apply(self, key: str, value: float) -> bool:
        """Validate ``value`` for ``key`` and commit it. Returns True if applied."""
        allowed, reason = self.can_edit()
        if not allowed:
            self._reject(key, reason)
            return False

        if key in _BASIC_INPUT_KEYS:
            applied = self._apply_basic_input(key, value)
        elif key == KEY_TS_GIRDER_SPACING:
            applied = self._apply_girder_spacing(value)
        elif key == KEY_TS_DECK_THICKNESS:
            applied = self._apply_deck_thickness(value)
        else:
            self._reject(key, "This value cannot be edited from the CAD.")
            return False

        if applied:
            name, unit, _, _ = CAD_EDITABLE_PARAMETERS[key]
            bridge_logger.info(f"2D CAD: {name} set to {self._fmt(value, unit)}")
        return applied

    def solve_layout(self):
        """
        ``solve_extend_basic_input_dict`` that keeps user-set girder spacing /
        deck thickness. A kept girder spacing is re-solved against the new
        width (same girder count, overhang re-derived); if it no longer fits,
        the default is used and the user is told why in the log.
        """
        input_dict = self.page.input_dict
        kept = {k: input_dict.get(k) for k in self.user_set_keys()}
        solve_extend_basic_input_dict(input_dict)
        self._solved = {k: input_dict.get(k) for k in _PINNABLE_KEYS}   # solver's own values
        for key, value in kept.items():
            if self._restore_pinned(key, float(value)):
                continue
            name, unit, _, _ = CAD_EDITABLE_PARAMETERS[key]
            bridge_logger.warning(
                f"2D CAD: {name} {self._fmt(value, unit)} does not fit the new layout; "
                f"reset to {self._fmt(float(input_dict[key]), unit)}."
            )

    def user_set_keys(self):
        """CAD-editable additional inputs whose value differs from the last solve."""
        input_dict = self.page.input_dict
        keys = []
        for key in _PINNABLE_KEYS:
            value, solved = input_dict.get(key), self._solved.get(key)
            if value in (None, "") or solved in (None, ""):
                continue
            try:
                if abs(float(value) - float(solved)) > 1e-9:
                    keys.append(key)
            except (TypeError, ValueError):
                continue
        return keys

    def clear_pinned(self):
        """Forget user-set values (e.g. when an OSI file replaces all inputs)."""
        self._solved = {}

    def _restore_pinned(self, key, value) -> bool:
        candidate = dict(self.page.input_dict)
        candidate[key] = value
        if self.validator.validate_additional_inputs(key, candidate) is not None:
            return False
        if key == KEY_TS_GIRDER_SPACING:
            try:
                resolve_girder_spacing(self.page.input_dict, value)
            except (ValueError, TypeError):
                return False
        else:
            self.page.input_dict[key] = value
        return True

    # ── per-parameter handlers ───────────────────────────────────────────
    def _apply_basic_input(self, key, value) -> bool:
        candidate = dict(self.page.input_dict)
        candidate[key] = value
        result = self.validator.validate_basic_inputs(key, candidate)
        if result is not None:
            self._reject(key, result[1])
            return False

        dock = self.page.input_dock
        widget = dock.input_widget.findChild(QLineEdit, key) if dock.input_widget else None
        if widget is None:
            self._reject(key, "The matching Basic Inputs field was not found.")
            return False

        name, unit, _, _ = CAD_EDITABLE_PARAMETERS[key]
        widget.blockSignals(True)
        widget.setText(self._fmt(value, unit, with_unit=False))
        widget.blockSignals(False)
        dock.reset_error_state(widget)
        # Same path as the user finishing an edit in the dock: updates
        # input_dict, flags required-field changes and redraws the CAD.
        dock._on_field_edited(key, widget)
        self._reveal_values()
        return True

    def _apply_girder_spacing(self, value) -> bool:
        if not self._ensure_layout_solved(KEY_TS_GIRDER_SPACING):
            return False

        candidate = dict(self.page.input_dict)
        candidate[KEY_TS_GIRDER_SPACING] = value
        result = self.validator.validate_additional_inputs(KEY_TS_GIRDER_SPACING, candidate)
        if result is not None:
            self._reject(KEY_TS_GIRDER_SPACING, result[1])
            return False

        try:
            layout = resolve_girder_spacing(self.page.input_dict, value)
        except (ValueError, TypeError) as exc:
            self._reject(KEY_TS_GIRDER_SPACING, str(exc))
            return False

        bridge_logger.info(
            f"2D CAD: deck overhang re-derived to {layout.deck_overhang:.2f} m "
            f"({int(layout.no_of_girders)} girders, overall width {layout.overall_width:.2f} m)"
        )
        if layout.deck_overhang > layout.girder_spacing + 1e-6:
            bridge_logger.warning(
                f"Overhang ({layout.deck_overhang:.2f} m) exceeds girder spacing "
                f"({layout.girder_spacing:.2f} m)."
            )
        self._redraw()
        return True

    def _apply_deck_thickness(self, value) -> bool:
        if not self._ensure_layout_solved(KEY_TS_DECK_THICKNESS):
            return False

        candidate = dict(self.page.input_dict)
        candidate[KEY_TS_DECK_THICKNESS] = value
        result = self.validator.validate_additional_inputs(KEY_TS_DECK_THICKNESS, candidate)
        if result is not None:
            self._reject(KEY_TS_DECK_THICKNESS, result[1])
            return False

        self.page.input_dict[KEY_TS_DECK_THICKNESS] = float(value)
        self._redraw()
        return True

    # ── helpers ──────────────────────────────────────────────────────────
    def _ensure_layout_solved(self, key) -> bool:
        """
        Additional-input values (girder spacing, deck thickness) are re-defaulted
        whenever a required basic input changes. Settle any pending re-default
        *before* applying the CAD edit so the edit is not silently overwritten
        at the next Design / Additional Inputs click.
        """
        page, dock = self.page, self.page.input_dock
        missing = [
            CAD_EDITABLE_PARAMETERS[k][0]
            for k in _LAYOUT_PREREQUISITES
            if page.input_dict.get(k) in (None, "")
        ]
        if missing:
            self._reject(key, f"Enter {' and '.join(missing)} in Basic Inputs first - "
                              "the bridge layout is derived from them.")
            return False
        if dock.is_require_field_changed or page.input_dict.get(KEY_TS_NO_OF_GIRDERS) in (None, ""):
            try:
                self.solve_layout()
            except Exception as exc:          # solver rejects the current basic inputs
                self._reject(key, f"The bridge layout could not be solved from the current inputs:\n{exc}")
                return False
            dock.is_require_field_changed = False
        return True

    def _redraw(self):
        self.page.cad_comp_widget.update_from_osdag_inputs(self.page.input_dict)
        self._reveal_values()

    def _reveal_values(self):
        """Show numeric values on the dimension labels once the user has edited one."""
        cad = self.page.cad_comp_widget
        for view in (cad.cross_section_widget, cad.top_view_widget):
            view.show_span_values = True
            view.show_carriageway_values = True
            view.update()

    def _reject(self, key, message):
        name = CAD_EDITABLE_PARAMETERS.get(key, (key,))[0]
        bridge_logger.warning(f"2D CAD edit of {name} rejected: {message}")
        CustomMessageBox(
            title="Input Error",
            text=f"{name}: {message}\n\nThe previous value has been kept.",
            dialogType=MessageBoxType.Warning,
        ).exec()

    @staticmethod
    def _fmt(value, unit, with_unit=True):
        text = f"{value:.0f}" if unit == "mm" else f"{value:g}"
        return f"{text} {unit}" if with_unit else text
