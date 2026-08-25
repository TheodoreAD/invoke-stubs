# invoke-stubs

Partial [PEP 561](https://peps.python.org/pep-0561/) type stubs for
[invoke](https://github.com/pyinvoke/invoke). Two things invoke's own inline annotations get wrong
for a strict type checker, fixed without touching anything else:

- `@task` keeps the decorated function's signature. invoke declares
  `task(*args, **kwargs) -> Callable` — a bare `Callable` — so every decorated task is
  `Callable[..., Any]` to its callers (pyright: `reportUntypedFunctionDecorator`, then "partially
  unknown" at every reference). Here `task` is two `ParamSpec` overloads returning
  `Task[Callable[P, R]]`, and `Task.__call__` forwards `P`/`R`.
- `from invoke import task, Context, Result, ...` is a public re-export. invoke's `__init__.py`
  re-exports with `# noqa` imports and no `__all__`, which a typed package's rules read as private
  (pyright: `reportPrivateImportUsage`; mypy `--strict`: `no_implicit_reexport`). The stub's
  `__init__.pyi` uses the `import X as X` form.

`py.typed` says `partial`, so only `invoke.tasks` and the package `__init__` come from here; every
other module resolves to invoke's inline types as before. Works with pyright/basedpyright and mypy.

## Install

```shell
uv add --dev 'invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs'
```

Nothing to configure — type checkers find `invoke-stubs` in site-packages ahead of `invoke` itself.

## Status

Stopgap until invoke carries the same signatures. Delete the dependency once a released invoke
declares `task()` with `ParamSpec` and re-exports its public names as such.
