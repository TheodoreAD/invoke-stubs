"""Every attribute invoke assigns to `self` has to be declared on the corresponding stub class.

`basedpyright --createstub` emits methods, properties and class-level names and silently drops
instance attributes, so a generated stub looks complete while missing exactly the members consumers
read. 47 were missing across 13 classes when the modules first landed — `Result.exited`, `.stdout`
and `.stderr` among them.

It needs invoke's own source, so it cannot be a unit test; it is also the check that catches an
invoke release adding an attribute to a class already stubbed here.
"""

import ast
from pathlib import Path

import pytest

from tests.conftest import STUBS

# Declared by a stdlib base in typeshed; redeclaring conflicts with it.
INHERITED = {"daemon"}

# A module-level constant rather than a `frozenset()` call in a parameter default, which
# basedpyright's reportCallInDefaultInitializer rejects — correctly, since a default is evaluated
# once at definition time.
NOTHING_SEEN: frozenset[str] = frozenset()


def site_packages(venv_basedpyright: Path) -> Path:
    return next((venv_basedpyright.parent.parent / "lib").glob("python*/site-packages"))


def declared_with_bases(stub: Path) -> dict[str, set[str]]:
    """Per class, the names it declares plus everything its in-module bases declare.

    Following bases matters: `warned_about_pty_fallback` belongs on `Runner` and `Local` assigns it
    too, and declaring it twice is what a stub should not do.
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

    def resolve(name: str, seen: frozenset[str] = NOTHING_SEEN) -> set[str]:
        if name in seen or name not in own:
            return set()
        return set(own[name]).union(*(resolve(b, seen | {name}) for b in bases[name]), set())

    return {name: resolve(name) for name in own}


def assigned_to_self(module: ast.Module) -> dict[str, set[str]]:
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


def stubbed_modules() -> list[str]:
    return sorted(p.stem for p in STUBS.glob("*.pyi") if p.stem != "__init__")


@pytest.mark.parametrize("module", stubbed_modules())
def test_no_instance_attribute_is_missing_from_its_stub(module: str, venv_with_invoke: Path):
    source = site_packages(venv_with_invoke) / "invoke" / f"{module}.py"
    if not source.exists():
        pytest.skip(f"invoke ships no {module}.py — this stub has no upstream counterpart")
    declared = declared_with_bases(STUBS / f"{module}.pyi")
    missing = {
        cls: sorted(attrs - declared[cls] - INHERITED)
        for cls, attrs in assigned_to_self(ast.parse(source.read_text())).items()
        if cls in declared and attrs - declared[cls] - INHERITED
    }
    assert missing == {}, (
        f"{module}.pyi is missing attributes invoke assigns: {missing}. A generated stub drops "
        f"these silently — declare each one with the type of its matching __init__ parameter."
    )
