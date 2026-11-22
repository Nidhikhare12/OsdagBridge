#!/usr/bin/env python3
"""
Dictionary Comparison Utility for OsdagBridge Testing
=====================================================

This script compares two OsdagBridge dictionaries (e.g., input dictionaries,
output dictionaries, or serialized .osi / .json project dumps) to verify state
isolation, run-to-run determinism, and data integrity.

Supports:
- Recursive dictionary traversal.
- Configurable floating-point tolerance (absolute & relative).
- Identification of missing, unexpected, and mismatched keys.
- Formatted console output and JSON diff reporting.

Usage:
    python compare_dictionaries.py --file1 run1.json --file2 run2.json
    python compare_dictionaries.py --file1 state_run1.osi --file2 state_run3.osi --tolerance 1e-5
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def is_close(val1: Any, val2: Any, rel_tol: float = 1e-6, abs_tol: float = 1e-6) -> bool:
    """Compare two numbers with a numerical tolerance."""
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        return math.isclose(float(val1), float(val2), rel_tol=rel_tol, abs_tol=abs_tol)
    return False


def deep_compare_dicts(
    d1: Dict[str, Any],
    d2: Dict[str, Any],
    path: str = "",
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-6,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Recursively compare two dictionaries.
    
    Returns:
        (missing_in_d2, extra_in_d2, value_mismatches)
    """
    missing_in_d2 = []
    extra_in_d2 = []
    value_mismatches = []

    keys1 = set(d1.keys())
    keys2 = set(d2.keys())

    # Keys in d1 but missing in d2
    for k in keys1 - keys2:
        missing_in_d2.append(f"{path}.{k}" if path else str(k))

    # Keys in d2 but unexpected in d1
    for k in keys2 - keys1:
        extra_in_d2.append(f"{path}.{k}" if path else str(k))

    # Common keys comparison
    for k in keys1 & keys2:
        current_path = f"{path}.{k}" if path else str(k)
        v1 = d1[k]
        v2 = d2[k]

        if isinstance(v1, dict) and isinstance(v2, dict):
            sub_missing, sub_extra, sub_mismatch = deep_compare_dicts(
                v1, v2, path=current_path, rel_tol=rel_tol, abs_tol=abs_tol
            )
            missing_in_d2.extend(sub_missing)
            extra_in_d2.extend(sub_extra)
            value_mismatches.extend(sub_mismatch)
        elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            if not is_close(v1, v2, rel_tol=rel_tol, abs_tol=abs_tol):
                diff = abs(float(v1) - float(v2))
                value_mismatches.append(
                    f"{current_path}: {v1} != {v2} (diff: {diff:.6e})"
                )
        elif isinstance(v1, list) and isinstance(v2, list):
            if len(v1) != len(v2):
                value_mismatches.append(
                    f"{current_path}: length mismatch (len1={len(v1)}, len2={len(v2)})"
                )
            else:
                for idx, (elem1, elem2) in enumerate(zip(v1, v2)):
                    elem_path = f"{current_path}[{idx}]"
                    if isinstance(elem1, (int, float)) and isinstance(elem2, (int, float)):
                        if not is_close(elem1, elem2, rel_tol=rel_tol, abs_tol=abs_tol):
                            value_mismatches.append(
                                f"{elem_path}: {elem1} != {elem2}"
                            )
                    elif elem1 != elem2:
                        value_mismatches.append(
                            f"{elem_path}: {elem1!r} != {elem2!r}"
                        )
        else:
            if v1 != v2:
                value_mismatches.append(
                    f"{current_path}: {v1!r} != {v2!r}"
                )

    return missing_in_d2, extra_in_d2, value_mismatches


def load_dictionary_file(filepath: Path) -> Dict[str, Any]:
    """Load dictionary from a JSON or OSI file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Root object in {filepath.name} must be a dictionary, got {type(data)}")
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Compare two OsdagBridge dictionary dumps (.json or .osi)"
    )
    parser.add_argument("--file1", "-f1", required=True, type=Path, help="Path to reference dictionary file")
    parser.add_argument("--file2", "-f2", required=True, type=Path, help="Path to target dictionary file to compare")
    parser.add_argument(
        "--tolerance", "-t", type=float, default=1e-6, help="Floating point absolute tolerance (default: 1e-6)"
    )
    parser.add_argument(
        "--output-json", "-o", type=Path, default=None, help="Optional path to output comparison results as JSON"
    )

    args = parser.parse_args()

    try:
        dict1 = load_dictionary_file(args.file1)
        dict2 = load_dictionary_file(args.file2)
    except Exception as e:
        print(f"[ERROR] Failed to load input file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"==================================================")
    print(f"OsdagBridge Dictionary Comparison")
    print(f"File 1 (Reference): {args.file1}")
    print(f"File 2 (Target)   : {args.file2}")
    print(f"Numerical Abs Tol : {args.tolerance}")
    print(f"==================================================")

    missing, extra, mismatches = deep_compare_dicts(
        dict1, dict2, abs_tol=args.tolerance, rel_tol=args.tolerance
    )

    total_diffs = len(missing) + len(extra) + len(mismatches)

    if total_diffs == 0:
        print("\n[RESULT: PASS] Dictionaries are IDENTICAL within specified tolerance.")
        result_code = 0
    else:
        print(f"\n[RESULT: FAIL] Found {total_diffs} difference(s):")
        if missing:
            print(f"\n--- Keys Missing in File 2 ({len(missing)}) ---")
            for k in missing:
                print(f"  [-] {k}")
        if extra:
            print(f"\n--- Extra Keys in File 2 ({len(extra)}) ---")
            for k in extra:
                print(f"  [+] {k}")
        if mismatches:
            print(f"\n--- Value Mismatches ({len(mismatches)}) ---")
            for m in mismatches:
                print(f"  [~] {m}")
        result_code = 1

    if args.output_json:
        report = {
            "file1": str(args.file1),
            "file2": str(args.file2),
            "identical": total_diffs == 0,
            "total_differences": total_diffs,
            "missing_keys": missing,
            "extra_keys": extra,
            "value_mismatches": mismatches,
        }
        with open(args.output_json, "w", encoding="utf-8") as out_f:
            json.dump(report, out_f, indent=2)
        print(f"\nDiff report saved to: {args.output_json}")

    sys.exit(result_code)


if __name__ == "__main__":
    main()
