"""Calls into the classes an import-only check merely names.

Run by `checks/verify.py` against a virtualenv holding invoke, basedpyright and this package. Not
executed — basedpyright reads it. The edge cases at the bottom are each a defect this file caught
once, so they stay even though they look arbitrary.
"""

from pathlib import Path
from typing import Any

from invoke import (
    Argument,
    Collection,
    Config,
    Context,
    Executor,
    FailingResponder,
    FilesystemLoader,
    Local,
    Parser,
    ParserContext,
    Program,
    Responder,
    Result,
    Task,
    task,
)


@task
def noop(c: Context) -> None:
    c.run("true")


ns = Collection()
ns.add_task(noop)

# Config
config = Config(overrides={"run": {"echo": True}}, defaults=None, lazy=False)
config.load_shell_env()
merged: dict[str, Any] = config.global_defaults()
prefix: str = config.prefix
clone: Config = config.clone()

# Loader and Program
loader = FilesystemLoader(config=config, start="/tmp")
program = Program(version="1.0", namespace=ns, name="demo", binary="demo")
program.run(argv=["demo", "noop"], exit=False)
core_args: list[Argument] = program.core_args()
depth: int | None = program.list_depth
fmt: str = program.list_format

# Executor
executor = Executor(collection=ns, config=config)
results: dict[Task[Any], Result] = executor.execute("noop")

# Parser
parser_context = ParserContext(name="noop", aliases=(), args=[Argument(names=["clean"], kind=bool)])
parser = Parser(contexts=[parser_context], ignore_unknown=True)
unparsed: list[str] = parser.parse_argv(["noop", "--clean"]).unparsed

# Watchers
responder = Responder(pattern=r"Password:", response="hunter2\n")
failing = FailingResponder(pattern=r"Password:", response="hunter2\n", sentinel="denied")
seen: object = responder.submit("Password:")
tried: bool = failing.tried

# Runner
runner = Local(Context(config=config))
chunk: int = runner.read_chunk_size
use_pty: bool = runner.should_use_pty(pty=True, fallback=False)

# Each of these was a real defect once.
config["timeout"] = 30  # invoke annotates the value as str; the runtime takes anything
_ = Config(project_location=Path("/tmp"))  # bare PathLike resolves as PathLike[Unknown]
with Context(config=config).cd(Path("/tmp")):  # same, via cd
    pass

print(merged, prefix, clone, loader, core_args, depth, fmt, results, unparsed, seen, tried, chunk, use_pty)
