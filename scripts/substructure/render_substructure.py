"""Offscreen render of the full bridge (superstructure + substructure) to PNG.

Usage:  python scripts/substructure/render_substructure.py [out_dir] [skew_deg]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "..", "src"), os.path.join(HERE, "..", "..", "tests", "integration")]

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from sample_params import sample_params
from osdagbridge.core.bridge_types.plate_girder.cad_generator import (
    PlateGirderCADGenerator, SUBSTRUCTURE_CONCRETE_TRANSPARENCY, SUBSTRUCTURE_CONCRETE_KEYS)

out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
skew = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
os.makedirs(out_dir, exist_ok=True)

md = PlateGirderCADGenerator().generate(sample_params(skew))
C = lambda r, g, b: Quantity_Color(r / 255, g / 255, b / 255, Quantity_TOC_RGB)
CONCRETE = C(150, 150, 145)   # same as the app
REBAR = C(150, 75, 40)

# Use the Qt-backed pythonOCC viewer (offscreen Cocoa contexts are unreliable on macOS)
from OCC.Display.SimpleGui import init_display
v, _start, _add_menu, _add_fn = init_display("pyside6", size=(1600, 1000))
v.SetModeShaded()
v.set_bg_gradient_color([255, 255, 255], [225, 230, 238])


def show(keys, color, transparency=None):
    for k in keys:
        items = md.get(k, [])
        for s in (items if isinstance(items, list) else [items]):
            v.DisplayShape(s, color=color, transparency=transparency, update=False)


def superstructure():
    show(["girder_web", "girder_flanges", "stiffeners"], C(90, 90, 70))
    show(["cross_bracings"], C(60, 60, 60))
    show(["deck_slab"], C(120, 120, 120))
    show(["crash_barriers", "railings"], C(50, 50, 50))


def substructure(rebar=True, support=None, concrete=True):
    """support=None -> all support lines, else index of one support line."""
    for k in (SUBSTRUCTURE_CONCRETE_KEYS if concrete else ()):
        for i, s in enumerate(md.get(k, [])):
            if support is None or i == support:
                v.DisplayShape(s, color=CONCRETE, transparency=SUBSTRUCTURE_CONCRETE_TRANSPARENCY, update=False)
    if rebar:
        # one rebar compound holding one sub-compound per support line
        from OCC.Core.TopoDS import TopoDS_Iterator
        it = TopoDS_Iterator(md["substructure_rebars"][0])
        i = 0
        while it.More():
            if support is None or i == support:
                v.DisplayShape(it.Value(), color=REBAR, update=False)
            it.Next(); i += 1


def snap(name, view):
    view(); v.FitAll(); v.Repaint()
    path = os.path.join(out_dir, name)
    v.ExportToImage(path)
    print("wrote", path)


tag = f"_skew{int(skew)}" if skew else ""
superstructure(); substructure()
snap(f"full_bridge_iso{tag}.png", v.View_Iso)
snap(f"full_bridge_front{tag}.png", v.View_Front)
v.EraseAll()
substructure()
snap(f"substructure_rebar_iso{tag}.png", v.View_Iso)
snap(f"substructure_rebar_side{tag}.png", v.View_Right)
v.EraseAll()
substructure(support=0)
snap(f"support_closeup_iso{tag}.png", v.View_Iso)
snap(f"support_closeup_front{tag}.png", v.View_Front)
snap(f"support_closeup_right{tag}.png", v.View_Right)
v.EraseAll()
superstructure(); substructure(support=0)
snap(f"support_with_girders_iso{tag}.png", v.View_Iso)

# Close-up: same builders with a short pier cap (parametric override) so the
# 16 mm / 8 mm bars are legible on screen.
from osdagbridge.core.bridge_components.sub_structure.substructure_builder import SubstructureParams
md = PlateGirderCADGenerator().generate(sample_params(
    skew, substructure_params=SubstructureParams(pier_cap_length=3600, include_pedestals=False)))
v.EraseAll()
substructure(support=0)
snap(f"closeup_short_cap_iso{tag}.png", v.View_Iso)
v.EraseAll()
substructure(support=0, rebar=True)
v.View.SetProj(1, -1, 0.35); v.FitAll(); v.ZoomFactor(1.0)
snap(f"closeup_short_cap_persp{tag}.png", lambda: None)
v.EraseAll()
substructure(support=0, concrete=False)
snap(f"closeup_rebar_cage{tag}.png", v.View_Iso)
