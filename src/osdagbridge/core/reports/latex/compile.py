"""LaTeX compilation engine, rerun detection, and log diagnostics (Requirement P4-3)."""

from __future__ import annotations
import os
import re
from pathlib import Path
import subprocess
import logging
from dataclasses import dataclass, field
from typing import Tuple, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class CompileReport:
    """Diagnostic report extracted from LaTeX engine compilation log."""
    success: bool
    passes: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_packages: List[str] = field(default_factory=list)
    log_path: str | None = None


def find_compiler() -> Tuple[str, Dict[str, str]]:
    """Discover the pdflatex executable path and configured environment."""
    compiler = "pdflatex"
    env = os.environ.copy()

    try:
        import importlib
        module = importlib.import_module("osdag_latex_env.__main__")
        latex_env = getattr(module, "OsdagLatexEnv")()
        if latex_env.pdflatex:
            compiler = str(latex_env.pdflatex)
            if latex_env.bin_dir:
                env["PATH"] = str(latex_env.bin_dir) + os.pathsep + env.get("PATH", "")
    except Exception as exc:
        logger.debug("osdag_latex_env discovery not available: %s", exc)

    return compiler, env


def get_compiler_cmd() -> Tuple[str, Dict[str, str]]:
    """Backward-compatible alias for find_compiler."""
    return find_compiler()


def parse_log(log_text: str) -> CompileReport:
    """Parse pdflatex log output for errors, overfull/underfull warnings, and missing packages."""
    errors = []
    warnings = []
    missing_pkgs = []

    lines = log_text.splitlines()
    for idx, line in enumerate(lines):
        clean = line.strip()
        # LaTeX error: starts with "! "
        if clean.startswith("!"):
            # Capture error message and context line if present
            err_msg = clean[2:].strip()
            if idx + 1 < len(lines) and lines[idx + 1].strip().startswith("l."):
                err_msg += f" ({lines[idx + 1].strip()})"
            errors.append(err_msg)

        # Missing packages or file not found
        if "LaTeX Error: File `" in clean and "' not found" in clean:
            match = re.search(r"File `([^']+)' not found", clean)
            if match:
                missing_pkgs.append(match.group(1))

        # LaTeX Warnings (e.g. Overfull \vbox, undefined references)
        if "Warning:" in clean or "Overfull \\" in clean:
            warnings.append(clean)

    success = len(errors) == 0
    return CompileReport(
        success=success,
        passes=1,
        errors=errors,
        warnings=warnings,
        missing_packages=missing_pkgs,
    )


def run_latex(tex_path: str | Path, max_passes: int = 4) -> CompileReport:
    """Compile LaTeX document with automatic rerun detection for longtable and references."""
    path = Path(tex_path).resolve()
    cwd = str(path.parent)
    stem = path.stem
    compiler, env = find_compiler()

    kwargs = {
        "cwd": cwd,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "check": False,
        "env": env,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    passes_run = 0
    log_content = ""
    log_file = path.with_suffix(".log")
    pdf_file = path.with_suffix(".pdf")

    # Stale output from an earlier run must not be mistaken for a fresh PDF.
    if pdf_file.is_file():
        try:
            pdf_file.unlink()
        except OSError:
            pass

    # Always run at least two passes (contents page, page total) when allowed.
    min_passes = min(2, max_passes)

    for pass_idx in range(1, max_passes + 1):
        passes_run = pass_idx
        res = subprocess.run([compiler, "-interaction=nonstopmode", f"{stem}.tex"], **kwargs)

        if log_file.is_file():
            try:
                log_content = log_file.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.warning("Failed to read log file: %s", e)
                log_content = res.stdout or ""
        else:
            log_content = res.stdout or ""

        # A pass that yields no PDF is fatal: rerunning cannot help.
        if not pdf_file.is_file():
            break

        # Recoverable errors (nonstopmode carries on past them) must NOT stop
        # the rerun loop: the table of contents, the page total and longtable
        # column widths all need a further pass whether or not errors occurred.
        rerun_patterns = (
            "Rerun to get",
            "Rerun LaTeX",
            "Please rerun LaTeX",
            "There were undefined references",
        )
        rerun_needed = any(pattern in log_content for pattern in rerun_patterns)

        if pass_idx >= min_passes and not rerun_needed:
            break

    report = parse_log(log_content)
    report.passes = passes_run
    report.log_path = str(log_file) if log_file.is_file() else None
    report.success = pdf_file.is_file() and len(report.errors) == 0

    return report


def compile_tex(tex_path: str | Path, passes: int = 1) -> bool:
    """Backward-compatible single/multi-pass compile helper."""
    report = run_latex(tex_path, max_passes=max(1, passes))
    return report.success
