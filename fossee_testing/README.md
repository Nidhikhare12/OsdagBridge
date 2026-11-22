# FOSSEE Winter Internship 2026: OsdagBridge Software Testing Workspace

Welcome to the **FOSSEE Testing Workspace** for **OsdagBridge**. This dedicated workspace is organized to support systematic software quality assurance, verification & validation (V&V), bug identification, code-level root cause analysis, automation scripting, and comprehensive technical documentation as part of the FOSSEE Winter Internship 2026 screening task.

---

## 1. Project Background & Context

- **Target Application**: [OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge)
- **Internship Candidate Repository**: [Pranshu10khtk/OsdagBridge](https://github.com/Pranshu10khtk/OsdagBridge)
- **Domain**: Automated analysis, design, CAD modeling, and design documentation of steel and composite bridges compliant with Indian Standard codes (IRC:5–2015, IRC:6–2017, IRC:22–2015, IRC:24–2010, IS 800:2007).
- **Core Technology Stack**: Python 3.10+, PySide6 (Qt GUI), OpenCASCADE / pythonocc-core (3D CAD), Matplotlib (analysis & envelope plotting), OpenSeesPy / OspGrillage / native numerical FEM solvers, LaTeX (report compilation).

---

## 2. Strict Workspace Governance & Safety Rules

To preserve software integrity and maintain scientific rigor:
1. **Repository Boundary**: Testing activities, test data, logs, bug reports, and LaTeX sources reside strictly inside `fossee_testing/`.
2. **Immutability of Source Code**: Application files in `src/`, `tests/`, `examples/`, `docs/`, and package recipes are protected and remain unmodified.
3. **No Synthetic Results**: No fictitious test runs, mock execution logs, or fabricated defect screenshots are permitted. Every logged observation must originate from a verified execution run.
4. **Git Discipline**: No commits or remote pushes are executed without explicit authorization.

---

## 3. Directory Layout & Architecture

```text
fossee_testing/
│
├── README.md                           # Master testing roadmap and workspace documentation
│
├── 01_project_planning/                # Strategy, operational boundaries, and schedules
│   ├── testing_strategy.md             # Quality assurance methodology and verification pillars
│   ├── project_scope.md                # Boundaries, covered modules, and out-of-scope items
│   └── testing_schedule.md             # Milestones, task tracking, and deliverable timeline
│
├── 02_test_cases/                      # Systematic test specifications and registers
│   ├── test_case_register.csv          # Master register tracking all functional and edge test cases
│   ├── basic_input_tests.md            # Geometric, skew, and carriageway input test specs
│   ├── custom_material_tests.md        # Steel and concrete custom material property tests
│   ├── additional_input_tests.md       # Superstructure, sub-structure, loading, and limit-state tests
│   ├── multi_run_tests.md              # Consecutive run persistence, memory leak, and cache tests
│   ├── dictionary_tests.md             # Input and output dictionary schema and type verification
│   ├── cad_plot_tests.md               # 3D CAD visualization and 2D envelope plot verification
│   └── osi_files/                      # Repository of .osi project files for test cases
│
├── 03_test_data/                       # Test datasets and parameter catalogs
│   ├── input_profiles/                 # Parameter sets, edge-case YAML/JSON configs
│   ├── expected_results/               # Theoretical and benchmark calculation baselines
│   └── test_parameters.md              # Comprehensive parameter ranges, types, and limits reference
│
├── 04_test_execution/                 # Logs, runs, and execution records
│   └── execution_summary.csv           # Multi-run execution history with pass/fail outcomes
│
├── 05_bug_reports/                     # Defect management and tracking
│   └── bug_register.csv                # Defect register tracking severity, root causes, and fixes
│
├── 06_automation_scripts/              # Automated verification tools
│   ├── compare_dictionaries.py         # Dictionary diff and floating-point tolerance comparator
│   ├── validate_inputs.py              # Batch input validator using OsdagBridge core engine
│   └── generate_test_summary.py        # Automated test execution metrics and markdown reporter
│
├── 07_documentation/                   # LaTeX final report package
│   └── report/
│       ├── main.tex                    # Primary LaTeX document root
│       ├── references.bib              # Standard codes, mathematical models, and library citations
│       ├── sections/                   # Modular LaTeX chapters (14 distinct chapters)
│       └── figures/                    # High-resolution architectural and execution figures
│
├── 08_video_demo/                      # Demonstration video production
│   ├── recording_plan.md               # Video script, scene breakdown, and technical storyboard
│   └── video_link.md                   # Video URL, timestamps, and hosting references
│
└── 09_submission/                      # Deliverables verification
    ├── submission_checklist.md         # Final pre-submission compliance audit
    └── github_issue_links.md           # Tracking list of reported upstream GitHub issues
```

---

## 4. How to Use This Workspace

### Phase 1: Planning & Setup
- Review `01_project_planning/testing_strategy.md` to understand verification pillars (IRC compliance, dictionary schemas, CAD geometry).
- Check `01_project_planning/project_scope.md` to ensure tests target the active Plate Girder Bridge module and its interactions.

### Phase 2: Test Case Design
- Define test cases across the specialized categories in `02_test_cases/`.
- Ensure all test cases are cataloged in `02_test_cases/test_case_register.csv` with a unique `Test ID` (e.g., `TC_BI_001`, `TC_CM_001`).
- Save reproducible project states as `.osi` files in `02_test_cases/osi_files/`.

### Phase 3: Test Execution & Logging
- Run test cases via OsdagBridge GUI (`run_desktop.bat`) or CLI (`run_cli.bat`).
- Log execution results into `04_test_execution/execution_summary.csv`.
- For multi-run tests, record at least three consecutive execution cycles per configuration to verify state stability.

### Phase 4: Defect Investigation & Reporting
- When an unexpected behavior, exception, validation failure, or visual glitch occurs, record it in `05_bug_reports/bug_register.csv`.
- Isolate the defect to the specific source file (e.g., `validator.py`, `cad_3d.py`, `initial_sizing.py`).
- Formulate a clear code-level suggested fix and record the corresponding GitHub Issue link.

### Phase 5: Automation Scripting
- Use `06_automation_scripts/compare_dictionaries.py` to compare consecutive input/output dictionaries.
- Run `06_automation_scripts/validate_inputs.py` to batch-evaluate `.osi` files against core validation rules.
- Generate metrics using `06_automation_scripts/generate_test_summary.py`.

### Phase 6: Report Compilation & Submission
- Complete LaTeX report sections inside `07_documentation/report/sections/`.
- Compile `07_documentation/report/main.tex` using `pdflatex` or `latexmk`.
- Finalize the demonstration video according to `08_video_demo/recording_plan.md` and update `08_video_demo/video_link.md`.
- Complete the pre-submission check in `09_submission/submission_checklist.md`.
