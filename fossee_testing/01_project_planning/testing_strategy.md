# Testing Strategy: OsdagBridge Verification & Validation

## 1. Testing Objectives

The primary objective of the OsdagBridge testing campaign is to ensure structural engineering accuracy, numerical stability, interface integrity, and user workflow robustness for steel plate girder bridge design under Indian Standard codes.

Specifically, the testing strategy aims to:
1. **Verify Compliance with Design Standards**: Ensure strict adherence to IRC:5–2015, IRC:6–2017, IRC:22–2015, IRC:24–2010, and IS 800:2007.
2. **Validate Input Integrity**: Prevent application crashes, unhandled exceptions, and invalid design states caused by erroneous user inputs.
3. **Audit Custom Material Handling**: Ensure user-defined structural steel and concrete deck properties are propagated without data loss or corruption.
4. **Ensure Multi-Run State Isolation**: Guarantee that consecutive design executions in the same session produce deterministic results without state leakage.
5. **Verify Data Contract (Dictionaries)**: Validate input and output dictionary schemas, data types, and unit conversions.
6. **Confirm CAD and Plot Integrity**: Ensure 3D OpenCASCADE geometric representations and 2D Matplotlib response envelopes render accurately.
7. **Isolate and Diagnose Defects**: Provide actionable, code-level root cause analyses for all identified bugs.

---

## 2. Testing Methodology & Pyramid

The testing strategy follows a tiered approach combining automated and exploratory techniques:

```
           / \
          /   \     Exploratory & Usability (GUI, Workflow, Video)
         /-----\
        /  CAD  \   CAD & Plot Visual Verification (OpenCASCADE, Matplotlib)
       /---------\
      / Integration\ Integration & Multi-Run Testing (Consecutive solves, .osi I/O)
     /-------------\
    /   Validation   \ Input Boundary & Schema Validation (BridgeInputValidator, OSI)
   /-----------------\
  /     Unit Tests     \ Core Engineering & Calculation Checks (IRC formulas, section props)
 /---------------------\
```

---

## 3. Testing Pillars & Detailed Approaches

### 3.1 Functional Testing
- **Goal**: Verify that all core functional workflows (plate girder sizing, grillage analysis, design checks, load combination generation) perform as specified.
- **Approach**: Execute end-to-end bridge design workflows from GUI and CLI with standard spans (e.g., 20m, 25m, 30m, 35m).
- **Verification Criteria**: Design outputs, capacity ratios, and summary tables match theoretical expectations.

### 3.2 Input Boundary & Validation Testing
- **Goal**: Confirm that user inputs are validated against physical, codal, and software limits before analysis execution.
- **Approach**: Test Equivalence Partitioning (EP) and Boundary Value Analysis (BVA) on:
  - Span length ($12\text{ m} \le L \le 45\text{ m}$)
  - Carriageway width ($4.25\text{ m} \le W \le 24.0\text{ m}$)
  - Skew angles ($-60^\circ \le \theta \le 60^\circ$)
  - Girder spacings, flange thicknesses, web depths, and deck thickness.
  - Non-numeric inputs, negative values, null values, and excessive whitespace.
- **Verification Criteria**: UI flags invalid inputs gracefully via `CustomMessageBox` or inline validation without throwing unhandled exceptions.

### 3.3 Custom Material Testing
- **Goal**: Confirm that user-defined material properties correctly override default grades and propagate through all downstream calculation modules.
- **Approach**:
  - Define custom structural steel properties for Girder, Cross Bracing, and End Diaphragms ($f_y, f_u, E, G, \nu, \alpha, \rho$).
  - Define custom concrete deck properties ($f_{ck}, f_{ctm}, E_{cm}, \alpha_c, \rho_c$).
  - Inspect runtime `input_dict` to ensure user values are preserved and fed into `composite_section_properties()` and stress evaluation routines.
- **Verification Criteria**: Calculation outputs reflect custom moduli and yield strengths; defaults are not silently restored.

### 3.4 Multi-Run Testing (State Isolation & Memory Guard)
- **Goal**: Verify that running multiple consecutive designs within a single application session produces identical, independent results.
- **Approach**:
  - Run Test Sequence: Run 1 (Span 25m) $\rightarrow$ Run 2 (Span 35m) $\rightarrow$ Run 3 (Span 25m).
  - Verify that Run 3 yields identical results to Run 1.
  - Monitor memory consumption and object references to ensure OpenCASCADE AIS objects and solver instances are freed.
- **Verification Criteria**: No stale dictionary keys remain; output docks clear prior run values; zero memory leakage or GUI degradation across 3+ consecutive runs.

### 3.5 Dictionary Verification (Data Contracts)
- **Goal**: Verify that the internal data exchange mechanisms (`input_dict` and `output_dict`) conform to standard keys and data types.
- **Approach**:
  - Inspect keys defined in `osdagbridge.core.utils.common` (e.g., `geometry.span`, `geometry.carriageway_width`, `material.girder.fy`).
  - Compare dumped dictionaries before and after UI actions, file save/load (`.osi`), and analysis execution using `compare_dictionaries.py`.
- **Verification Criteria**: All keys exist with correct data types (float, int, str, bool); no key collisions or undefined keys appear.

### 3.6 CAD and Plot Verification
- **Goal**: Ensure 3D structural model rendering and 2D analysis envelope graphs are geometrically accurate and interactively responsive.
- **Approach**:
  - **CAD**: Verify 3D rendering of girders, stiffeners, cross bracings, shear studs, and deck slab. Test interactive rotation, zoom, pan, and part visibility toggles.
  - **Plots**: Verify Bending Moment Diagrams (BMD), Shear Force Diagrams (SFD), and Deflection profiles across individual load cases and combinations (IRC Class A, Class 70R, Special Vehicles).
- **Verification Criteria**: 3D model geometry matches input dimensions; plots update dynamically upon load case selection without canvas freezing.

### 3.7 Regression Testing
- **Goal**: Ensure that bug fixes and enhancements do not regress existing functionality.
- **Approach**: Execute automated pytest suites (`tests/test_additional_inputs_validation.py`, `tests/test_cad_interactive_edit.py`, `tests/test_transverse_plotting.py`) whenever changes are analyzed.

---

## 4. Test Environment & Prerequisites

- **Operating System**: Windows 10/11 64-bit
- **Python Runtime**: Python 3.10 / 3.11 / 3.12 within Conda / virtual environment
- **Key Dependencies**:
  - GUI: `PySide6`
  - 3D CAD: `pythonocc-core` (OpenCASCADE 7.x)
  - Plotting: `matplotlib`, `numpy`
  - Solvers: `openseespy`, `ospgrillage`
  - Quality Tools: `pytest`, `flake8`
  - Documentation: TeX Live / MiKTeX (`pdflatex`)

---

## 5. Pass/Fail & Severity Definitions

| Status | Definition |
| :--- | :--- |
| **Pass** | Actual result matches expected result within numerical tolerance ($\le 0.1\%$). |
| **Fail** | Actual result deviates from expected result, produces wrong calculations, or raises error. |
| **Blocked** | Test execution cannot proceed due to an upstream blocking bug or application crash. |

| Defect Severity | Criteria |
| :--- | :--- |
| **Critical** | Application crash, numerical error violating safety codes, silent data corruption. |
| **Major** | Feature failure (e.g., CAD fails to render, .osi fails to save), incorrect validation blocking valid input. |
| **Moderate** | UI glitch, missing unit label, non-blocking state persistence issue. |
| **Minor** | Cosmetic formatting, typographical error, minor logging inconsistency. |
