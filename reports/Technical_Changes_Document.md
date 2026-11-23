# OsdagBridge — Technical Changes Document

## Scope
Refactoring of the existing PyLaTeX report-generation workflow for the FOSSEE OsdagBridge Winter Internship 2026 screening task. Structural analysis and design calculations were not changed as part of this report-only task.

## Architecture
- `core/reports/styles.py` is the centralized source for page geometry, margins, header/footer, typography, brand colors, table spacing, chart theme, and the shared `format_longtable()` renderer.
- `report_generator.py` uses `get_latex_preamble()` to assemble every report with the shared style configuration.
- Chapter modules continue to own their content and data mapping. Chapter 3 and Chapter 7 use the shared longtable helper; other chapter longtables have explicit continuation header/footer sections.

## Longtable changes
- Added repeated headers to the remaining unheaded Chapter 2 girder tables.
- Completed repeated header/footer definitions in Chapter 5's stiffener summary and end-panel check tables.
- Converted Chapter 8 IRC and IS code tables from fixed `table`/`tabular` blocks to `longtable` blocks with repeated headings.
- Existing repeated-header tables in Chapters 3, 4, 5 and 7 were retained.

## Layout
- Centralized geometry uses A4 paper, 20 mm left/right margins, 25 mm top margin, 30 mm bottom margin, explicit head height/separation and foot skip.
- Shared table spacing, row stretch, cell padding and longtable pre/post spacing are defined in `styles.py`.
- The report compiler now requires a successful LaTeX return code and a non-empty PDF before copying a generated report to the destination. It will not accept a stale/partial PDF as success.
- Before chapter assembly, generated figure paths are checked against the filesystem. Missing/optional charts are omitted instead of being embedded as broken `\includegraphics` references that stop PDF compilation.

## Live-load reporting
- Vehicle and footway live-load tables remain distinct.
- Vehicle selection is read from the report input dictionary (the same selected input values passed from the GUI).
- Braking calculation no longer assumes two lanes when lane input is absent.
- Centrifugal force is calculated only when radius, speed and selected-vehicle weight inputs are supplied. No vehicle weight or design speed is invented.
- Missing impact/braking/footway inputs are identified as unavailable/not applicable instead of being filled with guessed defaults.

## Charts
- Utilization ratio charts use a horizontal bar chart with a red dashed UR=1.0 threshold. Values above 1.0 are marked as failing; values at or below 1.0 are passing.
- Chapter 5 chart embedding uses PyLaTeX-compatible `figure`/`includegraphics` blocks.
- Cross-bracing chart integration now passes the report's `ReportDataBridge` adapter, so actual bracing result extraction is available to the chart function.
- End-diaphragm results are sourced only from `enddiaphragm_design_results`; cross-bracing values are not mirrored into missing diaphragm results.
- Chapter 7 steel tonnage charts require actual BOM values for girders, all cross-bracing groups and end diaphragms. Missing values do not produce estimated quantities.
- Concrete volume and reinforcement weight are displayed on separate axes because m³ and MT are different units. Only available BOM fields are plotted.
- Chart images are written under the report generator's `TemporaryDirectory`; temporary assets are cleaned up automatically when report generation exits.

## Files modified/created
- Modified: `src/osdagbridge/core/reports/report_generator.py`
- Modified: `src/osdagbridge/core/reports/charts.py`
- Modified: `src/osdagbridge/core/reports/chap2.py`
- Modified: `src/osdagbridge/core/reports/chap3.py`
- Modified: `src/osdagbridge/core/reports/chap5.py`
- Modified: `src/osdagbridge/core/reports/chap8.py`
- Retained/used: `src/osdagbridge/core/reports/styles.py`, `chap4.py`, `chap7.py`
- Added: `tests/unit/test_report_enhancements.py`
- Added: this technical changes document and PDF
- Retained: `reports/Report_Before.pdf`, baseline TeX and genuine before screenshots

## Verification and limitations
- Python syntax compilation: passed for all files under `src` and `tests`.
- Focused regression tests: 9 passed, including shared longtable syntax, no-data chart behavior, invalid utilization rejection, and Chapter 8 design-log inclusion.
- A two-pass pdfLaTeX smoke test of the centralized preamble passed with common engineering Unicode symbols (≤, ≥, ≠, ×, ±, °, α, β).
- The current execution environment has `pdflatex`, Matplotlib, NumPy, SciPy and Pandas, but does not have PySide6 or PyLaTeX. A two-pass LaTeX layout smoke test for the centralized preamble and Chapter 8 completed successfully with `pdflatex`; this is a layout test, not a structural report. A full GUI-driven bridge design session and captured design-output dictionary are not included in the archive.
- Consequently, the genuine baseline PDF is retained, but no `Report_After.pdf` is fabricated. Full end-to-end PDF verification with real structural data must be performed from a completed design run in the project's Windows/Conda environment.
