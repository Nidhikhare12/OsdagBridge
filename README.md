# OsdagBridge

OsdagBridge is a modular, shared-core software plugin for the analysis and design of steel bridges within the Osdag ecosystem.  
It supports desktop (PySide6), web (Django + React), and CLI interfaces through a unified Python core.

> **FOSSEE OsdagBridge Screening Task Submission**  
> **Contributor:** Chirag Yadav  
> **Task:** Substructure Geometry Generation & IFC Integration 

---

## Task Implementation Details (Screening Task)

This fork extends the existing OsdagBridge repository by implementing a fully parametric, 3D CAD substructure using `pythonOCC`. The integration includes the generation of physical concrete geometries along with their internal steel reinforcement (rebar), successfully routed through the main GUI and connected to the `ifcopenshell` exporter.

### Key Features Developed
* **Parametric Substructure Geometry:** Developed `builder.py` modules for the Pier (circular), Pier Cap (hammerhead), Pile Cap, and 4-Pile Group.
* **Internal Reinforcement Visualization:** Generated 16mm longitudinal steel rebar inside all concrete components with strict material property mapping (Concrete opacity = 0.35).
* **Pipeline Integration:** Injected routing logic into `cad_generator.py` to seamlessly join the new substructure geometry with the existing superstructure dictionary.
* **BIM Export:** Wired the new component dictionaries to `bridge_ifc_generator.py`, mapping the new arrays to `IfcColumn` and `IfcSlab` to enable successful `.ifc` file exports.

### Included Files & Modifications
1. `src/osdagbridge/core/bridge_components/sub_structure/...` *(Added parametric geometry in respective `builder.py` files)*
2. `src/osdagbridge/core/bridge_types/plate_girder/cad_generator.py` *(Modified for CAD routing and UI color/visibility)*
3. `standalone_substructure_viewer.py` *(Added at root as a pure-pythonOCC viewer for isolated geometry testing)*
4. `bridge_ifc_generator.py` *(Modified IFC wrapper for substructure export)*

---

## Original Project Features

### Shared Core Architecture
All numerical logic and I/O are implemented once in `osdagbridge.core`.  
The desktop GUI, web app, and CLI all reuse the same core for consistent behavior.

### Reusable Bridge Components
Common structural elements are defined in `bridge_components/`:
- Girders, Decks, Crash barriers, Pedestals
- Piers, Foundations, Piles and pile caps (Implemented via this task)

---

## Installation

Clone the repository and install dependencies (requires `pythonocc-core` and `ifcopenshell`):

```bash
git clone [https://github.com/osdag-admin/OsdagBridge.git](https://github.com/osdag-admin/OsdagBridge.git)
cd OsdagBridge
conda activate osdagbridge-env
pip install -e .
```

---

## Usage

### Desktop Application (GUI with Substructure View)
```bash
python -m osdagbridge.desktop
```
*Click `Design`, toggle the bridge view, and select `File -> Save 3D CAD Model` to export the complete `.ifc` file.*

### Standalone Geometry Viewer (Task Specific)
```bash
python standalone_substructure_viewer.py
```
*Bypasses the UI entirely to strictly render the new pythonOCC substructure and internal rebar.*

### Command-Line Interface
```bash
osdagbridge analyze project.yaml --solver native
osdagbridge report project.yaml report.pdf
```

---

## Environment & Troubleshooting Notes (macOS ARM64)

During development on an Apple Silicon (M-series) environment, several upstream repository issues were identified and resolved to successfully execute the task:
1. **Missing `osdag_core`:** The main steel-connection calculation engine was missing from the provided environment. A mock `osdag_core` initialization script was temporarily created to bypass the KeyError and allow the 3D pipeline to run.
2. **NavCube UI Crash:** An `AttributeError` (`'_FakeSignal' object has no attribute 'size'`) triggered in `custom_3dviewer.py` on macOS. An early return was injected into the `_resize_navcube` method to bypass the broken pyqt5 resize event and stabilize the 3D window.
3. **Missing `ifcopenshell`:** Forced installation of this missing Conda dependency was executed to enable the IFC export wrapper.

---

## Testing

Run the complete test suite:
```bash
pytest -q
```
Continuous integration runs automatically through GitHub Actions (`.github/workflows/ci.yml`).

---

## License
This project is licensed under the MIT License.  
See the `LICENSE` file for full details.