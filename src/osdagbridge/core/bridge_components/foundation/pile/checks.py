"""
Detailing checks for piles and pile caps (geometry / reinforcement rules).

References
----------
IS 2911 (Part 1/Sec 2):2010  Bored cast in-situ concrete piles
IRC 78:2014                   Foundations and Substructure
IS 456:2000                   Plain and Reinforced Concrete
"""

import math

from osdagbridge.core.bridge_components.sub_structure.pier.checks import check

PILE_MIN_COVER = 50.0          # IS 2911-1-2 (piles in contact with soil)
PILE_MIN_STEEL = 0.4           # % of gross section, IS 2911-1-2
PILE_SPACING_FACTOR = 3.0      # x D, friction piles, IS 2911-1-2 / IRC 78
CAP_EDGE_CLEARANCE = 150.0     # cap beyond outer pile face, IS 2911-1-2 / IRC 78
PILE_MIN_EMBEDMENT = 50.0      # pile head into cap, IS 2911-1-2


def pile_checks(layouts, params):
    """Checks on the pile group of one pile cap (all piles identical)."""
    rb = params.rebar
    lay = layouts[0]
    D = params.pile_diameter
    n = lay["n_main"]
    rho = 100.0 * n * rb.main_dia ** 2 / D ** 2
    sx = params.pile_spacing
    sy = params.pile_spacing if params.pile_spacing_y is None else params.pile_spacing_y
    s_min = min(sx if params.n_piles_x > 1 else math.inf, sy if params.n_piles_y > 1 else math.inf)
    req_s = PILE_SPACING_FACTOR * D
    return [
        check("Pile", "Number of longitudinal bars", "IS 2911-1-2", ">= 6", n, n >= 6),
        check("Pile", "Longitudinal steel", "IS 2911-1-2 (>= 0.4 %)",
              f">= {PILE_MIN_STEEL:.1f} %", f"{rho:.2f} %", rho >= PILE_MIN_STEEL),
        check("Pile", "Clear cover", "IS 2911-1-2 (>= 50 mm)",
              f">= {PILE_MIN_COVER:.0f} mm", f"{rb.cover:.0f} mm", rb.cover >= PILE_MIN_COVER,
              "" if rb.cover >= PILE_MIN_COVER else "set RebarParams(cover=50) for piles in soil"),
        check("Pile", "Tie diameter / spacing", "IS 2911-1-2 (>= 6 mm, <= 300 mm)",
              ">= 6 mm @ <= 300 mm", f"{rb.tie_dia:.0f} mm @ {rb.tie_spacing:.0f} mm",
              rb.tie_dia >= 6 and rb.tie_spacing <= 300),
        check("Pile group", "Pile spacing", "IS 2911-1-2; IRC 78 (>= 3 D, friction piles)",
              f">= {req_s:.0f} mm", f"{s_min:.0f} mm", s_min >= req_s,
              "" if s_min >= req_s else f"task default; set pile_spacing >= {req_s:.0f} mm"),
        check("Pile group", "Pile head embedment in cap", "IS 2911-1-2 (>= 50 mm)",
              f">= {PILE_MIN_EMBEDMENT:.0f} mm", f"{params.pile_embedment:.0f} mm",
              params.pile_embedment >= PILE_MIN_EMBEDMENT),
    ]


def pile_cap_checks(layout, params):
    """Checks on one pile cap."""
    rb = params.rebar
    D = params.pile_diameter
    sy = params.pile_spacing if params.pile_spacing_y is None else params.pile_spacing_y
    edge_x = params.pile_cap_width / 2.0 - (params.n_piles_x - 1) * params.pile_spacing / 2.0 - D / 2.0
    edge_y = params.pile_cap_length / 2.0 - (params.n_piles_y - 1) * sy / 2.0 - D / 2.0
    edge = min(edge_x, edge_y)
    out = [
        check("Pile cap", "Edge clearance beyond outer pile face", "IS 2911-1-2; IRC 78 (>= 150 mm)",
              f">= {CAP_EDGE_CLEARANCE:.0f} mm", f"{edge:.0f} mm", edge >= CAP_EDGE_CLEARANCE,
              "" if edge >= CAP_EDGE_CLEARANCE else
              f"increase pile_cap_width to >= {params.pile_cap_width + 2 * (CAP_EDGE_CLEARANCE - edge_x):.0f} mm"
              if edge_x < CAP_EDGE_CLEARANCE else ""),
        check("Pile cap", "Bottom-steel spacing", "IS 456 cl. 26.3.3 (<= 3 d, 300 mm)",
              "<= 300 mm", f"{rb.main_spacing:.0f} mm", rb.main_spacing <= 300),
    ]
    As = math.pi * rb.main_dia ** 2 / 4.0 * 1000.0 / rb.main_spacing
    As_min = 0.0012 * 1000.0 * params.pile_cap_depth      # 0.12 % for HYSD, per metre
    out.append(check("Pile cap", "Minimum bottom steel (per m)", "IS 456 cl. 26.5.2.1 (0.12 %)",
                     f">= {As_min:.0f} mm2/m", f"{As:.0f} mm2/m", As >= As_min))
    return out
