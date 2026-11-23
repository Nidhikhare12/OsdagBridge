"""Render a before/after page from two PDFs and compose a labelled side-by-side PNG.

Used by CI to embed a visual comparison in the PR comment.

    python scripts/make_ci_comparison.py BEFORE.pdf AFTER.pdf PAGE OUT.png
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import matplotlib

FONT = (Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
        / "DejaVuSans.ttf")


def _render(pdf: str, page: int, dest: Path) -> Path:
    subprocess.run(
        ["pdftoppm", "-f", str(page), "-l", str(page), "-r", "80",
         "-png", "-singlefile", pdf, str(dest)],
        check=True, capture_output=True)
    return dest.with_suffix(".png")


def main() -> None:
    before, after, page, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    with tempfile.TemporaryDirectory() as tmp:
        b = _render(before, page, Path(tmp) / "before")
        a = _render(after, page, Path(tmp) / "after")
        ib, ia = Image.open(b).convert("RGB"), Image.open(a).convert("RGB")
        h = 700
        ib = ib.resize((int(ib.width * h / ib.height), h))
        ia = ia.resize((int(ia.width * h / ia.height), h))
        pad, bar = 20, 60
        W = ib.width + ia.width + pad * 3
        H = h + bar + pad * 2
        canvas = Image.new("RGB", (W, H), (245, 246, 240))
        canvas.paste(ib, (pad, bar + pad))
        canvas.paste(ia, (ib.width + pad * 2, bar + pad))
        d = ImageDraw.Draw(canvas)
        d.rectangle((0, 0, W, bar), fill=(34, 34, 34))
        f = ImageFont.truetype(str(FONT), 30)
        d.text((pad, 14), "BEFORE (baseline)", font=f, fill=(255, 120, 120))
        d.text((ib.width + pad * 2, 14), "AFTER (this PR)", font=f, fill=(145, 220, 120))
        canvas.save(out)
        print(f"Wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
