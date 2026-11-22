"""Build a polished silent demo video from the real GUI/report captures.

Requires Pillow and ffmpeg.  Run from the repository root:

    python scripts/make_demo_video.py
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
FONT = (Path(matplotlib.__file__).parent / "mpl-data" / "fonts" /
        "ttf" / "DejaVuSans.ttf")
if not FONT.exists():
    FONT = Path("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf")

W, H = 1920, 1080
BAR = 104
BG = (245, 246, 240)
GREEN = (145, 176, 20)
DARK = (34, 34, 34)

SLIDES = [
    ("TITLE", "OsdagBridge - Design Report Enhancements",
     "GUI - Tables - Charts - Verification", 5),
    ("gui_window.png", "1. Real OsdagBridge desktop UI",
     "Basic Inputs, 2-D CAD canvas and Design button", 5),
    ("gui_after_design.png", "2. Design completed in the real UI",
     "1001 output keys from OpenSees + IRC 22 design", 5),
    ("gui_after_report.png", "3. Generate Report clicked in the real UI",
     "Dialog -> QThread worker -> PDF", 5),
    ("report_assets/before_loads.png", "4. Before: merged Live Loads table",
     "Values and units mixed in one column", 5),
    ("report_assets/after_loads.png", "5. After: structured load tables",
     "Vehicle / footway split, units, shaded headers", 6),
    ("report_assets/ur_chart.png", "6. Utilization Ratio chart (Section 5.5)",
     "Red dashed UR = 1.0 threshold", 6),
    ("report_assets/material_chart.png", "7. Material quantity charts (Chapter 7)",
     "Steel tonnage, concrete volume, rebar weight", 6),
    ("report_assets/real_page30.png", "8. Real design, Page 30",
     "G4 rows clear of footer; header repeated", 7),
]


def _font(size):
    return ImageFont.truetype(str(FONT), size)


def _slide(image_path, title, subtitle, duration, workdir, index):
    canvas = Image.new("RGB", (W, H), BG)
    if image_path == "TITLE":
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, W, 16), fill=GREEN)
        draw.text((W // 2, H // 2 - 70), title, font=_font(64),
                  fill=DARK, anchor="mm")
        draw.text((W // 2, H // 2 + 30), subtitle, font=_font(38),
                  fill=GREEN, anchor="mm")
    else:
        img = Image.open(OUT / image_path).convert("RGB")
        img.thumbnail((W - 40, H - BAR - 40))
        canvas.paste(img, ((W - img.width) // 2, 20))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, H - BAR, W, H), fill=DARK)
        draw.text((40, H - BAR + 20), title, font=_font(40), fill="white")
        draw.text((40, H - BAR + 62), subtitle, font=_font(26), fill=(200, 215, 180))
    path = workdir / f"slide_{index:02d}.png"
    canvas.save(path)
    return f"file '{path}'\nduration {duration}\n", duration


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        lines, total = [], 0
        for i, (img, title, sub, dur) in enumerate(SLIDES):
            line, dur = _slide(img, title, sub, dur, workdir, i)
            lines.append(line)
            total += dur
        lines.append(f"file '{workdir / 'slide_00.png'}'\n")
        listing = workdir / "list.txt"
        listing.write_text("".join(lines))

        target = OUT / "Demo_Video.mp4"
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-vf", f"scale={W}:{H},setsar=1", "-c:v", "mpeg4", "-q:v", "3",
            "-pix_fmt", "yuv420p", "-r", "10", str(target),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Wrote {target} ({total} s)")


if __name__ == "__main__":
    main()
