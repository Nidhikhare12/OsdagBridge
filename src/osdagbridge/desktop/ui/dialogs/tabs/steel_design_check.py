from math import isfinite

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.design_checks import compute_all
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea

# From load_combination_tab.py defaults + output_dock
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]

# 8 design checks from the screenshot — 2 columns × 4 rows
DESIGN_CHECKS = [
    ("flexure",          "Strength Limit State (Flexure)"),
    ("shear_long_trans", "Resistance to Longitudinal and Transverse Shear"),
    ("shear",            "Strength Limit State (Shear)"),
    ("fatigue",          "Resistance to Fatigue"),
    ("interaction",      "Interaction"),
    ("stress",           "Stress Limitation"),
    ("ltb",              "Lateral Torsional Buckling"),
    ("deflection",       "Deflection and Crack Control"),
]


class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        self.check_widgets = {}   # key → labels for each check result

        super().__init__(parent)

        # ── identical white bg to SteelDesignDetailsTab ───────────────────────
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(18, 6, 18, 12)
        container_layout.setSpacing(16)

        # ── TOP BAR: Member ID (left) + Load Combination (right) ─────────────
        container_layout.addLayout(self._build_top_bar())

        # ── CHECK CARDS GRID: 2 columns ───────────────────────────────────────
        container_layout.addLayout(self._build_checks_grid())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        self.run_checks()

    # ── HELPERS — exact copy from steel_design_details.py ────────────────────

    def _section_card(self, title):
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setStyleSheet("""
            QFrame#sectionCard {
                background-color: white;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def _row_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; color: #000;")
        lbl.setMinimumWidth(180)
        return lbl

    def _make_grid(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._row_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _value_row(self, label_text):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 10px; color: #666; font-weight: 600;")

        value = QLabel("—")
        value.setStyleSheet("font-size: 10px; color: #000;")
        value.setTextFormat(Qt.RichText)
        value.setWordWrap(True)

        row.addWidget(label)
        row.addWidget(value, 1)
        return row, value

    def _status_style(self, status):
        if status == "PASS":
            return (
                "color: #2e7d32; background: #eaf5d1; border: 1px solid #9ccc65; "
                "border-radius: 6px; padding: 2px 8px; font-weight: bold; font-size: 10px;"
            )
        if status == "FAIL":
            return (
                "color: #c62828; background: #fdecea; border: 1px solid #f5a9a9; "
                "border-radius: 6px; padding: 2px 8px; font-weight: bold; font-size: 10px;"
            )
        return (
            "color: #444; background: #f1f1f1; border: 1px solid #d0d0d0; "
            "border-radius: 6px; padding: 2px 8px; font-weight: bold; font-size: 10px;"
        )

    # ── TOP BAR ───────────────────────────────────────────────────────────────

    def _build_top_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(24)
        bar.setContentsMargins(0, 0, 0, 0)

        # Member ID
        member_lbl = QLabel("Member ID")
        member_lbl.setStyleSheet("font-size: 11px; color: #000;")

        self.member_combo = NoScrollComboBox()
        apply_field_style(self.member_combo)
        self.member_combo.setFixedWidth(150)
        self.member_combo.setFixedHeight(22)
        self.member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])

        bar.addWidget(member_lbl)
        bar.addWidget(self.member_combo)

        bar.addSpacing(40)

        # Load Combination
        load_lbl = QLabel("Load Combination:")
        load_lbl.setStyleSheet("font-size: 11px; color: #000;")

        self.load_combo = NoScrollComboBox()
        apply_field_style(self.load_combo)
        self.load_combo.setFixedWidth(150)
        self.load_combo.setFixedHeight(22)
        self.load_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load_combo.addItems(LOAD_COMBINATIONS)

        bar.addWidget(load_lbl)
        bar.addWidget(self.load_combo)
        bar.addStretch()

        return bar

    # ── CHECK CARDS GRID ──────────────────────────────────────────────────────

    def _build_checks_grid(self):
        """
        2-column grid of check cards.
        Left column: flexure, shear, interaction, LTB
        Right column: longitudinal/transverse shear, fatigue, stress, deflection
        """
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for idx, (key, title) in enumerate(DESIGN_CHECKS):
            col = idx % 2
            row = idx // 2
            card = self._build_check_card(key, title)
            grid.addWidget(card, row, col)

        return grid

    def _fmt_value(self, value):
        if value is None:
            return "—"
        try:
            num = float(value)
        except (TypeError, ValueError):
            return str(value)
        if not isfinite(num):
            return "—"
        text = f"{num:.3f}".rstrip("0").rstrip(".")
        return text or "0"

    def _apply_status(self, label, status):
        status_text = status or "—"
        label.setText(status_text)
        label.setStyleSheet(self._status_style(status))

    def _update_check_card(self, key, data):
        widgets = self.check_widgets.get(key)
        if not widgets or not data:
            return

        equation = data.get("equation", "")
        widgets["equation"].setText(equation)

        result_label = data.get("result_label", "Result")
        result_value = self._fmt_value(data.get("result"))
        widgets["result"].setText(f"{result_label}: {result_value}")

        dcr_label = data.get("dcr_label", "DCR")
        dcr_value = self._fmt_value(data.get("dcr"))
        widgets["dcr"].setText(f"{dcr_label}: {dcr_value}")

        self._apply_status(widgets["status"], data.get("status"))

        details = data.get("details")
        if details:
            widgets["details"].setText(details)
            widgets["details"].setVisible(True)
        else:
            widgets["details"].clear()
            widgets["details"].setVisible(False)

    def _build_check_card(self, key, title):
        """
        Single check card:
          - Rounded border matching the screenshot style
                    - Bold title at top
                    - Equation, result, DCR, and status labels
        """
        card = QFrame()
        card.setObjectName("checkCard")
        card.setStyleSheet("""
            QFrame#checkCard {
                background-color: white;
                border: 1px solid #CFCFCF;
                border-radius: 8px;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #000;
                background: transparent;
                border: none;
            }
        """)
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)

        equation_lbl = QLabel()
        equation_lbl.setTextFormat(Qt.RichText)
        equation_lbl.setWordWrap(True)
        equation_lbl.setStyleSheet("font-size: 10px; color: #444;")
        card_layout.addWidget(equation_lbl)

        result_row, result_value_lbl = self._value_row("Result")
        card_layout.addLayout(result_row)

        dcr_row, dcr_value_lbl = self._value_row("DCR")
        card_layout.addLayout(dcr_row)

        details_lbl = QLabel()
        details_lbl.setWordWrap(True)
        details_lbl.setStyleSheet("font-size: 9px; color: #666;")
        details_lbl.setVisible(False)
        card_layout.addWidget(details_lbl)

        status_lbl = QLabel("—")
        status_lbl.setAlignment(Qt.AlignCenter)
        status_lbl.setFixedHeight(22)
        status_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        status_lbl.setStyleSheet(self._status_style(None))
        card_layout.addWidget(status_lbl, alignment=Qt.AlignRight)

        self.check_widgets[key] = {
            "equation": equation_lbl,
            "result": result_value_lbl,
            "dcr": dcr_value_lbl,
            "status": status_lbl,
            "details": details_lbl,
        }
        return card

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def run_checks(self, overrides=None):
        results = compute_all(overrides)
        for key, data in results.items():
            self._update_check_card(key, data)

    def set_girder_count(self, count):
        """Mirrors GirderDetailsTab.set_girder_count."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        """Populate from cad_state — populate girder count if available."""
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass

        overrides = None
        if isinstance(cad_state, dict):
            overrides = cad_state.get("design_check_inputs") or cad_state.get("design_checks")

        if isinstance(overrides, dict):
            self.run_checks(overrides)
        else:
            self.run_checks()

    def set_check_result(self, key: str, text: str):
        """Set result text for a specific check card."""
        if isinstance(text, dict):
            self._update_check_card(key, text)
            return

        widgets = self.check_widgets.get(key)
        if widgets and text:
            widgets["details"].setText(str(text))
            widgets["details"].setVisible(True)

    def clear_results(self):
        """Clear all check output areas."""
        for widgets in self.check_widgets.values():
            widgets["equation"].clear()
            widgets["result"].setText("—")
            widgets["dcr"].setText("—")
            widgets["details"].clear()
            widgets["details"].setVisible(False)
            self._apply_status(widgets["status"], None)