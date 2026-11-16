# OsdagBridge report generator: technical changes

The report changes build on upstream `dev` commit `d74f56dd7f22925fb8148cabf5740ed8d1e39ff3`, which matches the supplied ZIP.

| Area | Implementation |
| --- | --- |
| Table continuation | `core/reports/styles.py` supplies repeat headers and continuation markers. Its chapter adapter normalizes existing longtable widths against the printable line width and preserves explicit multi-row headers, including Chapter 4. The executive summary and Chapters 1–9 use the shared layout. |
| Page layout | The shared preamble defines A4 margins, base font size, table padding, row spacing and header/footer rules. Chapter 5 fixes malformed row endings; Chapter 8 uses pageable standards tables. The G4 row and its note fit above the footer in the comparison. |
| Live loads | `chap3.py` and `load_tables.py` split road vehicles and footway loads into tables with unit columns. Vehicle names follow the selection flags, including opted-in custom vehicles. The tables use existing IRC helpers for supported factors and braking inputs. Missing inputs are shown as unavailable; the current solver exposes no centrifugal force value. |
| Utilization | `report_charts.py` reads governing ratios from the girder, deck, cross bracing and end diaphragm result structures. `chap5.py` embeds the plot in §5.5 with a dashed red line at 1.0. Missing data receives a label instead of a zero bar. The diaphragm table uses diaphragm results. |
| Quantities | `chap7.py` embeds the take-off plot. Steel is compared in tonnes; concrete volume and reinforcement weight have separate axes. `core/boq/boq_generator.py` estimates diaphragm steel from section line mass and modeled member lengths at both ends. The estimate excludes fittings and connection steel. Reinforcement uses the existing 120 kg/m³ estimate. |
| Compilation and theme | `styles.py` holds the shared document settings, table styling, status colors and PyLaTeX figure helper. `report_generator.py` stages chart images with the report assets, saves a compilable source folder, and checks both PDF compiler passes. Matplotlib uses a local canvas so it does not switch the desktop plot backend. |

Reusing the existing raw LaTeX chapter templates keeps engineering values and their display logic separate from layout settings. PyLaTeX is used for the new figure wrappers; the charts and tables consume the same calculation data as the report.

## Comparison and verification

[Original report](report-comparison/Report_Before.pdf) · [Updated report](report-comparison/Report_After.pdf)

Both reports use one calculated 20 m, four-girder custom bridge case. The original ZIP's compiler returned exit code 1 with table alignment errors but still emitted the baseline PDF. The enhanced report compiled in two successful passes. The final build showed no vertical box overflow; the updated source has a header block for each longtable. The G4 table, live-load split, and both chart pages were visually reviewed.

The sample returned utilization ratios for the girders, deck and cross bracing. It did not return an end diaphragm utilization ratio, so that chart category is labeled unavailable; its steel take-off is reported separately. The case has no footway and no explicit lane count. It is a format verification case and contains failed girder checks. The full desktop Design → Generate Report flow was not verified: the app started but the Windows desktop interaction did not finish. The calculation engine and the production report entry point were exercised directly. The drawing chapter contains placeholders because no GUI CAD exports were provided.

## Reproduce

1. Set up and activate the repository's Conda environment from `environment.yml`. Run `python -m pip install -e ".[test]"` to install the report dependency and test tools.
2. From the enhanced checkout, run `python -m pytest tests -q` (17 passed) and `python examples/report_verification/run_design_case.py`. The second command creates a local `design_case.pkl` next to the script. Only use a snapshot you generated locally.
3. Run `python examples/report_verification/render_case.py Report_After <output-directory>`. For the baseline, point `PYTHONPATH` to the original ZIP checkout's `src` directory and run the same render script with `Report_Before`. Both commands use the saved snapshot and record the second compiler pass.
