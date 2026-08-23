import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCloseEvent
from osdagbridge.core.utils.common import (
    KEY_CB_TYPE,
    KEY_CB_DENSITY,
    KEY_CB_WIDTH,
    KEY_CB_HEIGHT,
    KEY_CB_AREA,
    KEY_CB_LOAD,
    KEY_INCLUDE_MEDIAN,
    VALUES_NO_YES,
    KEY_MD_TYPE,
    KEY_MD_DENSITY,
    KEY_MD_WIDTH,
    KEY_MD_HEIGHT,
    KEY_MD_AREA,
    KEY_MD_LOAD,
    KEY_FOOTPATH,
    VALUES_FOOTPATH,
    KEY_RL_TYPE,
    KEY_RL_WIDTH,
    KEY_RL_HEIGHT,
    KEY_RL_LOAD_MODE,
    KEY_RL_LOAD_VALUE,
    KEY_WC_MATERIAL,
    KEY_WC_DENSITY,
    KEY_WC_THICKNESS,
    KEY_WL_GUST_FACTOR,
    KEY_DESIGN_MODE,
    KEY_MP_GIRDER_DEPTH,
    VALUE_CUSTOM,
)
from osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs import AdditionalInputs

# Ensure QApplication exists for GUI tests
app = QApplication.instance() or QApplication([])


def test_additional_inputs_initial_state():
    dialog = AdditionalInputs()
    assert dialog.is_modified is False


def test_additional_inputs_modified_flag_on_update():
    dialog = AdditionalInputs()
    assert dialog.is_modified is False
    dialog._update_input_dict("some_key", "some_value")
    assert dialog.is_modified is True


def test_custom_validation_empty_crash_barrier():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_CB_TYPE] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_CB_DENSITY] = ""
    dialog.working_input_dict[KEY_CB_WIDTH] = "0.5"
    dialog.working_input_dict[KEY_CB_HEIGHT] = "1.0"
    dialog.working_input_dict[KEY_CB_AREA] = "0.4"
    dialog.working_input_dict[KEY_CB_LOAD] = "10.0"
    
    errors = dialog._validate_custom_inputs()
    assert any("Crash Barrier Material Density" in err for err in errors)


def test_custom_validation_valid_crash_barrier():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_CB_TYPE] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_CB_DENSITY] = "25.0"
    dialog.working_input_dict[KEY_CB_WIDTH] = "0.5"
    dialog.working_input_dict[KEY_CB_HEIGHT] = "1.0"
    dialog.working_input_dict[KEY_CB_AREA] = "0.4"
    dialog.working_input_dict[KEY_CB_LOAD] = "10.0"
    dialog.working_input_dict[KEY_INCLUDE_MEDIAN] = VALUES_NO_YES[0]  # No
    dialog.working_input_dict[KEY_FOOTPATH] = VALUES_FOOTPATH[0]      # None
    dialog.working_input_dict[KEY_WC_MATERIAL] = "Bituminous Concrete"
    dialog.working_input_dict[KEY_DESIGN_MODE] = "Auto"

    errors = dialog._validate_custom_inputs()
    assert not any("Crash Barrier" in err for err in errors)


def test_custom_validation_empty_median():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_INCLUDE_MEDIAN] = VALUES_NO_YES[1]  # Yes
    dialog.working_input_dict[KEY_MD_TYPE] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_MD_DENSITY] = ""
    dialog.working_input_dict[KEY_MD_WIDTH] = "1.2"
    dialog.working_input_dict[KEY_MD_HEIGHT] = "0.8"
    dialog.working_input_dict[KEY_MD_AREA] = "0.9"
    dialog.working_input_dict[KEY_MD_LOAD] = "8.0"
    
    errors = dialog._validate_custom_inputs()
    assert any("Median Material Density" in err for err in errors)


def test_custom_validation_empty_railing():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_FOOTPATH] = VALUES_FOOTPATH[1]  # Left
    dialog.working_input_dict[KEY_RL_TYPE] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_RL_WIDTH] = ""
    dialog.working_input_dict[KEY_RL_HEIGHT] = "1.1"
    
    errors = dialog._validate_custom_inputs()
    assert any("Railing Width" in err for err in errors)


def test_custom_validation_empty_wearing_course():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_WC_MATERIAL] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_WC_DENSITY] = ""
    dialog.working_input_dict[KEY_WC_THICKNESS] = "0.065"
    
    errors = dialog._validate_custom_inputs()
    assert any("Wearing Course Density" in err for err in errors)


def test_custom_validation_empty_wind_load():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_WL_GUST_FACTOR + ".mode"] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_WL_GUST_FACTOR + ".value"] = ""
    
    errors = dialog._validate_custom_inputs()
    assert any("Gust Factor, G" in err for err in errors)


def test_custom_validation_empty_girder_custom():
    dialog = AdditionalInputs()
    dialog.working_input_dict[KEY_DESIGN_MODE] = VALUE_CUSTOM
    dialog.working_input_dict[KEY_MP_GIRDER_DEPTH] = ""
    
    errors = dialog._validate_custom_inputs()
    assert any("Girder Depth" in err for err in errors)


def test_close_event_unmodified():
    dialog = AdditionalInputs()
    dialog.is_modified = False
    event = QCloseEvent()
    dialog.closeEvent(event)
    assert event.isAccepted()
