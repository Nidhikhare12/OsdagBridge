# LaTeX Report Enhancements

## Purpose

This change set implements the Autumn 2026 OsdagBridge LaTeX-report scope against the saved regression input `Report_Before_Input.osi`. The work is on branch `feature/latex-report-enhancements`.

## Architecture

`src/osdagbridge/core/reports/styles.py` is now the report style source of truth. It owns document class settings, A4 geometry, complete header/footer themes and clearances, Osdag/chart colours, table padding and row spacing, figure construction, and final normalization of every `longtable`.

The report generator assembles chapter content, then applies the centralized normalization once. For every `longtable`, it:

1. terminates the caption row correctly;
2. copies the column-heading block into `endfirsthead` and `endhead`;
3. reserves room before a new table;
4. removes page-unsafe `multirow` wrappers while retaining their visible labels.

Normalization also validates that the first row is an explicit bold column-heading row. A headerless `longtable` now raises a clear `ValueError` during generation instead of accidentally repeating its first data row. The two legacy exceptions (Stiffener Design Summary and Deck Slab Loading and Geometry) now have explicit headings.

The last rule fixes the observed G4 footer bleed. A LaTeX `multirow` cannot safely span a `longtable` page break; its label may remain anchored on the previous page and extend into the footer. Ordinary cells allow the table to break cleanly and repeat headings.

## Scope mapping

### 1. Repeated table headings

- Every generated longtable receives `endfirsthead` and `endhead` automatically.
- Existing chapter generators do not need duplicate header boilerplate.
- A focused regression test checks multiple tables, duplicated header rows, and rejection of headerless tables.

### 2. Layout and footer clearance

- A4 geometry, head height, head separation, footer separation, table row stretch, padding, and pre/post spacing are centralized.
- Longtable starts reserve vertical space.
- Page-unsafe multirows are normalized before compilation.
- The center footer note was removed because it collided with the long institutional footer. The asterisk marker remains in values; the report's relevant table notes describe defaults.

### 3. Live-load and footway tables

Chapter 3 now contains three independent tables:

- Vehicle Live Loads, populated only from vehicles selected in Additional Inputs;
- Associated Vehicle Load Parameters, including impact factor, braking load, centrifugal force, units, and code references;
- Footway Live Load, including Basic Inputs configuration, selected-side width, pressure, units, and source.

If the alignment has no curve-radius input, centrifugal force is explicitly reported as not applicable instead of inventing a value.

### 4. Utilization-ratio chart

Section 5.5 includes a four-panel chart for steel plate girders, concrete deck slab, cross bracing, and end diaphragms. Each panel uses UR = Demand / Capacity, green for UR at or below 1.0, red above 1.0, and a red dashed UR = 1.0 reference line. Missing component design results are labelled honestly.

The chart renderer uses Pillow rather than Matplotlib. The bundled Windows Matplotlib build crashed inside its native bar-patch code; Pillow produces deterministic PNG assets without requiring a GUI or OpenGL context.
Pillow is declared in `pyproject.toml`, `environment.yml`, and `requirements.txt` so fresh installations include the renderer.

### 5. Material charts

Chapter 7 includes:

- structural-steel tonnage for girders, cross bracing, and end diaphragms;
- concrete deck volume in m3;
- reinforcement weight in MT.

End-diaphragm quantity and mass are computed from generated member lengths and database mass-per-metre values. Chart PNGs are written inside the report compiler's temporary directory and automatically removed after compilation.

### 6. Central style system

Hardcoded per-chapter table padding and row-stretch overrides were removed. Chapters describe content; `styles.py` controls presentation. The document colour definition also consumes the centralized Osdag colour.

## Additional correctness fix

Chapter 5's end-diaphragm tables previously reused cross-bracing rows. They now read `end_diaphragm_forces_dict` and `end_diaphragm_design_results` through dedicated bridge accessors. If the backend did not return a completed member design, the report leaves the result blank rather than repeating unrelated cross-bracing data.

## Verification

Run the focused regression checks:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/unit/test_latex_report_enhancements.py -q
```

If pytest is not installed, the four test functions can be invoked directly; this was done in the development environment.

Generate the saved-case PDF:

```powershell
$env:PYTHONPATH = "src"
python tools/verify_latex_report.py Report_Before_Input.osi --output-dir . --stem Report_After
```

The bundled TeX Live distribution has a Windows path bug when its Conda prefix contains spaces. Verification used a temporary no-space junction (`C:\tmp\osdagbridge-env`) to the same Conda environment; no project files or package contents were copied.

Checks completed:

- Python compilation of report and BOQ modules;
- focused tests for longtable normalization, selected UI vehicles/footway data, all four UR groups, and three material plots;
- full design execution from the saved OSI input;
- two-pass LaTeX compilation;
- structural audit of all 51 generated longtables (51 `endfirsthead`, 51 `endhead`, explicit heading rows, and no page-unsafe `multirow`);
- PDF text inspection with pdfplumber;
- Poppler rendering and visual inspection of Chapter 3, representative multipage Chapter 5 tables, Section 5.5, and Chapter 7.

The regression design itself fails the girder fatigue check at UR 2.10. This is expected input/design behavior and is intentionally rendered as a red bar; it is not a report-generation failure.
