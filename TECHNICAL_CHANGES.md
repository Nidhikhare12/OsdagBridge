# Report fixes and verification handover

Updated: 11 November 2026. Repository: `Winter-internship/osdagbridge`.

## Status

The report defects identified in the review have been corrected in the local working tree. The delivered PDF is a **synthetic report verification case**, not a solved engineering design and not proof of complete backend coverage. Earlier statements describing it as a production design report or claiming full engineering acceptance are superseded by this document.

The engineering solver and quantity formulas were not changed. Missing backend results remain explicit rather than being replaced with invented numbers.

## Changes

| Files under `src/osdagbridge/core/reports` | Change |
| --- | --- |
| `report_data.py` | Shared numeric check and quantity records; reads the actual `per_girder -> checks[] -> dcr` schema, deck report values and Osdag cross-bracing results. Keeps source, member, demand, capacity, units and load combination. Filters nonfinite values and informational/inapplicable checks. Explicit percentage conversion for legacy fields. |
| `visualizations.py` | Removes numeric defaults. Missing categories have an annotation and no bar; real zero remains zero. Uses `Figure` and `FigureCanvasAgg` without changing the GUI backend. Unrounded UR <= 1 passes; failures have text and hatching. Concrete and reinforcement use separate axes. |
| `chap3.py` | Normalizes vehicle checkboxes; separates footway data, reads actual width and pressure mode, preserves zero and reports no-footway applicability. Removes fallback braking/impact values and invented centrifugal/seismic zeros. Safely escapes custom names. |
| `chap5.py` | Governing table uses the same records as the chart. Removes generic cross-bracing results from diaphragm tables. Partial deck dictionaries no longer imply missing checks passed or failed. Adds the missing stiffener column header and removes forced girder page breaks. |
| `executive_summary.py` | Removes unconditional design-pass statements and duplicate utilization extraction. Shows individual girder ratios rather than repeating the overall maximum for every girder. |
| `styles.py`, `chap2.py`, `chap4.py`, `chap7.py`, `chap8.py` | Bounded wrapping header regions, reserved header space, table widths including padding/rules, safer table starts and wrapping labels. Material estimate disclosure. |
| `report_generator.py` | Leaves correctly structured longtables intact, repeats member labels instead of multirow cells, respects figure/source-only options, copies data before preparing reports, exports relative asset paths, checks compiler return codes, bounds compilation to two passes plus an optional reference pass, preserves diagnostics and never returns an old PDF after failure. |
| `report_utils.py` | Separates adjacent placeholder boxes into paragraphs and escapes special characters without re-escaping generated LaTeX commands. |

`build_report_payload`, `generate_report`, `ReportResult.pdf_path` and `ReportResult.tex_path` remain compatible. Existing raw-LaTeX chapter assembly is retained. PyLaTeX is explicitly declared as a runtime dependency; PDF inspection dependencies are included in the test extras.

## Delivered evidence

- `docs/reports/Report_After.pdf`: 55 physical pages, including the title page. Body pagination ends at 54.
- `docs/reports/Report_After.tex`, `images/`, `assets/`: rebuildable source package; keep these together.
- `docs/reports/verification_case.json`: the exact synthetic inputs/results used by the verification script.
- `scripts/verify_report.py`: reproducible report-only generation, using repository-local fixtures.
- `tests/integration/conftest.py`: fixtures are now inside the repository.
- `tests/integration/test_report_regressions.py`: 21 focused regressions in addition to the 22 existing report checks.
- `docs/reports/Report_Before.pdf` is preserved. Its existing source was copied from the parent workspace into `docs/reports/Report_Before.tex` for the historical comparison test. It is not a fresh same-case engineering baseline.

The fixture contains five girders with intentional failures (G1 = 1.210 through G5 = 1.250), deck sagging UR = 65/85, and unavailable bracing/diaphragm results. These are test values, not outputs of a solver run. Missing engineering drawings appear as labelled placeholders. The report-only fixture uses an OpenSees stub and therefore cannot validate analysis or GUI integration.

## Verification performed

- Existing report integration checks: 22 passed.
- Focused regression checks: 21 passed.
- Coverage includes actual girder result schema, UR below/equal/above 1, explicit percentages, zero capacity, nonfinite/missing values, quantity sums, missing vs zero bars, vehicle serialization, special characters, custom/absent/zero footway loads, partial deck results, executive statuses, figures disabled, source-only export, caller immutability, backend preservation, governing-combination ties and compiler failure with a pre-existing PDF.
- The report compiled successfully with MiKTeX/pdflatex. Final log: **0 overfull boxes; no header-height warnings**. Non-layout hyperlink/caption notices can remain.
- All 55 pages were rendered for contact-sheet review; critical headers, continuation tables, loads, summary charts and material pages were also inspected at larger scale. No header/footer overlap was observed in this fixture. Table 5.1 spans multiple pages with repeated headers and member labels.
- The exported source and assets were copied to an independent temporary directory with spaces in its name. Both LaTeX rebuild passes exited 0 after the original generation directory had been removed.
- `git diff --check` passed.

These checks establish the report behavior for the supplied fixtures, not correctness of every engineering design or every possible model.

## Reproduce

From the repository root, with the project environment and a TeX compiler available:

```powershell
$env:PYTHONPATH = 'src'
python -m pip install pytest pypdf pillow pylatex
python scripts/verify_report.py
python -m pytest tests/integration/test_report_generator_e2e.py tests/integration/test_report_regressions.py -q
```

To rebuild only the exported source:

```powershell
Set-Location docs/reports
pdflatex -interaction=nonstopmode -halt-on-error Report_After.tex
pdflatex -interaction=nonstopmode -halt-on-error Report_After.tex
```

Use the repository's `docs/reports` artifacts; older copies and scripts in the parent `Winter-internship` folder are not the current handover. Report scripts require the project's normal Python dependencies. Compilation checks skip explicitly if no supported TeX compiler is available.

## Remaining acceptance work

| Item | Status / next action |
| --- | --- |
| Review findings: false utilization, invented quantities/loads, wrong footway handling, overlapping headers, mixed quantity units, missing fixtures | Fixed and covered by the checks above. |
| Complete end-diaphragm utilization and quantity numbers | Backend dependency. Supply independently validated, member-attributable results; do not substitute generic bracing values. |
| Braking helper failure and unavailable centrifugal/seismic results | Report handles absence honestly. Numeric coverage needs verified backend results or a separately validated engineering calculation fix. |
| Full GUI Design -> Generate Report | Pending in a fully configured Osdag environment using a real saved bridge model. |
| Same-case before/after engineering regression | Pending that real model and its baseline outputs. Current historical PDF comparison is a presentation check only. |
| Visual acceptance for real models, long metadata, more girders and dense real load combinations | Repeat render review on the real acceptance case. The synthetic five-girder case is verified. |
| Submission | Feature branch: `feature/report-refactor` in `89Aman/OsdagBridge`. No pull request or collaborator invitation is included in this push. Repository-owner access is needed for collaborator administration. |

No numeric backend formulas were invented to close these dependencies. The task's report corrections are complete; full engineering/GUI acceptance must not be claimed until the remaining work is performed.

## Submission contents

The feature branch retains implementation code, dependencies, tests, before/after PDFs, exported LaTeX and its assets, the synthetic verification case, the reproduction script, and this technical checklist. The obsolete implementation-plan document was removed. Temporary compiler logs and local caches are not submission deliverables.
