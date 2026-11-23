# FOSSEE Winter Internship 2026: Project Demonstration Plan

## Video Deliverable Specifications
- **Project Name:** OsdagBridge Desktop Application (UI, 2D CAD, and Plotting Enhancements)
- **Organization:** FOSSEE, IIT Bombay
- **Target Role:** Winter Internship 2026 Screening Task
- **Video File:** `FOSSEE_Project_Demonstration.mp4`
- **Preview File:** `Recording_Preview.mp4`
- **Duration:** 3:45 (225 seconds / 6750 frames)
- **Resolution:** 1920 × 1080 (Full HD, 16:9 widescreen)
- **Framerate:** 30 FPS
- **Audio:** Silent (as requested; professional lower-third subtitle banners guide the viewer)
- **Format:** MP4 (Video: H.264 / `libx264`, `yuv420p`, CRF 18)

---

## Detailed Scene-by-Scene Demonstration Timeline

### 1. Project Introduction (0:00 – 0:30 | 900 Frames)
- **0:00 – 0:12 (360 frames): Title & Architecture Presentation**
  - High-impact opening slide introducing OsdagBridge, IIT Bombay FOSSEE screening submission, candidate details, and core technologies: Python 3.11, PySide6, OpenSeesPy, OspGrillage, Matplotlib, and OpenCascade.
- **0:12 – 0:22 (300 frames): Architecture & Source Code Workspace**
  - VS Code workspace inspection showing package hierarchy: `src/osdagbridge/core/` (structural analysis & plot generation), `src/osdagbridge/desktop/ui/` (docks, dialogs, CAD widgets), and `tests/` automated test suite.
- **0:22 – 0:30 (240 frames): Live Application Window Launch**
  - OsdagBridge main window initialized with 25.0 m span plate girder bridge, displaying synchronized Basic Inputs dock, 2D Cross-Section canvas, and Plan View canvas.

### 2. Problem Statement & Screening Objectives (0:30 – 1:00 | 900 Frames)
- **0:30 – 0:45 (450 frames): Real-World Engineering Motivation**
  - Discussing challenges in bridge engineering workflows: static CAD drawings causing manual input re-entry errors, risks of corrupted input dictionaries upon dialog cancellation, and limitation of legacy post-processors visualizing only longitudinal girders.
- **0:45 – 1:00 (450 frames): Three Core Screening Objectives**
  - **Task I:** Interactive 2D CAD Parameter Editing with bi-directional synchronization and derived parameter locking.
  - **Task II:** Additional Inputs Validation (strict custom parameter checks) and state management (unsaved modification warnings).
  - **Task III:** Transverse Member Result Plotting (End Diaphragms and Cross Bracings SFD, BMD, and deflections).

### 3. Program Running & Task I: Interactive 2D CAD Parameter Editing (1:00 – 1:55 | 1650 Frames)
- **1:00 – 1:12 (360 frames): Canvas Inspection & Hit-Testing**
  - Detailed inspection of the 2D CAD Cross-Section canvas (7.50 m Carriageway Width, 4 Girders @ 2.10 m spacing, 1.05 m Overhang).
- **1:12 – 1:26 (420 frames): Carriageway Width In-Place Editing (7.50 m → 8.00 m)**
  - Cursor glides to the Carriageway Width dimension label and double-clicks.
  - In-place `QLineEdit` overlay spawns directly over the dimension text.
  - Value edited to `8.00` and committed via [Enter].
  - Canvas redraws with wider deck; Basic Inputs dock synchronously updates to 8.00 m.
- **1:26 – 1:40 (420 frames): Girder Spacing In-Place Editing & Symmetrical Overhang Recalculation**
  - Cursor moves to Girder Spacing label ("2.10 m") and double-clicks.
  - Value edited to `2.20`.
  - Cursor clicks outside on canvas background (defocus commit).
  - Deck geometry updates; Overhang is automatically recomputed symmetrically to 1.15 m; Basic Inputs dock updates.
- **1:40 – 1:55 (450 frames): Locked Derived Dimension Enforcement**
  - Cursor double-clicks on Overhang (1.15 m), Overall Width (8.90 m), and Bracing Spacing (3.00 m).
  - System rejects edit attempts and displays locked HUD badge: *"Derived parameter is read-only to preserve geometric consistency."*

### 4. Task II: Additional Inputs Validation & State Management (1:55 – 2:25 | 900 Frames)
- **1:55 – 2:05 (300 frames): Opening Additional Inputs Dialog**
  - Cursor clicks "Additional Inputs" on toolbar; modal dialog opens smoothly.
- **2:05 – 2:15 (300 frames): Empty Custom Parameter Validation**
  - Crash Barrier Type set to "Custom"; Crash Barrier Load cleared to empty (`""`).
  - Cursor clicks "Save".
  - Authentic Critical Error dialog appears: *"Error: The custom value for 'Crash Barrier Load' cannot be empty."*
  - Cursor clicks OK; dialog remains open without saving corrupted data.
- **2:15 – 2:25 (300 frames): Unsaved Changes State Tracking & Safe Cancellation**
  - Valid load `7.56` entered; Wearing Course modified (`is_modified = True`).
  - Cursor clicks close button ('X').
  - Authentic Warning dialog appears: *"You have unsaved changes. Closing this window will discard them. Do you want to proceed?"* with `[Discard]` and `[Cancel]`.
  - Cursor hovers over `[Cancel]` (keeps edits), then clicks `[Discard]`, safely closing dialog and reverting uncommitted changes.

### 5. Task III: Transverse Member Result Plotting (2:25 – 3:15 | 1500 Frames)
- **2:25 – 2:35 (300 frames): Finite Element Analysis Execution**
  - Cursor clicks "Run Analysis". OpenSeesPy & OspGrillage grillage model constructed and solved across all IRC load combinations.
- **2:35 – 2:48 (390 frames): Output Dock Transverse Member Selection**
  - In Output Dock, Member Type dropdown switched to "End Diaphragms". Member dropdown dynamically populates with "End Diaphragm 1 (Start)" and "End Diaphragm 2 (End)".
- **2:48 – 3:00 (360 frames): End Diaphragm Shear Force ($V_y$) Diagram**
  - Shear Force $V_y$ radio button selected.
  - Matplotlib canvas renders transverse shear force with girder markers (G1..Gn), zero baseline, peak annotations, and semi-transparent `SummaryOverlay` HUD table.
- **3:00 – 3:08 (240 frames): Cross Bracing Vertical Deflection ($D_y$) Diagram**
  - Member Type switched to "Cross Bracings" → "Cross Bracing 1".
  - Vertical Deflection $D_y$ selected. Deflection curve across transverse span rendered with millimeter units and HUD metrics.
- **3:08 – 3:15 (210 frames): Regression Verification — 3D Isometric View**
  - Member Type switched back to "Longitudinal Members" → "Girder 1".
  - 3D Isometric View renders seamlessly with NavCube orientation gizmo active, verifying zero regressions across existing features.

### 6. Automated Testing Verification & Conclusion (3:15 – 3:45 | 900 Frames)
- **3:15 – 3:27 (360 frames): Pytest Automated Verification (27/27 Passed)**
  - Terminal view showing `python -m pytest -q` execution:
    - `test_cad_interactive_edit.py`: 12 tests passed
    - `test_additional_inputs_validation.py`: 4 tests passed
    - `test_transverse_plotting.py`: 11 tests passed
    - Total: `27 passed, 37 warnings in 42.54s [100%]`
- **3:27 – 3:36 (270 frames): Engineering Documentation & Technical Deliverables**
  - Showcase `FOSSEE_OsdagBridge_Technical_Report.pdf` (12-page comprehensive report) and `documentation/testing_report.md`.
- **3:36 – 3:45 (270 frames): Concluding Slide & Submission Information**
  - Summary of achievements, repository link (`https://github.com/Nidhikhare12/OsdagBridge`), working branch (`feature/osdagbridge-enhancements`), and acknowledgments.
