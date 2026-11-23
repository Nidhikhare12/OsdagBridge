# Why some report tables contain empty cells (`---` / `N.A.`)

This is expected behaviour, not a formatter bug. The report is a **data-driven
view of whatever the design backend produced**; it deliberately prints `---`
instead of inventing numbers.

## 1. Sample/demo reports

`Report_Before.pdf`, `Report_After.pdf`, `Report_From_GUI.pdf` are built from a
representative payload with only a few dozen input keys. Chapters 1–9 reference
hundreds of canonical `KEY_*` values (material properties, load cases, member
forces, connection results, etc.). Missing keys render as `---` or `N.A.`

The real verification reports (`Report_Real_Design.pdf`, `Report_Real_UI.pdf`)
are generated from a full 30 m / 4-girder design with ~1000 output keys, so most
cells are populated.

## 2. Genuine backend gaps in the real design

Even with a complete run, a few rows stay empty:

| Row | Reason |
|---|---|
| Cross Bracing --- Compression / Tension / Slenderness | `osdag_core` connection design returned `None` for these members (the sample forces are only 3–6 kN). No design result → no capacity/UR. |
| End Diaphragm --- Moment / Shear | Rolled/welded end-diaphragm design is **not implemented** in the backend; the report prints "design to be added". |
| Bearing/intermediate stiffener checks | Only produced in `Custom` design mode; the sample uses `Optimized`, so those tables are intentionally omitted. |
| Some project-location/weather fields | Not selected in the UI for the demo. |

## 3. Fixed in this refinement

- **Transverse Shear (slab)** in Table 5.22 used retired DCR check id `16`; it now
  sources `deck_design_results` (`KEY_DD_SHEAR_VED` / `KEY_DD_SHEAR_VRDC`) so the
  demand, capacity and UR are filled.
- `ReportDataBridge._cb_osdag()` no longer imports `results_data` → OpenSeesPy
  just to read two dictionary keys (saves ~0.8 s on real design reports).

## 4. Design principle

Showing `---` is the correct engineering behaviour: a blank means "the backend
did not compute this value for this configuration", not zero and not a pass.
If you need a specific row filled, the fix belongs in the design engine (populate
the canonical key), not in the LaTeX formatter.
