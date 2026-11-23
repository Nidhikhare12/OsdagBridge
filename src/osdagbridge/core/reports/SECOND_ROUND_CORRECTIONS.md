# Consolidated report-source corrections

Replacement target: `src/osdagbridge/core/reports/`

## Modified files

- `executive_summary.py`
  - Use the declared `plan` figure payload for the Executive Summary overall plan.
  - Append the known units to girder spacing (m) and deck thickness (mm).
  - Read the persisted per-girder total-load deflection values and compare the maximum with the same L/600 limit used in Chapters 4 and 5.
  - Disclose total-load deflection status and demand/capacity in the Key Design Outcomes; include a failed total-load deflection in the overall status and overall UR.
- `chap5.py`
  - Populate the overall transverse-shear row from the bridge-level values already used by the detailed transverse-shear check, instead of searching only the per-girder check records.
  - Retain the existing per-load-case deflection row and add a separate L/600 total-load deflection row using the persisted per-girder values, so the 13.69 mm load-case result is not conflated with the 37.125 mm total-load result.
- `chap6.py`
  - Replace fabricated-looking placeholder boxes with concise unavailable-figure explanations.
  - Check that a supplied path is an existing file before emitting `\\includegraphics`.

## Verification performed

- `compileall` and AST parsing: passed for all 14 supplied Python files.
- Executive Summary synthetic regression: passed for units, the 37.125 mm / 33.3 mm total-load failure, and combined overall status.
- Chapter 6 missing-figure fallback regression: passed; no `[PLACEHOLDER]` text remains in generated chapter content when figures are absent.
- Chapter 5 overall-summary mapping: source-level check confirms the transverse-shear row now reads bridge-level demand/capacity/UR, and the L/600 total-load deflection row is separate from the per-load-case row.

## Not verified

The ZIP does not include the complete OsdagBridge application, backend calculation modules, CAD export implementation, actual input/output payload, or the original FOSSEE project brief. Consequently, imports against the real application, backend data mapping, actual CAD figure generation, chart generation in the application, LaTeX compilation, and a regenerated PDF were not run. No engineering inputs, formulas, or calculated capacities were changed.
