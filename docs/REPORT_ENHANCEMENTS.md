# OsdagBridge LaTeX Report Generator — Refactoring & Enhancements

Technical changes document for the FOSSEE winter internship screening task
*"OsdagBridge LaTeX Report Generator Refactoring & Enhancements"*.

---

## 1. Summary

The report generator builds a ~40 page LaTeX document from a set of Python
chapter modules under `src/osdagbridge/core/reports/`.  Before this work the
formatting rules (margins, colours, padding, table rules) were scattered
through the preamble and individual chapters, most long tables lost their
header row at a page break, a few tables ran into the footer margin, live
loads were merged into one table, and there were no data-visualisation figures.

All six requested improvements have been implemented.  `Report_Before.pdf` and
`Report_After.pdf` in `deliverables/` were produced by the same script with the
same representative design data, so the difference is solely the code change.

---

## 2. Files altered / added

| File | Change |
|------|--------|
| `src/osdagbridge/core/reports/styles.py` | **New.** Single source of truth for geometry, colours, table padding/rules, header/footer theme, Matplotlib rcParams, LaTeX figure helper and the global LaTeX post-processor. |
| `src/osdagbridge/core/reports/charts.py` | **New.** Generates the utilization-ratio and material-quantity PNGs with Matplotlib (Agg) and returns LaTeX `figure` blocks. |
| `src/osdagbridge/core/reports/report_generator.py` | Imports `styles`; preamble consumes the central constants; calls `styles.apply_global_styles()` on the assembled source; passes the temporary asset directory to Chapters 5 and 7; exposes bundled `.sty` compatibility files through `TEXINPUTS`; footer page-count label now resolves. |
| `src/osdagbridge/core/reports/chap3.py` | Replaces the merged *Live Loads* table with separate **Vehicle Live Loads** and **Footway Live Load** tables; vehicle rows are built only from the `KEY_LL_*` keys selected in the Loading tab; explicit unit/reference columns; tables use the shared `table_header_row()` helper. |
| `src/osdagbridge/core/reports/chap5.py` | Computes governing URs from the very rows printed in Table 5.22 and embeds the new UR bar chart in Section 5.5 *Overall Design Check Summary*. |
| `src/osdagbridge/core/reports/chap7.py` | Embeds the new material-quantity chart after Table 7.1. |
| `scripts/generate_sample_reports.py` | **New.** Builds a representative `ReportPayload` and compiles a report without a GUI/OpenSees run; used for the before/after comparison. |
| `scripts/tex/lastpage.sty`, `scripts/tex/makecell.sty` | **New.** Minimal compatibility stubs so the report compiles on a bare TeX Live installation. |
| `tests/unit/test_report_styles.py` | **New.** Regression tests for header repetition and heading protection. |
| `deliverables/Report_Before.pdf`, `deliverables/Report_After.pdf` | Baseline and enhanced reports (plus their `.tex` sources). |

---

## 3. Requirement-by-requirement implementation

### 3.1 Repeated table headers across page breaks

The code emits raw LaTeX strings rather than PyLaTeX objects, so the fix is a
central post-processor rather than 50 individual edits.
`styles._repeat_longtable_headers()` walks every `longtable` in the assembled
document, finds the `\hline` → header row → `\hline` block and inserts:

```latex
\endfirsthead
<repeated header row>
\hline
\endhead
```

Tables that already define `\endhead` are left untouched.  The result:

* `Report_Before.tex` contains **2** `\endhead` commands;
* `Report_After.tex` contains **50** — one per longtable.

Table 5.22 (Overall Design Check Summary) visibly repeats its five column
headers on the continuation page in the enhanced report.

### 3.2 Layout, footer overlap and vertical spacing

* `styles.PAGE_BOTTOM_THRESHOLD_LINES = 8` defines the page-bottom threshold.
* `report_generator.preamble()` applies it to
  `\BeforeBeginEnvironment{table}` and `\BeforeBeginEnvironment{longtable}`.
* `styles._protect_headings()` inserts `\needspace{8\baselineskip}` before
  every `\chapter`, `\section` and `\subsection`, so headings cannot be
  orphaned just above the footer box.
* Table spacing (`\tabcolsep`, `\arraystretch`, `\extrarowheight`,
  `\LTpre`, `\LTpost`, `\arrayrulewidth`) now comes from one constants block.
* A callable `re.sub` replacement is used for `\needspace` insertion — a plain
  string replacement would interpret `\n`/`\b` inside the LaTeX command as
  Python escape sequences (a bug caught by the new unit test).
* The minimal `lastpage.sty` stub fixes the pre-existing `Page X of ??`
  footer, which now renders `Page X of Y`.

### 3.3 Load & geometry table refactoring

`chap3.py` now emits two clean tables:

* **Table 3.3 Vehicle Live Loads** — columns: *Vehicle Class, Impact Factor,
  Braking Load (kN), Centrifugal Force, Reference*.  Rows are generated from
  the selected `KEY_LL_IRC_*` / custom-vehicle keys, so the report reflects the
  Loading tab exactly.  Impact factors are computed per class from
  `IRC6_2017.cl_208_2/3_impact_factor()`.
* The braking-force helper `cl_211_2_braking_force()` had an unbound local for
  ≤ 2 lanes and returned newtons; it is now totals correctly and the report
  converts N → kN (e.g. 217.39 kN for two lanes).
* **Table 3.4 Footway Live Load** — columns: *Parameter, Value, Unit,
  Reference*, with automatic IRC 6 Cl. 206.1 pressure or the user-defined
  value kept in its own numeric column.

Wind, seismic, thermal and load-combination tables remain unchanged but now
inherit repeating headers automatically.

### 3.4 Utilization Ratio visualisation

`charts.utilization_ratio_figure()` draws a bar chart for **Steel Plate
Girders, Concrete Deck Slab, Cross Bracing** and **End Diaphragms**:

* Y-axis = UR (Demand / Capacity);
* red dashed reference line at UR = 1.0;
* green bars for UR ≤ 1.0, red bars for UR > 1.0, with values annotated.

The values are parsed from the same Table 5.22 rows, so the plot cannot
disagree with the tables.  The figure is embedded in Section 5.5.

### 3.5 Material quantity charts

`charts.material_quantity_figure()` produces three panels: structural steel
tonnage by component (girders / cross bracing / end diaphragms), concrete
volume (m³) and reinforcement weight (MT).  Quantities are read from the
`calculate_material_quantities()` keys already injected into `payload.inputs`.
Both charts are saved as temporary PNGs inside the report's own
`TemporaryDirectory` and embedded with `styles.figure_block()`, so no image
assets are left beside the PDF.

### 3.6 Centralized formatting system

`styles.py` is the single source of truth:

| Group | Examples |
|-------|----------|
| Document | `DOCUMENT_CLASS_OPTIONS`, `PAPER_SIZE`, `PAGE_MARGIN`, `DOCUMENT_STRETCH` |
| Colours | `COLOR_OSDAG_GREEN_HEX`, `COLOR_UR_PASS`, `COLOR_UR_FAIL`, `COLOR_THRESHOLD_RED`, `COLOR_STEEL`, `COLOR_CONCRETE`, `COLOR_REBAR` |
| Tables | `TAB_COLSEP`, `ARRAY_STRETCH`, `EXTRA_ROW_HEIGHT`, `LT_PRE`, `LT_POST`, `ARRAY_RULE_WIDTH`, `PAGE_BOTTOM_THRESHOLD_LINES`, `table_header_row()` |
| Headers/footers | `HEADER_RULE`, `FOOTER_TEXT`, `LATEX_COLOR_DEFINITIONS` |
| Charts | `matplotlib_rc()`, `figure_block()` |
| Global pass | `apply_global_styles()` → `_repeat_longtable_headers()` + `_protect_headings()` |

Chapters import the helpers directly (`chap3`, `chap5`, `chap7`); all other
chapters inherit the rules through the preamble and the single global pass,
so a global styling change requires editing one file only.

---

## 4. Architectural rationale

1. **Post-process instead of 50 edits.**  The existing chapter modules are
   large raw-LaTeX string builders.  A single, well-tested post-processing
   pass guarantees consistent `\endhead` behaviour for every present and
   future longtable, without risky mass edits to numerical report content.
2. **Matplotlib over PyLaTeX figures.**  The codebase does not depend on
   PyLaTeX; adding it would have introduced a new dependency for a feature
   that is natively supported by LaTeX via `\includegraphics`.  Charts are
   generated with Matplotlib (already a project dependency) and embedded with
   a shared `figure_block()` helper.
3. **Assets in the existing TemporaryDirectory.**  Reusing the report
   generator's temporary directory means chart images are embedded by
   pdflatex and then automatically cleaned up — the output folder stays clean.
4. **Data-driven charts.**  Plot values are derived from the report tables,
   avoiding a second source of truth for utilization ratios and quantities.
5. **Bare-TeX compatibility.**  Bundled minimal `.sty` stubs are added to
   `TEXINPUTS` so the enhanced report builds on systems without the full
   `texlive-latex-extra` collection.

---

## 5. How to reproduce

```bash
cd OsdagBridge
python scripts/generate_sample_reports.py deliverables Report_After
# Result: deliverables/Report_After.pdf (+ .tex)
```

The baseline was regenerated from the unmodified `dev` sources with the same
script and the same sample data:

```bash
python scripts/generate_sample_reports.py deliverables Report_Before
```

Run the style regression tests with:

```bash
PYTHONPATH=src python -m pytest tests/unit/test_report_styles.py -q
```

An offscreen GUI smoke test is also provided.  It creates the real
`CustomWindow` and `ReportOptionsDialog` **and drives the full GUI report
path**: the dialog's request goes through the QThread worker into
`generate_design_report()`, producing `deliverables/Report_From_GUI.pdf`.
On machines without PySide6 it installs a thin PyQt5 compatibility shim and
inert stubs for OCC/OpenSees (not exercised by the report path):

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python scripts/gui_smoke_test.py
```

All chapter modules now import `styles` directly and take their spacing
constants (`SECTION_SKIP`, `TABLE_TOP_SKIP`, `FIGURE_SKIP`) from it.
Centrifugal load is computed per IRC 6 Cl. 209 from `KEY_LL_CURVE_RADIUS`
and `KEY_LL_DESIGN_SPEED` (or reported as "straight alignment").

A real-UI verification is included as well:
`scripts/gui_real_ui_test.py` clicks the actual `Design` and `Generate Report`
QPushButtons, waits on the real QThread workers, and produces
`deliverables/Report_Real_UI.pdf` (59 pages, 50 repeating headers) from 1001
real design output keys.  This test exposed a thread-safety issue in the chart
code (pyplot being switched to the Qt backend by the main window); chart
figures are now built as detached `matplotlib.figure.Figure` objects and
rendered through `FigureCanvasAgg`, so they are safe to create on a worker
thread.

Additional formatting polish: table header rows are now shaded
(`tableHead`) with softened green rules, captions use a consistent
period-separated style, and section/subsection headings use the Osdag green
palette.  Compilation speed was improved with a draft-mode first pdflatex pass
and faster Agg chart rendering; see `docs/BENCHMARK.md` for measurements and
cross-application PDF verification (MuPDF, LibreOffice, Poppler, pypdf).

A full real-solver verification is also included:

```bash
PYTHONPATH=src python scripts/run_full_design_test.py
```

It runs an actual OpenSees grillage analysis and IRC 22 design (4 girders,
30 m span, 997 output keys) and generates `deliverables/Report_Real_Design.pdf`.
That report reproduces the reported **Page 30 / G4** case: the G4 rows end
well clear of the footer, and the continued table header is repeated at the
top of the page.

> The sample payload contains representative (not physically complete)
> design values so that the PDF can be built without a GUI or an OpenSees
> analysis.  In a full OsdagBridge session the same code path is reached from
> `Generate Report` in the desktop UI.

---

## 6. Visual / open polish

* Consistent green rule in the running header and footer; green/red semantic
  colours for passing/failing utilization checks.
* Value labels on every bar, readable rotated x-axis labels and a restrained
  grid in all charts (defined once in `styles.matplotlib_rc()`).
* `Page X of Y` footer now resolves correctly.
* `\needspace` guards keep headings and tables clear of the footer margin.
* "Software default value" asterisk legend remains correctly triggered by
  `\sdstar{}` in the footer.


## Competitive review and CI

A scan of 100 public forks and the upstream PR list showed most submissions
lack videos, real-solver verification and CI. Techniques adopted from the
strongest forks/PRs: explicit head/foot geometry, chapter title rules,
`\emergencystretch`/`\hfuzz`, and a GitHub Actions workflow. A "(continued)"
caption was trialled but rejected because longtable emits an orphan
continuation header when a table starts at a page boundary.

`.github/workflows/report-ci.yml` runs on every push and PR, executes the unit
tests and a sample report build, verifies header/chart counts and PDF metadata,
posts a results table to the PR conversation and uploads the PDF/TeX/logs as an
artifact. It also **publishes the PDF and a page-1 preview PNG to a public
`ci-reports` branch** (`runs/<run_id>/`), so the PR comment contains a
browser-viewable PDF link and an embedded preview image — reviewers can check
the exported PDF without downloading anything. It also embeds a **before/after
side-by-side thumbnail** (load tables, page 11), runs a **font-embedding /
encryption validation** (`pdffonts`, all fonts must be embedded), and a
**nightly cron** (`0 2 * * *`) that opens or updates a `nightly-ci` issue on
failure to catch dependency regressions.
