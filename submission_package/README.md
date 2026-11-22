# OsdagBridge Screening Task Submission Package

**Candidate Name:** Aryan Vyas  
**GitHub Profile:** [@Aaryanvyas](https://github.com/Aaryanvyas)  
**Target Repository:** [Nidhikhare12/OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge)  
**Submitted Pull Request:** [PR #196: Fix report table column alignment and LaTeX formatting](https://github.com/Nidhikhare12/OsdagBridge/pull/196)  
**Task Topic:** LaTeX Report Generator Refactoring & Visual Enhancements  

---

## 📁 Package Contents

This submission package contains all deliverables, generated comparison reports, technical documentation, source code, and automated tests:

```text
submission_package/
├── Report_Before.pdf              # Original baseline report output
├── Report_After.pdf               # Enhanced 49-page design report reflecting all fixes
├── TECHNICAL_REPORT.md            # Detailed technical report documenting architecture and fixes
├── DEMO_VIDEO_GUIDE.md            # Step-by-step storyboard and recording guide for video demo
├── README.md                      # Overview and instructions (this file)
├── test_execution_log.txt         # 100% passing pytest output log across 12 test cases
├── styles.py                      # Centralized styling module (Single Source of Truth)
├── report_charts.py               # Automated Matplotlib visualization generators
├── chap2.py                       # Refactored Chapter 2 source with column fixes
├── chap3.py                       # Refactored Chapter 3 source with separated load tables
├── chap5.py                       # Refactored Chapter 5 with UR chart & repeated headers
├── chap7.py                       # Refactored Chapter 7 with BOQ charts & repeated headers
├── report_generator.py            # Central reporting pipeline orchestration
├── test_report_enhancements.py    # Automated test suite verifying all 6 task requirements
├── test_report_tables.py          # Regression test verifying table column alignment
└── latex_evidence/
    ├── table_before.tex           # Isolated LaTeX snippet demonstrating original bugs
    └── table_after.tex            # Isolated LaTeX snippet demonstrating corrected tables
```

---

## 🚀 Quickstart: Running the Automated Test Suite

From the root of the repository:

```bash
# On Windows PowerShell:
$env:PYTHONPATH="src"
pytest -v tests/

# On Linux / macOS / Bash:
PYTHONPATH=src pytest -v tests/
```

### Expected Output (12/12 Passed)
```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1
collected 12 items

tests/integration/test_api_plate_girder.py::test_api_placeholder PASSED  [  8%]
tests/integration/test_cli_plate_girder.py::test_cli_placeholder PASSED  [ 16%]
tests/unit/test_analyser.py::test_placeholder_analyser PASSED            [ 25%]
tests/unit/test_designer.py::test_placeholder_designer PASSED            [ 33%]
tests/unit/test_io.py::test_placeholder_io PASSED                        [ 41%]
tests/unit/test_report_enhancements.py::test_styles_configuration PASSED [ 50%]
tests/unit/test_report_enhancements.py::test_repeated_headers_structure PASSED [ 58%]
tests/unit/test_report_enhancements.py::test_chapter3_load_tables_separation PASSED [ 66%]
tests/unit/test_report_enhancements.py::test_overall_ur_chart_creation PASSED [ 75%]
tests/unit/test_report_enhancements.py::test_boq_charts_creation PASSED  [ 83%]
tests/unit/test_report_enhancements.py::test_chapter7_figures_embed PASSED [ 91%]
tests/unit/test_report_tables.py::test_bracing_tables_have_matching_column_counts PASSED [100%]

============================= 12 passed in 1.38s ==============================
```

---

## 🛠 Summary of Core Enhancements

1. **Repeated Table Headers Across Page Breaks:** Standard `longtable` continuation headers (`\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`) generated via `build_longtable_header()` in `styles.py`.
2. **Layout & Footer Spacing Fixes:** Re-engineered geometry with `bottom=30mm` and `footskip=18mm`, completely preventing table rows from bleeding into the footer rule on Page 30 and elsewhere.
3. **Chapter 3 Load Table Refactoring:** Vehicle Live Loads and Footpath Live Loads separated into two distinct tables with clear unit columns and dynamic UI vehicle selection.
4. **Section 5.5 UR Bar Chart:** Programmatic Matplotlib bar chart plotting element Utilization Ratios with a distinct red dashed line at $\text{UR} = 1.0$.
5. **Chapter 7 Material Quantity Bar Charts:** Automated bar charts visualizing structural steel tonnage breakdown and material take-off comparisons.
6. **Centralized Style System (`styles.py`):** Authoritative single source of truth for color palettes, typography, table layouts, and margins.
7. **Resilient Compiler Integration:** Headless `-disable-installer` execution and `\IfFileExists` package fallbacks ensure failure-free compilation on any evaluator machine.
