"""Render an IFC file (tessellated by IfcOpenShell) to PNG - an independent
check that the exported .ifc contains super- and substructure geometry.

Usage:  python scripts/substructure/render_ifc.py model.ifc out.png [substructure_only]
"""
import sys
import ifcopenshell
import ifcopenshell.geom
from OCC.Display.SimpleGui import init_display
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

path, out = sys.argv[1], sys.argv[2]
sub_only = len(sys.argv) > 3
f = ifcopenshell.open(path)
settings = ifcopenshell.geom.settings()
settings.set("use-world-coords", True)
settings.set("use-python-opencascade", True)

v, *_ = init_display("pyside6", size=(1600, 1000))
v.SetModeShaded()
C = lambda r, g, b: Quantity_Color(r, g, b, Quantity_TOC_RGB)
sub_storeys = {"Substructure", "Foundation"}
import ifcopenshell.util.element as ue
for e in f.by_type("IfcElement"):
    if not e.Representation:
        continue
    storey = ue.get_container(e)
    is_sub = storey is not None and storey.Name in sub_storeys
    if sub_only and not is_sub:
        continue
    try:
        shp = ifcopenshell.geom.create_shape(settings, e).geometry
    except Exception as ex:
        print("skip", e, ex); continue
    if e.is_a("IfcReinforcingBar"):
        v.DisplayShape(shp, color=C(0.59, 0.29, 0.16), update=False)
    elif is_sub:
        v.DisplayShape(shp, color=C(0.59, 0.59, 0.57), transparency=0.65, update=False)
    else:
        v.DisplayShape(shp, color=C(0.45, 0.45, 0.42), update=False)
v.View_Iso(); v.FitAll(); v.Repaint()
v.ExportToImage(out)
print("wrote", out)
