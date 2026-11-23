# OsdagBridge Report Generator — Refactoring & Enhancements

[![Report generator CI](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml/badge.svg?branch=report-generator-enhancements)](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml)

Branch: `report-generator-enhancements`
Repository: https://github.com/danish9661/OsdagBridge

This branch implements the six requirements of the FOSSEE screening task on the
LaTeX report generator. The technical write-up is in
[`docs/REPORT_ENHANCEMENTS.md`](docs/REPORT_ENHANCEMENTS.md).

## Implemented changes

| Requirement | Implementation |
|---|---|
| Repeating longtable headers | `styles.apply_global_styles()` inserts `\endfirsthead`/`\endhead` into every `longtable`; 2 → 50 header blocks in the generated `.tex` |
| Layout, footer and spacing | Explicit page geometry (`headheight`, `headsep`, `footskip`), `\needspace` heading guards, unified table spacing constants, working `Page X of Y` footer |
| Vehicle vs footway loads | `chap3.py` emits separate *Vehicle Live Loads* and *Footway Live Load* tables; vehicle rows follow the Loading-tab selection |
| Utilization-ratio chart | `charts.utilization_ratio_figure()` bar chart with a red dashed UR = 1.0 line, embedded in Section 5.5 |
| Material quantity charts | `charts.material_quantity_figure()` panels for steel tonnage, concrete volume and reinforcement weight in Chapter 7 |
| Centralized styles | `styles.py` is the single source for geometry, colours, table rules, header/footer theme and Matplotlib settings |

## Source files

| Area | Path |
|---|---|
| Central style module | `src/osdagbridge/core/reports/styles.py` |
| Chart module | `src/osdagbridge/core/reports/charts.py` |
| Report assembly | `src/osdagbridge/core/reports/report_generator.py` |
| Load tables | `src/osdagbridge/core/reports/chap3.py` |
| UR chart | `src/osdagbridge/core/reports/chap5.py` |
| Material charts | `src/osdagbridge/core/reports/chap7.py` |
| Braking and centrifugal force | `src/osdagbridge/core/utils/codes/irc6_2017.py`, `src/osdagbridge/core/utils/common.py` |
| Sample report builder | `scripts/generate_sample_reports.py` |
| Tests | `tests/unit/test_report_styles.py` |

## Generated documents

| Document | Path |
|---|---|
| Baseline report | `submission/Report_Before.pdf` |
| Enhanced report | `submission/Report_After.pdf` |
| Technical changes document | `submission/Technical_Report.pdf` |
| Real OpenSees design report | `submission/Report_Real_Design.pdf` |
| Combined document (technical + before + after + real design) | `submission/OsdagBridge_Submission.pdf` |
| Demo video, 1920×1080, 75 s | `submission/Demo_Video_1080p.mp4` |
| Real-time capture, 34 s | `submission/Demo_Live_X11_1080p.mp4` |

The same artefacts are produced in `deliverables/` by the scripts below, and CI
publishes every built PDF to the
[`ci-reports`](https://github.com/danish9661/OsdagBridge/tree/ci-reports) branch.

## Reproduction

```bash
# Enhanced report
python scripts/generate_sample_reports.py deliverables Report_After

# Unit tests
PYTHONPATH=src python -m pytest tests/unit -q

# Real GUI path (Design + Generate Report buttons)
GUI_VISIBLE=1 PYTHONPATH=src python scripts/gui_real_ui_test.py

# Real OpenSees analysis and IRC 22 design
PYTHONPATH=src python scripts/run_full_design_test.py
```

## Verification

| Check | Result |
|---|---|
| Unit tests | 9 passed |
| Sample report | 46 pages, 50 `\endhead` blocks, UR and material charts present |
| Real GUI report | 59 pages from 1001 design output keys |
| Real OpenSees design | 997 output keys, G4 rows clear of the footer, header repeated |
| PDF metadata | title present, all fonts embedded, not encrypted |
| Readers | MuPDF, Poppler, LibreOffice and pypdf open the output without warnings |
| Export time | 1.90 s first export, 0.0002 s repeat export via SHA-256 payload cache |

## CI

`.github/workflows/report-ci.yml` runs on every push and pull request, nightly
at 02:00 UTC, and on manual dispatch:

| Check | Result |
|---|---|
| Unit tests | `pytest tests/unit` |
| Sample PDF build | `generate_sample_reports.py` |
| Structure verification | `\endhead ≥ 40`, UR and material charts, PDF title |
| Font embedding | zero non-embedded fonts, PDF not encrypted |
| Before/after image | page 11 of baseline and enhanced reports |
| PR reporting | results table, embedded preview and comparison, link to the PDF on `ci-reports` |
| Artifact | `ci-report` (PDF, TeX, previews, logs) |
| Nightly | opens or updates a `nightly-ci` issue on failure |
