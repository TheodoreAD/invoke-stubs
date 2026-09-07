---
status: landed
updated: 2026-09-07
source_repo: github.com-personal/repo-tasks
source_session: 52905ee0-50ff-4376-bd19-5ab4d9ca0a24.jsonl
source_moment: 2026-09-07T11:15:05Z
---

## Context

`plans/2026-08-30-missing-collection-and-context-stubs.md` closes with four things not run, the
third of them: "**Not run, and owed.** `repo-tasks`' `inv quality.type-check` is the only consumer
with a real suite... the version bump should not be consumed there until someone runs it in that
repo."

That session ran, in `repo-tasks`, 2026-09-07. This file reports what it found, so the plan there
can be closed out by a session working in this repo — nothing in this repo was touched.

## Evidence

Session transcript `52905ee0-50ff-4376-bd19-5ab4d9ca0a24.jsonl` under
`~/.claude/projects/-home-tdumitrescu-projects-github-com-personal-repo-tasks/`, 2026-09-07,
starting from the user's "we just finished upgrading the invoke stubs, continue any plans we had for
that to integrate with this repo".

What was run there, in order:

1. `inv deps.lock --package invoke-stubs` — "Updated invoke-stubs v0.1.0 (ad052ca2) -> v0.2.0
   (13bcc9ee)".
2. `inv venv.sync`, then `inv quality.type-check` — **37 errors**, all `reportAny`, all in
   `tests/unit/test_init.py`, all on `ns.collections["<name>"]` lookups and what they feed.
3. After the fix below, `inv quality.precommit` — 15 steps green, basedpyright 0 errors 0 warnings,
   616 unit tests passed.

The cause, and the only consumer-visible cost of 0.2.0 found:

- `collection.pyi` declares `collections: Lexicon`, and `util.pyi` declares
  `class Lexicon(dict[str, Any])`, so `ns.collections["quality"]` is `Any`.
- Under 0.1.0 that attribute fell through to invoke's own untyped vendored `Lexicon`, where the same
  lookup was `Unknown | None` — probed directly in that session against invoke 3.0.3 and
  basedpyright 1.39.10:

  ```
  from invoke.vendor.lexicon import Lexicon
  value = Lexicon()["quality"]        # Type of "value" is "Unknown | None"
  ```

- `repo-tasks`' tests tier sets every `reportUnknown*` to `none` and keeps `reportAny` an error, so
  the honest type is the one that fails the gate. The `assert x is not None` each of those tests
  carried was narrowing the old `| None`, not defensive noise.

Fixed consumer-side, no change asked of this repo: the 14 lookups took
`cast(Collection, ns.collections["<name>"])`, the shape `tests/unit/test_cli.py` in that repo
already used for the identical lookup. Committed there as "Take invoke-stubs 0.2.0, and cast the
lookups it made honest", with the pitfall written into that repo's `contributing/type-checking.md`.

Nothing else moved: no suppression in `repo-tasks` became stale
(`reportUnnecessaryTypeIgnoreComment` is an error there and the gate is green), and `runner.py`'s
`reportImplicitOverride` ignore is still needed for a reason that has nothing to do with the stubs
(`typing.override` lands in 3.12, that package's floor is 3.11).

## The decision, 2026-09-07

[DECISION: `Lexicon` is generic in the stub — `class Lexicon(dict[str, _VT])`, `__getattr__` and
`__setattr__` in `_VT` — and every site holding one names its value type: `Collection.collections`
as `Lexicon[Collection]`, `Collection.tasks` as `Lexicon[Task[Any]]`, `ParserContext.args`/`.flags`
and `Program.args` as `Lexicon[Argument]`, `Parser.contexts` and `ParseMachine.contexts` as
`Lexicon[ParserContext]`. Shipped in 0.3.0.

It beat declaring the two `Collection` attributes as plain `dict[str, Collection]` /
`dict[str, Task[Any]]`, which is the smaller change and gets the same win at the two call sites that
matter. Two things decided it. Attribute access — `ns.collections.build` — and `.aliases_of()` are
real members of the runtime object, and a `dict` declaration makes valid code fail, which is the
same argument that widened `DataProxy.__setitem__` rather than transcribing it. And a `dict` would
have to be decided again for `ParserContext.args`, `Program.args` and `Parser.contexts`, where the
value type is equally knowable; the generic parameter answers all six at once.

Against, and accepted: it is a fourth deliberate departure from invoke's source, and a regeneration
reverts it. That is what the in-place comment and `AGENTS.md`'s list of departures are for. The
homogeneity claim is not an assumption — `add_task` only ever stores a `Task`, `add_collection` only
ever a `Collection`, `ParserContext.args[main] = arg` only ever an `Argument`, checked against
invoke 3.0.3's source rather than inferred from its annotations.]

[PITFALL: **a probe that calls the value proves nothing about an `Any`.** `Any` satisfies every call
and every annotated assignment, so a usage case exercising `ns.collections["x"].configuration()`
would have passed against the old bare-`dict` declaration exactly as it does against the fix. The
probe cases use `assert_type`, and were confirmed by putting `Lexicon[Any]` back and watching three
diagnostics return — two `assert_type` mismatches and the `reportAny` that cost the consumer its
casts.]

## What is left

[DEFERRED: `repo-tasks`' 14 `cast(Collection, ns.collections["<name>"])` are unnecessary once it
takes 0.3.0, and nothing there will say so: `reportUnnecessaryTypeIgnoreComment` is an error in that
repo and catches a stale `# pyright: ignore`, but a redundant `cast` is not a suppression and no
rule flags it. So this is a deliberate pass in that repo rather than something its gate announces —
filed there as its own plan.]

Item 4 of `2026-08-30-missing-collection-and-context-stubs.md`'s Verification (`ingesta`'s 59
suppressions) is still that repo's session to do. Item 5 (mypy) is closed: run 2026-09-07, clean in
both environments, and a test in the integration tier since.
