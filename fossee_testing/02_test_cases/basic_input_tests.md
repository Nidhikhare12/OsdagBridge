# Basic Input Test Specifications: Plate Girder Bridge

## 1. Overview & Objectives

This test suite evaluates the input validation, boundary constraints, and error handling mechanisms for basic geometric parameters within the OsdagBridge Plate Girder module. These checks verify strict compliance with **IRC:5–2015 Clause 104.3.1** (Carriageway Widths), **IRC:24–2010** (Steel Bridge Design & Skew Constraints), and internal software geometric limitations.

Validation logic under test:
- Class: `BridgeInputValidator` (`osdagbridge.core.bridge_types.plate_girder.validator`)
- Methods: `validate_basic_inputs(key, inputs)`

---

## 2. Test Cases Specification

### Test Case: TC_BI_001 – Minimum Permissible Span Boundary
- **Test ID**: `TC_BI_001`
- **Test Objective**: Verify that the minimum allowable span limit ($12.0\text{ m}$) is accepted and correctly sized without raising validation warnings.
- **Preconditions**: OsdagBridge GUI launched; Plate Girder Bridge module active; default materials loaded.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 12.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0,
      "geometry.include_median": "No",
      "geometry.footpath": "No",
      "geometry.design_mode": "Auto"
  }
  ```
- **Expected Result**:
  1. Input is accepted by validator (`validate_basic_inputs` returns `None`).
  2. Initial sizing calculates appropriate girder depth ($L/12$ to $L/15 \approx 0.8\text{ m} - 1.0\text{ m}$).
  3. No error dialog is displayed.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: Logs / Screenshot ID: `LOG_BI_001`
- **Remarks**: Baseline minimum span verification.

---

### Test Case: TC_BI_002 – Maximum Permissible Span Boundary
- **Test ID**: `TC_BI_002`
- **Test Objective**: Verify that the maximum supported span limit ($45.0\text{ m}$) is accepted and handled by grillage discretization.
- **Preconditions**: Same as TC_BI_001.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 45.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0,
      "geometry.include_median": "No"
  }
  ```
- **Expected Result**:
  1. Input is accepted; validator passes.
  2. Section sizing calculates girder depth within realistic structural bounds ($2.5\text{ m} - 3.2\text{ m}$).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_002`
- **Remarks**: Baseline maximum span verification.

---

### Test Case: TC_BI_003 – Span Below Lower Limit
- **Test ID**: `TC_BI_003`
- **Test Objective**: Verify that a span length below $12.0\text{ m}$ is rejected with an informative error message.
- **Preconditions**: Same as TC_BI_001.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 10.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0
  }
  ```
- **Expected Result**:
  1. Validator flags error: `"Span must be between 12.0 m and 45.0 m (software limitation)."`.
  2. Software suggests or auto-corrects to $12.0\text{ m}$.
  3. Analysis button remains disabled or warns the user before execution.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_003`
- **Remarks**: Boundary value analysis (lower violation).

---

### Test Case: TC_BI_004 – Span Exceeding Upper Limit
- **Test ID**: `TC_BI_004`
- **Test Objective**: Verify that a span length exceeding $45.0\text{ m}$ is rejected.
- **Preconditions**: Same as TC_BI_001.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 50.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0
  }
  ```
- **Expected Result**:
  1. Validator returns corrected value `45.0` with message `"Span must be between 12.0 m and 45.0 m (software limitation)."`.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_004`
- **Remarks**: Boundary value analysis (upper violation).

---

### Test Case: TC_BI_005 – Non-Numeric Span Input
- **Test ID**: `TC_BI_005`
- **Test Objective**: Verify robust handling of non-numeric or malformed string values in numeric input fields.
- **Preconditions**: Same as TC_BI_001.
- **Input Parameters**:
  ```python
  {
      "geometry.span": "twenty-five",
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0
  }
  ```
- **Expected Result**:
  1. Validator catches parsing exception via `_to_float()`.
  2. Returns message: `"Span must be a numeric value."`.
  3. UI does not crash or raise uncaught `ValueError`.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_005`
- **Remarks**: Type safety and exception handling.

---

### Test Case: TC_BI_006 – Minimum Carriageway Width for Two Lanes (IRC:5)
- **Test ID**: `TC_BI_006`
- **Test Objective**: Verify compliance with IRC:5 Clause 104.3.1 for two-lane two-way carriageway without median ($7.5\text{ m}$).
- **Preconditions**: `geometry.include_median` set to `"No"`.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 25.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 0.0,
      "geometry.include_median": "No"
  }
  ```
- **Expected Result**:
  1. Accepted as valid 2-lane bridge configuration.
  2. IRC 5 lane calculation logic resolves to 2 design traffic lanes.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_006`
- **Remarks**: Codal design standard validation.

---

### Test Case: TC_BI_007 – Sub-Minimum Carriageway Width Violation
- **Test ID**: `TC_BI_007`
- **Test Objective**: Verify rejection of carriageway width below minimum allowable single lane road ($< 4.25\text{ m}$).
- **Preconditions**: `geometry.include_median` set to `"No"`.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 25.0,
      "geometry.carriageway_width": 3.5,
      "geometry.skew_angle": 0.0
  }
  ```
- **Expected Result**:
  1. Rejected with message referencing IRC 5:2015 Clause 104.3.1 minimum width requirement.
  2. Suggests minimum width ($4.25\text{ m}$).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_007`
- **Remarks**: Boundary value analysis (codal minimum).

---

### Test Case: TC_BI_008 & TC_BI_009 – Skew Angle Limits ($\pm 60^\circ$)
- **Test ID**: `TC_BI_008` ($+60^\circ$) / `TC_BI_009` ($-60^\circ$)
- **Test Objective**: Verify that extreme skew angles within the permissible $\pm 60^\circ$ range are handled correctly in grillage geometry.
- **Preconditions**: Standard 25m span, 7.5m carriageway.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 25.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 60.0  # and -60.0 for TC_BI_009
  }
  ```
- **Expected Result**:
  1. Skew angle accepted without validator error.
  2. Grillage mesh generator applies skew coordinates and offset transverse members.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_008`, `LOG_BI_009`
- **Remarks**: Grillage geometry transformation check.

---

### Test Case: TC_BI_010 – Skew Angle Exceeding Permissible Limit
- **Test ID**: `TC_BI_010`
- **Test Objective**: Verify rejection of skew angle outside $[-60^\circ, +60^\circ]$.
- **Preconditions**: Same as TC_BI_001.
- **Input Parameters**:
  ```python
  {
      "geometry.span": 25.0,
      "geometry.carriageway_width": 7.5,
      "geometry.skew_angle": 75.0
  }
  ```
- **Expected Result**:
  1. Rejected with message: `"Skew angle must be between -60° and 60°."`.
  2. Clamped to $60.0^\circ$.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_BI_010`
- **Remarks**: IRC:24 skew angle limitation check.
