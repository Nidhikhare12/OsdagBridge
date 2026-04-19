import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QFrame, QSizePolicy, QTextEdit,
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

# ── HTML formula strings shown in the card header (subscripts + superscripts) ─
# QLabel with Qt.RichText renders <sub> and <sup> natively.
EQ_HTML = {
    "flexure": (
        "M<sub>r</sub> = &beta;<sub>b</sub> &middot; Z<sub>p</sub> "
        "&middot; f<sub>y</sub> / &gamma;<sub>m</sub>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = M<sub>d</sub> / M<sub>r</sub>"
    ),
    "shear_long_trans": (
        # Full equation — this was the missing piece flagged by the reviewer
        "V<sub>rd</sub> = V<sub>rd,c</sub> + V<sub>rd,s</sub>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "V<sub>rd,c</sub> = 0.18&middot;k&middot;(100&rho;f<sub>ck</sub>)<sup>1/3</sup>&middot;b&middot;d"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "V<sub>rd,s</sub> = A<sub>sv</sub>&middot;f<sub>y</sub>&middot;d / s"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = V<sub>d</sub> / V<sub>rd</sub>"
    ),
    "shear": (
        "V<sub>r</sub> = A<sub>v</sub> &middot; f<sub>y</sub> "
        "/ (&radic;3 &middot; &gamma;<sub>m</sub>)"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = V<sub>d</sub> / V<sub>r</sub>"
    ),
    "fatigue": (
        "&Delta;&sigma;<sub>allow</sub> = "
        "&Delta;&sigma;<sub>C</sub> / &gamma;<sub>mf</sub>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = &Delta;&sigma; / &Delta;&sigma;<sub>allow</sub>"
    ),
    "interaction": (
        "M<sub>d</sub>/M<sub>r</sub> + V<sub>d</sub>/V<sub>r</sub> &le; 1"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = M<sub>d</sub>/M<sub>r</sub> + V<sub>d</sub>/V<sub>r</sub>"
    ),
    "stress": (
        "&sigma; = M<sub>d</sub> / Z<sub>e</sub>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "&sigma; &le; f<sub>y</sub> / &gamma;<sub>m</sub>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = &sigma; / (f<sub>y</sub>/&gamma;<sub>m</sub>)"
    ),
    "ltb": (
        "M<sub>cr</sub> = &pi;<sup>2</sup>&middot;E&middot;I<sub>y</sub> "
        "/ L<sub>LTB</sub><sup>2</sup>"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = M<sub>d</sub> / M<sub>cr</sub>"
    ),
    "deflection": (
        "&delta; &le; L / 600"
        "&nbsp;&nbsp;|&nbsp;&nbsp;"
        "DCR = &delta; / (L/600)"
    ),
}


# ── Calculation logic (zero PySide6 imports) ──────────────────────────────────

class DesignChecks:
    """
    Pure-Python calculation class — all 8 steel design checks.
    Returns a dict with:
      'lines' : list of HTML strings (subscripts/superscripts) for display
      'DCR'   : Demand/Capacity Ratio (float)
      'pass'  : bool (DCR <= 1.0)
    Units: N, mm, MPa throughout.
    """

    GAMMA_M  = 1.10   # IS 800 material partial safety factor
    GAMMA_MF = 1.15   # fatigue partial safety factor

    # 1. Flexure ───────────────────────────────────────────────────────────────
    @staticmethod
    def flexure(Md, Zp, fy, beta_b=1.0):
        gm  = DesignChecks.GAMMA_M
        Mr  = beta_b * Zp * fy / gm
        DCR = Md / Mr if Mr > 0 else float("inf")
        return {
            "lines": [
                f"&beta;<sub>b</sub> = {beta_b},&nbsp; Z<sub>p</sub> = {Zp/1e3:.1f}×10<sup>3</sup> mm<sup>3</sup>",
                f"f<sub>y</sub> = {fy} MPa,&nbsp; &gamma;<sub>m</sub> = {gm}",
                f"M<sub>r</sub> = &beta;<sub>b</sub>&middot;Z<sub>p</sub>&middot;f<sub>y</sub>/&gamma;<sub>m</sub> = {Mr/1e6:.2f} kN&middot;m",
                f"M<sub>d</sub> = {Md/1e6:.2f} kN&middot;m",
                f"DCR = M<sub>d</sub>/M<sub>r</sub> = {DCR:.3f}",
            ],
            "Mr": Mr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 2. Shear ─────────────────────────────────────────────────────────────────
    @staticmethod
    def shear(Vd, Av, fy):
        gm  = DesignChecks.GAMMA_M
        Vr  = (Av * fy) / (math.sqrt(3) * gm)
        DCR = Vd / Vr if Vr > 0 else float("inf")
        return {
            "lines": [
                f"A<sub>v</sub> = {Av:.0f} mm&sup2;,&nbsp; f<sub>y</sub> = {fy} MPa",
                f"V<sub>r</sub> = A<sub>v</sub>&middot;f<sub>y</sub>/(&radic;3&middot;&gamma;<sub>m</sub>) = {Vr/1e3:.2f} kN",
                f"V<sub>d</sub> = {Vd/1e3:.2f} kN",
                f"DCR = V<sub>d</sub>/V<sub>r</sub> = {DCR:.3f}",
            ],
            "Vr": Vr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 3. Interaction ───────────────────────────────────────────────────────────
    @staticmethod
    def interaction(Md, Mr, Vd, Vr):
        mr  = Md / Mr if Mr > 0 else float("inf")
        vr  = Vd / Vr if Vr > 0 else float("inf")
        DCR = mr + vr
        return {
            "lines": [
                f"M<sub>d</sub>/M<sub>r</sub> = {mr:.3f}",
                f"V<sub>d</sub>/V<sub>r</sub> = {vr:.3f}",
                f"DCR = {mr:.3f} + {vr:.3f} = {DCR:.3f}",
            ],
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 4. LTB ───────────────────────────────────────────────────────────────────
    @staticmethod
    def ltb(Md, E, Iy, L_LTB):
        Mcr = (math.pi**2 * E * Iy) / (L_LTB**2) if L_LTB > 0 else float("inf")
        DCR = Md / Mcr if Mcr > 0 else float("inf")
        return {
            "lines": [
                f"E = {E/1e3:.0f}×10<sup>3</sup> MPa,&nbsp; I<sub>y</sub> = {Iy/1e6:.2f}×10<sup>6</sup> mm<sup>4</sup>",
                f"L<sub>LTB</sub> = {L_LTB:.0f} mm",
                f"M<sub>cr</sub> = &pi;<sup>2</sup>&middot;E&middot;I<sub>y</sub>/L<sub>LTB</sub><sup>2</sup> = {Mcr/1e6:.2f} kN&middot;m",
                f"M<sub>d</sub> = {Md/1e6:.2f} kN&middot;m",
                f"DCR = M<sub>d</sub>/M<sub>cr</sub> = {DCR:.3f}",
            ],
            "Mcr": Mcr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 5. Resistance to Long. & Trans. Shear ────────────────────────────────────
    @staticmethod
    def shear_long_trans(Vd, rho, fck, b, d, Asv, fy, s):
        """
        V_rd,c  = 0.18 · k · (100 · rho · fck)^(1/3) · b · d
        V_rd,s  = Asv · fy · d / s
        k       = 1 + sqrt(200/d)  <= 2.0   (size factor)
        V_rd    = V_rd,c + V_rd,s
        DCR     = Vd / V_rd
        """
        k     = min(2.0, 1.0 + math.sqrt(200.0 / d)) if d > 0 else 2.0
        Vrd_c = 0.18 * k * (100.0 * rho * fck) ** (1.0/3.0) * b * d
        Vrd_s = (Asv * fy * d) / s if s > 0 else 0.0
        Vrd   = Vrd_c + Vrd_s
        DCR   = Vd / Vrd if Vrd > 0 else float("inf")
        return {
            "lines": [
                f"k = 1+&radic;(200/d) = {k:.3f}&nbsp;(&le;2.0)",
                f"V<sub>rd,c</sub> = 0.18&middot;k&middot;(100&rho;f<sub>ck</sub>)<sup>1/3</sup>&middot;b&middot;d = {Vrd_c/1e3:.2f} kN",
                f"V<sub>rd,s</sub> = A<sub>sv</sub>&middot;f<sub>y</sub>&middot;d/s = {Vrd_s/1e3:.2f} kN",
                f"V<sub>rd</sub> = V<sub>rd,c</sub> + V<sub>rd,s</sub> = {Vrd/1e3:.2f} kN",
                f"V<sub>d</sub> = {Vd/1e3:.2f} kN",
                f"DCR = V<sub>d</sub>/V<sub>rd</sub> = {DCR:.3f}",
            ],
            "Vrd": Vrd, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 6. Fatigue ───────────────────────────────────────────────────────────────
    @staticmethod
    def fatigue(delta_sigma, delta_sigma_C):
        gmf = DesignChecks.GAMMA_MF
        dsa = delta_sigma_C / gmf
        DCR = delta_sigma / dsa if dsa > 0 else float("inf")
        return {
            "lines": [
                f"&Delta;&sigma;<sub>C</sub> = {delta_sigma_C:.2f} MPa,&nbsp; &gamma;<sub>mf</sub> = {gmf}",
                f"&Delta;&sigma;<sub>allow</sub> = &Delta;&sigma;<sub>C</sub>/&gamma;<sub>mf</sub> = {dsa:.2f} MPa",
                f"&Delta;&sigma; = {delta_sigma:.2f} MPa",
                f"DCR = &Delta;&sigma;/&Delta;&sigma;<sub>allow</sub> = {DCR:.3f}",
            ],
            "delta_sigma_allowable": dsa,
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 7. Stress Limitation ─────────────────────────────────────────────────────
    @staticmethod
    def stress(Md, Ze, fy):
        gm    = DesignChecks.GAMMA_M
        sigma = Md / Ze if Ze > 0 else float("inf")
        slim  = fy / gm
        DCR   = sigma / slim if slim > 0 else float("inf")
        return {
            "lines": [
                f"Z<sub>e</sub> = {Ze/1e3:.1f}×10<sup>3</sup> mm<sup>3</sup>",
                f"&sigma; = M<sub>d</sub>/Z<sub>e</sub> = {sigma:.2f} MPa",
                f"Limit = f<sub>y</sub>/&gamma;<sub>m</sub> = {slim:.2f} MPa",
                f"DCR = &sigma;/(f<sub>y</sub>/&gamma;<sub>m</sub>) = {DCR:.3f}",
            ],
            "sigma": sigma, "sigma_limit": slim,
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # 8. Deflection ────────────────────────────────────────────────────────────
    @staticmethod
    def deflection(delta, L, x=600.0):
        limit = L / x if x > 0 else float("inf")
        DCR   = delta / limit if limit > 0 else float("inf")
        return {
            "lines": [
                f"L = {L:.0f} mm,&nbsp; x = {x:.0f}",
                f"Limit = L/x = {limit:.2f} mm",
                f"&delta; = {delta:.2f} mm",
                f"DCR = &delta;/(L/x) = {DCR:.3f}",
            ],
            "limit": limit, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── Run all checks ────────────────────────────────────────────────────────
    @classmethod
    def run_all(cls, data):
        flex_r  = cls.flexure(data["Md"], data["Zp"], data["fy"], data.get("beta_b", 1.0))
        shear_r = cls.shear(data["Vd"], data["Av"], data["fy"])
        return {
            "flexure":          flex_r,
            "shear":            shear_r,
            "interaction":      cls.interaction(data["Md"], flex_r["Mr"],
                                                data["Vd"], shear_r["Vr"]),
            "ltb":              cls.ltb(data["Md"], data["E"],
                                        data["Iy"], data["L_LTB"]),
            "shear_long_trans": cls.shear_long_trans(
                                    data["Vd"], data["rho"], data["fck"],
                                    data["b"],  data["d"],
                                    data["Asv"], data["fy"], data["s"]),
            "fatigue":          cls.fatigue(data["delta_sigma"],
                                            data["delta_sigma_C"]),
            "stress":           cls.stress(data["Md"], data["Ze"], data["fy"]),
            "deflection":       cls.deflection(data["delta"], data["L"],
                                               data.get("defl_x", 600.0)),
        }

    @staticmethod
    def _default_data():
        return {
            "Md": 500e6, "Zp": 3000e3, "Ze": 2700e3,
            "fy": 250,   "beta_b": 1.0,
            "Vd": 300e3, "Av": 4800,
            "E": 2.0e5,  "Iy": 1.5e8, "L_LTB": 3500,
            "rho": 0.012, "fck": 35, "b": 300, "d": 600,
            "Asv": 402,  "s": 150,
            "delta_sigma": 80, "delta_sigma_C": 100,
            "delta": 12, "L": 20000, "defl_x": 600,
        }


# ── UI ────────────────────────────────────────────────────────────────────────

class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        self.check_outputs = {}
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()
        container   = QWidget()
        container.setStyleSheet("background-color: white;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(18, 6, 18, 12)
        c_layout.setSpacing(16)
        c_layout.addLayout(self._build_top_bar())
        c_layout.addLayout(self._build_checks_grid())
        c_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)
        self._populate_defaults()

    def _populate_defaults(self):
        results = DesignChecks.run_all(DesignChecks._default_data())
        for key, result in results.items():
            self._display_result(key, result)

    def _display_result(self, key: str, result: dict):
        if key not in self.check_outputs:
            return
        output = self.check_outputs[key]
        lines  = result.get("lines", [])
        passed = result.get("pass", True)
        html_lines = []
        for line in lines:
            if line.startswith("DCR"):
                color  = "#2e7d32" if passed else "#c62828"
                status = "&nbsp;&nbsp;&#10003; OK" if passed else "&nbsp;&nbsp;&#10007; FAIL"
                html_lines.append(
                    f'<span style="color:{color}; font-weight:bold;">{line}{status}</span>'
                )
            else:
                html_lines.append(f'<span style="color:#333333;">{line}</span>')
        output.setHtml(
            '<div style="font-family:\'Courier New\',monospace; font-size:10px; line-height:1.5;">'
            + "<br>".join(html_lines) + "</div>"
        )

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
            card = self._build_check_card(key, title)
            grid.addWidget(card, idx // 2, idx % 2)
        return grid

    def _build_check_card(self, key: str, title: str) -> QFrame:
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

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #000;"
            "background: transparent; border: none;"
        )
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)

        # ── Equation formula with HTML subscripts/superscripts ────────────────
        eq_lbl = QLabel()
        eq_lbl.setTextFormat(Qt.RichText)
        eq_lbl.setText(
            f'<span style="font-size:9px; color:#555;">{EQ_HTML.get(key, "")}</span>'
        )
        eq_lbl.setWordWrap(True)
        eq_lbl.setStyleSheet("background: transparent; border: none;")
        card_layout.addWidget(eq_lbl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#E0E0E0; background-color:#E0E0E0; border:none;")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        # Result text area — extra height for the 6-line shear_long_trans card
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(104 if key == "shear_long_trans" else 88)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output.setStyleSheet(
            "QTextEdit { background-color:white; border:none;"
            "font-family:'Courier New',monospace; font-size:10px; color:#333; }"
        )
        card_layout.addWidget(output)
        self.check_outputs[key] = output
        return card

    # ── Public API ────────────────────────────────────────────────────────────

    def set_girder_count(self, count: int):
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        if not cad_state:
            return
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass
        data = DesignChecks._default_data()
        key_map = {
            "Md": "Md", "Vd": "Vd", "fy": "fy", "Zp": "Zp", "Ze": "Ze",
            "Av": "Av", "E_modulus": "E", "Iy": "Iy", "L_LTB": "L_LTB",
            "rho": "rho", "fck": "fck", "b": "b", "d": "d",
            "Asv": "Asv", "s": "s",
            "delta_sigma": "delta_sigma", "delta_sigma_C": "delta_sigma_C",
            "deflection": "delta", "span": "L",
        }
        for src, dst in key_map.items():
            val = cad_state.get(src)
            if val is not None:
                try:
                    data[dst] = float(val)
                except (ValueError, TypeError):
                    pass
        has_pre = any(cad_state.get(f"check_{k}") for k in self.check_outputs)
        if has_pre:
            for key in self.check_outputs:
                txt = cad_state.get(f"check_{key}", "")
                if txt:
                    self.check_outputs[key].setPlainText(str(txt))
            return
        for key, result in DesignChecks.run_all(data).items():
            self._display_result(key, result)

    def set_check_result(self, key: str, text: str):
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def set_check_result_from_dict(self, key: str, result: dict):
        self._display_result(key, result)

    def clear_results(self):
        for output in self.check_outputs.values():
            output.clear()