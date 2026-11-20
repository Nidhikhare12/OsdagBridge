# Technical Changes & Report Refactoring Documentation

**Project:** FOSSEE OsdagBridge Winter Internship 2026 Screening Task
**Task:** LaTeX Report Generator Refactoring, Optimization, and Visual Enhancements
**Repository:** `C:\Users\office\Downloads\fosseeak\OsdagBridge`
**Branch:** `feat/fossee-report-refactoring`
**Author:** Akshay Ujjwal
**Reviewer:** FOSSEE / IIT Bombay
**Date:** November 2026

---

## 1. Project Objective

The primary objective of this project was to refactor, standardize, and enhance the automated engineering design report generation system in **OsdagBridge** (an open-source structural software suite developed under the FOSSEE project, IIT Bombay). The original report generation system suffered from fragile tabular layout formatting, hardcoded styling across multiple chapter modules, 32 distinct LaTeX compilation errors (mostly malformed multi-page `longtable` environments), unhandled table overflow across page boundaries, confusing live-load reporting, and a complete absence of structural utilization and material quantity visualizations.

This project refactored the entire reporting pipeline into a modular, robust architecture while strictly preserving backend structural analysis, design calculations, code checks, and Bill of Quantities (BOQ) formulations without altering underlying engineering solvers.

---

## 2. Original Problems Identified

An in-depth technical audit of the baseline report (`Report_Before.pdf`) and original codebase identified several critical issues:

1. **32 LaTeX Compilation Errors in Baseline TeX**:
   - In Chapters 2 and 4, numerous `longtable` captions were written as `\caption{...}\\` immediately inside the table without standard `\endfirsthead` / `\endhead` pagination commands. When `longtable` splits across pages, LaTeX threw syntax errors (`Misplaced \omit`, `Extra \ctable`, `Missing \endgroup`).
   - In the executive summary and utility strings, literal Unicode comparison glyphs (`≤`) were passed unescaped into standard `pdflatex`, causing fatal `Unicode character ≤ (U+2264) not set up for use with LaTeX` errors.
2. **Missing Brand Assets and Broken Image References**:
   - The official title logo (`assets/osdag_logo.png`) was referenced via relative paths but not copied to the export destination directory, leading to missing figure errors or fallback placeholder boxes.
3. **Table Continuation and Header Clipping**:
   - Critical design tables spanning multiple pages (notably Table 5.7 *Plate Girder Design Checks* and Table 5.29 *Cross Bracing Design Checks*) had no continuation headers, continuation footers, or column alignment constraints, making multipage review confusing and resulting in text clipping.
4. **Ambiguous Live-Load and Footpath Reporting (Chapter 3)**:
   - Vehicle live-load configurations and pedestrian footpath loadings were combined into a single ambiguous table (Table 3.3).
   - Class AA (Wheeled) was described with conflicting total loads (400 kN vs. 700 kN) due to conflation between Class 70R wheeled ($1000\text{ kN} / 700\text{ kN}$ train) and Class AA bogie/single-vehicle loading.
   - Footway loading failed to distinguish between ordinary footways ($400\text{ kg/m}^2$), footbridges/crowd loading ($500\text{ kg/m}^2$), and the IRC 6:2017 Clause 206.3 span reduction formula ($400 - (100/20)(30-10) = 300\text{ kg/m}^2$ for 30 m spans).
5. **Lack of Graphical Utilization & Material Take-off Visualizations**:
   - Structural design results were presented solely as dense raw numerical tables without clear visual utilization ratio (UR) bar charts to identify governing checks.
   - Material quantities in Chapter 7 consisted of an unstyled table without component-wise graphical distribution charts, and the $120\text{ kg/m}^3$ deck slab reinforcement allowance was ambiguously documented as a universal IRC 112 requirement rather than a preliminary estimating rule of thumb.

---

## 3. Centralized Styling Implementation (`styles.py`)

To eliminate hardcoded LaTeX styling duplicated across individual chapter modules, a centralized styling module was introduced at `src/osdagbridge/core/reports/styles.py`:

- **Design System Color Palette**:
  - `OSDAG_NAVY` (`#1A365D`): Primary document headers, section divider bars, and table primary headers.
  - `OSDAG_GREEN` (`#2E7D32`): Design verification **PASS** status indicator (UR $\le 1.0$).
  - `OSDAG_RED` (`#C62828`): Design verification **FAIL** status indicator (UR $> 1.0$).
  - `OSDAG_AMBER` (`#F57C00`): Near-capacity threshold warning ($0.90 \le \text{UR} \le 1.0$).
  - `OSDAG_GRAY` (`#616161`): Inactive, secondary, or boundary reference elements.
  - `OSDAG_LIGHT_GRAY` (`#F5F5F5`): Alternating table row banding for readability.
- **Predefined Table Column Formats**:
  - Fixed-width column specifications using the LaTeX `array` package (`C{<width>}`, `L{<width>}`, `R{<width>}`) utilizing `>{\centering\arraybackslash}p{...}` to enforce automated text wrapping and prevent cell overflow.
- **Preamble and Package Governance**:
  - Centralized inclusion of required packages: `booktabs`, `longtable`, `array`, `xcolor`, `colortbl`, `graphicx`, `float`, `needspace`, and `fancyhdr`.

---

## 4. Table Builder Architecture and Continuation Fixes (`table_builder.py`)

A structured table generation utility was designed in `src/osdagbridge/core/reports/table_builder.py` to encapsulate standard `longtable` construction:

- **Automated Longtable Lifecycle**:
  - Automatically emits standard pagination blocks:
    - `\firsthead`: Initial table header with bold column titles and double top border (`\toprule`).
    - `\endhead`: Continuation header with `\multicolumn{N}{c}{\textit{Table X (Continued)}}` and repeated column titles.
    - `\endfoot`: Bottom footer on breaking pages displaying `\textit{Continued on next page\dots}`.
    - `\endlastfoot`: Terminal bottom rule (`\bottomrule`) on the final table page.
- **Automatic Alignment & Escaping**:
  - Handles string sanitation for special characters (`_`, `%`, `&`, `#`) and mathematical inequality operators.
  - Standardizes padding (`\tabcolsep`) and row spacing (`\arraystretch`).
- **Applied Tables**:
  - Successfully restructured Table 5.7 (*Plate Girder Comprehensive Design Checks*) and Table 5.29 (*Cross Bracing Summary Checks*), eliminating page break collisions and completely resolving the 32 baseline LaTeX compiler errors.

---

## 5. Chapter 3: Live Load and Footpath Restructuring (`chap3.py`)

Chapter 3 was systematically reorganized into dedicated subsections matching IRC 6:2017 specifications:

1. **Separation of Vehicle and Footpath Tables**:
   - **Table 3.3: Carriageway Design Live Load Vehicles**: Dedicated to vehicular traffic configurations.
   - **Table 3.4: Footpath and Pedestrian Live Loading**: Dedicated to footway, kerb, and crowd load criteria.
2. **IRC 6:2017 Vehicle Loading Consistency**:
   - Reconciled vehicle specifications:
     - **IRC Class 70R (Wheeled)**: $1000\text{ kN}$ total train load ($170\text{ kN}$ bogie, $400\text{ kN}$ double axle group).
     - **IRC Class AA (Wheeled)**: $400\text{ kN}$ total vehicle weight ($200\text{ kN}$ per axle at $1.20\text{ m}$ spacing).
   - Documented centrifugal force behavior for straight alignments ($R = \infty$, $F_c = 0\text{ kN}$).
   - Documented braking force calculations per Clause 211.2 (20% of first vehicle + 5% of trailing load).
3. **Footway Load Distinction (Clause 206.1 vs 206.3)**:
   - Documented ordinary footway surface loading ($400\text{ kg/m}^2 = 3.924\text{ kN/m}^2$).
   - Documented foot overbridge and crowd loading ($500\text{ kg/m}^2 = 4.905\text{ kN/m}^2$).
   - Documented main girder reduction per Clause 206.3:
     $$P = 400 - \left(\frac{100}{20}\right)(L - 10) = 400 - 5(30 - 10) = 300\text{ kg/m}^2 = 2.943\text{ kN/m}^2$$
   - Documented IRC 6:2017 explicit exception: *When crowd load is considered, the Clause 206.3 reduction does not apply*.
   - Documented software limitation: OsdagBridge currently applies a conservative default of $500\text{ kg/m}^2$ ($4.905\text{ kN/m}^2$) without dynamic GUI reduction selection.

---

## 6. Chapter 5: Utilization Ratio (UR) Chart Architecture (`ur_charts.py`)

To provide immediate visual clarity on structural adequacy, a Matplotlib-based chart generation pipeline was built in `src/osdagbridge/core/reports/ur_charts.py`. The module extracts real calculation results from the solver's `output_dict` and renders 300-DPI high-resolution charts integrated into Section 5.5:

1. **Figure 5.1: Longitudinal Plate Girders Utilization Ratios (`ur_chart_girders.png`)**:
   - Renders 10 critical checks across G1 through G4:
     - Mid-span Bending Moment (Governing check, UR $\approx 1.57$, **FAIL**).
     - Support Shear Force (UR $\approx 0.58$, **PASS**).
     - Lateral-Torsional Buckling (UR $\approx 0.94$, **PASS**).
     - Web Buckling / Web Shear Capacity.
     - Web Yielding.
     - Bearing Stiffener Capacity.
     - Intermediate Stiffener Buckling.
     - Fatigue Stress Range (UR $\approx 0.94$, **PASS**).
     - Live Load Deflection (UR $\approx 0.81$, **PASS**).
     - Total Deflection.
2. **Figure 5.2: Concrete Deck Slab Utilization Ratios (`ur_chart_deck_slab.png`)**:
   - Renders 6 deck slab design checks (Sagging/Hogging Flexure, Punching Shear, SLS Stress, Crack Width).
3. **Figure 5.3: Transverse Cross-Bracing Utilization Ratios (`ur_chart_cross_bracing.png`)**:
   - Renders critical compression and tension efficiencies for diagonal members and horizontal chords across girder pairs G1–G2, G2–G3, and G3–G4. Maximum compression UR $\approx 0.74$ (**PASS**).
4. **Figure 5.4: End Diaphragm Status (`ur_chart_end_diaphragm.png`)**:
   - Represents the status of end diaphragm rolled/welded section design checks. Instead of falsely displaying $0.00$ or synthetic PASS ratings, the chart explicitly renders a hatched gray bar labeled `Solver Pending (Checks Not Available)` to ensure engineering honesty.

All charts feature:
- A prominent red dashed reference line at $\text{UR} = 1.0$ (`Capacity Limit`).
- Color coding: Dark Blue / Green for $\text{UR} \le 1.0$, Crimson Red for $\text{UR} > 1.0$.
- Clear numerical annotations on top of each bar.
- Direct LaTeX integration into Section 5.5 of `chap5.py`.

---

## 7. Chapter 7: Material Quantity Charts & Reconciliation (`material_charts.py`)

A comprehensive material take-off and visualization module was implemented in `src/osdagbridge/core/reports/material_charts.py` and integrated into `chap7.py`:

1. **Complete Structural Steel Reconciliation ($33.52\text{ MT}$)**:
   - **Girders Subtotal**: $4 \times 8.2234\text{ MT} = \mathbf{32.8935\text{ MT}} \approx \mathbf{32.89\text{ MT}}$.
     - G1, G2, G3, G4: Each $274.1124\text{ kg/m} \times 30.00\text{ m} / 1000 = \mathbf{8.223\text{ MT}}$ (displayed with 3 decimals in text to explain the subtotal without perceived rounding error).
   - **Cross Bracing**: $0.1064 + 0.1064 + 0.2533 = \mathbf{0.4661\text{ MT}} \approx \mathbf{0.47\text{ MT}}$ across 27 panels.
   - **Shear Stud Connectors**: $640\text{ studs} \times 0.0000314\text{ m}^3 \times 7.85\text{ MT/m}^3 = \mathbf{0.1578\text{ MT}} \approx \mathbf{0.16\text{ MT}}$. Displayed as an independent bar category in Figure 7.1.
   - **Grand Total Structural Steel**: $32.8935 + 0.4661 + 0.1578 = \mathbf{33.5174\text{ MT}} \approx \mathbf{33.52\text{ MT}}$.
   - **End Diaphragms**: Marked `Unavailable (Not in BOQ)` (hatched gray bar).
2. **Concrete Quantity Breakdown ($81.14\text{ m}^3$)**:
   - Quantified strictly by volume ($\text{m}^3$) to prevent confusion with gravitational mass:
     - Deck Slab (Grade M40): $8.40\text{ m} \times 0.25\text{ m} \times 30.00\text{ m} = \mathbf{63.00\text{ m}^3}$ ($157.50\text{ MT}$).
     - Concrete Crash Barriers: $2 \times 9.068\text{ m}^3 = \mathbf{18.14\text{ m}^3}$ ($45.34\text{ MT}$).
     - Total Superstructure Concrete: **$81.14\text{ m}^3$** ($202.84\text{ MT}$).
3. **Reinforcement Allowance Terminology Governance ($7.56\text{ MT}$)**:
   - Rate: $120\text{ kg/m}^3$ of deck slab concrete ($63.00\text{ m}^3 \times 120\text{ kg/m}^3 = \mathbf{7.56\text{ MT}}$).
   - Governed by clear technical definitions:
     - Labeled as the application's **preliminary BOQ estimation allowance**.
     - Explicitly disclaimed as a mandatory universal IRC 112 requirement or detailed Bar Bending Schedule (BBS).
     - Documented as **strictly covering deck slab concrete only** (excluding crash barriers, kerbs, and substructure).
4. **Table 7.1 Formatting Overhaul**:
   - Fixed column widths ($C\{0.9\text{cm}\}$, $L\{3.4\text{cm}\}$, $C\{3.8\text{cm}\}$, $C\{1.2\text{cm}\}$, $C\{1.7\text{cm}\}$, $C\{1.7\text{cm}\}$, $C\{1.7\text{cm}\}$) completely eliminated formula text wrapping and cell clipping.

---

## 8. Files Added and Modified

### Newly Added Modules
| File Path | Purpose |
|---|---|
| `src/osdagbridge/core/reports/styles.py` | Centralized styling parameters, color constants, column formats, and preambles. |
| `src/osdagbridge/core/reports/table_builder.py` | Robust `longtable` generator with automated pagination, continuation headers, and footers. |
| `src/osdagbridge/core/reports/ur_charts.py` | Structural utilization ratio extraction and 300-DPI bar chart generation module. |
| `src/osdagbridge/core/reports/material_charts.py` | Material quantity data extraction, reconciliation, and 300-DPI take-off visualization module. |
| `tests/unit/test_report_styles.py` | Complete test suite containing 45 targeted unit tests covering styles, tables, UR, materials, and Chapter 8. |

### Modified Existing Modules
| File Path | Changes Applied |
|---|---|
| `src/osdagbridge/core/reports/chap2.py` | Fixed `longtable` captions and labels; eliminated baseline LaTeX errors. |
| `src/osdagbridge/core/reports/chap3.py` | Split vehicle and footway tables; added IRC 6 Cl. 206.1/206.3 distinctions and limitations. |
| `src/osdagbridge/core/reports/chap4.py` | Fixed `longtable` captions and labels. |
| `src/osdagbridge/core/reports/chap5.py` | Integrated `TableBuilder` for Table 5.7 and 5.29; integrated Section 5.5 UR charts. |
| `src/osdagbridge/core/reports/chap7.py` | Widened Table 7.1 columns; reconciled steel ($33.52\text{ MT}$) and concrete ($81.14\text{ m}^3$); clarified reinforcement allowance; integrated Figures 7.1–7.3. |
| `src/osdagbridge/core/reports/chap8.py` | Formally listed all 5 required software and solver limitations in Section 8.3. |
| `src/osdagbridge/core/reports/report_generator.py` | Integrated UR and material chart generation into pipeline; ensured asset copying (`osdag_logo.png`, `.png` charts). |
| `src/osdagbridge/core/reports/report_utils.py` | Fixed unescaped Unicode glyphs (`≤` replaced with LaTeX `$\le$`). |

### Confirmed Untouched Structural Solver Files
The following critical structural engine files were audited and confirmed **100% untouched** (0 lines changed):
- `src/osdagbridge/core/bridge_types/plate_girder/analyser.py`
- `src/osdagbridge/core/bridge_types/plate_girder/grillage.py`
- `src/osdagbridge/core/bridge_types/plate_girder/designer.py`
- `src/osdagbridge/core/codes/IRC6_2017.py`
- `src/osdagbridge/core/codes/IRC24_2010.py`
- `src/osdagbridge/core/codes/IRC112_2020.py`
- `src/osdagbridge/core/reports/boq_generator.py`

---

## 9. Test Results

The unit test suite was executed in the project environment (`osdagbridge-env`):

```bash
cd C:\Users\office\Downloads\fosseeak\OsdagBridge
python -m unittest tests/unit/test_report_styles.py
```

**Outcome:**
```text
----------------------------------------------------------------------
Ran 45 tests in 8.523s

OK
```

All 45 tests passed successfully, verifying:
- Preamble generation and LaTeX macro declarations.
- Robust multi-page table formatting and continuation headers.
- Unicode character sanitization.
- Chapter 3 live load and footpath table separation and notes.
- Chapter 5 UR chart generation, thresholds, and annotations.
- Chapter 7 steel reconciliation ($33.52\text{ MT}$), concrete volume ($81.14\text{ m}^3$), and reinforcement allowance disclaimers.
- Chapter 8 known software limitations enumeration.
- Asset copying and file-linking integrity.

---

## 10. Before-versus-After Improvements

| Evaluation Dimension | Baseline Report (`Report_Before.pdf`) | Final Refactored Report (`Report_After.pdf`) |
|---|---|---|
| **LaTeX Compilation** | 32 compiler errors (`Misplaced \omit`, `Extra \ctable`, Unicode `≤` failures) | **0 compiler errors** (clean dual-pass compilation) |
| **Document Branding** | Missing logo (`assets/osdag_logo.png` not exported) | High-resolution official Osdag logo copied and embedded cleanly |
| **Table Formatting** | Inconsistent margins, column clipping, no page break headers | Standardized column widths, auto-wrapping, repeated continuation headers |
| **Table 5.7 & 5.29** | Broken across pages without context | Full `longtable` lifecycle with `(Continued)` headers and footers |
| **Chapter 3 Loading** | Mixed vehicle and footpath table; ambiguous Class AA / 70R loads | Dedicated vehicle (3.3) and footway (3.4) tables; IRC 6 Cl. 206.1/206.3 distinctions |
| **Design Utilization** | Raw numbers only; difficult to spot governing checks | Four 300-DPI UR charts with capacity limit lines ($\text{UR} = 1.0$) and PASS/FAIL badges |
| **Solver Status Honesty** | End diaphragm showed blank or unclear checks | Explicitly annotated as `Solver Pending (Checks Not Available)` |
| **Chapter 7 Materials** | Text-only table with clipped formulas; $120\text{ kg/m}^3$ mislabeled as IRC 112 rule | Three 300-DPI charts; reconciled steel ($33.52\text{ MT}$) and concrete ($81.14\text{ m}^3$); preliminary allowance disclaimed |
| **Physical Page Count** | 44 pages (incomplete formatting) | **60 physical pages** (59 printed numbered pages) with complete styling and appendices |

---

## 11. Known Software and Engineering Limitations

To maintain engineering integrity, the following limitations are formally documented in Chapter 8 of the report and in this technical document:

1. **End Diaphragm Structural Checks**:
   - Detailed structural sizing and code compliance checks for rolled or welded end diaphragm sections are pending solver implementation. They are honestly marked as `Unavailable` / `Solver Pending` rather than displayed as passing or zero.
2. **Entire Carriageway Crowd Loading**:
   - IRC 6:2017 Clause 206.1 permits crowd loading over the entire carriageway for certain bridge classifications; this load configuration is not currently supported by the grillage model.
3. **Tracked Vehicle Braking**:
   - Braking force for tracked vehicles (Class 70R / AA Tracked) is unsupported in the current solver iteration; longitudinal braking forces are evaluated for wheeled trains.
4. **Footway Load Reduction Selection**:
   - The interactive GUI does not currently offer a selection toggle between ordinary footway loading ($400\text{ kg/m}^2$, subject to span reduction per Clause 206.3) and crowd loading ($500\text{ kg/m}^2$, exempt from reduction). The solver conservatively adopts $500\text{ kg/m}^2$.
5. **Headless vs. Interactive GUI Calculations**:
   - Headless script runs and interactive GUI sessions exhibit minor differences due to railing load input precision and grillage node discretization:
     - Girder Moment Demand: Baseline $2224.95\text{ kNm}$ vs. Headless $2219.12\text{ kNm}$ ($\Delta = 0.26\%$).
     - Girder Shear Demand: Baseline $379.98\text{ kN}$ vs. Headless $378.79\text{ kN}$ ($\Delta = 0.31\%$).
     - Fatigue Stress Range: Baseline $145.86\text{ MPa}$ vs. Headless $145.45\text{ MPa}$ ($\Delta = 0.28\%$).
     - Governing UR: Baseline $1.58$ vs. Headless $1.57$ (both decisively **FAIL** due to girder flexure).

---

## 12. Instructions for Reproducing the Report

### A. Automatic Generation via OsdagBridge Pipeline
Execute the Python driver script using the project's Conda environment:

```bash
cd C:\Users\office\Downloads\fosseeak\OsdagBridge
C:\Users\office\miniconda3\envs\osdagbridge-env\python.exe C:\Users\office\.gemini\antigravity\brain\5c080f3f-cf57-4f8d-a4e4-3ffdcf43e037\scratch\run_final_report.py
```

This runs the plate girder design analysis, generates all 7 charts, and compiles `Report_After.pdf`, `Report_After.tex`, and `Report_After.log` in `C:\Users\office\Downloads\fosseeak\`.

### B. Standalone Independent LaTeX Compilation
To compile the generated LaTeX source completely outside the application runtime:

1. Ensure `Report_After.tex` and the `assets/` subfolder (containing `osdag_logo.png` and all `.png` charts) are present in the working directory.
2. Run standard `pdflatex` twice to resolve cross-references and the Table of Contents:

```bash
pdflatex -interaction=nonstopmode Report_After.tex
pdflatex -interaction=nonstopmode Report_After.tex
```

3. Confirm that `Report_After.pdf` is produced with **0 errors** in `Report_After.log`.
