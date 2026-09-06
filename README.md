# OsdagBridge Substructure CAD Modeling & IFC4 Export Integration

This repository contains the complete implementation of the **Bridge Substructure Layer** for the **OsdagBridge** parametric bridge modeling desktop application (IIT Bombay, Autumn Internship 2026 Screening Task).

It provides end-to-end parametric 3D CAD geometry generation using OpenCASCADE (`pythonOCC`), desktop visualization in PySide6, and standard-compliant Building Information Modeling (BIM) export in **IFC4** (`ifcopenshell`) with automated property sets and Bill of Quantities (BOQ) metrics.

---

## 1. Overview & Key Objectives

1. **Parametric 3D Solid Geometry**: Implemented 5 dedicated substructure builders for Pier Columns, Hammerhead Pier Caps, Pile Caps, Bored Pile Clusters, and Reinforcement Cages using `pythonOCC`.
2. **Modular Architecture & DTO**: Unified all geometric and topological parameters into a type-safe `SubstructureParametersDTO` dataclass with sensible engineering defaults (in mm) without breaking backward compatibility (`substructure=None` support).
3. **CAD Engine Integration**: Wired the substructure geometry into `PlateGirderCADGenerator` (Step 12) and `CAD_3D` viewer with individual component layer visibility toggles and transparency controls.
4. **IFC4 BIM Export Pipeline**: Built a 4-stage parametric extraction and serialization workflow mapping elements to standard IFC classes (`IfcColumn`, `IfcBeam`, `IfcFooting`, `IfcPile`, `IfcReinforcingBar`) with `IfcRelAggregates`, `IfcMaterial`, and `Qto_*BaseQuantities`.
5. **Quality Assurance & Verification**: Resolved cross-platform coordinate frame and extrusion vector transformations across external BIM viewers (Autodesk Revit, web IFC viewers). Validated via 8 automated unit tests and an IFC deep-inspection suite.

---

## 2. Directory & Module Structure

```
src/osdagbridge/
├── core/
│   ├── bridge_components/
│   │   ├── sub_structure/
│   │   │   ├── pier/
│   │   │   │   └── builder.py         # Pier shaft geometry (build_pier)
│   │   │   ├── pier_cap/
│   │   │   │   └── builder.py         # Hammerhead trapezoidal cap (build_pier_cap)
│   │   │   └── pier_rebar/
│   │   │       └── builder.py         # Rebar cages & grid mats (build_pier_rebar, build_pile_rebar)
│   │   └── foundation/
│   │       ├── pile_cap/
│   │       │   └── builder.py         # Rectangular footing block (build_pile_cap)
│   │       └── pile/
│   │           └── builder.py         # Bored cast-in-situ piles (build_piles)
│   │
│   ├── bridge_types/
│   │   └── plate_girder/
│   │       ├── dto.py                 # SubstructureParametersDTO & BridgeParametersDTO
│   │       └── cad_generator.py       # Step 12 substructure pipeline wiring
│   │
│   └── ifc_export_bridge/
│       ├── bridge_cad_extraction.py  # PlateGirderIFCExtractor (_extract_substructure)
│       ├── bridge_geometry_mapper.py  # Profile helpers & assign_material()
│       ├── bridge_ifc_generator.py    # IFC4 entity assembly (_process_substructure)
│       └── metadata_mapper.py         # Property sets & BOQ quantity sets
│
├── desktop/
│   └── ui/
│       └── cad_3d.py                  # 3D viewer rendering, transparency, checkboxes
│
tests/
└── unit/
    ├── test_substructure.py           # Automated unit test suite (8 test cases)
    └── validate_ifc_export.py         # Deep IFC export & entity verification script
```

---

## 3. Coordinate System & Elevation Datum

All geometry conforms to the right-handed reference frame established in ` .md`:
* **$X$-axis**: Longitudinal (along bridge span length $L$, traffic direction).
* **$Y$-axis**: Transverse (across deck width).
* **$Z$-axis**: Vertical, positive upward.
* **Origin $(0,0,0)$**: Center of span at the **girder mid-height** (web centroid).

### Vertical Elevation Chain
All substructure components sit entirely below $Z = 0$, cascading downward from the girder soffit:
$$\begin{aligned}
Z_{\text{soffit}} &= -\frac{D_{\text{web}}}{2} - T_{f,\text{bottom}} \\
Z_{\text{pier cap top}} &= Z_{\text{soffit}} \\
Z_{\text{pier base}} &= Z_{\text{pier cap top}} - h_{\text{pier cap}} - h_{\text{pier}} \\
Z_{\text{pile cap top}} &= Z_{\text{pier base}} \\
Z_{\text{pile top}} &= Z_{\text{pile cap top}} - t_{\text{pile cap}} \\
Z_{\text{pile base}} &= Z_{\text{pile top}} - L_{\text{pile}}
\end{aligned}$$

---

## 4. Component Geometry Specifications

| Component | Default Dimensions (mm) | CAD Primitive / Construction Method |
|---|---|---|
| **Pier Shaft** | $d = 800$, $h = 3000$, solid | Solid or hollow cylinder via `BRepPrimAPI_MakeCylinder` along $+Z$ axis. Hollow shafts utilize `BRepAlgoAPI_Cut`. |
| **Pier Cap** | Top width = 3000, Bottom width = 1200, Depth = 600, Height = 600 | Trapezoidal hammerhead loft via `BRepOffsetAPI_ThruSections` between top and bottom rectangular wires. |
| **Pile Cap** | $L_x = 2200$, $L_y = 1200$, $t = 600$ | Rectangular footing prism via `BRepPrimAPI_MakeBox` centered under the column group. |
| **Bored Piles** | $2 \times 2$ grid, $d = 400$, $L = 5000$, $s_x = s_y = 600$ | Grid of downward cylinders extending below the pile cap base. |
| **Reinforcement** | Main: $12\times\phi16$, Ties: $\phi8$ @ 200, Cover = 40 | Main vertical bar cylinders arranged in a circle + horizontal torus rings (`BRepPrimAPI_MakeTorus`). Orthogonal grid mats for caps. |

---

## 5. IFC4 BIM Export Architecture

The IFC4 export pipeline executes across four sequential stages:

```
[ CAD Generator / DTO ]
         │
         ▼
[ Stage 1: Extraction ] ──────────► PlateGirderIFCExtractor (_extract_substructure)
         │                          Reconstructs positions parametrically (no tessellation)
         ▼
[ Stage 2: Geometry Mapping ] ────► BridgeGeometryMapper
         │                          Builds IfcCircleProfileDef, IfcRectangleProfileDef, IfcExtrudedAreaSolid
         ▼
[ Stage 3: Entity Assembly ] ─────► BridgeIfcGenerator
         │                          Creates IfcColumn, IfcBeam, IfcFooting, IfcPile, IfcReinforcingBar
         ▼
[ Stage 4: Metadata & BOQ ] ──────► BridgeMetadataMapper
         │                          Applies Pset_OsdagBridgeProperties, Qto_*BaseQuantities, IfcMaterial
         ▼
   [ .ifc File Output ]
```

### Key BIM Implementation Highlights:
1. **Standard-Compliant Extrusion Vector**: In buildingSMART IFC4, `IfcExtrudedAreaSolid` sweeps strictly along the *local positive $+Z$ axis*. Piles are anchored at their physical base ($Z_{\text{base}} = Z_{\text{top}} - L$) and swept along $+Z$, ensuring identical downward placement across Autodesk Revit, Solibri, and web IFC viewers.
2. **Polygonal Profile Lofting**: Pier caps are extruded along the longitudinal $X$-axis using `IfcArbitraryClosedProfileDef` to represent the trapezoidal hammerhead cross-section accurately in BIM.
3. **Spatial Hierarchy & Rebar Aggregation**: All components link to `IfcBuildingStorey`. Reinforcement elements aggregate under their respective concrete elements via `IfcRelAggregates`.
4. **Automatic BOQ Metrics**: Volumes ($m^3$), lengths ($m$), and steel weights ($\text{kg} = 7850 \cdot \pi r^2 L$) are calculated and attached via `IfcElementQuantity`.

---

## 6. Development Challenges & QA Solutions

During development and cross-platform verification between pythonOCC and BIM viewers, several subtleties were investigated and solved:
* **Challenge 1: IFC Pile Orientation**: pythonOCC permits $-Z$ axes for downward solids, whereas IFC4 interprets a negative local axis as an inverted frame. Fixed by switching to base-anchored $+Z$ extrusion.
* **Challenge 2: Centroidal Datum Alignment**: Fixed a vertical gap ($\approx 750\text{ mm}$) by correctly referencing the girder mid-web centroid origin ($Z = 0$) rather than the top flange.
* **Challenge 3: Support Layout Harmonization**: Synchronized support coordinate placement logic so that simply supported configurations ($N=2$) place piers at bridge bearing lines ($X = 0, L$) rather than interior span thirds.
* **Challenge 4: Pile Rebar Extraction**: Implemented explicit extraction loops for bored pile rebar rings and cages.

---

## 7. How to Run the Application & Tests

### Prerequisites
* Python 3.10+ in an environment with `pythonocc-core`, `PySide6`, and `ifcopenshell`.
* Recommended Conda environment: `osdagbridge-env`.

### 1. Launch the Desktop Application
```bash
# Full OsdagBridge application
python -m osdagbridge.desktop

# Or the 3D CAD Viewer window directly
python src/osdagbridge/desktop/ui/cad_3d.py
```

### 2. Run the Unit Test Suite (8 Tests)
```bash
python tests/unit/test_substructure.py
```

### 3. Run the Deep IFC Export Validation Script
```bash
python tests/unit/validate_ifc_export.py
```

---

## 8. Verification & Test Results

```
======================================================================
STARTING IFC SUBSTRUCTURE EXPORT VALIDATION
======================================================================
--- ELEMENT COUNTS BY IFC ENTITY TYPE ---
  IfcProject            : 1
  IfcSite               : 1
  IfcBuilding           : 1
  IfcBuildingStorey     : 1
  IfcBeam (Pier Cap)    : 1
  IfcColumn (Piers)     : 2
  IfcFooting (Pile Cap) : 1
  IfcPile (Bored Piles) : 4
  IfcReinforcingBar     : 186
  IfcElementQuantity    : 194
  IfcRelAssociatesMaterial : 194

--- REBAR AGGREGATION (IfcRelAggregates) ---
  Parent: 'Pier Shaft 1.1' -> Aggregates 186 children
  Parent: 'Pier Shaft 1.2' -> Aggregates 186 children

======================================================================
VALIDATION SUCCESSFUL: ALL ENTITIES, PLACEMENTS, MATERIALS & BOQ VERIFIED!
======================================================================
```
