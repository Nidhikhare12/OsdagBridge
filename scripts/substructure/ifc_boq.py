"""
Bill of Quantities from an OsdagBridge IFC file.

Reads the IFC4 base quantities written by the exporter (Qto_*BaseQuantities)
and prints / saves a BOQ - the same information a BIM tool such as Revit
schedules after importing the file.

Usage:
    python scripts/substructure/ifc_boq.py <model.ifc> [boq.csv]
"""
import csv
import sys
from collections import defaultdict

import ifcopenshell
import ifcopenshell.util.element as ue

CONCRETE_CLASSES = {
    "IfcBeam": "Pier cap", "IfcColumn": "Pier", "IfcFooting": "Pile cap",
    "IfcPile": "Pile", "IfcBuildingElementProxy": "Pedestal",
}


def boq(path):
    f = ifcopenshell.open(path)
    rows = []

    # Concrete items (substructure)
    conc = defaultdict(lambda: {"count": 0, "volume": 0.0, "material": ""})
    for cls, label in CONCRETE_CLASSES.items():
        for e in f.by_type(cls):
            psets = ue.get_psets(e)
            if "Pset_OsdagSubstructure" not in psets:
                continue
            qto = next((v for k, v in psets.items() if k.startswith("Qto_")), {})
            c = conc[label]
            c["count"] += 1
            c["volume"] += qto.get("NetVolume", 0.0)
            mat = ue.get_material(e)
            c["material"] = mat.Name if mat else ""
    for label, c in conc.items():
        rows.append(["Concrete", label, c["material"], c["count"], "m3", round(c["volume"], 3)])

    # Reinforcement grouped by host type, role and diameter
    steel = defaultdict(lambda: {"count": 0, "length": 0.0, "weight": 0.0})
    for bar in f.by_type("IfcReinforcingBar"):
        ps = ue.get_psets(bar)
        q = ps.get("Qto_ReinforcingElementBaseQuantities", {})
        host = ps.get("Pset_OsdagReinforcement", {}).get("HostElement", "")
        host_type = host.split(" S")[0]
        key = (host_type, bar.PredefinedType, round(bar.NominalDiameter * 1000))
        s = steel[key]
        s["count"] += 1
        s["length"] += q.get("Length", 0.0)
        s["weight"] += q.get("Weight", 0.0)
    for (host, role, dia), s in sorted(steel.items()):
        rows.append(["Reinforcement", f"{host} - {role.lower()} {dia} mm "
                     f"({s['count']} bars, {s['length']:.1f} m)", "Fe 500", s["count"], "kg",
                     round(s["weight"], 1)])

    total_conc = sum(c["volume"] for c in conc.values())
    total_steel = sum(s["weight"] for s in steel.values())
    rows.append(["Total", "Substructure concrete", "", "", "m3", round(total_conc, 3)])
    rows.append(["Total", "Substructure reinforcement", "", "", "kg", round(total_steel, 1)])
    return rows


def main():
    path = sys.argv[1]
    rows = boq(path)
    header = ["Category", "Item", "Material", "Nos", "Unit", "Quantity"]
    widths = [max(len(str(r[i])) for r in rows + [header]) for i in range(len(header))]
    for r in [header] + rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(r, widths)))
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", newline="") as fh:
            csv.writer(fh).writerows([header] + rows)
        print(f"\nBOQ written to {sys.argv[2]}")


if __name__ == "__main__":
    main()
