# Custom Material Test Specifications

## 1. Overview & Objectives

In bridge engineering, projects frequently employ specialized high-performance structural steel grades (e.g., weathering steel, micro-alloyed steel) or non-standard concrete mixes. OsdagBridge provides "Custom" material property inputs alongside standard presets (E250, E350, E410, E450 steel; M30–M60 concrete).

This test suite rigorously checks:
1. Per-field boundary validation for user-defined steel and concrete properties.
2. Data persistence across UI docks and internal dictionaries.
3. Accurate propagation of custom parameters into modular ratios, cross-section inertias, and capacity code checks.
4. Complete independence of material assignments between distinct structural members (Girder vs. Cross Bracing vs. End Diaphragm vs. Deck).

---

## 2. Applicable Keys & Validation Limits

From `osdagbridge.core.bridge_types.plate_girder.validator`:

| Parameter | Dictionary Key | Permissible Range | Unit |
| :--- | :--- | :---: | :---: |
| Steel Weight Density ($\rho$) | `material.girder.density` | $50.0 - 120.0$ | $\text{kN/m}^3$ |
| Steel Yield Strength ($f_y$) | `material.girder.fy` | $100.0 - 1200.0$ | $\text{MPa}$ |
| Steel Ultimate Strength ($f_u$)| `material.girder.fu` | $100.0 - 1500.0$ | $\text{MPa}$ |
| Modulus of Elasticity ($E$) | `material.girder.e` | $100.0 - 300.0$ | $\text{GPa}$ |
| Modulus of Rigidity ($G$) | `material.girder.g` | $30.0 - 120.0$ | $\text{GPa}$ |
| Poisson's Ratio ($\nu$) | `material.girder.poisson`| $0.1 - 0.4$ | — |
| Thermal Coefficient ($\alpha$) | `material.girder.thermal`| $5.0 \times 10^{-6} - 25.0 \times 10^{-6}$ | $/\text{^\circ C}$ |
| Concrete Strength ($f_{ck}$) | `material.deck.fck` | $20.0 - 100.0$ | $\text{MPa}$ |
| Concrete Modulus ($E_{cm}$) | `material.deck.ecm` | $10.0 - 60.0$ | $\text{GPa}$ |

---

## 3. Test Cases Specification

### Test Case: TC_CM_001 – Standard Custom Steel Property Assignment
- **Test ID**: `TC_CM_001`
- **Test Objective**: Verify that valid user-defined steel properties for the main plate girder are stored and applied in calculations without default reversion.
- **Preconditions**: OsdagBridge open; Main Girder material set to `"Custom"`.
- **Input Parameters**:
  ```python
  {
      "material.girder": "Custom",
      "material.girder.fy": 345.0,       # Custom ASTM A572 Grade 50 equivalent
      "material.girder.fu": 450.0,
      "material.girder.e": 200.0,
      "material.girder.g": 76.9,
      "material.girder.poisson": 0.30,
      "material.girder.density": 78.5,
      "material.girder.thermal": 1.2e-5
  }
  ```
- **Expected Result**:
  1. All inputs pass validation without warnings.
  2. `win.input_dict` contains exact custom float values.
  3. Design checks in `output_dict` use $f_y = 345\text{ MPa}$ to compute moment capacity $M_{dr} = f_y \cdot Z_{eff} / \gamma_{m0}$.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_001`
- **Remarks**: Fundamental custom steel propagation test.

---

### Test Case: TC_CM_002 – Lower Bound Permissible Yield Strength
- **Test ID**: `TC_CM_002`
- **Test Objective**: Verify that the minimum allowable steel yield strength ($f_y = 100\text{ MPa}$) is accepted.
- **Preconditions**: Same as TC_CM_001.
- **Input Parameters**:
  ```python
  {
      "material.girder.fy": 100.0
  }
  ```
- **Expected Result**:
  1. Accepted by `validate_material_inputs(KEY_MATERIAL_GIRDER_FY, inputs)`.
  2. No error prompt displayed.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_002`
- **Remarks**: Exact lower limit boundary test.

---

### Test Case: TC_CM_003 – Below Lower Bound Yield Strength Rejection
- **Test ID**: `TC_CM_003`
- **Test Objective**: Verify that an unphysically low steel yield strength ($f_y < 100\text{ MPa}$) is rejected.
- **Preconditions**: Same as TC_CM_001.
- **Input Parameters**:
  ```python
  {
      "material.girder.fy": 80.0
  }
  ```
- **Expected Result**:
  1. Rejected with message: `"Yield Strength, Fy must be between 100.0 and 1200.0 MPa."`.
  2. Corrected value `100.0` suggested.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_003`
- **Remarks**: Input protection against sub-structural material values.

---

### Test Case: TC_CM_004 – Elastic Modulus Range Validation
- **Test ID**: `TC_CM_004`
- **Test Objective**: Verify upper boundary validation for steel Modulus of Elasticity ($E \le 300\text{ GPa}$).
- **Preconditions**: Same as TC_CM_001.
- **Input Parameters**:
  ```python
  {
      "material.girder.e": 350.0  # Exceeds physical steel stiffness
  }
  ```
- **Expected Result**:
  1. Rejected with message: `"Modulus of Elasticity, E must be between 100.0 and 300.0 GPa."`.
  2. Clamped to $300.0\text{ GPa}$.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_004`
- **Remarks**: Physical stiffness bound check.

---

### Test Case: TC_CM_005 – Custom Deck Concrete Property Propagation
- **Test ID**: `TC_CM_005`
- **Test Objective**: Verify that custom concrete compressive strength ($f_{ck} = 45\text{ MPa}$) and modulus ($E_{cm} = 34.0\text{ GPa}$) correctly adjust modular ratio $m = E_s / E_c$.
- **Preconditions**: Deck material combobox set to `"Custom"`.
- **Input Parameters**:
  ```python
  {
      "material.deck": "Custom",
      "material.deck.fck": 45.0,
      "material.deck.fctm": 3.8,
      "material.deck.ecm": 34.0,
      "material.deck.density": 25.0,
      "material.deck.thermal": 1.0e-5
  }
  ```
- **Expected Result**:
  1. Modular ratio computed as $m = 200 / 34.0 \approx 5.88$.
  2. Transformed section properties in `output_dict` use $m = 5.88$ rather than default M35 ($m \approx 6.45$).
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_005`
- **Remarks**: Composite action calculation check.

---

### Test Case: TC_CM_006 – Structural Member Material Decoupling
- **Test ID**: `TC_CM_006`
- **Test Objective**: Verify that assigning custom properties to cross bracings does not overwrite girder or end diaphragm material assignments.
- **Preconditions**: Plate Girder module open; distinct materials assigned to each member.
- **Input Parameters**:
  ```python
  {
      "material.girder": "E350",
      "material.girder.fy": 350.0,
      "material.cross_bracing": "Custom",
      "material.cross_bracing.fy": 410.0,
      "material.end_diaphragm": "E250",
      "material.end_diaphragm.fy": 250.0
  }
  ```
- **Expected Result**:
  1. `input_dict` maintains independent values for each key.
  2. Member capacity checks for bracing use $410\text{ MPa}$, girder uses $350\text{ MPa}$, diaphragm uses $250\text{ MPa}$.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_CM_006`
- **Remarks**: Namespace isolation between structural components.
