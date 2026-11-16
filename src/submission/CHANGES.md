# OsdagBridge Report Generator: Changes

Baseline commit: `460af74`
Deliverables: `Report_Before.pdf` (original code), `Report_After.pdf` (this branch)
Both reports were generated from the same `inputs.osi`.

## 1. Summary

The LaTeX report generator was refactored so that long tables repeat their
header row on every page, no table ends with a lone header bar or an orphaned
row, and tables stay inside the text margin. Several tables that were wrong or
missing in the original report were also corrected.

## 2. Changes made

### Layout and pagination
| Area | Change | Where |
|---|---|---|
| Long tables | Added `make_longtable()` so the header repeats on every page and the closing rule is kept with the last row (`\endlastfoot`), which removes the lone header bar at the bottom or top of a page. | `report_utils.py` |
| Legacy raw tables | `add_repeating_headers()` now fixes raw longtables as well: `_add_header()` adds the repeating header, and `_pin_closing_rule()` moves the final `\hline` into `\endlastfoot`. | `report_utils.py` |
| Capacity tables (5.25, 5.28) | Removed the trailing `\cline{2-8}` after the last row of each panel pair. Row pairs are kept together (`\\*`). `\Needspace{12\baselineskip}` keeps each small table from splitting across pages. Column widths were narrowed so both tables fit the margin. | `chap5.py`, `styles.py` (`needspace` package) |
| Footnote | The "* Software default value" footnote is now on the same page as its asterisk (Table 3.2, page 13). | |
| Table 2.7 | Dimensions are now shown in mm (1120 mm, 8 mm, 340 mm / 16 mm). | |
| Table 2.8 | Restraint and stiffener table is ragged-aligned and fits the page. | |

### Content
| Area | Change | Where |
|---|---|---|
| Table 3.1 | Dead Load: Self Weight table restored. It had been overwritten by a duplicate Load Combinations table during the longtable conversion. Load Combinations now appears once (Table 3.8). | `chap3.py` |
| Table 3.3 | Live loads now list per-vehicle impact factors (IRC 6 Cl. 208). Braking load is moved to a note below the table. | `chap3.py` |
| Table 3.4 | Footpath live load now reads "No footpath provided" when no footpath is selected, and shows the IRC 6 default otherwise. | `chap3.py` |

## 3. Verified in Report_After.pdf

- Cover page, page headers and Section 1.1 are filled in from the project details.
- Table 4.2 is filled in.
- Executive Summary shows Girder FAIL (Fatigue Normal Stress).
- Figure 5.1 shows the fatigue bar at 1.45 in red, and Figure 7.1 adds up to 84.9 MT.
- No lone header bar or orphaned row: Tables 5.25, 5.28 and 5.29 break cleanly.
- Tables 5.25 and 5.28 are inside the right margin.
- Page count: Before 53 PDF pages, After 56 PDF pages.

## 4. Observed, not changed

These come from upstream data or backend values, not from the report layout code.

1. Executive Summary says "End Diaphragm design: not evaluated", but Section 5.4
   shows full PASS tables. The values are identical to the cross-bracing tables.
2. Table 5.29 shows load combination names with visible underscores
   (`ACCIDENTAL_1`, `SLS_RARE_1`, `SLS_FREQUENT_1`).
3. Table 5.29 note says "All values <= 1.0 indicate passing checks", but the fatigue row is 1.45.
4. Table 5.29 gives girder deflection a UR of 0.43 (14.40 mm), while Tables 4.3 and 5.9
   report total-load deflection FAIL (39.9 mm against 33.3 mm).
5. Cells still blank: wind Vz, Pz and forces (Table 3.5), seismic forces (Table 3.6),
   No. of Traffic Lanes (Table 2.4), intermediate stiffener spacing (Table 5.7).
   End-panel stiffener thickness of 0.9 mm in Table 5.7 looks wrong.
6. Tables 2.6 and 2.7 stick out slightly past the right margin.
7. The footer says "Page N of 55", but the PDF has 56 pages. The cover and the
   table of contents are both counted as page 1.