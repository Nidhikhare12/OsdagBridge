"""Pytest configuration and shared fixtures for OsdagBridge test suite."""

import json
import os
import shutil
from pathlib import Path
import pytest




def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "latex: mark test as requiring a pdflatex compiler"
    )


@pytest.fixture(scope="session")
def pdflatex_available() -> bool:
    """Return True if pdflatex is available on PATH or via osdag_latex_env."""
    try:
        from osdag_latex_env.__main__ import OsdagLatexEnv
        env = OsdagLatexEnv()
        if env.available and os.path.exists(env.pdflatex):
            return True
    except Exception:
        pass
    return shutil.which("pdflatex") is not None


@pytest.fixture(autouse=True)
def skip_latex_if_missing(request, pdflatex_available):
    """Automatically skip tests marked with @pytest.mark.latex if pdflatex is unavailable."""
    if request.node.get_closest_marker("latex") and not pdflatex_available:
        pytest.skip("pdflatex compiler not available in environment")


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "reports"


@pytest.fixture
def baseline_fixture(fixtures_dir) -> dict:
    path = fixtures_dir / "baseline_default.json"
    if not path.is_file():
        pytest.skip(f"Fixture {path} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
