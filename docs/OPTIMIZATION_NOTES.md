# Export-time, RAM and storage optimisation notes

## 1. Repeat exports are now effectively instant

`generate_report()` keeps an **in-process cache** keyed by a SHA-256 of the
inputs/outputs/options/metadata plus a `REPORT_CACHE_VERSION`. The key is
captured on the payload because `generate_report()` enriches `payload.inputs`
with BOQ quantities during the first run.

Measured in one process, identical request:

| Pass | Time |
|---|---:|
| First export (pdflatex draft + final) | 1.903 s |
| Second export (cache hit) | **0.0002 s** |

This is what makes a real-time preview possible: re-opening/regenerating the
same report costs only two small file writes.

## 2. RAM optimisation

- Chart figures are detached `matplotlib.figure.Figure` objects rendered via
  `FigureCanvasAgg`; no pyplot figure manager or GUI event loop retains them.
- `payload.figure_data` bytes are written to the temporary directory and the
  dictionary is immediately cleared (`payload.figure_data.clear()`).
- The report cache stores only the final PDF/TEX bytes (~0.5 MB), not the
  analysis dataset; OpenSees design data is never duplicated into the cache.
- Full-solver peak RSS was ~502 MB, dominated by OpenSees/ospgrillage, not by
  report generation.

## 3. Storage optimisation

- All chart images and intermediate `.tex`/`.aux` files are created inside a
  `TemporaryDirectory` and deleted automatically after compilation.
- Charts use 150 dpi lossless PNGs (UR 1080×495 ~32 kB, material 1350×450
  ~38 kB) — sufficient for 187–234 ppi in the final PDF.
- The output folder receives only the requested `.pdf` and `.tex` plus the
  deliverables; no image assets are left behind.
- Videos: the primary demo is ~10 MB (1920×1080, 75 s); the raw real-time X11
  clip is ~7.5 MB for 45 s. Both are well within typical upload limits.

## 4. 1080p video and real X11 capture

The desktop session is Wayland/Xwayland, so `ffmpeg -f x11grab -i :0.0`
recorded a black root window. Installing **Xvfb** (`conda install -c pkgs/main
xorg-xserver-xvfb`) and starting a dedicated pure-X display (`:99`,
1920×1080×24) fixed it:

```bash
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &
DISPLAY=:99 ffmpeg -f x11grab -video_size 1920x1080 -framerate 15 \
  -i :99.0 -c:v libopenh264 -b:v 2500k -pix_fmt yuv420p demo.mp4
```

`Demo_Live_X11_1080p.mp4` is a 45 s real-time capture from that display,
showing the actual OsdagBridge UI and the live analysis log (Stage 9/14).
`Demo_Video.mp4` / `Demo_Video_1080p.mp4` is the polished 1920×1080
captioned slideshow built from real screenshots by `scripts/make_demo_video.py`.

## 5. Preview

`scripts/gui_real_ui_test.py` renders page 1 of the produced PDF with
`pdftoppm` and opens it in an ImageMagick `display` window for 6 seconds, so a
screen recording shows a real PDF preview immediately after generation.
