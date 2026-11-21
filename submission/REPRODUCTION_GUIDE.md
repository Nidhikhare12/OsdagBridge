# Reproduce the OsdagBridge reports

The original baseline is the detached worktree at `d74f56dd7f22925fb8148cabf5740ed8d1e39ff3`. The current enhanced report was produced from `c5ec65bf334106e72cd8a1607f70f890771f764c` on `feat/fossee-latex-reports`. Later packaging commits can contain evidence and documentation.

`test-design.osi` is a 30 m optimized plate girder test bridge configured in the desktop application. It uses a 7.5 m carriageway in Mumbai (Colaba), four girders, and no footpath or median. It has failing structural checks. Use it to reproduce the software result.

## Windows desktop

1. Use the existing Python 3.12 Conda environment, including the bundled Osdag LaTeX environment. Run from the OsdagBridge repository root.
2. Launch `python -m osdagbridge.desktop` with `PYTHONPATH` set to `src`. Load `submission/test-design.osi`, click **Design**, and wait for the analysis to reach 100%.
3. Open **Design Report**. Set the project name to **OsdagBridge test design**. Select all sections, figures, TOC and PDF. Choose a fresh destination.
4. The alternate file adds a single 1.5 m footpath. After loading it, open **Additional Inputs**, select Class A and 70R Tracked only, set the footpath pressure mode to Custom and the value to 0.000004, then save and run Design. The saved advanced load settings can revert to defaults on OSI reload.

The equivalent scripted desktop session loads through the normal file handler, runs the Qt design worker, captures report images through the output dock and invokes the Qt report worker. The script supplies dialog responses and sets the report date. Run it in an interactive Windows session.

```powershell
$e = (Resolve-Path ../conda-envs/osdagbridge-env).Path
$env:PATH = "$e\Library\bin;$e\Scripts;$e;$env:PATH"
$env:PYTHONPATH = (Resolve-Path src).Path
$env:PYTHONUTF8 = '1'
& "$e\python.exe" -u submission/reproduce_report.py submission/test-design.osi verify/Report_After.pdf --report-date 2026-11-07 *> desktop.log
& "$e\python.exe" -u submission/reproduce_report.py submission/alternate-loads.osi verify/Alternate_Loads.pdf --report-date 2026-11-07 --reapply-live-load-inputs *> alternate-desktop.log
```

Each report exports its PDF, TeX, pdfTeX log, sibling assets and post-analysis dictionaries. The dictionary snapshots preserve the data used to check the report. JSON object keys are strings and non-JSON-native objects are represented as text. The earlier baseline run predates dictionary and full log capture.

## Compiler and tests

`OSDAG_PDFLATEX` must point at the working pdfTeX executable. `OSDAG_PDF_PYTHON` must point at a Python executable with PyMuPDF for the pagination test. The application tests still run under Python 3.12. In PowerShell with the environment above active:

```powershell
$env:OSDAG_PDFLATEX = "$e\Library\share\osdag_latex_env\bin\x86_64-windows\pdflatex.exe"
$env:OSDAG_PDF_PYTHON = 'C:\path\to\python-with-PyMuPDF.exe'
& "$e\python.exe" -m pytest -q
git diff --check
```

Keep `Report_After.tex` beside `Report_After_assets` and run pdfTeX twice from that directory. Set a separate job name to preserve the supplied report. Use `audit_pdf.py` with PyMuPDF and Pillow to render and record page geometry.

```powershell
& $env:OSDAG_PDFLATEX -interaction=nonstopmode -halt-on-error -jobname=Portable_Verification Report_After.tex
& $env:OSDAG_PDFLATEX -interaction=nonstopmode -halt-on-error -jobname=Portable_Verification Report_After.tex
& $env:OSDAG_PDF_PYTHON audit_pdf.py Report_After.pdf qa
```
