from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.core.utils.design_checks import run_all_checks
from osdagbridge.desktop.ui.widgets.status_badge import StatusBadge
from osdagbridge.desktop.ui.widgets.utilization_bar import UtilizationBar

# From load_combination_tab.py defaults + output_dock
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]

# 8 design checks 
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

_CHECK_TOOLTIPS = {
    "flexure":          "IS 800:2007 Cl. 8.2.1.2 — Design Bending Strength",
    "shear":            "IS 800:2007 Cl. 8.4 — Design Shear Strength",
    "interaction":      "IS 800:2007 Cl. 9.2 — Combined Bending and Shear",
    "ltb":              "IS 800:2007 Cl. 8.2.2 — Lateral Torsional Buckling",
    "shear_long_trans": "IRC:22-2015 Cl. 606 — Shear Connectors",
    "fatigue":          "IRC:22-2015 Cl. 12 — Fatigue Assessment",
    "stress":           "IRC:24-2010 Cl. 509 — Stress Limitation at Service",
    "deflection":       "IRC:24-2010 Cl. 304 — Deflection Limits",
}


class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):

        self.check_eq_labels = {}
        self.check_val_labels = {}
        self.check_dcr_labels = {}
        self.check_bars = {}
        self.check_badges = {}

        self.summary_passed_label = None
        self.summary_failed_label = None
        self.summary_badge = None

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

        # ── SUMMARY BAR: Passed/Failed counts ────────────────────────────────
        container_layout.addWidget(self._build_summary_bar())

        # ── CHECK CARDS GRID: 2 columns ───────────────────────────────────────
        container_layout.addLayout(self._build_checks_grid())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    # ── (Removed dead config methods from steel_design_details) ──

    # ── SUMMARY BAR ──────────────────────────────────────────────────────────

    def _build_summary_bar(self):
        frame = QFrame()
        frame.setObjectName("summaryFrame")
        frame.setStyleSheet(
            "QFrame#summaryFrame {"
            "background: #f0f4e8; border: 1px solid #90AF13;"
            "border-radius: 6px; padding: 4px;"
            "}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(16)
        
        label = QLabel("Checks: 8")
        label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2b2b2b; background: transparent; border: none;")
        layout.addWidget(label)
        
        self.summary_passed_label = QLabel("Passed: —")
        self.summary_passed_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2b2b2b; background: transparent; border: none;")
        layout.addWidget(self.summary_passed_label)
        
        self.summary_failed_label = QLabel("Failed: —")
        self.summary_failed_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2b2b2b; background: transparent; border: none;")
        layout.addWidget(self.summary_failed_label)
        
        layout.addStretch()
        
        self.summary_badge = StatusBadge()
        layout.addWidget(self.summary_badge)
        
        return frame

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
        self.member_combo.currentTextChanged.connect(self._on_inputs_changed)

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
        self.load_combo.currentTextChanged.connect(self._on_inputs_changed)

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
        card_layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #000;
                background: transparent;
                border: none;
            }
        """)
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)
        
        card_layout.addSpacing(4)

        eq_label = QLabel()
        eq_label.setStyleSheet("""
            font-family: 'Cambria Math', 'Times New Roman', serif;
            font-size: 13px;
            color: #2E3B4E;
            background-color: #F8F9FA;
            border: 1px solid #E4E7EB;
            border-radius: 4px;
            padding: 6px;
        """)
        eq_label.setWordWrap(True)
        eq_label.setToolTip(_CHECK_TOOLTIPS.get(key, ""))
        card_layout.addWidget(eq_label)
        
        card_layout.addSpacing(6)

        val_label = QLabel()
        val_label.setStyleSheet("font-size: 13px; color: #222; background: transparent; border: none;")
        val_label.setWordWrap(True)
        card_layout.addWidget(val_label)
        
        card_layout.addSpacing(6)

        dcr_label = QLabel()
        dcr_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #000; background: transparent; border: none;")
        card_layout.addWidget(dcr_label)

        card_layout.addSpacing(6)
        
        bar = UtilizationBar()
        card_layout.addWidget(bar)
        
        card_layout.addSpacing(4)

        badge = StatusBadge()
        card_layout.addWidget(badge)

        self.check_eq_labels[key] = eq_label
        self.check_val_labels[key] = val_label
        self.check_dcr_labels[key] = dcr_label
        self.check_bars[key] = bar
        self.check_badges[key] = badge
        return card

    # ── PUBLIC API ────────────────────────────────────────────────────────────

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

        self._current_cad_state = dict(cad_state)
        self.update_results(self._current_cad_state)

    def _on_inputs_changed(self):
        bridge_data = getattr(self, "_current_cad_state", {})
        
        member = self.member_combo.currentText()
        load = self.load_combo.currentText()

        modifier = 1.0
        if "Girder 1" in member:
            modifier = 1.1
        elif "Girder 2" in member:
            modifier = 0.9

        if "DL" in load and "LL" not in load:
            modifier *= 0.6
        elif "WL" in load:
            modifier *= 0.8

        bridge_data["_dynamic_modifier"] = modifier
        self.update_results(bridge_data)
        
    def update_results(self, bridge_data: dict):
        self.design_results = run_all_checks(bridge_data)

        result_mapping = {}
        if len(self.design_results) >= 8:
            result_mapping = {
                "flexure": self.design_results[0],
                "shear": self.design_results[1],
                "interaction": self.design_results[2],
                "ltb": self.design_results[3],
                "shear_long_trans": self.design_results[4],
                "fatigue": self.design_results[5],
                "stress": self.design_results[6],
                "deflection": self.design_results[7],
            }

        render_map = {
            "flexure": {
                "eq": "<i>M<sub>d</sub></i> &le; <i>M<sub>r</sub></i><br><i>M<sub>r</sub></i> = <i>&beta;<sub>b</sub></i> &middot; <i>Z<sub>p</sub></i> &middot; <i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>",
                "dem_pfx": "<i>M<sub>d</sub></i>", "cap_pfx": "<i>M<sub>r</sub></i>", "unit": "kN&middot;m"
            },
            "shear": {
                "eq": "<i>V<sub>d</sub></i> &le; <i>V<sub>r</sub></i><br><i>V<sub>r</sub></i> = <i>A<sub>v</sub></i> &middot; <i>f<sub>y</sub></i> / (&radic;3 &middot; <i>&gamma;<sub>m</sub></i>)",
                "dem_pfx": "<i>V<sub>d</sub></i>", "cap_pfx": "<i>V<sub>r</sub></i>", "unit": "kN"
            },
            "interaction": {
                "eq": "<i>M<sub>d</sub></i> / <i>M<sub>r</sub></i> + <i>V<sub>d</sub></i> / <i>V<sub>r</sub></i> &le; 1.0",
                "unit": ""
            },
            "ltb": {
                "eq": "<i>M<sub>d</sub></i> &le; <i>M<sub>cr</sub></i><br><i>M<sub>cr</sub></i> &approx; (&pi;&sup2; &middot; <i>E</i> &middot; <i>I<sub>y</sub></i>) / <i>L<sub>LTB</sub></i>&sup2;",
                "dem_pfx": "<i>M<sub>d</sub></i>", "cap_pfx": "<i>M<sub>cr</sub></i>", "unit": "kN&middot;m"
            },
            "shear_long_trans": {
                "eq": "<i>V<sub>d</sub></i> &le; <i>V<sub>rd</sub></i><br><i>V<sub>rd</sub></i> = <i>V<sub>rd,c</sub></i> + <i>V<sub>rd,s</sub></i><br><i>V<sub>rd,c</sub></i> = 0.18 &middot; <i>k</i> &middot; (100<i>f<sub>ck</sub></i>)<sup>1/3</sup> &middot; <i>b</i> &middot; <i>d</i><br><i>V<sub>rd,s</sub></i> = (<i>A<sub>sv</sub></i> &middot; <i>f<sub>y</sub></i> &middot; <i>d</i>) / <i>s</i>",
                "dem_pfx": "<i>V<sub>d</sub></i>", "cap_pfx": "<i>V<sub>rd</sub></i>", "unit": "kN"
            },
            "fatigue": {
                "eq": "&Delta;<i>&sigma;</i> &le; &Delta;<i>&sigma;<sub>allowable</sub></i><br>&Delta;<i>&sigma;<sub>allowable</sub></i> = &Delta;<i>&sigma;<sub>c</sub></i> / <i>&gamma;<sub>mf</sub></i>",
                "dem_pfx": "&Delta;<i>&sigma;</i>", "cap_pfx": "&Delta;<i>&sigma;<sub>allowable</sub></i>", "unit": "MPa"
            },
            "stress": {
                "eq": "<i>&sigma;</i> = <i>M<sub>d</sub></i> / <i>Z</i><br><i>&sigma;</i> &le; <i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>",
                "dem_pfx": "<i>&sigma;</i>", "cap_pfx": "<i>f<sub>y</sub> / &gamma;<sub>m</sub></i>", "unit": "MPa"
            },
            "deflection": {
                "eq": "<i>&delta;</i> &le; <i>L</i> / <i>x</i><br>(Default <i>x</i> = 600)",
                "dem_pfx": "<i>&delta;</i>", "cap_pfx": "<i>L / x</i>", "unit": "mm"
            }
        }

        for key, res in result_mapping.items():
            if key not in self.check_eq_labels:
                continue

            demand = res.get("demand", 0.0)
            capacity = res.get("capacity", 0.0)
            ratio = res.get("ratio", 0.0)
            passed = res.get("passed", False)
            
            rm = render_map.get(key, {})
            unit = rm.get("unit", "")
            unit_str = f" {unit}" if unit else ""

            if key == "interaction":
                eq_text = rm.get('eq', "")
                val_text = f"<i>M<sub>d</sub></i> / <i>M<sub>r</sub></i> + <i>V<sub>d</sub></i> / <i>V<sub>r</sub></i> = {demand:.2f}"
                dcr_text = f"DCR = {ratio:.2f}"
            else:
                eq_text = rm.get('eq', "")
                val_text = f"{rm.get('dem_pfx', '')} = {demand:.2f}{unit_str}<br>{rm.get('cap_pfx', '')} = {capacity:.2f}{unit_str}"
                dcr_text = f"DCR = {ratio:.2f}"

            self.check_eq_labels[key].setText(eq_text)
            self.check_val_labels[key].setText(val_text)
            self.check_dcr_labels[key].setText(dcr_text)

            dcr_col = "#388E3C" if passed else "#D32F2F"
            self.check_dcr_labels[key].setStyleSheet(f"font-size: 14px; font-weight: bold; color: {dcr_col}; background: transparent; border: none;")

            self.check_bars[key].set_ratio(ratio)
            if passed:
                self.check_badges[key].set_pass()
            else:
                self.check_badges[key].set_fail()

        self._refresh_summary()

    def _refresh_summary(self):
        passed = sum(1 for r in self.design_results if r.get("passed"))
        failed = len(self.design_results) - passed
        if self.summary_passed_label:
            self.summary_passed_label.setText(f"Passed: {passed}")
        if self.summary_failed_label:
            self.summary_failed_label.setText(f"Failed: {failed}")
        if self.summary_badge:
            if failed == 0:
                self.summary_badge.set_pass()
            else:
                self.summary_badge.set_fail()


    def clear_results(self):
        for key in self.check_badges:
            if key in self.check_eq_labels:
                self.check_eq_labels[key].setText("")
            if key in self.check_val_labels:
                self.check_val_labels[key].setText("")
            if key in self.check_dcr_labels:
                self.check_dcr_labels[key].setText("")
            if key in self.check_bars:
                self.check_bars[key].set_ratio(0)
            if key in self.check_badges:
                self.check_badges[key].set_neutral()


