# Baseline and work in progress

**Historical note:** This document records the initial attempt. For current environment, GUI and PDF results, see `CONTINUATION_STATUS.md`.

This is an incomplete screening submission. No original or enhanced PDF has been produced or visually inspected.

## Repository and environment

- Official upstream: https://github.com/Nidhikhare12/OsdagBridge, branch `dev`.
- `git fetch upstream` succeeded; fetched `upstream/dev` and feature branch started at `d74f56dd7f22925fb8148cabf5740ed8d1e39ff3`.
- Fork remote: https://github.com/Trunal2005/OsdagBridge.git. The original working tree was clean.
- Windows 11, Python 3.13.5, Git 2.54.0.windows.1, pytest 9.1.1, Matplotlib 3.9.2. Project metadata requires Python >=3.11,<3.13.
- Conda, PySide6, Osdag and pdflatex were not found in the active environment; `wsl --list --quiet` returned access denied. No compiler version or genuine desktop design run is available.
- `python -m pytest -q` on the baseline: 5 passed. These existing tests include placeholders and do not establish report correctness.
- After the focused changes, `python -m pytest -q`: 7 passed on Python 3.13.5 (outside the supported range). The added tests check generated Chapter 7 LaTeX and Chapter 5 source structure; neither compiles a PDF. `git diff --check` passed.
- With `PYTHONPATH=src`, `python -m osdagbridge.desktop` fails at startup with `ModuleNotFoundError: No module named 'PySide6'`.

## Report path and findings

`PlateGirderBridge.generate_design_report` copies input and output dictionaries, calls `build_report_payload`, attaches figure bytes, then calls `generate_report` in `src/osdagbridge/core/reports/report_generator.py`. The latter calculates quantities using `core/boq/boq_generator.py`, assembles chapters, writes temporary assets and LaTeX, and invokes pdflatex twice. Chapter 3 uses UI keys for selected vehicles; Chapter 5 reads through `ReportDataBridge`; Chapter 7 uses calculated quantity fields injected into the inputs. `preamble` defines geometry, colors, table spacing and headers/footers inline.

Chapter 7 contained an unclosed LaTeX group. Its table and the girder design summary lacked continuation headers. Focused changes address these two tables only. Many other tables still lack continuation headers; the existing multirow blocks can also affect page breaks. These changes have not been compiled or visually verified. The GUI, before/after PDFs, page-30/G4 reproduction, six-requirement completion, charts, style centralization, and end-to-end testing remain outstanding.

Additional hazards requiring investigation: `generate_report` clears `payload.figure_data`, which affects repeated use of a payload; the copied `.tex` refers to temporary figure paths; chapter 3 computes a footpath value but its table displays a different input field; quantity defaults include LaTeX placeholders and must not be treated as numeric data. Determine the actual availability and units of each design result before charting.

## Next steps

Create the supported Conda environment from `environment.yml`, install the application's desktop and LaTeX dependencies, and use a supported example to generate and inspect a genuine baseline PDF before further changes. Record inputs, report selection, compiler output, page count and hash. Then complete and validate all requirements with the same design in the enhanced report. Do not represent isolated tests as integration proof.
