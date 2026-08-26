# Agent instructions for invoke-stubs

A stubs-only distribution — no runtime code, no tests of its own. `invoke-stubs/` holds a partial
PEP 561 stub package (`py.typed` = `partial`): only `tasks.pyi` and `__init__.pyi` are declared
here, everything else falls through to invoke's inline annotations.

- Keep it partial. Adding a module here shadows invoke's inline version of that module entirely,
  so a new `.pyi` must declare that module's whole public surface.
- `__init__.pyi` mirrors the names invoke's own `__init__.py` re-exports, in `import X as X` form.
  When bumping against a new invoke release, diff it against `invoke/__init__.py` in that release.
- Verification lives in the consumer: `repo-tasks` depends on this package and its
  `inv quality.type-check` is the test (`from invoke import task` typed, zero
  `reportPrivateImportUsage`/`reportUntypedFunctionDecorator`). See
  `repo-tasks/contributing/type-checking.md` for why this exists and why it ships as a PEP 561
  partial stub distribution rather than via `stubPath`, and
  `repo-tasks/plans/2026-08-26-typing-followups.md` for the upstream-contribution status.
- Consumers install it by git URL (`invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`),
  so a push to `main` is a release. Bump `version` in `pyproject.toml` on any stub change so
  `uv lock --upgrade-package invoke-stubs` has something to move to.
