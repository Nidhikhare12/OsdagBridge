"""
Substructure IFC writer.

Writes the substructure (pier caps, pedestals, piers, pile caps, piles and
their reinforcement) into the IFC4 file produced by ``BridgeIfcGenerator``.

The input is the *same* pure-Python layout used to build the OCC model
(``substructure_builder.substructure_layout``), so the exported geometry is
identical to what is displayed in the CAD window.

Spatial structure
-----------------
    IfcProject
      IfcSite "Default Site"
        IfcBuilding "Bridge Structure"
          IfcBuildingStorey "Superstructure"   (existing exporter)
          IfcBuildingStorey "Substructure"     pier caps, pedestals, piers (+ rebar)
          IfcBuildingStorey "Foundation"       pile caps, piles (+ rebar)

Placement hierarchy (global axis -> relative local axes)
--------------------------------------------------------
    storey placement            global origin, global axes
      support placement         origin = support point, X rotated by -skew
        element placement       element origin in the support frame
          rebar placement       relative to its host element

IFC entities
------------
    pier       -> IfcColumn            (ObjectType "Pier")
    pier cap   -> IfcBeam  USERDEFINED (ObjectType "PierCap")
    pedestal   -> IfcBuildingElementProxy (ObjectType "Pedestal")
    pile cap   -> IfcFooting PILE_CAP
    pile       -> IfcPile   BORED, CAST_IN_PLACE
    rebar      -> IfcReinforcingBar MAIN / LIGATURE with IfcSweptDiskSolid body,
                  typed by IfcReinforcingBarType (one per diameter + role)

Every element carries a material (IfcRelAssociatesMaterial), Osdag property
sets and standard IFC4 base quantities (Qto_*BaseQuantities) so that BIM
tools (e.g. Revit) can schedule volumes, lengths and rebar weights for a BOQ.
"""

import math

from osdagbridge.core.ifc_export_bridge.bridge_geometry_mapper import create_ifc_guid
from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (
    bar_mass_kg,
)

S = 0.001  # mm -> m (file units are metres)

CONCRETE_RGB = (0.62, 0.62, 0.60)
CONCRETE_TRANSPARENCY = 0.65          # opacity 0.35, same as the CAD window
REBAR_RGB = (0.59, 0.29, 0.16)

# component key -> (storey, label)
COMPONENT_STOREY = {
    "pier_caps": "Substructure",
    "pedestals": "Substructure",
    "piers": "Substructure",
    "pile_caps": "Foundation",
    "piles": "Foundation",
}


def _m(v):
    return float(v) * S


class SubstructureIfcWriter:
    """Adds the substructure to an initialised ``BridgeIfcGenerator``."""

    def __init__(self, generator, concrete_grade="M35", rebar_grade="Fe 500"):
        self.g = generator
        self.f = generator.file
        self.mapper = generator.mapper
        self.oh = generator._owner_history
        self.concrete_grade = concrete_grade or "M35"
        self.rebar_grade = rebar_grade
        self._contained = {}          # storey -> [elements]
        self._mat_members = {}        # material -> [elements]
        self._type_members = {}       # bar type -> [bars]
        self._bar_types = {}
        self._styles = {}
        self.stats = {"elements": 0, "bars": 0}

    # ------------------------------------------------------------------ setup

    def _ensure_mass_unit(self):
        """Weights in Qto_ReinforcingElementBaseQuantities need a mass unit."""
        ua = self.g.project.UnitsInContext
        if not any(getattr(u, "UnitType", None) == "MASSUNIT" for u in ua.Units):
            kg = self.f.createIfcSIUnit(None, "MASSUNIT", "KILO", "GRAM")
            ua.Units = list(ua.Units) + [kg]

    def _create_storeys(self, levels_m):
        place = self.mapper.create_axis2placement_3d((0.0, 0.0, 0.0))
        self.storeys = {}
        for name, elev in (("Substructure", levels_m["Substructure"]),
                           ("Foundation", levels_m["Foundation"])):
            self.storeys[name] = self.f.createIfcBuildingStorey(
                create_ifc_guid(), self.oh, Name=name,
                Description=f"OsdagBridge {name.lower()}",
                ObjectPlacement=self.f.createIfcLocalPlacement(self.g.building.ObjectPlacement, place),
                CompositionType="ELEMENT", Elevation=float(elev))
        self.f.createIfcRelAggregates(
            create_ifc_guid(), self.oh, Name="Substructure storeys",
            RelatingObject=self.g.building, RelatedObjects=list(self.storeys.values()))

    def _create_materials(self):
        self.mat_concrete = self.f.createIfcMaterial(
            f"Concrete {self.concrete_grade}", "Reinforced cement concrete (IS 456 / IRC 112)", "Concrete")
        self.mat_rebar = self.f.createIfcMaterial(
            f"Reinforcement Steel {self.rebar_grade}", "HYSD bars (IS 1786)", "Steel")

    def _style(self, key, rgb, transparency=None):
        """IFC4-valid surface style (ReflectanceMethod is mandatory)."""
        if key not in self._styles:
            colour = self.f.createIfcColourRgb(None, *map(float, rgb))
            rendering = self.f.createIfcSurfaceStyleRendering(
                SurfaceColour=colour, Transparency=transparency, ReflectanceMethod="NOTDEFINED")
            self._styles[key] = self.f.createIfcSurfaceStyle(key, "BOTH", [rendering])
        return self._styles[key]

    def _shape(self, items, rep_type, style):
        rep = self.f.createIfcShapeRepresentation(self.mapper._context3d, "Body", rep_type, items)
        for it in items:
            self.f.createIfcStyledItem(it, [style], None)
        return self.f.createIfcProductDefinitionShape(None, None, [rep])

    def _placement(self, parent, origin_m, x_dir=(1.0, 0.0, 0.0)):
        return self.f.createIfcLocalPlacement(
            parent, self.mapper.create_axis2placement_3d(origin_m, z_dir=(0., 0., 1.), x_dir=x_dir))

    # ------------------------------------------------------------- properties

    def _qto(self, element, name, quantities):
        """quantities: list of (kind, name, value) with kind in L/A/V/W/C."""
        ctor = {
            "L": self.f.createIfcQuantityLength, "A": self.f.createIfcQuantityArea,
            "V": self.f.createIfcQuantityVolume, "W": self.f.createIfcQuantityWeight,
            "C": self.f.createIfcQuantityCount,
        }
        qs = [ctor[k](n, None, None, float(v)) for k, n, v in quantities if v is not None]
        eq = self.f.createIfcElementQuantity(create_ifc_guid(), self.oh, name, None, None, qs)
        self.f.createIfcRelDefinesByProperties(create_ifc_guid(), self.oh, None, None, [element], eq)

    def _pset(self, element, name, props):
        self.g.metadata.assign_metadata(element, props, property_set_name=name)

    # --------------------------------------------------------------- concrete

    def _concrete_geometry(self, c):
        """
        Return (element_origin_in_support_frame_mm, [solid], gross quantities)
        with the solid expressed in the element's local axes (metres).
        """
        ident = self.mapper.create_axis2placement_3d((0., 0., 0.))
        if c["type"] == "cylinder":
            origin = c["base"]
            prof = self.f.createIfcCircleProfileDef("AREA", None, self.mapper.create_axis2placement_2d(),
                                                   _m(c["radius"]))
            solid = self.mapper.create_extruded_solid(prof, _m(c["height"]), ident)
            area = math.pi * c["radius"] ** 2
            q = {"length": c["height"], "area": area, "volume": area * c["height"],
                 "surface": 2 * math.pi * c["radius"] * c["height"]}
        elif c["type"] == "box":
            (x0, y0, z0), (sx, sy, sz) = c["min"], c["size"]
            origin = (x0 + sx / 2.0, y0 + sy / 2.0, z0)
            prof = self.mapper.create_rectangular_profile(_m(sx), _m(sy))
            solid = self.mapper.create_extruded_solid(prof, _m(sz), ident)
            q = {"length": sx, "width": sy, "height": sz, "area": sx * sy, "volume": sx * sy * sz}
        elif c["type"] == "lofted_sections":
            # Hammerhead / trapezoidal pier cap: ruled loft through trapezoidal
            # sections.  All faces are planar, so an IfcFacetedBrep is exact.
            z_bot = c["z_top"] - c["depth"]
            origin = (0.0, 0.0, z_bot)
            solid = self._faceted_loft(c["stations"], z_bot)
            q = {"length": c["length"], "width": c["top_width"], "height": c["depth"],
                 "area": c["max_area"], "volume": c["volume_mm3"]}
            return origin, [solid], q, "Brep"
        else:
            raise ValueError(f"Unknown concrete type {c['type']}")
        q.setdefault("gross_volume", c.get("gross_volume_mm3", q["volume"]))
        q["volume"] = c.get("volume_mm3", q["volume"])
        return origin, [solid], q, "SweptSolid"

    def _faceted_loft(self, stations, z_ref):
        """
        IfcFacetedBrep of a ruled loft through planar sections.

        ``stations``: [{"y", "profile_xz": CCW [(x, z), ...]}], y increasing.
        A CCW (x, z) profile has its normal along -Y, so the first section is
        used as-is for the -Y end cap and reversed for the +Y end cap; side
        faces are ordered so their normals point outwards.
        """
        rings = [[self.f.createIfcCartesianPoint((_m(x), _m(st["y"]), _m(z - z_ref)))
                  for x, z in st["profile_xz"]] for st in stations]
        n = len(rings[0])

        def face(pts):
            return self.f.createIfcFace([self.f.createIfcFaceOuterBound(self.f.createIfcPolyLoop(pts), True)])

        faces = [face(rings[0]), face(list(reversed(rings[-1])))]
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(n):
                k1 = (k + 1) % n
                faces.append(face([a[k], b[k], b[k1], a[k1]]))
        return self.f.createIfcFacetedBrep(self.f.createIfcClosedShell(faces))

    def _create_concrete(self, kind, layout, support, support_place, storey):
        c = layout["concrete"]
        origin, solids, q, rep_type = self._concrete_geometry(c)
        q.setdefault("gross_volume", q["volume"])
        place = self._placement(support_place, tuple(_m(v) for v in origin))
        shape = self._shape(solids, rep_type,
                            self._style("Concrete", CONCRETE_RGB, CONCRETE_TRANSPARENCY))
        common = dict(GlobalId=create_ifc_guid(), OwnerHistory=self.oh, Name=layout["name"],
                      ObjectPlacement=place, Representation=shape, Tag=layout["name"])
        m3 = lambda mm3: mm3 * 1e-9
        m2 = lambda mm2: mm2 * 1e-6

        if kind == "piers":
            el = self.f.create_entity("IfcColumn", ObjectType="Pier", PredefinedType="COLUMN", **common)
            self._qto(el, "Qto_ColumnBaseQuantities", [
                ("L", "Length", _m(q["length"])), ("A", "CrossSectionArea", m2(q["area"])),
                ("A", "OuterSurfaceArea", m2(q["surface"])),
                ("V", "GrossVolume", m3(q["volume"])), ("V", "NetVolume", m3(q["volume"]))])
        elif kind == "pier_caps":
            el = self.f.create_entity("IfcBeam", ObjectType="PierCap", PredefinedType="USERDEFINED", **common)
            self._qto(el, "Qto_BeamBaseQuantities", [
                ("L", "Length", _m(q["length"])), ("A", "CrossSectionArea", m2(q["area"])),
                ("V", "GrossVolume", m3(q["volume"])), ("V", "NetVolume", m3(q["volume"]))])
        elif kind == "pile_caps":
            el = self.f.create_entity("IfcFooting", ObjectType="PileCap", PredefinedType="PILE_CAP", **common)
            self._qto(el, "Qto_FootingBaseQuantities", [
                ("L", "Length", _m(q["width"])), ("L", "Width", _m(q["length"])),
                ("L", "Height", _m(q["height"])), ("A", "GrossSurfaceArea", m2(q["area"])),
                # Net = gross - pile heads projecting into the cap
                ("V", "GrossVolume", m3(q["gross_volume"])), ("V", "NetVolume", m3(q["volume"]))])
        elif kind == "piles":
            el = self.f.create_entity("IfcPile", ObjectType="BoredCastInSituPile", PredefinedType="BORED",
                                      ConstructionType="CAST_IN_PLACE", **common)
            self._qto(el, "Qto_PileBaseQuantities", [
                ("L", "Length", _m(q["length"])), ("A", "CrossSectionArea", m2(q["area"])),
                ("A", "OuterSurfaceArea", m2(q["surface"])),
                ("V", "GrossVolume", m3(q["volume"])), ("V", "NetVolume", m3(q["volume"]))])
        else:  # pedestals
            el = self.f.create_entity("IfcBuildingElementProxy", ObjectType="Pedestal",
                                      PredefinedType="USERDEFINED", **common)
            self._qto(el, "Qto_BuildingElementProxyQuantities", [
                ("V", "NetVolume", m3(q["volume"]))])

        self._pset(el, "Pset_ConcreteElementGeneral", {
            "StrengthClass": self.concrete_grade, "ConstructionMethod": "InSitu",
            "ExposureClass": "Moderate (IRC 112)",
        })
        self._pset(el, "Pset_OsdagSubstructure", {
            "Component": kind.rstrip("s").replace("_", " ").title(),
            "Shape": c.get("style", c["type"]),
            "SupportLine": support["name"],
            "ConcreteVolume_m3": round(m3(q["volume"]), 4),
            "SkewRotation_deg": float(support["rotation_deg"]),
            "Cover_mm": float(self.cover),
        })
        self._contained.setdefault(storey, []).append(el)
        self._mat_members.setdefault(self.mat_concrete, []).append(el)
        self.stats["elements"] += 1
        return el, place, origin

    # ------------------------------------------------------------------ rebar

    def _bar_type(self, dia, role):
        key = (dia, role)
        if key not in self._bar_types:
            area = math.pi * (dia / 2.0) ** 2
            self._bar_types[key] = self.f.create_entity(
                "IfcReinforcingBarType", GlobalId=create_ifc_guid(), OwnerHistory=self.oh,
                Name=f"{role.title()} bar {dia:.0f} mm", PredefinedType=role,
                NominalDiameter=_m(dia), CrossSectionArea=area * 1e-6, BarSurface="TEXTURED")
        return self._bar_types[key]

    def _create_bar(self, bar, host, host_place, host_origin, storey, idx):
        ox, oy, oz = host_origin
        pts = [self.f.createIfcCartesianPoint((_m(x - ox), _m(y - oy), _m(z - oz)))
               for x, y, z in bar["path"]]
        # Loops are already open polylines that close with a lap (see
        # reinforcement/builder.py); swept-disk solids need an open directrix.
        directrix = self.f.createIfcPolyline(pts)
        solid = self.f.createIfcSweptDiskSolid(directrix, _m(bar["dia"] / 2.0), None, None, None)
        shape = self._shape([solid], "AdvancedSweptSolid", self._style("Rebar", REBAR_RGB))
        place = self.f.createIfcLocalPlacement(host_place, self.mapper.create_axis2placement_3d((0., 0., 0.)))
        name = f"{host.Name} {'Main' if bar['role'] == 'MAIN' else 'Tie'} {bar['dia']:.0f}mm #{idx}"
        area = math.pi * (bar["dia"] / 2.0) ** 2
        el = self.f.create_entity(
            "IfcReinforcingBar", GlobalId=create_ifc_guid(), OwnerHistory=self.oh, Name=name,
            ObjectType=bar["role"], ObjectPlacement=place, Representation=shape, Tag=f"{host.Tag}-{idx}",
            NominalDiameter=_m(bar["dia"]), CrossSectionArea=area * 1e-6,
            BarLength=_m(bar["length"]), PredefinedType=bar["role"], BarSurface="TEXTURED")
        self._qto(el, "Qto_ReinforcingElementBaseQuantities", [
            ("C", "Count", 1), ("L", "Length", _m(bar["length"])), ("W", "Weight", bar_mass_kg(bar))])
        self._pset(el, "Pset_OsdagReinforcement", {
            "HostElement": host.Name, "BarDiameter_mm": float(bar["dia"]),
            "BarRole": bar["role"], "SteelGrade": self.rebar_grade,
        })
        self._type_members.setdefault(self._bar_type(bar["dia"], bar["role"]), []).append(el)
        self._contained.setdefault(storey, []).append(el)
        self._mat_members.setdefault(self.mat_rebar, []).append(el)
        self.stats["bars"] += 1

    # ------------------------------------------------------------------- main

    def write(self, supports, cover=40.0):
        """Write all supports (list from substructure_layout) into the file."""
        if not supports:
            return self.stats
        self.cover = cover
        self._ensure_mass_unit()
        self._create_materials()

        lv = supports[0]["levels"]
        z0 = supports[0]["origin"][2]
        self._create_storeys({
            # storey elevation = level of its lowest element
            "Substructure": _m(z0 + lv["pile_cap_top"]),
            "Foundation": _m(z0 + lv["pile_toe"]),
        })

        for sup in supports:
            phi = math.radians(sup["rotation_deg"])
            x_dir = (math.cos(phi), math.sin(phi), 0.0)
            origin_m = tuple(_m(v) for v in sup["origin"])
            # One support frame per storey (same origin & axes)
            sup_places = {
                name: self._placement(st.ObjectPlacement, origin_m, x_dir)
                for name, st in self.storeys.items()
            }
            for kind, layouts in sup["components"].items():
                storey_name = COMPONENT_STOREY[kind]
                storey = self.storeys[storey_name]
                for lay in layouts:
                    host, host_place, host_origin = self._create_concrete(
                        kind, lay, sup, sup_places[storey_name], storey)
                    for i, bar in enumerate(lay["bars"], start=1):
                        self._create_bar(bar, host, host_place, host_origin, storey, i)

        # Batched relationships
        for storey, elems in self._contained.items():
            self.f.createIfcRelContainedInSpatialStructure(
                create_ifc_guid(), self.oh, None, None, elems, storey)
        for mat, elems in self._mat_members.items():
            self.f.createIfcRelAssociatesMaterial(create_ifc_guid(), self.oh, None, None, elems, mat)
        for btype, bars in self._type_members.items():
            self.f.createIfcRelDefinesByType(create_ifc_guid(), self.oh, None, None, bars, btype)
        decl = self.f.createIfcRelDeclares(create_ifc_guid(), self.oh, "Rebar types", None,
                                          self.g.project, list(self._bar_types.values()))
        return self.stats
