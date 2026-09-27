---
status: idea
updated: 2026-09-07
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

[UNVERIFIED: that the parameterised form type-checks clean against this repo's own suite — it was
read off the consumer's report rather than tried here, since this session had no business editing
this repo. `contributing/stub-decisions.md`'s own rule applies: put the defect back and watch which
check fires, then fix it and watch that check pass.]

A second, smaller one from the same report, listed because it is the same class of thing and one
line away: `create_io_threads` (`runners.pyi:36`) returns
`tuple[dict[Callable[..., Any], ExceptionHandlingThread], list[str], list[str]]`, and a bare
`Callable[..., Any]` is partially unknown for the same reason. It did not reach `repo-tasks`'
report, since nothing there calls it — so it is worth fixing only if this repo's own completeness
check looks at it.

## Open questions

[NEEDS CLARIFICATION: is `Promise` the only unparameterised generic base in the distribution, or is
this one instance of a class of gap? A grep for base classes that take type arguments —
`AbstractContextManager`, `Generic`, the `dict`/`list` subclasses — would answer it in one pass, and
the answer decides whether this is a one-line fix or a check worth adding beside the attribute
comparison that already runs.]

## Recommended direction

Parameterise the base class, then re-run the consumer's report as the outcome measure: `repo-tasks`'
`inv quality.verify-types` should print 100% for `repo_tasks`, since this is the only remaining
source of unknowns there. That makes the fix's effect visible outside this repo, which the attribute
checks here cannot show.
