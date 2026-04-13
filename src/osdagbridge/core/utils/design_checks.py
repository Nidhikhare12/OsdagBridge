"""IS 800:2007 / IRC design check calculations for plate girder bridges.

Units: Mu (kN·m), Vu (kN), fy/fyw (MPa), Ze/Zp (cm³), hw/tw/span (mm).
"""

import math

_GM0 = 1.10  # IS 800 Cl. 5.4.1


def _get(d):
    # Map UI geometry to structural parameters for DCR demo
    mod = float(d.get("_dynamic_modifier", 1.0))
    
   
    span_m = float(d.get("Span", d.get("bridge_span", 20.0)))
    span = span_m * 1000.0

    Ze = float(d.get("Ze", 1200))
    if "Girder Depth" in d:
        Ze = Ze * (hw / 1200.0) ** 2
    
    Zp = float(d.get("Zp", Ze * 1.15))

    Mu = float(d.get("Mu", 850)) * (span_m / 20.0)**2 * mod
    Vu = float(d.get("Vu", 350)) * (span_m / 20.0) * mod
    
    fy  = float(d.get("fy", 250))
    fyw = float(d.get("fyw", 250))
    
    return (Mu, Vu, fy, fyw, Ze, Zp, hw, tw, span)


def _check(demand, capacity):
    if capacity == 0:
        return 9.999, False
    r = demand / capacity
    return r, r <= 1.0


def check_flexure(bd):
    Mu, _, fy, _, _, Zp, _, _, _ = _get(bd)
    beta_b = 1.0
    Mr = (beta_b * Zp * 1000) * fy / (_GM0 * 1e6)
    r, ok = _check(Mu, Mr)
    return {
        "name": "Strength — Flexure",
        "equation": "Mr = βb·Zp·fy / γm0  |  Mu/Mr ≤ 1.0",
        "demand": round(Mu, 3),
        "capacity": round(Mr, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_shear(bd):
    _, Vu, _, fyw, _, _, hw, tw, _ = _get(bd)
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
    val = (f["demand"] / f["capacity"]) + (s["demand"] / s["capacity"])
    return {
        "name": "Interaction: M + V",
        "equation": "Mu/Md + Vu/Vd ≤ 1.0",
        "demand": round(val, 4),
        "capacity": 1.0,
        "ratio": round(val, 4),
        "passed": val <= 1.0,
    }


def check_ltb(bd):
    Mu, _, fy, _, Ze, _, hw, _, span = _get(bd)
    E = 200_000.0
    # Approximate Iy for I-section: I ≈ Ze * (h/2)
    Iy = Ze * 1000 * hw / 2
    Lb = span / 6.0
    Mcr = (math.pi ** 2 * E * Iy) / (Lb ** 2 * 1e6)
    r, ok = _check(Mu, Mcr)
    return {
        "name": "Lateral Torsional Buckling",
        "equation": "Mcr = π²EIy/(LLTB)²",
        "demand": round(Mu, 3),
        "capacity": round(Mcr, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def check_shear_long_trans(bd):
    _, Vu, fy, _, _, _, hw, tw, _ = _get(bd)

    fck = 30.0    
    rho = 0.012   
    b   = tw * 1.5 
    d   = hw      
    Asv = 314.0   
    s   = 200.0   

    # Vrd,c = 0.18 * k * (100 * rho * fck)^(1/3) * b * d
    k = min(2.0, 1 + math.sqrt(200.0 / max(d, 1.0)))
    Vrd_c = (0.18 * k * (100 * rho * fck) ** (1/3) * b * d) / 1000.0
    
    # Vrd,s = (Asv * fy * d) / s
    Vrd_s = (Asv * fy * d) / (s * 1000.0)
    
    Vrd = Vrd_c + Vrd_s
    r, ok = _check(Vu, Vrd)

    return {
        "name": "Shear — Long. & Trans.",
        "equation": "Vrd = Vrd,c + Vrd,s",
        "demand": round(Vu, 3),
        "capacity": round(Vrd, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }

def check_fatigue(bd):
    Mu, _, _, _, Ze, _, _, _, _ = _get(bd)

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
    Mu, _, fy, _, Ze, _, _, _, _ = _get(bd)
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
    Mu, _, _, _, Ze, _, hw, _, span = _get(bd)
    # I_approx = Ze × (hw/2); δ ≈ (5/48) × ML²/EI
    I = (Ze * 1000) * (hw / 2)
    delta = (5 / 48) * (Mu * 1e6 * span ** 2) / (200_000 * I)
    limit = span / 600
    r, ok = _check(delta, limit)
    return {
        "name": "Deflection (Live Load)",
        "equation": "δ_LL ≤ L/600  (IRC:24-2010 Cl. 304)",
        "demand": round(delta, 3),
        "capacity": round(limit, 3),
        "ratio": round(r, 4),
        "passed": ok,
    }


def run_all_checks(bd):
    results = []
    for check_func in ALL_CHECKS:
        try:
            results.append(check_func(bd))
        except Exception as e:
            # Maintain list length and provide error feedback
            results.append({
                "name": "Check Error",
                "passed": False,
                "demand": 0.0,
                "capacity": 0.0,
                "ratio": 0.0,
                "equation": f"Error: {str(e)}"
            })
    return results


ALL_CHECKS = [
    check_flexure,
    check_shear,
    check_interaction,
    check_ltb,
    check_shear_long_trans,
    check_fatigue,
    check_stress_limitation,
    check_deflection,
]
