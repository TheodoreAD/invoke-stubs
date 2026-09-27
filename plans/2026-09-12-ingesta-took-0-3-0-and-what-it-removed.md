---
status: landed
updated: 2026-09-12
---

# The consumer took 0.3.0, and it removed 71 suppressions rather than 59

## Context

`plans/2026-08-30-missing-collection-and-context-stubs.md` carries a deferral naming this as the
outcome measure and leaving it to the consumer's own session:

> [DEFERRED: removing `ingesta`'s 59 suppressions. They are in another repo, so they are that repo's
> session to make, and `reportUnnecessaryTypeIgnoreComment` will name each one on its next gate run
> after it takes 0.2.0.]

That session ran on 2026-09-12, straight to **0.3.0 (`f70ff01`)** on the advice filed for it. Filed
back here rather than edited in, because writing to another repository from a session that does not
own it is out — so this is the measurement, and whoever works in this repo next can fold it into
that plan and close the deferral.

## What it measured

|                                                      |                   |
| ---------------------------------------------------- | ----------------- |
| suppressions the deferral predicted                  | 59                |
| **rules `reportUnnecessaryTypeIgnoreComment` named** | **71**            |
| lines carrying a suppression, before                 | 80                |
| lines carrying a suppression, after                  | 33                |
| gate after removing them                             | green, 1174 tests |

Spread across five task modules — `tasks/web.py` (44), `tasks/catalogue.py` (8), `tasks/dev.py` (8),
`tasks/__init__.py` (6), `tasks/telegram.py` (5).

**The 59 was an undercount rather than a wrong count**, and the difference is the interesting part:
it was taken before that repository's task modules grew a browser-driving tier, so `tasks/web.py`
alone now accounts for more than half the total. A prediction about a consumer's suppression burden
ages in the direction of more.

## What the removals actually were

Three shapes, all of them what the stub distribution was for:

- `Context` imported under `TYPE_CHECKING` no longer needs
  `reportAttributeAccessIssue, reportUnknownVariableType`.
- A task signature `def example(c: Context, ...)` no longer needs `reportUnknownParameterType`.
- `c.run(...)` no longer needs `reportUnknownVariableType, reportUnknownMemberType` — the result is
  typed, which is the `Result` work landing where a consumer can feel it.

`reportMissingModuleSource` on `from invoke import task` **stays**, which matches what that plan
already predicts: it is the consumer's to carry, alone, with everything else resolved.

## The 0.2.0 cost did not appear here

The consumer plan filed for that repository warned that 0.2.0 turned a silenced `Unknown` into a
loud `reportAny` at every `Collection.collections[...]` lookup, and cost `repo-tasks` sixteen casts
before 0.3.0's generic `Lexicon` removed them again.

**No file in that repository indexes a collection's members**, so it went from 0.1.0 to 0.3.0 with
neither the cost nor the fix. Worth recording as a negative result: the 0.2.0 → 0.3.0 churn was a
`repo-tasks`-shaped problem rather than a general consumer one, which is a point in favour of the
advice that sent this consumer straight to 0.3.0.

## What is left

Fold the numbers above into the deferral in
`plans/2026-08-30-missing-collection-and-context-stubs.md` and close it. Nothing else is owed: the
consumer's lock is bumped, its suppressions are deleted, and the two landed in one commit because
neither passes a gate without the other.

## Migrated to

- `plans/2026-08-30-missing-collection-and-context-stubs.md`, verification item 4: the 59 → 71 count
  and why it grew, 80 → 33 lines, the three removal shapes, the surviving
  `reportMissingModuleSource`, and the 0.2.0 negative result. Its `DEFERRED` on the consumer's
  suppressions is closed there.
- Not migrated: the per-module breakdown beyond `tasks/web.py`, which describes the consumer rather
  than this repo, and "sixteen casts" for `repo-tasks`' 0.2.0 cost — this repo's own measurement,
  verification item 3, says 14, and that is the figure kept.
