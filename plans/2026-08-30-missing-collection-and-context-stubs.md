---
status: planned
updated: 2026-09-06
---

# Every re-exported name but `task` resolves to nothing where invoke itself is absent

## Context

Found 2026-08-30 while adding the first local task module to a consumer repo that takes its tasks
from `repo_tasks` and runs them through the globally installed tool. Re-measured 2026-09-06 against
basedpyright 1.39.10, invoke 3.0.3 and Python 3.11, with two throwaway virtualenvs — one with invoke
installed, one without — and the diagnostics below are that run's, not the original session's.

The package ships `__init__.pyi` and `tasks.pyi`. `__init__.pyi` re-exports from twelve sibling
modules, and only one of them (`.tasks`) exists here:

```
from .collection import Collection as Collection
from .context import Context as Context, MockContext as MockContext
```

With invoke's own source installed, that costs nothing — the checker falls back to it, which is what
`allowedUntypedLibraries: ["invoke"]` in the family's `pyrightconfig.json` is for. Where invoke is
not installed, a consumer importing four names gets **4 errors and 9 warnings**, and with
`failOnWarnings` on every one of them fails the gate.

**The plan's original title was too narrow.** This is not a `Collection`/`Context` problem: `Exit`
fails identically, from `.exceptions`, and so would every other name `__init__.pyi` re-exports.
`task`, `Task`, `Call` and `call` are the only names that work, because `tasks.pyi` is the one
sibling that exists. Anything the stub re-exports from a module it does not ship is broken wherever
invoke is absent, which is precisely the configuration this distribution exists to serve.

[PITFALL: The obvious fix — install invoke in the consumer's own virtualenv — breaks the consumer.
It puts a second `inv` on `PATH` ahead of the globally installed repo-tasks tool, and that one
cannot import `repo_tasks`, so every task in the repo fails at collection load. Measured in one
session: added, `inv` broken, removed. A consumer that takes its task collection from the global
tool therefore _cannot_ have invoke as a dependency.]

[PITFALL: `reportMissingModuleSource` on `import invoke` is irreducible from this side and no
version of this work removes it. It means "a stub was found but the source module was not", which is
the permanent condition of a stubs-only distribution whose runtime is absent — the fully-clean
candidate below still emits it, alone, with everything else resolved. It is the consumer's to
configure, and no amount of stub surface will close it.]

The consumer's suppression burden has grown, which is the argument for acting rather than
documenting. The original note recorded four `# pyright: ignore` comments across two files; the same
five task modules now carry **59** — 11, 7, 7, 5 and 29 — of which exactly one is about `repo_tasks`
rather than invoke. `reportUnnecessaryTypeIgnoreComment` is an error in that config, so whenever
this is fixed the gate flags every stale suppression on its next run: the cleanup is
self-announcing rather than something anyone has to remember.

## Design

The two shapes the original plan posed — separate sibling modules, or inlined declarations in
`__init__.pyi` — were both measured. Neither is free, and they fail differently enough that the
choice is settled rather than a preference.

### 1. Inlining is rejected: it forks class identity

Declaring `class Collection` directly in `__init__.pyi` works where invoke is absent — it took the
probe from 4 errors + 9 warnings to 1 error + 1 warning, and to the irreducible error alone once
`Result` was inlined too. But with invoke **installed** it breaks code that type-checks today:

```
Argument of type "Collection" cannot be assigned to parameter "coll" of type "Collection"
  "invoke.Collection" is not assignable to "invoke.collection.Collection"
```

[DECISION: Inlining is out. The same class reached by two import paths becomes two nominal types,
and the diagnostic names both of them "Collection", which is the worst form the failure could take.
It is not fixable by declaring more — declaring more is what causes it. The control run, pristine
stubs with invoke installed, is clean, so this would be a regression introduced by the fix. Sibling
modules keep one identity and are the shape to build on.]

### 2. A sibling stub must be complete for its own module

`AGENTS.md` already said this. It is now measured rather than asserted: a `collection.pyi` declaring
only `from_module`, `add_task` and `add_collection`, with invoke installed, turns
`Collection.configuration()` — a member `repo-tasks`' own suite calls — into
`Cannot access attribute "configuration" for class "Collection"`. The stub shadows invoke's module
whole; there is no per-member merging.

Rewritten complete for invoke 3.0.3 — all twelve public members, transcribed from invoke's own
inline annotations — the same file is clean in both configurations: it closes every `Collection`
diagnostic where invoke is absent and regresses nothing where it is present.

[DECISION: This is why "which members are worth declaring" stopped being a question. It was posed as
a free choice per class and is not one: shipping a module means declaring all of it. The choice that
remains is *which modules*, and it is a transitive closure rather than a list — `collection` pulls
in `parser` (`to_contexts` returns `ParserContext`) and `tasks`; `context` pulls in `runners`
(`run` returns `Result`), `config` and `watchers`.]

### 3. Go non-partial, and ship all twelve modules

Chosen 2026-09-06 over three narrower options: a consumer-facing subset of five modules (~96
members), a minimal three (~24, leaving `Result` unknown), and leaving the stubs alone.

Measured surface, invoke 3.0.3: 16 submodules, 59 public top-level names, 160 public class members.
The twelve `__init__.pyi` names hold ~143 of those; `tasks.pyi` already covers 9. `program` (35) and
`runners` (49) are the bulk. `runners` is not optional despite nothing importing it directly — both
`Context.run` returning `Result` and `repo-tasks`' own `from invoke.runners import Local` require
it.

[PITFALL: **Non-partial removes the fallback entirely, so the marker flip is the breaking moment and
cannot precede the modules.** With `py.typed` emptied but `config.pyi` and `context.pyi` not yet
written, a consumer that *has* invoke installed loses `Config` and `Context` — names that resolve
fine under `partial`. Confirmed 2026-09-06: two errors and four warnings in the invoke-installed
probe, on imports that were clean a moment earlier. Under `partial` each new module is independently
safe, which is what makes the phasing below work; there is no such safety once the marker is gone.]

Hence two phases, in this order and not the other:

1. **Add every module's `.pyi` while `py.typed` still says `partial`.** Each addition is inert for
   repos that have invoke and closes its own names for repos that do not. Verifiable one file at a
   time.
2. **Empty `py.typed` only once all twelve exist.** `invoke.parser` is a package upstream, so it
   needs a `parser/__init__.pyi` rather than a flat `parser.pyi`.

[DEFERRED: dropping `allowedUntypedLibraries: ["invoke"]` from the family's `pyrightconfig.json`
once phase 2 lands. It is the upside that motivated going this far, but it is a change in four other
repos, each of which has to be re-checked at zero warnings, and none of them is blocked meanwhile.]

[DEFERRED: `invoke.util`, `env`, `completion`, `main` and `vendor` are not re-exported by
`__init__.pyi` and are not covered by phase 1. Nothing in the family imports them, so non-partial
does not strand anything today — but a consumer that later does `from invoke.util import cd` will
find it unresolvable with no fallback, and that is a worse error than today's.]

[UNVERIFIED: the whole design is measured on basedpyright 1.39.10 only. The README claims mypy
support, and mypy's partial-stub and shadowing behaviour was not exercised in any of these runs.]

## Files touched

- `invoke-stubs/collection.pyi`, `context.pyi`, `exceptions.pyi`, `config.pyi`, `runners.pyi`,
  `parser/__init__.pyi`, `program.pyi`, `executor.pyi`, `loader.pyi`, `terminals.pyi`,
  `watchers.pyi` — new, one per module `__init__.pyi` re-exports from, each complete for its module.
- `invoke-stubs/py.typed` — `partial` emptied, in phase 2 and only then.
- `invoke-stubs/__init__.pyi` — unchanged in shape; it already names every module correctly.
- `pyproject.toml` — `version` bump, since consumers install by git URL and a push to `main` is the
  release.
- `AGENTS.md` — "Keep it partial" and the rule beneath it are reversed by this and must be rewritten
  rather than left standing.
- `README.md` — the `py.typed` paragraph and the two-things-fixed framing both describe the partial
  design.

## Verification

The consumer configuration is the test, and it is the one nobody was running: a repo with **invoke
absent** type-checking a task module. Both probes are throwaway virtualenvs, not fixtures in this
repo, since this repo has no suite of its own.

1. Invoke absent, stubs installed: a module importing `Collection`, `Context`, `Exit` and `task` and
   calling `Collection.from_module`, `add_task` and `c.run` reports **only**
   `reportMissingModuleSource`. Baseline for comparison is 4 errors + 9 warnings.
2. Invoke installed, stubs installed: the same module, plus `Collection.configuration()` and
   `from invoke.collection import Collection`, reports nothing at all. This is the regression test
   for both rejected shapes — it is what inlining and partial-module stubs each break.
3. `repo-tasks`' `inv quality.type-check` stays at zero, per this repo's `AGENTS.md`. It is the only
   consumer with a real suite, and it has invoke installed, so it exercises case 2 and not case 1.
4. `ingesta`'s gate after the stale suppressions are removed — `reportUnnecessaryTypeIgnoreComment`
   is an error there, so it will name every one of the 59 that is no longer needed. That count going
   to near-zero is the outcome measure for the whole plan.
