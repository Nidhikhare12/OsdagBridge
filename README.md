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

## Report Engine (FOSSEE Screening Task Refactoring)

This fork includes a major architectural refactoring of the LaTeX design report generation subsystem, completed for the **FOSSEE Osdag Winter Internship 2026 Screening Task** by **Pranav Chaudhari** (`Pranav-chaudhari-2006`).

### Core Enhancements (Requirements R1–R6)

1. **R1 (Repeated Table Headers)**: Migrated all 54 tables across Chapters 1–8 and the Executive Summary to `ReportTable` (`latex/tables.py`), built upon PyLaTeX `LongTable`. Headers repeat cleanly across all page breaks (`\endfirsthead` / `\endhead`).
2. **R2 (Footer Overlap Elimination)**: Rebuilt document geometry (`margin_bottom=2.8cm`, `footskip=38pt`, `headheight=20pt`, `headsep=14pt`) and reserved software default note space in `latex/document.py`. Automated character bounding-box linting (`qa/pdf_lint.py`) verified 0 footer overlaps across all 55 pages (down from 157 baseline defects).
3. **R3 (Load Restructure)**: Separated Chapter 3 loads into distinct tables via `data/live_loads.py`: Table 3.3 *Vehicular Live Loads (IRC 6:2017)* with 2-level headers and Table 3.4 *Footpath Live Load*.
4. **R4 (Utilization Ratio Bar Charts)**: Implemented `data/utilization.py` and `charts/utilization_chart.py`. Section 5.5 now embeds an Overall UR Summary bar chart (grouped by structural element) and a Per-Girder Governing UR chart, both featuring a red dashed limit line at $UR = 1.0$ and greyscale-legible hatching for failing checks.
5. **R5 (Material Quantity Bar Charts)**: Implemented `data/quantities.py` and `charts/quantity_charts.py`. Chapter 7 now embeds a Structural Steel Tonnage Breakdown bar chart and a side-by-side dual-panel visualization of Concrete Volume ($m^3$) vs. Reinforcement Steel Weight (MT).
6. **R6 (Centralized Style System)**: Created `core/reports/theme.py` as the single source of truth for colors, typography, paddings, and page geometry, eliminating all inline hardcoded styling.

### Architecture Diagram

```
src/osdagbridge/core/reports/
├── theme.py                  # Single source of truth for styles, colors, dimensions
├── report_generator.py       # Orchestrator and ReportDataBridge
├── data/                     # Pure data extraction adapters (zero calculation logic)
│   ├── live_loads.py         # Live load dataclasses and extractors (R3)
│   ├── utilization.py        # URRecord and design check extractors (R4)
│   └── quantities.py         # QuantitySummary extractors (R5)
├── charts/                   # Headless Matplotlib (Agg) chart generators
│   ├── base.py               # Shared chart styles, figure setup, DPI export
│   ├── utilization_chart.py  # Overall and per-girder UR plots (R4)
│   └── quantity_charts.py    # Steel tonnage and concrete/rebar plots (R5)
├── latex/                    # PyLaTeX layout and markup emitters
│   ├── document.py           # Geometry, packages, preamble, title, TOC
│   ├── tables.py             # ReportTable, KeyValueTable, SimpleTable (R1)
│   ├── figures.py            # Figure and placeholder embedders
│   ├── text.py & escape.py   # Safe TeX sanitizers and status badges
│   └── compile.py            # Headless pdflatex runner with rerun detection
├── qa/                       # Automated quality assurance linters
│   ├── pdf_lint.py           # Bounding-box footer overlap scanner (pdfplumber)
│   └── tex_lint.py           # TeX source linter for tables and styles
└── chap1.py ... chap9.py     # Pure presentation chapter renderers
```

### Running Headless Report Generation

Generate a complete design report from a saved design fixture without launching the GUI:

```bash
python -m osdagbridge.core.reports.cli --fixture tests/fixtures/reports/baseline_default.json --out deliverables --stem Report_After
```

### Running Verification Tests

Run the full automated test suite (37 tests across unit, integration, layout, lint, and calculation parity):

```bash
pytest -q
```

To run only the PDF and TeX linters:

```bash
pytest -q tests/unit/test_layout.py tests/unit/test_tex_lint.py
```

### Adding or Customizing a Theme

To create a custom color palette or page layout, define a new `Theme` in `core/reports/theme.py`:

```python
from osdagbridge.core.reports.theme import Theme, Palette, PageTheme, set_active_theme

dark_theme = Theme(
    name="monochrome",
    palette=Palette(brand="000000", secondary="333333"),
    page=PageTheme(margin_left_cm=2.5, margin_right_cm=2.5),
)
set_active_theme(dark_theme)
```

---

## Acknowledgements

OsdagBridge is part of the Osdag project, promoting open-source tools for steel design education, research, and practice.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
