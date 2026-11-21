# Report generation deliverables

| File | Description |
|------|-------------|
| `Report_Before.pdf` | Baseline output produced from the unmodified `dev` branch. |
| `Report_After.pdf` | Enhanced output after the refactoring described in `docs/REPORT_ENHANCEMENTS.md`. |
| `Report_Before.tex`, `Report_After.tex` | Corresponding LaTeX sources (useful for diffing header repetition). |

Both PDFs were generated from the **same representative payload** with
`scripts/generate_sample_reports.py`; no GUI or OpenSees analysis is required.

Quick checks on the enhanced report:

```bash
grep -c '\\endhead' deliverables/Report_After.tex   # 50 (baseline: 2)
grep -n 'fig:ur-summary|fig:material-quantities' deliverables/Report_After.tex
```
