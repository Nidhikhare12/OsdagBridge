# Report generator enhancements

## Architecture

The report generator remains the orchestration point.  It now applies
`table_utils.normalise_longtables()` to the assembled LaTeX, so existing
chapter data and calculations are preserved while legacy longtables receive
standard `endfirsthead`, `endhead`, `endfoot`, and `endlastfoot` blocks.

## Changed files

- `src/osdagbridge/core/reports/styles.py`: report-wide geometry, palette,
  typography, table metrics, figure widths, and caption styling.
- `src/osdagbridge/core/reports/table_utils.py`: reusable longtable builder and
  safe legacy-table continuation-header normalisation.
- `src/osdagbridge/core/reports/chart_generator.py`: Matplotlib/Agg charts
  sourced only from existing output/design-result and BOQ dictionaries.
- `report_generator.py`: central style injection, temporary report-asset chart
  lifecycle, and assembly-wide longtable handling.
- `chap3.py`: separate vehicle and footway tables populated from UI-bound load
  selection keys.
- `chap5.py`: inserts the utilization figure only when valid result data is
  available.
- `chap7.py`: inserts material charts only when numeric BOQ outputs exist.

## Engineering-data handling

Charts do not recalculate design capacities.  The utilization chart consumes
stored DCR/utilization/efficiency values and only derives a ratio where a
result explicitly supplies both demand and capacity.  Material charts consume
the existing `calculate_material_quantities()` output.  The present BOQ does
not expose a distinct end-diaphragm mass, and the current result payload does
not reliably expose end-diaphragm utilization; those bars are intentionally
omitted rather than represented as zero or passing.

## Layout and temporary assets

The centralized geometry reserves header and footer space (`headheight`,
`headsep`, and `footskip`) and uses `needspace` before tables/figures. Charts
are generated in the compilation `TemporaryDirectory`, embedded while LaTeX
compiles, and automatically removed afterwards.

## Validation

`PYTHONPATH=src python -m pytest tests/unit -q` passed: 7 tests.

The desktop GUI/PDF comparison was not run in this environment because the
Conda Osdag environment and a LaTeX distribution are not provisioned here.
Consequently, no authentic `Report_Before.pdf` or `Report_After.pdf` has been
claimed or produced.
