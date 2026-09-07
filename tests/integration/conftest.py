"""The two virtualenvs the tier is about, built once per session.

invoke is deliberately not a dependency of this project — a second `inv` on PATH would shadow the
globally installed repo-tasks tool — so the tier supplies it here instead. That is not a workaround
for the missing dependency: the whole subject of these stubs is how they behave *with invoke
installed* versus *without it*, so two environments is the thing being tested, not scaffolding
around it.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

import pytest

# basedpyright's `reportAny` is an error in this family, and `json.loads` returns `Any` by
# construction — so every crossing of that boundary is cast once, here, rather than suppressed at
# each call site.
Diagnostics = list[dict[str, object]]

PYTHON = "3.11"

# `recommended` plus the family's own departures, matching what a consumer actually runs. Kept here
# rather than pulled from the repo's own pyrightconfig.json: this is the *consumer's* config, and
# the point is to reproduce what a repo taking this package would see.
CONSUMER_PYRIGHT_CONFIG = {
    "typeCheckingMode": "recommended",
    "include": ["probe*"],
    "failOnWarnings": True,
    "reportUnusedCallResult": "none",
    "reportUnusedParameter": "hint",
    "reportExplicitAny": "none",
}


def _run(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)


def _build(path: Path, repo_root: Path, *, with_invoke: bool) -> Path:
    if shutil.which("uv") is None:
        pytest.skip("uv is not on PATH")
    if not (path / "bin" / "python").exists():
        created = _run("uv", "venv", "--python", PYTHON, str(path))
        assert created.returncode == 0, created.stderr
    # mypy alongside basedpyright: the README claims both, and a claim nothing runs is a claim that
    # rots. Same two environments, so it costs one install rather than a third venv.
    packages = ["basedpyright", "mypy", str(repo_root)] + (["invoke"] if with_invoke else [])
    python = str(path / "bin" / "python")
    installed = _run("uv", "pip", "install", "--python", python, "--reinstall-package", "invoke-stubs", *packages)
    assert installed.returncode == 0, installed.stderr
    return path / "bin" / "basedpyright"


@pytest.fixture(scope="session")
def venv_with_invoke(tmp_path_factory: pytest.TempPathFactory, repo_root: Path) -> Path:
    return _build(tmp_path_factory.mktemp("with-invoke") / "venv", repo_root, with_invoke=True)


@pytest.fixture(scope="session")
def venv_without_invoke(tmp_path_factory: pytest.TempPathFactory, repo_root: Path) -> Path:
    return _build(tmp_path_factory.mktemp("without-invoke") / "venv", repo_root, with_invoke=False)


def probe_sources(tmp_path: Path, sources: dict[str, str]) -> Path:
    """Write a throwaway consumer package. Shared so both checkers see byte-identical sources."""
    package = tmp_path / "probe"
    package.mkdir(exist_ok=True)
    (package / "__init__.py").write_text("")
    for name, source in sources.items():
        (package / name).write_text(source)
    return package


@pytest.fixture
def check_consumer(tmp_path: Path):
    """Type-check a throwaway consumer package against one of the virtualenvs.

    `venvPath`/`venv` are not optional: the checker resolves imports from the environment its config
    names, not from the interpreter that launched it, so without them every probe reports
    `reportMissingImports` for invoke whichever binary runs.
    """

    def check(basedpyright: Path, sources: dict[str, str]) -> Diagnostics:
        venv = basedpyright.parent.parent
        config = CONSUMER_PYRIGHT_CONFIG | {"venvPath": str(venv.parent), "venv": venv.name}
        (tmp_path / "pyrightconfig.json").write_text(json.dumps(config))
        probe_sources(tmp_path, sources)
        proc = _run(str(basedpyright), "--outputjson", cwd=tmp_path)
        assert proc.stdout.strip(), f"basedpyright produced no output: {proc.stderr}"
        return cast("Diagnostics", json.loads(proc.stdout)["generalDiagnostics"])

    return check
