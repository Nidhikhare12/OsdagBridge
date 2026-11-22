# OsdagBridge: UI, 2D CAD and Plotting Enhancements

Branch: `osdagbridge-enhancements` (based on `upstream/dev` at `d74f56d`)

## 1. Overview

Three enhancements were implemented on the OsdagBridge desktop application:

| Task | Feature | Main files |
|---|---|---|
| I | Double-click editing of dimension labels on the 2D CAD | `desktop/ui/docks/cad_label_editing.py` (new), `cad_cross_section.py`, `cad_top_view.py`, `cad_dual_view.py`, `template_page.py` |
| II | Additional Inputs: empty-Custom validation on Save, unsaved-changes warning on close | `desktop/ui/dialogs/additional_input/custom_input_validation.py` (new), `additional_inputs.py`, `core/utils/common.py` |
| III | Result plots for transverse members (end diaphragms and intermediate cross bracings) | `core/bridge_types/plate_girder/results_data.py`, `plot_generator.py`, `desktop/ui/mpl_plot_widget.py`, `desktop/ui/docks/output_dock.py`, `core/utils/common.py` |

Every change reuses the existing validators, solvers, dialogs (`CustomMessageBox`) and central keys in `core/utils/common.py` instead of duplicating logic.

## 2. Task I: Interactive 2D CAD parameter editing

### Approach

Both CAD canvases (cross-section and top view) are drawn with `QPainter`, so there are no label widgets to attach events to. The solution records where each label is painted and hit-tests double-clicks against those regions.

1. **Tagging labels at paint time.** A mixin, `EditableCADLabelsMixin`, is added to `CrossSectionCADWidget` and `TopViewCADWidget`. Immediately before a dimension label is drawn, the drawing code calls `_tag_label('<cad_param>')`. The shared `draw_text_with_background()` method then records the painted background rectangle (mapped through the painter transform) as a hit region for that parameter. Regions are rebuilt on every paint, so they always match the current zoom and scroll position.
2. **Double-click handling.** `mouseDoubleClickEvent` finds the label under the cursor. Where labels overlap (for example Overhang and Girder Spacing when zoomed out), the label painted last, which is the one visible on top, wins. For an editable parameter, a temporary `QLineEdit` is placed exactly over the label, pre-filled with the current value and selected, with a `QDoubleValidator`. **Enter** or clicking outside applies the value, **Esc** cancels, and an unchanged value is ignored.
3. **Hover feedback.** Editable labels show a pointing-hand cursor and a "Double-click to edit" tooltip. Locked labels show a forbidden cursor and a "Derived value (read-only)" tooltip.
4. **Pushing the value to the input dictionaries.** The canvas emits `label_value_committed(param, text)`. `BridgeDualCADWidget` relays it as `cad_parameter_edited`, and `CustomWindow._on_cad_parameter_edited` in `template_page.py` applies it:
   - **Span length and carriageway width** (basic inputs): the value is written into the input-dock field and passed through `InputDock._on_field_edited`. This is the same path as typing in the field, so the existing range validation and error popup, the update to `input_dict`, the required-field re-solve (`solve_extend_basic_input_dict`) and the CAD redraw all apply.
   - **Girder spacing and deck thickness** (additional inputs): the Additional Inputs dialog object is loaded with the committed dictionary and its own `_on_field_edited` validator is run. For girder spacing, `update_girder_layout("spacing")` then re-solves overhang, number of girders and overall width, exactly as when editing in the dialog. The working dictionary is committed to `input_dict` the same way Save does, and both views are redrawn with `update_from_osdag_inputs`.
   - Edits are refused with a message while inputs are locked after a design run. Non-numeric or non-positive entries are rejected.

### Editable and locked parameters

| Label | CAD view | Behaviour |
|---|---|---|
| Carriageway Width | cross-section | editable (m) |
| Girder Spacing | cross-section and top view | editable (m) |
| Deck Thickness | cross-section | editable (mm) |
| Span Length | top view | editable (m) |
| Overhang, Overall Bridge Width, Bracing Spacing | both | locked: derived by the layout solver, double-click only shows the read-only tooltip |

Label editing is switched on only for the main-window CAD (`label_editing_enabled`). The CAD preview inside the Additional Inputs dialog stays read-only.

## 3. Task II: Additional Inputs validation and state management

### Pre-save validation of empty Custom fields

Instead of hard-coding parameter names, the list of Custom-capable fields is derived once from `ADDITIONAL_INPUTS_SCHEMA` (`build_custom_rules`). Every widget is then looked up by its schema id, which is the central `KEY_*` constant from `core/utils/common.py`. The schema contains three Custom patterns, and all of them are covered (21 fields in total):

| Pattern | Example | Rule |
|---|---|---|
| `TYPE_MODE_LINE` (mode combo + value box) | Wind Load > Gust Factor, Live Load > Footpath Pressure, Camber | mode = Custom → `<id>.value` must not be empty |
| `TYPE_ADAPTIVE` with a Custom text page | Girder Details > Total Depth, flange widths | design mode = Custom → the visible line edit must not be empty |
| `TYPE_COMBOBOX` with a Custom choice | Crash Barrier, Median, Railing, Wearing Course type | type = Custom → every text box in the same sub-tab that the dialog has enabled for entry must not be empty |

`_save_inputs` runs `find_empty_custom_fields` first. Fields on disabled tabs (for example Median when no median is included, or the disabled Custom Load tab), hidden fields and disabled fields are skipped. If anything is missing, Save stops, nothing is committed, and the standard error dialog (`CustomMessageBox`, Critical) lists every missing field in the required format, with the tab path so the user can find it:

> Error: The custom value for 'Typical Section Details > Crash Barrier > Width (m)' cannot be empty.

### Unsaved-changes warning

- `self.is_modified` is set by every user edit path (`_on_field_edited`, `_on_field_editing`, bounds and Custom selections, the Defaults button) and cleared on a successful Save.
- A `_track_changes` flag is off while the dialog fills itself programmatically (`set_input_dictionary`, `design_mode_trigger`, tab refreshes). It is switched on only after the dialog is shown, so opening the dialog never counts as a modification.
- `closeEvent` (title-bar close, Alt+F4) and `reject` (Esc key) both call `_confirm_discard()`. If there are unsaved changes, it shows the standard warning dialog with **Discard / Cancel** and the required message. Cancel keeps the dialog open. Discard closes it, and the next opening rebuilds the working copy from the committed dictionary, so the discarded edits are gone.

### New keys in `common.py`

`KEY_ADD_CUSTOM_OPTION`, `KEY_ADD_MSG_TITLE_ERROR`, `KEY_ADD_MSG_CUSTOM_EMPTY`, `KEY_ADD_MSG_TITLE_UNSAVED`, `KEY_ADD_MSG_UNSAVED_CHANGES`, `KEY_ADD_BTN_DISCARD` and `KEY_ADD_BTN_CANCEL`. These are only the strings that did not already exist. Field identities come from the existing keys.

## 4. Task III: Result plotting for transverse members

### Data extraction (`results_data.py`)

- `split_longitudinal_transverse(nodes, members)` is now the single function that separates element tags. An element is longitudinal when both end nodes share Y and Z, and transverse otherwise. Only the lateral coordinate is tested, so skewed (oblique) meshes are handled. The existing `_build_full_data` now uses it as well.
- `classify_transverse_lines(nodes, members, edge_dist)` keeps only transverse elements whose two nodes lie on main girders. Overhang pieces between an edge beam and the exterior girder are deck-slab cantilevers and are excluded, the same rule as `build_crossbracings` in post-processing. It then groups the elements into lines by connectivity and orders them along the span. The two support lines are the end diaphragms `ED1` and `ED2` (the `start_edge` / `end_edge` members). The intermediate lines are the cross bracings `CB1 … CBn` (the `transverse_slab` members). Elements are ordered from G1 towards Gn.
- `extract_transverse_member_results(ds, nodes, members, plot_key, edge_dist)` reads the selected load case:
  - **Forces** (Fx, Vy, Vz, Tx, My, Mz): ospgrillage returns element end forces in **global** axes. For a member running across the deck (global Z), the raw global "Mx" is actually its bending moment and "Vz" its axial force. The end-force vectors are therefore rotated into member axes (local x along the member, local y vertical, local z = x × y). This gives each label the same meaning as on the girder plots: Fx axial, Vy vertical shear, Vz horizontal shear, Tx torsion, My bending about the vertical axis, Mz bending in the vertical plane. Values are in kN / kNm. The sign convention matches the girder diagrams: start-end force at the first node, negated far-end force at the second.
  - **Displacements** (Dx, Dy, Dz): nodal and in global axes (mm), with the same vertical sign flip as the existing deflection plot.

### Plot and UI

- `plot_generator.build_figure_transverse()` draws a 3D diagram along every transverse line on top of the grillage. End diaphragms are drawn in a darker colour than the cross bracings. It includes max/min markers and values, the optional "all values" labels, element/node hover readout, line labels (ED1, CB1, …), supports, and a summary table (`{line: {max, min}}`). Because these diagrams lie in the vertical plane across the deck, the front elevation used for girders would show them edge-on, so they open in an isometric view. The camera is kept while switching between components of the same plot family.
- `FORCE_MAP` in `plot_generator.py` now comes from `results_data.FORCE_COMPONENT_MAP`, so there is one source of truth for components.
- The analysis **Member** dropdown lists `All, G1 … Gn, Transverse Members` (`VALUE_ANALYSIS_MEMBER_TRANSVERSE` in `common.py`). Choosing it routes all nine force/displacement buttons and every load case or combination to the transverse plot. The summary panel heading changes from "Girder" to "Member". Grillage view with this selection shows the whole mesh.

## 5. Verification

Everything was tested by running the real application in a virtual display (Xvfb) inside the project's conda environment (`osdagbridge-env` from `environment.yml`, including `osdag` / pythonocc) and driving the UI from scripts. Dialog boxes were captured to check the exact messages.

**Task I**: double-clicks with typed values on each label:

- Deck thickness 250 → 300 mm was committed. Girder spacing 2.10 → 2.40 m re-derived the overhang (1.05 → 0.60 m).
- Carriageway width 7.5 → 11 m and span 30 → 40 m were applied through the input dock, with the layout re-solved and both views redrawn. Girder spacing edited from the top view also worked.
- Esc cancelled without a change.
- Deck thickness 900 mm was corrected to 500 mm with the existing "must not exceed 500 mm" message. Span 500 m was corrected to 45 m with the existing range message. Letters cannot be typed (validator).
- Double-clicking Overhang, Overall Width or Bracing Spacing opened no editor.
- The Additional Inputs preview canvas was not editable.

**Task II**:

- Crash Barrier = Custom with an empty width blocked Save. The committed dictionary was unchanged and the error named the field.
- Adding an empty Custom gust factor produced both errors in one dialog. After filling both, Save succeeded and `is_modified` reset.
- After an edit, close → Cancel kept the dialog open and close → Discard closed it with the committed value unchanged.
- Reopening and closing without edits showed no prompt. Esc was guarded the same way.

**Task III**: a full design was run (span 30 m, carriageway 7.5 m, 4 girders, 1.05 m overhang):

- 225 elements were split into 120 longitudinal and 105 transverse, with no overlap and nothing missing. That gives 21 transverse lines (ED1, CB1–CB19, ED2) with 3 girder-to-girder elements each, and 42 overhang pieces excluded.
- The rotation was checked against the raw data: local Fx = global Vz, local Mz = −global Mx, local Vy = global Vy, local Tx = global Mz.
- Equilibrium: axial force and shear are constant along each element, and the moment change equals shear × length (maximum error 0.0002 kNm).
- Mid-span transverse deflection equals the girder deflection plot at the same nodes (−56.39 / −56.53 mm, Envelope ULS).
- All nine components were plotted for a basic load case and for Envelope ULS through the UI. Switching back to G2 and All still produced the girder plots.

## 6. Notes and limitations

- Editing span or carriageway width (on the CAD or in the input dock) marks a required field as changed. The app's existing `solve_extend_basic_input_dict` then re-solves the layout and restores Additional Inputs defaults such as deck thickness. This is the existing behaviour for required fields, and it was kept on purpose.
- When the cross-section is zoomed far out, the existing drawing code hides the deck-thickness dimension (deck thinner than 5 px). Zoom in to edit it.
- The intermediate transverse lines are the grillage's transverse grid members, which the app already treats as cross bracings in post-processing. Their number follows the analysis mesh, not the Bracing Spacing value shown on the CAD.
- The interpreter can crash at exit ("shared QObject was deleted directly") in headless runs. This happens on the unmodified `dev` branch too and is unrelated to these changes.

## 7. Commits

1. Additional Inputs: validate empty Custom fields on Save and warn on unsaved close
2. 2D CAD: double-click to edit carriageway width, girder spacing, deck thickness and span
3. Plots: add Transverse Members (end diaphragms + cross bracings) for all components
