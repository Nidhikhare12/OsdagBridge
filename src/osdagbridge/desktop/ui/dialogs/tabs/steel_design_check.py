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

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea


LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
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


# 🔥 EQUATIONS (MAIN ADDITION)
CHECK_EQUATIONS = {
    "flexure": """
    <b>Md ≤ Mr</b><br>
    Mr = β<sub>b</sub> · Z<sub>p</sub> · f<sub>y</sub> / γ<sub>m</sub><br>
    DCR = Md / Mr
    """,

    "shear": """
    <b>Vd ≤ Vr</b><br>
    Vr = A<sub>v</sub> · f<sub>y</sub> / (√3 · γ<sub>m</sub>)<br>
    DCR = Vd / Vr
    """,

    "interaction": """
    <b>Md/Mr + Vd/Vr ≤ 1</b><br>
    DCR = Md/Mr + Vd/Vr
    """,

    "ltb": """
    <b>Md ≤ Mcr</b><br>
    Mcr = π² E I<sub>y</sub> / (L<sub>LTB</sub>)²<br>
    DCR = Md / Mcr
    """,

    "shear_long_trans": """
    <b>Vd ≤ Vrd</b><br>
    Vrd = Vrd,c + Vrd,s<br>
    DCR = Vd / Vrd
    """,

    "fatigue": """
    <b>Δσ ≤ Δσ allowable</b><br>
    Δσ allowable = Δσc / γmf<br>
    DCR = Δσ / Δσ allowable
    """,

    "stress": """
    <b>σ = Md / Z</b><br>
    σ ≤ f<sub>y</sub> / γ<sub>m</sub><br>
    DCR = σ / (f<sub>y</sub>/γ<sub>m</sub>)
    """,

    "deflection": """
    <b>δ ≤ L / x</b><br>
    (x = 600 default)
    """,
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

    # ── TOP BAR ─────────────────────────────────────────────

    def _build_top_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(24)

        member_lbl = QLabel("Member ID")
        member_lbl.setStyleSheet("font-size: 11px;")

        self.member_combo = NoScrollComboBox()
        apply_field_style(self.member_combo)
        self.member_combo.setFixedSize(150, 22)
        self.member_combo.addItems(["All", "Girder 1", "Girder 2"])

        bar.addWidget(member_lbl)
        bar.addWidget(self.member_combo)

        bar.addSpacing(40)

        load_lbl = QLabel("Load Combination:")
        load_lbl.setStyleSheet("font-size: 11px;")

        self.load_combo = NoScrollComboBox()
        apply_field_style(self.load_combo)
        self.load_combo.setFixedSize(150, 22)
        self.load_combo.addItems(LOAD_COMBINATIONS)

        bar.addWidget(load_lbl)
        bar.addWidget(self.load_combo)
        bar.addStretch()

        return bar

    # ── GRID ───────────────────────────────────────────────

    def _build_checks_grid(self):
        grid = QGridLayout()
        grid.setSpacing(16)

        for idx, (key, title) in enumerate(DESIGN_CHECKS):
            col = idx % 2
            row = idx // 2
            grid.addWidget(self._build_check_card(key, title), row, col)

        return grid

    # 🔥 MAIN CARD WITH EQUATIONS
    def _build_check_card(self, key, title):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #CFCFCF;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        layout.addWidget(title_lbl)

        # 🔥 EQUATION LABEL
        eq_label = QLabel()
        eq_label.setTextFormat(Qt.RichText)
        eq_label.setWordWrap(True)
        eq_label.setStyleSheet("font-size: 10px; color: #444;")
        eq_label.setText(CHECK_EQUATIONS.get(key, ""))

        layout.addWidget(eq_label)

        # RESULT BOX
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(50)
        output.setStyleSheet("font-size: 10px;")
        layout.addWidget(output)

        self.check_outputs[key] = output

        return card

    # ── API ───────────────────────────────────────────────

    def set_check_result(self, key: str, text: str):
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def clear_results(self):
        for output in self.check_outputs.values():
            output.clear()