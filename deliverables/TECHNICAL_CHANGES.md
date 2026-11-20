# OsdagBridge LaTeX Report Generator Refactoring & Enhancements
## Technical Changes Document & Audit Report

**Date:** 21 November 2026  
**Project:** OsdagBridge (Osdag Bridge Plugin Ecosystem)  
**Deliverables Directory:** `e:\Fosse\OsdagBridge\deliverables\`  
**Target Repository:** [https://github.com/Nidhikhare12/OsdagBridge.git](https://github.com/Nidhikhare12/OsdagBridge.git)

---

### 1. Executive Summary & Overview
The report generation module in **OsdagBridge** compiles structural design outputs into a formal PDF report. Prior to this refactoring, the design report exhibited several formatting, visual, layout, and structural limitations:
1. Multi-page tables split across page breaks without repeating column headers (`\endfirsthead` / `\endhead`).
2. Table rows, content, and section markers overlapped with footers (e.g., page 30 text and girder rows bleeding into footer margins).
3. Live loads and footpath loads were merged into a single unstructured table in Chapter 3 without distinct vehicle classifications or units.
4. No utilization ratio ($UR = \text{Demand} / \text{Capacity}$) summary visualizations existed in Section 5.5.
5. No material quantity take-off charts existed in Chapter 7.
6. Formatting parameters (colors, margins, paddings, table styles) were hardcoded and scattered across multiple chapter modules.

All 6 core objectives and requirements have been systematically refactored, implemented, and verified through a complete pipeline run resulting in `Report_After.pdf`.

---

### 2. Detailed Technical Changes & File Modifications

#### A. Centralized Styling System (`styles.py`)
- **New Module:** `src/osdagbridge/core/reports/styles.py`
- **Architecture:** Serves as the **Single Source of Truth** for the entire report generation subsystem.
- **Components:**
  - `COLORS`: Brand colors (`osdag_green: #91B014`, `osdag_dark_green`), UI statuses (`pass_green: #2E7D32`, `fail_red: #C62828`, `threshold_red: #D32F2F`), and chart category colors for girders, deck, cross-bracing, diaphragms, steel, and rebar.
  - `GEOMETRY`: Centralized page metrics defining standard A4 dimensions with enhanced margins (`top=2.2cm`, `bottom=2.6cm`, `left=2.0cm`, `right=2.0cm`), `headheight=18pt` (resolving the `fancyhdr` warning), `headsep=14pt`, and `footskip=28pt`.
  - `TABLE_STYLE`: Standardized table paddings (`tabcolsep=5.5pt`, `arraystretch=1.15`, `extrarowheight=0.6pt`, `needspace_lines=5\baselineskip`).
  - `PLOT_STYLE`: Matplotlib layout parameters (`figure_figsize=(8.5, 4.2)`, `dpi=300`, clear typography, threshold styling).
  - Helper functions `get_latex_geometry_options()` and `get_table_spacing_latex()` emit standard LaTeX configurations directly into the preamble.

#### B. Dynamic Chart & Visualization Engine (`charts.py`)
- **New Module:** `src/osdagbridge/core/reports/charts.py`
- **Capabilities:**
  1. `generate_ur_summary_chart(design_checks_data, bridge, output_png_path)`:
     - Extracts governing utilization ratios across all primary structural elements:
       - Steel Plate Girders ($G_1, G_2, \dots, G_n$)
       - Concrete Deck Slab (Flexure Sagging, Flexure Hogging, Shear, Crack Width)
       - Cross Bracing (Compression, Tension)
       - End Diaphragms (Compression, Tension)
     - Embeds a red dashed horizontal threshold reference line at $UR = 1.0$.
     - Annotates each bar with precise numerical UR values and color-codes passing vs. exceeding checks.
     - Saves high-resolution (300 DPI) figures embedded directly into **Section 5.5 (Overall Design Check Summary)**.
  2. `generate_material_takeoff_charts(quantities, output_steel_path, output_concrete_rebar_path)`:
     - Generates two synchronized visualization panels:
       - **Structural Steel Tonnage Breakdown:** Bar chart comparing Plate Girders, Cross Bracing, End Diaphragms, and Shear Studs in Metric Tonnes (MT).
       - **Concrete vs. Reinforcement:** Comparative visual showing Concrete Deck Slab and Crash Barrier volumes ($\text{m}^3$) alongside Rebar tonnage ($\text{MT}$).
     - Automatically embedded into **Chapter 7 (Section 7.1 Material Breakdown Visualizations)**.

#### C. Repeated Table Headers Across Multi-Page Tables (`\endfirsthead` & `\endhead`)
- **Modified Modules:** `chap2.py`, `chap3.py`, `chap4.py`, `chap5.py`, `chap7.py`.
- **Implementation:**
  - Converted all 50 `longtable` definitions throughout the report to declare:
    - Primary header row followed by `\endfirsthead`.
    - Continuation caption `\caption[]{\textbf{<Table Name> (Continued)}} \\`.
    - Repeated column header row followed by `\endhead`.
  - Audited `Report_After.tex` verifying **50 of 50 longtables** contain proper `\endhead` repetitions with zero missing headers.

#### D. Layout, Spacing & Footer Clearance Fixes
- **Modified Modules:** `report_generator.py`, `styles.py`.
- **Implementation:**
  - Expanded bottom margin to $2.6\,\text{cm}$ and set `footskip=28pt`.
  - Added `\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}` to dynamically prevent table headers or trailing rows from orphaned breaks into footers.
  - Fixed `fancyhdr` `\headheight` to $18\,\text{pt}$, completely eliminating LaTeX layout warnings.
  - Performed automated coordinate scanning with `pdfplumber` confirming that content rows and table bodies maintain safe clearance buffer above footer borders across all 46 pages.

#### E. Load & Geometry Table Refactoring (`chap3.py`)
- **Modified Module:** `src/osdagbridge/core/reports/chap3.py`
- **Implementation:**
  - Decoupled vehicular live loads and footpath loads into distinct, clearly formatted tables:
    - **Table 3.3:** *Vehicular Live Load Parameters (IRC 6:2017)*, displaying vehicle class, category, dynamic impact factor, braking force, and centrifugal force. Vehicles are populated directly from UI selections (`Class A`, `Class 70R`, `Class AA`, `Class SV`, `Fatigue`).
    - **Table 3.4:** *Footpath and Pedestrian Live Loads (IRC 6 Cl. 206)*, showing pedestrian live load intensity, kerb impact load, and pedestrian railing loads with proper unit columns ($\text{kN/m}^2$, $\text{kN/m}$).

#### F. Pipeline Integration in `report_generator.py`
- Centralized preamble generation imports `styles.py`.
- Automated chart invocation inside `generate_report()` renders all Matplotlib charts to temporary asset paths before LaTeX compilation, copies generated figures seamlessly, and compiles 2 passes of `pdflatex` ensuring TOC and cross-references are fully resolved.

---

### 3. Deliverables Verification
1. **Report_Before.pdf**: Original baseline output preserved in `e:\Fosse\OsdagBridge\deliverables\Report_Before.pdf` (42 pages, 450 KB).
2. **Report_After.pdf**: Refactored output in `e:\Fosse\OsdagBridge\deliverables\Report_After.pdf` (46 pages, 755 KB) containing:
   - All 50 tables with repeated headers.
   - Clean footer buffers with zero bleed/overlap.
   - Separate Vehicular and Footpath Live Load tables in Chapter 3.
   - Dynamic UR summary chart at Section 5.5 (Figure 5.1).
   - Material Take-off breakdown charts at Section 7.1 (Figures 7.1 and 7.2).
3. **Technical Changes Document**: Saved in `e:\Fosse\OsdagBridge\deliverables\TECHNICAL_CHANGES.md`.
