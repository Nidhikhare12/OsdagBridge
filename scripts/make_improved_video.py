"""Build an improved demo video with richer real screenshot content.

Improvements over make_demo_video.py:
- gui_after_design.png (35% dark content, full design output) instead of gui_window.png
- gui_after_report.png added (report export dialog)
- ci_before_after.png side-by-side comparison slide added
- Fewer pure text cards; every slide shows real visual evidence

Run from repo root:
    python scripts/make_improved_video.py
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import matplotlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"

FONT_PATH = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / "DejaVuSans.ttf"
FONT_BOLD_PATH = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"
if not FONT_PATH.exists():
    FONT_PATH = Path("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf")
    FONT_BOLD_PATH = FONT_PATH

W, H = 1920, 1080
BAR_H = 112                 # caption bar height
CAPTION_Y_OFFSET = 68      # keep captions clear of player controls
BG = (245, 246, 240)       # Osdag off-white
GREEN = (145, 176, 20)     # Osdag green  #91B014
DARK = (34, 34, 34)
WHITE = (255, 255, 255)
SAGE = (200, 215, 180)


# ---------------------------------------------------------------------------
# Slide definitions: (image_path | "TITLE", title_text, subtitle_text, duration_s)
# ---------------------------------------------------------------------------
SLIDES = [
    # 0: Branded title card
    ("TITLE",
     "OsdagBridge — Report Generator Enhancements",
     "FOSSEE Winter Internship Screening Task  |  November 2026",
     5),

    # 1: Real desktop GUI — clean left panel only (3D viewport cropped out, it was garbled Mesa/software OpenGL)
    ("report_assets/gui_after_design_clean.png",
     "1. OsdagBridge real desktop UI — after design run",
     "1001 output keys  |  OpenSees grillage + IRC 22 member design",
     7),

    # 2: Report export dialog — clean left panel only
    ("report_assets/gui_after_report_clean.png",
     "2. Generate Report dialog — real UI",
     "QThread worker → pdflatex → PDF  |  First export: 1.90 s",
     6),

    # 3: Before/After side-by-side comparison
    ("report_assets/ci_before_after.png",
     "3. Before vs After — Live Load table (Page 11)",
     "Merged raw table  →  Vehicle + Footway tables with units & shaded headers",
     7),

    # 4: Before loads table (PDF page screenshot)
    ("report_assets/before_loads.png",
     "4. BEFORE — merged Live Loads table",
     "Values, units and classes in one unstructured column  |  No impact factor column",
     6),

    # 5: After loads table (PDF page screenshot)
    ("report_assets/after_loads.png",
     "5. AFTER — structured Load tables",
     "Table 3.3 Vehicle Loads  +  Table 3.4 Footway Load  |  Shaded headers repeat on every page",
     7),

    # 6: UR chart
    ("report_assets/ur_chart.png",
     "6. NEW — Utilization Ratio chart  (Section 5.5)",
     "Green = pass (UR ≤ 1.0)  |  Red dashed limit line  |  Values annotated",
     7),

    # 7: Material quantity chart
    ("report_assets/material_chart.png",
     "7. NEW — Material Quantity charts  (Chapter 7)",
     "Steel tonnage  |  Concrete volume (m³)  |  Rebar weight (MT)",
     7),

    # 8: Page 30 footer proof
    ("report_assets/real_page30.png",
     "8. Real design — Page 30  (Girder G4)",
     "50 longtable headers repeat on continuation pages  |  No footer overflow",
     7),

    # 9: Closing title card
    ("TITLE",
     "All 6 requirements implemented  ·  9 unit tests passing",
     "Branch: report-generator-enhancements  |  github.com/danish9661/OsdagBridge",
     5),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD_PATH if bold else FONT_PATH
    return ImageFont.truetype(str(path), size)


def _draw_caption_bar(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    """Draw the dark caption bar near the bottom of the canvas."""
    bar_top = H - BAR_H - CAPTION_Y_OFFSET
    draw.rectangle((0, bar_top, W, bar_top + BAR_H), fill=DARK)
    draw.text((40, bar_top + 12), title, font=_font(40, bold=True), fill=WHITE)
    draw.text((40, bar_top + 60), subtitle, font=_font(26), fill=SAGE)


def _make_title_card(title: str, subtitle: str) -> Image.Image:
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    # Green top stripe
    draw.rectangle((0, 0, W, 18), fill=GREEN)
    # Green bottom stripe
    draw.rectangle((0, H - 18, W, H), fill=GREEN)
    # Center text
    draw.text((W // 2, H // 2 - 80), title, font=_font(60, bold=True),
              fill=DARK, anchor="mm")
    draw.text((W // 2, H // 2 + 30), subtitle, font=_font(34),
              fill=GREEN, anchor="mm")
    return canvas


def _make_screenshot_slide(img_rel_path: str, title: str, subtitle: str) -> Image.Image:
    img_path = OUT / img_rel_path
    src = Image.open(img_path).convert("RGB")

    # Available area for the screenshot (leave room for caption bar + padding)
    avail_h = H - BAR_H - CAPTION_Y_OFFSET - 40  # 40 px top padding
    avail_w = W - 40                              # 20 px side margin each side

    src.thumbnail((avail_w, avail_h), Image.LANCZOS)

    canvas = Image.new("RGB", (W, H), BG)
    # Centre the screenshot horizontally, top-pad 20 px
    paste_x = (W - src.width) // 2
    paste_y = 20
    canvas.paste(src, (paste_x, paste_y))

    draw = ImageDraw.Draw(canvas)
    _draw_caption_bar(draw, title, subtitle)
    return canvas


def _build_slide(img_path: str, title: str, subtitle: str,
                 duration: int, workdir: Path, index: int) -> tuple[str, int]:
    if img_path == "TITLE":
        canvas = _make_title_card(title, subtitle)
    else:
        canvas = _make_screenshot_slide(img_path, title, subtitle)

    out_path = workdir / f"slide_{index:02d}.png"
    canvas.save(out_path)
    return f"file '{out_path}'\nduration {duration}\n", duration


def main() -> None:
    target_1080p = OUT / "Demo_Video_Improved_1080p.mp4"

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        lines: list[str] = []
        total_duration = 0
        last_line = ""

        for i, (img, title, sub, dur) in enumerate(SLIDES):
            line, d = _build_slide(img, title, sub, dur, workdir, i)
            lines.append(line)
            total_duration += d
            last_line = line

        # ffmpeg concat demuxer needs trailing entry
        lines.append(last_line)

        listing = workdir / "slides.txt"
        listing.write_text("".join(lines))

        print(f"Building {len(SLIDES)}-slide video ({total_duration} s) → {target_1080p.name}")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                   f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0xF5F6F0,"
                   "setsar=1",
            "-c:v", "mpeg4",
            "-q:v", "2",           # higher quality than original (was 3)
            "-pix_fmt", "yuv420p",
            "-r", "10",
            str(target_1080p),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffmpeg stderr:", result.stderr[-1000:])
            raise RuntimeError("ffmpeg failed")

        size_mb = target_1080p.stat().st_size / 1024 / 1024
        print(f"✓ Written: {target_1080p}  ({size_mb:.1f} MB, {total_duration} s)")
        print(f"  Slides: {len(SLIDES)}")
        print(f"  Resolution: {W}×{H}")


if __name__ == "__main__":
    main()
