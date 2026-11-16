# Technical Changes — OsdagBridge Report Generator Refactor

## Environment fixes (local macOS)
- Installed `osdag_core` (from conda `osdag-2026.04.0.0`) into the env — the
  installed `osdag 2025.01.a.2` lacked it, breaking cross-bracing member design
  ("No module named 'osdag_core'"). Populated its `Intg_osdag.sqlite` from the
  bundled `Intg_osdag.sql` (fixed "no such table: Material" skips).
- Installed TinyTeX (`~/Library/TinyTeX`) + required packages; symlinked
  `pdflatex`/`xelatex` into `/opt/homebrew/bin` (the previous `~/.local/bin`
  Tectonic shim halted on recoverable LaTeX errors).
- Downgraded PySide6 to 6.9.3 per `requirements.txt` (6.12 caused Cocoa hangs).

## New files
- `tools/generate_baseline_report.py` — headless driver replicating the GUI
  Design → Generate Report flow (defaults, material priming, compute
  functions, `PlateGirderBridge.design()`, `generate_report()`).
- `build_pdf.sh` — one-command report build (conda env + TinyTeX PATH + cleanup).
- `src/osdagbridge/core/reports/styles.py` — centralized style system.
- `src/osdagbridge/core/reports/charts.py` — matplotlib→PNG figure generators.

## styles.py (single source of truth)
- Color palette (`OSDAG_GREEN_HTML`, `COLOR_*`), semantic spacing/font macros
  (`SPACING_MACROS` → `\OsdagVspace*`, `\OsdagTabcolsep*`, font commands),
  geometry/package block, fancyhdr theme, columntypes, `\sdstar` machinery,
  `preamble()`, `title_page()`, `toc_section()`, and Python helpers
  (`PASS`, `FAIL`, `PASS_BLACK`, `status()`, `colored_status()`, `text_colored()`).

## Chapter files
- `report_generator.py`: preamble/title/TOC delegated to `styles`; added
  `_collect_utilization_ratios()` and hooks rendering material + UR charts into
  the temp images dir.
- `chap1–9`, `executive_summary.py`: all hardcoded `\vspace`, `\hspace`,
  `\setlength`, font-size, and `\textcolor` literals replaced by `\Osdag*`
  macros / `S.*` helpers.
- All ~49 `longtable`s now emit `\endfirsthead` (caption+header on page 1) and
  `\endhead` (repeated header on continuation pages); `\\` added after
  `\caption` (fixes misplaced-`\hline` errors).
- `chap3.py`: Live Loads (vehicle) and Footway Live Load split into two tables.
- `chap5.py`: accepts `fig_paths`, embeds UR summary chart in §5.5.
- `chap7.py`: accepts `fig_paths`, embeds steel-quantity and concrete-vs-rebar
  bar charts.

## Known gaps
- UR chart wiring is in place but produced no figure on the smoke input —
  `_collect_utilization_ratios` likely found no numeric URs in
  `design_results`/`deck_design_results` for this case; verify keys against a
  real GUI run.
- 5 small `table`[H]+`tabular` blocks (chap2 ×3, chap8 ×2) not converted.
- Footer-bleed fix relies on longtable migration + needspace guard; visual
  check of ~page 30 recommended.
