# Project rules for OsdagBridge substructure task

- This is a modular PyQt/PySide + pythonOCC (pythonocc-core) desktop app.
- Geometry for each bridge component lives in that component's own
  `builder.py` under the relevant folder in `core/`. Match the existing
  superstructure components (cross bracing, plate girder) exactly in style:
  same function signatures, same docstring format, same return type
  (a single TopoDS_Shape or TopoDS_Compound per component), same units (mm).
- Do not modify superstructure builder.py files. Only add code to the empty
  substructure builder.py files, and only touch cad_generator.py / cad_3D.py /
  the IFC wrapper to wire in the new components.
- All new dimensions must be named module-level variables or function
  parameters with sensible defaults — never magic numbers inline.
- Coordinate system: X = longitudinal (span), Y = transverse (deck width),
  Z = vertical. Origin = center of span at deck level. Substructure sits
  below Z = 0.
- Before writing any geometry code, find and read the existing superstructure
  builder.py, cad_generator.py, and the IFC export module in full, and mimic
  their patterns rather than introducing new ones.
- Every new function needs a docstring stating units and what each parameter
  controls.
- After each component is added, run the app (`python -m osdagbridge.desktop`)
  and confirm it renders before moving to the next component.
