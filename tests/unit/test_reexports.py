"""Every name `__init__.pyi` re-exports has to resolve in the module it names.

This is the tier's most valuable test and the cheapest: `from invoke import Failure` shipped broken
in 0.2.0 because `invoke/__init__.py` re-exports `Failure` from `.runners` although `.exceptions`
defines it, and the generated `runners.pyi` carried no such name. It took two throwaway virtualenvs
and a type checker to find. It is an AST walk over two files.
"""

import ast

import pytest

from tests.conftest import STUBS, stub_module, stub_paths


def reexports() -> list[tuple[str, str, str]]:
    """`(module, original name, exported name)` for every relative import in `__init__.pyi`."""
    out: list[tuple[str, str, str]] = []
    for node in stub_module("__init__").body:
        if isinstance(node, ast.ImportFrom) and node.level and node.module:
            out += [(node.module, alias.name, alias.asname or alias.name) for alias in node.names]
    return out


def declared(module: ast.Module) -> set[str]:
    """Top-level names a stub module binds — classes, functions, annotated names, and the names it
    imports under an explicit alias, which is how a stub re-exports something it did not define."""
    names: set[str] = set()
    for node in module.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


@pytest.mark.parametrize(("module", "name", "exported"), reexports(), ids=str)
def test_every_reexported_name_exists_in_the_module_it_comes_from(module: str, name: str, exported: str):
    assert name in declared(stub_module(module)), (
        f"__init__.pyi re-exports {exported} from .{module}, which declares no {name}. "
        f"Either {module}.pyi is missing it, or it needs importing there under an explicit alias — "
        f"invoke re-exports several names from a module other than the one defining them."
    )


@pytest.mark.parametrize("module", sorted({module for module, _, _ in reexports()}))
def test_every_module_init_names_is_shipped(module: str):
    flat, package = STUBS / f"{module}.pyi", STUBS / module / "__init__.pyi"
    assert flat.exists() or package.exists(), (
        f"__init__.pyi imports from .{module}, which this package does not ship. Under the "
        f"`partial` marker that falls back to invoke's own annotations only where invoke is "
        f"installed; where it is not, every name from it is an unknown import symbol."
    )


def test_reexports_use_the_redundant_alias_form():
    """PEP 484 counts a stub's import as public only when it is aliased to its own name."""
    plain = [f".{module}:{name}" for module, name, exported in reexports() if name != exported]
    assert plain == [], (
        f"re-exported without `as`: {plain}. A type checker reads those as private, which is the "
        f"reportPrivateImportUsage this distribution exists to fix."
    )


def test_every_stub_parses():
    """A stub that does not parse fails silently — the checker falls back rather than erroring."""
    for path in stub_paths():
        ast.parse(path.read_text(), filename=str(path))


def test_py_typed_still_says_partial():
    """The marker is a decision, not a stage — see contributing/stub-decisions.md.

    Emptying it removes the fallback for every module this package does not ship, and buys nothing
    that shipping the modules did not already buy.
    """
    assert (STUBS / "py.typed").read_text().strip() == "partial"
