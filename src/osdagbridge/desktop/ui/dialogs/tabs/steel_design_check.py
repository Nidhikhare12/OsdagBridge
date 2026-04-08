import math

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

# From load_combination_tab.py defaults + output_dock
LOAD_COMBINATIONS = [
    "Envelope",
    "DL + LL",
    "1.35 DL + 1.5 LL",
    "DL", "SIDL", "LL",
    "WL", "EL", "IMF", "TL",
]

# 8 design checks — order matches the screenshot layout (left-col first, row by row)
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


# ── Calculation logic (separated from UI) ─────────────────────────────────────

class DesignChecks:
    """
    Pure-calculation class for all 8 steel design checks.
    No UI imports — keeps logic completely separate from presentation.

    All inputs are in consistent SI units:
      Forces  : N
      Moments : N·mm
      Lengths : mm
      Stress  : MPa (N/mm²)
      Area    : mm²
    """

    GAMMA_M  = 1.10   # material partial safety factor (IS 800)
    GAMMA_MF = 1.15   # fatigue partial safety factor

    # ── 1. Strength Limit State — Flexure ─────────────────────────────────────
    @staticmethod
    def flexure(Md: float, Zp: float, fy: float, beta_b: float = 1.0) -> dict:
        """
        Check  : Md ≤ Mr
        Mr     = beta_b · Zp · fy / gamma_m
        DCR    = Md / Mr
        """
        gamma_m = DesignChecks.GAMMA_M
        Mr  = beta_b * Zp * fy / gamma_m
        DCR = Md / Mr if Mr > 0 else float("inf")
        return {
            "equation": (
                f"Mr = βb·Zp·fy/γm\n"
                f"   = {beta_b}×{Zp/1e3:.1f}×10³×{fy}/{gamma_m}\n"
                f"   = {Mr/1e6:.2f} kN·m\n"
                f"Md = {Md/1e6:.2f} kN·m\n"
                f"DCR = Md/Mr = {DCR:.3f}"
            ),
            "Mr": Mr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 2. Strength Limit State — Shear ───────────────────────────────────────
    @staticmethod
    def shear(Vd: float, Av: float, fy: float) -> dict:
        """
        Check  : Vd ≤ Vr
        Vr     = Av·fy / (√3·gamma_m)
        DCR    = Vd / Vr
        """
        gamma_m = DesignChecks.GAMMA_M
        Vr  = (Av * fy) / (math.sqrt(3) * gamma_m)
        DCR = Vd / Vr if Vr > 0 else float("inf")
        return {
            "equation": (
                f"Vr = Av·fy/(√3·γm)\n"
                f"   = {Av:.0f}×{fy}/{math.sqrt(3):.3f}×{gamma_m}\n"
                f"   = {Vr/1e3:.2f} kN\n"
                f"Vd = {Vd/1e3:.2f} kN\n"
                f"DCR = Vd/Vr = {DCR:.3f}"
            ),
            "Vr": Vr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 3. Interaction (Bending + Shear) ──────────────────────────────────────
    @staticmethod
    def interaction(Md: float, Mr: float, Vd: float, Vr: float) -> dict:
        """
        Check  : Md/Mr + Vd/Vr ≤ 1
        DCR    = Md/Mr + Vd/Vr
        """
        m_ratio = Md / Mr if Mr > 0 else float("inf")
        v_ratio = Vd / Vr if Vr > 0 else float("inf")
        DCR     = m_ratio + v_ratio
        return {
            "equation": (
                f"Md/Mr + Vd/Vr ≤ 1\n"
                f"= {m_ratio:.3f} + {v_ratio:.3f}\n"
                f"DCR = {DCR:.3f}"
            ),
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 4. Lateral Torsional Buckling ─────────────────────────────────────────
    @staticmethod
    def ltb(Md: float, E: float, Iy: float, L_LTB: float) -> dict:
        """
        Check      : Md ≤ Mcr
        Mcr (simp) = π²·E·Iy / L_LTB²
        DCR        = Md / Mcr
        """
        Mcr = (math.pi ** 2 * E * Iy) / (L_LTB ** 2) if L_LTB > 0 else float("inf")
        DCR = Md / Mcr if Mcr > 0 else float("inf")
        return {
            "equation": (
                f"Mcr = π²·E·Iy/L²\n"
                f"    = π²×{E/1e3:.0f}×10³×{Iy/1e6:.2f}×10⁶/{L_LTB:.0f}²\n"
                f"    = {Mcr/1e6:.2f} kN·m\n"
                f"Md  = {Md/1e6:.2f} kN·m\n"
                f"DCR = Md/Mcr = {DCR:.3f}"
            ),
            "Mcr": Mcr, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 5. Resistance to Longitudinal and Transverse Shear ────────────────────
    @staticmethod
    def shear_long_trans(
        Vd: float, rho: float, fck: float, b: float, d: float,
        Asv: float, fy: float, s: float
    ) -> dict:
        """
        Vrd   = Vrd_c + Vrd_s
        Vrd_c = 0.18·k·(100·ρ·fck)^(1/3)·b·d
        Vrd_s = Asv·fy·d / s
        DCR   = Vd / Vrd
        """
        k     = min(2.0, 1 + math.sqrt(200 / d)) if d > 0 else 2.0
        Vrd_c = 0.18 * k * (100 * rho * fck) ** (1 / 3) * b * d
        Vrd_s = (Asv * fy * d) / s if s > 0 else 0.0
        Vrd   = Vrd_c + Vrd_s
        DCR   = Vd / Vrd if Vrd > 0 else float("inf")
        return {
            "equation": (
                f"Vrd = Vrd,c + Vrd,s\n"
                f"Vrd,c = {Vrd_c/1e3:.2f} kN\n"
                f"Vrd,s = {Vrd_s/1e3:.2f} kN\n"
                f"Vrd   = {Vrd/1e3:.2f} kN\n"
                f"DCR = Vd/Vrd = {DCR:.3f}"
            ),
            "Vrd": Vrd, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 6. Fatigue Check ──────────────────────────────────────────────────────
    @staticmethod
    def fatigue(delta_sigma: float, delta_sigma_C: float) -> dict:
        """
        Check            : Δσ ≤ Δσ_allowable
        Δσ_allowable     = Δσ_C / gamma_mf
        DCR              = Δσ / Δσ_allowable
        """
        gamma_mf         = DesignChecks.GAMMA_MF
        delta_sigma_all  = delta_sigma_C / gamma_mf
        DCR              = delta_sigma / delta_sigma_all if delta_sigma_all > 0 else float("inf")
        return {
            "equation": (
                f"Δσ_allow = ΔσC/γmf\n"
                f"         = {delta_sigma_C}/{gamma_mf}\n"
                f"         = {delta_sigma_all:.2f} MPa\n"
                f"Δσ       = {delta_sigma:.2f} MPa\n"
                f"DCR = Δσ/Δσ_allow = {DCR:.3f}"
            ),
            "delta_sigma_allowable": delta_sigma_all,
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 7. Stress Limitation ──────────────────────────────────────────────────
    @staticmethod
    def stress(Md: float, Ze: float, fy: float) -> dict:
        """
        σ    = Md / Ze
        σ ≤ fy / gamma_m
        DCR  = σ / (fy/gamma_m)
        """
        gamma_m     = DesignChecks.GAMMA_M
        sigma       = Md / Ze if Ze > 0 else float("inf")
        sigma_limit = fy / gamma_m
        DCR         = sigma / sigma_limit if sigma_limit > 0 else float("inf")
        return {
            "equation": (
                f"σ = Md/Ze\n"
                f"  = {Md/1e6:.2f}×10⁶/{Ze/1e3:.1f}×10³\n"
                f"  = {sigma:.2f} MPa\n"
                f"Limit = fy/γm = {sigma_limit:.2f} MPa\n"
                f"DCR = σ/(fy/γm) = {DCR:.3f}"
            ),
            "sigma": sigma, "sigma_limit": sigma_limit,
            "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── 8. Deflection and Crack Control ───────────────────────────────────────
    @staticmethod
    def deflection(delta: float, L: float, x: float = 600.0) -> dict:
        """
        δ ≤ L/x   (default x = 600)
        DCR = δ / (L/x)
        """
        limit = L / x if x > 0 else float("inf")
        DCR   = delta / limit if limit > 0 else float("inf")
        return {
            "equation": (
                f"δ ≤ L/x  (x = {x:.0f})\n"
                f"Limit = {L:.0f}/{x:.0f} = {limit:.2f} mm\n"
                f"δ     = {delta:.2f} mm\n"
                f"DCR = δ/(L/x) = {DCR:.3f}"
            ),
            "limit": limit, "DCR": DCR, "pass": DCR <= 1.0,
        }

    # ── Convenience: run all checks from a data dict ──────────────────────────
    @classmethod
    def run_all(cls, data: dict) -> dict:
        """
        Run all 8 checks and return a dict keyed by check name.
        `data` must contain the keys listed in _default_data().
        """
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
    def _default_data() -> dict:
        """
        Realistic placeholder values for a typical highway steel-girder bridge.
        Replace with values pulled from the actual model/cad_state.
        Units: N, mm, MPa.
        """
        return {
            "Md":            500e6,    # N·mm   factored bending moment demand
            "Zp":           3000e3,    # mm³    plastic section modulus
            "Ze":           2700e3,    # mm³    elastic section modulus
            "fy":              250,    # MPa    yield strength (E 250)
            "beta_b":          1.0,    # –      bending factor
            "Vd":           300e3,     # N      factored shear demand
            "Av":            4800,     # mm²    shear area (d_w × t_w)
            "E":            2.0e5,     # MPa    Young's modulus
            "Iy":           1.5e8,     # mm⁴    minor-axis second moment of area
            "L_LTB":         3500,     # mm     unbraced length between bracings
            "rho":           0.012,    # –      longitudinal reinforcement ratio
            "fck":              35,    # MPa    characteristic concrete strength
            "b":               300,    # mm     section width
            "d":               600,    # mm     effective depth
            "Asv":             402,    # mm²    stirrup area (2-legged 16 mm φ)
            "s":               150,    # mm     stirrup spacing
            "delta_sigma":      80,    # MPa    fatigue stress range
            "delta_sigma_C":   100,    # MPa    fatigue strength (detail category)
            "delta":            12,    # mm     mid-span deflection
            "L":             20000,    # mm     span length (matches UI default 20 m)
            "defl_x":          600,    # –      deflection limit divisor
        }


# ── UI ────────────────────────────────────────────────────────────────────────

class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        # Must init dict BEFORE super().__init__ because _build_check_card
        # is called inside _build_checks_grid which is called from __init__
        self.check_outputs = {}   # key → QTextEdit

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

        # Populate cards with default placeholder values on startup
        self._populate_defaults()

    # ── Default population ────────────────────────────────────────────────────

    def _populate_defaults(self):
        """Show equations + placeholder DCR values so cards are never empty."""
        data    = DesignChecks._default_data()
        results = DesignChecks.run_all(data)
        for key, result in results.items():
            self._display_result(key, result)

    # ── Display helper ────────────────────────────────────────────────────────

    def _display_result(self, key: str, result: dict):
        """
        Write the formatted equation + DCR into the card's QTextEdit.
        Colors the DCR line green (pass) or red (fail).
        """
        if key not in self.check_outputs:
            return

        output = self.check_outputs[key]
        eq_text = result.get("equation", "")
        dcr     = result.get("DCR", None)
        passed  = result.get("pass", True)

        # Build HTML so the DCR line can be coloured
        lines_html = []
        for line in eq_text.splitlines():
            if line.startswith("DCR"):
                color  = "#2e7d32" if passed else "#c62828"
                status = "  ✓ OK" if passed else "  ✗ FAIL"
                lines_html.append(
                    f'<span style="color:{color}; font-weight:bold;">'
                    f'{line}{status}</span>'
                )
            else:
                lines_html.append(
                    f'<span style="color:#333333;">{line}</span>'
                )

        html = "<br>".join(lines_html)
        output.setHtml(
            f'<div style="font-family: Courier New, monospace; font-size: 10px;">'
            f'{html}</div>'
        )

    # ── Helpers (same style as the rest of the dialog) ────────────────────────

    def _row_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; color: #000;")
        lbl.setMinimumWidth(180)
        return lbl

    def _readonly_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedWidth(150)
        field.setFixedHeight(22)
        field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    # ── Top bar ───────────────────────────────────────────────────────────────

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

    # ── Check cards grid ──────────────────────────────────────────────────────

    def _build_checks_grid(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for idx, (key, title) in enumerate(DESIGN_CHECKS):
            col  = idx % 2
            row  = idx // 2
            card = self._build_check_card(key, title)
            grid.addWidget(card, row, col)

        return grid

    def _build_check_card(self, key: str, title: str) -> QFrame:
        """
        Single check card — rounded border, bold title, monospace output area.
        Height is taller than original (90 px) so the equation lines fit.
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
        card_layout.setSpacing(6)

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

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E0E0E0; background-color: #E0E0E0; border: none;")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        # Readonly output — taller than original so all equation lines show
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFixedHeight(92)
        output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #333;
            }
        """)
        card_layout.addWidget(output)

        self.check_outputs[key] = output
        return card

    # ── Public API ────────────────────────────────────────────────────────────

    def set_girder_count(self, count: int):
        """Update Member ID combo when girder count changes."""
        self.member_combo.clear()
        self.member_combo.addItems(["All"] + [f"Girder {i}" for i in range(1, count + 1)])

    def load_data(self, cad_state: dict):
        """
        Called by SteelDesign dialog when cad_state is available.
        Pulls section/material properties from cad_state, runs all checks,
        and populates the cards.  Falls back to defaults for any missing key.
        """
        if not cad_state:
            return

        # Update girder count if available
        try:
            self.set_girder_count(int(cad_state.get("no_of_girders", 2)))
        except (ValueError, TypeError):
            pass

        # Build data dict — merge defaults with whatever cad_state provides
        data = DesignChecks._default_data()
        key_map = {
            # cad_state key       : data key
            "Md":                   "Md",
            "Vd":                   "Vd",
            "fy":                   "fy",
            "Zp":                   "Zp",
            "Ze":                   "Ze",
            "Av":                   "Av",
            "E_modulus":            "E",
            "Iy":                   "Iy",
            "L_LTB":                "L_LTB",
            "rho":                  "rho",
            "fck":                  "fck",
            "b":                    "b",
            "d":                    "d",
            "Asv":                  "Asv",
            "s":                    "s",
            "delta_sigma":          "delta_sigma",
            "delta_sigma_C":        "delta_sigma_C",
            "deflection":           "delta",
            "span":                 "L",
        }
        for src_key, dst_key in key_map.items():
            val = cad_state.get(src_key)
            if val is not None:
                try:
                    data[dst_key] = float(val)
                except (ValueError, TypeError):
                    pass

        # Also accept pre-computed check results stored in cad_state
        # (e.g. from the analysis engine) — these take priority
        has_precomputed = any(
            cad_state.get(f"check_{k}") for k in self.check_outputs
        )
        if has_precomputed:
            for key in self.check_outputs:
                result_text = cad_state.get(f"check_{key}", "")
                if result_text:
                    self.check_outputs[key].setPlainText(str(result_text))
            return

        # Run calculations and populate cards
        results = DesignChecks.run_all(data)
        for key, result in results.items():
            self._display_result(key, result)

    def set_check_result(self, key: str, text: str):
        """Directly set plain-text result for a specific check card."""
        if key in self.check_outputs:
            self.check_outputs[key].setPlainText(text)

    def set_check_result_from_dict(self, key: str, result: dict):
        """Set result from a DesignChecks result dict (shows coloured DCR)."""
        self._display_result(key, result)

    def clear_results(self):
        """Clear all check output areas."""
        for output in self.check_outputs.values():
            output.clear()