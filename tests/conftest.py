"""What both tiers share: where the stub package is, and how to read it.

The stub package's directory name is `invoke-stubs`, which is not an importable module name — so
every test reads it as files rather than importing it, and `stub_module` is the accessor that keeps
that detail in one place.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STUBS = REPO_ROOT / "invoke-stubs"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def stubs() -> Path:
    return STUBS


def stub_paths() -> list[Path]:
    """Every `.pyi` in the package, including the `parser/` subpackage."""
    return sorted(STUBS.rglob("*.pyi"))


def stub_module(name: str) -> ast.Module:
    """Parse one stub by its module name — `runners`, or `parser` for the subpackage's `__init__`."""
    path = STUBS / f"{name}.pyi"
    if not path.exists():
        path = STUBS / name / "__init__.pyi"
    return ast.parse(path.read_text(), filename=str(path))
