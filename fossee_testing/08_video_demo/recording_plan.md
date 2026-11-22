# Video Demonstration Recording Plan & Storyboard

## 1. Video Objectives & Target Audience

This recording plan outlines the structure for the official video demonstration required for the **FOSSEE Winter Internship 2026 Screening Task: OsdagBridge Software Testing & Issue Reporting**.

- **Target Duration**: 5 – 8 minutes
- **Recording Resolution**: 1080p (1920x1080) at 30 or 60 fps
- **Audio**: Clear narration with noise suppression
- **Target Platform**: YouTube (Unlisted) / Google Drive

---

## 2. Storyboard & Scene Breakdown

### Scene 1: Introduction & Project Context (0:00 – 0:45)
- **Visual**: Title slide showing Candidate Name, GitHub repository links, FOSSEE Winter Internship 2026 task title, and OsdagBridge logo.
- **Narrative**:
  - Introduce self and candidate repository (`Pranshu10khtk/OsdagBridge`).
  - Outline task objective: Systematic testing, boundary verification, state isolation, and defect reporting on OsdagBridge without modifying existing application code.
  - Present the dedicated `fossee_testing/` workspace layout.

### Scene 2: Application Launch & Environment Walkthrough (0:45 – 1:30)
- **Visual**: Terminal showing launching via `run_desktop.bat`, PySide6 desktop splash screen, and Plate Girder Bridge module opening.
- **Narrative**:
  - Explain execution environment (Python 3.12, PySide6, OpenCASCADE/pythonocc, OpenSeesPy, OspGrillage).
  - Highlight the clean initialization of input docks and CAD viewport.

### Scene 3: Basic Geometric Inputs & Boundary Validation (1:30 – 2:45)
- **Visual**: Screen capture of entering inputs into the Main Window.
  - Input valid span ($25.0\text{ m}$), carriageway ($7.5\text{ m}$), skew ($0.0^\circ$).
  - Demonstrate boundary validation: Input invalid span ($50.0\text{ m}$), invalid narrow carriageway ($3.5\text{ m}$), and out-of-range skew ($75.0^\circ$).
  - Show error popups and input sanitization guards.
- **Narrative**:
  - Discuss compliance with IRC:5 Clause 104.3.1 and IRC:24 skew limits.
  - Show how `BridgeInputValidator` rejects invalid inputs.

### Scene 4: Custom Material Definition & Verification (2:45 – 3:45)
- **Visual**: Navigate to Material dock $\rightarrow$ Select "Custom" for Girder and Deck.
  - Enter custom steel properties ($f_y = 345\text{ MPa}, E = 200\text{ GPa}$).
  - Enter custom concrete properties ($f_{ck} = 45\text{ MPa}, E_{cm} = 34\text{ GPa}$).
  - Run initial sizing and verify updated modular ratio ($m \approx 5.88$).
- **Narrative**:
  - Explain how custom materials override default presets and correctly influence modular ratios and transformed section inertia.

### Scene 5: Multi-Run Testing & State Isolation (3:45 – 4:45)
- **Visual**: Execute consecutive solves in a single GUI session (Run 1: 20m $\rightarrow$ Run 2: 36m $\rightarrow$ Run 3: 20m).
  - Open terminal and run `python compare_dictionaries.py --file1 state_run1.json --file2 state_run3.json`.
- **Narrative**:
  - Demonstrate deterministic state isolation across consecutive design cycles.
  - Prove that reverting inputs in Run 3 restores the exact state of Run 1 with zero memory contamination.

### Scene 6: 3D CAD Visualization & 2D Response Plots (4:45 – 5:45)
- **Visual**:
  - Interact with 3D CAD window: Rotate, zoom, and pan the 4-girder composite bridge.
  - Toggle skew angle to $30^\circ$ and show skewed bearing line alignment.
  - Switch to 2D Plot dock and cycle through load combinations (Dead Load, Live Load Class 70R, ULS Envelope) to demonstrate real-time curve updating.
- **Narrative**:
  - Highlight OpenCASCADE rendering fidelity and Matplotlib dynamic plot updates.

### Scene 7: Defect Walkthrough & Code-Level Suggested Fixes (5:45 – 6:45)
- **Visual**: Display `05_bug_reports/bug_register.csv` and show source code diffs in VS Code.
- **Narrative**:
  - Present key defects identified during the testing campaign.
  - Walk through root causes in source code files (e.g., in validator or CAD cleanup).
  - Explain non-invasive, robust fix proposals.

### Scene 8: Automation Tools, Report & Conclusion (6:45 – End)
- **Visual**:
  - Run `python generate_test_summary.py` in terminal.
  - Showcase compiled LaTeX technical report PDF (`main.pdf`).
  - Show GitHub issue links and submission checklist.
- **Narrative**:
  - Summarize achievements and conclude presentation.

---

## 3. Pre-Recording Checklist

- [ ] Display resolution set to 1920x1080 (100% DPI scaling).
- [ ] Desktop icons organized; unnecessary background applications closed.
- [ ] Working microphone with pop filter and noise gate tested.
- [ ] Python conda environment activated and confirmed working.
- [ ] Test `.osi` files pre-loaded in `02_test_cases/osi_files/`.
