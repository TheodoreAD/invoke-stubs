"""The other checker the README claims, exercised against the same two environments.

Everything else in this repo is measured on basedpyright alone, and mypy is the checker whose
handling of a `partial` marker and of stub-shadowing this distribution most depends on: `partial` is
a deliberate, permanent choice here, so a checker that ignored it would silently drop every name
the package does not ship rather than falling back to invoke's own annotations.

Measured clean both ways on mypy 2.3.1 the day this was written; the test exists so the next mypy
release says so itself instead of the README continuing to assert it.
"""

import subprocess
from pathlib import Path

import pytest

from tests.integration.conftest import probe_sources
from tests.integration.test_consumer_integration import USAGE_PROBE, import_everything


def run_mypy(venv_basedpyright: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """`--strict` because a consumer's own gate is stricter than mypy's default, not to be showy.

    The venv's own mypy rather than this repo's: it resolves imports from the interpreter it ships
    with, which is the whole point of having two environments.
    """
    probe_sources(tmp_path, {"all_names.py": import_everything(), "usage.py": USAGE_PROBE})
    mypy = venv_basedpyright.parent / "mypy"
    return subprocess.run([str(mypy), "--strict", "probe"], cwd=tmp_path, capture_output=True, text=True, check=False)


@pytest.mark.smoke
def test_mypy_resolves_every_name_without_invoke_installed(venv_without_invoke: Path, tmp_path: Path):
    """The configuration the distribution exists for, through the checker it had never been run on."""
    proc = run_mypy(venv_without_invoke, tmp_path)
    assert proc.returncode == 0, f"mypy, invoke absent:\n{proc.stdout}{proc.stderr}"


@pytest.mark.smoke
def test_mypy_is_not_regressed_by_the_stubs_where_invoke_is_installed(venv_with_invoke: Path, tmp_path: Path):
    """`partial` means mypy has invoke's own annotations to fall back to; shadowing must not break that."""
    proc = run_mypy(venv_with_invoke, tmp_path)
    assert proc.returncode == 0, f"mypy, invoke installed:\n{proc.stdout}{proc.stderr}"
