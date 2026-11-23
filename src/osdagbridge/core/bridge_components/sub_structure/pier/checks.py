"""
Detailing checks for the pier and the pier cap.

These are geometric / detailing checks on the modelled reinforcement (not a
strength design): they confirm that the parametric model obeys the code
detailing rules, and report a WARN with the governing clause when a
user-supplied (or task-default) value falls outside them.

References
----------
IS 456:2000          Plain and Reinforced Concrete (clauses quoted)
IRC 112:2020         Code of Practice for Concrete Road Bridges
EN 1992-1-1:2004     (basis of IRC 112) cl. 9.5.2 column minimum steel
"""

import math

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    development_length, BEND_ANCHORAGE_FACTOR,
)

MIN_COVER_MODERATE = 40.0      # IRC 112, moderate exposure


def check(component, name, reference, required, provided, ok, note=""):
    """One check record (status PASS / WARN)."""
    return {"component": component, "check": name, "reference": reference,
            "required": required, "provided": provided,
            "status": "PASS" if ok else "WARN", "note": note}


def _main_bars(layout):
    return [b for b in layout["bars"] if b["role"] == "MAIN"]


def pier_checks(layout, params, fck):
    """Checks on one pier layout."""
    rb = params.rebar
    c = layout["concrete"]
    D = 2 * c["radius"]
    out = []
    n = layout["n_main"]
    As = n * math.pi * rb.main_dia ** 2 / 4.0
    Ac = math.pi * D ** 2 / 4.0
    rho = 100.0 * As / Ac
    out.append(check("Pier", "Number of longitudinal bars (circular)", "IS 456 cl. 26.5.3.1(b)",
                     ">= 6", n, n >= 6))
    out.append(check("Pier", "Longitudinal steel ratio", "IRC 112 / EN 1992-1-1 cl. 9.5.2 (0.2 % to 4 %)",
                     "0.20 % - 4.0 %", f"{rho:.2f} %", 0.2 <= rho <= 4.0))
    out.append(check("Pier", "Clear cover", "IRC 112 (moderate exposure)",
                     f">= {MIN_COVER_MODERATE:.0f} mm", f"{rb.cover:.0f} mm", rb.cover >= MIN_COVER_MODERATE))
    out.append(check("Pier", "Tie diameter", "IS 456 cl. 26.5.3.2(c) (>= max(6, d/4))",
                     f">= {max(6.0, rb.main_dia / 4):.0f} mm", f"{rb.tie_dia:.0f} mm",
                     rb.tie_dia >= max(6.0, rb.main_dia / 4)))
    s_max = min(16 * rb.main_dia, D, 300.0)
    out.append(check("Pier", "Tie pitch", "IS 456 cl. 26.5.3.2(c) (<= min(16 d, D, 300))",
                     f"<= {s_max:.0f} mm", f"{rb.tie_spacing:.0f} mm", rb.tie_spacing <= s_max))
    le_D = 2.0 * params.pier_height / D          # cantilever pier: le = 2 L
    out.append(check("Pier", "Slenderness le/D (short column)", "IS 456 cl. 25.1.2 (le = 2 L, cantilever)",
                     "< 12", f"{le_D:.1f}", le_D < 12))

    # Anchorage of starter bars into the pile cap: straight length + 90 deg bend
    ld = development_length(rb.main_dia, fck)
    bar = _main_bars(layout)[0]
    z_pcap_top = c["base"][2]
    straight = z_pcap_top - min(p[2] for p in bar["path"])
    has_bend = len(bar["path"]) > 2
    provided = straight + (BEND_ANCHORAGE_FACTOR * rb.main_dia if has_bend else 0.0)
    out.append(check("Pier", "Starter-bar anchorage in pile cap", "IS 456 cl. 26.2.1, 26.2.2.1(b)",
                     f">= Ld = {ld:.0f} mm", f"{provided:.0f} mm", provided >= ld,
                     "straight embedment + 8 d for the 90 deg bend (conservative)"
                     + ("" if provided >= ld else
                        f"; deepen pile cap by {ld - provided:.0f} mm or use a higher concrete grade")))
    return out


def pier_cap_checks(layout, params, fck):
    """Checks on the pier cap layout."""
    rb = params.rebar
    c = layout["concrete"]
    out = []
    d_eff = c["depth"] - rb.cover - rb.tie_dia - rb.main_dia / 2.0
    top = [b for b in _main_bars(layout) if b["path"][1][2] > c["z_top"] - c["depth"] / 2]
    As_top = len(top) * math.pi * rb.main_dia ** 2 / 4.0
    As_min = 0.85 * c["top_width"] * d_eff / 500.0
    out.append(check("Pier cap", "Minimum tension steel (top, over pier)", "IS 456 cl. 26.5.1.1 (0.85 b d / fy)",
                     f">= {As_min:.0f} mm2", f"{As_top:.0f} mm2", As_top >= As_min))
    s_max = min(0.75 * d_eff, 300.0)
    out.append(check("Pier cap", "Stirrup spacing", "IS 456 cl. 26.5.1.5 (<= 0.75 d, 300)",
                     f"<= {s_max:.0f} mm", f"{rb.tie_spacing:.0f} mm", rb.tie_spacing <= s_max))
    out.append(check("Pier cap", "Side-face reinforcement", "IS 456 cl. 26.5.1.3 (needed if D > 750 mm)",
                     "D <= 750 mm or side bars", f"D = {c['depth']:.0f} mm", c["depth"] <= 750))
    if c.get("style") == "HAMMERHEAD":
        out.append(check("Pier cap", "Cantilever tip depth", "Design practice (tip depth >= 0.5 D)",
                         f">= {0.5 * c['depth']:.0f} mm", f"{c['end_depth']:.0f} mm",
                         c["end_depth"] >= 0.5 * c["depth"] - 1e-6))
    return out
