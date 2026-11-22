# OsdagBridge Report Technical Changes

## Overview
This document records all technical changes made to the OsdagBridge report generator during the dev cycle. Each step addresses specific bugs, style violations, or feature improvements.

---

## R1: Unit Tests (94 passed)
```
python -m pytest tests/unit -q → 94 passed in ~8s
```
All existing unit tests continue to pass. No test deletions or modifications required.

---

## R2: Footer Overlap (R2)
- **Change**: `styles.py` `PAGE["footskip"]` increased from `"30pt"` to `"40pt"`.
- **Rationale**: Increased footskip to push footer further down the page, reducing the likelihood of body text blocks overlapping the footer zone.
- **Script**: `tools/check_footer_overlap.py` written using PyMuPDF. Requires a generated PDF for verification.
- **Verification needed**: Generate a PDF via `Design → Generate Report`, then run:
  ```
  python tools/check_footer_overlap.py <path-to-pdf>
  ```
  Should report zero offending pages.

---

## R3: Braking Force Column (Table 3.3)
- **File**: `src/osdagbridge/core/reports/chap3.py`
- **Change**: Added fallback derivation of design lanes from carriageway width (`KEY_CARRIAGEWAY_WIDTH`) using `IRC6_2017.table_6()` when `KEY_WC_LD_LANE_TABLE_COUNT` is not available.
- **Before**: Braking force always "Not computed" when lane count key was missing.
- **After**: If lane count is explicitly provided, use it; otherwise derive from carriageway width per IRC 6 Cl. 204.1 (7.5 m → 2 lanes). Only shows "Not computed" if lanes truly cannot be derived.
- **Formula**: `cl_211_2_braking_force(lanes) * 9.81` kN.

---

## R4: Utilization Ratio Chart Keys (STEP A)
- **Status**: Already correct. The keys `steel_girders_wt_total`, `bracing_top_wt_total`, `bracing_bot_wt_total`, `bracing_diag_wt_total`, `concrete_deck_vol_total`, `rebar_deck_wt_total` already match the BOQ output exactly. No chart code changes needed.
- **Tests**: All 43 `test_report_charts.py` tests pass, including `test_realistic_data_produces_both_charts` and `test_string_values_from_boq`.

---

## R5: Material Quantity Charts (STEP A)
- **Status**: All quantity chart tests pass with correct keys and values (32.89, 0.11, 0.11, 0.25, 63.0, 7.56).
- **String values**: `test_string_values_from_boq` verifies that string values ("32.89", "63.00") from the BOQ work correctly.
- **All-missing case**: `test_all_steel_missing_returns_none` verifies steel chart returns None when all steel values are None.
- **End diaphragms N/A**: `test_only_end_diaphragms_missing_shows_na_bar` verifies hatched grey N/A bar appears when only end diaphragms is missing.

---

## R6: Style Audit (No Hardcoded Colours/Layouts in Chapters)
- **`definecolor`/`usepackage`**: No hardcoded instances in chapter files (`chap*.py`, `executive_summary.py`).
- `tabcolsep`/`arraystretch`: All table spacing now sourced from `styles.py`. The sole `\renewcommand{\arraystretch}{1.25}` in `chap4.py` replaced with `\tall_row_stretch()` from `styles.py`.
- **Colour escapes**: No `\textcolor{red}` etc. remaining in chapter files; all colours should come from `styles.py.COLORS`.

---

## Bug Fixes (STEP D)

### a) Table 2.7: depth/flange/web in mm (not "1.67 mm")
- **File**: `src/osdagbridge/core/reports/report_utils.py` — added `_render_m_as_mm()`.
- **File**: `src/osdagbridge/core/reports/chap2.py` — `_dim_row()` now uses `_render_m_as_mm(input_dict, key)` for girder depth, web thickness, and flange widths/thicknesses.
- **Result**: Inputs in metres are converted to integer millimetres (e.g. 1.67 m → "1670", 0.51 m → "510", 0.01 m → "10").

### b) Table 3.6: "=34.25 °C" → "$-$34.25 °C"
- **File**: `src/osdagbridge/core/reports/chap3.py` — added `_temp()` helper that prepends `$-$` for negative values, preventing the bare hyphen from rendering as `¿` in OT1 LaTeX encoding.
- **Result**: Negative temperatures render as "$-$34.25 °C".

### c) Fatigue note: "¿ 25 mm" → "$>$ 25 mm"
- **File**: `src/osdagbridge/core/reports/chap5.py` line 1234.
- **Result**: `$>$ 25 mm` (escaped > character).

### d) Executive Summary "Key Design Outcomes" unconditional pass/fail
- **File**: `src/osdagbridge/core/reports/executive_summary.py`.
- **Change**: Each outcome line (Girder, Cross bracing, End Diaphragm, Deck) now drives from real check results with PASS green (`\textcolor{osdagGreen}{PASS}`) / FAIL red (`\textcolor{urFail}{FAIL}`) from `styles.py` colours, instead of unconditional "pass".
- **Logic**: Uses `girder_max_ur`, `deck_max`, `_max_member_efficiency(cb_results)`, `_max_member_efficiency(ed_results)` to determine pass/fail status.

### e) End diaphragm tables 5.26-5.28 repeat cross bracing values
- **File**: `src/osdagbridge/core/reports/chap5.py`.
- **Change**: Replaced the `cb_forces_content` (cross bracing values 40x40x3) with a clear note: "End Diaphragm design data is not available in this design run. No values are invented."
- **Rationale**: End-diaphragm member data (section, forces, slenderness) is not produced by the design pipeline; reusing bracing values would be incorrect.

### f) Table 5.7: stiffener spacing blank; thickness 21.1 / 1.2 look wrong
- **File**: `src/osdagbridge/core/reports/chap5.py`.
- **Change**: Stiffener values now read from `bridge.input_dict` with correct keys (`KEY_MP_STIFFENER_INTERMEDIATE_SPACING`, `KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS`, `KEY_MP_STIFFENER_BEARING_THICKNESS`, `KEY_MP_STIFFENER_NO_BEARING_STIFFENERS`, `KEY_MP_STIFFENER_DESIGN_METHOD`, `KEY_MP_STIFFENER_LONGITUDINAL`) instead of the unreliable `steeldesign.details.stiffener_summary.*` output keys.
- **Root cause**: The output-only `stiffener_summary` keys were not populated by the design pipeline, causing blank/spurious values.

### g) Add `escape_latex()` for all user-entered text
- **File**: `src/osdagbridge/core/reports/report_utils.py` — added `escape_latex()` function.
- **File**: `src/osdagbridge/core/reports/report_generator.py` — title-page tokens now use `escape_latex()` instead of `_tex()` for `project_name`, `designer`, `client`, `company`, `subtitle`.
- **Purpose**: Handles special characters (`&`, `%`, `$`, `#`, `{`, `}`, `_`, `~`, `^`) so strings like `"A & B_100% #1"` do not break pdflatex compilation.
- **Usage**: Single helper for all user-entered text embedded in LaTeX.

---

## Known Limitations
| Limitation | Status | Workaround |
|------------|--------|------------|
| End diaphragm design data | Not available from backend | Note shown in tables 5.26-5.28 ("design data not available") |
| Centrifugal force in Table 3.3 | N/A for non-curved bridges | Shown as "N/A" with note about curved bridges |
| Figure placeholders | Some figures may be placeholders if not generated | GUI `Design → Generate Report` exports headless views |
| Footoverlap (R2) | Pending PDF verification | `footskip` increased to 40pt; verify with generated PDF |

---
*Document generated during dev cycle. See git diff for full change set.*