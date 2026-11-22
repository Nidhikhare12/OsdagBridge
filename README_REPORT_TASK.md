# OsdagBridge Report Generator — submission checklist

Branch: `report-generator-enhancements`
Repo: https://github.com/danish9661/OsdagBridge

## Deliverables

| Requirement | Location |
|---|---|
| Generated reports (before / after) | `deliverables/Report_Before.pdf`, `deliverables/Report_After.pdf` |
| Technical changes document | `deliverables/Technical_Report.pdf`, `docs/REPORT_ENHANCEMENTS.md` |
| Source code | `src/osdagbridge/core/reports/`, `src/osdagbridge/core/utils/common.py`, `src/osdagbridge/core/utils/codes/irc6_2017.py` |
| Central style module | `src/osdagbridge/core/reports/styles.py` |
| Chart module | `src/osdagbridge/core/reports/charts.py` |
| Extra verification PDFs | `deliverables/Report_From_GUI.pdf`, `deliverables/Report_Real_UI.pdf`, `deliverables/Report_Real_Design.pdf` |
| Screenshots | `deliverables/gui_window.png`, `deliverables/gui_after_design.png`, `deliverables/gui_after_report.png` |
| Benchmarks | `docs/BENCHMARK.md`, `docs/PERFORMANCE_DETAIL.md` |
| ZIP | `OsdagBridge_Report_Task_Deliverables.zip` |

## Remaining manual steps (GitHub account required)

1. Add `Nidhikhare12` as a collaborator: repo → **Settings → Collaborators → Add people**.
2. Optional: open a PR from `report-generator-enhancements` to upstream `dev`:
   https://github.com/danish9661/OsdagBridge/pull/new/report-generator-enhancements
3. Submit the repo link, the two required PDFs and the technical document as required.

A silent screengrab demo is included at `deliverables/Demo_Video.mp4` (50 s, 1280×800) — upload it as an unlisted YouTube video and include the link.

The full conda environment is installed at `/home/danish1075/miniconda3/envs/osdagbridge-env`; all GUI/report tests were re-run there with real OCC, osdag_core, fiona and PySide6 (no stubs).
