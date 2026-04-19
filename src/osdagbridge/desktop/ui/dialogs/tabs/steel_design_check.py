from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QPushButton,
    QSizePolicy,
    QTextEdit,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.docks.output_dock import (
    NoScrollComboBox,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
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

# Static equation-template strings shown on each card before any computation
def _build_eq(*lines):
    html = '<div style="font-family: sans-serif; font-size: 11px;">'
    for line in lines:
        if isinstance(line, list):
            html += '<table cellspacing="0" cellpadding="0" align="center" style="margin-top: 5px; margin-bottom: 5px;"><tr>'
            for item in line:
                if isinstance(item, tuple):
                    html += f'<td valign="middle"><table cellspacing="0" cellpadding="0"><tr><td align="center" style="border-bottom: 1px solid #888; padding: 0 4px;">{item[0]}</td></tr><tr><td align="center" style="padding: 0 4px;">{item[1]}</td></tr></table></td>'
                else:
                    html += f'<td valign="middle" style="padding: 0 4px;">{item}</td>'
            html += '</tr></table>'
        else:
            html += f'<div style="text-align: center; margin-top: 5px; margin-bottom: 5px;">{line}</div>'
    html += '</div>'
    return html

def _dcr(num, den):
    return [
        "<span style='font-size: 13px; font-style: italic;'>DCR</span><span style='font-size: 13px;'> = </span>", 
        (f"<span style='font-size: 13px;'>{num}</span>", f"<span style='font-size: 13px;'>{den}</span>")
    ]

EQUATION_TEMPLATES = {
    "flexure": _build_eq(
        "<i>M<sub>d</sub></i> &le; <i>M<sub>r</sub></i>",
        ["<i>M<sub>r</sub></i> = ", ("<i>&beta;<sub>b</sub></i> &middot; <i>Z<sub>p</sub></i> &middot; <i>f<sub>y</sub></i>", "<i>&gamma;<sub>m</sub></i>")],
        _dcr("<i>M<sub>d</sub></i>", "<i>M<sub>r</sub></i>")
    ),
    "shear": _build_eq(
        "<i>V<sub>d</sub></i> &le; <i>V<sub>r</sub></i>",
        ["<i>V<sub>r</sub></i> = ", ("<i>A<sub>v</sub></i> &middot; <i>f<sub>y</sub></i>", "&radic;<span style='text-decoration: overline;'>3</span> &middot; <i>&gamma;<sub>m</sub></i>")],
        _dcr("<i>V<sub>d</sub></i>", "<i>V<sub>r</sub></i>")
    ),
    "interaction": _build_eq(
        [("<i>M<sub>d</sub></i>", "<i>M<sub>r</sub></i>"), " + ", ("<i>V<sub>d</sub></i>", "<i>V<sub>r</sub></i>"), " &le; 1"],
        ["<span style='font-size: 13px; font-style: italic;'>DCR</span><span style='font-size: 13px;'> = </span>", 
         (f"<span style='font-size: 13px;'><i>M<sub>d</sub></i></span>", f"<span style='font-size: 13px;'><i>M<sub>r</sub></i></span>"),
         "<span style='font-size: 13px;'> + </span>",
         (f"<span style='font-size: 13px;'><i>V<sub>d</sub></i></span>", f"<span style='font-size: 13px;'><i>V<sub>r</sub></i></span>")]
    ),
    "ltb": _build_eq(
        "<i>M<sub>d</sub></i> &le; <i>M<sub>cr</sub></i>",
        ["<i>M<sub>cr</sub></i> &approx; ", ("&pi;<sup>2</sup> <i>E I<sub>y</sub></i>", "<i>L</i><sup>2</sup><sub>LTB</sub>")],
        _dcr("<i>M<sub>d</sub></i>", "<i>M<sub>cr</sub></i>")
    ),
    "shear_long_trans": _build_eq(
        "<i>V<sub>d</sub></i> &le; <i>V<sub>rd</sub></i>",
        ["<i>V<sub>rd</sub></i> = ", "<i>V<sub>rd,c</sub></i>", " + ", "<i>V<sub>rd,s</sub></i>"],
        ["<i>V<sub>rd,c</sub></i> = ",
         ("0.18 &middot; <i>k</i> &middot; (100 &middot; <i>&rho;<sub>l</sub></i> &middot; <i>f<sub>ck</sub></i>)<sup>1/3</sup>",
          "<i>&gamma;<sub>m</sub></i>"),
         " &middot; <i>b<sub>w</sub></i> &middot; <i>d</i>"],
        _dcr("<i>V<sub>d</sub></i>", "<i>V<sub>rd</sub></i>")
    ),
    "fatigue": _build_eq(
        ["&Delta;<i>&sigma;</i><sub>allow</sub> = ", ("&Delta;<i>&sigma;<sub>C</sub></i>", "<i>&gamma;<sub>mf</sub></i>")],
        _dcr("&Delta;<i>&sigma;</i>", "&Delta;<i>&sigma;</i><sub>allow</sub>")
    ),
    "stress": _build_eq(
        ["<i>&sigma;</i> = ", ("<i>M<sub>d</sub></i>", "<i>Z<sub>e</sub></i>"), " &le; ", ("<i>f<sub>y</sub></i>", "<i>&gamma;<sub>m</sub></i>")],
        _dcr("<i>&sigma;</i>", "<i>f<sub>y</sub></i> / <i>&gamma;<sub>m</sub></i>")
    ),
    "deflection": _build_eq(
        ["<i>&delta;</i> &le; ", ("<i>L</i>", "<i>x</i>"), " &nbsp;(<i>x</i> = 600 default)"],
        _dcr("<i>&delta;</i>", "<i>L</i> / <i>x</i>")
    ),
}

# Badge colours
_BADGE_OK_BG = "#90AF13"
_BADGE_FAIL_BG = "#D9534F"
_BADGE_PENDING_BG = "#BBBBBB"


class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        self.check_outputs = {}   # key → QTextEdit for each check result
        self.check_badges = {}    # key → QLabel status badge

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

        # ── RUN CHECKS BUTTON ROW ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        self.run_btn = QPushButton("Run Design Checks")
        self.run_btn.setFixedHeight(28)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 18px;
            }
            QPushButton:hover { background-color: #7a9510; }
            QPushButton:pressed { background-color: #647c0e; }
        """)
        self.run_btn.clicked.connect(self._execute_checks)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 10px; color: #666;")

        btn_row.addWidget(self.run_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.status_lbl)
        btn_row.addStretch()
        container_layout.addLayout(btn_row)

        # ── CHECK CARDS GRID: 2 columns ───────────────────────────────────────
        container_layout.addLayout(self._build_checks_grid())

        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

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

    def _readonly_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setFixedHeight(22)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(self._row_label(text), row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget,                row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        return row + 1

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

    def _build_check_card(self, key, title):
        """
        Single check card:
          - Rounded border matching the screenshot style
          - Bold title at top
          - Italic gray equation template label
          - Expanding QTextEdit output area below (readonly)
          - Colored status badge (OK / FAIL / pending)
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
        card_layout.setSpacing(4)

        # ── Title row with badge ──────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

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
        title_row.addWidget(title_lbl, 1)

        # Status badge
        badge = QLabel("\u2014")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(48, 20)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {_BADGE_PENDING_BG};
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
                padding: 0 6px;
            }}
        """)
        title_row.addWidget(badge, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.check_badges[key] = badge

        card_layout.addLayout(title_row)

        # ── Equation template label ───────────────────────────────────────────
        eq_template = EQUATION_TEMPLATES.get(key, "")
        eq_lbl = QLabel(eq_template)
        eq_lbl.setTextFormat(Qt.RichText)
        eq_lbl.setAlignment(Qt.AlignCenter)
        eq_lbl.setWordWrap(True)
        eq_lbl.setStyleSheet("""
            QLabel {
                color: #888;
                background: transparent;
                border: none;
            }
        """)
        card_layout.addWidget(eq_lbl)

        # ── Output area — readonly, shows check results ───────────────────────
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(44)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 10px;
                color: #333;
            }
        """)
        card_layout.addWidget(output)

        self.check_outputs[key] = output
        return card

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def set_girder_count(self, count):
        """Mirrors GirderDetailsTab.set_girder_count."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        """Populate from cad_state — populate girder count if available."""
        self._cad_state = cad_state or {}
        if not self._cad_state:
            return
        
        try:
            self.set_girder_count(int(self._cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass

        # Populate check output areas if results are explicitly in cad_state
        for key, output in self.check_outputs.items():
            result = self._cad_state.get(f"check_{key}", "")
            output.setPlainText(str(result) if result else "")

        self._execute_checks()

    def set_check_result(self, key: str, text: str):
        """Set result text for a specific check card."""
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def clear_results(self):
        """Clear all check output areas and reset badges."""
        for output in self.check_outputs.values():
            output.clear()
        for badge in self.check_badges.values():
            badge.setText("\u2014")
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {_BADGE_PENDING_BG};
                    color: white;
                    font-size: 9px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: none;
                    padding: 0 6px;
                }}
            """)

    def _update_badge(self, key: str, status: str):
        """Update the status badge colour and text for *key*."""
        badge = self.check_badges.get(key)
        if badge is None:
            return
        bg = _BADGE_OK_BG if status == "OK" else _BADGE_FAIL_BG
        badge.setText(status)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
                padding: 0 6px;
            }}
        """)

    # ── RUN CHECKS ────────────────────────────────────────────────────────────

    def run_checks(self, params: dict):
        """Run all 8 design checks via :class:`DesignCheckEngine`.

        *params* must map each check key to a sub-dict of the values that
        particular check expects.  For example::

            params = {
                "flexure": {"beta_b": 1.0, "Zp": 2500, "fy": 250, "gamma_m": 1.1, "Md": 200},
                "shear":   {"Av": 3000, "fy": 250, "gamma_m": 1.1, "Vd": 150},
                ...
            }

        Missing keys are silently skipped so partial runs are safe.
        """
        from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check_engine import (
            DesignCheckEngine,
        )

        _dispatch = {
            "flexure":          DesignCheckEngine.check_flexure,
            "shear":            DesignCheckEngine.check_shear,
            "interaction":      DesignCheckEngine.check_interaction,
            "ltb":              DesignCheckEngine.check_ltb,
            "shear_long_trans": DesignCheckEngine.check_shear_long_trans,
            "fatigue":          DesignCheckEngine.check_fatigue,
            "stress":           DesignCheckEngine.check_stress,
            "deflection":       DesignCheckEngine.check_deflection,
        }

        for key, check_fn in _dispatch.items():
            sub = params.get(key)
            if sub is None:
                continue
            try:
                result = check_fn(sub)
                self.set_check_result(key, result["equation_str"])
                self._update_badge(key, result["status"])
            except (KeyError, TypeError, ZeroDivisionError):
                # Missing / malformed param — surface gracefully
                self.set_check_result(key, "⚠ insufficient parameters")
                self._update_badge(key, "FAIL")

    # ── CHECK EXECUTION ───────────────────────────────────────────────────────

    def _execute_checks(self):
        """Run checks with real values extracted from cad_state."""
        self.status_lbl.setText("Running…")
        
        cad_state = getattr(self, "_cad_state", {})

        def get_val(key, default):
            try:
                val = cad_state.get(key)
                if val is not None and str(val).strip() != "":
                    return float(val)
            except (ValueError, TypeError):
                pass
            return default

        # Bridge geometry and material properties
        span = get_val("span", 35.0)
        fy = get_val("fy", 250.0)
        E = get_val("E", 200000.0)
        gamma_m = get_val("gamma_m", 1.10)

        # Analysis Demands (Moment and Shear)
        Md = get_val("moment_demand", 480e6)
        Vd = get_val("shear_demand", 1800e3)
        
        # Section properties & other inputs
        Zp = get_val("Zp", 2500e3)
        Av = get_val("Av", 18000.0)
        Iy = get_val("Iy", 6.5e8)
        Ze = get_val("Ze", 2200e3)

        # Computed resistances for interaction check
        Mr = 1.0 * Zp * fy / gamma_m
        import math
        Vr = Av * fy / (math.sqrt(3) * gamma_m)

        params = {
            "flexure": {
                "beta_b": 1.0,
                "Zp": Zp,
                "fy": fy,
                "gamma_m": gamma_m,
                "Md": Md,
            },
            "shear": {
                "Av": Av,
                "fy": fy,
                "gamma_m": gamma_m,
                "Vd": Vd,
            },
            "interaction": {
                "Md": Md,
                "Mr": Mr,
                "Vd": Vd,
                "Vr": Vr,
            },
            "ltb": {
                "E": E,
                "Iy": Iy,
                "L_LTB": span * 1000,
                "Md": Md,
            },
            "shear_long_trans": {
                "k": get_val("k", 2.0),
                "rho": get_val("rho", 0.015),
                "fck": get_val("fck", 35),
                "b": get_val("deck_width", 2000),
                "d": get_val("deck_depth", 200),
                "Asv": get_val("Asv", 1200),
                "fy": get_val("rebar_fy", 500),
                "s": get_val("stirrup_spacing", 150),
                "Vd": get_val("shear_demand_long", 350e3),
            },
            "fatigue": {
                "delta_sigma_C": get_val("delta_sigma_C", 71),
                "gamma_mf": get_val("gamma_mf", 1.15),
                "delta_sigma": get_val("delta_sigma", 52),
            },
            "stress": {
                "Md": Md,
                "Ze": Ze,
                "fy": fy,
                "gamma_m": gamma_m,
            },
            "deflection": {
                "L": span,
                "delta": get_val("delta", 0.048),
                "x": get_val("deflection_limit_x", 600),
            },
        }

        self.run_checks(params)

        passed = sum(1 for b in self.check_badges.values() if b.text() == "OK")
        total  = len(self.check_badges)
        self.status_lbl.setText(
            f"{passed}/{total} checks passed  •  "
            + ("✓ All OK" if passed == total else "⚠ Review failures")
        )
        ok_color = "#90AF13" if passed == total else "#D9534F"
        self.status_lbl.setStyleSheet(f"font-size: 10px; color: {ok_color};")