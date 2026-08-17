# osdagbridge/src/report_generator/config/validation_key_based.py
# Key-Based Input Interception, Validation, and State Management Layer

from PySide6.QtWidgets import QMessageBox

# Importing central keys as strictly required by OsdagBridge Architecture Rules
# to prevent hardcoding of parameter strings
try:
    from osdagbridge.core.utils.common import (
        KEY_ADD_CARRIAGEWAY_WIDTH,
        KEY_ADD_GIRDER_SPACING,
        KEY_ADD_DECK_THICKNESS,
        KEY_ADD_SPAN_LENGTH
    )
except ImportError:
    # Fallback keys mapped explicitly to prevent system halt during module load
    KEY_ADD_CARRIAGEWAY_WIDTH = "KEY_ADD_CARRIAGEWAY_WIDTH"
    KEY_ADD_GIRDER_SPACING = "KEY_ADD_GIRDER_SPACING"
    KEY_ADD_DECK_THICKNESS = "KEY_ADD_DECK_THICKNESS"
    KEY_ADD_SPAN_LENGTH = "KEY_ADD_SPAN_LENGTH"

class AdditionalInputsValidator:
    def __init__(self, dialog_instance):
        self.dialog = dialog_instance
        self.dialog.is_modified = False  # Track unsaved changes state flag

    def check_pre_save_validation(self):
        """
        Intercepts the Save action. Iterates through all active tabs 
        using central architecture keys to halt empty 'Custom' input submissions.
        """
        # Central architecture mapping matrix using defined common keys
        validation_matrix = [
            {"key": KEY_ADD_CARRIAGEWAY_WIDTH, "name": "Carriageway Width", "input_attr": "carriageway_width_input", "mode_attr": "carriageway_mode"},
            {"key": KEY_ADD_GIRDER_SPACING, "name": "Girder Spacing", "input_attr": "girder_spacing_input", "mode_attr": "girder_mode"},
            {"key": KEY_ADD_DECK_THICKNESS, "name": "Deck Thickness", "input_attr": "deck_thickness_input", "mode_attr": "deck_mode"},
            {"key": KEY_ADD_SPAN_LENGTH, "name": "Span Length", "input_attr": "span_length_input", "mode_attr": "span_mode"}
        ]

        for item in validation_matrix:
            mode = getattr(self.dialog, item["mode_attr"], "Standard")
            input_field = getattr(self.dialog, item["input_attr"], None)
            
            # Validation Trigger: Dropdown/Radio set to "Custom" but field is empty
            if mode == "Custom" or (input_field and hasattr(input_field, "isEnabled") and input_field.isEnabled()):
                if input_field and hasattr(input_field, "text"):
                    if not input_field.text().strip():
                        self.trigger_error_dialog(item["name"])
                        return False  # Halt save process immediately
        return True

    def trigger_error_dialog(self, parameter_name):
        """
        Triggers standard OsdagBridge Error Dialog matching explicit required format.
        """
        error_msg = f"Error: The custom value for '{parameter_name}' cannot be empty."
        msg_box = QMessageBox(self.dialog)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Validation Error")
        msg_box.setText(error_msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def process_close_event(self, event):
        """
        Overrides closeEvent. If self.is_modified is True, prompts user with Unsaved Warning.
        """
        if getattr(self.dialog, "is_modified", False):
            warning_msg = "You have unsaved changes. Closing this window will discard them. Do you want to proceed?"
            
            msg_box = QMessageBox(self.dialog)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Unsaved Changes")
            msg_box.setText(warning_msg)
            
            discard_btn = msg_box.addButton("Discard", QMessageBox.DestRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.exec()
            
            if msg_box.clickedButton() == discard_btn:
                event.accept()  # Close and discard
            else:
                event.ignore()  # Cancel closure
        else:
            event.accept()
