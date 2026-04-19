"""Design check calculation engine — pure Python, zero UI imports.

Each static method takes a ``params`` dict that **must** contain the keys
documented in the corresponding docstring.  Every method returns a common
result dict::

    {
        "equation_str": str,   # human-readable equation with computed values
        "Md": float | None,    # moment demand  (where applicable)
        "Mr": float | None,    # moment resistance  (where applicable)
        "DCR": float,          # demand-capacity ratio
        "status": "OK" | "FAIL",
    }
"""

from __future__ import annotations

import math
from typing import Dict, Any


def _status(dcr: float) -> str:
    return "OK" if dcr <= 1.0 else "FAIL"


class DesignCheckEngine:
    """Collection of IS-800/EN-1994 style design-check calculations."""

    # ── a) Flexure ────────────────────────────────────────────────────────────

    @staticmethod
    def check_flexure(p: Dict[str, Any]) -> Dict[str, Any]:
        """Strength Limit State (Flexure).

        Required keys: beta_b, Zp, fy, gamma_m, Md
        """
        Mr = p["beta_b"] * p["Zp"] * p["fy"] / p["gamma_m"]
        DCR = p["Md"] / Mr
        equation_str = (
            f"Mr = \u03b2_b\u00b7Zp\u00b7fy/\u03b3m = {Mr:.2f} kNm "
            f"| Md = {p['Md']:.2f} kNm "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": p["Md"],
            "Mr": Mr,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── b) Shear ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_shear(p: Dict[str, Any]) -> Dict[str, Any]:
        """Strength Limit State (Shear).

        Required keys: Av, fy, gamma_m, Vd
        """
        Vr = p["Av"] * p["fy"] / (math.sqrt(3) * p["gamma_m"])
        DCR = p["Vd"] / Vr
        equation_str = (
            f"Vr = Av\u00b7fy/(\u221a3\u00b7\u03b3m) = {Vr:.2f} kN "
            f"| Vd = {p['Vd']:.2f} kN "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": None,
            "Mr": None,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── c) Interaction ────────────────────────────────────────────────────────

    @staticmethod
    def check_interaction(p: Dict[str, Any]) -> Dict[str, Any]:
        """Interaction check (combined flexure + shear).

        Required keys: Md, Mr, Vd, Vr
        """
        DCR = p["Md"] / p["Mr"] + p["Vd"] / p["Vr"]
        equation_str = f"Md/Mr + Vd/Vr = {DCR:.3f} \u2264 1"
        return {
            "equation_str": equation_str,
            "Md": p["Md"],
            "Mr": p["Mr"],
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── d) Lateral Torsional Buckling ─────────────────────────────────────────

    @staticmethod
    def check_ltb(p: Dict[str, Any]) -> Dict[str, Any]:
        """Lateral Torsional Buckling.

        Required keys: E, Iy, L_LTB, Md
        """
        Mcr = (math.pi ** 2 * p["E"] * p["Iy"]) / (p["L_LTB"] ** 2)
        DCR = p["Md"] / Mcr
        equation_str = (
            f"Mcr = \u03c0\u00b2EIy/L\u00b2 = {Mcr:.2f} kNm "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": p["Md"],
            "Mr": Mcr,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── e) Longitudinal and Transverse Shear ──────────────────────────────────

    @staticmethod
    def check_shear_long_trans(p: Dict[str, Any]) -> Dict[str, Any]:
        """Resistance to Longitudinal and Transverse Shear.

        Required keys: k, rho, fck, b, d, Asv, fy, s, Vd
        """
        Vrd_c = (
            0.18 * p["k"]
            * (100 * p["rho"] * p["fck"]) ** (1 / 3)
            * p["b"]
            * p["d"]
        )
        Vrd_s = p["Asv"] * p["fy"] * p["d"] / p["s"]
        Vrd = Vrd_c + Vrd_s
        DCR = p["Vd"] / Vrd
        equation_str = (
            f"Vrd = Vrd,c + Vrd,s = {Vrd:.2f} kN "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": None,
            "Mr": None,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── f) Fatigue ────────────────────────────────────────────────────────────

    @staticmethod
    def check_fatigue(p: Dict[str, Any]) -> Dict[str, Any]:
        """Resistance to Fatigue.

        Required keys: delta_sigma_C, gamma_mf, delta_sigma
        """
        delta_sigma_allowable = p["delta_sigma_C"] / p["gamma_mf"]
        DCR = p["delta_sigma"] / delta_sigma_allowable
        equation_str = (
            f"\u0394\u03c3_allow = \u0394\u03c3C/\u03b3mf = "
            f"{delta_sigma_allowable:.2f} MPa "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": None,
            "Mr": None,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── g) Stress Limitation ──────────────────────────────────────────────────

    @staticmethod
    def check_stress(p: Dict[str, Any]) -> Dict[str, Any]:
        """Stress Limitation.

        Required keys: Md, Ze, fy, gamma_m
        """
        sigma = p["Md"] / p["Ze"]
        limit = p["fy"] / p["gamma_m"]
        DCR = sigma / limit
        equation_str = (
            f"\u03c3 = Md/Ze = {sigma:.2f} MPa "
            f"| Limit = fy/\u03b3m = {limit:.2f} MPa "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": p["Md"],
            "Mr": None,
            "DCR": DCR,
            "status": _status(DCR),
        }

    # ── h) Deflection and Crack Control ───────────────────────────────────────

    @staticmethod
    def check_deflection(p: Dict[str, Any]) -> Dict[str, Any]:
        """Deflection and Crack Control.

        Required keys: L, delta
        Optional keys: x  (span-to-deflection ratio divisor, default 600)
        """
        x = p.get("x", 600)
        limit = p["L"] / x
        DCR = p["delta"] / limit
        equation_str = (
            f"\u03b4 \u2264 L/{x} = {limit:.4f} m "
            f"| \u03b4 = {p['delta']:.4f} m "
            f"| DCR = {DCR:.3f}"
        )
        return {
            "equation_str": equation_str,
            "Md": None,
            "Mr": None,
            "DCR": DCR,
            "status": _status(DCR),
        }
