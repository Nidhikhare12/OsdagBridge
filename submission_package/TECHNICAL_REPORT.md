# Technical Changes & Architecture Report

## OsdagBridge — LaTeX Report Generator Refactoring & Visual Enhancements

**Candidate Name:** Aryan Vyas  
**GitHub Profile:** [@Aaryanvyas](https://github.com/Aaryanvyas)  
**Target Repository:** [Nidhikhare12/OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge)  
**Pull Request:** [PR #196: Fix report table column alignment and LaTeX formatting](https://github.com/Nidhikhare12/OsdagBridge/pull/196)  
**Status:** Completed Full Implementation (All 6 Screening Scope Items)  
**Date:** November 2026  

---

## 1. Executive Summary

OsdagBridge is an open-source structural bridge engineering design software developed under the FOSSEE initiative at IIT Bombay. A core deliverable of the software is the automated generation of detailed, publication-grade design calculation reports formatted using LaTeX (`pdflatex`).

This project delivers a comprehensive refactoring of the reporting pipeline in `src/osdagbridge/core/reports/`, resolving longstanding layout defects, establishing a centralized single source of truth for styling, and introducing publication-quality data visualizations.

### Summary of Completed Scope

| # | Requirement | Implementation Summary | Primary Files Altered |
| :- | :--- | :--- | :--- |
| **1** | **Repeated Table Headers Across Page Breaks** | Reusable `build_longtable_header()` helper implementing `\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`. Column headers repeat on all page transitions. | `styles.py`, `chap3.py`, `chap5.py`, `chap7.py` |
| **2** | **Layout, Footer Overlap & Spacing Fixes** | Replaced hardcoded `1in` margin with `bottom=30mm`, `footskip=18mm`, and `\needspace` buffers. Eliminates row bleeding into footer rules (Page 30 / G4 row). | `styles.py`, `report_generator.py` |
| **3** | **Load & Geometry Table Refactoring** | Cleanly separated Vehicle Live Loads (with dynamic vehicle list, impact factor, braking load) from Pedestrian/Footway Loads. | `chap3.py` |
| **4** | **Utilization Ratio (UR) Summary Chart** | Dynamic Matplotlib bar chart for primary components (Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms) with a red dashed line at $\text{UR} = 1.0$. | `report_charts.py`, `chap5.py`, `report_generator.py` |
| **5** | **Material Quantity Bar Charts** | Programmatic bar charts for Structural Steel tonnage breakdown and Concrete Volume vs. Rebar/Steel weight embedded in Chapter 7. | `report_charts.py`, `chap7.py`, `report_generator.py` |
| **6** | **Centralized Formatting System (`styles.py`)** | Dedicated architecture module as Single Source of Truth for palettes, page geometry, table rules, and chart aesthetics. | `styles.py`, `report_generator.py` |
| **—** | **Table Column & Caption Bug Fixes** | Corrected 5-column cross-bracing and 4-column end-diaphragm tables; fixed trailing `\\` delimiters. | `chap2.py`, `test_report_tables.py` |

---

## 2. Centralized Formatting & Style System (`styles.py`)

### 2.1 Architectural Motivation
Previously, formatting parameters (cell padding, line stretch, color codes, page margins, and rule widths) were dispersed across chapter scripts or hardcoded in `preamble()`. Modifying global branding or margins required altering multiple files, risking visual regressions.

### 2.2 System Implementation
`src/osdagbridge/core/reports/styles.py` now serves as the authoritative single source of truth:

```python
# Document Geometry (prevents footer collision)
PAGE_GEOMETRY = {
    "paper": "a4paper",
    "top": "25mm",
    "bottom": "30mm",
    "left": "20mm",
    "right": "20mm",
    "headheight": "15pt",
    "headsep": "10pt",
    "footskip": "18mm",
}

# Unified Color Palette
COLORS = {
    "primary": "#91B014",     # Osdag Brand Green
    "secondary": "#2A4B7C",   # Bridge Blue
    "accent": "#4A7C59",      # Muted Structural Green
    "dark_text": "#1F2937",   # High-contrast Charcoal Slate
    "pass": "#16A34A",        # Safety Check Pass Green
    "fail": "#DC2626",        # Limit Exceeded Red
    "grid": "#E5E7EB",        # Subtle Grid Gray
}

# Table Layout & Spacing
TABLE_LAYOUT = {
    "tabcolsep": "5.5pt",
    "arraystretch": 1.15,
    "arrayrulewidth": "0.5pt",
    "extrarowheight": "0.8pt",
    "page_break_threshold": "6",
}
```

---

## 3. Repeated Table Headers Across Multi-Page Tables

### 3.1 Problem
Engineering calculation reports span dozens of pages. Previously, `longtable` blocks omitted LaTeX header continuation blocks, leaving readers on subsequent pages without column headers.

### 3.2 Solution
In `styles.py`, `build_longtable_header()` generates the standardized 4-part LaTeX continuation block:

```latex
\begin{longtable}{|...|}
\caption{\textbf{Table Title}}\label{tab:...}\\
\hline
\textbf{Col 1} & \textbf{Col 2} & ... \\
\hline
\endfirsthead

\multicolumn{N}{c}{\small\itshape Table \thetable\ -- Continued from previous page} \\[4pt]
\hline
\textbf{Col 1} & \textbf{Col 2} & ... \\
\hline
\endhead

\hline
\multicolumn{N}{r}{\footnotesize\itshape Continued on next page...} \\
\hline
\endfoot

\hline
\endlastfoot
```

This structure is systematically integrated across:
- **Chapter 3:** Dead Load, Surfacing, Vehicular Live Load, Footway Load, Wind, Seismic, and Load Combinations.
- **Chapter 5:** Girder Design Summary (Table 5.13) and Overall Design Check Summary (Table 5.22).
- **Chapter 7:** Bill of Materials (Table 7.1).

---

## 4. Layout, Footer Clearance & Vertical Spacing Fixes

### 4.1 Root Cause of Footer Bleeding
The original template configured `\usepackage[a4paper, margin=1in]{geometry}` with no explicit `footskip`. When `hasSDonPage` (*Software default value*) was triggered, negative vertical spacing (`\vspace{-20pt}`) hoisted the footer line upward by nearly 7 mm directly into the printable text area, causing rows like **G4** on Page 30 to overlap with the green footer rule.

### 4.2 Resolution
1. **Geometry Re-allocation:** Set explicit `bottom=30mm` and `footskip=18mm` in `styles.py`, providing a guaranteed 18 mm clearance barrier between table contents and footer elements.
2. **Footer Rule Adjustment:** Reduced vertical displacement to a safe `\vspace{-10pt}` with `\needspace{6\baselineskip}` before major tabular sections.
3. **Resilient Compiler Wrappers:** Optional packages in `preamble()` now use `\IfFileExists{...}` conditional blocks with native LaTeX fallbacks, ensuring the document compiles cleanly on any evaluator's system without freezing on missing CTAN packages.

---

## 5. Chapter 3 Load Table Refactoring

### 5.1 Separation of Vehicle vs. Footway Loads
Previously, Vehicular Live Loads and Footpath Live Load were merged into an unstructured 2-column key-value table. 

### 5.2 Refactored Implementation
Chapter 3 now presents two distinct, clearly formatted tables:
1. **Table 3.3 (Vehicular Live Load Parameters):**
   - Columns: `Vehicle Class`, `Standard Reference`, `Impact Factor`, `Braking Force`, `Centrifugal Force`.
   - Dynamically populated from UI selections (`loading.live_load.irc.*`), displaying calculated impact factors and lane braking forces per IRC:6-2017 Clauses 208 and 211.
2. **Table 3.4 (Pedestrian / Footway Live Load):**
   - Details footpath width provided, applied intensity ($4.0 - 5.0 \text{ kN/m}^2$ calculated via IRC 6 Cl. 206.1), and traffic combination rules.

---

## 6. Data Visualizations & Dynamic Charting

### 6.1 Section 5.5: Utilization Ratio (UR) Summary Chart
- **Module:** `src/osdagbridge/core/reports/report_charts.py` (`generate_overall_ur_chart`)
- **Plot Specifications:**
  - Evaluates primary components: Plate Girders, Concrete Deck Slab, Cross Bracing, and End Diaphragms.
  - **Threshold Line:** Distinct horizontal red dashed line at $\text{UR} = 1.0$ labeled *Capacity Limit ($UR = 1.0$)*.
  - **Color-Coding:** Bars render in Osdag Green (`#91B014`) when $\text{UR} \le 1.0$, automatically switching to Alert Red (`#DC2626`) if $\text{UR} > 1.0$.
  - Embedded as **Figure 5.1** directly within Section 5.5.

### 6.2 Chapter 7: Material Quantity & BOQ Visualizations
- **Figure 7.1:** Structural Steel Tonnage Breakdown by Subsystem (Metric Tonnes for Girders, Cross Bracing, End Diaphragms, and Shear Studs).
- **Figure 7.2:** Material Take-off Summary comparing Concrete Volume ($\text{m}^3$) against Rebar Fe 500 Weight (MT) and Structural Steel Weight (MT).
- Automatically generated as 300 DPI image assets and embedded via `_fig_embed()`.

---

## 7. Verification & Automated Regression Testing

A comprehensive test suite in `tests/unit/test_report_enhancements.py` verifies all requirements alongside the existing tests:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1
rootdir: C:\Users\Asus\OsdagBridge
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

## 8. Generated Deliverables

The following compiled PDF documents are included in the submission package:
1. **`Report_Before.pdf`** (654 KB): Baseline output generated prior to enhancements.
2. **`Report_After.pdf`** (654 KB): Enhanced 49-page publication report featuring centralized styling, repeated multi-page headers, separated load tables, and embedded high-resolution visualizations.
