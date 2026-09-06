---
status: in-progress
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

### 3. Ship all twelve modules — and, as chosen at the time, go non-partial

**Half of this was superseded within the hour by section 4: the modules shipped, the marker did
not.** The reasoning is kept because it is what the shipped work was built on, and because the
measurements in it are still the ones that justify the module set.

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
   needs a `parser/__init__.pyi` rather than a flat `parser.pyi`. — **Withdrawn; see section 4.**

**Phase 1 landed 2026-09-06**, and two things about it were wrong in the paragraphs above.

`util` is not optional and was not a phase-2 concern: `runners` and `exceptions` take
`ExceptionHandlingThread`/`ExceptionWrapper` from it and `program` takes `Lexicon`, so it shipped
with phase 1 as a twelfth module. Its `Lexicon` is **declared** rather than imported from
`.vendor.lexicon`, which stops the closure before it reaches invoke's vendored libraries — the same
call was made for `ParseMachine`, whose vendored `StateMachine` base is dropped. Neither forks an
identity the way inlining did, because the vendored paths are not shipped and so have no second
resolution to disagree with.

[PITFALL: **`basedpyright --createstub` emits methods, properties and class-level names, and
silently drops every attribute a class assigns to `self`.** A generated `runners.pyi` looked
complete and had no `Result.exited`, `.stdout` or `.stderr` — the attributes every consumer of a
`c.run(...)` result actually reads. It surfaced only because the probe read `result.exited`; a stub
reviewed by eye would have passed. 47 attributes across 13 classes were missing, recovered by
walking invoke's own AST for `self.<name> =` and typing each from the matching `__init__`
parameter. Any future regeneration needs that pass, and `--createstub` run in a virtualenv that
also holds *this* package stubs these files rather than invoke's.]

### 4. Phase 2 should not happen — its premise did not survive being tested

Measured 2026-09-06, immediately after phase 1 landed and before writing any phase-2 stub.

**The upside phase 2 was chosen for is already delivered.** Dropping
`allowedUntypedLibraries: ["invoke"]` was the reason to go non-partial. With the `partial` marker
still in place, phase 1's modules, and that setting removed from the checker config, a consumer
exercising the whole surface — `Collection`, `Config`, `Context`, `MockContext`, `Result`,
`UnexpectedExit`, `Local`, `assert_type(ns, Collection)`, the `.body` declaration — is clean: 0
errors, 0 warnings. The setting is redundant now, and flipping the marker is not what made it so.

**And the flip has a cost with nothing on the other side of it.** In the same clean environment,
`from invoke.env import Environment` type-checks under `partial` and becomes
`reportMissingImports` under a non-partial marker, because `env` is not shipped and there is no
longer anything to fall back to. That is the whole observable difference between the two markers
once phase 1 exists: the same consumer code, one hard error worse.

Closing that gap means declaring `env`, `completion`, `main`, `__main__`, `_version` and invoke's
vendored packages — including its vendored yaml, by far the largest thing in the distribution — to
buy back a diagnostic that only appears because the marker was flipped.

[DECISION: Stay `partial`, permanently. The two-phase plan was written when the marker looked like
what made the stubs authoritative; the measurement says the *modules* do that and the marker only
removes a fallback that is currently working. Phase 2 is therefore not deferred pending effort — it
is withdrawn, and `py.typed` keeps saying `partial` as a positive choice rather than a stepping
stone.]

[PITFALL: **A site-packages directory that has been hand-edited across several experiments stops
being evidence, and says so in no way at all.** The first non-partial run in this session reported 6
errors and 27 warnings, including a hit on the `repo-tasks` contract assertion, and it was entirely
an artifact of a probe venv whose stub files had been swapped by hand a dozen times — `uv pip
install --reinstall-package` did not clear it, and a diff of the one file suspicion fell on came
back identical. A fresh virtualenv, same package, same marker: 0 errors. Any result that would
change a decision gets re-run in a venv built for that run.]

[DEFERRED: dropping `allowedUntypedLibraries: ["invoke"]` from the family's `pyrightconfig.json`.
Now unblocked rather than waiting on phase 2 — but it is a change in four other repos, each of which
has to be re-checked at zero warnings, and none of them is blocked meanwhile.]

`env`, `completion`, `main` and the vendored packages stay undeclared, and under a `partial` marker
that costs nothing — they resolve to invoke's inline annotations exactly as before. Section 4 below
records why that is now the end state rather than a phase-2 backlog.

[DEFERRED: removing `ingesta`'s 59 suppressions. They are in another repo, so they are that repo's
session to make, and `reportUnnecessaryTypeIgnoreComment` will name each one on its next gate run
after it takes 0.2.0.]

[UNVERIFIED: the whole design is measured on basedpyright 1.39.10 only. The README claims mypy
support, and mypy's partial-stub and shadowing behaviour was not exercised in any of these runs.]

## Files touched

Done in phase 1:

- `invoke-stubs/collection.pyi`, `config.pyi`, `context.pyi`, `exceptions.pyi`, `executor.pyi`,
  `loader.pyi`, `program.pyi`, `runners.pyi`, `terminals.pyi`, `util.pyi`, `watchers.pyi` and
  `parser/` (`__init__.pyi`, `argument.pyi`, `context.pyi`, `parser.pyi`) — new, each complete for
  its module.
- `invoke-stubs/__init__.pyi` — unchanged in shape, as expected; only its header comment, which
  claimed everything but `.tasks` fell through to invoke.
- `ruff.toml` — new, and not foreseen above. The generated modules are unreadable unformatted, and
  `combine-as-imports` is needed or the sorter splits `__init__.pyi`'s re-export block one name per
  line. There is no gate in this repo, so it records the formatting rather than enforcing it.
- `pyproject.toml` — `version` 0.1.0 to 0.2.0, since consumers install by git URL and a push to
  `main` is the release.
- `AGENTS.md`, `README.md` — the "keep it partial" rule and the two-things-fixed framing both
  described the old design.

Not touched, and now deliberately not:

- `invoke-stubs/py.typed` — stays `partial`. See design section 4.

## Verification

The consumer configuration is the test, and it is the one nobody was running: a repo with **invoke
absent** type-checking a task module. Both probes are throwaway virtualenvs, not fixtures in this
repo, since this repo has no suite of its own.

1. **Passing.** Invoke absent, stubs installed: a module importing `Collection`, `Context`, `Exit`
   and `task` and calling `Collection.from_module`, `add_task`, `c.run` and `result.exited` reports
   **only** `reportMissingModuleSource`. Baseline was 4 errors + 9 warnings.
2. **Passing.** Invoke installed, stubs installed: the same module, plus `Collection.configuration()`
   and `Collection` reached through both `invoke` and `invoke.collection`, reports nothing at all.
   This is the regression test for both rejected shapes.
3. **Not run, and owed.** `repo-tasks`' `inv quality.type-check` is the only consumer with a real
   suite. Running it means installing an unreleased build into that repo's virtualenv, which is not
   a session working here doing it. What was done instead: its `tests/unit/test_types.py`
   assertions — `assert_type(ns, Collection)` and the `Callable[[Context], None] = <task>.body`
   declaration — were mirrored into probe 2 and pass there. That covers the contract but not the
   real suite, so the version bump should not be consumed there until someone runs it in that repo.
4. **Not run.** `ingesta`'s gate after its 59 suppressions are removed, which is likewise that
   repo's session to do. `reportUnnecessaryTypeIgnoreComment` is an error there, so its next gate
   run after taking 0.2.0 names every suppression that is now stale. That count going to near-zero
   is the outcome measure for the whole plan.
5. **Not run.** mypy, per the `UNVERIFIED` tag above.
