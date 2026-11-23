#!/usr/bin/env python3
"""
Test Execution Summary Generator
================================

Parses `04_test_execution/execution_summary.csv` and
`02_test_cases/test_case_register.csv` to generate progress metrics,
pass/fail percentages, and an executive Markdown status report.

Usage:
    python generate_test_summary.py
    python generate_test_summary.py --output ../04_test_execution/test_report.md
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_csv(filepath: Path) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of row dictionaries."""
    if not filepath.exists():
        print(f"[WARN] File not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def analyze_test_metrics(exec_rows: List[Dict[str, str]], reg_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """Compute test progress and outcome statistics."""
    total_defined = len(reg_rows)
    total_executions = len(exec_rows)

    status_counts = {
        "Pass": 0,
        "Fail": 0,
        "Blocked": 0,
        "Pending Execution": 0,
        "Pending": 0,
        "Other": 0,
    }

    for row in exec_rows:
        status = row.get("Status", "").strip()
        if status in status_counts:
            status_counts[status] += 1
        elif not status:
            status_counts["Pending Execution"] += 1
        else:
            status_counts["Other"] += 1

    executed = status_counts["Pass"] + status_counts["Fail"] + status_counts["Blocked"]
    pending = total_executions - executed

    pass_rate = (status_counts["Pass"] / executed * 100.0) if executed > 0 else 0.0

    return {
        "total_defined": total_defined,
        "total_executions": total_executions,
        "executed": executed,
        "pending": pending,
        "pass_count": status_counts["Pass"],
        "fail_count": status_counts["Fail"],
        "blocked_count": status_counts["Blocked"],
        "pass_rate": pass_rate,
    }


def generate_markdown_report(metrics: Dict[str, Any], output_path: Path = None) -> str:
    """Generate Markdown formatted summary report."""
    md = f"""# Test Execution Summary Report

**Generated from**: `04_test_execution/execution_summary.csv`  
**Total Defined Test Cases**: {metrics['total_defined']}  
**Total Execution Runs Logged**: {metrics['total_executions']}

---

## 1. Executive Metrics

| Metric | Count | Percentage |
| :--- | :---: | :---: |
| **Total Test Runs** | {metrics['total_executions']} | 100.0% |
| **Completed Runs** | {metrics['executed']} | {(metrics['executed'] / metrics['total_executions'] * 100) if metrics['total_executions'] else 0.0:.1f}% |
| **Pending Runs** | {metrics['pending']} | {(metrics['pending'] / metrics['total_executions'] * 100) if metrics['total_executions'] else 0.0:.1f}% |
| **Passed** | {metrics['pass_count']} | {(metrics['pass_count'] / metrics['total_executions'] * 100) if metrics['total_executions'] else 0.0:.1f}% |
| **Failed** | {metrics['fail_count']} | {(metrics['fail_count'] / metrics['total_executions'] * 100) if metrics['total_executions'] else 0.0:.1f}% |
| **Blocked** | {metrics['blocked_count']} | {(metrics['blocked_count'] / metrics['total_executions'] * 100) if metrics['total_executions'] else 0.0:.1f}% |
| **Pass Rate (of executed)** | — | **{metrics['pass_rate']:.1f}%** |

---

## 2. Multi-Run Testing Observations
Multi-run tests verify sequential execution determinism across Run 1, Run 2, and Run 3 cycles.

*(Detailed test execution notes and observations will populate here as actual runs are executed).*
"""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[INFO] Report written to: {output_path}")

    return md


def main():
    script_dir = Path(__file__).resolve().parent
    workspace_dir = script_dir.parent

    exec_csv = workspace_dir / "04_test_execution" / "execution_summary.csv"
    reg_csv = workspace_dir / "02_test_cases" / "test_case_register.csv"

    parser = argparse.ArgumentParser(description="Generate testing metrics summary")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output markdown path")
    args = parser.parse_args()

    exec_rows = parse_csv(exec_csv)
    reg_rows = parse_csv(reg_csv)

    metrics = analyze_test_metrics(exec_rows, reg_rows)

    print("\n==============================================")
    print("OsdagBridge Testing Metric Summary")
    print("==============================================")
    print(f"Total Test Cases Defined   : {metrics['total_defined']}")
    print(f"Total Test Execution Rows  : {metrics['total_executions']}")
    print(f"Executed Runs              : {metrics['executed']}")
    print(f"Pending Runs               : {metrics['pending']}")
    print(f"Pass Count                 : {metrics['pass_count']}")
    print(f"Fail Count                 : {metrics['fail_count']}")
    print(f"Blocked Count              : {metrics['blocked_count']}")
    print(f"Pass Rate                  : {metrics['pass_rate']:.1f}%")
    print("==============================================\n")

    report_md = generate_markdown_report(metrics, args.output)


if __name__ == "__main__":
    main()
