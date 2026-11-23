
> **Note:** `deliverables/` and `*.zip` are intentionally **git-ignored**. They are generated locally (see the reproduction commands) and/or published by CI to the public `ci-reports` branch. Upload the PDFs/ZIP separately with your submission; they are not part of the git diff.

# OsdagBridge Report Generator — submission checklist

[![Report generator CI](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml/badge.svg?branch=report-generator-enhancements)](https://github.com/danish9661/OsdagBridge/actions/workflows/report-ci.yml)

Branch: `report-generator-enhancements`
Repo: https://github.com/danish9661/OsdagBridge

## CI status

The badge above tracks `.github/workflows/report-ci.yml` on this branch. It runs
on every push, on every PR (open/synchronize/reopen/ready), nightly at 02:00 UTC
and on manual dispatch. A green badge means all checks below passed on the
latest run.

| CI check | What it does | Last local verification |
|---|---|---|
| Unit tests | `pytest tests/unit` | **9 passed** |
| Sample PDF build | `generate_sample_reports.py` | `CI_Report.pdf` produced |
| Structure verification | `\endhead ≥ 40`, UR + material charts, title | 50 / 1 / 1, title present |
| Font embedding | `pdffonts`: zero non-embedded fonts; PDF not encrypted | 0 / no |
| Baseline build | clones upstream `d74f56d` and rebuilds baseline PDF | 44 pages |
| Before/after image | `make_ci_comparison.py` page 11 | 1050×800 PNG |
| PR reporting | posts results table + embeds preview/comparison, links browser-viewable PDF on `ci-reports` | validated (YAML + local simulation) |
| Artifact | uploads `ci-report` (PDF + TeX + previews + logs) | configured |
| Nightly | cron `0 2 * * *`; opens/updates `nightly-ci` issue on failure | configured |

The full workflow is 15 steps; all commands were executed locally against the
current tree and passed.

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
| Note on empty cells | Intentional: `---` appears only where the backend produced no value (e.g. cross-bracing connection results were `None` for the small sample forces). Explained in the Technical Report. |
| Speed | First export **1.90 s**; identical repeat export / preview **0.0002 s** (SHA-256 payload cache) |
| CI | `.github/workflows/report-ci.yml` — tests + build on every push/PR, PR comment + artifact |
| ZIP | `OsdagBridge_Report_Task_Deliverables.zip` |

**If the form allows only one PDF and one video:** submit
`submission/OsdagBridge_Submission.pdf` (merged technical report + before +
after + real design, 150 pp) and `submission/Demo_Video_1080p.mp4`. The
individual files are still listed above and in `submission/`.

## Remaining manual steps (GitHub account required)

1. Add `Nidhikhare12` as a collaborator: repo → **Settings → Collaborators → Add people**.
2. Optional: open a PR from `report-generator-enhancements` to upstream `dev`:
   https://github.com/danish9661/OsdagBridge/pull/new/report-generator-enhancements
3. Submit the repo link, the two required PDFs and the technical document as required.

A silent **1920×1080** demo is included at `deliverables/Demo_Video.mp4` / `Demo_Video_1080p.mp4` (75 s), plus a 34 s real-time X11 capture `Demo_Live_X11_1080p.mp4`. Upload the 1080p demo as an unlisted YouTube video and include the link.

The full conda environment is installed at `/home/danish1075/miniconda3/envs/osdagbridge-env`; all GUI/report tests were re-run there with real OCC, osdag_core, fiona and PySide6 (no stubs).


### Local submission pack

A clean, git-ignored folder `submission/` contains the files to upload:
`Report_Before.pdf`, `Report_After.pdf`, `Technical_Report.pdf`,
`Demo_Video_1080p.mp4`, plus supporting `Report_Real_Design.pdf` and
`Demo_Live_X11_1080p.mp4`. The full artefact set remains in `deliverables/`;
CI publishes built PDFs to the public `ci-reports` branch.
