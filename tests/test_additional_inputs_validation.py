import os
import sys
from copy import deepcopy
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit, QComboBox
from PySide6.QtGui import QCloseEvent

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs import (
    AdditionalInputs, CUSTOM_PARAMETER_MAPPINGS
)
from osdagbridge.desktop.ui.template_page import CustomWindow
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def setup_dialog(qapp):
    win = CustomWindow("Test", PlateGirderBridge)
    win.input_dict[KEY_SPAN] = 25.0
    win.input_dict[KEY_CARRIAGEWAY_WIDTH] = 7.5
    win.input_dict[KEY_SKEW_ANGLE] = 0.0
    solve_extend_basic_input_dict(win.input_dict)
    dlg = win._get_additional_inputs()
    win._show_additional_inputs()
    return win, dlg

def test_initial_state_is_not_modified(qapp):
    win, dlg = setup_dialog(qapp)
    assert dlg.is_modified is False

def test_user_input_marks_modified(qapp):
    win, dlg = setup_dialog(qapp)
    assert dlg.is_modified is False
    
    # Simulate user editing a textbox
    w = dlg.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
    assert w is not None
    w.setText("300")
    w.textEdited.emit("300")
    assert dlg.is_modified is True

def test_custom_validation_empty_fails(qapp):
    win, dlg = setup_dialog(qapp)
    
    # Set Footpath Pressure mode to Custom, and empty value
    mode_w = dlg.findChild(QComboBox, KEY_LL_FOOTPATH_PRESSURE_MODE)
    val_w = dlg.findChild(QLineEdit, KEY_LL_FOOTPATH_PRESSURE_VALUE)
    assert mode_w is not None
    assert val_w is not None
    
    mode_w.setCurrentText("Custom")
    val_w.setText("")
    dlg.working_input_dict[KEY_LL_FOOTPATH_PRESSURE_MODE] = "Custom"
    dlg.working_input_dict[KEY_LL_FOOTPATH_PRESSURE_VALUE] = ""
    
    with patch("osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs.CustomMessageBox") as MockMsgBox:
        mock_instance = MagicMock()
        MockMsgBox.return_value = mock_instance
        
        saved = dlg.validate_custom_inputs()
        assert saved is False
        assert MockMsgBox.called
        call_kwargs = MockMsgBox.call_args.kwargs
        assert "Footpath Pressure" in call_kwargs.get("text", "")
        assert "cannot be empty" in call_kwargs.get("text", "")
        assert call_kwargs.get("title") == "Error"

def test_custom_validation_whitespace_fails(qapp):
    win, dlg = setup_dialog(qapp)
    
    # Set Wind Gust Factor to Custom with whitespace only
    mode_w = dlg.findChild(QComboBox, KEY_WL_GUST_FACTOR_MODE)
    val_w = dlg.findChild(QLineEdit, KEY_WL_GUST_FACTOR_VALUE)
    assert mode_w is not None
    assert val_w is not None
    
    mode_w.setCurrentText("Custom")
    val_w.setText("   ")
    dlg.working_input_dict[KEY_WL_GUST_FACTOR_MODE] = "Custom"
    dlg.working_input_dict[KEY_WL_GUST_FACTOR_VALUE] = "   "
    
    with patch("osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs.CustomMessageBox") as MockMsgBox:
        mock_instance = MagicMock()
        MockMsgBox.return_value = mock_instance
        
        saved = dlg.validate_custom_inputs()
        assert saved is False
        assert MockMsgBox.called
        call_kwargs = MockMsgBox.call_args.kwargs
        assert "Gust Factor" in call_kwargs.get("text", "")
        assert "cannot be empty" in call_kwargs.get("text", "")

def test_custom_validation_valid_succeeds(qapp):
    win, dlg = setup_dialog(qapp)
    
    # Make sure all custom fields are either not custom or have valid values
    mode_w = dlg.findChild(QComboBox, KEY_LL_FOOTPATH_PRESSURE_MODE)
    val_w = dlg.findChild(QLineEdit, KEY_LL_FOOTPATH_PRESSURE_VALUE)
    mode_w.setCurrentText("Custom")
    val_w.setText("0.005")
    dlg.working_input_dict[KEY_LL_FOOTPATH_PRESSURE_MODE] = "Custom"
    dlg.working_input_dict[KEY_LL_FOOTPATH_PRESSURE_VALUE] = "0.005"
    
    assert dlg.validate_custom_inputs() is True

def test_close_event_unmodified_closes(qapp):
    win, dlg = setup_dialog(qapp)
    dlg.is_modified = False
    
    event = QCloseEvent()
    dlg.closeEvent(event)
    assert event.isAccepted() is True

def test_close_event_modified_cancel_keeps_open(qapp):
    win, dlg = setup_dialog(qapp)
    dlg.is_modified = True
    
    event = QCloseEvent()
    with patch("osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs.CustomMessageBox") as MockMsgBox:
        mock_instance = MagicMock()
        mock_instance.exec.return_value = "Cancel"
        MockMsgBox.return_value = mock_instance
        
        dlg.closeEvent(event)
        assert event.isAccepted() is False
        assert dlg.is_modified is True

def test_close_event_modified_discard_reverts(qapp):
    win, dlg = setup_dialog(qapp)
    
    w = dlg.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
    initial_val = w.text()
    w.setText("999")
    dlg.working_input_dict[KEY_TS_DECK_THICKNESS] = "999"
    dlg.is_modified = True
    
    event = QCloseEvent()
    with patch("osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs.CustomMessageBox") as MockMsgBox:
        mock_instance = MagicMock()
        mock_instance.exec.return_value = "Discard"
        MockMsgBox.return_value = mock_instance
        
        dlg.closeEvent(event)
        assert event.isAccepted() is True
        assert dlg.is_modified is False
        # Verify reverted
        assert dlg.working_input_dict[KEY_TS_DECK_THICKNESS] == dlg.default_input_dict[KEY_TS_DECK_THICKNESS]
