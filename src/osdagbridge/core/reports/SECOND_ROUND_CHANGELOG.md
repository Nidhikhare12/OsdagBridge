# OsdagBridge — Second-Round Report Generator Corrections

This package contains one consolidated replacement set. Replace the matching files under:

`src/osdagbridge/core/reports/`

## Files included

- `report_generator.py`
- `report_utils.py`
- `report_formatting.py`
- `executive_summary.py`
- `chap2.py`
- `chap3.py`
- `chap4.py`
- `chap5.py`

## Corrections included

1. **Header and pagination**
   - Running header split into two aligned lines to prevent project/job/date/version overlap.
   - Increased reserved header height.
   - Cover page labelled `Cover`; report page numbering starts at the contents/body, avoiding duplicate Page 1 labels.
   - Kept the existing footer note area and green rule.

2. **Figure handling and placeholders**
   - `generate_report()` now copies file-backed figures from `payload.figures` as well as byte-backed `figure_data`.
   - Figure helpers check that a file exists before emitting `\includegraphics`.
   - Missing figures now receive compact explanatory text rather than oversized placeholder boxes.

3. **Girder dimensions**
   - Chapter 2 converts the stored metre values to millimetres before displaying them in the Girder Section Dimensions table.

4. **Chapter 4 analysis results**
   - Support reaction rows are built from the actual `analysis_summary["reactions"]` data.
   - If the analysis summary contains no reaction values, the report says so explicitly instead of showing blank rows.
   - The support-reaction table repeats its headings across pages.

5. **Chapter 5 utilization chart**
   - Girder chart entries are restricted to the configured girders, avoiding pseudo/extra members.
   - The chart is a vertical bar chart with a horizontal red dashed UR = 1.0 line and UR on the Y-axis.
   - End-diaphragm entries are shown when the diaphragm is configured as bracing, with an explicit note that these use the shared bracing-module results rather than an independent calculation.
   - No utilization values are fabricated for unsupported rolled/welded end-diaphragm design.

6. **Executive Summary**
   - Key component outcomes are now based on stored design results.
   - Missing component results are labelled `NOT AVAILABLE`; the summary no longer hard-codes every component as passing.
   - Shared end-diaphragm/bracing results are identified as shared.

7. **Wind and seismic reporting**
   - Stored wind/seismic calculation values in `output_dict` are merged into report inputs before chapter generation.
   - Wind-force fields no longer render as blank; missing source values are identified explicitly.
   - Seismic resultant forces are described as not calculated/exposed by the current analysis module. No engineering force values have been invented.

8. **Centralized formatting**
   - `report_formatting.py` provides shared escaping, value rendering, table and caption helpers.
   - `report_utils.py` retains the legacy helper names used by existing chapters.

## Validation performed

All eight Python files passed Python syntax compilation (`py_compile`) and AST parsing in the preparation environment.

**Still required:** run OsdagBridge with the same bridge design and generate a fresh PDF. Python syntax validation does not prove that the local LaTeX installation will compile every generated page or that all backend result fields are populated for that particular design.
