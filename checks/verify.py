#!/usr/bin/env python3
"""Verify the stubs. Stdlib only; needs `uv` on PATH and a network for the first run.

    python3 checks/verify.py              # build throwaway venvs, run everything, clean up
    python3 checks/verify.py --workdir .verify   # reuse venvs across runs (much faster)
    python3 checks/verify.py --invoke 3.1.0      # check against a specific invoke release

This repo has no runtime code and no suite, so there is nothing to unit-test: what can be wrong
with a stub is that a name does not resolve, that a signature disagrees with invoke, or that the
package contradicts itself. Those are the four checks below.

The reason it is a script rather than a paragraph in AGENTS.md is that phase 1 shipped with four
defects that two hand-written consumer probes all passed — a probe written from what a consumer
imports only tests the names its author thought of. Checks 1 and 2 need no imagination and would
have caught two of the four on their own.

Exit status is 0 only if every check passes.
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STUBS = REPO / "invoke-stubs"
PYTHON = "3.11"

# The one diagnostic no version of this package can remove: a stubs-only distribution whose runtime
# is not installed always reports it. See the README.
IRREDUCIBLE = "reportMissingModuleSource"

CONFIG = {
    "typeCheckingMode": "recommended",
    "include": ["probe*"],
    "reportUnusedCallResult": "none",
    "reportUnusedParameter": "hint",
    "reportExplicitAny": "none",
}


def run(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)


def make_venv(path: Path, with_invoke: bool, invoke_spec: str) -> Path:
    """A virtualenv holding basedpyright, this package, and optionally invoke itself."""
    python = path / "bin" / "python"
    if not python.exists():
        proc = run("uv", "venv", "--python", PYTHON, str(path))
        if proc.returncode:
            sys.exit(f"uv venv failed:\n{proc.stderr}")
    packages = ["basedpyright", str(REPO)] + ([invoke_spec] if with_invoke else [])
    proc = run("uv", "pip", "install", "--python", str(python), "--reinstall-package", "invoke-stubs", *packages)
    if proc.returncode:
        sys.exit(f"uv pip install failed:\n{proc.stderr}")
    return path / "bin" / "basedpyright"


def diagnostics(basedpyright: Path, project: Path) -> list[dict[str, object]]:
    proc = run(str(basedpyright), "--outputjson", cwd=project)
    if not proc.stdout.strip():
        sys.exit(f"basedpyright produced no output:\n{proc.stderr}")
    return json.loads(proc.stdout)["generalDiagnostics"]


def describe(diags: list[dict[str, object]]) -> str:
    return "\n".join(f"    {d['severity']}: {d['message'].splitlines()[0]} ({d.get('rule')})" for d in diags)


def reexported_names() -> list[str]:
    """Every name `__init__.pyi` re-exports, parsed from it so the list cannot drift.

    Relative imports only: `from typing import Any` is not a re-export, and unaliased imports in a
    stub are private, but this package's `__init__.pyi` aliases every public one.
    """
    tree = ast.parse((STUBS / "__init__.pyi").read_text())
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level:
            names.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name)
    return sorted(names)


def write_project(root: Path, probes: dict[str, str], venv: Path, extra: dict[str, object] | None = None) -> Path:
    """A throwaway pyright project pointed at `venv`.

    `venvPath`/`venv` are not optional here: the checker resolves imports from the environment its
    config names, not from the interpreter it happens to be launched with, so without them every
    probe reports `reportMissingImports` for invoke no matter which venv's binary runs.
    """
    root.mkdir(parents=True, exist_ok=True)
    config = dict(CONFIG) | {"venvPath": str(venv.parent), "venv": venv.name} | (extra or {})
    (root / "pyrightconfig.json").write_text(json.dumps(config, indent=2))
    package = root / "probe"
    package.mkdir(exist_ok=True)
    (package / "__init__.py").write_text("")
    for name, source in probes.items():
        (package / name).write_text(source)
    return root


def declared_in_stub(stub: Path) -> dict[str, set[str]]:
    """Per class, the names the stub declares — attributes, methods and properties alike.

    Parsed rather than grepped. A substring search for `"    name:"` also matches the same name as
    an indented `__init__` parameter, so removing `Result.exited` from the class body left this
    check reporting ok — found by deliberately reintroducing that defect.

    A name declared on a base class counts for its subclasses, since declaring it twice is what a
    stub should not do: `warned_about_pty_fallback` belongs on `Runner`, and `Local` assigns it too.
    Only bases defined in the same stub module are followed, which covers every class here.
    """
    own: dict[str, set[str]] = {}
    bases: dict[str, list[str]] = {}
    for cls in (n for n in ast.parse(stub.read_text()).body if isinstance(n, ast.ClassDef)):
        names: set[str] = set()
        for node in cls.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
            elif isinstance(node, ast.Assign):
                names.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
        own[cls.name] = names
        bases[cls.name] = [b.id for b in cls.bases if isinstance(b, ast.Name)]

    def inherited(name: str, seen: frozenset[str] = frozenset()) -> set[str]:
        if name in seen or name not in own:
            return set()
        acc = set(own[name])
        for base in bases[name]:
            acc |= inherited(base, seen | {name})
        return acc

    return {name: inherited(name) for name in own}


def assigned_in_source(module: ast.Module) -> dict[str, set[str]]:
    """Per class, the public attributes invoke assigns to `self` anywhere in the class body."""
    assigned: dict[str, set[str]] = {}
    for cls in (n for n in ast.walk(module) if isinstance(n, ast.ClassDef)):
        names: set[str] = set()
        for node in ast.walk(cls):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            names.update(
                t.attr
                for t in targets
                if isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
                and not t.attr.startswith("_")
            )
        assigned[cls.name] = names
    return assigned


# Declared by a stdlib base class in typeshed; redeclaring them here conflicts with it.
INHERITED = {"daemon"}


def missing_attributes(venv: Path) -> dict[str, list[str]]:
    """Attributes invoke assigns to `self` that the corresponding stub class does not declare.

    basedpyright --createstub emits methods and class-level names and drops these silently, so a
    regenerated stub can look complete while missing the members consumers actually read. Also
    catches an invoke release that adds an attribute to a class already stubbed here.
    """
    site = next((venv / "lib").glob("python*/site-packages"))
    missing: dict[str, list[str]] = {}
    for source in sorted((site / "invoke").glob("*.py")):
        stub = STUBS / f"{source.stem}.pyi"
        if not stub.exists():
            continue
        declared = declared_in_stub(stub)
        for cls_name, attrs in assigned_in_source(ast.parse(source.read_text())).items():
            if cls_name not in declared:
                continue
            gap = sorted(attrs - declared[cls_name] - INHERITED)
            if gap:
                missing[f"{source.stem}.{cls_name}"] = gap
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workdir", type=Path, help="reuse venvs here instead of a temporary directory")
    parser.add_argument("--invoke", default="invoke", help="invoke requirement to check against, e.g. 'invoke==3.0.3'")
    args = parser.parse_args()

    if not shutil.which("uv"):
        sys.exit("uv is not on PATH; see https://docs.astral.sh/uv/")

    temp = None if args.workdir else tempfile.TemporaryDirectory()
    workdir = args.workdir or Path(temp.name)  # pyright: ignore[reportOptionalMemberAccess]
    workdir.mkdir(parents=True, exist_ok=True)

    names = reexported_names()
    all_names = (
        '"""Imports every name `invoke.__init__` re-exports. Generated by checks/verify.py."""\n\n'
        + "from invoke import (\n"
        + "".join(f"    {n},\n" for n in names)
        + ")\n\nprint(\n"
        + "".join(f"    {n},\n" for n in names)
        + ")\n"
    )
    usage = (Path(__file__).parent / "usage_probe.py").read_text()

    failures: list[str] = []

    print(f"invoke-stubs checks — {len(names)} re-exported names, python {PYTHON}")

    # 1. The stub package against itself. No venv, no consumer, and it is what found the two
    #    defects that a consumer probe structurally cannot see.
    with_invoke_venv = workdir / "with-invoke"
    with_invoke = make_venv(with_invoke_venv, True, args.invoke)
    selfcheck = write_project(
        workdir / "selfcheck",
        {},
        with_invoke_venv,
        extra={"typeCheckingMode": "standard", "include": [str(STUBS)], "reportMissingModuleSource": "none"},
    )
    diags = diagnostics(with_invoke, selfcheck)
    print(f"  1. stub package self-consistency        {'ok' if not diags else 'FAILED'}")
    if diags:
        failures.append("stub package self-consistency\n" + describe(diags))

    # 2. Every re-exported name, in both configurations. Cheap, generated, and the check that
    #    `from invoke import Failure` needed.
    project = write_project(workdir / "consumer", {"all_names.py": all_names, "usage.py": usage}, with_invoke_venv)
    diags = diagnostics(with_invoke, project)
    print(f"  2. all names + usage, invoke installed  {'ok' if not diags else 'FAILED'}")
    if diags:
        failures.append("all names + usage, invoke installed\n" + describe(diags))

    without_invoke_venv = workdir / "without-invoke"
    without_invoke = make_venv(without_invoke_venv, False, args.invoke)
    names_only = write_project(workdir / "consumer-bare", {"all_names.py": all_names}, without_invoke_venv)
    diags = [d for d in diagnostics(without_invoke, names_only) if d.get("rule") != IRREDUCIBLE]
    print(f"  3. all names, invoke absent             {'ok' if not diags else 'FAILED'}")
    if diags:
        failures.append("all names, invoke absent\n" + describe(diags))

    # 4. Attributes invoke assigns to self that no stub declares. Catches a regenerated stub, and
    #    an invoke release that adds attributes to an existing class.
    missing = missing_attributes(workdir / "with-invoke")
    print(f"  4. declared instance attributes         {'ok' if not missing else 'FAILED'}")
    if missing:
        failures.append(
            "declared instance attributes\n"
            + "\n".join(f"    {cls}: {', '.join(attrs)}" for cls, attrs in sorted(missing.items()))
        )

    if temp:
        temp.cleanup()

    if failures:
        print("\n" + "\n\n".join(failures))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
