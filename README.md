# OsdagBridge — final targeted report corrections

Apply this ZIP at the repository root (`C:\\Users\\User\\FOSSEE\\OsdagBridge`).
It contains only two changed report files. Extract with overwrite enabled.

## Scope
- Chapter 2: show a traffic-lane count only when the saved project input contains a valid numeric count. Otherwise show an explicit N.A. explanation instead of displaying a reference string or blank value.
- Chapter 7: clarify the girder-weight basis. The BOQ uses the saved per-girder section mass (kg/m) when supplied; the configured material unit weight is used only for the area-based fallback. This explains the small difference between the two supplied source properties without changing engineering calculations.

## Deliberately unchanged
- `boq_generator.py` calculation logic.
- PDF compilation, page breaks, repeated table headers, Chapters 3–6, 8–9, utilization chart, material chart, and end-diaphragm handling.

## Validation performed
- Python syntax compilation for both changed files.
- Traffic-lane display helper tested with missing, numeric, and nonnumeric values.
- Chapter 7 generated LaTeX smoke-compiled successfully with a synthetic quantity payload.

The full application and the user's local project environment were not available here; after applying, run the normal Design → Generate Report workflow and review the resulting PDF.
