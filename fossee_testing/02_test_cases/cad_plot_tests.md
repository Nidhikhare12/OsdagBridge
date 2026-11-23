# CAD & Plot Verification Test Specifications

## 1. Overview & Objectives

OsdagBridge integrates two visual feedback systems:
1. **3D CAD Viewport (`CAD3DWindow`)**: Built using OpenCASCADE technology (`pythonocc-core` and Qt `QGLWidget` / `QOpenGLWidget`), rendering 3D structural members including longitudinal girders, intermediate and end cross frames, shear connector studs, stiffeners, and concrete deck slab.
2. **2D Structural Response Plots (`MplPlotWidget`)**: Built using Matplotlib within a PySide6 dock widget, displaying internal force envelopes (BMD, SFD) and deflection profiles across multiple longitudinal girders and IRC:6 load combinations.

This test suite verifies:
1. Geometric fidelity of the 3D model relative to input parameters.
2. Responsiveness and stability of the 3D viewport (rotation, panning, zooming).
3. Accuracy, scaling, axis labeling, and load combination switching in 2D response graphs.

---

## 2. Test Cases Specification

### Test Case: TC_CP_001 – 3D CAD Geometry Generation for Right Bridge
- **Test ID**: `TC_CP_001`
- **Test Objective**: Verify that a 3D solid model is generated with the exact number of girders, correct span length, and deck width for a right bridge (skew = $0^\circ$).
- **Preconditions**: Design solve completed for Span = $30.0\text{ m}$, 4 girders, Skew = $0.0^\circ$.
- **Execution Steps**:
  1. Navigate to 3D CAD tab.
  2. Inspect generated model in OpenCASCADE viewport.
  3. Check girder count (4 parallel I-beams), intermediate cross bracings, and deck slab.
- **Expected Result**:
  1. 3D solid renders without OpenGL shader errors or pythonocc exceptions.
  2. All 4 girders span $30.0\text{ m}$ longitudinally along the X-axis.
  3. Girder spacing matches input $S_g$.
  4. Viewport supports smooth rotation, panning, and zooming without UI latency.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CP_001`, `SCREENSHOT_CP_001`
- **Remarks**: Baseline 3D CAD rendering test.

---

### Test Case: TC_CP_002 – 3D CAD Geometry with Non-Zero Skew Angle
- **Test ID**: `TC_CP_002`
- **Test Objective**: Verify that the 3D model correctly handles skew geometry ($+30.0^\circ$), skewing bearing lines and diaphragms accordingly.
- **Preconditions**: Design solve completed for Span = $25.0\text{ m}$, Skew = $30.0^\circ$.
- **Execution Steps**:
  1. Switch to 3D CAD tab.
  2. Inspect end supports and diaphragm alignments.
- **Expected Result**:
  1. Girder ends and abutment bearing lines align with $30^\circ$ skew angle.
  2. End diaphragms are placed along the skew orientation.
  3. Deck slab boundary matches skew geometry without topological self-intersections.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CP_002`, `SCREENSHOT_CP_002`
- **Remarks**: Geometric skew transformation test in OpenCASCADE.

---

### Test Case: TC_CP_003 – 2D Envelope Plot Generation & Load Combination Switch
- **Test ID**: `TC_CP_003`
- **Test Objective**: Verify that Matplotlib response plots (BMD, SFD, Deflection) render correctly and update dynamically when the user selects different load combinations from the combobox.
- **Preconditions**: Analysis solved; Output Dock open.
- **Execution Steps**:
  1. Open 2D Plot dock.
  2. Observe default plot (e.g., Ultimate Limit State Bending Moment envelope).
  3. Switch combobox `analysis.load_combination` to:
     - Dead Load (DL)
     - Live Load Class 70R
     - 1.35 DL + 1.5 LL (ULS Combination)
  4. Verify graph refresh for each selection.
- **Expected Result**:
  1. Plot curves update immediately upon combobox change.
  2. Axes display appropriate titles, engineering units ($\text{kN}\cdot\text{m}$, $\text{kN}$, $\text{mm}$), and legends for each girder.
  3. Peak bending moment occurs near mid-span ($x \approx L/2$); peak shear occurs at supports ($x = 0, x = L$).
  4. No figure redraw exceptions or GUI thread locking.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CP_003`, `SCREENSHOT_CP_003`
- **Remarks**: Structural response visualization check.
