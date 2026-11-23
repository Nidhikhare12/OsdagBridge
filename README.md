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

## Report generator enhancements (FOSSEE OsdagBridge Winter Internship 2026)

The report-generation implementation has been refactored around
`src/osdagbridge/core/reports/styles.py`, which owns the shared LaTeX geometry,
header/footer layout, typography, table spacing, brand colors, and reusable
longtable formatting. Chapter tables use repeated first-page/continuation
headers. Chapters 2, 4, 5, 7 and 8 include longtable structures; Chapter 3 uses
the shared `format_longtable` helper for load tables.

Dynamic chart generation is in `src/osdagbridge/core/reports/charts.py`.
Utilization charts use available design demand/capacity or reported efficiency
values and a UR=1.0 limit. Quantity charts only render when the corresponding
BOM fields are present. Missing end-diaphragm quantities and missing design
results are not estimated or copied from other components. Chapter 3 vehicle
and footway live-load reporting is separated; values that cannot be derived
from the selected vehicle, span, lane, or GUI inputs are shown as unavailable
rather than silently substituted with assumed values.

The repository contains the original `reports/Report_Before.pdf`, its TeX
source, and baseline screenshots. A new `Report_After.pdf` is intentionally not
included: this archive contains no captured live bridge-design session/output
that can be used to create a genuine after-report. Creating one from guessed or
fabricated structural results would be misleading. Generate the after-report
from the OsdagBridge GUI after running a valid bridge design; the enhanced
report generator will consume that run's real inputs and outputs.

See `reports/Technical_Changes_Document.pdf` for the implementation summary
and verification results. The focused regression tests are in
`tests/unit/test_report_enhancements.py`.
