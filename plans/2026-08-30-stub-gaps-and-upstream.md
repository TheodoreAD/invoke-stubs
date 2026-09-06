---
status: idea
updated: 2026-08-30
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

## Open questions

- [DEFERRED: offer the `@task` signature upstream to pyinvoke — the stub's `ParamSpec` overloads for
  `task()` plus an `__all__` (or `import X as X` re-exports) in `invoke/__init__.py`. invoke's `main`
  was unchanged as of 2026-08-25. If a released invoke ever carries it, **this whole distribution is
  deleted outright**, and `repo-tasks`' `repo-tasks-quality` entry with it — which is the whole
  reason it is worth offering rather than maintaining a stub indefinitely.]

[NEEDS CLARIFICATION: is an upstream PR actually wanted, given it means owning a contribution against
a project that has not moved on this? The cheap middle option is opening an issue with the stub as
the proposed shape and letting the maintainers decide, rather than a PR that may sit.]

- [DEFERRED: a `task(klass=..., **kwargs)` overload. invoke's own extension point for task metadata
  is a `Task` subclass plus custom keywords, and the stub types `klass` but has no overload accepting
  the extra keywords that subclass exists to receive — so `@task(klass=Custom, thing=...)` matches
  nothing, `@task` degrades to an untyped decorator, and the decorated function's `.body` becomes
  `Any` with `reportUntypedFunctionDecorator` firing. Measured 2026-08-26 while designing
  `repo-tasks`' `requirements.py`, which routed around it with a separately-typed decorator instead.
  Nothing needs the stub change today; it is recorded because it is the **second** real gap found in
  the stub, which is this plan's own stated trigger for revisiting the upstream question.]

## Recommended direction

Leave both. The upstream one only becomes worth doing if the stub starts needing maintenance; as of
the 08-26 assessment it did not.

Revisit if this distribution grows past the two narrowings it ships today, or if invoke releases
anything touching `tasks.py`'s signatures. The trigger is deliberately "a third gap appears" rather
than a date — two gaps is a stub doing its job, three is a stub becoming a project.
