# OsdagBridge — LaTeX Report Generator Refactoring & Enhancements
## Technical Architecture & Quality Gate Documentation

---

### 1. Executive Summary

This document details the refactoring, modernization, and quality hardening of the LaTeX Design Report Generator within **OsdagBridge** (`src/osdagbridge/core/reports/`).

The primary goals of this engineering initiative were:
1. **Centralize Styling & Geometry**: Replace scattered, duplicate, hardcoded LaTeX geometry, colors, table paddings, and column specifications with a single source of truth (`styles.py`).
2. **Eliminate LaTeX Errors & Syntax Defects**: Resolve 138 baseline LaTeX compilation errors (`Misplaced \noalign`, `Misplaced \omit`, `Extra alignment tab`), unclosed groups, duplicate labels, and headheight warnings.
3. **Multi-Page Table Support**: Enable robust repeated headers across page breaks (`\endfirsthead`, `\endhead`) using a reusable helper (`make_longtable` in `helpers.py`) across all 46 tables in the report.
4. **Solve Footer Overlap**: Prevent tabular text and multirow blocks from colliding with or intruding into the running page footer rule.
5. **Dynamic Data Visualizations**: Implement automated, headless Matplotlib charts for Section 5.5 (Overall Component Utilization Ratios) and Chapter 7 (Structural Steel & Concrete Material Quantities).
6. **Zero-Regression Architecture**: Preserve strict backward compatibility, graceful degradation on missing/custom data, and zero heavy third-party dependencies (no PyLaTeX).

---

### 2. Architectural Rationale: Helper-Based Raw LaTeX vs. PyLaTeX

During the Phase 1 exploration and design approval, the codebase was confirmed to generate report chapters using Python raw string formatting. The decision was made **not to introduce PyLaTeX** as an external dependency for the following technical reasons:

1. **Dependency Footprint**: PyLaTeX introduces external dependencies and requires wrapping existing LaTeX code into an object-oriented Python AST. For an open-source structural engineering software (Osdag), adding heavyweight external packages risks installation friction, distribution packaging bloat, and version incompatibilities across different OS targets (macOS, Windows, Linux).
2. **Full Low-Level Control of TeX Tokens**: PyLaTeX abstracts away low-level TeX primitives. Certain delicate formatting constructs required in high-compliance engineering reports—such as exact `\endfirsthead`, `\endhead`, `\cline{i-j}`, `\noalign{\nopagebreak}`, `\needspace`, and `fancyhdr` hooks—are difficult to manage cleanly in PyLaTeX without resorting to `NoEscape` strings.
3. **Clean Helper Architecture**: By building lightweight, pure-Python helper modules (`styles.py`, `helpers.py`, `charts.py`), the codebase achieves complete centralization, readability, and modularity without changing the battle-tested string compilation pipeline.

---

### 3. File Inventory: Modified & Created Modules

| File Path | Status | Purpose & Description |
|:---|:---:|:---|
| `src/osdagbridge/core/reports/styles.py` | **Created** | Single source of truth for page geometry (`geometry`), unified Osdag green brand colors (`#91B014`), document font sizes, line stretch, arraystretch, column-width presets, needspace thresholds, and `generate_preamble()`. |
| `src/osdagbridge/core/reports/helpers.py` | **Created** | Reusable `make_longtable(...)` generator providing automatic header repetition (`\endfirsthead` / `\endhead`), non-incrementing continuation captions (`\tablename\ \thetable{} -- continued`), and clean column counting. |
| `src/osdagbridge/core/reports/charts.py` | **Created** | Headless Matplotlib chart generator (Agg backend) for Section 5.5 (Utilization Ratio summary bar chart with limit line at UR = 1.0) and Chapter 7 (Structural steel tonnage breakdown and Concrete vs. Rebar quantities). |
| `scripts/test_report.py` | **Created** | Comprehensive test harness and quality gate analyzer. Builds realistic mock payloads (Normal 3-girder and `--large` 6-girder stress test), parses `.log` files for compilation metrics, detects multi-page tables via `.aux`, and verifies footer margins via PyMuPDF. |
| `src/osdagbridge/core/reports/report_generator.py` | **Modified** | Refactored `preamble()` to call `generate_preamble()`, integrated asset resolution, wired chart generation pipelines into temporary and output directories, and passed charts to Chapters 5 & 7. |
| `src/osdagbridge/core/reports/chap1.py` | **Modified** | Converted tabular metadata tables to centralized styles and `make_longtable`. |
| `src/osdagbridge/core/reports/chap2.py` | **Modified** | Converted Tables 2.4 through 2.12 (Materials, Cross Bracing, End Diaphragms, Girder Details) to `make_longtable` with column presets. |
| `src/osdagbridge/core/reports/chap3.py` | **Modified** | Refactored dead load and live load tables into Vehicle Live Load (one row per selected vehicle with Cl. 208 impact, Cl. 211 braking, straight bridge centrifugal note) and Footpath Live Load (Cl. 206.1 intensity, Cl. 206.2 kerb, software default/user-modified mode). |
| `src/osdagbridge/core/reports/chap4.py` | **Modified** | Escaped caption unescaped `&`, adjusted 3-line demand cell to 2-line makecell (eliminating 2 overfull vboxes), added `\par\vspace{0.8em}` to placeholder figures (eliminating 442pt overfull hbox). |
| `src/osdagbridge/core/reports/chap5.py` | **Modified** | Converted all 29 design check tables to `make_longtable`, added `\\*[6pt]` pagebreak guards inside multirow girder blocks, embedded the Section 5.5 UR summary bar chart. |
| `src/osdagbridge/core/reports/chap7.py` | **Modified** | Closed unclosed `\begingroup`, converted BOQ Table 7.1 to `make_longtable`, added side-by-side material quantity subfigures. |
| `src/osdagbridge/core/reports/chap8.py` | **Modified** | Closed two unclosed `\begingroup` blocks, resolved duplicate label `sec:assumptions` to `sec:exec-assumptions`, split unbroken inline math strings. |
| `src/osdagbridge/core/reports/executive_summary.py` | **Modified** | Replaced hardcoded width calculation in Table 1 with tabcolsep-aware math, preventing table from overflowing textwidth. |

---

### 4. Quality Gate Progression Table

The table below tracks the metrics parsed directly from `pdflatex` compilation `.log` files, `.aux` files, and the PyMuPDF footer overlap detector across each development phase:

| Metric | Baseline (Phase 3A) | Phase 3B (Tables & Loads) | Phase 4 (Layout & Overlap) | Phase 5 (UR Chart) | Phase 6 & 7 (Final Normal) | Phase 6 & 7 (Final Large) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Total LaTeX Errors (`! ...`)** | **138** | **0** | **0** | **0** | **0** | **0** |
| - Misplaced `\noalign` | 46 | 0 | 0 | 0 | 0 | 0 |
| - Misplaced `\omit` | 46 | 0 | 0 | 0 | 0 | 0 |
| - Extra alignment tab | 46 | 0 | 0 | 0 | 0 | 0 |
| **Overfull `\hbox` Count** | 59 | 59 | **46** | **46** | **46** | **53** |
| **Overfull `\vbox` Count** | 2 | 2 | **0** | **0** | **0** | **0** |
| **Headheight Warnings** | 44 | 44 | **0** | **0** | **0** | **0** |
| **Multiply-Defined Labels** | 2 | 0 | **0** | **0** | **0** | **0** |
| **Unclosed Groups (`level > 0`)** | 1 | 0 | **0** | **0** | **0** | **0** |
| **Multi-page Tables Detected** | 0 | 4 | **4** | **6** | **6** | **10** |
| **Footer Collisions (`y > 765pt`)**| **Detected** | Detected | **0** | **0** | **0** | **0** |

---

### 5. Detailed Root-Cause Analyses & Technical Solutions

#### 5.1 Misplaced `\noalign` / `\omit` / Extra alignment tab
- **Root Cause**: In LaTeX `longtable`, `\caption{...}` must be terminated by a newline macro `\\`. In the legacy code, captions were written as `\caption{...}` without `\\` immediately followed by `\hline` or column headers. Because `\caption` internally processes tabular cells, omitting the trailing `\\` caused TeX's alignment state machine to misinterpret subsequent `\hline` commands as misplaced `\noalign` or `\omit` operations, resulting in 138 cascading compilation errors.
- **Resolution**: Implemented `make_longtable` in `helpers.py`, which strictly outputs:
  ```latex
  \caption{\textbf{<caption_text>}} \label{<label>} \\
  ```
  Every table conversion across Chapters 1 through 8 now uses this helper, reducing misplaced `\noalign` errors to **0**.

#### 5.2 Multi-Page Longtable Header Repetition
- **Root Cause**: The legacy codebase wrapped `longtable` environments with a single top header and immediately transitioned into body rows. On tables spanning across page boundaries (e.g. Table 5.1, Table 5.4, Table 5.29), continuation pages had no column headings.
- **Resolution**: `make_longtable` automatically structures every table with:
  ```latex
  \hline
  <header_tex>
  \hline
  \endfirsthead
  \multicolumn{N}{c}{\textbf{\tablename\ \thetable{} -- continued from previous page}} \\[6pt]
  \hline
  <header_tex>
  \hline
  \endhead
  \hline
  \multicolumn{N}{r}{\textit{Continued on next page}} \\
  \endfoot
  \hline
  \endlastfoot
  ```
  The table number increments exactly once, and column headers repeat seamlessly on every page.

#### 5.3 Unclosed Groups (`\end occurred inside a group at level 3`)
- **Root Cause**:
  1. `chap7.py` opened `\begingroup \small \setlength{\tabcolsep}{...}` around line 8 but omitted the matching `\endgroup`.
  2. `chap8.py` opened two `\begingroup \small` blocks around the IRC and IS code reference tables without closing them.
- **Resolution**: Inserted matching `\endgroup` calls in `chap7.py` and `chap8.py`.

#### 5.4 Duplicate Label (`sec:assumptions`)
- **Root Cause**: Both `executive_summary.py` (Section "Design Assumptions & Limitations") and `chap8.py` (Section "Design Assumptions") declared `\label{sec:assumptions}`.
- **Resolution**: Renamed the executive summary label to `\label{sec:exec-assumptions}` and updated corresponding references.

#### 5.5 Overfull `\hbox` and `\vbox` Elimination
- **Root Cause 1 (442pt Overfull `\hbox`)**: In Chapter 4 (`chap4.py`), three structural analysis placeholder diagrams `\noindent\fbox{\parbox{0.97\textwidth}{...}}` were placed consecutively without a paragraph break (`\par`), forcing TeX to layout three full-width boxes on a single horizontal line.
  - *Fix*: Added `\par\vspace{0.8em}` to `_fig_embed()` in `report_utils.py`.
- **Root Cause 2 (Overfull `\vbox`)**: In Table 4.1, a 3-line cell `\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}` was placed inside a 2-row `\multirow{2}{*}`.
  - *Fix*: Compressed to 2 lines `\makecell{\textbf{Load Case/}\\\textbf{Combination}}`.
- **Root Cause 3 (27pt Overfull `\hbox` in Table 1)**: `executive_summary.py` calculated girder column width assuming `15.0cm` total text width without subtracting `2 * tabcolsep` per column.
  - *Fix*: Reduced available width to `13.5cm - label_col_cm`.
- **Root Cause 4 (Inline Math `\hbox`)**: In `chap8.py`, long unbroken inline math `$E_s = 200{,}000 \, \text{MPa}, \ G_s = 80{,}000 \, \text{MPa}, \ \nu = 0.30, \ \alpha = 11.7 \times 10^{-6}/^\circ\mathrm{C}$` could not break across margins.
  - *Fix*: Broken into individual math tokens `$E_s = ...$`, `$G_s = ...$`.

#### 5.6 Headheight Warnings (`fancyhdr`)
- **Root Cause**: `geometry` was invoked without specifying `headheight`, defaulting to `12.0pt`. LaTeX logged 44 warnings requiring `headheight >= 17.1pt`.
- **Resolution**: Set `headheight=20pt`, `headsep=14pt` in `styles.py`.

#### 5.7 Footer Overlap Bug Proof & Resolution
- **Bug Proof**:
  - In `output/before/Report_Before.pdf`, body text reached $y = 772.0\text{ pt}$ while the footer rule was dragged upward to $y = 770.0\text{ pt}$ by a legacy `\vspace{-20pt}` hack in `fancyhdr`.
  - In large models (6 girders), `\multirow{13}{*}{\makecell{G4}}` and `\makecell{G6}` broke across pages. Because TeX centered the multirow text across all 13 rows, the labels were rendered at $y = 785.7\text{ pt}$ and $y = 836.2\text{ pt}$, directly on top of the footer text.
- **Resolution**:
  1. Removed `\vspace{-20pt}` and `\vspace{-8pt}` hacks from `fancyhdr`.
  2. Configured document geometry in `styles.py` with `bottom=1.25in`, `footskip=28pt`.
  3. Added `\\*[6pt]` (pagebreak prohibition) between internal rows of multirow girder blocks in `chap5.py`, ensuring pagebreaks occur exclusively at girder boundaries (`\hline`).
  4. Added `\needspace{10\baselineskip}` before opening longtables.
  5. Built an automated PyMuPDF bounding-box detector into `test_report.py` checking all non-footer text blocks below $y = 765.0\text{ pt}$. Result: **0 footer collisions detected**.

---

### 6. Test Harness & Quality Verification Guide

The test harness operates in `scripts/test_report.py` without requiring GUI interaction.

#### Normal Mode (3-Girder Standard Model):
```bash
python3 scripts/test_report.py --out-dir output/final --stem Report_After_harness_normal
```
- Verifies: Chapter presence, 2-pass `pdflatex` compilation, `.log` quality gate summary, `.aux` multi-page table tracking, PyMuPDF footer overlap check.

#### Large Stress-Test Mode (6 Girders, Multi-Vehicle):
```bash
python3 scripts/test_report.py --out-dir output/final --stem Report_After_harness_large --large
```
- Stresses: 6 girders (G1–G6), 5 cross-bracing panels, multiple selected IRC live loads + custom vehicle, 10 multi-page tables.

---

### 7. Generated Final Artifacts
- **Normal Design Report**: [Report_After_harness_normal.pdf](file:///Users/adityagupta/Desktop/IIT%20BOMBAY/OsdagBridge/output/final/Report_After_harness_normal.pdf)
- **Large Stress-Test Report**: [Report_After_harness_large.pdf](file:///Users/adityagupta/Desktop/IIT%20BOMBAY/OsdagBridge/output/final/Report_After_harness_large.pdf)
- **LaTeX Source (Normal)**: [Report_After_harness_normal.tex](file:///Users/adityagupta/Desktop/IIT%20BOMBAY/OsdagBridge/output/final/Report_After_harness_normal.tex)
- **LaTeX Source (Large)**: [Report_After_harness_large.tex](file:///Users/adityagupta/Desktop/IIT%20BOMBAY/OsdagBridge/output/final/Report_After_harness_large.tex)
