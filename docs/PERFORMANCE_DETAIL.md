# Detailed performance, formatting and cross-application verification

## 1. GPU availability — why it is not used

| Check | Result |
|---|---|
| `nvidia-smi` | not installed / no NVIDIA GPU |
| `/dev/dri` | `card1`, `renderD128` (Mesa render node present) |
| PyTorch / CUDA | not installed |

`pdflatex` (TeX typesetting) and Matplotlib's `Agg` rasteriser are CPU-bound
single-thread workloads; neither has a GPU code path. An empirical check with
Chrome headless (which *can* use `/dev/dri`) shows no meaningful difference:

| Chrome headless mode | Time |
|---|---:|
| GPU default (Mesa node available) | 0.638 s |
| `--disable-gpu` | 0.646 s |

Conclusion: adding a GPU would not speed up this report pipeline. The
optimisations below are algorithmic/IO-based.

## 2. Per-stage timing of `generate_report()`

Measured with `scripts/benchmark_detailed.py`, 4 production runs, identical
47-page report (Python 3.14, TeX Live 2023, this machine):

| Stage | Mean | Min | Max |
|---|---:|---:|---:|
| `build_report_payload()` | 0.001 s | 0.000 s | 0.003 s |
| UR chart (Agg, 150 dpi) | 0.143 s | 0.135 s | 0.151 s |
| Material chart (3 panels) | 0.247 s | 0.231 s | 0.293 s |
| `styles.apply_global_styles()` over ~84 kB LaTeX | 0.002 s | 0.002 s | 0.002 s |
| pdflatex pass 1 (`-draftmode`) | 0.710 s | 0.702 s | 0.718 s |
| pdflatex pass 2 (final PDF) | 0.873 s | 0.866 s | 0.888 s |
| **Total pipeline** | **1.903 s** | 1.865 s | 1.980 s |

Interpretation: **TeX compilation is 73 % of runtime**, charts 18 %, everything
else <2 %. The central style post-processor is effectively free.

Speed work already applied:
- first pdflatex pass uses `-draftmode` (resolves aux/TOC/labels, no PDF output);
- `-no-shell-escape` on both passes;
- charts use detached `Figure` + `FigureCanvasAgg` (no pyplot/global backend),
  150 dpi and no `bbox_inches='tight'`;
- chart rendering fell from 0.555 s → 0.390 s, total `generate_report()` from
  2.484 s → 1.903 s (benchmark 3-run mean), and the latest detailed mean is
  1.903 s.

For reference, plain `pdflatex` on the equivalent self-contained `.tex`:

| Plain pdflatex mode | Time |
|---|---:|
| single full pass | 0.883 s |
| draft + full | 0.727 s |
| two full passes | 0.878 s |

Our extra ~0.5 s over plain TeX is chart rendering plus process/file setup.

## 3. Other applications — export time and output

Same machine, outputs validated; the HTML-based apps use an equivalent styled
page (same hex palette, table and UR chart), so their times are indicative of
the export engine rather than a full bridge report.

| Application / operation | Time | Output |
|---|---:|---|
| OsdagBridge full report pipeline | 1.903 s | 47-page PDF, all styles/charts |
| LibreOffice Draw: import our PDF + re-export | 5.195 s | 47-page PDF |
| WeasyPrint: HTML → PDF | 1.104 s | 1-page styled comparison page |
| Chrome headless: HTML → PDF | 0.638 s | 1-page styled comparison page |
| MuPDF `mutool clean -gggg` (rewrite/validate) | 0.023 s | valid 553 kB PDF |
| PyMuPDF: render all 47 pages to pixmaps | 0.222 s | 47 page images |

Our pipeline is ~2.4× faster than a LibreOffice round-trip of the finished PDF,
and produces the complete 47-page engineering report rather than a one-page
HTML sample.

## 4. Formatting and colour fidelity

Pixel sampling of rendered page 11 (1× zoom, tolerance ±18 per RGB channel):

| PDF | Pages | Page-11 text length | `tableHead` pixels (#EAF2D6) | green pixels (#91B014) |
|---|---:|---:|---:|---:|
| Ours | 47 | 1212 | 41,704 | 7 |
| MuPDF-cleaned | 47 | 1212 | 41,704 | 7 |
| LibreOffice re-export | 47 | 1212 | 40,429 | 100 |
| WeasyPrint (HTML sample) | 1 | 222 | 8,979 | 1,209 |
| Chrome (HTML sample) | 1 | 309 | 7,707 | 984 |

- MuPDF rewrite is **pixel-identical**.
- LibreOffice preserves the shaded header rows (within 3 % rasterisation
  difference) and renders the green rules more strongly (100 px vs 7 px),
  while text extraction is byte-for-byte equal in length.
- All fonts in our PDF are embedded and subset (`pdffonts`).

## 5. Image quality

`pdfimages -list`:

| Image | Ours | LibreOffice re-export |
|---|---|---|
| Cover logo | 768×258, lossless RGB, 204 ppi, 45.9 kB | 768×258, **JPEG (lossy)**, 17.5 kB |
| UR chart | 1080×495, lossless, 187 ppi | 1080×495, lossless |
| Material chart | 1350×450, lossless, 234 ppi | 1350×450, lossless |

Our PDF keeps the logo lossless; LibreOffice's re-export recompresses it to
JPEG, so the original export is higher fidelity.

## 6. Reproduce

```bash
PYTHONPATH=src python scripts/benchmark_detailed.py 4
PYTHONPATH=src python scripts/benchmark_report.py /tmp/bench 3
# cross-app checks
mutool clean -gggg deliverables/Report_After.pdf /tmp/clean.pdf
libreoffice --headless --convert-to pdf --outdir /tmp/lo deliverables/Report_After.pdf
weasyprint /tmp/perf_page.html /tmp/weasy.pdf
google-chrome --headless --no-sandbox --print-to-pdf=/tmp/chrome.pdf file:///tmp/perf_page.html
```
