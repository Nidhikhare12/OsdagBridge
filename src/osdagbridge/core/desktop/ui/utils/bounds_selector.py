"""
Bounds Selector Dialog
Validation: popup on limit violation (editingFinished + textChanged),
silent adjustment for LL/UL relationship.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QPushButton, QLineEdit, QFormLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType


_DIALOG_STYLE = """
    QDialog#BoundsSelectorDialog {
        background-color: #FFFFFF;
        border: 1px solid #91b014;
        border-radius: 0px;
    }
    QDialog#BoundsSelectorDialog QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 12px;
        color: #333333;
    }
    QDialog#BoundsSelectorDialog QLineEdit:hover {
        border: 1px solid #999999;
    }
    QDialog#BoundsSelectorDialog QLineEdit:focus {
        border: 1px solid #91b014;
        background-color: #F5FFF9;
    }
    QDialog#BoundsSelectorDialog QLabel {
        color: #000000;
        font-size: 12px;
        background: transparent;
    }
"""

_BTN_STYLE = """
    QPushButton {
        background-color: white;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        border: 1px solid black;
        padding: 5px 14px;
        text-align: center;
    }
    QPushButton:hover {
        background-color: #91b014;
        border: 1px solid #91b014;
        color: white;
    }
    QPushButton:pressed {
        color: black;
        background-color: white;
        border: 1px solid black;
    }
"""


class BoundsSelectorDialog(QDialog):
    """
    Reusable bounds selector dialog.

    Validation rules:
    - Lower < lower_limit  → popup on editingFinished + textChanged, reset to lower_limit
    - Upper > upper_limit  → popup on editingFinished + textChanged, reset to upper_limit
    - Lower >= Upper       → silently adjust the other field
    - Increment >= (U-L)   → silently clamp

    Parameters
    ----------
    title : str
    bounds : dict  {"lower": float|None, "upper": float|None, "increment": float|None}
    with_increment : bool
    lower_limit : float | None
    upper_limit : float | None
    parent : QWidget | None
    """

    def __init__(
        self,
        title: str,
        bounds: dict,
        *,
        with_increment: bool = True,
        lower_limit: float | None = None,
        upper_limit: float | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("BoundsSelectorDialog")
        self._with_increment = with_increment
        self._lower_limit    = lower_limit
        self._upper_limit    = upper_limit
        self.bounds          = None
        self._showing_popup  = False  # guard against re-entrant popups

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet(_DIALOG_STYLE)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(1, 1, 1, 1)
        mainLayout.setSpacing(0)

        self.titleBar = CustomTitleBar(parent=self)
        self.titleBar.setTitle(title)
        mainLayout.addWidget(self.titleBar)

        contentWidget = QWidget(self)
        contentWidget.setStyleSheet("background:#ffffff;")
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(20, 20, 20, 20)
        contentLayout.setSpacing(12)

        # ── Extract initial values ─────────────────────────────────────────────
        raw_lower = bounds.get("lower")
        raw_upper = bounds.get("upper")
        raw_step  = bounds.get("increment")

        lower_text = f"{float(raw_lower):.2f}" if raw_lower is not None else ""
        upper_text = f"{float(raw_upper):.2f}" if raw_upper is not None else ""

        if raw_step is not None and raw_lower is not None and raw_upper is not None:
            lower_f = float(raw_lower)
            upper_f = float(raw_upper)
            step_f  = float(raw_step)
            if upper_f > lower_f and 0 < step_f < (upper_f - lower_f):
                step_text = f"{step_f:.2f}"
            else:
                step_max  = max(0.01, upper_f - lower_f - 0.01)
                step_text = f"{min(0.1, step_max):.2f}"
        else:
            step_text = ""

        # ── Form ───────────────────────────────────────────────────────────────
        formLayout = QFormLayout()
        formLayout.setSpacing(12)
        formLayout.setContentsMargins(0, 0, 0, 0)

        self.lowerBoundLineEdit = QLineEdit(lower_text)
        self.lowerBoundLineEdit.setObjectName("LowerBoundLineEdit")
        self.lowerBoundLineEdit.setFixedHeight(30)
        self.lowerBoundLineEdit.setPlaceholderText(
            f"Min: {lower_limit:.2f}" if lower_limit is not None else "Enter lower bound"
        )
        # Use permissive validator — real validation in callbacks
        self.lowerBoundLineEdit.setValidator(QDoubleValidator(-999999.0, 999999.0, 3))
        formLayout.addRow(QLabel("Lower Bound:"), self.lowerBoundLineEdit)

        self.upperBoundLineEdit = QLineEdit(upper_text)
        self.upperBoundLineEdit.setObjectName("UpperBoundLineEdit")
        self.upperBoundLineEdit.setFixedHeight(30)
        self.upperBoundLineEdit.setPlaceholderText(
            f"Max: {upper_limit:.2f}" if upper_limit is not None else "Enter upper bound"
        )
        self.upperBoundLineEdit.setValidator(QDoubleValidator(-999999.0, 999999.0, 3))
        formLayout.addRow(QLabel("Upper Bound:"), self.upperBoundLineEdit)

        self.stepLineEdit = QLineEdit(step_text)
        self.stepLineEdit.setObjectName("StepLineEdit")
        self.stepLineEdit.setFixedHeight(30)
        self.stepLineEdit.setPlaceholderText("Enter increment")
        self.stepLineEdit.setValidator(QDoubleValidator(0.0001, 999999.0, 3))
        if with_increment:
            formLayout.addRow(QLabel("Increment:"), self.stepLineEdit)

        contentLayout.addLayout(formLayout)

        # ── Signal wiring ──────────────────────────────────────────────────────
        # Limit validation — popup on BOTH textChanged (when complete) and editingFinished
        self.lowerBoundLineEdit.editingFinished.connect(self._validate_lower_finished)
        self.upperBoundLineEdit.editingFinished.connect(self._validate_upper_finished)

        # LL/UL relationship — silent on textChanged
        self.lowerBoundLineEdit.textChanged.connect(self._adjust_upper_if_needed)
        self.upperBoundLineEdit.textChanged.connect(self._adjust_lower_if_needed)

        # Increment
        if with_increment:
            self.lowerBoundLineEdit.textChanged.connect(self._update_step_max)
            self.upperBoundLineEdit.textChanged.connect(self._update_step_max)
            self.stepLineEdit.editingFinished.connect(self._validate_step)

        # ── Buttons ───────────────────────────────────────────────────────────
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(8)
        buttonLayout.setContentsMargins(0, 8, 0, 0)
        buttonLayout.addStretch()

        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.setStyleSheet(_BTN_STYLE)
        self.cancelButton.clicked.connect(self.reject)
        buttonLayout.addWidget(self.cancelButton)

        self.okButton = QPushButton("OK", self)
        self.okButton.setStyleSheet(_BTN_STYLE)
        self.okButton.clicked.connect(self._on_accept)
        buttonLayout.addWidget(self.okButton)

        contentLayout.addLayout(buttonLayout)
        mainLayout.addWidget(contentWidget)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _parse(self, text: str) -> float | None:
        try:
            return float(text.strip())
        except Exception:
            return None

    def _set_silently(self, widget: QLineEdit, text: str):
        widget.blockSignals(True)
        widget.setText(text)
        widget.blockSignals(False)

    def _popup(self, message: str):
        if self._showing_popup:
            return
        self._showing_popup = True
        CustomMessageBox(
            title="Invalid Value",
            text=message,
            buttons=["OK"],
            dialogType=MessageBoxType.Warning,
        ).exec()
        self._showing_popup = False

    # ── Limit validation with popup ────────────────────────────────────────────

    def _validate_lower_finished(self):
        """On editingFinished — popup + reset if outside hard limits."""
        val = self._parse(self.lowerBoundLineEdit.text())
        if val is None:
            return
        if self._lower_limit is not None and val < self._lower_limit:
            self._popup(
                f"Lower bound cannot be less than {self._lower_limit:.2f}.\n"
            )
            self._set_silently(self.lowerBoundLineEdit, f"{self._lower_limit:.2f}")
        elif self._upper_limit is not None and val > self._upper_limit:
            self._popup(
                f"Lower bound cannot exceed {self._upper_limit:.2f}.\n"
            )
            self._set_silently(self.lowerBoundLineEdit, f"{self._upper_limit:.2f}")

    def _validate_upper_finished(self):
        """On editingFinished — popup + reset if outside hard limits."""
        val = self._parse(self.upperBoundLineEdit.text())
        if val is None:
            return
        if self._upper_limit is not None and val > self._upper_limit:
            self._popup(
                f"Upper bound cannot exceed {self._upper_limit:.2f}.\n"
            )
            self._set_silently(self.upperBoundLineEdit, f"{self._upper_limit:.2f}")
        elif self._lower_limit is not None and val < self._lower_limit:
            self._popup(
                f"Upper bound cannot be less than {self._lower_limit:.2f}.\n"
            )
            self._set_silently(self.upperBoundLineEdit, f"{self._lower_limit:.2f}")

    # ── LL/UL relationship — silent ────────────────────────────────────────────

    def _adjust_upper_if_needed(self, text: str):
        lower = self._parse(text)
        upper = self._parse(self.upperBoundLineEdit.text())
        if lower is None or upper is None:
            return
        if lower >= upper:
            new_upper = lower + 1.0
            if self._upper_limit is not None:
                new_upper = min(self._upper_limit, new_upper)
            self._set_silently(self.upperBoundLineEdit, f"{new_upper:.2f}")

    def _adjust_lower_if_needed(self, text: str):
        upper = self._parse(text)
        lower = self._parse(self.lowerBoundLineEdit.text())
        if upper is None or lower is None:
            return
        if upper <= lower:
            new_lower = upper - 1.0
            if self._lower_limit is not None:
                new_lower = max(self._lower_limit, new_lower)
            self._set_silently(self.lowerBoundLineEdit, f"{new_lower:.2f}")

    # ── Increment ──────────────────────────────────────────────────────────────

    def _update_step_max(self, *_):
        lower = self._parse(self.lowerBoundLineEdit.text())
        upper = self._parse(self.upperBoundLineEdit.text())
        if lower is None or upper is None or upper <= lower:
            return
        step_max = max(0.0001, upper - lower - 0.0001)
        self.stepLineEdit.setValidator(QDoubleValidator(0.0001, step_max, 3))
        current = self._parse(self.stepLineEdit.text())
        if current and current >= (upper - lower):
            self._set_silently(self.stepLineEdit, f"{step_max:.4f}")

    def _validate_step(self):
        lower = self._parse(self.lowerBoundLineEdit.text())
        upper = self._parse(self.upperBoundLineEdit.text())
        step  = self._parse(self.stepLineEdit.text())
        if None in (lower, upper, step) or upper <= lower:
            return
        step_max = max(0.0001, upper - lower - 0.0001)
        if step <= 0 or step >= (upper - lower):
            self._set_silently(self.stepLineEdit, f"{step_max:.4f}")

    # ── Accept ─────────────────────────────────────────────────────────────────

    def _on_accept(self):
        lower_text = self.lowerBoundLineEdit.text().strip()
        upper_text = self.upperBoundLineEdit.text().strip()

        if not lower_text or not upper_text:
            self._popup("Please fill in both Lower Bound and Upper Bound.")
            return

        lower = self._parse(lower_text)
        upper = self._parse(upper_text)

        if lower is None or upper is None:
            self._popup("Please enter valid numeric values.")
            return

        if self._lower_limit is not None and lower < self._lower_limit:
            self._popup(f"Lower bound cannot be less than {self._lower_limit:.2f}.")
            return

        if self._upper_limit is not None and upper > self._upper_limit:
            self._popup(f"Upper bound cannot exceed {self._upper_limit:.2f}.")
            return

        if upper <= lower:
            self._popup("Upper bound must be greater than lower bound.")
            return

        if self._with_increment:
            step_text = self.stepLineEdit.text().strip()
            if not step_text:
                self._popup("Please enter an increment value.")
                return
            step = self._parse(step_text)
            if step is None or step <= 0:
                self._popup("Increment must be a positive number.")
                return
            if step >= (upper - lower):
                self._popup(
                    f"Increment must be less than (Upper - Lower) = {upper - lower:.2f}."
                )
                return
        else:
            step = 1.0

        self.bounds = {"lower": lower, "upper": upper, "increment": step}
        self.accept()

    def result_bounds(self) -> dict | None:
        return self.bounds