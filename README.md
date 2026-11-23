# OsdagBridge: Parametric Substructure and IFC Integration

## What was added
Parametric pythonOCC models of the bridge substructure (mm, X = span, Y = deck width, Z = up):
- Pier (circular column), pier cap (trapezoidal/hammerhead), pile cap (rectangular), piles (2x2 grid)
- Internal reinforcement (main bars and transverse bars/hoops, 40 mm cover)

## File structure
- `core/bridge_components/sub_structure/params.py` - parametric dimensions
- `core/bridge_components/sub_structure/common.py` - shared OCC helpers and the `Part` record
- `core/bridge_components/sub_structure/pier/builder.py` - piers
- `core/bridge_components/sub_structure/pier_cap/builder.py` - pier cap
- `core/bridge_components/foundation/pile_cap/builder.py` - pile cap
- `core/bridge_components/foundation/pile/builder.py` - piles
- `core/bridge_components/sub_structure/reinforcement/` - rebar
- `core/bridge_components/sub_structure/assembly.py` - `build_bridge_substructure`, `group_parts`
- `core/bridge_types/plate_girder/cad_generator.py` - passes substructure shapes and parts into `model_data`
- `desktop/ui/cad_3d.py` - Substructure and Rebar checkboxes; concrete drawn semi-transparent
- `core/ifc_export_bridge/bridge_ifc_generator.py` - IFC generator (accepts `substructure_parts`)
- `core/ifc_export_bridge/substructure_ifc.py` - `add_substructure_to_ifc` (Part to IFC elements)
- `core/ifc_export_bridge/export_ifc_handler.py` - reads `substructure_parts` from `model_data`

## Run
conda activate osdagbridge-env
cd src
python -m osdagbridge.desktop

## Status
- 3D display of substructure with semi-transparent concrete and visible rebar: working.
- Substructure IFC content verified in a test file: 4 IfcColumn, 2 IfcBeam, 4 IfcFooting, 16 IfcPile, 980 IfcReinforcingBar (IFC4).
- File > Save 3D CAD Model > .ifc from the GUI: see report (known issue at submission time).