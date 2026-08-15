# Technical Changes Document

**Project:** OsdagBridge Report Generator Refactoring  
**Module:** `src/osdagbridge/core/reports/`  

---

## 1. Architectural Changes & Refactoring Summary

The original report generator built PDF design reports via PyLaTeX, but had a few structural and formatting issues: hardcoded table styles were scattered across individual chapter scripts, multi-page tables overflowed into page footers without repeating headers, live loads were merged together, and summary charts were missing.

To fix these issues cleanly, the report generator code was refactored into a more modular structure:

1. **Centralized Style Configuration (`styles.py`)**:  
   Created a single style configuration module to act as the single source of truth for all layout parameters. It holds page geometry settings (`DOCUMENT_GEOMETRY`), brand and alert colors (`COLOR_PALETTE`), table spacing (`TABLE_CONFIG`), running headers/footers (`fancyhdr`), and global Matplotlib styling (`apply_matplotlib_style()`).

2. **Page Break & Table Header Handling (`make_longtable_header`)**:  
   Replaced basic `table` and standard LaTeX table wrappers across Chapters 1–9 with PyLaTeX `longtable` blocks. The `make_longtable_header()` helper automatically inserts `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot` directives so that column headers repeat at the top of every new page.

3. **Footer Overlap Protection**:  
   Added `\needspace{4\baselineskip}` before table headers and set `\raggedbottom` to prevent table rows (such as girder check rows on page 30) from creeping down into footer margins.

4. **Dynamic Plot Generation (`report_plots.py`)**:  
   Added a plotting module using Matplotlib's non-interactive `Agg` backend to generate chart images during report build:
   - **Section 5.5 (Overall Utilization Ratio Summary)**: Bar chart comparing demand/capacity ratios across girders, deck slab, cross bracing, and end diaphragms, featuring a red dashed horizontal threshold line at `UR = 1.0`.
   - **Chapter 7 (Material Take-off)**: Dual bar charts displaying structural steel tonnage breakdown and concrete volume vs. rebar weight.

5. **Pass/Fail UR Cell Color Highlighting (`colorize_ur_cell`)**:  
   Created a helper function to dynamically format and highlight UR cells in LaTeX tables—green (`#2E7D32`) for $\text{UR} \le 1.0$ and red (`#C62828`) for $\text{UR} > 1.0$.

---

## 2. Files Modified

| File | Key Changes |
| :--- | :--- |
| `src/osdagbridge/core/reports/styles.py` | **[NEW]** Central style system containing color definitions, geometry rules, longtable header generator, UR cell colorizer, and Matplotlib theme setup. |
| `src/osdagbridge/core/reports/report_plots.py` | **[NEW]** Generates UR summary chart and Material Take-off bar charts using Matplotlib `Agg` backend, with fallback handling for missing values. |
| `src/osdagbridge/core/reports/report_generator.py` | Imports centralized style preambles, triggers plot generation before PDF compilation, and wires assets into document assembly. |
| `src/osdagbridge/core/reports/chap3.py` | Separated vehicle live loads (**Table 3.3a**) and footpath live loads (**Table 3.3b**) into distinct longtables, pulling vehicle parameters dynamically from UI selection keys. |
| `src/osdagbridge/core/reports/chap5.py` | Embedded Section 5.5 UR summary bar chart (`assets/ur_summary_chart.png`), added `colorize_ur_cell()` highlighting across design tables, and refactored multi-page check tables with longtable headers. |
| `src/osdagbridge/core/reports/chap7.py` | Embedded Chapter 7 material take-off charts (`steel_quantities_chart.png`, `concrete_rebar_chart.png`) and updated Table 7.1 longtable headers. |
| `src/osdagbridge/core/reports/executive_summary.py` & `chap1.py` – `chap9.py` | Updated table construction across all chapters to use `styles.py` helpers and repeated longtable headers. |

---

## 3. Structure of `styles.py`

```python
# Document Geometry & Margins
DOCUMENT_GEOMETRY = {
    'paper': 'a4paper',
    'top': '1.0in', 'bottom': '1.2in', 'left': '1.0in', 'right': '1.0in',
    'headheight': '15pt', 'headsep': '18pt', 'footskip': '35pt',
}

# Color Palette (Brand & Alerts)
COLOR_PALETTE = {
    'osdagGreen': '#91B014',         # Primary Osdag brand color
    'osdagGreenDark': '#6F870F',     # Dark green headings
    'tableHeaderBg': '#EBF2D4',      # Soft green header fill
    'tableAltRow': '#F5F8E8',        # Alternating row background
    'passGreen': '#2E7D32',          # Pass status cell fill
    'failRed': '#C62828',            # Fail status cell fill
    'thresholdRed': '#D32F2F',       # Dashed reference line (UR=1.0)
    'chartSteel': '#2B5C8F',         # Steel tonnage bar
    'chartConcrete': '#4CAF50',      # Concrete volume bar
    'chartRebar': '#FF9800',         # Rebar weight bar
}

# Table Padding & Spacing
TABLE_CONFIG = {
    'arraystretch': 1.15,
    'tabcolsep': '6pt',
    'LTpre': '8pt',
    'LTpost': '12pt',
}
```

---

## 4. Technical Rationale & Decisions

- **Using `\needspace{4\baselineskip}` instead of `\keepwithnext`**: `\keepwithnext` is not a standard TeX command in default TeX Live / pdflatex distributions and causes build errors. Using `\needspace` ensures LaTeX measures remaining vertical space before starting a table block, preventing orphan headers.
- **Native LongTable Captions**: Using native `longtable` caption placement (`\caption{...} \\` with `\endfirsthead`) avoids caption duplication on page breaks without introducing external package conflicts like `\captionof` inside longtables.
- **Forcing `matplotlib.use('Agg')`**: Enforced at the top of `styles.py` and `report_plots.py` before importing `pyplot`. This ensures chart generation works in headless server environments without requiring active GUI display drivers or GUI thread hooks.
- **Relative Asset Paths**: Chart PNGs are saved to `<output_dir>/assets/` and referenced via relative paths (`assets/...`). This makes LaTeX compilation deterministic across operating systems (macOS, Linux, Windows).

---

## 5. Environment & Deliverables

- **LaTeX Package Dependencies**: `lmodern`, `needspace`, `titlesec`, `fancyhdr`, `subcaption`, `xcolor` (with `table` option).
- **Deliverable PDF Reports**:
  - `Report_Before.pdf`: Baseline output generated from original code.
  - `Report_After.pdf`: Refactored output featuring repeated longtable headers, clean footer boundaries, separated live load tables, UR threshold bar chart, material take-off plots, and pass/fail cell highlighting.
