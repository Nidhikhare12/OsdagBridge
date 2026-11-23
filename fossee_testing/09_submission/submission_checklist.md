# FOSSEE Screening Task Submission Checklist

Use this checklist to verify compliance with all requirements of the **FOSSEE Winter Internship 2026 Screening Task: OsdagBridge Software Testing & Issue Reporting** prior to final submission.

---

## 1. Repository & Workspace Integrity

- [x] **Workspace Isolation**: All testing activities, documentation, scripts, and logs are contained strictly within `fossee_testing/`.
- [x] **Core Code Protection**: No original application files in `src/`, `tests/`, `examples/`, `docs/`, or `tools/` have been modified, renamed, moved, or deleted.
- [x] **Configuration Protection**: `environment.yml`, `requirements.txt`, and `pyproject.toml` remain unmodified.
- [x] **Dependency Integrity**: No unauthorized packages were installed or removed.
- [x] **Git Cleanliness**: No unapproved commits or unauthorized git pushes have been made.

---

## 2. Testing Workspace Completeness

- [x] **Directory Hierarchy**: All 9 required directories exist exactly as specified.
- [x] **Project Planning**:
  - [x] `testing_strategy.md` completed with all testing pillars and methodologies.
  - [x] `project_scope.md` completed with in-scope/out-of-scope boundaries.
  - [x] `testing_schedule.md` completed with phase breakdowns and milestones.
- [x] **Test Cases**:
  - [x] `test_case_register.csv` populated with structured test case definitions.
  - [x] `basic_input_tests.md` detailed test specifications.
  - [x] `custom_material_tests.md` detailed test specifications.
  - [x] `additional_input_tests.md` detailed test specifications.
  - [x] `multi_run_tests.md` detailed test specifications.
  - [x] `dictionary_tests.md` detailed test specifications.
  - [x] `cad_plot_tests.md` detailed test specifications.
  - [x] `osi_files/` directory prepared for project saves.
- [x] **Test Data**:
  - [x] `test_parameters.md` comprehensive parameters, ranges, and units reference.
  - [x] `input_profiles/` and `expected_results/` directories structured.
- [x] **Test Execution**:
  - [x] `execution_summary.csv` structured with all required columns, supporting 3+ consecutive runs.
- [x] **Bug Reports**:
  - [x] `bug_register.csv` structured with all required columns; zero synthetic or invented bugs.
- [x] **Automation Scripts**:
  - [x] `compare_dictionaries.py` operational with tolerance and deep comparison support.
  - [x] `validate_inputs.py` operational with native and standalone validation modes.
  - [x] `generate_test_summary.py` operational for metrics and report generation.
- [x] **LaTeX Final Report**:
  - [x] `main.tex` structured with title page, abstract, table of contents, and all 14 section chapters.
  - [x] `references.bib` with complete citations for IRC/IS codes and tools.
  - [x] All 14 modular chapter files in `sections/`.
  - [x] `figures/` directory prepared.
- [x] **Video Demonstration**:
  - [x] `recording_plan.md` complete with scene breakdown and pre-recording checklist.
  - [x] `video_link.md` complete with metadata and timestamp placeholders.
- [x] **Submission Pack**:
  - [x] `submission_checklist.md` completed.
  - [x] `github_issue_links.md` register prepared.

---

## 3. Data Integrity & Scientific Rigor

- [x] **Zero Synthetic Data**: No fabricated test results, mock screenshots, or imaginary bugs are populated.
- [x] **Usable Templates**: All CSV files use standard comma delimiters and RFC 4180 compliant formats.
- [x] **Documentation Clarity**: Markdown formatting follows consistent heading styles, tables, and file links.
