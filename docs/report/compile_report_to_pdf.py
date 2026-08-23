#!/usr/bin/env python3
"""
Report Compiler for OsdagBridge Task 3 Technical Report
Compiles docs/report/OsdagBridge_Task3_Report.md to HTML and PDF.
"""

import os
import sys
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "OsdagBridge_Task3_Report.md"
HTML_PATH = BASE_DIR / "OsdagBridge_Task3_Report.html"
PDF_PATH = BASE_DIR / "OsdagBridge_Task3_Report.pdf"


def markdown_to_html(md_content: str) -> str:
    """Simple, robust markdown to HTML converter with styling."""
    try:
        import markdown
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "codehilite", "toc"]
        )
    except ImportError:
        # Fallback simple converter for basic elements
        lines = md_content.split("\n")
        html_lines = []
        in_code = False
        in_table = False
        
        for line in lines:
            if line.startswith("```"):
                if in_code:
                    html_lines.append("</code></pre>")
                    in_code = False
                else:
                    lang = line[3:].strip()
                    html_lines.append(f"<pre><code class=\"language-{lang}\">")
                    in_code = True
                continue
            if in_code:
                html_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
                continue
            
            # Headings
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("#### "):
                html_lines.append(f"<h4>{line[5:]}</h4>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("|") and line.endswith("|"):
                if "---" in line:
                    continue
                cells = [c.strip() for c in line.split("|")[1:-1]]
                row_html = "".join(f"<td>{c}</td>" for c in cells)
                html_lines.append(f"<tr>{row_html}</tr>")
            elif line.strip() == "---":
                html_lines.append("<hr/>")
            elif line.strip():
                # bold and italic
                l = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
                l = re.sub(r"`(.*?)`", r"<code>\1</code>", l)
                html_lines.append(f"<p>{l}</p>")
            else:
                html_lines.append("<br/>")
                
        html_body = "\n".join(html_lines)

    # Wrap in modern, professional printable CSS
    styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>OsdagBridge Task 3 Technical Report</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #24292e;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    padding: 30px;
    background: #ffffff;
  }}
  h1 {{
    color: #1a1a1a;
    font-size: 26px;
    border-bottom: 2px solid #90AF13;
    padding-bottom: 8px;
    margin-top: 20px;
  }}
  h2 {{
    color: #2e7d32;
    font-size: 20px;
    border-bottom: 1px solid #e1e4e8;
    padding-bottom: 6px;
    margin-top: 28px;
  }}
  h3 {{
    color: #333333;
    font-size: 16px;
    margin-top: 20px;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 18px 0;
    font-size: 13px;
  }}
  th, td {{
    border: 1px solid #dfe2e5;
    padding: 8px 12px;
    text-align: left;
  }}
  th {{
    background-color: #f6f8fa;
    font-weight: 600;
  }}
  tr:nth-child(2n) {{
    background-color: #fcfcfc;
  }}
  code {{
    background-color: rgba(27,31,35,0.05);
    padding: 2px 5px;
    border-radius: 3px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 88%;
  }}
  pre {{
    background-color: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 14px;
    overflow: auto;
    font-size: 12px;
    line-height: 1.45;
  }}
  pre code {{
    background: transparent;
    padding: 0;
  }}
  blockquote {{
    margin: 0;
    padding: 0 15px;
    color: #6a737d;
    border-left: 4px solid #90AF13;
  }}
  hr {{
    border: 0;
    height: 1px;
    background: #e1e4e8;
    margin: 24px 0;
  }}
  li {{
    margin-bottom: 4px;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    return styled_html


def export_pdf_with_pyside(html_content: str, output_pdf_path: Path):
    """Export HTML to PDF using PySide6's QTextDocument."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
        from PySide6.QtCore import QMarginsF
        
        app = QApplication.instance() or QApplication(sys.argv[:1])
        doc = QTextDocument()
        doc.setHtml(html_content)
        
        from PySide6.QtGui import QPdfWriter
        writer = QPdfWriter(str(output_pdf_path))
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
        
        doc.print_(writer)
        print(f"✅ Generated PDF report via PySide6 QPdfWriter at: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"⚠️ PySide6 PDF generation notice: {e}")
        return False


def main():
    if not MD_PATH.exists():
        print(f"❌ Error: Markdown file not found at {MD_PATH}")
        sys.exit(1)
        
    md_content = MD_PATH.read_text(encoding="utf-8")
    html_content = markdown_to_html(md_content)
    
    # Save HTML
    HTML_PATH.write_text(html_content, encoding="utf-8")
    print(f"✅ Generated HTML report at: {HTML_PATH}")
    
    # Generate PDF
    export_pdf_with_pyside(html_content, PDF_PATH)


if __name__ == "__main__":
    main()
