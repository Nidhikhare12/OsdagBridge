# Additional Input Test Specifications

## 1. Overview & Objectives

The "Additional Inputs" dialog in OsdagBridge allows the user to configure granular geometric details, component dimensions (crash barriers, footpaths, railings), design limits, and environmental loading parameters (IRC:6 live load configurations, wind, seismic, thermal).

This suite tests:
1. Field validation in `AdditionalInputs` dialog (`osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs`).
2. Interaction between modal parameters (Auto vs. Custom modes for barriers, footpaths, camber).
3. Live load combination generation and partial safety factor assignments.
4. Prevention of empty or whitespace inputs when toggled to "Custom" mode.

---

## 2. Test Cases Specification

### Test Case: TC_AI_001 – Girder Spacing and Count Coherence
- **Test ID**: `TC_AI_001`
- **Test Objective**: Verify that girder spacing ($S_g$) multiplied by $(N_g - 1)$ plus overhangs matches total deck width.
- **Preconditions**: Additional Inputs dialog open.
- **Input Parameters**:
  ```python
  {
      "geometry.carriageway_width": 7.5,
      "superstructure.no_of_girders": 4,
      "superstructure.girder_spacing": 2.5,
      "superstructure.deck_overhang": 1.25
  }
  ```
- **Expected Result**:
  1. Total bridge width $W_{tot} = (4 - 1) \times 2.5 + 2 \times 1.25 = 10.0\text{ m}$.
  2. With $7.5\text{ m}$ carriageway and two crash barriers ($0.5\text{ m}$ each) and footpath ($1.5\text{ m}$), transverse dimensions balance without geometric clash.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_AI_001`
- **Remarks**: Transverse dimensional consistency check.

---

### Test Case: TC_AI_002 – Empty Custom Input Rejection in Dialog
- **Test ID**: `TC_AI_002`
- **Test Objective**: Verify that selecting "Custom" mode for Footpath Pressure or Wind Gust Factor but leaving the value field blank displays an error and prevents saving.
- **Preconditions**: Additional Inputs dialog open.
- **Input Parameters**:
  ```python
  {
      "load.live_load.footpath_pressure_mode": "Custom",
      "load.live_load.footpath_pressure_value": ""  # Empty string
  }
  ```
- **Expected Result**:
  1. `validate_custom_inputs()` catches empty string.
  2. `CustomMessageBox` displays: `"Footpath Pressure cannot be empty."`.
  3. Dialog does not close; changes are not committed to `working_input_dict`.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_AI_002`
- **Remarks**: UI input validation guarding against empty strings.

---

### Test Case: TC_AI_003 – Whitespace Input Rejection
- **Test ID**: `TC_AI_003`
- **Test Objective**: Verify that entering whitespace-only strings (e.g., `"   "`) in custom value fields fails validation.
- **Preconditions**: Same as TC_AI_002.
- **Input Parameters**:
  ```python
  {
      "load.wind.gust_factor_mode": "Custom",
      "load.wind.gust_factor_value": "   "
  }
  ```
- **Expected Result**:
  1. `validate_custom_inputs()` strips whitespace and detects zero length.
  2. Dialog prompts: `"Gust Factor cannot be empty."`.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_AI_003`
- **Remarks**: Sanitization of string inputs.

---

### Test Case: TC_AI_004 – IRC:6 Live Load Vehicle Configuration Selection
- **Test ID**: `TC_AI_004`
- **Test Objective**: Verify that selecting Class 70R Wheeled + Class A vehicle combinations generates appropriate load cases in the grillage solver.
- **Preconditions**: Plate Girder module open; Live Load tab selected.
- **Input Parameters**:
  ```python
  {
      "load.live_load.vehicles": ["Class 70R Wheeled", "Class A"],
      "load.live_load.eccentricity": 0.3
  }
  ```
- **Expected Result**:
  1. Moving load generator creates grillage load cases for each vehicle.
  2. Congestion factors and multi-lane reduction factors are applied per IRC:6 Clause 204.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_AI_004`
- **Remarks**: Live load engine generation check.

---

### Test Case: TC_AI_005 – Partial Safety Factors Customization
- **Test ID**: `TC_AI_005`
- **Test Objective**: Verify that custom partial safety factors ($\gamma_{m0}, \gamma_{m1}, \gamma_v$) propagate to code checks.
- **Preconditions**: Design Options tab active in Additional Inputs.
- **Input Parameters**:
  ```python
  {
      "design.gamma_m0": 1.15,  # Non-standard test factor (standard 1.10)
      "design.gamma_m1": 1.30,
      "design.gamma_v": 1.35
  }
  ```
- **Expected Result**:
  1. Plate girder bending capacity check calculates $M_{dr} = f_y Z / 1.15$.
  2. Output report reflects modified factor.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_AI_005`
- **Remarks**: Limit state factor verification.
