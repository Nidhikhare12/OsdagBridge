# Changelog — Report Generator enhancements

## Unreleased (screening-task branch `report-generator-enhancements`)

### Added
- `styles.py`: single source of truth for geometry, palette, table rules,
  header/footer theme, caption/section/chapter formatting and Matplotlib rcParams.
- `charts.py`: thread-safe Agg charts (UR summary, material quantities).
- Global LaTeX post-processor: repeating `\endfirsthead`/`\endhead` on every
  longtable, shaded header rows, `\needspace` heading protection.
- Explicit page geometry (`headheight`, `headsep`, `footskip`), `\emergencystretch`,
  `\hfuzz`, `\LTcapwidth`; green chapter/section title rules.
- PDF metadata (title/author/subject/keywords) and clickable TOC (`linktoc=all`).
- In-process SHA-256 report cache → identical repeat export/preview in ~0.0002 s.
- Separate Vehicle Live Loads and Footway Live Load tables with unit columns.
- Centrifugal-load keys and IRC 6 Cl. 209 computation; braking-force N→kN fix.
- Verification scripts: sample reports, GUI smoke test, real-UI button test,
  full OpenSees design test, detailed benchmark, demo-video builder.
- Live in-app Qt PDF preview after generation.
- 1920×1080 silent demo video + 34 s real-time Xvfb/X11 capture.
- GitHub Actions CI (`report-ci.yml`): runs on every push and PR, posts a
  results table to the PR conversation and uploads the PDF/TeX/logs as an artifact.
- 9 unit tests; docs: enhancements, benchmarks, performance detail,
  optimization notes, PDF/video review, data notes.

### Changed
- `deliverables/`, `*.zip` and Python/LaTeX build artefacts are now git-ignored; CI publishes the exported PDF publicly instead.
- First export reduced from ~2.85 s to ~1.90 s (no lazy OpenSeesPy import in
  report path, no `tight_layout`, no empty placeholder figures).
- Retired DCR check id 16 remapped to `deck_design_results` so the
  Transverse Shear (slab) summary row is populated.

### Fixed
- Repeating table headers on page breaks (2 → 50 `\endhead`).
- Footer overlap / "Page X of ??" footer.
- Garbled OCC-viewport video slides replaced; black X11 lead-in trimmed.
