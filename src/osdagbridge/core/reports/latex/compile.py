"""LaTeX compilation engine and environment discovery."""

from __future__ import annotations
import os
from pathlib import Path
import subprocess
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


def get_compiler_cmd() -> Tuple[str, Dict[str, str]]:
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


def compile_tex(tex_path: str | Path, passes: int = 1) -> bool:
    """Compile a .tex file to PDF using discovered compiler."""
    path = Path(tex_path).resolve()
    cwd = str(path.parent)
    stem = path.stem
    compiler, env = get_compiler_cmd()

    kwargs = {
        "cwd": cwd,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "check": False,
        "env": env,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    for _ in range(passes):
        subprocess.run([compiler, "-interaction=nonstopmode", f"{stem}.tex"], **kwargs)

    pdf_file = path.with_suffix(".pdf")
    return pdf_file.exists()
