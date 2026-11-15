# LaTeX Report Generator Refactoring and Enhancements

## Scope

This change improves the plate-girder design report generator while preserving
the existing report payload and UI workflow. It covers the six requested areas:
repeated table headers, printable page layout, separated load tables,
utilization charts, material-quantity charts, and centralized report styling.

## Changes

### 1. Repeating table headers

`core/reports/styles.py` provides `repeating_longtable_header()`, the shared
LaTeX fragment for `LongTable` first, continued, and final page headers.
Chapter 3 applies it to the load-combination table and Chapter 7 applies it to
the bill of materials. The helper includes `\\endfirsthead`, `\\endhead`,
`\\endfoot`, and `\\endlastfoot`, so a table that crosses a page repeats its
column labels and clearly marks continuation pages.

### 2. Page layout and footer safety

`styles.py` centralizes the A4 margins, header height, header/footer spacing,
table padding, row stretch, colors, and `needspace` protection. The report
preamble now consumes this module. The 0.95-inch bottom margin and 30-point
footer skip reserve printable space before a footer; tables are moved to the
next page when fewer than six baselines remain.

### 3. Vehicle and footway load tables

Chapter 3 now emits a `Vehicle Live Loads` table and a distinct `Footway Live
Load` table. The vehicle table derives the selected standard and custom
vehicles directly from the report input dictionary. The footway table shows its
mode, calculated/entered intensity, units, and IRC 6 reference separately.

### 4. Utilization-ratio chart

`core/reports/report_charts.py` discovers utilization values from the structured
design-check payload (supporting `utilization_ratio`, `ur`, `dcr`, and `ratio`).
It renders a PNG bar chart with a UR=1.0 limit line and pass/fail colours.
`report_generator.py` creates this image from the active report payload and
Chapter 5 embeds it after the design-check summary. No chart value is
hard-coded.

### 5. Material-quantity chart

The same chart module reads calculated bill-of-material values for structural
steel, bracing, concrete deck, reinforcement, and shear studs. Chapter 7
embeds the resulting PNG beneath its bill of materials. Values originate in
`calculate_material_quantities()`.

### 6. Centralized theme

`core/reports/styles.py` is the source of truth for report colors, margins,
table sizing, long-table behavior, and image embedding. The report generator
imports this module instead of owning its own package/layout block.

## Files changed

- `src/osdagbridge/core/reports/styles.py` - central report theme and LaTeX helpers.
- `src/osdagbridge/core/reports/report_charts.py` - data-derived PNG chart generation.
- `src/osdagbridge/core/reports/report_generator.py` - applies the shared theme,
  creates temporary chart assets, and passes them to report chapters.
- `src/osdagbridge/core/reports/chap3.py` - separate live-vehicle and footway tables.
- `src/osdagbridge/core/reports/chap5.py` - utilization chart placement.
- `src/osdagbridge/core/reports/chap7.py` - repeated bill-of-material headers and
  material chart placement.
- `tests/test_report_enhancements.py` - focused regression coverage.

## Verification

`python -m pytest tests -q` passes all 10 tests. The chart tests validate PNG
output generated from supplied calculation values, and the LaTeX tests validate
the shared layout, repeated headers, and report chapter integration.

## PDF evidence status

The supplied source archive contains no completed bridge design input/output
case and this environment has no available `pdflatex` executable. Therefore
`Report_Before.pdf` and `Report_After.pdf` are not included: creating them here
would require fabricated engineering results. To produce the final evidence,
run a representative completed bridge design once before the changes and once
after the changes in an environment with the Osdag LaTeX runtime available;
save the two generated PDFs with the required names.
