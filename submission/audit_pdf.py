"""Render PDF evidence and record text geometry for each physical page."""
import argparse
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pdf", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    markers = ("Key Design Outcomes Summary", "1670", "Vehicle Live Loads",
               "Footpath Live Load", "Stiffener Design", "Controlling LC",
               "Girder Design Summary", "Governing computed utilization",
               "Material quantities from the bill", "No end-diaphragm axial design checks")
    lines = ["| Physical page | Raster images | Footer intrusions | Words outside text width | Markers |",
             "| --- | ---: | --- | --- | --- |"]
    with fitz.open(args.pdf) as pdf:
        for page in pdf:
            index = page.number
            if index % 9 == 0:
                sheet = Image.new("RGB", (1200, 1767), "white")
                draw = ImageDraw.Draw(sheet)
            words = page.get_text("words")
            page_text = page.get_text()
            y_rules = sorted(d["rect"].y0 for d in page.get_drawings()
                             if d.get("color") and d["rect"].width > page.rect.width * .7
                             and abs(d["color"][1] - .69) < .01 and d["rect"].height < 1)
            footer_y = y_rules[-1] if y_rules and y_rules[-1] > page.rect.height * .85 else None
            footers = [box for text in ("Osdag | FOSSEE | Indian Institute of Technology Bombay",
                                       "Page ") for box in page.search_for(text)
                       if footer_y and box.y0 > footer_y]
            for box in footers:
                if box.width < 50:
                    box.x1 = page.rect.width - 68
            intrusions = [word[4] for word in words if footer_y and word[3] > footer_y + .75
                          and not any(box.intersects(fitz.Rect(word[:4])) for box in footers)]
            outside = [f"{word[4]} ({word[0]:.1f}–{word[2]:.1f})" for word in words
                       if 65 < word[1] < (footer_y or page.rect.height - 60)
                       and (word[0] < 69 or word[2] > page.rect.width - 69)]
            if index == 0:
                outside = []  # title page uses decorative offsets
            found = [f"{marker} ×{page_text.count(marker)}" for marker in markers if marker in page_text]
            lines.append(f"| {index + 1} | {len(page.get_image_info())} | "
                         f"{', '.join(intrusions) or '—'} | {', '.join(outside[:8]) or '—'} | "
                         f"{', '.join(found) or '—'} |")
            pix = page.get_pixmap(matrix=fitz.Matrix(0.65, 0.65), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            x = index % 3 * 400 + 6
            y = index % 9 // 3 * 589 + 22
            draw.text((x, y - 17), f"Physical PDF page {index + 1}", fill="black")
            sheet.paste(image, (x, y))
            if index % 9 == 8 or index == len(pdf) - 1:
                sheet.save(args.output / f"pages-{index // 9 * 9 + 1:02d}-{index + 1:02d}.png")
            if found or intrusions or outside:
                if any(marker != "1670" and marker in page_text for marker in markers) or intrusions or outside:
                    page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False).save(
                        args.output / f"detail-{index + 1:02d}.png"
                    )
    (args.output / "page-geometry.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
