
> **Note:** `deliverables/` and `*.zip` are intentionally **git-ignored**. They are generated locally (see the reproduction commands) and/or published by CI to the public `ci-reports` branch. Upload the PDFs/ZIP separately with your submission; they are not part of the git diff.

# OsdagBridge Report Generator — submission checklist

[![Report generator CI](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml/badge.svg?branch=report-generator-enhancements)](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml)

Branch: `report-generator-enhancements`
Repo: https://github.com/danish9661/OsdagBridge

## Deliverables

| Requirement | Local path (git-ignored — upload separately) |
|---|---|
| Generated reports (before / after) | `deliverables/Report_Before.pdf`, `deliverables/Report_After.pdf` |
| Technical changes document | `deliverables/Technical_Report.pdf`, `docs/REPORT_ENHANCEMENTS.md` |
| Source code | `src/osdagbridge/core/reports/`, `src/osdagbridge/core/utils/common.py`, `src/osdagbridge/core/utils/codes/irc6_2017.py` |
| Central style module | `src/osdagbridge/core/reports/styles.py` |
| Chart module | `src/osdagbridge/core/reports/charts.py` |
| Extra verification PDFs | `deliverables/Report_From_GUI.pdf`, `deliverables/Report_Real_UI.pdf`, `deliverables/Report_Real_Design.pdf` |
| Screenshots | `deliverables/gui_window.png`, `deliverables/gui_after_design.png`, `deliverables/gui_after_report.png`, `deliverables/live_preview.png` |
| Demo video | `deliverables/Demo_Video.mp4`, `deliverables/Demo_Video_1080p.mp4` (1920×1080, 75 s) |
| Real-time capture | `deliverables/Demo_Live_X11_1080p.mp4` (34 s, Xvfb/x11grab, live analysis log) |
| Data notes | `docs/REPORT_DATA_NOTES.md` — explanation of empty cells and fixed rows |
| Benchmarks | `docs/BENCHMARK.md`, `docs/PERFORMANCE_DETAIL.md`, `docs/OPTIMIZATION_NOTES.md`, `docs/PDF_VIDEO_REVIEW.md` |
| Speed | First export **1.90 s**; identical repeat export / preview **0.0002 s** (SHA-256 payload cache) |
| CI | `.github/workflows/report-ci.yml` — tests + build on every push/PR, PR comment + artifact |
| Changelog | `CHANGELOG.md` |
| ZIP | `OsdagBridge_Report_Task_Deliverables.zip` |

## Remaining manual steps (GitHub account required)

1. Add `Nidhikhare12` as a collaborator: repo → **Settings → Collaborators → Add people**.
2. Optional: open a PR from `report-generator-enhancements` to upstream `dev`:
   https://github.com/danish9661/OsdagBridge/pull/new/report-generator-enhancements
3. Submit the repo link, the two required PDFs and the technical document as required.

A silent **1920×1080** demo is included at `deliverables/Demo_Video.mp4` / `Demo_Video_1080p.mp4` (75 s), plus a 34 s real-time X11 capture `Demo_Live_X11_1080p.mp4`. Upload the 1080p demo as an unlisted YouTube video and include the link.

The full conda environment is installed at `/home/danish1075/miniconda3/envs/osdagbridge-env`; all GUI/report tests were re-run there with real OCC, osdag_core, fiona and PySide6 (no stubs).
