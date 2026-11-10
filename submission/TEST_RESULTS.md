> Current evidence: the November 10 desktop report was built from `c5ec65bf334106e72cd8a1607f70f890771f764c`. Both desktop compiler passes and both independent portable compiler passes succeeded; 25 tests passed. The nine-page technical report includes direct baseline comparison and current charts. Earlier sections below are historical.

# Test results and report verification

The earlier report was generated on 9 November 2026 from source commit `80e44e595357af4b6cb3e1efd0623cc1cb598cca` using the preserved test-design.osi and report selections. The displayed report date matches the original comparison report. The source changes in the subsequent packaging commit contain documentation only.

| Verification | Result |
| --- | --- |
| Supported test suite | `python -m pytest -q` returned **24 passed**. The run included unit tests, controlled result fixtures, mocked compiler boundaries and a real pdfTeX/PyMuPDF pagination regression. |
| Desktop workflow | The real Qt loader, design worker, structural analysis, output-dock figure capture and report worker completed. Desktop process exit code was 0. |
| PDF compiler | Both report pdfTeX passes returned 0. Two independent portable compilation passes also returned 0. |
| Portable output | Extracted text and 0.45-scale rendered pixels matched on all 57 pages. |
| PDF review | Every physical page was reviewed using the contact sheets in evidence/nov09-qa. Geometry scanning flagged no body words outside the text area or below the footer rule. The modified pages were reviewed at higher resolution. |
| Cover and TOC | The cover has no ordinary numbered footer. The following TOC begins the interior page numbering at page 1. |
| Header and footer regressions | G4 stiffener rows continue above the footer on physical pages 31–32. The girder summary on page 35 has a single header below its caption. |
| Live-load tables | Vehicle and footpath tables have parameter, value and unit columns. The baseline and captured alternate-input dictionaries both generated the expected tables. The alternate GUI run was captured on the prior revision; its solver limitations remain. |
| Utilization chart | The chart on page 45 uses vertical bars, a utilization-ratio y-axis and a horizontal red dashed line at 1.0. Girder 1.577 and deck 0.9914 are derived from captured results. Cross bracing and diaphragms are unavailable. |
| Material quantities | The chart reflects 32.89 t girder steel, 0.47 t bracing steel, 63.00 m³ concrete and a 7.56 t reinforcement estimate. End-diaphragm weight is unavailable. |
| Baseline integrity | The original baseline PDF remains SHA-256 `3c5b689249b8d03492acff357e063e604340035bd4c8fa59db29ed1d6536a25a`. The test input remains `95d60509867d267bc396dea3e92e2bcfb10d508a39f2e0415d78dc13370847e1`. |

The final PDF SHA-256 is `9f4fabeb7174c96fb061ada4149d0c37f156d9bd0c58d228115a6eaef4bd1ffa`. The captured dictionaries, desktop log, pdfTeX log, portable compiler logs, test output and page geometry log are under submission/evidence.

## Remaining limitations

- The bracing export contains efficiencies 0.740 and 0.610 but does not identify their controlling denominators. They are displayed separately from verified demand/capacity ratios. Diaphragm design entries are empty.
- The selected vehicles and custom footpath pressure are inputs. The prior alternate desktop run showed that the deck designer still selected a wheeled 70R case. The solver's application of those inputs is outside this report refactoring.
- The final analysis emitted 27 missing thermal-case warnings. The report marks unavailable wind, seismic, braking and centrifugal magnitudes as unavailable.
- The compiler log contains 13 overfull-box and 20 recovered infinite-glue notices, with no missing-character notices. The 57-page visual and geometry review found no corresponding footer crossing or clipped text for this design. These warnings can still merit attention on other inputs.
- PySide6 6.11.3 exceeds the requirements.txt cap of 6.9.3. The tested environment completed successfully. Compatibility at the capped version was not tested.
- The original baseline predates full input/output and log capture. Its PDF and the exact saved design remain preserved.

The official detailed task document was not accessible beyond its title to the browser. The six requirement descriptions supplied in the user's request were used for this verification.


## Final handoff review

The source and tests were unchanged during the handoff. The recorded 24-test run was inspected and was not rerun. The 57-page report and original baseline hashes match the captured manifest. The input and output snapshots confirm the girder and deck values, the two stored cross-bracing efficiencies, and empty diaphragm results. The desktop log identifies source commit 80e44e595357af4b6cb3e1efd0623cc1cb598cca and records two successful pdfTeX passes. The portable recompilation record reports matching text and renders.

At the November 9 handoff the technical changes report had six pages. Pages 5–6 compare genuine crops from the historical enhanced draft and current report. The earlier draft is explicitly labeled. Its current SHA-256 is recorded in evidence/manifest.json.

The read-only GitHub fork check on 9 November 2026 found no feat/fossee-latex-reports branch on origin. The fork's default dev branch responded at the original baseline. Publication and collaborator access are the applicant's manual actions.

## Final independent pass (2026-11-10)

On Python 3.12.16, the command `python -m pytest -q` with `OSDAG_PDFLATEX` set to the bundled executable and `OSDAG_PDF_PYTHON` set to the separate Python 3.13 installation containing PyMuPDF produced **25 passed in 9.83s**, with no skips. The earlier attempt produced 24 passed and one failure because the helper accidentally pointed to the Conda Python without PyMuPDF. Both logs are retained as `evidence/pytest-nov10.log` and `evidence/pytest-nov10-corrected.log`. The test suite includes actual two-pass TeX pagination compilation. The new test covers ambiguous barrier-area units; the chart test asserts distinct fills and hatching as well as explicit status labels.
The November 10 desktop run loaded `submission/test-design.osi`, completed actual analysis at 100%, and exited 0. The report worker invoked pdfTeX twice, with return codes 0 and 0. A separate two-pass portable compilation also returned 0 and matched all 57 text and rendered pages. The final report has 13 overfull-box notices, 20 recovered infinite-glue notices, zero missing-character notices, and the analysis reported 27 missing thermal-load-case warnings. Contact sheets and geometry checks cover all 57 pages; no footer intrusions were flagged by that geometry check. These observations apply to this test design and do not certify other reports or structural designs.
