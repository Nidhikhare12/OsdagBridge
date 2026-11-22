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

## Testing

Run the complete test suite:

```bash
pytest -q
```

Continuous integration runs automatically through GitHub Actions (`.github/workflows/test.yml`).

---

## LaTeX Report Generator Enhancements

This repository contains comprehensive enhancements to the OsdagBridge PDF Report Generator module:
- **Centralized Style System (`styles.py`)**: Single source of truth for document geometries, color palettes (`osdagGreen`, `osdagBlue`), table paddings, and rule widths.
- **Repeated Multi-Page Table Headers**: Reusable LaTeX `longtable` header generator (`build_longtable_header()`) with `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot` across multi-page tables.
- **Layout & Footer Clearance Fixes**: 18 mm footskip clearance barrier and `\needspace{6\baselineskip}` constraints eliminating footer bleed (e.g. Page 30 / G4 row).
- **Chapter 3 Load Table Refactoring**: Clean separation into Table 3.3 (Vehicular Live Loads with dynamic vehicle UI selections, impact factors, braking loads) and Table 3.4 (Pedestrian / Footway Live Load).
- **Chapter 5.5 UR Summary Visualizations**: Programmatic Matplotlib bar charts plotting Utilization Ratios against a distinct red dashed reference line at UR = 1.0.
- **Chapter 7 Material BOQ Visualizations**: Programmatic Matplotlib bar charts summarizing Structural Steel tonnage breakdown (MT) and Concrete volume ($m^3$) vs Reinforcement Steel weight (MT).

### Running Report Enhancement Tests
```powershell
cd C:\Users\Asus\OsdagBridge
$env:PYTHONPATH="src"
pytest -v tests/
```

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
