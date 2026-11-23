
> **Note:** `deliverables/` and `*.zip` are intentionally **git-ignored**. They are generated locally (see the reproduction commands) and/or published by CI to the public `ci-reports` branch. Upload the PDFs/ZIP separately with your submission; they are not part of the git diff.

# PDF and video quality review (final refinement loop)

## 1. Report PDF (`deliverables/Report_After.pdf`)

| Check | Result | Verdict |
|---|---|---|
| Page count | 47 pages (baseline 42) | Complete report, 3 extra pages from charts |
| PDF metadata | Title `OsdagBridge Design Report - Sample Steel Girder Bridge`; Author `OsdagBridge / FOSSEE`; Subject and Keywords set | Pass |
| Navigation | `linktoc=all` — TOC entries clickable | Pass |
| Fonts | All Type 1 fonts embedded and subset (`pdffonts`) | Pass |
| Images | Cover logo 768×258 lossless; UR chart 1080×495 @187 ppi lossless; material chart 1350×450 @234 ppi lossless | Pass |
| Colour | Osdag green header/footer rules `#91B014`, shaded table headers `#EAF2D6`; 94 `rowcolor` instances in source | Pass |
| Layout | No out-of-margin text spans; no significant text overlaps (PyMuPDF geometry check) | Pass |
| Headers | 50 `\endhead` repetitions vs 2 in baseline; verified on continuation pages | Pass |
| MuPDF | `mutool clean -gggg` exit 0, rewritten PDF pixel-identical | Pass |
| LibreOffice | Draw import/re-export: 47 pages, identical page-11 text length | Pass |
| pypdf / PyMuPDF | 47 pages parsed, text extraction works | Pass |

**Judgement:** the PDF is publication-quality for this task: consistent palette,
embedded fonts, lossless figures, correct repeated headers, and clean
interoperability with three independent PDF engines. The only cosmetic
difference after a LibreOffice round-trip is JPEG recompression of the cover
logo, so the direct export is the higher-fidelity master.

## 2. Demo video (`deliverables/Demo_Video.mp4`)

| Property | Value |
|---|---|
| Duration | 75 s |
| Resolution | **1920×1080** |
| Codec | MPEG-4 Part 2 (`mpeg4`), `yuv420p` |
| Audio | None (silent, as permitted) |
| Slides | 9: title card, real GUI, after-design, after-report, before/after load tables, UR chart, material chart, Page 30/G4 |
| Captions | White title + subtitle bar on every content slide |
| Source | Real screenshots from the conda-env GUI tests and rendered report pages |
| Reproducible | `python scripts/make_demo_video.py` (Pillow + ffmpeg) |
| Real-time capture | `Demo_Live_X11_1080p.mp4` — 34 s 1920×1080 Xvfb/x11grab recording of the live GUI and analysis log |

Frame extraction at 2 s and 30 s confirms the title card and captioned report
slides render correctly — not a black screen (the earlier raw X11 capture was
black because the display is Wayland/Xwayland).

Two early slides originally used screenshots of the OCC 3-D viewport captured
under software OpenGL; the Mesa framebuffer was garbled (coloured streaks).
Those slides were replaced with clean text cards, and caption bars were raised
64 px so video-player overlays cannot cover them.

Frame-by-frame audit (15 samples across the main video and 9 across the live
clip) confirms: no black lead-in in either video, no one-frame title flash at
the end, chronological slide order, readable captions, and a live clip that
starts on the visible GUI and ends on "Analysis Completed Successfully".

**Judgement:** the video satisfies “a short video showcasing the functionality;
a simple screengrab is sufficient; the video can be silent”. It is ready to be
uploaded as unlisted; only the upload/link is a manual user step.

## 3. Overall deliverable judgement

- Requirements: **6/6 implemented** with code, tests and artefact evidence.
- Verification: unit, sample, GUI, real UI buttons, real OpenSees design, real
  conda dependencies, cross-app PDF checks and a demo video.
- Performance: 2.18 s mean report generation, TeX-bound, no GPU path available.
- Submission-ready. Remaining manual steps: add collaborator, upload video,
  submit links/PDFs.
