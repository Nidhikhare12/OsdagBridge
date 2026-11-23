"""Task II - Additional Inputs: empty-Custom validation and unsaved-change warning."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QComboBox, QLineEdit, QWidget

from copy import deepcopy

from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
    KEY_CB_TYPE, KEY_CB_WIDTH, KEY_WC_MATERIAL, KEY_WC_DENSITY, KEY_WL_GUST_FACTOR,
    KEY_DESIGN_MODE, KEY_MP_GIRDER_DEPTH, KEY_SUFFIX_MODE, KEY_SUFFIX_VALUE, VALUE_CUSTOM,
)

EMPTY_MSG = "Error: The custom value for '{}' cannot be empty."


@pytest.fixture
def dialog(window, basic_inputs, pump):
    window.common_design_func("Additional Inputs")
    pump(800)
    dlg = window._additional_inputs_dialog
    assert dlg.isVisible()
    return dlg


def combo(dlg, key):
    return dlg.findChild(QComboBox, key)


def line(dlg, key):
    return dlg.findChild(QLineEdit, key)


def test_opening_the_dialog_is_not_a_modification(dialog):
    assert dialog.is_modified is False


def test_clean_save_passes(dialog, messages, pump):
    n = len(messages)
    dialog._save_inputs()
    pump(100)
    assert not any("cannot be empty" in m for m in messages.since(n))


def test_empty_custom_values_block_save(window, dialog, messages, pump):
    combo(dialog, KEY_CB_TYPE).setCurrentText(VALUE_CUSTOM)
    line(dialog, KEY_CB_WIDTH).clear()
    combo(dialog, KEY_WL_GUST_FACTOR + KEY_SUFFIX_MODE).setCurrentText(VALUE_CUSTOM)
    combo(dialog, KEY_WC_MATERIAL).setCurrentText(VALUE_CUSTOM)
    line(dialog, KEY_WC_DENSITY).clear()
    pump(100)
    assert dialog.is_modified

    missing = [name for name, _ in dialog.validate_custom_fields()]
    assert len(missing) == 3
    committed = window.input_dict.get(KEY_CB_TYPE)
    n = len(messages)
    dialog._save_inputs()
    pump(200)
    shown = " ".join(messages.since(n))
    for name in missing:
        assert EMPTY_MSG.format(name) in shown
    assert window.input_dict.get(KEY_CB_TYPE) == committed          # nothing committed
    assert line(dialog, KEY_CB_WIDTH).property("error") in (True, "true")   # highlighted


def test_filling_the_values_allows_save_and_clears_the_flag(window, dialog, messages,
                                                            type_into, pump):
    combo(dialog, KEY_CB_TYPE).setCurrentText(VALUE_CUSTOM)
    type_into(line(dialog, KEY_CB_WIDTH), "0.45")
    assert line(dialog, KEY_CB_WIDTH).property("error") not in (True, "true")
    assert dialog.validate_custom_fields() == []
    n = len(messages)
    dialog._save_inputs()
    pump(200)
    assert not any("cannot be empty" in m for m in messages.since(n))
    assert window.input_dict.get(KEY_CB_TYPE) == VALUE_CUSTOM
    assert dialog.is_modified is False


def test_reverting_a_change_clears_the_flag(dialog, pump):
    field = line(dialog, KEY_WC_DENSITY)
    original = field.text()
    field.setText("99")
    pump(50)
    field.setText(original)
    pump(50)
    assert dialog.is_modified is False


def _modify(dialog, type_into):
    combo(dialog, KEY_WC_MATERIAL).setCurrentText(VALUE_CUSTOM)   # unlocks the density
    field = line(dialog, KEY_WC_DENSITY)
    dialog._reveal_widget(field)
    type_into(field, "9")
    assert dialog.is_modified


def test_close_without_changes_does_not_warn(dialog, messages, pump):
    n = len(messages)
    dialog.close()
    pump(100)
    assert messages.since(n) == []
    assert not dialog.isVisible()


@pytest.mark.parametrize("how", ["title_bar_x", "escape"])
def test_cancel_keeps_the_dialog_open(dialog, messages, type_into, pump, how):
    _modify(dialog, type_into)
    messages.reply = "Cancel"
    n = len(messages)
    if how == "title_bar_x":
        dialog.title_bar.btn_close.click()
    else:
        QTest.keyClick(dialog, Qt.Key_Escape)
    pump(100)
    assert any("You have unsaved changes. Closing this window will discard them. "
               "Do you want to proceed?" in m for m in messages.since(n))
    assert dialog.isVisible()


def test_discard_closes_and_drops_the_edits(window, dialog, messages, type_into, pump):
    committed = window.input_dict.get(KEY_WC_DENSITY)
    _modify(dialog, type_into)
    messages.reply = "Discard"
    dialog.title_bar.btn_close.click()
    pump(100)
    assert not dialog.isVisible()
    assert window.input_dict.get(KEY_WC_DENSITY) == committed


def test_uncommitted_typing_counts_as_a_change(dialog, messages, type_into, pump):
    _modify(dialog, type_into)
    dialog._save_inputs()                       # start from a saved, clean state
    pump(100)
    assert dialog.is_modified is False
    field = line(dialog, KEY_WC_DENSITY)
    field.setFocus()
    field.selectAll()
    QTest.keyClicks(field, "8")                 # no Enter / focus-out yet
    messages.reply = "Cancel"
    n = len(messages)
    dialog.title_bar.btn_close.click()
    pump(100)
    assert any("unsaved changes" in m for m in messages.since(n))


def test_custom_design_mode_girder_depth(window, basic_inputs, messages, pump):
    window.input_dock._current_design_mode = VALUE_CUSTOM
    window.input_dict[KEY_DESIGN_MODE] = VALUE_CUSTOM
    window.common_design_func("Additional Inputs")
    pump(800)
    dlg = window._additional_inputs_dialog
    depth = dlg.findChild(QWidget, KEY_MP_GIRDER_DEPTH).currentWidget()
    depth.clear()
    pump(50)
    n = len(messages)
    dlg._save_inputs()
    pump(200)
    assert any("cannot be empty" in m and "Girder" in m for m in messages.since(n))
    assert dlg.focusWidget() is depth           # the dialog jumped to the field


def test_spacing_and_thickness_saved_in_the_dialog_survive_a_span_change(
        window, dialog, basic_inputs, type_into, pump):
    dialog._reveal_widget(line(dialog, KEY_TS_GIRDER_SPACING))
    type_into(line(dialog, KEY_TS_GIRDER_SPACING), "2.2")
    dialog._reveal_widget(line(dialog, KEY_TS_DECK_THICKNESS))
    type_into(line(dialog, KEY_TS_DECK_THICKNESS), "300")
    dialog._save_inputs()
    dialog.close()
    pump(200)
    for span in ("40", "38"):                      # kept across repeated changes
        type_into(basic_inputs(KEY_SPAN), span)
        pump(300)
        assert float(window.input_dict[KEY_TS_GIRDER_SPACING]) == pytest.approx(2.2)
        assert float(window.input_dict[KEY_TS_DECK_THICKNESS]) == pytest.approx(300)


def test_opening_the_dialog_without_edits_keeps_defaults_live(window, dialog, basic_inputs,
                                                               type_into, pump):
    dialog.close()
    pump(100)
    type_into(basic_inputs(KEY_CARRIAGEWAY_WIDTH), "9.5")
    pump(300)
    fresh = deepcopy(window.input_dict)
    solve_extend_basic_input_dict(fresh)          # what the solver alone produces
    assert float(window.input_dict[KEY_TS_GIRDER_SPACING]) == pytest.approx(
        float(fresh[KEY_TS_GIRDER_SPACING]))
    assert float(window.input_dict[KEY_TS_DECK_THICKNESS]) == pytest.approx(
        float(fresh[KEY_TS_DECK_THICKNESS]))
