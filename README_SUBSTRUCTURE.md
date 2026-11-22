# Substructure 3D CAD & IFC Workflow — Task C (OsdagBridge / FOSSEE Winter Internship 2026)

This branch (`task/3dcad-substructure-ifc`) adds a **parametric, modular
substructure** to the plate-girder bridge: circular RC piers with hammerhead
caps, rectangular pile caps with bored pile groups, and visible rebar cages —
in both the **pythonOCC 3D CAD viewer** and the **IFC4 export** used for BIM
(Revit) and BOQ take-off.

---

## 1. What was added (file map)

```
src/osdagbridge/core/bridge_components/
├── sub_structure/
│   ├── pier/
│   │   ├── properties.py     # PierParams dataclass + concrete/steel volumes (BOQ)
│   │   ├── geometry.py       # pure-Python bar-ring / tie placement math
│   │   └── builder.py        # build_pier(): pythonOCC column + rebar cage
│   └── pier_cap/
│       ├── properties.py     # PierCapParams + trapezoid prism volume
│       ├── geometry.py       # trapezoid profile points, auto cap length
│       └── builder.py        # build_pier_cap(): hammerhead prism
└── foundation/
    ├── pile_cap/
    │   ├── properties.py     # PileCapParams + volumes
    │   ├── geometry.py       # bottom-mat bar grid positions (pure Python)
    │   └── builder.py        # build_pile_cap(): box + rebar mat
    └── pile/
        ├── properties.py     # PileParams + volumes
        ├── geometry.py       # pile group grid positions (pure Python)
        └── builder.py        # build_pile(), build_pile_group()
```

Modified existing files:

| File | Change |
|---|---|
| `core/bridge_types/plate_girder/dto.py` | new `SubstructureParamsDTO` (all default dims) appended to `BridgeParametersDTO` with a default factory — fully backward compatible |
| `core/bridge_types/plate_girder/cad_generator.py` | imports the 4 builders; `STEP 12` assembles the substructure at both support lines; `display_3dModel` "Substructure" branch; `create3Dcad()` now also fuses the substructure into STEP/IGS/STL/BREP |
| `desktop/ui/cad_3d.py` | renders Pier / Pier Cap / Pile Cap / Pile (semi-transparent concrete) + opaque steel Rebar; new **Substructure** checkbox |
| `core/ifc_export_bridge/bridge_geometry_mapper.py` | `IfcCircleProfileDef` + `IfcCircleHollowProfileDef` translators |
| `core/ifc_export_bridge/bridge_cad_extraction.py` | `_extract_substructure()` — parametric reconstruction shared with the builders |
| `core/ifc_export_bridge/bridge_ifc_generator.py` | "Substructure" `IfcBuildingStorey`; processors → `IfcColumn`, `IfcBeam`, `IfcFooting`, `IfcPile`, `IfcBuildingElementProxy` (rebar) |
| `core/ifc_export_bridge/metadata_mapper.py` | `map_substructure()` — BOQ-relevant property sets |

Each component follows the superstructure pattern: `properties.py`
(parametric dataclass + quantities), `geometry.py` (pure-Python placement
math, **no OCC** — also imported by the IFC extractor so CAD and IFC never
diverge), `builder.py` (pythonOCC solids, returns `TopoDS_Shape` lists).
`checks.py` files remain design-check stubs (out of CAD scope).

## 2. Coordinate system & placement

Identical to the superstructure builders:

```
X = longitudinal (span), from 0 .. span_length_L
Y = transverse (deck width), centred on 0
Z = vertical, Z = 0 at girder mid-height (substructure is at negative Z)
```

Supports of the simply-supported plate girder sit at the span ends, so the
substructure is built twice — at **X = 0** and **X = span_length_L** (this is
where the plate-girder builder places its support frames). Vertical stack
per support line (top → bottom):

```
z_bearing      = -(D/2 + T_fb)            girder soffit = bearing level
pier cap       top @ z_bearing            (trapezoid, deep = pier_cap_depth)
pier column    top @ cap soffit           (circular, high = pier_height)
pile cap       top @ pier base            (rect prism, deep = pile_cap_depth)
piles          heads @ pile-cap soffit    (2x2 grid, long = pile_length)
```

`z_bearing` is computed from the **end girder segments** exactly like the
support frames in `super_structure/plate_girder/builder.py`, so a deeper end
segment automatically lowers the pier cap. Skewed bridges: the substructure is
placed square to the global axes (the pier axis is on Y = 0, where the
superstructure skew offset is zero by definition).

## 3. Parametric API (all dimensions in mm)

```python
build_pier(                                   # sub_structure/pier/builder.py
    *, pier_diameter=800, pier_height=3000,
    x_center=0, y_center=0, top_z=0,          # top_z = pier-cap soffit
    include_rebar=True,
    rebar_main_diameter=16, rebar_spacing_longitudinal=150,
    rebar_transverse_diameter=8, rebar_spacing_transverse=200,
    rebar_cover=40)
# -> {"concrete": [...], "rebar_longitudinal": [...], "rebar_transverse": [...]}

build_pier_cap(                               # sub_structure/pier_cap/builder.py
    *, top_width=3000, bottom_width=1200, depth=600,
    length=None,                              # None -> 3*bottom_width standalone;
                                              #         assembly passes deck width
    x_center=0, y_center=0, top_z=0)          # top_z = bearing level
# -> {"concrete": [...]}

build_pile_cap(                               # foundation/pile_cap/builder.py
    *, length=2200, width=1200, depth=600,
    x_center=0, y_center=0, top_z=0,          # top_z = pier base
    include_rebar=True,
    rebar_main_diameter=16, rebar_spacing_longitudinal=150,
    rebar_transverse_diameter=8, rebar_spacing_transverse=200,
    rebar_cover=40)
# -> {"concrete": [...], "rebar_longitudinal": [...], "rebar_transverse": [...]}

build_pile_group(                             # foundation/pile/builder.py
    *, n_piles_x=2, n_piles_y=2,              # 2x2 = 4 piles per cap
    pile_diameter=400, pile_length=5000,
    pile_spacing_x=600, pile_spacing_y=600,   # c/c
    x_center=0, y_center=0, top_z=0)          # top_z = pile-cap soffit
# -> {"concrete": [...], "positions": [(dx, dy), ...]}
```

### How dimensions flow

```
UI / plategirderbridge.py
   └─ BridgeParametersDTO.substructure_params : SubstructureParamsDTO   (dto.py)
         (defaults: pier 800x3000, cap 3000/1200x600, pile cap 2200x1200x600,
          4xØ400x5000 piles @600 c/c, Ø16@150 + Ø8@200, cover 40,
          transparency 0.35)
   └─ PlateGirderCADGenerator._set_parameters()      (cad_generator.py)
         reads the DTO (getattr fallbacks for older DTOs)
   └─ PlateGirderCADGenerator.generate()  STEP 12    (cad_generator.py)
         per support line: build_pier_cap -> build_pier ->
         build_pile_cap -> build_pile_group;  rebar solids are
         compounded into one shape (stiffener/shear-stud pattern)
   └─ model_data["piers" | "pier_caps" | "pile_caps" | "piles" |
                 "substructure_rebar"]
         ├─ desktop/ui/cad_3d.py  (display, transparency, hover labels)
         ├─ create3Dcad()         (STEP/IGS/STL/BREP fuse)
         └─ PlateGirderIFCExtractor._extract_substructure()   (IFC path)
```

The IFC extractor re-imports the same `geometry.py` helpers
(`bar_ring_radius`, `tie_levels`, `main_bar_positions`,
`transverse_bar_positions`, `pile_positions`, `trapezoid_profile_points`,
`auto_pier_cap_length`) and the same `properties.py` volume functions, so the
`.ifc` geometry and metadata always coincide with the CAD solids.

### Reinforcement detailing rules

* **Pier**: longitudinal bars on a ring at `D/2 - cover - Ø/2`; bar count
  `ceil(core circumference / spacing)` (min 6) so the real spacing never
  exceeds the nominal. Ties are thin annular solids
  (`outer cylinder − inner cylinder`) whose centreline wraps the bar ring
  (outer radius = ring + Ø/2, wall = Ø, both in CAD and IFC); the tie count
  again guarantees actual spacing ≤ nominal, with ties at both cover
  planes. Bars run from bottom+cover to top−cover. The pier-cap trapezoid
  profile is wound **counter-clockwise** (face normal along the +Y
  extrusion, `IfcArbitraryClosedProfileDef` rule).
* **Pile cap**: bottom mat — main bars along X spread across Y, transverse
  bars along Y spread across X **resting on top of the main bars**; bar ends
  inset by the cover; symmetric grids with actual spacing ≤ nominal.

## 4. Running the 3D CAD

```bash
# conda env from environment.yml (includes pythonocc-core)
conda activate osdagbridge
python -m osdagbridge.desktop
```

1. New Project → Plate Girder → fill the design inputs → **Design**.
2. Open the **3D CAD** view — the substructure is generated automatically
   (defaults from `SubstructureParamsDTO`).
3. Tick/untick the new **Substructure** checkbox: concrete members
   (piers, pier caps, pile caps, piles) render semi-transparent
   (opacity 0.35) in concrete grey; the rebar cage renders opaque in steel
   blue and is visible *through* the pier/pile-cap concrete. Hover a member
   to see its dimensions.

To customize dimensions programmatically (UI fields are not wired yet):

```python
from osdagbridge.core.bridge_types.plate_girder.dto import SubstructureParamsDTO
design_params.substructure_params = SubstructureParamsDTO(
    pier_diameter=1000, pier_height=3500, rebar_cover=50, ...)
```

## 5. Exporting the IFC

`File → Save 3D CAD Model → file type "IFC (*.ifc)"` (or the *Export IFC
Model* action). The generated `.ifc` is an **IFC4** file (metres) containing:

| Content | IFC entity | PredefinedType |
|---|---|---|
| Pier column | `IfcColumn` | `COLUMN` |
| Pier cap (hammerhead) | `IfcBeam` | `BEAM` |
| Pile cap | `IfcFooting` | `PILE_CAP` |
| Pile | `IfcPile` | `BORED` |
| Rebar cage (per member) | `IfcBuildingElementProxy` | ObjectType `RebarAssembly` |
| All superstructure parts | unchanged (`IfcPlate`, `IfcMember`, `IfcSlab`, …) | — |

Spatial structure: `IfcProject → IfcSite → IfcBuilding → {IfcBuildingStorey
"Superstructure", IfcBuildingStorey "Substructure"}`. Global axes are kept
(X span, Y transverse, Z vertical, substructure at negative Z), each element
carries an `IfcLocalPlacement` with meaningful local axes relative to its
storey.

BOQ-relevant `Pset_OsdagBridgeProperties` (same pattern as the existing
superstructure psets) are attached to every substructure element:
`ComponentRole`, dimensions in metres, `NumberOfPiles`, `ConcreteVolume`
(m³), `BarCount`, `MainBarDiameter`, spacings, `ClearCover`, `SteelVolume`,
`Material` (concrete grade enriched with fck/fctm/Ecm from the Osdag
database; `Fe 500` for rebar). Import in Revit / BIMcollab / usBIM to
schedule quantities.

## 6. Environment note

The pythonOCC code targets **pythonocc-core** as provided by the conda
environment in `environment.yml` (OCC 7.x, `OCC.Core.*` modules) — the exact
API surface used by the existing superstructure builders. It cannot run under
the plain-pip sandbox used for development; every file passes
`python -m py_compile` and every OCC class used was cross-checked against a
pre-existing, known-working builder (see commit history / task report).

## 7. Verification performed (no OCC/ifcopenshell in sandbox)

* `python -m py_compile` on **every** created/modified file — zero errors.
* Pure-Python placement/quantity modules (`geometry.py`, `properties.py`,
  `dto.py`) were imported and numerically validated:
  16 pier bars @ 141 mm ≤ 150 nominal, 16 ties @ 194.7 mm ≤ 200,
  9 main bars @ 140 mm ≤ 150, 12 transverse bars @ 192.7 mm ≤ 200,
  2×2 pile grid at ±300 mm, concrete/steel volumes computed
  (pier 1.508 m³ concrete / 0.0112 m³ steel ≈ 88 kg per cage).
* Winding checks: pier-cap trapezoid shoelace area +1 260 000 mm² (CCW),
  same |area| as `(a+b)/2·h`; cover to the outermost rebar surface = 40 mm
  exactly on the pier ring and the pile-cap mat.
* OCC API cross-check (automated against the pre-task commit): all OCC
  imports used in new/modified files already appear, with identical import
  paths, in the pre-existing code — 0 exceptions (incl. `BRepAlgoAPI_Cut`,
  which the untouched `railing/builder.py` already uses).
* Runtime GUI/IFC validation must be done in the conda env (see §4–5).
