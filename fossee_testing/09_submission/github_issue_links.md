# GitHub Issue Links & Defect Tracking Register

This document tracks all software issues identified in OsdagBridge during testing that are submitted to the upstream GitHub issue tracker.

- **Target Upstream Repository**: [Nidhikhare12/OsdagBridge Issues](https://github.com/Nidhikhare12/OsdagBridge/issues)
- **Candidate Fork Issues Tracker**: [Pranshu10khtk/OsdagBridge Issues](https://github.com/Pranshu10khtk/OsdagBridge/issues)

---

## Issue Tracking Register

| Issue ID | Corresponding Bug ID | Issue Title | Target Module | Severity | Date Submitted | Upstream GitHub Issue URL | Status |
| :---: | :---: | :--- | :--- | :---: | :---: | :--- | :---: |
| ISSUE-01 | BUG_OB_001 | [Designer] Missing shear modulus Gs fallback causes ValueError for database steel grades | `core/bridge_types/plate_girder/designer.py` | Critical | 2026-11-22 | https://github.com/Nidhikhare12/OsdagBridge/issues/1 | Verified & Patch Proposed |
| ISSUE-02 | BUG_OB_002 | [Designer] Concrete deck properties fck/fctm/Ecm resolution failure for standard concrete grades | `core/bridge_types/plate_girder/designer.py` | Critical | 2026-11-22 | https://github.com/Nidhikhare12/OsdagBridge/issues/2 | Verified & Patch Proposed |

---

## Issue 1 Description & Context
- **Title**: `[Designer] Missing shear modulus Gs fallback causes ValueError for standard database steel grades`
- **Component**: `BridgeConfig.from_plate_girder_bridge` in `src/osdagbridge/core/bridge_types/plate_girder/designer.py`
- **Traceback**:
  ```text
  ValueError: Gs (shear modulus) is not set for grade 'E 350A'. Populate it in the material database before running the design check.
  ```
- **Root Cause**: The SQLite database `Intg_osdag.sqlite` does not define `Gs` in `Steel_Grade_Properties`. `designer.py` required `input_dict[KEY_MATERIAL_GIRDER_G]` without computing $G_s = E_s / [2(1 + \nu)]$.
- **Fix & Regression Test**: Patched in `designer.py` lines 311–320; regression verified in `tests/unit/test_designer.py::test_shear_modulus_fallback_regression`.

---

## Issue 2 Description & Context
- **Title**: `[Designer] Concrete deck properties fck/fctm/Ecm resolution failure for standard concrete grades`
- **Component**: `BridgeConfig.from_plate_girder_bridge` in `src/osdagbridge/core/bridge_types/plate_girder/designer.py`
- **Traceback**:
  ```text
  ValueError: 'material.deck.fck' is required but was not found in 'input_dict'.
  ```
- **Root Cause**: Selecting standard concrete grades (e.g. M35) populates `KEY_DECK_CONCRETE_GRADE_BASIC` in `input_dict`. `BridgeConfig` directly demanded sub-keys `material.deck.fck`, `material.deck.fctm`, `material.deck.ecm` rather than retrieving them from `bridge.material_props.concrete_prop`.
- **Fix & Regression Test**: Patched in `designer.py` lines 344–360; regression verified in `tests/unit/test_designer.py::test_standard_concrete_properties_resolution_regression`.
