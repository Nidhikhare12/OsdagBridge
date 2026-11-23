# OsdagBridge – Substructure 3D CAD + IFC Integration

Parametric pythonOCC models of the bridge **substructure** (pier cap, pier,
pile cap, piles, bearing pedestals and their reinforcement), integrated into
the existing plate-girder CAD workflow and the IFC4 exporter.

**Author:** Aditya Sarna  
**Video demonstration:** https://youtu.be/h6h36OT0hyM  
**Report:** `docs/report/Substructure_CAD_IFC_Report.pdf`

## What was added

| Component | Builder | Geometry | Reinforcement |
|---|---|---|---|
| Pier cap | `core/bridge_components/sub_structure/pier_cap/builder.py` | **Hammerhead**: section 3000 top / 1200 soffit × 600; full depth over the pier, cantilevers tapering to 300 at the tips; length = deck width. `pier_cap_style="TRAPEZOIDAL"` for constant depth | Stirrups Ø8 @ 200 following the local depth; top Ø16 bent down at tips; bottom Ø16 following the soffit, bent up at tips |
| Pier | `core/bridge_components/sub_structure/pier/builder.py` | Circular column Ø800 × 3000 | 15 Ø16 L-bars (foot on pile-cap mat, head under cap top steel), ties Ø8 @ 200 |
| Pedestal | `core/bridge_components/sub_structure/pedestal/builder.py` | 600 × 600 × 150 under each girder, 100 mm bearing gap | Ø8 @ 100 top/bottom meshes, 4 Ø16 dowels |
| Pile cap | `core/bridge_components/foundation/pile_cap/builder.py` | 1200 (X) × 2200 (Y) × 600; net volume excludes pile heads | Bottom Ø16 **U-bars** @ ≤150 both ways on the pile heads, top mat Ø8 @ ≤200 |
| Piles | `core/bridge_components/foundation/pile/builder.py` | 2 × 2 group, Ø400 × 5000, 600 c/c, heads 50 mm into the cap | 7 Ø16 bars with 12d bends in the cap, ties Ø8 @ 200 |
| Checks | `sub_structure/pier/checks.py`, `foundation/pile/checks.py` | 20 detailing checks (IS 456, IRC 112, IS 2911, IRC 78), shown in the Log dock | – |
| Rebar helpers | `core/bridge_components/sub_structure/reinforcement/builder.py` | Shared rebar params (cover 40), bar layouts, OCC bar solids | |
| Assembly | `core/bridge_components/sub_structure/substructure_builder.py` | `SubstructureParams` dataclass; stacks components at each support line (X = 0 and X = L), follows skew | |
| IFC writer | `core/ifc_export_bridge/substructure_ifc.py` | Writes all of the above into the IFC4 file | |

Every builder has a **pure-Python layout function** (dimensions, positions,
bar centre-lines in mm) and an **OCC build function**. The CAD window and the
IFC exporter both use the same layout, so the two always match.

## Modified existing files

* `core/bridge_types/plate_girder/dto.py` – `include_substructure`, `substructure_params` fields.
* `core/bridge_types/plate_girder/cad_generator.py` – step 12 builds the substructure; new keys
  `pier_caps, pedestals, piers, pile_caps, piles, substructure_rebars, substructure_layout`.
  Also included in STEP/IGES/STL/BREP export via `create3Dcad()`.
* `desktop/ui/cad_3d.py` – concrete shown at opacity 0.35 (transparency 0.65), rebar opaque;
  new **Substructure** and **Reinforcement** checkboxes; hover labels.
* `core/ifc_export_bridge/bridge_cad_extraction.py` – `_extract_substructure()`; IFC girder layout
  now uses the designed girder count/spacing so it matches the CAD.
* `desktop/ui/docks/input_dock.py` – guarded a missing `notify_additional_inputs_footpath` hook
  (AttributeError when the Footpath option changed).
* `core/ifc_export_bridge/bridge_ifc_generator.py` – calls `SubstructureIfcWriter`; OwnerHistory
  `LastModifiedDate` (fixes an IFC4 rule violation).
* `core/ifc_export_bridge/bridge_geometry_mapper.py` – mandatory `ReflectanceMethod` in styles.

## Coordinate system

Same as the existing superstructure: **X** longitudinal (girders from X = 0 to L),
**Y** transverse (deck centred on Y = 0), **Z** vertical (Z = 0 at girder mid-depth).
Each support has a local frame (origin on the pier-cap top at the support line,
rotated by −skew about Z). In IFC: storey placement (global) → support placement →
element placement → rebar placement (relative to its host).

## IFC mapping

| Item | IFC4 entity | Quantities |
|---|---|---|
| Pier | `IfcColumn` (ObjectType Pier) | `Qto_ColumnBaseQuantities` |
| Pier cap | `IfcBeam` USERDEFINED / PierCap (exact `IfcFacetedBrep`) | `Qto_BeamBaseQuantities` |
| Pile cap | `IfcFooting` PILE_CAP | `Qto_FootingBaseQuantities` |
| Pile | `IfcPile` BORED, CAST_IN_PLACE | `Qto_PileBaseQuantities` |
| Pedestal | `IfcBuildingElementProxy` / Pedestal | NetVolume |
| Rebar | `IfcReinforcingBar` MAIN / LIGATURE, `IfcSweptDiskSolid`, typed by `IfcReinforcingBarType` | `Qto_ReinforcingElementBaseQuantities` (Count, Length, Weight) |

Storeys: *Superstructure* (existing), *Substructure*, *Foundation*. Materials:
`Concrete <grade>` and `Reinforcement Steel Fe 500`. The file passes
ifcopenshell schema **and** EXPRESS-rule validation with zero issues.

## Running

```bash
conda activate osdagbridge-env
pip install ifcopenshell          # needed by the IFC exporter (not in environment.yml before)
cd src && python -m osdagbridge.desktop
```
Design a plate-girder bridge → 3D CAD shows super- and substructure →
*File → Save 3D Model → Save as type: IFC (*.ifc)*.

Tests and tools (from the repo root):
```bash
PYTHONPATH=src:tests/integration pytest tests/integration/test_substructure.py -q
python scripts/substructure/ifc_boq.py samples/osdagbridge_super_sub_skew0.ifc samples/boq.csv
python scripts/substructure/render_substructure.py docs/images [skew]
python scripts/substructure/render_ifc.py samples/osdagbridge_super_sub_skew10.ifc out.png
python scripts/substructure/detailing_checks.py samples/detailing_checks_default.csv
```

## Changing dimensions

```python
from osdagbridge.core.bridge_components.sub_structure.substructure_builder import SubstructureParams
from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import RebarParams
dto.substructure_params = SubstructureParams(pier_height=4500, n_piers_per_support=2,
                                             pier_cap_style="TRAPEZOIDAL",
                                             pile_spacing=1200, rebar=RebarParams(main_dia=20))
```
