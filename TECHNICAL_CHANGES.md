# OsdagBridge LaTeX Report Generator — Technical Changes Document

**Project:** OsdagBridge Report Generator Refactoring & Enhancements
**Scope covered in this document:** Requirements #1, #2, #3, #4, #5, #6 (complete).

---

## 1. Summary of Changes

| Req # | Description | Status |
|---|---|---|
| 1 | Repeated table headers across page breaks | Complete |
| 2 | Layout / footer overlap / vertical spacing fixes | Complete |
| 3 | Live Load & Footway Load table refactoring | Complete |
| 4 | Utilization Ratio summary bar charts | Complete |
| 5 | Material quantity bar charts | Complete |
| 6 | Centralized formatting & style system | Complete |

---

## 2. Files Changed

- `core/reports/styles.py`
- `core/reports/report_utils.py`
- `core/reports/chap3.py`
- `core/reports/chap5.py`
- `core/reports/chap7.py`
- `core/reports/report_charts.py` (new)
- `core/reports/report_generator.py`

---

## 3. Key Changes by File

*(Note: This section only details the new changes and files modified since the previous reference version.)*

### `report_generator.py` — Report Data Bridge Extension
- Extended the `ReportDataBridge` helper class to include `_vehicle_total_weight_kN()`. This method imports `IRC6_2017` and dynamically calculates the total weight for Class A (543.5 kN), Class 70R Wheeled (981.0 kN), and Class 70R Tracked (686.8 kN), converting force values from Newtons to kN.
- Passed the `bridge` instance as the second argument to `ch3_loads()`.
- **Why:** decapsulates the report generation flow by allowing `chap3.py` to query computed properties from the helper bridge wrapper instead of directly referencing raw analyser imports.

### `chap3.py` — Live Load Table Populate & Placeholder wrapping
- Updated `ch3_loads()` to accept `bridge` and mapped vehicle classes to their respective keys in `_vehicle_weight_map`.
- Programmatically populated the "Total Load (kN)" column of Table 3.3 using `bridge._vehicle_total_weight_kN(weight_key)` for the three supported active vehicle classes: Class A, Class 70R (Wheeled), and Class 70R (Tracked).
- Shortened the placeholder string for the remaining unsupported vehicle classes (Class AA Wheeled/Tracked, Class 70R Bogie, Class SV, Class Fatigue) and user-defined custom vehicles to `N/A \\ not impl.`, wrapped inside a `\makecell{...}` block.
- **Why:** The previous long placeholder text "Not computed — axle configuration not yet implemented" visually overflowed the narrow `2.0cm` table column and overlapped adjacent columns. The shortened `N/A \\ not impl.` wraps and fits perfectly within the column borders.

---

## 4. Verification Method

All fixes were verified by:
1. Running the full OsdagBridge design and analysis pipeline against a saved input file end-to-end (not mocked), producing a real generated `.tex`/`.pdf`.
2. Compiling with `pdflatex` and confirming zero `!` errors in the log.
3. Rendering the compiled PDF's individual pages as images and visually inspecting the specific tables and pages that were previously broken.
4. **Specific verification for the live loads table:** Rendered page 15 (PDF Page 15) and visually confirmed that Table 3.3 displays the correct kN values ($543.5\text{ kN}$, $981.0\text{ kN}$, $686.8\text{ kN}$) for the active vehicles, and the shortened placeholder `N/A \\ not impl.` wraps and centers perfectly without any column overlap.

---

## 5. Rationale for Architectural Choices

- **Decoupled data extraction via ReportDataBridge**: Adding vehicle total weight calculations to `ReportDataBridge` keeps the chapter modules clean, focused solely on LaTeX document structure formatting, and decoupled from direct code-basis dependencies.
- **Strict layout containment in narrow columns**: Using `\makecell` with manual linebreaks to handle text placeholders inside narrow table columns ensures that long strings wrap predictably instead of overflowing and overlapping adjacent cells.

---

## 6. Open Items (Not Yet Resolved)

### Core Analysis Gap — Tier 2 Axle Configurations
Class AA (Wheeled/Tracked), Class 70R (Bogie), Class SV, and Class Fatigue have no axle configuration implemented anywhere in the core codebase (`irc6_2017.py`). Implementing these axle layouts is a core analyser design task and is out of scope for the report generator. The report correctly shows the honest `N/A \\ not impl.` placeholder until they are wired into the core.

### Chapter 7 — End Diaphragm steel not itemized
The material quantity bar chart in Chapter 7 omits End Diaphragm steel tonnage because it is not itemized as a separate line in the Bill of Materials (Table 7.1). If End Diaphragm steel should be tracked separately, the BOM generation logic (not the report generator) needs to be updated first.

---

## 7. Deliverables Status

| Deliverable | Status |
|---|---|
| GitHub repository link with collaborator added | Pending |
| `Report_Before.pdf` | Pending |
| `Report_After.pdf` | Available — verification PDF from this cycle serves as this |
| Technical Changes Document | This document (`TECHNICAL_CHANGES.md`) |
| Visual/typographical polish beyond the listed scope | Complete |
