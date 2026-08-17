# osdagbridge/src/report_generator/config/cad_interaction.py
# Interactive 2D CAD Canvas Parameter Editing and UI Synchronization Hook

from PySide6.QtWidgets import QGraphicsTextItem, QLineEdit, QGraphicsProxyWidget
from PySide6.QtCore import Qt

class EditableCADLabel(QGraphicsTextItem):
    def __init__(self, text, parameter_name, main_window_instance, is_editable=True):
        super().__init__(text)
        self.parameter_name = parameter_name
        self.main_window = main_window_instance
        self.is_editable = is_editable  # Write-Enabled vs Read-Only Lock Flag
        
        # Locked Parameters (Overhang, Width, Bracing) will remain non-editable
        if not self.is_editable:
            self.setDefaultTextColor(Qt.darkGray)

    def mouseDoubleClickEvent(self, event):
        """
        Intercepts double-click events on the CAD canvas text labels.
        Replaces text with a temporary line-edit box for authorized parameters.
        """
        if not self.is_editable:
            print(f"🔒 Derived Parameter '{self.parameter_name}' is locked (Read-Only) to prevent mathematical conflicts.")
            return  # Halts execution for locked parameters
            
        self.setVisible(False)
        
        # Create a temporary numerical line-edit input box
        self.line_edit = QLineEdit()
        self.line_edit.setText(self.toPlainText())
        self.line_edit.setFixedWidth(65)
        
        proxy = QGraphicsProxyWidget(self.parentItem())
        proxy.setWidget(self.line_edit)
        proxy.setPos(self.pos())
        
        # Save changes upon pressing Enter or losing focus
        self.line_edit.returnPressed.connect(lambda: self.apply_new_value(proxy))
        self.line_edit.editingFinished.connect(lambda: self.apply_new_value(proxy) if proxy.isVisible() else None)
        self.line_edit.setFocus()

    def apply_new_value(self, proxy):
        """
        Validates the typed numerical value and pushes it back to main UI input dictionaries.
        """
        if not proxy.isVisible():
            return
            
        new_text = self.line_edit.text().strip()
        try:
            numeric_value = float(new_text)
            
            # Synchronize changes back to the main basic/additional input dictionaries
            if hasattr(self.main_window, 'basic_inputs') and self.parameter_name in self.main_window.basic_inputs:
                self.main_window.basic_inputs[self.parameter_name] = numeric_value
            elif hasattr(self.main_window, 'additional_inputs'):
                self.main_window.additional_inputs[self.parameter_name] = numeric_value
                
            self.setPlainText(new_text)
            
            # Trigger the standard OsdagBridge redraw sequence
            if hasattr(self.main_window, 'redraw_cad_canvas'):
                self.main_window.redraw_cad_canvas()
            elif hasattr(self.main_window, 'update_drawings'):
                self.main_window.update_drawings()
                
        except ValueError:
            print("⚠️ Validation Failure: Input must be a valid numerical value.")
            
        proxy.deleteLater()
        self.setVisible(True)
