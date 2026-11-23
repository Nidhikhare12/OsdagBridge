# Testing Schedule & Milestone Tracking

## 1. Project Execution Phases

The testing campaign is structured into six sequential phases to ensure systematic verification, rigorous defect isolation, and high-quality documentation.

```text
Phase 1: Workspace & Environment Setup (Days 1–2)
Phase 2: Test Case Design & Baseline Preparation (Days 3–5)
Phase 3: Test Execution & Multi-Run Stability Testing (Days 6–9)
Phase 4: Defect Investigation & Root Cause Analysis (Days 10–12)
Phase 5: Automation Scripting & Verification (Days 13–14)
Phase 6: Technical Report, Video Demo & Final Submission (Days 15–18)
```

---

## 2. Activity Breakdown & Milestones

| Milestone ID | Phase / Activity | Description | Target Deliverable | Status |
| :--- | :--- | :--- | :--- | :--- |
| **M1.1** | Phase 1: Planning | Establish `fossee_testing` workspace and directory structure | Complete folder layout | Completed |
| **M1.2** | Phase 1: Planning | Define strategy, scope, parameters, and scheduling documents | Markdown planning docs | Completed |
| **M2.1** | Phase 2: Design | Author Basic Input test cases (span, width, skew limits) | `basic_input_tests.md` | In Progress |
| **M2.2** | Phase 2: Design | Author Custom Material test cases (steel grades, concrete deck) | `custom_material_tests.md` | In Progress |
| **M2.3** | Phase 2: Design | Author Additional Inputs test cases (loads, barriers, camber) | `additional_input_tests.md` | In Progress |
| **M2.4** | Phase 2: Design | Author Multi-Run, Dictionary, and CAD/Plot test specs | Markdown test suites | In Progress |
| **M2.5** | Phase 2: Design | Compile Master Test Case Register | `test_case_register.csv` | In Progress |
| **M3.1** | Phase 3: Execution | Execute Basic Geometric Input test suite on GUI and CLI | Execution logs & entries | Planned |
| **M3.2** | Phase 3: Execution | Execute Custom Material override test suite | Execution logs & entries | Planned |
| **M3.3** | Phase 3: Execution | Execute Multi-Run stability test suite (Run 1, Run 2, Run 3) | `execution_summary.csv` | Planned |
| **M3.4** | Phase 3: Execution | Execute CAD 3D rendering and 2D envelope plot tests | Screenshot & visual logs | Planned |
| **M4.1** | Phase 4: Bugs | Log all identified defects, exceptions, and anomalies | `bug_register.csv` | Planned |
| **M4.2** | Phase 4: Bugs | Perform source code root cause analysis on each logged defect | Root cause documentation | Planned |
| **M4.3** | Phase 4: Bugs | Formulate code-level fix recommendations | Suggested fix snippets | Planned |
| **M5.1** | Phase 5: Automation| Develop `compare_dictionaries.py` for automated schema diffs | Python script | Completed |
| **M5.2** | Phase 5: Automation| Develop `validate_inputs.py` for batch `.osi` verification | Python script | Completed |
| **M5.3** | Phase 5: Automation| Develop `generate_test_summary.py` for test metrics | Python script | Completed |
| **M6.1** | Phase 6: Report | Author modular LaTeX chapters (`sections/01` to `sections/14`) | LaTeX section files | Completed |
| **M6.2** | Phase 6: Report | Compile master LaTeX report (`main.tex`) to PDF | `main.pdf` | Planned |
| **M6.3** | Phase 6: Video | Record and edit project demonstration video | Video link & plan | Planned |
| **M6.4** | Phase 6: Final | Audit submission checklist and finalize GitHub issue links | `submission_checklist.md` | Planned |

---

## 3. Progress Tracking Dashboard

| Work Package | Total Items | Planned | Executed / Written | Passing | Failing | Completion % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Planning & Governance | 3 docs | 3 | 3 | 3 | 0 | 100% |
| Test Case Specifications | 6 docs | 6 | 6 | — | — | 100% |
| Test Case Register | 1 register | 1 | 1 | — | — | 100% |
| Execution Summary | 1 register | 1 | 1 | — | — | 100% |
| Bug Register | 1 register | 1 | 1 | — | — | 100% |
| Automation Scripts | 3 scripts | 3 | 3 | 3 | 0 | 100% |
| LaTeX Report Structure | 17 files | 17 | 17 | — | — | 100% |
| Video Demo Documentation | 2 docs | 2 | 2 | — | — | 100% |
| Final Submission Pack | 2 docs | 2 | 2 | — | — | 100% |
