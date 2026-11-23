# OsdagBridge

OsdagBridge is a modular, shared-core software plugin for the analysis and design of steel bridges within the Osdag ecosystem.  
It supports desktop (PySide6), web (Django + React), and CLI interfaces through a unified Python core.

The system currently supports:
- Plate Girder Bridges  
 

Additional bridge types can be added through the plugin architecture.

---

## Key Features

### Shared Core Architecture
All numerical logic and I/O are implemented once in `osdagbridge.core`.  
The desktop GUI, web app, and CLI all reuse the same core for consistent behavior.

### Modular Bridge-Type System
Each bridge type includes:
- DTO (input model schema)
- Initial sizing routines
- Structural analysis configuration
- Design and code-check modules
- CAD geometry generation
- Report generation utilities

### Reusable Bridge Components
Common structural elements are defined in `bridge_components/`:
- Girders  
- Decks  
- Crash barriers  
- Pedestals  
- Piers  
- Foundations  
- Piles and pile caps  

Components are shared across multiple bridge types.

### Multi-Solver Analysis Support
Multiple analysis backends are supported:
- Native lightweight FEM solver  
- OpenSeesPy  
- OspGrillage  

Solvers are switchable at runtime via adapters.

### Integrated Indian Standards
Included under `core/utils/codes/`:
- IRC:6–2017  
- IRC:22–2015  
- IRC:24–2010  

These modules provide load models, combinations, material factors, and code checks.

---

## Project Structure

```
OsdagBridge/
├── docs/
├── examples/
├── tests/
└── src/
    └── osdagbridge/
        ├── core/              # Analysis, design, IO, solvers, codes
        ├── bridge_types/      # Plate girder, box girder, truss
        ├── bridge_components/ # Reusable components
        ├── cli/               # Command-line interface
        ├── desktop/           # PySide6 GUI
        └── web/               # Django + React web stack
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/osdag-admin/OsdagBridge.git
cd OsdagBridge
```

Install in editable mode:

```bash
pip install -e .
```

---

## Usage

### Command-Line Interface

Run an analysis:

```bash
osdagbridge analyze project.yaml --solver native
```

Generate a report:

```bash
osdagbridge report project.yaml report.pdf
```

### Desktop Application

```bash
python -m osdagbridge.desktop
```

### Web Application

Backend:

```bash
python src/osdagbridge/web/backend/manage.py runserver
```

Frontend:

```bash
cd src/osdagbridge/web/frontend
npm install
npm start
```

---

## FOSSEE IIT Bombay Screening Task Enhancements (Winter Internship 2026)

This repository contains the complete implementation, automated tests, and documentation for the **FOSSEE IIT Bombay Winter Internship 2026 Screening Task** for the **OsdagBridge** project across three core subtasks.

### Task I: Interactive 2D CAD Parameter Editing
Implements dynamic double-click parameter editing directly within the 2D CAD canvas (Cross-Section View and Top View) while maintaining bidirectional synchronization with the UI input dictionaries:
- **Editable Parameters**:
  - `Carriageway Width` (`KEY_CS_CARRIAGEWAY_WIDTH`)
  - `Girder Spacing` (`KEY_CS_GIRDER_SPACING`)
  - `Deck Thickness` (`KEY_CS_SLAB_THICKNESS`)
  - `Span Length` (`KEY_SPAN_LENGTH`)
- **Locked Derived Parameters (Read-Only)**:
  - `Overhang` (`KEY_TS_DECK_OVERHANG`)
  - `Overall Bridge Width` (`KEY_CS_OVERALL_WIDTH`)
  - `Bracing Spacing` (`KEY_BRACING_SPACING`)
- **Interaction Model**: Double-clicking an editable dimension text label overlays an in-place `QLineEdit` widget styled to match the label. Commits are accepted on pressing `Enter` or clicking outside the widget; edits can be canceled via `Escape`.
- **Validation**: Reuses `BridgeInputValidator` to enforce numeric positivity, non-zero values, and engineering constraints. Reverts safely without geometry corruption if validation fails.
- **Synchronization**: Automatically updates the central input dictionary, reflects changes across the basic input dock widgets (with signals temporarily blocked to avoid loops), triggers `solve_extend_basic_input_dict`, and redraws both CAD views with refreshed dimensions.

### Task II: Additional Inputs Validation and State Management
Prevents accidental data loss and ensures parameter integrity in the `AdditionalInputsDialog`:
- **Unsaved Changes Tracking (`self.is_modified`)**: Dynamically tracks changes across all active tabs (Geometric Parameters, Loading, Support & Bearing, Diaphragm & Bracing, Sizing) by intercepting user input signals (`textChanged`, `currentIndexChanged`, `toggled`). Programmatic population and initial loading safely bypass dirty tracking.
- **Pre-Save Custom Validation**: Intercepts the Save button to iterate over all active parameter widgets. Whenever a parameter is set to `Custom`, its associated custom input field is validated to ensure it is not empty or purely whitespace. If invalid, saving is blocked and an error dialog displays:
  ```
  "Error: The custom value for '[Parameter Name]' cannot be empty."
  ```
  Uses canonical parameter keys from `osdagbridge/core/utils/common.py` without hardcoded strings.
- **Close Event Interception (`closeEvent`)**: When closing with unsaved changes (`is_modified == True`), prompts a confirmation dialog offering **Discard Changes** (reverts working dictionary to saved state and closes) or **Cancel** (keeps dialog open to resume editing). If saved or unmodified, the dialog closes immediately without prompting.

### Task III: Transverse Member Result Plotting
Extends the post-analysis Matplotlib visualization from 3D longitudinal girders to complete 2D engineering response plots for transverse structural members:
- **Member Type Selection**: Adds a `Member Type` dropdown in the Output Dock allowing selection between:
  - `Longitudinal Members`
  - `End Diaphragms` (End Diaphragm 1 at start $x=0$, End Diaphragm 2 at end $x=L$)
  - `Cross Bracings` (grouped across all intermediate $x$ bracing stations)
- **All 9 Engineering Components Supported**:
  - **Shear / Axial Forces**: $F_x$ (Axial), $V_y$ (Major Shear), $V_z$ (Minor Shear) in $\text{kN}$
  - **Torsional / Bending Moments**: $T_x$ (Torsion), $M_y$ (Minor Bending), $M_z$ (Major Bending) in $\text{kNm}$
  - **Displacements**: $D_x$ (Longitudinal), $D_y$ (Vertical Deflection), $D_z$ (Transverse) in $\text{mm}$
- **2D Diagram Styling**: High-contrast engineering plots showing continuous response across transverse member length, vertical dashed lines indicating girder crossing locations ($G_1, G_2, \ldots, G_n$), zero baseline, callout annotations for maximum and minimum values, and an interactive `SummaryOverlay` HUD table.
- **Zero Regressions**: Preserves 3D camera controls, isometric viewing, and NavCube synchronization for longitudinal girder plots.

---

## Testing

Run the complete test suite including the FOSSEE enhancement test suite:

```bash
pytest -v
```

To run individual enhancement test modules:

```bash
# Task I: 2D CAD Interactive Editing
pytest tests/test_cad_interactive_edit.py -v

# Task II: Additional Inputs Validation & State Management
pytest tests/test_additional_inputs_validation.py -v

# Task III: Transverse Member Result Plotting
pytest tests/test_transverse_plotting.py -v
```

Continuous integration runs automatically through GitHub Actions (`.github/workflows/ci.yml`).

---

## Development Guidelines

### Key Code Locations
- Core logic: `src/osdagbridge/core/`
- Codes & standards: `src/osdagbridge/core/utils/codes/`
- Bridge types: `src/osdagbridge/bridge_types/`
- Components: `src/osdagbridge/bridge_components/`
- CLI: `src/osdagbridge/cli/`
- Desktop GUI: `src/osdagbridge/desktop/`
- Web backend/frontend: `src/osdagbridge/web/`

### Contribution Workflow
1. Fork the repository  
2. Create a feature branch  
3. Ensure all tests pass (`pytest`)  
4. Submit a pull request

---

## Acknowledgements

OsdagBridge is part of the Osdag project, promoting open-source tools for steel design education, research, and practice.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
