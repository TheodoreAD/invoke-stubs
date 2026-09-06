# Agent instructions for invoke-stubs

A stubs-only distribution — no runtime code, no tests of its own. `invoke-stubs/` holds a PEP 561
stub package, still marked `py.typed` = `partial`, declaring every module `__init__.pyi` re-exports
from plus `util`. `env`, `completion`, `main` and the vendored packages are not declared and fall
through to invoke's inline annotations.

- A new `.pyi` shadows invoke's inline version of that module entirely, so it must declare that
  module's whole public surface — including the attributes a class assigns to `self`, which
  `basedpyright --createstub` does not emit. Measured: `Result.exited` was missing from a generated
  stub that otherwise looked complete.
- The marker stays `partial` until every remaining module is declared. Emptying it removes the
  fallback outright, so a consumer that *has* invoke installed loses any name whose module is not
  shipped — see `plans/2026-08-30-missing-collection-and-context-stubs.md`, which measured that and
  sets the order.
- `__init__.pyi` mirrors the names invoke's own `__init__.py` re-exports, in `import X as X` form.
  When bumping against a new invoke release, diff it against `invoke/__init__.py` in that release.
  Do not run an import sorter over it without this repo's `ruff.toml`: without `combine-as-imports`,
  the `import X as X` form reads as a duplicate import and the block is split one name per line.
- `tasks.pyi` is hand-written and is not regenerated — its `ParamSpec` overloads are the whole point
  of the distribution, and a generator flattens them back to invoke's bare `Callable`. The other
  modules started from `basedpyright --createstub invoke`, run in a virtualenv holding invoke and
  nothing else (with this package installed, the generator stubs *these* files instead), then
  stripped of docstrings, modernized to `X | None` and builtin generics, and given the missing
  `self` attributes by hand.
- Verification lives in the consumer: `repo-tasks` depends on this package and its
  `inv quality.type-check` is the test (`from invoke import task` typed, zero
  `reportPrivateImportUsage`/`reportUntypedFunctionDecorator`). See
  `repo-tasks/contributing/type-checking.md` for why this exists and why it ships as a PEP 561
  partial stub distribution rather than via `stubPath`, and
  `repo-tasks/plans/2026-08-26-typing-followups.md` for the upstream-contribution status.
- Consumers install it by git URL (`invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`),
  so a push to `main` is a release. Bump `version` in `pyproject.toml` on any stub change so
  `uv lock --upgrade-package invoke-stubs` has something to move to.
