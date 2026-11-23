# FOSSEE IIT Bombay Winter Internship 2026 Screening Task Submission
## Project: OsdagBridge UI, 2D CAD, and Plotting Enhancements

**Candidate / Engineer:** Senior Python Developer, PySide6 Desktop Application Engineer, and Open-Source Contributor  
**Target Repository (Origin):** [https://github.com/Pranshu10khtk/OsdagBridge](https://github.com/Pranshu10khtk/OsdagBridge)  
**Feature Branch:** `feature/osdagbridge-enhancements`  
**Upstream Repository (Preserved Unmodified):** [https://github.com/Nidhikhare12/OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge)  
**Report Document:** `FOSSEE_OsdagBridge_Technical_Report.pdf` (enclosed in this submission directory)

---

## 1. Executive Summary

This submission provides the complete, robust, and verified implementation of all three screening subtasks for the **OsdagBridge** short-span steel plate girder bridge application:

1. **Task I — Interactive 2D CAD Parameter Editing**:
   - Implemented in-place double-click parameter editing inside the 2D CAD canvas (`CadCrossSectionView` and `CadTopView`).
   - Supports 4 editable parameters: *Carriageway Width*, *Girder Spacing*, *Deck Thickness*, and *Span Length*.
   - Strictly enforces read-only status on 3 locked derived parameters: *Overhang*, *Overall Bridge Width*, and *Bracing Spacing*.
   - In-place overlay `QLineEdit` with `Enter` and click-outside commit handlers, `Escape` cancellation, and full validation via `BridgeInputValidator`.
   - Bidirectional synchronization with the basic inputs dock and automatic CAD canvas redraw.

2. **Task II — Additional Inputs Validation and State Management**:
   - Added dirty-state tracking (`self.is_modified = False`) tracking modifications across all active tabs in `AdditionalInputsDialog`.
   - Safe handling for programmatic updates (`self._loading_state = True`) to prevent false dirty markings during initialization.
   - Pre-save validation for Custom parameter fields using canonical keys from `osdagbridge/core/utils/common.py` (`KEY_ADD_...`).
   - Rejects empty or whitespace-only custom inputs with exact error dialog:
     `Error: The custom value for '[Parameter Name]' cannot be empty.`
   - Intercepts `closeEvent` when unsaved changes exist to display confirmation dialog with **Discard Changes** and **Cancel** choices.

3. **Task III — Transverse Member Result Plotting**:
   - Extended Matplotlib post-analysis visualization to complete 2D engineering response plots for transverse structural members.
   - Added Member Type combobox in Output Dock (`Longitudinal Members`, `End Diaphragms`, `Cross Bracings`).
   - Intelligently groups OspGrillage transverse elements into continuous lines across the deck width ($x=0$ End Diaphragm 1, $x=L$ End Diaphragm 2, and intermediate Cross Bracings).
   - Supports all 9 structural response components:
     - Forces: $F_x$ (Axial), $V_y$ (Major Shear), $V_z$ (Minor Shear) in $\text{kN}$
     - Moments: $T_x$ (Torsion), $M_y$ (Minor Bending), $M_z$ (Major Bending) in $\text{kNm}$
     - Displacements: $D_x$ (Longitudinal), $D_y$ (Vertical Deflection), $D_z$ (Transverse) in $\text{mm}$
   - Features girder crossing indicator lines ($G_1, G_2, \dots, G_n$), zero reference baseline, global Max/Min callout annotations, and interactive `SummaryOverlay` HUD table.
   - Retains 3D isometric visualization, camera controls, and NavCube synchronization for longitudinal girder plots with zero regressions.

---

## 2. Repository Git Commits

All changes are committed onto branch `feature/osdagbridge-enhancements` and pushed to `origin`:

| Commit Hash | Type | Subject |
|---|---|---|
| `8bfbe66` | feat(cad) | implement interactive 2D CAD parameter editing (Task I) |
| `7b93768` | feat(ui) | implement additional inputs validation and state management (Task II) |
| `453ca0a` | feat(plotting) | implement transverse member result plotting (Task III) |
| `364a1ee` | test | add comprehensive automated test suite for Tasks I, II, and III |
| `2628227` | docs | document Tasks I, II, and III enhancements and testing in README |

Patch files are provided under `patches/`:
- `0001-feat-cad-implement-interactive-2D-CAD-parameter-edit.patch`
- `0002-feat-ui-implement-additional-inputs-validation-and-s.patch`
- `0003-feat-plotting-implement-transverse-member-result-plo.patch`
- `0004-test-add-comprehensive-automated-test-suite-for-Task.patch`
- `0005-docs-document-Tasks-I-II-and-III-enhancements-and-te.patch`

---

## 3. Automated Test Suite & Verification Results

A suite of 22 automated tests was executed under `tests/` using `pytest` and `pytest-qt` within the `osdagbridge-env` environment:

```bash
pytest tests/test_cad_interactive_edit.py tests/test_additional_inputs_validation.py tests/test_transverse_plotting.py -v
```

### Verification Matrix (22/22 Passed, 100% Pass Rate)

| Module | Test Case | Scope & Verification | Status |
|---|---|---|:---:|
| **Task I: 2D CAD** | `test_cross_section_label_registration` | Verifies labels are registered with correct parameter keys | **PASSED** |
| | `test_top_view_label_registration` | Verifies top view dimensions (Bracing Spacing, Span Length) | **PASSED** |
| | `test_locked_parameters_remain_readonly` | Ensures Overhang, Overall Width, Bracing Spacing ignore edits | **PASSED** |
| | `test_editable_parameter_enter_commit` | Verifies Enter key commits value and updates input dict | **PASSED** |
| | `test_editable_parameter_click_outside_commit` | Verifies click-outside eventFilter commits value | **PASSED** |
| | `test_invalid_input_validation` | Confirms non-numeric, zero, and negative inputs are rejected | **PASSED** |
| | `test_span_length_editing_in_top_view` | Verifies Span Length editing in Top View triggers redraw | **PASSED** |
| | `test_dual_view_relay_signals` | Verifies `BridgeDualCADWidget` forwards signals to page | **PASSED** |
| **Task II: Validation** | `test_initial_state_is_not_modified` | Verifies dialog starts with `is_modified == False` | **PASSED** |
| | `test_user_input_marks_modified` | Verifies line edit / combo change sets `is_modified = True` | **PASSED** |
| | `test_custom_validation_empty_fails` | Verifies empty Custom field blocks save with required error | **PASSED** |
| | `test_custom_validation_whitespace_fails`| Verifies whitespace Custom field blocks save with error | **PASSED** |
| | `test_custom_validation_valid_succeeds` | Verifies valid Custom field saves and resets `is_modified` | **PASSED** |
| | `test_close_event_unmodified_closes` | Verifies unmodified dialog closes without confirmation prompt | **PASSED** |
| | `test_close_event_modified_cancel_keeps_open` | Verifies Cancel choice keeps dialog open to resume editing | **PASSED** |
| | `test_close_event_modified_discard_reverts` | Verifies Discard choice reverts working dict to saved state | **PASSED** |
| **Task III: Plotting** | `test_transverse_lines_identification` | Verifies extraction and sorting of End Diaphragm & Bracing lines | **PASSED** |
| | `test_end_diaphragm_all_components` | Tests End Diaphragm plotting across all 9 components | **PASSED** |
| | `test_cross_bracing_all_components` | Tests Cross Bracing plotting across all 9 components and 'All' | **PASSED** |
| | `test_output_dock_member_type_dropdown`| Verifies Member Type dropdown dynamic filtering of members | **PASSED** |
| | `test_plot_widget_transverse_plot_rendering`| Verifies 2D canvas rendering and NavCube hiding | **PASSED** |
| | `test_longitudinal_plots_regression_free`| Verifies 3D longitudinal plots continue rendering without regressions | **PASSED** |

---

## 4. How to Run the Application & Tests

### Activating the Conda Environment
```bash
conda activate osdagbridge-env
```

### Running the Test Suite
```bash
# Run all 22 enhancement tests:
pytest tests/test_cad_interactive_edit.py tests/test_additional_inputs_validation.py tests/test_transverse_plotting.py -v
```

### Launching the Desktop Application
```bash
python -m osdagbridge.desktop
```

---

## 5. Submission Artifacts Checklist

- [x] Full source code changes committed to `feature/osdagbridge-enhancements`
- [x] Changes pushed to origin `https://github.com/Pranshu10khtk/OsdagBridge.git`
- [x] Standard git patch files (`patches/*.patch`) generated
- [x] 22 automated tests located under `tests/`
- [x] `README.md` updated with comprehensive enhancement documentation
- [x] `FOSSEE_OsdagBridge_Technical_Report.pdf` generated and included
- [x] Final submission ZIP archive generated
