"""Substructure assembly for OsdagBridge.

build_bridge_substructure(...) is called from plate_girder/cad_generator.py.
Reference frame of the repo: girders are centred at Z = 0 (web mid-depth), span runs
X = 0 .. L, Y is transverse and symmetric about 0. Substructure hangs below the girders.
"""
from dataclasses import replace

from osdagbridge.core.bridge_components.sub_structure.params import SubstructureParams
from osdagbridge.core.bridge_components.sub_structure.pier.builder import build_piers
from osdagbridge.core.bridge_components.sub_structure.pier_cap.builder import build_pier_cap
from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import build_all_rebar
from osdagbridge.core.bridge_components.foundation.pile_cap.builder import build_pile_caps
from osdagbridge.core.bridge_components.foundation.pile.builder import build_piles


def build_substructure(p: SubstructureParams, include_rebar=True):
    """All Parts (concrete + rebar) for ONE pier line."""
    parts = build_pier_cap(p) + build_piers(p) + build_pile_caps(p) + build_piles(p)
    if include_rebar:
        parts += build_all_rebar(p)
    return parts


def build_bridge_substructure(span_length_L, deck_width, girder_depth, bottom_flange_t,
                              params: SubstructureParams = None,
                              support_clearance=300, x_positions=None):
    """Substructure for a whole bridge: one pier line at each end of the span.

    support_clearance : gap between girder soffit and pier-cap top (bearing height), mm.
    x_positions       : override pier-line X positions (default: 0 and span_length_L).
    """
    base = params or SubstructureParams()
    depth = girder_depth / 2.0 + bottom_flange_t + support_clearance   # deck-side datum -> cap top
    xs = x_positions or (0.0, float(span_length_L))
    ys = (-deck_width / 4.0, deck_width / 4.0)
    parts = []
    for k, x in enumerate(xs, 1):
        p = replace(base, superstructure_depth=depth, pier_cap_length=deck_width,
                    pier_x=x, pier_y_positions=ys)
        line = build_substructure(p)
        for part in line:
            part.name = f"Line{k}_{part.name}"
        parts += line
    return parts


def group_parts(parts):
    """Fuse parts into one compound per kind for fast display / export."""
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.TopoDS import TopoDS_Compound
    out = {}
    for kind, key in (("concrete", "substructure_concrete"), ("steel", "substructure_rebar")):
        b, c = BRep_Builder(), TopoDS_Compound()
        b.MakeCompound(c)
        for part in parts:
            if part.kind == kind:
                b.Add(c, part.shape)
        out[key] = [c]
    return out
