"""Rebar for pier, pier cap, pile cap and piles. Bars are opaque steel cylinders
(straight bars) or torus hoops (circular ties), placed inside `rebar_cover`."""
import math
from osdagbridge.core.bridge_components.sub_structure.common import (Part, cylinder, ring, grid_positions, z_range, circle_points, STEEL_COLOR)


def _bar(name, shape, dia, length, mark):
    return Part(name, shape, "IfcReinforcingBar", "steel", STEEL_COLOR, 1.0,
                {"diameter": dia, "length": length, "type": mark})


def pier_rebar(p, y, tag):
    out = []
    d, t, c = p.rebar_main_diameter, p.rebar_transverse_diameter, p.rebar_cover
    ring_r = p.pier_diameter / 2 - c - t - d / 2
    n = max(6, int(2 * math.pi * ring_r // p.rebar_spacing_longitudinal))
    z0, z1 = p.pier_bot_z + c, p.pier_top_z - c
    for i, (x, yy) in enumerate(circle_points(p.pier_x, y, ring_r, n)):
        out.append(_bar(f"{tag}_Main_{i+1}", cylinder((x, yy, z0), (0, 0, 1), d / 2, z1 - z0), d, z1 - z0, "MAIN"))
    R = p.pier_diameter / 2 - c - t / 2
    for i, z in enumerate(z_range(z0, z1, p.rebar_spacing_transverse)):
        out.append(_bar(f"{tag}_Hoop_{i+1}", ring(p.pier_x, y, z, R, t / 2), t, 2 * math.pi * R, "LIGATURE"))
    return out


def pier_cap_rebar(p):
    out = []
    d, t, c = p.rebar_main_diameter, p.rebar_transverse_diameter, p.rebar_cover
    L = p.pier_cap_length - 2 * c
    y0 = -p.pier_cap_length / 2 + c
    for layer, z, w in (("Bot", p.cap_bot_z + c + t + d / 2, p.pier_cap_bottom_width),
                        ("Top", p.cap_top_z - c - t - d / 2, p.pier_cap_top_width)):
        half = w / 2 - c - t - d / 2
        for i, x in enumerate(grid_positions(half, p.rebar_spacing_longitudinal)):
            out.append(_bar(f"Cap_{layer}Long_{i+1}", cylinder((p.pier_x + x, y0, z), (0, 1, 0), d / 2, L), d, L, "MAIN"))
        zt = z - (d / 2 + t / 2) if layer == "Bot" else z + (d / 2 + t / 2)
        xl = w / 2 - c
        for i, y in enumerate(z_range(y0, y0 + L, p.rebar_spacing_transverse)):
            out.append(_bar(f"Cap_{layer}Tran_{i+1}",
                            cylinder((p.pier_x - xl, y, zt), (1, 0, 0), t / 2, 2 * xl), t, 2 * xl, "LIGATURE"))
    return out


def pile_cap_rebar(p, y, tag):
    out = []
    d, t, c = p.rebar_main_diameter, p.rebar_transverse_diameter, p.rebar_cover
    lx, ly = p.pile_cap_length - 2 * c, p.pile_cap_width - 2 * c
    x0, y0 = p.pier_x - lx / 2, y - ly / 2
    for layer, zl, zt in (("Bot", p.pilecap_bot_z + c + d / 2, p.pilecap_bot_z + c + d + t / 2),
                          ("Top", p.pilecap_top_z - c - d / 2, p.pilecap_top_z - c - d - t / 2)):
        for i, yy in enumerate(grid_positions(ly / 2 - d / 2, p.rebar_spacing_longitudinal)):
            out.append(_bar(f"{tag}_{layer}X_{i+1}", cylinder((x0, y + yy, zl), (1, 0, 0), d / 2, lx), d, lx, "MAIN"))
        for i, xx in enumerate(grid_positions(lx / 2 - t / 2, p.rebar_spacing_transverse)):
            out.append(_bar(f"{tag}_{layer}Y_{i+1}", cylinder((p.pier_x + xx, y0, zt), (0, 1, 0), t / 2, ly), t, ly, "LIGATURE"))
    return out


def pile_rebar(p, px, py, tag):
    out = []
    d, t, c = p.rebar_main_diameter, p.rebar_transverse_diameter, p.rebar_cover
    ring_r = p.pile_diameter / 2 - c - t - d / 2
    z0 = p.pile_bot_z + c
    z1 = p.pilecap_top_z - c          # dowels extend up into the pile cap
    for i, (x, y) in enumerate(circle_points(px, py, ring_r, p.pile_main_bars)):
        out.append(_bar(f"{tag}_Main_{i+1}", cylinder((x, y, z0), (0, 0, 1), d / 2, z1 - z0), d, z1 - z0, "MAIN"))
    R = p.pile_diameter / 2 - c - t / 2
    for i, z in enumerate(z_range(z0, p.pile_top_z - c, p.rebar_spacing_transverse)):
        out.append(_bar(f"{tag}_Hoop_{i+1}", ring(px, py, z, R, t / 2), t, 2 * math.pi * R, "LIGATURE"))
    return out


def build_all_rebar(p):
    out = pier_cap_rebar(p)
    for ci, y in enumerate(p.pier_y_positions, 1):
        out += pier_rebar(p, y, f"Pier{ci}")
        out += pile_cap_rebar(p, y, f"PileCap{ci}")
        for pi, (dx, dy) in enumerate(p.pile_offsets(), 1):
            out += pile_rebar(p, p.pier_x + dx, y + dy, f"Pile{ci}_{pi}")
    return out
