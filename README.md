# OsdagBridge Substructure CAD & IFC Export Module

This module extends the **OsdagBridge** parametric bridge modeling framework with full 3D CAD geometry generation, PySide6/pythonOCC display rendering, and IFC4 BIM export for bridge substructure components (**piers**, **pier caps**, **pile caps**, **piles**, and **reinforcement cages**).

---

## 1. Directory & File Structure

The substructure components are organized within the existing modular `osdagbridge` package structure:

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
│   │   │       └── builder.py         # Rebar cages & grid mats (build_*_rebar)
│   │   └── foundation/
│   │       ├── pile_cap/
│   │       │   └── builder.py         # Rectangular footing block (build_pile_cap)
│   │       └── pile/
│   │           └── builder.py         # Bored cast-in-situ piles (build_piles)
│   │
│   ├── bridge_types/
│   │   └── plate_girder/
│   │       ├── dto.py                 # SubstructureParametersDTO & BridgeParametersDTO
│   │       └── cad_generator.py       # CAD generator pipeline (Step 12 wiring)
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
    ├── test_substructure.py           # Substructure unit test suite (8 tests)
    └── validate_ifc_export.py         # IFC export & ifcopenshell validation script
```

---

## 2. Component Specifications & Coordinate System

### Coordinate System
Per `GEMINI.md` conventions:
- **X-axis**: Longitudinal (along bridge span length $L$)
- **Y-axis**: Transverse (across deck width)
- **Z-axis**: Vertical (positive upward)
- **Origin $(0,0,0)$**: Centre of span at deck level. Substructure sits below $Z = 0$.

### Component Summary

| Component | Default Parameters (mm) | Geometry Primitive / Construction |
|---|---|---|
| **Pier Shaft** | `pier_diameter = 800`, `pier_height = 3000` | `BRepPrimAPI_MakeCylinder` on `gp_Ax2` aligned with +Z. Supports hollow shafts via `BRepAlgoAPI_Cut`. |
| **Pier Cap** | `top_width = 3000`, `bot_width = 1200`, `depth = 600`, `height = 600` | `BRepOffsetAPI_ThruSections` lofted between top and bottom rectangular wires along Y-Z. |
| **Pile Cap** | `len_x = 2200`, `len_y = 1200`, `depth = 600` | `BRepPrimAPI_MakeBox` centered under the pier column group. |
| **Piles** | $2 \times 2$ grid, `diameter = 400`, `length = 5000`, `spacing = 600` | Four downward cylinders (`gp_Ax2` with $-Z$ axis) extending below pile cap base. |
| **Rebar** | `main_dia = 16`, `tie_dia = 8`, `tie_spacing = 200`, `cover = 40` | Vertical cylinders arranged in a ring + horizontal torus tie rings (`BRepPrimAPI_MakeTorus`). Orthogonal grid mats for caps. |

---

## 3. How to Run the Application & Tests

### Prerequisites
- Python environment with `pythonocc-core`, `PySide6`, and `ifcopenshell` installed.
- Recommended Conda environment: `osdagbridge-env`.

### Running the Desktop Application / 3D Viewer
```bash
# Launch the full main desktop application
python -m osdagbridge.desktop

# Or launch the 3D CAD viewer window directly
python src/osdagbridge/desktop/ui/cad_3d.py
```

### Running the Unit Test Suite
```bash
python tests/unit/test_substructure.py
```

### Running the IFC Export Validation Script
```bash
python tests/unit/validate_ifc_export.py
```

---

## 4. IFC Export Implementation Details

The IFC4 export pipeline integrates substructure elements alongside the superstructure:

1. **Entity Class Mapping**:
   - Pier Shaft $\rightarrow$ `IfcColumn`
   - Pier Cap $\rightarrow$ `IfcBeam`
   - Pile Cap $\rightarrow$ `IfcFooting` (`PredefinedType="PAD_FOOTING"`)
   - Pile $\rightarrow$ `IfcPile` (`PredefinedType="BORED"`)
   - Rebar $\rightarrow$ `IfcReinforcingBar`

2. **Rebar Parent Aggregation**:
   - Rebar elements are aggregated under their parent concrete column element via `IfcRelAggregates` (`RelatingObject = Pier Column`, `RelatedObjects = [IfcReinforcingBar, ...]`).

3. **Material Assignment**:
   - `IfcMaterial` definitions created for concrete (`"M35"`) and steel (`"Fe500 Rebar Steel"`) and assigned via `IfcRelAssociatesMaterial`.

4. **BOQ Quantity Sets (`IfcElementQuantity`)**:
   - Concrete elements receive `Qto_*BaseQuantities` (`NetVolume` in $\text{m}^3$, `Length`/`Height` in m).
   - Rebar elements receive `Qto_ReinforcingBarBaseQuantities` (`Length` in m, `Weight` in kg calculated using steel density $7850 \text{ kg/m}^3$).

---

## 5. Known Limitations & Simplifications

1. **Geometric Rebar Representation**: Rebar is modeled geometrically as solid cylinders and tori for 3D visualization and BOQ estimation. It is not structurally simulated or verified against code lap-length or hook bend requirements.
2. **Simplified Hammerhead Pier Cap Lofting**: Pier cap chamfers and end cantilevers are modeled using a clean 2-wire `BRepOffsetAPI_ThruSections` loft between top and bottom rectangular profiles.
3. **Pier Cap Length Defaulting**: Pier cap length defaults to `pier_cap_top_width = 3000 mm` when explicit deck width is not supplied to the substructure module directly.
4. **Rebar Aggregation Parent**: In the IFC file, rebar elements are aggregated under `IfcColumn` (pier shaft). For full BIM granularity, future revisions can break down cap and pile rebar into individual parent `IfcBeam` / `IfcFooting` / `IfcPile` aggregations.
