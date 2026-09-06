---
status: idea
updated: 2026-08-30
---

# `Collection` and `Context` resolve to nothing where invoke itself is absent

## Context

Found 2026-08-30 while adding the first local task module to a consumer repo that takes its tasks
from `repo_tasks` and runs them through the globally installed tool.

The package ships `__init__.pyi` and `tasks.pyi`. The `__init__.pyi` re-exports from siblings that
do not exist:

```
from .collection import Collection as Collection
from .context import Context as Context, MockContext as MockContext
```

With invoke's own source installed, that costs nothing — the checker falls back to it, which is what
`allowedUntypedLibraries: ["invoke"]` in the family's `pyrightconfig.json` is for. **Where invoke is
not installed, the same import is three diagnostics**: `reportMissingModuleSource` on the module,
`reportAttributeAccessIssue` on the name, and `reportUnknownVariableType` on its type. With
`failOnWarnings` on, every one of them fails the gate.

[PITFALL: The obvious fix — install invoke in the consumer's own virtualenv — breaks the consumer.
It puts a second `inv` on `PATH` ahead of the globally installed repo-tasks tool, and that one
cannot import `repo_tasks`, so every task in the repo fails at collection load. Measured in one
session: added, `inv` broken, removed. A consumer that takes its task collection from the global
tool therefore _cannot_ have invoke as a dependency, which is exactly the configuration these stubs
have to serve.]

The consumer worked around it with four `# pyright: ignore` comments across two files, each naming
its rule and pointing here. `reportUnnecessaryTypeIgnoreComment` is an error in that config, so
whenever this is fixed the gate will flag those suppressions on its next run — the cleanup is
self-announcing rather than something anyone has to remember.

## Open questions

[NEEDS CLARIFICATION: Whether to ship real `collection.pyi` and `context.pyi`, or to inline the
declarations into `__init__.pyi` and stop re-exporting from modules that are not there. Inlining is
smaller and closes the hole immediately; separate modules match invoke's real layout and leave room
for the rest of its surface. Depends on how far "partial" is meant to go, which the README states as
a deliberate scope rather than a stage.]

[NEEDS CLARIFICATION: Which members are worth declaring. `Collection` needs `from_module`,
`add_collection` and `add_task` for a consumer that builds a namespace; `Context` needs `run` and
its `Result`. Anything beyond that is speculative until a consumer wants it.]

## Recommended direction

Close the re-export hole, and take the two or three members a consumer's `tasks/` package actually
touches while doing so. The test that matters is not "does the stub import" but a consumer repo with
**invoke absent** type-checking a small task module cleanly — that is the configuration where these
stubs are the only source of truth, and it is the one nobody has been checking.
