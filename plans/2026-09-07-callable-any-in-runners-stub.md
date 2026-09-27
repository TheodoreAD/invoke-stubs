---
status: landed
updated: 2026-09-28
source_repo: github.com-personal/repo-tasks
source_session: 52905ee0-50ff-4376-bd19-5ab4d9ca0a24.jsonl
source_moment: 2026-09-07T15:18:45Z
---

# `Promise`'s bare `AbstractContextManager` is the last unknown a consumer sees

## Context

`repo-tasks` ran a quality pass over its own package 2026-09-07 and took type completeness from
92.7% to 99.1% by annotating what its own code left inferable. What is left is not its to fix: every
remaining unknown in `basedpyright --verifytypes repo_tasks` comes from this distribution, through
`repo_tasks.runner.ReportingLocal`, which subclasses `invoke.runners.Local`.

Nothing is blocked. `verify_types` is a report in that repo and deliberately not a gate step, so
this is about the number being explainable rather than about anything failing.

## Evidence

Run in `repo-tasks` at 99.1%, against invoke-stubs 0.3.0 (`f70ff01`) and basedpyright 1.39.10:

```
invoke.runners.Local
   error: Type of base class "invoke.runners.Runner" is partially unknown
invoke.runners.Runner.make_promise
  .../invoke-stubs/runners.pyi:35:9 - error: Return type is partially unknown
    Return type is "Promise"
invoke.runners.Promise
   error: Type of base class "contextlib.AbstractContextManager" is partially unknown
```

The chain is one declaration deep. `runners.pyi:120` is:

```python
class Promise(Result, AbstractContextManager):
```

`AbstractContextManager` is generic, so unparameterised it is `AbstractContextManager[Unknown]` —
which makes `Promise` partially unknown, then `make_promise`'s return type, then `Runner`, then
`Local`, then every consumer subclassing it. One type argument closes all five lines.

`Promise.__enter__` already declares `-> Promise` right below it, so the argument the base class
wants is the one the stub has already committed to:

```python
class Promise(Result, AbstractContextManager["Promise"]):
```

Verified 2026-09-28, the way `contributing/stub-decisions.md` asks. With `reportMissingTypeArgument`
turned on in the stub self-check, the check fired on this line and nowhere else. It passed once the
base became `AbstractContextManager[Promise, None]`, and the whole integration tier, mypy included,
stayed green.

A second, smaller one from the same report, listed because it is the same class of thing and one
line away: `create_io_threads` (`runners.pyi:36`) returns
`tuple[dict[Callable[..., Any], ExceptionHandlingThread], list[str], list[str]]`, and a bare
`Callable[..., Any]` is partially unknown for the same reason. It did not reach `repo-tasks`'
report, since nothing there calls it — so it is worth fixing only if this repo's own completeness
check looks at it.

## Open questions

Whether `Promise` was the only unparameterized generic base: it was. `reportMissingTypeArgument`
over every stub reported exactly one diagnostic. The answer was both a one-line fix and a check
worth keeping: the rule now runs in `test_the_stub_package_is_internally_consistent`, so the next
bare generic fails there instead of in a consumer's completeness report.

## Recommended direction

Parameterise the base class, then re-run the consumer's report as the outcome measure: `repo-tasks`'
`inv quality.verify-types` should print 100% for `repo_tasks`, since this is the only remaining
source of unknowns there. That makes the fix's effect visible outside this repo, which the attribute
checks here cannot show.

## Outcome

Shipped in 0.3.1 (`1c4a806`). The original repro was re-run 2026-09-28 in a scratch virtualenv
outside `repo-tasks`, holding `repo-tasks` v0.5.0 from its tag and nothing written to its tree.
`basedpyright --verifytypes repo_tasks`, which is what its `quality.verify-types` runs, gave
**99.3%** against the published 0.3.0 stubs. That is the same five-line chain from `ReportingLocal`
to `Promise`, and 99.3 rather than 99.1 because `repo-tasks` itself moved since the filing. Against
0.3.1 it gave **100%**, and it exited 0, which `--verifytypes` does only at full completeness.
`repo-tasks` sees it once its lock takes 0.3.1.

`create_io_threads`' `Callable[..., Any]` was left alone. It is a fully parameterized `Callable`,
`reportMissingTypeArgument` does not flag it, and it contributes nothing to the 100%.

## Migrated to

- The check: `tests/integration/test_consumer_integration.py`, whose docstring says why the rule is
  on and what it would have caught.
- The fix: `invoke-stubs/runners.pyi`, where the type arguments are the ones `__enter__` and
  `__exit__` already declare, so there is no departure to comment.
- Deliberately not migrated: the evidence block, which is the consumer's report at 0.3.0 and is now
  history.
