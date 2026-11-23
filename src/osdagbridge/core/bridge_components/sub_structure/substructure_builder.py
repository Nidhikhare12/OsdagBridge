"""
Substructure assembly builder.

Stacks the individual substructure component builders into complete support
assemblies and places one assembly under each support line of the span:

    girder soffit
      | bearing gap   (bearing - shown by the existing support glyphs)
    pedestals         sub_structure/pedestal/builder.py
    pier cap          sub_structure/pier_cap/builder.py
    pier(s)           sub_structure/pier/builder.py
    pile cap(s)       foundation/pile_cap/builder.py
    piles             foundation/pile/builder.py
    + reinforcement   sub_structure/reinforcement/builder.py

Coordinate systems
------------------
Global (matches the existing OsdagBridge superstructure CAD):
    X longitudinal (span) - girders run from X = 0 to X = L
    Y transverse (deck width) - deck centred on Y = 0
    Z vertical - Z = 0 at the girder mid-depth

Support (local) frame - one per support line:
    origin  : (x_support, 0, z_pier_cap_top) in global coordinates
    +Y      : along the (possibly skewed) support line
    +X      : perpendicular to the support line
    +Z      : vertical
    The frame is rotated about Z by ``-skew`` so that the pier cap stays
    parallel to the skewed girder ends.

All component layouts are produced in the support frame.  The OCC solids are
moved to global coordinates with one rigid transformation per support, and
the IFC exporter reuses the same layouts with one ``IfcLocalPlacement`` per
support - so CAD and IFC are guaranteed to match.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    RebarParams, make_compound, summarize_bars, bend_leg_length,
)
from osdagbridge.core.bridge_components.sub_structure.pier import builder as pier_b
from osdagbridge.core.bridge_components.sub_structure.pier_cap import builder as cap_b
from osdagbridge.core.bridge_components.sub_structure.pedestal import builder as ped_b
from osdagbridge.core.bridge_components.foundation.pile_cap import builder as pcap_b
from osdagbridge.core.bridge_components.foundation.pile import builder as pile_b


@dataclass
class SubstructureParams:
    """All parametric substructure inputs (mm).  Defaults = task defaults."""

    # Piers (circular columns)
    pier_diameter: float = pier_b.PIER_DIAMETER
    pier_height: float = pier_b.PIER_HEIGHT
    n_piers_per_support: int = 1
    pier_spacing: Optional[float] = None          # c/c along support line (n > 1)

    # Pier cap (hammerhead / trapezoidal)
    pier_cap_top_width: float = cap_b.PIER_CAP_TOP_WIDTH
    pier_cap_bottom_width: float = cap_b.PIER_CAP_BOTTOM_WIDTH
    pier_cap_depth: float = cap_b.PIER_CAP_DEPTH
    pier_cap_length: Optional[float] = cap_b.PIER_CAP_LENGTH   # None -> deck width
    pier_cap_style: str = cap_b.PIER_CAP_STYLE                  # "HAMMERHEAD" / "TRAPEZOIDAL"
    pier_cap_end_depth: Optional[float] = None                  # None -> 0.5 x depth
    pier_cap_haunch_offset: float = cap_b.PIER_CAP_HAUNCH_OFFSET

    # Pedestals + bearing gap
    include_pedestals: bool = True
    pedestal_length: float = ped_b.PEDESTAL_LENGTH
    pedestal_width: float = ped_b.PEDESTAL_WIDTH
    pedestal_height: float = ped_b.PEDESTAL_HEIGHT
    bearing_thickness: float = ped_b.BEARING_THICKNESS

    # Pile cap (rectangular prism)
    pile_cap_length: float = pcap_b.PILE_CAP_LENGTH
    pile_cap_width: float = pcap_b.PILE_CAP_WIDTH
    pile_cap_depth: float = pcap_b.PILE_CAP_DEPTH

    # Piles
    n_piles_x: int = pile_b.N_PILES_X
    n_piles_y: int = pile_b.N_PILES_Y
    pile_diameter: float = pile_b.PILE_DIAMETER
    pile_length: float = pile_b.PILE_LENGTH
    pile_spacing: float = pile_b.PILE_SPACING
    pile_spacing_y: Optional[float] = None
    pile_embedment: float = pile_b.PILE_EMBEDMENT               # pile head into cap

    # Reinforcement
    include_reinforcement: bool = True
    rebar: RebarParams = field(default_factory=RebarParams)

    # Support lines: "BOTH_ENDS" places an assembly at X = 0 and X = L
    support_locations: str = "BOTH_ENDS"

    @property
    def n_piles_per_cap(self) -> int:
        return self.n_piles_x * self.n_piles_y


# ---------------------------------------------------------------------------
# Layout (pure Python - shared by CAD and IFC)
# ---------------------------------------------------------------------------

def girder_soffit_z(girder_section_d, girder_section_tf, segment=None, girder_section_tf_b=None):
    """
    Z of the girder bottom-flange soffit, replicating the plate-girder
    builder: Z_top = D/2 + T_ft;  soffit = Z_top - T_ft - D - T_fb (end segment).
    Without a segment the reference section is used (soffit = -D/2 - T_fb).
    """
    z_top = girder_section_d / 2.0 + girder_section_tf
    if segment is None:
        t_fb = girder_section_tf if girder_section_tf_b is None else girder_section_tf_b
        return -girder_section_d / 2.0 - t_fb
    return z_top - segment.T_ft - segment.D - segment.T_fb


def _support_x_positions(params, span_length):
    if params.support_locations == "BOTH_ENDS":
        return [0.0, float(span_length)]
    if params.support_locations == "START":
        return [0.0]
    return [float(span_length)]


def substructure_layout(
    params: SubstructureParams,
    *,
    span_length,
    soffit_z,
    deck_width,
    girder_y_positions,
    skew_angle=0.0,
):
    """
    Compute the complete substructure layout.

    Args:
        params:              SubstructureParams.
        span_length:         Span length L (mm).
        soffit_z:            Global Z of the girder soffit at the bearings.
        deck_width:          Total deck width (mm) - default pier-cap length.
        girder_y_positions:  Global Y of each girder (pedestal positions).
        skew_angle:          Skew angle in degrees, same sign convention as the
                             CAD generator (girder X shift = y * tan(skew)).

    Returns:
        list of support dicts::

            {
              "name": "S1",
              "origin": (x, 0, z_cap_top),     # global, mm
              "rotation_deg": -skew_angle,     # about global Z
              "core_length": core_length,
            "levels": {...},                 # key Z levels (local)
              "components": {
                  "pier_caps": [layout], "pedestals": [...], "piers": [...],
                  "pile_caps": [...], "piles": [...]
              }
            }
    """
    p = params
    rb = p.rebar
    cos_t = math.cos(math.radians(skew_angle)) or 1.0

    # Vertical stacking in the support frame (z = 0 at pier-cap top)
    z_cap_top_global = soffit_z - p.bearing_thickness - (p.pedestal_height if p.include_pedestals else 0.0)
    z_cap_top = 0.0
    z_pier_top = z_cap_top - p.pier_cap_depth
    z_pcap_top = z_pier_top - p.pier_height
    z_pcap_bot = z_pcap_top - p.pile_cap_depth
    z_pile_bot = z_pcap_bot - p.pile_length

    cap_length = p.pier_cap_length if p.pier_cap_length else deck_width / cos_t

    # Pier positions along the support line
    n_p = max(1, int(p.n_piers_per_support))
    pier_spacing = p.pier_spacing or (cap_length / n_p)
    pier_ys = [(i - (n_p - 1) / 2.0) * pier_spacing for i in range(n_p)]

    # Hammerhead: full depth over the pier group + haunch offset, then taper
    core_length = (max(abs(y) for y in pier_ys) * 2 + p.pier_diameter
                   + 2 * p.pier_cap_haunch_offset)

    # Pile-cap bottom steel rests on the pile heads (IS 2911: heads project into the cap)
    bot_clear = max(rb.cover, p.pile_embedment)

    # Anchorage levels of starter bars
    pier_bar_bot = z_pcap_bot + bot_clear + 2 * rb.main_dia + rb.main_dia / 2.0
    pier_bar_top = z_cap_top - rb.cover - rb.tie_dia - 2 * rb.main_dia
    pile_bar_top = z_pcap_top - rb.cover - 2 * rb.tie_dia - rb.main_dia

    # 90 deg bend legs (12 d, limited so hooks keep cover)
    r_pier_cage = p.pier_diameter / 2.0 - rb.cover - rb.tie_dia - rb.main_dia / 2.0
    room_out = min(p.pile_cap_width, p.pile_cap_length) / 2.0 - rb.cover - r_pier_cage - rb.main_dia
    pier_bottom_leg = bend_leg_length(rb.main_dia, room_out)
    pier_top_leg = bend_leg_length(rb.main_dia, r_pier_cage)
    r_pile_cage = p.pile_diameter / 2.0 - rb.cover - rb.tie_dia - rb.main_dia / 2.0
    pile_top_leg = bend_leg_length(rb.main_dia, 2 * r_pile_cage)
    pile_head_vol = math.pi * (p.pile_diameter / 2.0) ** 2 * p.pile_embedment

    supports = []
    for s_idx, x_s in enumerate(_support_x_positions(p, span_length)):
        tag = f"S{s_idx + 1}"
        comps = {"pier_caps": [], "pedestals": [], "piers": [], "pile_caps": [], "piles": []}

        comps["pier_caps"].append(cap_b.pier_cap_layout(
            z_top=z_cap_top, top_width=p.pier_cap_top_width,
            bottom_width=p.pier_cap_bottom_width, depth=p.pier_cap_depth,
            length=cap_length, style=p.pier_cap_style, end_depth=p.pier_cap_end_depth,
            core_length=core_length, rebar=rb, name=f"Pier Cap {tag}"))

        if p.include_pedestals:
            for g, y_g in enumerate(girder_y_positions):
                y_local = y_g / cos_t
                if abs(y_local) + p.pedestal_width / 2.0 > cap_length / 2.0:
                    continue
                comps["pedestals"].append(ped_b.pedestal_layout(
                    center_xy=(0.0, y_local), z_bottom=z_cap_top,
                    length=p.pedestal_length, width=p.pedestal_width,
                    height=p.pedestal_height, rebar=rb, name=f"Pedestal {tag}-G{g + 1}"))

        for k, y_p in enumerate(pier_ys):
            ptag = f"{tag}-P{k + 1}" if n_p > 1 else tag
            comps["piers"].append(pier_b.pier_layout(
                center_xy=(0.0, y_p), z_top=z_pier_top,
                diameter=p.pier_diameter, height=p.pier_height, rebar=rb,
                bar_z_bottom=pier_bar_bot, bar_z_top=pier_bar_top,
                bottom_leg=pier_bottom_leg, top_leg=pier_top_leg,
                name=f"Pier {ptag}"))

            centres = pile_b.pile_grid_positions(
                (0.0, y_p), p.n_piles_x, p.n_piles_y, p.pile_spacing, p.pile_spacing_y)

            comps["pile_caps"].append(pcap_b.pile_cap_layout(
                center_xy=(0.0, y_p), z_top=z_pcap_top,
                length=p.pile_cap_length, width=p.pile_cap_width,
                depth=p.pile_cap_depth, rebar=rb, bottom_clearance=bot_clear,
                embedded_volume_mm3=pile_head_vol * len(centres),
                name=f"Pile Cap {ptag}"))
            for j, c_xy in enumerate(centres):
                comps["piles"].append(pile_b.pile_layout(
                    center_xy=c_xy, z_top=z_pcap_bot, diameter=p.pile_diameter,
                    length=p.pile_length, rebar=rb, bar_z_top=pile_bar_top,
                    top_leg=pile_top_leg, embedment=p.pile_embedment,
                    name=f"Pile {ptag}-{j + 1}"))

        if not p.include_reinforcement:
            for lst in comps.values():
                for lay in lst:
                    lay["bars"] = []

        supports.append({
            "name": tag,
            "origin": (x_s, 0.0, z_cap_top_global),
            "rotation_deg": -float(skew_angle),
            "core_length": core_length,
            "levels": {
                "pier_cap_top": z_cap_top, "pier_top": z_pier_top,
                "pile_cap_top": z_pcap_top, "pile_cap_bottom": z_pcap_bot,
                "pile_toe": z_pile_bot,
            },
            "components": comps,
        })
    return supports


def run_detailing_checks(params: SubstructureParams, supports, concrete_grade="M35"):
    """
    Detailing checks (IS 456 / IRC 112 / IS 2911 / IRC 78) on the modelled
    substructure.  All support lines are identical, so the first one is checked.

    Returns a list of check records (see sub_structure/pier/checks.py).
    """
    from osdagbridge.core.bridge_components.sub_structure.pier import checks as pier_chk
    from osdagbridge.core.bridge_components.foundation.pile import checks as pile_chk
    from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import concrete_fck

    if not supports:
        return []
    fck = concrete_fck(concrete_grade)
    comps = supports[0]["components"]
    out = []
    out += pier_chk.pier_cap_checks(comps["pier_caps"][0], params, fck)
    out += pier_chk.pier_checks(comps["piers"][0], params, fck)
    out += pile_chk.pile_cap_checks(comps["pile_caps"][0], params)
    n_per_cap = params.n_piles_x * params.n_piles_y
    out += pile_chk.pile_checks(comps["piles"][:n_per_cap], params)
    return out


def iter_bars(supports):
    """Yield every bar record in a layout."""
    for s in supports:
        for lst in s["components"].values():
            for lay in lst:
                yield from lay["bars"]


def quantity_summary(supports):
    """Concrete volume (m3) by component type and rebar summary - BOQ helper."""
    concrete = {}
    for s in supports:
        for kind, lst in s["components"].items():
            for lay in lst:
                concrete[kind] = concrete.get(kind, 0.0) + lay["concrete"]["volume_mm3"] / 1e9
    return {"concrete_m3": concrete, "rebar": summarize_bars(list(iter_bars(supports)))}


# ---------------------------------------------------------------------------
# OCC geometry
# ---------------------------------------------------------------------------

def _support_transform(support):
    """gp_Trsf: rotate about global Z by rotation_deg, then translate to origin."""
    from OCC.Core.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir, gp_Vec

    rot = gp_Trsf()
    rot.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
                    math.radians(support["rotation_deg"]))
    tr = gp_Trsf()
    tr.SetTranslation(gp_Vec(*support["origin"]))
    return tr.Multiplied(rot)


_BUILDERS = {
    "pier_caps": cap_b.build_pier_cap,
    "pedestals": ped_b.build_pedestal,
    "piers": pier_b.build_pier,
    "pile_caps": pcap_b.build_pile_cap,
    "piles": pile_b.build_pile,
}


def build_substructure(params: SubstructureParams, **layout_kwargs):
    """
    Build the substructure OCC geometry.

    Keyword arguments are forwarded to :func:`substructure_layout`.

    Returns:
        dict::

            {
              "pier_caps": [shape], "pedestals": [...], "piers": [...],
              "pile_caps": [...], "piles": [...],   # concrete, one compound per support
              "substructure_rebars": [shape],       # all reinforcement (one compound)
              "substructure_layout": supports,      # pure data (IFC / BOQ)
            }
    """
    from OCC.Core.TopLoc import TopLoc_Location

    supports = substructure_layout(params, **layout_kwargs)
    out = {k: [] for k in _BUILDERS}
    all_rebars = []

    for s in supports:
        loc = TopLoc_Location(_support_transform(s))
        rebars_local = []
        for kind, layouts in s["components"].items():
            concrete_local = []
            for lay in layouts:
                built = _BUILDERS[kind](lay)
                concrete_local.append(built["concrete"])
                rebars_local.extend(built["rebars"])
            if concrete_local:
                out[kind].append(make_compound(concrete_local).Moved(loc))
        if rebars_local:
            all_rebars.append(make_compound(rebars_local).Moved(loc))

    out["substructure_rebars"] = [make_compound(all_rebars)] if all_rebars else []
    out["substructure_layout"] = supports
    return out
