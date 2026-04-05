from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QTextEdit,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import NoScrollComboBox
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea

LOAD_COMBINATIONS = [
    "Envelope", "DL + LL", "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL", "WL", "EL", "IMF", "TL",
]

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

CHECK_EQUATIONS = {
    "flexure": (
        "Equation:  Mu \u2264 \u03c6 \u00b7 Mn\n"
        "\u03c6 = 1.0 (composite),  Mn = plastic moment capacity\n"
        "Status: \u2014"
    ),
    "shear": (
        "Equation:  Vu \u2264 \u03c6 \u00b7 Vn\n"
        "\u03c6 = 1.0,  Vn = 0.58 \u00b7 Fyw \u00b7 D \u00b7 tw\n"
        "Status: \u2014"
    ),
    "interaction": (
        "Equation:  (Mu/\u03c6Mn)\u00b2 + (Vu/\u03c6Vn)\u00b2 \u2264 1.0\n"
        "Combined bending and shear interaction check\n"
        "Status: \u2014"
    ),
    "ltb": (
        "Equation:  Mn = Cb[Mp \u2212 (Mp \u2212 0.7FySx)\u00b7(Lb\u2212Lp)/(Lr\u2212Lp)]\n"
        "Lp = plastic limit,  Lr = elastic limit\n"
        "Status: \u2014"
    ),
    "shear_long_trans": (
        "Equation:  Vh = AsFy / (0.85 \u00b7 f'c \u00b7 b)\n"
        "Longitudinal: Vsr \u2264 \u03c6sc \u00b7 Qn,  Transverse: Vu \u2264 \u03c6Vn\n"
        "Status: \u2014"
    ),
    "fatigue": (
        "Equation:  \u03b3\u00b7(\u0394f) \u2264 (\u0394F)n\n"
        "\u03b3 = load factor,  (\u0394F)n = nominal fatigue resistance\n"
        "Status: \u2014"
    ),
    "stress": (
        "Equation:  fa/Fa + fb/Fb \u2264 1.0\n"
        "fa = axial stress,  fb = bending stress\n"
        "Status: \u2014"
    ),
    "deflection": (
        "Equation:  \u03b4 \u2264 L / 360\n"
        "\u03b4 = max deflection,  L = span length\n"
        "Status: \u2014"
    ),
}


class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        self.check_outputs = {}
        super().__init__(parent)
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

        container_layout.addLayout(self._build_top_bar())
        container_layout.addLayout(self._build_checks_grid())
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def _row_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; color: #000;")
        lbl.setMinimumWidth(180)
        return lbl

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._row_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

    def _build_top_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(24)
        bar.setContentsMargins(0, 0, 0, 0)

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

    def _build_checks_grid(self):
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

    def _build_check_card(self, key, title):
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

        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(80)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output.setStyleSheet("""
            QTextEdit {
                background-color: #F9F9F9;
                border: none;
                font-size: 10px;
                color: #333;
                font-family: Consolas, monospace;
            }
        """)

        default_text = CHECK_EQUATIONS.get(key, "")
        if default_text:
            output.setPlainText(default_text)

        card_layout.addWidget(output)
        self.check_outputs[key] = output
        return card

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def set_girder_count(self, count):
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass
        for key, output in self.check_outputs.items():
            result = cad_state.get(f"check_{key}", "")
            output.setPlainText(str(result) if result else "")

    def set_check_result(self, key: str, text: str):
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def clear_results(self):
        for output in self.check_outputs.values():
            output.clear()