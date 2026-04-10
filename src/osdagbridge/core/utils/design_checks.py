"""IS 800:2007 / IRC design check calculations for plate girder bridges.

Units: Mu (kN·m), Vu (kN), fy/fyw (MPa), Ze (cm³), hw/tw/span (mm).
"""

import math

_GM0 = 1.10  # IS 800 Cl. 5.4.1


def _get(d):
    return (
        float(d.get("Mu",   850)),
        float(d.get("Vu",   350)),
        float(d.get("fy",   250)),
        float(d.get("fyw",  250)),
        float(d.get("Ze",  1200)),
        float(d.get("hw",  1200)),
        float(d.get("tw",    12)),
        float(d.get("span", 20000)),
    )


def _check(demand, capacity):
    if capacity == 0:
        return 9.999, False
    r = demand / capacity
    return r, r <= 1.0


def check_flexure(bd):
    Mu, _, fy, _, Ze, _, _, _ = _get(bd)
    Md = (Ze * 1000) * fy / (_GM0 * 1e6)
    r, ok = _check(Mu, Md)
    return {
        "name": "Strength — Flexure",
        "equation": "Md = Ze·fy / γm0  |  Mu/Md ≤ 1.0",
        "demand": round(Mu, 3),
        "capacity": round(Md, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_shear(bd):
    _, Vu, _, fyw, _, hw, tw, _ = _get(bd)
    Vd = (hw * tw * fyw) / (math.sqrt(3) * _GM0 * 1e3)
    r, ok = _check(Vu, Vd)
    return {
        "name": "Strength — Shear",
        "equation": "Vd = hw·tw·fyw / (√3·γm0)  |  Vu/Vd ≤ 1.0",
        "demand": round(Vu, 3),
        "capacity": round(Vd, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_interaction(bd):
    f = check_flexure(bd)
    s = check_shear(bd)
    val = (f["demand"] / f["capacity"]) ** 2 + (s["demand"] / s["capacity"]) ** 2
    return {
        "name": "Interaction: M + V",
        "equation": "(Mu/Md)² + (Vu/Vd)² ≤ 1.0",
        "demand": round(val, 4),
        "capacity": 1.0,
        "ratio": round(val, 4),
        "passed": val <= 1.0,
    }


def check_ltb(bd):
    Mu, _, fy, _, Ze, _, _, span = _get(bd)
    Md = (Ze * 1000) * fy / (_GM0 * 1e6)

    E, ry = 200_000.0, 40.0
    Lb = span / 6.0
    Lp = 1.76 * ry * math.sqrt(E / fy)

    if Lb <= Lp:
        Mn, regime = Md, "Plastic"
    else:
        # Inelastic reduction; full formula needs rts/It/Iw not in bridge_data
        Mn, regime = 0.85 * Md, "Inelastic (simplified)"

    r, ok = _check(Mu, Mn)
    return {
        "name": "Lateral Torsional Buckling",
        "equation": "Lp = 1.76·ry·√(E/fy)  |  Mu/Mn ≤ 1.0",
        "demand": round(Mu, 3),
        "capacity": round(Mn, 3),
        "ratio": round(r, 4),
        "passed": ok,
        "regime": regime,
    }


def check_shear_connectors(bd):
    _, _, fy, _, _, hw, tw, span = _get(bd)

    # 20mm headed stud (IS 1786), fc' = 30 MPa deck concrete
    Asc, fc, Fu = 314.16, 30.0, 415.0
    Ec = 4500 * math.sqrt(fc)
    Qn = min(0.5 * Asc * math.sqrt(fc * Ec), 0.75 * Asc * Fu)
    Qr = 0.75 * Qn

    As = hw * tw
    Vh = min(0.85 * fc * 2e6, As * fy) / 2.0

    n = max(1, int((span / 2) / 300))
    r, ok = _check(Vh / 1000, n * Qr / 1000)
    return {
        "name": "Shear Connectors",
        "equation": "Qn = min(0.5·Asc·√(fc·Ec), 0.75·Asc·Fu)  |  Vh/ΣQr ≤ 1.0",
        "demand": round(Vh / 1000, 3),
        "capacity": round(n * Qr / 1000, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_fatigue(bd):
    Mu, _, _, _, Ze, _, _, _ = _get(bd)

    # Detail cat. 71 (welded web-flange), γMf = 1.15, NE = N0 = 2e6 cycles
    Ms = Mu / 1.5
    sigma_r = Ms * 1e6 / (Ze * 1000)
    delta_R = (71.0 / 1.15) * ((2e6 / 2e6) ** (1 / 3))

    r, ok = _check(sigma_r, delta_R)
    return {
        "name": "Fatigue",
        "equation": "σr = Ms·10⁶/(Ze·10³)  |  ΔσR = (ΔσC/γMf)·(N₀/NE)^(1/3)  |  σr ≤ ΔσR",
        "demand": round(sigma_r, 3),
        "capacity": round(delta_R, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_stress_limitation(bd):
    Mu, _, fy, _, Ze, _, _, _ = _get(bd)
    ft = (Mu / 1.5) * 1e6 / (Ze * 1000)
    limit = 0.55 * fy
    r, ok = _check(ft, limit)
    return {
        "name": "Stress Limitation (Service)",
        "equation": "ft = Ms·10⁶/(Ze·10³)  |  ft ≤ 0.55·fy  (IS 800 Cl. 7.1)",
        "demand": round(ft, 3),
        "capacity": round(limit, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_deflection(bd):
    Mu, _, _, _, Ze, hw, _, span = _get(bd)
    # I_approx = Ze × (hw/2); δ ≈ (5/48) × ML²/EI
    I = (Ze * 1000) * (hw / 2)
    delta = (5 / 48) * (Mu * 1e6 * span ** 2) / (200_000 * I)
    limit = span / 800
    r, ok = _check(delta, limit)
    return {
        "name": "Deflection (Live Load)",
        "equation": "δ_LL ≤ L/800  (IRC:24-2010 Cl. 304)",
        "demand": round(delta, 3),
        "capacity": round(limit, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


ALL_CHECKS = [
    check_flexure,
    check_shear,
    check_interaction,
    check_ltb,
    check_shear_connectors,
    check_fatigue,
    check_stress_limitation,
    check_deflection,
]


def run_all_checks(bridge_data):
    return [fn(bridge_data) for fn in ALL_CHECKS]
