# Technical Changes Document: OsdagBridge LaTeX Report Enhancements

**Project:** OsdagBridge (Osdag Bridge Design Plugin)  
**Task:** LaTeX Report Generator Refactoring & Visual Enhancements  
**Screening Task:** FOSSEE Winter Internship 2026  
**Candidate:** Chaitanya Phatak (<chaitanyaphatak20@gmail.com>)  
**Date:** November 2026  

---

## 1. Overview

This document details the modifications made to the OsdagBridge design report generation module (`osdagbridge/core/reports/`) to resolve layout shortcomings, ensure code compliance, and improve design visualization.

The key objectives addressed are:
1. **Repeated Table Headers (`\endfirsthead` / `\endhead`):** Every multi-page calculation table across all chapters now repeats column headers on continuation pages.
2. **Page Margin and Footer Collision Remediation:** Clean page geometry (`footskip=14mm`) and removal of negative vertical spacing in footers prevent text and table rules from overlapping page numbers.
3. **IRC:6 Compliant Load Tabulation:** Separation of vehicle live loads and footpath loads into distinct tables, with full multi-column braking force representation per IRC:6 Clause 204/208.
4. **Governing Utilization Ratio Summary Chart:** Bar chart in Section 5.5 showing governing DCR per bridge component with a distinct dashed line at the code limit of $UR = 1.0$.
5. **Bill of Quantities Visualization:** Material take-off bar charts in Chapter 7 displaying structural steel tonnage breakdown and concrete volume versus reinforcement steel.
6. **Centralized Styling Module (`styles.py`):** Single source of truth for color palette, geometry, table padding, and LaTeX generation helpers.

---

## 2. Technical Scope & Implementation Details

### 2.1 Multi-Page Table Header Repetition (Chapters 2–8)
* **Issue:** Calculation tables spanning multiple pages did not repeat column headers on subsequent pages, making multi-page outputs difficult to navigate during design review.
* **Root Cause:** Tables were declared as `\begin{longtable}` but lacked standard continuation blocks (`\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`). In addition, some tables in Chapter 2 and Chapter 8 used fixed `\begin{table}` wrappers that do not break across pages.
* **Solution:**
  - Implemented `build_longtable_header()` in `styles.py` to standardize table headers:
    - Primary header: `\caption{...}\label{...} \\ \hline <Headers> \\[6pt] \hline \endfirsthead`
    - Continuation header: `\multicolumn{N}{c}{\small\textit{<Caption> (Continued)}} \\[4pt] \hline <Headers> \\[6pt] \hline \endhead`
    - Footer transition: `\hline \multicolumn{N}{r}{\small\textit{Continued on next page...}} \\ \endfoot`
    - Final closing rule: `\hline \endlastfoot`
  - Converted all 56 tables across `chap2.py`, `chap3.py`, `chap4.py`, `chap5.py`, `chap7.py`, and `chap8.py` to `longtable` with continuation headers.

### 2.2 Margin & Footer Collision Fixes
* **Issue:** On dense calculation pages (such as girder checks in Chapter 5), table rows collided directly with the footer divider rule and page numbering.
* **Root Cause:**
  1. Default 1-inch margins with unconstrained `footskip` provided insufficient clearance (~30pt) for multi-line footers.
  2. The footer definition in `report_generator.py` applied negative vertical shifts (`\vspace*{-20pt}`) inside `\footrule`, pulling the footer upwards into the body text.
* **Solution:**
  - Centralized document geometry in `styles.py`:
    ```latex
    \usepackage[a4paper, top=25mm, bottom=28mm, left=20mm, right=20mm, headheight=15mm, headsep=7mm, footskip=14mm]{geometry}
    ```
  - Removed negative `\vspace*` offsets in `\fancypagestyle{main}`.
  - Added vertical page threshold buffers via `needspace`:
    ```latex
    \BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}
    ```
  - Standardized cell vertical padding (`\arraystretch=1.12`, `\extrarowheight=0.8pt`, `\tabcolsep=6pt`).

### 2.3 Load Table Refactoring per IRC:6-2017 (Chapter 3)
* **Issue:** Vehicle live loads and footpath pedestrian loads were combined into a single flat table lacking braking force details and eccentricity values.
* **Solution:**
  - Separated into two distinct tables:
    - **Table 3.3a: Vehicle Live Loads:** Grouped multi-column schema per IRC:6 Clause 204:
      `[Vehicle Class | Total Load (kN) | Impact Factor | Braking Load (Considered? | Value (kN) | Eccentricity (m))]`
    - **Table 3.3b: Footway Live Load:** Footpath width, pedestrian intensity ($\text{kN/m}^2$ per Clause 206.1), and applied reduction factors.
  - Populates dynamically based on vehicle classes selected in the UI (IRC Class A, 70R Wheeled/Tracked/Bogie, Class AA, Class SV, Class Fatigue, and user-defined vehicles).
  - Evaluates dynamic impact factors per IRC:6 Clause 208 based on bridge span length.

### 2.4 Governing Utilization Ratio Visualization (Section 5.5)
* **Issue:** Section 5.5 presented design check results purely as raw numbers without an immediate visual indicator of governing elements.
* **Solution:**
  - Implemented `generate_ur_summary_chart()` in `charts.py`.
  - Generates a horizontal bar chart plotting governing Utilization Ratios ($UR = \text{Demand} / \text{Capacity}$) across main components:
    - Steel Plate Girders (G1, G2, G3...)
    - Concrete Deck Slab
    - Cross Bracing
    - End Diaphragms
  - Added a distinct dashed red threshold line at $UR = 1.0$ (`Design Capacity Limit`).
  - Bars are dynamically colored: Green (`#15803D`) for pass ($UR \le 1.0$), Amber (`#B45309`) for warning ($0.90 \le UR \le 1.0$), and Red (`#B91C1C`) for fail ($UR > 1.0$).
  - Embedded figure directly into Section 5.5 before Table 5.22.

### 2.5 Material Take-off Visualizations (Chapter 7)
* **Issue:** Bill of quantities in Chapter 7 lacked graphical representation of component distributions.
* **Solution:**
  - Implemented two Matplotlib rendering functions in `charts.py`:
    1. `generate_material_steel_chart()`: Horizontal bar chart showing structural steel tonnage by component (Girders, Cross Bracing, End Diaphragms, Shear Connectors) with percentage contributions.
    2. `generate_concrete_vs_rebar_chart()`: Comparative bar chart comparing concrete volume ($\text{m}^3$) against reinforcement steel weight (MT).
  - Embedded both figures beneath the quantities table in Chapter 7.

### 2.6 Centralized Styling Architecture (`styles.py`)
* **Issue:** Style attributes, colors, and table settings were hardcoded across multiple chapter scripts.
* **Solution:**
  - Created `osdagbridge/core/reports/styles.py` as the centralized source of styling:
    - Palette: `COLOR_OSDAG_GREEN` (`#91B014`), status colors (`COLOR_PASS`, `COLOR_WARN`, `COLOR_FAIL`), and neutral tones.
    - Document metrics: `GEOMETRY_OPTIONS`, table padding, and spacing rules.
    - Helper generators: `get_latex_color_definitions()`, `get_table_environment_settings()`, `get_column_types()`, and `build_longtable_header()`.
  - All chapter modules import styling definitions directly from `styles.py`.

---

## 3. Files Modified & Created

| File | Status | Description |
|:---|:---:|:---|
| `src/osdagbridge/core/reports/styles.py` | **New** | Centralized styling definitions, geometry constants, and LaTeX table builders. |
| `src/osdagbridge/core/reports/charts.py` | **New** | Programmatic Matplotlib chart generation (UR summary, steel breakdown, concrete vs rebar). |
| `src/osdagbridge/core/reports/chap2.py` | **Modified** | Converted tables to `longtable`; added `\endfirsthead`/`\endhead` to all 12 tables. |
| `src/osdagbridge/core/reports/chap3.py` | **Modified** | Separated vehicle and footway tables; added IRC:6 6-column braking schema and repeated headers on all 8 tables. |
| `src/osdagbridge/core/reports/chap4.py` | **Modified** | Added repeated headers to all 3 analysis tables. |
| `src/osdagbridge/core/reports/chap5.py` | **Modified** | Added repeated headers to all 30 design check tables; embedded UR summary chart in Section 5.5. |
| `src/osdagbridge/core/reports/chap7.py` | **Modified** | Added repeated headers to BoQ table; embedded steel tonnage and concrete vs rebar charts. |
| `src/osdagbridge/core/reports/chap8.py` | **Modified** | Converted reference tables to `longtable` with repeated headers. |
| `src/osdagbridge/core/reports/executive_summary.py` | **Modified** | Added defensive fallback when optional FEM package (`openseespy`) is absent. |
| `src/osdagbridge/core/reports/report_generator.py` | **Modified** | Wired centralized preamble, chart generation pipeline, and relative asset handling. |
| `src/osdagbridge/core/reports/__init__.py` | **Modified** | Exported styling and chart functions. |
| `tests/unit/test_report_enhancements.py` | **New** | Automated unit test suite covering all 6 deliverables (9/9 passed). |

---

## 4. Verification and Generated Reports

### Unit Test Execution
```powershell
$env:PYTHONPATH="src"
python -m unittest tests/unit/test_report_enhancements.py
```
**Result:** `Ran 9 tests in ~13s — OK` (100% pass rate).

### Report Comparison (`reports/` directory)
The generated outputs for verification before and after refactoring are located in the `reports/` folder:

1. **`Report_Before.pdf` / `Report_Before.tex` (Original Output):**
   - 42 pages, 226.9 KB.
   - Demonstrates the baseline shortcomings: missing repeated headers on page breaks, merged live load table, absence of visual charts, and footer overlap risk.
2. **`Report_After.pdf` / `Report_After.tex` (Enhanced Output):**
   - 44 pages, 613.4 KB.
   - Demonstrates all enhancements: repeated headers across all 56 tables, clean 14mm footskip margins, IRC:6 compliant load tables, Section 5.5 UR summary chart ($UR = 1.0$ limit line), and Chapter 7 BoQ material distribution charts.
