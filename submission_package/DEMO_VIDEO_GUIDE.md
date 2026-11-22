# Silent Screen Recording & Screenshot Walkthrough Guide

**Mode:** Silent Screen Recording / Screenshot Evidence  
**Topic:** OsdagBridge – LaTeX Report Generator: Table Formatting Corrections and Regression Testing  
**Pull Request:** [#196 on Nidhikhare12/OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge/pull/196)  
**Author:** Aryan Vyas ([@Aaryanvyas](https://github.com/Aaryanvyas))  

---

## 📸 Step-by-Step Visual Storyboard

This guide is designed for **silent recording** (using OBS, Windows Game Bar `Win + G`, Loom, or Clipchamp) or for capturing **numbered screenshots** to attach directly to your submission.

---

### Step 1: GitHub Pull Request #196 Overview
- **What to display on screen:**
  - Browser tab open to: `https://github.com/Nidhikhare12/OsdagBridge/pull/196`
- **Key visual focus:**
  - PR Title: `Fix report table column alignment and LaTeX formatting`
  - Author: `Aaryanvyas`
  - Target: `Nidhikhare12:dev` from `Aaryanvyas:dev`
  - PR description and commit history (`64b8dd2`).
- **Screenshot Caption:**
  > *Screenshot 1: Submitted Pull Request #196 on Nidhikhare12/OsdagBridge.*

---

### Step 2: Code Diff in `chap2.py`
- **What to display on screen:**
  - Open `src/osdagbridge/core/reports/chap2.py` in VS Code (or show the "Files changed" tab on GitHub PR #196).
- **Key visual focus:**
  1. **Cross-Bracing Table:** Show the fix from 6 defined columns (`|L|L|L|L|C|C|`) down to 5 columns (`|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{4.0cm}|C{2.0cm}|`), matching the 5 data values.
  2. **End-Diaphragm Table:** Show the fix from 6 defined columns down to 4 columns (`|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{6.0cm}|`), matching the 4 data values.
  3. **Caption line breaks:** Show the trailing `\\` added after `\caption{\textbf{...}}\\` across Chapter 2 tables.
- **Screenshot Caption:**
  > *Screenshot 2: Code diff in chap2.py correcting table column specifications and caption line terminators.*

---

### Step 3: Automated Regression Test Code (`test_report_tables.py`)
- **What to display on screen:**
  - Open `tests/unit/test_report_tables.py` in VS Code.
- **Key visual focus:**
  - Highlight the test logic:
    - Regex pattern extracting `\begin{longtable}` blocks.
    - Automated extraction of column definitions (`[LCR]\{[\d.]+cm\}`).
    - Dynamic row iteration checking `assert row.count("&") + 1 == expected`.
- **Screenshot Caption:**
  > *Screenshot 3: Automated regression test enforcing column-to-cell count consistency.*

---

### Step 4: Live Test Execution in Terminal
- **What to display on screen:**
  - Integrated terminal in VS Code (or standalone PowerShell).
- **Command to run:**
  ```powershell
  $env:PYTHONPATH="src"
  pytest -v tests/unit/test_report_tables.py
  ```
- **Key visual focus:**
  - The green test result line:
    ```text
    tests/unit/test_report_tables.py::test_bracing_tables_have_matching_column_counts PASSED [100%]
    ============================== 1 passed in 0.07s ==============================
    ```
- **Screenshot Caption:**
  > *Screenshot 4: Clean execution and 100% pass of unit test in pytest.*

---

### Step 5: Before vs. After LaTeX Structure Comparison
- **What to display on screen:**
  - Split editor showing `latex_evidence/table_before.tex` on the left and `latex_evidence/table_after.tex` on the right.
- **Key visual focus:**
  - Left (Before): Highlight the mismatch (6 column specs for 5 and 4 data cells, missing `\\`).
  - Right (After): Highlight the corrected specification (5 and 4 columns, `\\` present).
- **Screenshot Caption:**
  > *Screenshot 5: Side-by-side comparison of original table syntax error vs. enhanced LaTeX structure.*

---

### Step 6: Git Log & Clean Working Tree
- **What to display on screen:**
  - Terminal executing:
    ```bash
    git status
    git log -n 1 --stat
    ```
- **Key visual focus:**
  - Commit `64b8dd2`: `Fix report table column alignment and LaTeX formatting`
  - Showing files changed: `chap2.py` and `tests/unit/test_report_tables.py`.
- **Screenshot Caption:**
  > *Screenshot 6: Git status and commit history confirming repository state.*

---

## 💡 Quick Tips for Silent Recording
- **Resolution:** Set screen to 1080p (1920x1080).
- **Font Size:** Zoom in slightly (`Ctrl + +` in VS Code and browser) so code and terminal text are crisp and easy to read.
- **Pacing:** Pause for 4–5 seconds on each screen so viewers can read the code changes and test outputs without pausing.
- **Total Duration:** 60 to 90 seconds is ideal for a silent walkthrough.
