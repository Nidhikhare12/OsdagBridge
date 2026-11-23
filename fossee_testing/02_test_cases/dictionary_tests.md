# Dictionary Verification Test Specifications

## 1. Overview & Objectives

In OsdagBridge, communication between the desktop GUI, core calculation modules, solvers, and reporting engines is mediated by centralized dictionaries:
- `input_dict`: Stores all geometric, material, design, and loading parameters.
- `working_input_dict`: Temp dictionary used within dialogs before committing.
- `output_dict`: Stores section dimensions, grillage nodal forces, design checks, and capacity ratios.

This test suite validates:
1. Adherence to canonical dot-notation keys defined in `osdagbridge.core.utils.common`.
2. Correct Python primitive data types (float, int, str, bool, list).
3. Preservation of all dictionary keys during `.osi` file save and reload cycles.
4. Graceful handling of missing or unknown keys.

---

## 2. Canonical Key Registry Reference

| Category | Primary Common Keys | Expected Type |
| :--- | :--- | :---: |
| **Geometry** | `geometry.span`, `geometry.carriageway_width`, `geometry.skew_angle` | `float` |
| **Switches** | `geometry.include_median`, `geometry.footpath`, `geometry.design_mode`| `str` |
| **Materials** | `material.girder`, `material.deck`, `material.cross_bracing` | `str` |
| **Steel Properties** | `material.girder.fy`, `material.girder.fu`, `material.girder.e`, `material.girder.density` | `float` |
| **Concrete Deck** | `material.deck.fck`, `material.deck.fctm`, `material.deck.ecm`, `material.deck.density` | `float` |
| **Superstructure**| `superstructure.no_of_girders`, `superstructure.girder_spacing`, `superstructure.deck_thickness` | `int` / `float` |
| **Outputs** | `design.moment_capacity`, `design.shear_capacity`, `analysis.max_bending_moment` | `float` |

---

## 3. Test Cases Specification

### Test Case: TC_DV_001 – Initial Input Dictionary Completeness
- **Test ID**: `TC_DV_001`
- **Test Objective**: Verify that when `CustomWindow` initializes for `PlateGirderBridge`, all essential keys exist in `win.input_dict` with default valid values.
- **Preconditions**: Plate Girder window instantiated.
- **Execution Steps**:
  1. Inspect `win.input_dict`.
  2. Check existence of `KEY_SPAN`, `KEY_CARRIAGEWAY_WIDTH`, `KEY_SKEW_ANGLE`, `KEY_GIRDER`, `KEY_DECK`.
  3. Verify data types are not `None`.
- **Expected Result**:
  1. All mandatory keys present.
  2. Values conform to expected defaults (e.g., span = $25.0$, width = $7.5$, skew = $0.0$).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_DV_001`
- **Remarks**: Initialization contract validation.

---

### Test Case: TC_DV_002 – Output Dictionary Population Post-Solve
- **Test ID**: `TC_DV_002`
- **Test Objective**: Verify that upon successful analysis and design execution, `win.output_dict` is comprehensively populated with valid numerical results.
- **Preconditions**: Standard 25m span design solve executed.
- **Execution Steps**:
  1. Trigger design solve.
  2. Assert `bool(win.output_dict)` is `True`.
  3. Check presence of analysis results (bending moments, shears) and section design checks.
- **Expected Result**:
  1. `output_dict` contains keys for governing design checks:
     - Bending capacity ($M_d$) and utilization ratio ($M_u / M_d \le 1.0$).
     - Shear capacity ($V_d$) and utilization ratio ($V_u / V_d \le 1.0$).
     - Mid-span deflection ($\delta_{max}$) and allowable limit ($L / 800$).
  2. Values are positive finite floating point numbers (no `NaN` or `inf`).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_DV_002`
- **Remarks**: Output contract verification.

---

### Test Case: TC_DV_003 – OSI Project File Serialization Roundtrip
- **Test ID**: `TC_DV_003`
- **Test Objective**: Verify that saving a project to a `.osi` file and reloading it reconstructs an identical `input_dict`.
- **Preconditions**: Plate Girder configured with custom parameters.
- **Execution Steps**:
  1. Configure inputs: Span = 28.5m, Skew = 15.0 deg, Custom steel $f_y = 380\text{ MPa}$.
  2. Save project as `test_roundtrip.osi`.
  3. Reset application or clear inputs.
  4. Load `test_roundtrip.osi`.
  5. Run `compare_dictionaries.py` on pre-save and post-load dictionaries.
- **Expected Result**:
  1. File saves cleanly in JSON/OSI format.
  2. Re-loaded dictionary matches pre-saved dictionary with 100% field parity.
  3. No type conversions (e.g., float turning into string).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_DV_003`
- **Remarks**: Persistence and serialization integrity.
