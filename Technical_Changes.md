\# Technical Changes – OsdagBridge Report Generator



\*\*Date:\*\* 21 November 2026



\## 1. Project Overview

The OsdagBridge report generator was enhanced to improve LaTeX report formatting, table presentation, and data visualization.



\## 2. Changes Implemented



\### A. Centralized Styling

\*\*New file:\*\* `reports/styles.py`



\- Added centralized LaTeX preamble and styling.

\- Centralized page geometry, colors, captions, table spacing, and headers/footers.

\- Integrated the style module with `report\_generator.py`.



Some chapter-specific table formatting still remains local.



\### B. Repeated Table Headers

Updated longtable formatting:



\- Chapter 2: 9 tables updated.

\- Chapter 3: 8 tables updated.

\- Chapter 4: 3 of 4 tables updated.

\- Chapter 5: 28 of 30 identified tables updated.



Some header and caption ordering issues remain and require visual refinement.



\### C. Chapter 3 – Live Load Tables

\*\*File:\*\* `reports/chap3.py`



\- Separated vehicle live loads and footway live loads.

\- Added vehicle classes and impact factors.

\- Added braking-load and eccentricity fields.

\- Added centrifugal-force information where available.



Braking force displays N/A because of an existing calculation issue. Centrifugal-force data is unavailable in the current report calculation output.



\### D. Utilization-Ratio Charts

\*\*File:\*\* `reports/ur\_charts.py`



Implemented four charts:

1\. Steel Plate Girder

2\. Concrete Deck Slab

3\. Cross Bracing

4\. End Diaphragm



Charts are embedded in Chapter 5. A red dashed UR = 1 reference line is included.



\### E. Chapter 7 – Quantity Charts

\*\*New file:\*\* `reports/quantity\_charts.py`



Implemented two charts:

\- Steel tonnage distribution.

\- Concrete volume and reinforcement steel weight comparison.



End diaphragm quantity data was unavailable in the current BOQ output and was not invented.



\## 3. Main Files Changed



\- `reports/styles.py` – centralized styling.

\- `reports/quantity\_charts.py` – quantity charts.

\- `reports/ur\_charts.py` – utilization-ratio charts.

\- `reports/report\_generator.py` – chart and style integration.

\- `reports/chap2.py` – repeated headers.

\- `reports/chap3.py` – live-load tables and repeated headers.

\- `reports/chap4.py` – partial repeated headers.

\- `reports/chap5.py` – repeated headers and UR charts.

\- `reports/chap7.py` – quantity chart integration.



\## 4. Testing



\- Python syntax checks passed for the modified report modules.

\- Centralized preamble check passed.

\- Chart PNG generation and validation passed.

\- Report PDFs were generated successfully.

\- PDF opening and page-count verification passed.

\- Important table and chart captions were checked using PDF text extraction.



\## 5. Before and After PDF Comparison



| Detail | Before | After |

|---|---:|---:|

| Filename | Report\_Before.pdf | Report\_After.pdf |

| Pages | 62 | 59 |

| File size | 422,908 bytes | 718,758 bytes |

| PDF validation | Passed | Passed |



The Before PDF was generated from the 7 November report-code backup. The After PDF represents the latest tested report version.



\## 6. Pending Improvements



\- Refine repeated-header and caption ordering in some Chapter 3 and Chapter 5 tables.

\- Add repeated-header formatting to the remaining Chapter 4 table.

\- Correct the existing braking-force calculation issue.

\- Provide centrifugal-force calculation data.

\- Provide end diaphragm quantity data in the BOQ output.

\- Complete visual review of footer spacing and page breaks.

\- Verify GitHub commit, push, and collaborator access.



Cross Bracing and End Diaphragm design checks currently show NOT CHECKED in the tested report. These are engineering verification statuses, not formatting errors.



\## 7. Conclusion



The report generator now includes centralized styling, separated live-load tables, four utilization-ratio charts, and two quantity charts. Repeated-header support has been added to most identified longtables.



Both Before and After PDFs were generated and validated. Some visual refinements and engineering-data limitations remain outstanding.

