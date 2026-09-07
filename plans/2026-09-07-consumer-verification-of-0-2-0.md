---
status: idea
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

## Open questions

[NEEDS CLARIFICATION: should `Lexicon` be generic in the stub — `class Lexicon(dict[str, _VT])` with
`__getattr__(self, name: str) -> _VT`, letting `collection.pyi` declare
`collections: Lexicon[Collection]` and `tasks: Lexicon[Task[Any]]`? Both are true of invoke at
runtime: `Collection.add_collection` only ever stores a `Collection` and `add_task` only ever a
`Task`. It would delete every cast this bump cost its one real consumer, and `Lexicon[Collection]`
is subscriptable at runtime anyway, since `dict.__class_getitem__` is inherited — so a stub-only
generic parameter costs nothing that a consumer could trip over.

Against: it is a **third** deliberate departure from what invoke's source says, on top of the two
`__setitem__`/`__exit__` widenings, and this repo's generator would keep reverting it. The
alternative is that consumers cast, which is what `repo-tasks` now does in 14 places — cheap, but it
is the kind of cheap that gets copied into every consumer rather than fixed once.]

[NEEDS CLARIFICATION: is `Lexicon` the right declaration for those two attributes at all, or should
they be `dict[str, Collection]` / `dict[str, Task[Any]]`? That is a smaller change than making
`Lexicon` generic and gets the same win at the two call sites that matter, at the cost of losing
`.aliases_of()`/attribute access on those specific attributes — which no consumer on this machine
uses.]

## Recommended direction

Close item 3 of `2026-08-30-missing-collection-and-context-stubs.md`'s Verification section: the
real consumer gate has now been run against 0.2.0 and is green, so the version is safe to consume.
Item 4 (`ingesta`'s 59 suppressions) is still that repo's session to do, and item 5 (mypy) is
untouched.

Then decide the `Lexicon` question above, ideally before another consumer takes 0.2.0 and writes its
own casts. Either answer is defensible; what is not is leaving it undecided and discovering the
casts have spread.
