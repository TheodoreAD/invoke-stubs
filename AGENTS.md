# Agent instructions for invoke-stubs

A stubs-only distribution — no runtime code, but a real test suite. `invoke-stubs/` holds a PEP 561
stub package, still marked `py.typed` = `partial`, declaring every module `__init__.pyi` re-exports
from plus `util`. `env`, `completion`, `main` and the vendored packages are not declared and fall
through to invoke's inline annotations.

## Build & test

Same shape as every other repo in the family: `tasks.py` re-exports repo-tasks' namespace, and the
five shared config files come from `inv configs.pull` rather than being written here.

**Unlike every other consumer, repo-tasks is a dev dependency** rather than only the global tool.
That is what lets `tasks.py` import it without suppressions, and it pins the manifest in `uv.lock`
instead of taking whatever the globally installed tool happens to be — the two disagreed on
2026-09-07, and only the pinned one asked for `pytest-socket`/`pytest-timeout`. It brings invoke
with it, which the family normally avoids because a second `inv` on `PATH` shadows the global tool
with one that cannot import `repo_tasks`; that one can.

```shell
inv quality.precommit   # the gate — runs the unit tier, formatters and the type checker
inv test.unit           # tests/unit — pure AST over the stubs, no venv, no network, ~0.1s
inv test.integration    # tests/integration — builds two throwaway venvs, ~5s
inv test.all            # both tiers
```

**The tier split is forced by prerequisites, not preference.** The unit tier reads the stub package
as files and asserts its structural invariants — every name `__init__.pyi` re-exports is declared in
the module it names, every module it names is shipped, every re-export uses the `X as X` form.
`from invoke import Failure` shipped broken because `invoke/__init__.py` re-exports it from
`.runners` while `.exceptions` defines it; that is now a unit test that fails in 0.08s.

The integration tier is the only one that can answer what this distribution exists for — a consumer
with **invoke absent** type-checking cleanly — because that needs invoke installed in one virtualenv
and absent from another. It also checks the stubs as source, that no class is missing an attribute
invoke assigns to `self`, and that mypy `--strict` agrees with basedpyright in both environments.

- A new `.pyi` shadows invoke's inline version of that module entirely, so it must declare that
  module's whole public surface — including the attributes a class assigns to `self`, which
  `basedpyright --createstub` does not emit. Measured: `Result.exited` was missing from a generated
  stub that otherwise looked complete. `tests/integration/test_attributes_integration.py` exists for
  exactly this, and globs `**/*.pyi` — it was flat until 2026-09-07, and the `parser/` subpackage it
  could not see was missing 19 attributes across five classes.
- **Add a case to the `USAGE_PROBE` in `tests/integration/test_consumer_integration.py` for anything
  the other tests cannot see.** They cover names and attributes; a wrong _signature_ is only found
  by calling it. Every case at the bottom of that probe was a real defect once. Use `assert_type`
  where the defect would be an `Any` — a plain call proves nothing, since `Any` satisfies every
  call.
- **Four declarations deliberately depart from what invoke's source says**, each commented in place
  so a regeneration does not quietly revert it: `DataProxy.__setitem__` takes `Any` rather than
  `str`; `Promise.__exit__` accepts `BaseException | None` so it satisfies `AbstractContextManager`;
  `PathLike` is parameterized to `PathLike[str]` in `config.pyi` and `context.pyi`; and `Lexicon` is
  generic in its value type, where invoke's subclasses a bare `dict`. The rule is still to mirror
  upstream — these exist because a stub that rejects valid code, or hands the consumer `Any`, is
  worse than one that diverges. The `Lexicon` one deleted 14 casts from the one real consumer.
- **`inv configs.diff` will always report `dependency-groups.dev is missing: invoke-stubs`, and that
  is correct.** The canonical manifest lists this package because every _other_ consumer needs it;
  this repo is it, and taking the published build as a dev dependency would shadow the working tree
  under test with whatever `main` last released. `configs.ensure-deps` is additive and re-adds the
  entry on every run — remove it again rather than keeping it.
- **invoke is deliberately not a direct dependency**, here for two reasons rather than the usual
  one: a second `inv` on `PATH` would shadow the global repo-tasks tool, and the integration tier
  needs to control whether invoke is present at all.
- **The marker stays `partial`. That is a decision, not a stage.** Emptying it removes the fallback
  outright, so a consumer that _has_ invoke installed loses any name whose module is not shipped,
  and it buys nothing: the modules are what make these stubs authoritative, and with them in place a
  consumer type-checks clean without `allowedUntypedLibraries: ["invoke"]` while `partial` is still
  set. Measured both ways — see "Why does `py.typed` still say `partial`?" in
  `contributing/stub-decisions.md`.
- `__init__.pyi` mirrors the names invoke's own `__init__.py` re-exports, in `import X as X` form.
  When bumping against a new invoke release, diff it against `invoke/__init__.py` in that release.
  The canonical `ruff.toml` has no `combine-as-imports`, so the sorter splits that block into one
  `from X import (Y as Y,)` statement per name. That is cosmetic and deliberate — the redundant
  alias survives, so every name stays a public re-export, and the unit tier asserts it.
- `tasks.pyi` is hand-written and is not regenerated — its `ParamSpec` overloads are the whole point
  of the distribution, and a generator flattens them back to invoke's bare `Callable`. The other
  modules started from `basedpyright --createstub invoke`, run in a virtualenv holding invoke and
  nothing else (with this package installed, the generator stubs _these_ files instead), then
  stripped of docstrings, modernized to `X | None` and builtin generics, and given the missing
  `self` attributes by hand.
- The end-to-end verification still lives in the consumer, and neither tier replaces it:
  `repo-tasks` depends on this package and its `inv quality.type-check` is the test
  (`from invoke import task` typed, zero
  `reportPrivateImportUsage`/`reportUntypedFunctionDecorator`). See
  `repo-tasks/contributing/type-checking.md` for why this exists and why it ships as a PEP 561
  partial stub distribution rather than via `stubPath`, and
  `repo-tasks/plans/2026-08-26-typing-followups.md` for the upstream-contribution status.
- Consumers install it by git URL (`invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`),
  so a push to `main` is a release. Bump `version` in `pyproject.toml` on any stub change so
  `uv lock --upgrade-package invoke-stubs` has something to move to.
