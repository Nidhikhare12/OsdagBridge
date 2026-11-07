# Current correction tests

Python 3.12 with the configured real pdfTeX and PyMuPDF paths reported 23 passed. The generated Chapter 5 regression checks the actual bracing force, retained exported efficiency, missing matching capacity, and the distinction between crack-width and reinforcement checks. The desktop regeneration and complete page-by-page review are recorded in CORRECTION_VERIFICATION.md. Both report compiler passes succeeded. The PDF SHA-256 is e9895d685304129016bffa8aef839b6b087329ec9380cb4805ddbe5bab6ae551.

# Superseded verification record

The previous PDF and test observations below predate the bracing correction. See CORRECTION_VERIFICATION.md for the current result.

# Test results and PDF review

## Build and desktop runs

| Evidence | Observed result |
| --- | --- |
| Branch and report source | `feat/fossee-latex-reports` at `f9784bac0cf98584158d635889b9c6a9af615be5` |
| Windows environment | Python 3.12.16, PySide6 6.11.3, Matplotlib 3.11.2, NumPy 2.5.4, OpenSeesPy 3.8.0.0, pdfTeX 1.40.28 |
| Pre-change pytest | 17 passed using the activated Conda environment |
| Final pytest | 21 passed using `python -m pytest -q`, including the real two-pass compiler pagination test |
| Enhanced desktop | 8 stages completed, exit 0, pdfTeX return codes 0 and 0, 576 input keys and 1,066 output keys captured |
| Alternate desktop | Exit 0, pdfTeX return codes 0 and 0, one footpath with Class A and 70R Tracked saved in Additional Inputs. The deck designer still reported Class70R(W). |
| Exported TeX | Two real compiler passes returned 0 from the final TeX and sibling assets. Extracted text and 0.45-scale raster output matched all 57 pages. |
| Git and baseline | `git diff --check` passed. The detached baseline worktree was clean. The saved OSI and original PDF hashes match the preserved values. |

Set `OSDAG_PDFLATEX` and `OSDAG_PDF_PYTHON` as described in REPRODUCTION_GUIDE. The 21 tests include source and formatter checks, controlled result fixtures, mocked compiler boundaries, and a real pdfTeX/PyMuPDF regression. The two desktop runs are separate from the pytest total. The controlled pagination test checks that 48 member rows survive across at least three pages, each page has one continuation header, the caption appears once, and identifiers stay above the footer.

The desktop harness supplies file picker and report dialog responses. The normal loader, GUI validation, worker threads, solver, output dock figure capture, report generator and bundled compiler ran. No alternate load result was substituted for the baseline report.

## Page review

The enhanced PDF was visually reviewed on all 57 physical pages using the seven contact sheets in `evidence/qa`. The geometry log records page-by-page image counts, text margins and green footer rule intrusions. It detected zero body words beyond the horizontal text bounds with the 3 pt tolerance or below the footer rule. Full-size renders confirmed the defect and chart pages. The original baseline has 58 pages and is preserved byte-for-byte.

| Physical page(s) | Review finding |
| --- | --- |
| 3–5 | Overall FAIL and girder FAIL agree. The final geometry caption and table share page 5. G1–G4 display 1.537, 1.545, 1.577 and 1.577. |
| 9–10 | The dimensions show 1670 mm depth, 10 mm web and 510 mm flange width. The stiffener input table continues with its header. |
| 13–16 | Vehicle and footpath tables are separate. Missing load values are labeled. The load and earthquake tables continue with their headers. |
| 17–22 | The demand table repeats its grouped heading and includes both support reactions. The empty duplicate table was removed. Report-only analysis extrema are legible below the plots. |
| 31–32 | Table 5.7 has all six G4 rows with the member identifiers inside the grid and clear of the footer. |
| 35 | Table 5.12 has exactly one heading below the caption, with all four girder rows. |
| 43–45 | Diaphragm data is explicitly unavailable. Section 5.5 contains the utilization chart with four labeled components, the 1.0 limit and distinct result labels. |
| 46–50 | CAD images are present. The diaphragm figures depict the configured CAD geometry. |
| 51–52 | The quantity table and plot identify the reinforcement estimate. The unavailable diaphragm steel annotation clears the chart border. |
| 53–57 | Standards, assumptions, limitations and references are legible. |

The final pdfTeX log contains 13 overfull box notices and 20 recovered infinite-glue notices. No missing-character notice was emitted. The notices remain reproducible in the supplied log. Visual review and extracted geometry found no associated clipped columns or body text crossing the footer in this design.

## Remaining limitations

- The alternate run verified actual GUI state, report values, and engine execution. Its deck result still uses a wheeled 70R vehicle with that class deselected, and the analyser still creates its code-based vehicle cases. The configured custom footpath pressure is displayed separately from the analysed footpath dead load.
- The final analysis emitted 27 missing thermal-load case warnings. Braking and centrifugal force magnitudes, and separate wind and seismic force values for the load tables, were unavailable in the capture.
- The baseline before report predates full input/output dictionary and execution log capture. Compare recorded values in the preserved report and the enhanced dictionaries. The baseline worktree remained untouched.
- The project location remained in the saved and analysed dictionary and in the PDF, with 44 m/s wind speed. The earlier GUI reload did not refresh its location label. The load choices also reverted on one OSI reload, so the alternate run reapplied them with real GUI controls.
- PySide6 6.11.3 exceeds the separate requirements file's 6.9.3 upper bound. The tested configuration completed. Compatibility with 6.9.3 was outside this run. Earlier startup logs reported Windows diagnostic `0x8001010d`. The final capture completed and did not emit that diagnostic.
- End diaphragm results contain three empty pair dictionaries. The diagram is drawn from configured inputs and the chart marks UR and tonnage unavailable. A controlled test checks the separate populated result schema.
- The report changes are verified for this bridge. Under a gate requiring actual solver enforcement of every selected vehicle and custom footpath pressure, requirement 3 remains partial. No full technical readiness claim is made for that gate.

The manifest records source revisions, page counts, compiler codes and hashes. The alternate session log records the commit at that run's start. The original `Report_Before.pdf` and `test-design.osi` hashes are unchanged.
