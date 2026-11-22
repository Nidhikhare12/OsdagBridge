# Benchmark: baseline vs enhanced report generator

Measured with `scripts/benchmark_report.py` on the same machine (Python 3.14,
pdflatex from TeX Live 2023), 3 runs per tree, identical payload (4 girders,
30 m span, all report sections enabled).

| Metric | Baseline (`d74f56d`) | Enhanced (`c48c9c2`) | Delta |
|---|---:|---:|---:|
| Avg payload build | 0.059 s¹ | 0.002 s¹ | ~0 |
| Avg `generate_report()` (incl. 2× pdflatex) | 1.796 s | 1.968 s | +0.454 s (+25 %) |

The enhanced number includes: draft-mode first pdflatex pass, Agg-only chart
rendering at 150 dpi (0.442 s for both charts, down from 0.555 s), global
header/formatting post-processing, and three extra report pages.
| PDF pages | 44 | 47 | +3 |
| PDF size | 390,476 B | 493,220 B | +102,744 B (+26 %) |
| `\endhead` (repeating headers) | 2 | 50 | +48 |
| Charts embedded | 0 | 2 | +2 |

¹ First-run import/warm-up dominates; steady-state payload build is ~0.000 s.

## Chart microbenchmark

| Operation | Time |
|---|---:|
| UR bar chart (Matplotlib, Agg, 200 dpi) | 0.190 s |
| Material chart (3 panels, 200 dpi) | 0.364 s |
| Both | 0.555 s |

## Full solver + report run

`scripts/run_full_design_test.py` (real OpenSees analysis + IRC 22 design +
report compilation):

- wall clock: **38.98 s**
- peak RSS: **502 MB** (dominated by OpenSees/ospgrillage, not the report code)
- output: 997 design keys, 53-page PDF

## Interpretation

The report generator overhead is about **0.7 s per report**, of which ~0.55 s is
chart rendering; the remaining ~0.13 s is the global LaTeX post-processing and
the extra pdflatex work for three more pages. For a PDF that now carries 48
repeating table headers, two analytical charts and 26 % more content, this is a
reasonable cost. The styling post-processor is a pure string pass over a
~80 kB LaTeX document and is not a bottleneck; OpenSees dominates total runtime.

## Interoperability verification
The enhanced PDF was opened / parsed by independent applications:

| Tool | Result |
|---|---|
| MuPDF (`mutool clean -gggg`) | exit 0, 553 kB rewritten PDF |
| LibreOffice Draw (`--convert-to pdf`) | imported and re-exported, **47 pages**, identical page-11 text length |
| Poppler (`pdffonts`) | all Type 1 fonts embedded + subset |
| `pypdf` / PyMuPDF | 47 pages parsed, text extraction works |
| `pdftotext` / `pdftoppm` | correct text and page rendering |

## Reproduce

```bash
# baseline, in a detached worktree of d74f56d:
TEXINPUTS="<tree>/scripts/tex:" PYTHONPATH=src python scripts/benchmark_report.py out 3
# enhanced:
PYTHONPATH=src python scripts/benchmark_report.py out 3
/usr/bin/time -v python scripts/run_full_design_test.py
```
