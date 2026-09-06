---
status: idea
updated: 2026-09-07
---

# The two known stub gaps, and whether any of this goes upstream

Filed from a `repo-tasks` session, 2026-08-30. Both items were carried in that repo's
`plans/2026-08-26-typing-followups.md`, which also held a third item about one of its own test
fixtures; that one was already resolved in code and the plan is retired there. These two are about
this repo, so they come here.

Neither blocks anything. Both would **delete** code if they land, which is the unusual property worth
keeping in view: this repo exists to be deleted eventually.

## Context

The 2026-08-25 type-checking rollout got `repo-tasks` and `power-user-linux-setup` to zero warnings
with `failOnWarnings: true` family-wide, on the back of this distribution. Two things were
consciously scoped out at the time and were still true as of 2026-08-26.

### The trigger fired, 2026-09-06

This plan set its own revisit condition: "if this distribution grows past the two narrowings it
ships today", with "a third gap appears" as the tell — "two gaps is a stub doing its job, three is a
stub becoming a project."

**It grew from 2 modules to 16 in one session**, declaring every module `__init__.pyi` re-exports
from plus `util`, and in doing so found three further places where invoke's own annotations are
wrong rather than merely absent:

- `DataProxy.__setitem__` annotates `value: str` while the runtime takes anything, so
  `config["timeout"] = 30` is rejected.
- `Promise.__exit__` annotates `exc_value: BaseException`, which does not satisfy
  `AbstractContextManager` — a `with` block that raises nothing passes `None`.
- `Task.__call__` returns `T`, the wrapped callable, rather than the callable's return value.

That is five gaps, not three. See `2026-08-30-missing-collection-and-context-stubs.md` section 5.

### And upstream moved, in a way that changes the question

The open question below assumes "a project that has not moved on this". Measured 2026-09-07 from
PyPI's release index and the GitHub API, that is no longer true:

- **invoke is active again.** 3.0.0 through 3.0.3 all shipped 2026-04, after roughly two years of
  near-silence (2.2.0 in 2023-07, then 2.1.4/2.2.1 in 2025-10). Still no `Typing ::` classifier and
  still no `py.typed`.
- **v3 added typing to `tasks.py`, and got it wrong.** `Task` is now `Generic[T]` with
  `T = TypeVar("T", bound=Callable)` — but `task()` is still `(*args: Any, **kwargs: Any) ->
  Callable`, so nothing ever parameterizes `Task[T]`, and `Task.__call__` returns `T` instead of the
  return type. Both are exactly what this distribution's `tasks.pyi` already fixes.
- **Three users filed that as bugs in 2026** — pyinvoke #1061 (04-07), #1067 (04-26), #1073 (06-08)
  — with one comment between them and no visible maintainer engagement.
- **The re-export half already has an open PR**: #981, "Explicitly re-export names from top-level
  package using `__all__`", open since 2024-01 and last touched 2026-04.
- **So does one of the gaps found today**: #1081 (2026-08-10) fixes `DataProxy.__setitem__`,
  independently and identically to the widening applied here.

The case for contributing is therefore stronger and the case against is unchanged in shape but now
quantified: the maintainers ship typing but do not engage on typing reports quickly, and a typing PR
has sat for over two years.

## Open questions

- [DEFERRED: offer the `@task` signature upstream to pyinvoke — the stub's `ParamSpec` overloads for
  `task()` plus an `__all__` (or `import X as X` re-exports) in `invoke/__init__.py`. invoke's `main`
  was unchanged as of 2026-08-25. If a released invoke ever carries it, **this whole distribution is
  deleted outright**, and `repo-tasks`' `repo-tasks-quality` entry with it — which is the whole
  reason it is worth offering rather than maintaining a stub indefinitely.]

[NEEDS CLARIFICATION: issue, PR, or neither? Deliberately left open 2026-09-07 — the evidence was
gathered and the decision deferred, rather than the question being unanswerable.

Its original premise is gone: this is no longer a contribution "against a project that has not moved
on this", it is a contribution against a project that moved, shipped `Task[Generic[T]]` that cannot
bind because `task()` still returns a bare `Callable`, and has three unanswered reports about it.
This repo holds a tested fix for two of the three.

What is genuinely undecided is appetite, and the three options price differently. An **issue** costs
one write-up, no ownership, and ties #1061/#1067/#1073 to a concrete shape. A **PR** is the only
route that ever deletes this distribution — but #981, which does the `__all__` half, has been open
since 2024-01. **Neither** stays defensible: nothing here is blocked, and the stub is verified.

Whichever is chosen, nothing is posted to a third-party tracker without the text being reviewed
first.]

- [DEFERRED: a `task(klass=..., **kwargs)` overload. invoke's own extension point for task metadata
  is a `Task` subclass plus custom keywords, and the stub types `klass` but has no overload accepting
  the extra keywords that subclass exists to receive — so `@task(klass=Custom, thing=...)` matches
  nothing, `@task` degrades to an untyped decorator, and the decorated function's `.body` becomes
  `Any` with `reportUntypedFunctionDecorator` firing. Measured 2026-08-26 while designing
  `repo-tasks`' `requirements.py`, which routed around it with a separately-typed decorator instead.
  Re-confirmed verbatim 2026-09-07 against invoke 3.0.3 and basedpyright 1.39.10: "No overloads for
  `task` match the provided arguments", then `reportUntypedFunctionDecorator`, then `.body` as
  `Any`. Still nothing needs it.]

## Recommended direction

**The "leave both" recommendation below was written when the trigger had not fired. It has now** —
five gaps rather than two, and an upstream that has moved. The reasoning is kept because it is what
the deferral rested on, and because the second item's conclusion is unchanged.

`klass=`: still leave it. Nothing in the family uses a `Task` subclass, and the workaround in
`repo-tasks` is a separately-typed decorator that costs nothing to keep.

Upstream: no longer obviously "leave". The shape that fits what was found is the cheap middle option
this plan already named — an issue rather than a PR — but pointed at something specific now: invoke
v3's own `Task[T]` is unusable because `task()` does not parameterize it, three people have reported
that, and this repo has a tested implementation of the fix. Whether to spend the effort is a
judgement about appetite for owning a contribution, not about whether the gap is real.

The original text, for the record: *"Leave both. The upstream one only becomes worth doing if the
stub starts needing maintenance; as of the 08-26 assessment it did not. Revisit if this distribution
grows past the two narrowings it ships today, or if invoke releases anything touching `tasks.py`'s
signatures. The trigger is deliberately 'a third gap appears' rather than a date — two gaps is a stub
doing its job, three is a stub becoming a project."*
