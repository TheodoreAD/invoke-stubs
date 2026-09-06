# Agent instructions for invoke-stubs

A stubs-only distribution — no runtime code. `invoke-stubs/` holds a PEP 561 stub package, still
marked `py.typed` = `partial`, declaring every module `__init__.pyi` re-exports from plus `util`.
`env`, `completion`, `main` and the vendored packages are not declared and fall through to invoke's
inline annotations.

## Build & test

```shell
python3 checks/verify.py                    # all four checks; needs uv, builds throwaway venvs
python3 checks/verify.py --workdir .verify  # reuse the venvs, much faster while iterating
python3 checks/verify.py --invoke 'invoke==3.1.0'   # check against a specific release
uvx ruff format . && uvx ruff check --select I .    # formatting; the repo has no other gate
```

Run `verify.py` before every commit that touches `invoke-stubs/`, and on any invoke version bump.
It builds two virtualenvs (one with invoke, one without) and checks: the stub package against
itself; every name `__init__.pyi` re-exports, in both configurations; the `checks/usage_probe.py`
fixture, which calls into classes an import-only check merely names; and that no class is missing an
attribute invoke assigns to `self`.

- A new `.pyi` shadows invoke's inline version of that module entirely, so it must declare that
  module's whole public surface — including the attributes a class assigns to `self`, which
  `basedpyright --createstub` does not emit. Measured: `Result.exited` was missing from a generated
  stub that otherwise looked complete. Check 4 exists for exactly this.
- **Add a case to `checks/usage_probe.py` for anything the other checks cannot see.** They cover
  names and attributes; a wrong *signature* is only found by calling it. Every edge case at the
  bottom of that file was a real defect once.
- **The marker stays `partial`. That is a decision, not a stage.** Emptying it removes the fallback
  outright, so a consumer that *has* invoke installed loses any name whose module is not shipped,
  and it buys nothing: the modules are what make these stubs authoritative, and with them in place
  a consumer type-checks clean without `allowedUntypedLibraries: ["invoke"]` while `partial` is
  still set. Measured both ways — see
  `plans/2026-08-30-missing-collection-and-context-stubs.md` section 4.
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
- The end-to-end verification still lives in the consumer, and `checks/verify.py` does not replace
  it: `repo-tasks` depends on this package and its `inv quality.type-check` is the test
  (`from invoke import task` typed, zero
  `reportPrivateImportUsage`/`reportUntypedFunctionDecorator`). See
  `repo-tasks/contributing/type-checking.md` for why this exists and why it ships as a PEP 561
  partial stub distribution rather than via `stubPath`, and
  `repo-tasks/plans/2026-08-26-typing-followups.md` for the upstream-contribution status.
- Consumers install it by git URL (`invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`),
  so a push to `main` is a release. Bump `version` in `pyproject.toml` on any stub change so
  `uv lock --upgrade-package invoke-stubs` has something to move to.
