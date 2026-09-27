"""What a consumer actually sees, in both configurations, through a real type checker.

The unit tier proves the package is internally consistent. Only this tier can prove the thing the
distribution exists for: that a repo with **invoke absent** type-checks a task module cleanly, and
that a repo with invoke installed is not regressed by the stubs shadowing its modules.
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import cast

import pytest

from tests.conftest import STUBS, stub_module
from tests.integration.conftest import Diagnostics

# A stubs-only distribution whose runtime is not installed always reports this, and no amount of
# stub surface closes it. The consumer configures it; the tier subtracts it rather than asserting
# a clean run that cannot happen.
IRREDUCIBLE = "reportMissingModuleSource"

# Embedded rather than kept as a file: a real `.py` importing invoke would itself be type-checked by
# this repo's own gate, where invoke is absent by design. Every case below the first block was a
# defect this probe caught once — add to it rather than replacing it.
USAGE_PROBE = '''
"""Calls into the classes an import-only check merely names."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, assert_type

from invoke import (
    Argument, Collection, Config, Context, Executor, FailingResponder, FilesystemLoader, Local,
    MockContext, Parser, ParserContext, Program, Responder, Result, Task, UnexpectedExit, task,
)
from invoke.collection import Collection as RealCollection
from invoke.exceptions import UnexpectedExit as RealUnexpectedExit


def takes_real(coll: RealCollection) -> None:
    print(coll)


ns = Collection()
takes_real(ns)
config = Config(overrides={"run": {"echo": True}}, defaults=None, lazy=False)
c = Context(config=Config(overrides=ns.configuration()))


@task
def type_check(ctx: Context) -> None:
    """The one-parameter shape repo-tasks pins with an annotated assignment."""
    result: Result = ctx.run("basedpyright")
    print(result.stdout, result.exited)


ns.add_task(type_check)

config.load_shell_env()
merged: dict[str, Any] = config.global_defaults()
loader = FilesystemLoader(config=config, start="/tmp")
program = Program(version="1.0", namespace=ns, name="demo", binary="demo")
program.run(argv=["demo", "type-check"], exit=False)
core_args: list[Argument] = program.core_args()
executor = Executor(collection=ns, config=config)
results: dict[Task[Any], Result] = executor.execute("type-check")
parser = Parser(contexts=[ParserContext(name="t", args=[Argument(names=["clean"], kind=bool)])])
unparsed: list[str] = parser.parse_argv(["t", "--clean"]).unparsed
responder = Responder(pattern=r"Password:", response="x\\n")
failing = FailingResponder(pattern=r"Password:", response="x\\n", sentinel="denied")
runner = Local(Context(config=config))
chunk: int = runner.read_chunk_size

mock: MockContext = MockContext(run=Result(stdout="", exited=0))
type_check.body(mock)
body: Callable[[Context], None] = type_check.body
error: type[UnexpectedExit] = RealUnexpectedExit
assert_type(ns, Collection)

# Each of these was a real defect once.
config["timeout"] = 30            # invoke annotates the value as str; the runtime takes anything
_ = Config(project_location=Path("/tmp"))   # bare PathLike resolves as PathLike[Unknown]
with Context(config=config).cd(Path("/tmp")):
    pass

# `Lexicon` is generic here where invoke's subclasses a bare dict, so these were `Any` and cost the
# one real consumer 14 casts. `assert_type` rather than a plain call: `Any` satisfies every call.
sub = Collection(name="sub")
ns.add_collection(sub)
assert_type(ns.collections["sub"], Collection)
assert_type(ns.tasks["type-check"], Task[Any])
assert_type(ns.collections.sub, Collection)
assert_type(program.args["help"], Argument)

print(merged, loader, core_args, results, unparsed, responder, failing, chunk, body, error, c)
'''


def reexported_names() -> list[str]:
    """Generated from `__init__.pyi` so the list cannot drift from what the package claims."""
    names: set[str] = set()
    for node in stub_module("__init__").body:
        if isinstance(node, ast.ImportFrom) and node.level:
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name)
    return sorted(names)


def import_everything() -> str:
    names = reexported_names()
    return (
        '"""Imports every name invoke re-exports. Generated from __init__.pyi."""\n\n'
        + "from invoke import (\n"
        + "".join(f"    {n},\n" for n in names)
        + ")\n\nprint(\n"
        + "".join(f"    {n},\n" for n in names)
        + ")\n"
    )


def describe(diagnostics: Diagnostics) -> str:
    return "\n".join(f"  {d['severity']}: {str(d['message']).splitlines()[0]} ({d.get('rule')})" for d in diagnostics)


@pytest.mark.smoke
def test_every_reexported_name_resolves_without_invoke_installed(check_consumer, venv_without_invoke: Path):
    """The configuration this distribution exists for, and the one nobody was checking.

    Before 0.2.0 a consumer importing four names got 4 errors and 9 warnings here.
    """
    diagnostics = [
        d
        for d in check_consumer(venv_without_invoke, {"all_names.py": import_everything()})
        if d.get("rule") != IRREDUCIBLE
    ]
    assert diagnostics == [], f"invoke absent, {len(diagnostics)} diagnostic(s):\n{describe(diagnostics)}"


@pytest.mark.smoke
def test_the_stubs_do_not_regress_a_consumer_that_has_invoke(check_consumer, venv_with_invoke: Path):
    """The regression test for the two shapes the design rejected.

    Declaring classes inline in `__init__.pyi` forks `invoke.Collection` from
    `invoke.collection.Collection`; a sibling stub that is partial for its own module drops the
    members it does not name. Both show up here and nowhere else.
    """
    diagnostics = check_consumer(venv_with_invoke, {"all_names.py": import_everything(), "usage.py": USAGE_PROBE})
    assert diagnostics == [], f"invoke installed, {len(diagnostics)} diagnostic(s):\n{describe(diagnostics)}"


def test_the_stub_package_is_internally_consistent(check_consumer, venv_with_invoke: Path, tmp_path: Path):
    """Type-check the stubs as source rather than as a dependency.

    Cheapest of the three and the one that found `Promise.__exit__` failing to satisfy
    `AbstractContextManager` — a defect no consumer probe reaches, because no consumer subclasses it.

    `reportMissingTypeArgument` is off in `standard` and on here: a bare generic in a stub, such as
    `Promise`'s unparameterized `AbstractContextManager` base, reads as `Unknown` and turns every
    class downstream partially unknown in a consumer's `--verifytypes`, with no diagnostic in the
    consumer's own code to say why.
    """
    (tmp_path / "pyrightconfig.json").write_text(
        json.dumps(
            {
                "typeCheckingMode": "standard",
                "include": [str(STUBS)],
                "reportMissingModuleSource": "none",
                "reportMissingTypeArgument": "error",
                "venvPath": str(venv_with_invoke.parent.parent.parent),
                "venv": venv_with_invoke.parent.parent.name,
            }
        )
    )
    proc = subprocess.run(
        [str(venv_with_invoke), "--outputjson"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    diagnostics = cast("Diagnostics", json.loads(proc.stdout)["generalDiagnostics"])
    assert diagnostics == [], f"{len(diagnostics)} diagnostic(s) in the stubs themselves:\n{describe(diagnostics)}"
