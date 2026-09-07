# invoke-stubs

Partial [PEP 561](https://peps.python.org/pep-0561/) type stubs for
[invoke](https://github.com/pyinvoke/invoke). Three things invoke's own inline annotations get wrong
for a strict type checker:

- `@task` keeps the decorated function's signature. invoke declares
  `task(*args, **kwargs) -> Callable` — a bare `Callable` — so every decorated task is
  `Callable[..., Any]` to its callers (pyright: `reportUntypedFunctionDecorator`, then "partially
  unknown" at every reference). Here `task` is two `ParamSpec` overloads returning
  `Task[Callable[P, R]]`, and `Task.__call__` forwards `P`/`R`.
- `from invoke import task, Context, Result, ...` is a public re-export. invoke's `__init__.py`
  re-exports with `# noqa` imports and no `__all__`, which a typed package's rules read as private
  (pyright: `reportPrivateImportUsage`; mypy `--strict`: `no_implicit_reexport`). The stub's
  `__init__.pyi` uses the `import X as X` form.
- Every re-exported name resolves **without invoke installed**. That is the configuration these
  stubs exist for — a repo whose `inv` comes from a globally installed tool cannot have invoke in
  its own virtualenv, because a second `inv` on `PATH` shadows that tool's entry point. Before 0.2.0
  only `task` worked there; `Collection`, `Context`, `Exit` and the rest were
  `reportAttributeAccessIssue`, because `__init__.pyi` re-exported them from sibling modules the
  package did not ship.

`py.typed` says `partial`. Every module `__init__.pyi` re-exports from is declared here, plus
`util`; `env`, `completion`, `main` and invoke's vendored packages still resolve to invoke's inline
types. Works with pyright/basedpyright; mypy is untested.

One diagnostic is not fixable from this side: with invoke absent, `import invoke` is
`reportMissingModuleSource` — "a stub was found but the source module was not", which is the
permanent condition of a stubs-only distribution whose runtime is not installed. Set that rule to
`none` in the consumer, or suppress it at the import.

## Install

```shell
uv add --dev 'invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs'
```

Nothing to configure — type checkers find `invoke-stubs` in site-packages ahead of `invoke` itself.

## Status

Stopgap until invoke carries the same signatures. Delete the dependency once a released invoke
declares `task()` with `ParamSpec` and re-exports its public names as such.
