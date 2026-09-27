---
status: landed
updated: 2026-09-28
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
this is fixed the gate flags every stale suppression on its next run: the cleanup is self-announcing
rather than something anyone has to remember.

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
remains is _which modules_, and it is a transitive closure rather than a list — `collection` pulls
in `parser` (`to_contexts` returns `ParserContext`) and `tasks`; `context` pulls in `runners` (`run`
returns `Result`), `config` and `watchers`.]

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
written, a consumer that _has_ invoke installed loses `Config` and `Context` — names that resolve
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
walking invoke's own AST for `self.<name> =` and typing each from the matching `__init__` parameter.
Any future regeneration needs that pass, and `--createstub` run in a virtualenv that also holds
_this_ package stubs these files rather than invoke's.]

### 4. Phase 2 should not happen — its premise did not survive being tested

Measured 2026-09-06, immediately after phase 1 landed and before writing any phase-2 stub.

**The upside phase 2 was chosen for is already delivered.** Dropping
`allowedUntypedLibraries: ["invoke"]` was the reason to go non-partial. With the `partial` marker
still in place, phase 1's modules, and that setting removed from the checker config, a consumer
exercising the whole surface — `Collection`, `Config`, `Context`, `MockContext`, `Result`,
`UnexpectedExit`, `Local`, `assert_type(ns, Collection)`, the `.body` declaration — is clean: 0
errors, 0 warnings. The setting is redundant now, and flipping the marker is not what made it so.

**And the flip has a cost with nothing on the other side of it.** In the same clean environment,
`from invoke.env import Environment` type-checks under `partial` and becomes `reportMissingImports`
under a non-partial marker, because `env` is not shipped and there is no longer anything to fall
back to. That is the whole observable difference between the two markers once phase 1 exists: the
same consumer code, one hard error worse.

Closing that gap means declaring `env`, `completion`, `main`, `__main__`, `_version` and invoke's
vendored packages — including its vendored yaml, by far the largest thing in the distribution — to
buy back a diagnostic that only appears because the marker was flipped.

[DECISION: Stay `partial`, permanently. The two-phase plan was written when the marker looked like
what made the stubs authoritative; the measurement says the _modules_ do that and the marker only
removes a fallback that is currently working. Phase 2 is therefore not deferred pending effort — it
is withdrawn, and `py.typed` keeps saying `partial` as a positive choice rather than a stepping
stone.]

[PITFALL: **A site-packages directory that has been hand-edited across several experiments stops
being evidence, and says so in no way at all.** The first non-partial run in this session reported 6
errors and 27 warnings, including a hit on the `repo-tasks` contract assertion, and it was entirely
an artifact of a probe venv whose stub files had been swapped by hand a dozen times —
`uv pip
install --reinstall-package` did not clear it, and a diff of the one file suspicion fell on
came back identical. A fresh virtualenv, same package, same marker: 0 errors. Any result that would
change a decision gets re-run in a venv built for that run.]

[DEFERRED: dropping `allowedUntypedLibraries: ["invoke"]` from the family's `pyrightconfig.json`.
Now unblocked rather than waiting on phase 2 — but it is a change in four other repos, each of which
has to be re-checked at zero warnings, and none of them is blocked meanwhile.]

`env`, `completion`, `main` and the vendored packages stay undeclared, and under a `partial` marker
that costs nothing — they resolve to invoke's inline annotations exactly as before. Section 4 below
records why that is now the end state rather than a phase-2 backlog.

Removing `ingesta`'s suppressions was deferred to that repo's own session, and it happened
2026-09-12 on 0.3.0: 71 rather than 59, one commit, gate green. Verification item 4 has the numbers.

The design was measured on basedpyright 1.39.10 only until 2026-09-07, when mypy 2.3.1 `--strict`
was run over the same probe sources in both environments and reported no issues in either — so mypy
honours the `partial` marker and the module shadowing the same way, and section 4's decision does
not rest on one checker's reading of PEP 561. It is a test now
(`tests/integration/test_mypy_integration.py`) rather than a claim in the README, because the next
mypy release is what the measurement cannot speak for.

### 5. What reviewing the shipped stubs found

Phase 1 was verified by two probes written around what a consumer imports, and both passed. Reading
the files afterwards found four defects none of them could reach, which is the argument for the
three mechanical checks now in Verification below.

[PITFALL: **A probe written from what consumers use tests the names you thought of.** The worst of
the four was `from invoke import Failure`, broken outright: invoke's `__init__.py` re-exports
`Failure` from `.runners` although it is defined in `.exceptions`, and the generated `runners.pyi`
did not carry it. Phase 1 therefore made that name _worse_ — it used to resolve where invoke was
installed, by falling back to invoke's real `runners`, and after phase 1 it failed in both
configurations. The check that catches this class of thing costs nothing and is now step 2: import
every name `__init__.pyi` re-exports, generated from that file rather than hand-listed.]

The other three, each caught by reading and then confirmed against a consumer:

- **`Promise.__exit__` did not satisfy `AbstractContextManager`.** invoke annotates `exc_value` as a
  bare `BaseException`, but a `with` block that raises nothing passes `None`. Widened, and found by
  type-checking the stub package against itself, which nothing had done.
- **Bare `PathLike` resolves as `PathLike[Unknown]`**, so `c.cd(Path(...))` produced
  `reportUnknownMemberType` in the consumer — a warning, and therefore a gate failure under
  `failOnWarnings`. Parameterized to `PathLike[str]` in `config.pyi` and `context.pyi`.
- **`DataProxy.__setitem__` rejected `config["timeout"] = 30`**, faithfully, because invoke
  annotates `value: str` while the runtime takes anything.

[DECISION: That last one is widened to `Any` rather than transcribed. Mirroring upstream is the
default and the rest of the distribution does it, but this package exists precisely because invoke's
annotations are wrong in places, and a stub that rejects valid code is worse than one that diverges.
It is commented in place as a deliberate departure so a regeneration does not quietly revert it —
the only such departure so far.]

`program.pyi` and `loader.pyi` also imported their types from the package `__init__`, the way
invoke's own modules do, which makes `__init__` import `Program` and `Program` import `__init__`.
Pyright resolved it, but the cycle buys nothing in a stub and both now import from the defining
module.

## Files touched

Done in phase 1:

- `invoke-stubs/collection.pyi`, `config.pyi`, `context.pyi`, `exceptions.pyi`, `executor.pyi`,
  `loader.pyi`, `program.pyi`, `runners.pyi`, `terminals.pyi`, `util.pyi`, `watchers.pyi` and
  `parser/` (`__init__.pyi`, `argument.pyi`, `context.pyi`, `parser.pyi`) — new, each complete for
  its module.
- `invoke-stubs/__init__.pyi` — unchanged in shape, as expected; only its header comment, which
  claimed everything but `.tasks` fell through to invoke.
- `ruff.toml` — new, and not foreseen above. The generated modules are unreadable unformatted, so
  the repo needed a config recording their formatting rather than enforcing it. Written here with
  `combine-as-imports`, to keep `__init__.pyi`'s re-export block one statement; **replaced
  2026-09-07 (9ae87d0) by the family's canonical config**, pulled with `inv configs.pull`, which has
  no such setting. The sorter now splits that block into one `from X import (Y as Y,)` per name.
  That is cosmetic and deliberate rather than a regression: the redundant alias survives, so every
  name stays a public re-export, which the unit tier asserts.
- `checks/verify.py`, `checks/usage_probe.py` — new, and not foreseen either. The repo had no gate
  because it has no runtime code, which is why phase 1's defects reached a commit; these were the
  four checks from section 5 made re-runnable at the next invoke bump. **Both deleted 2026-09-07
  (073c0d1)**, reimplemented as the two-tier pytest suite under `tests/` — same checks, see
  Verification.
- `pyproject.toml` — `version` 0.1.0 to 0.2.0, since consumers install by git URL and a push to
  `main` is the release.
- `AGENTS.md`, `README.md` — the "keep it partial" rule and the two-things-fixed framing both
  described the old design.

Not touched, and now deliberately not:

- `invoke-stubs/py.typed` — stays `partial`. See design section 4.

## Verification

The consumer configuration is the test, and it is the one nobody was running: a repo with **invoke
absent** type-checking a task module. Both probes are throwaway virtualenvs; they were scratchpad
scripts when this was written, and are now the `venv_with_invoke` / `venv_without_invoke` fixtures
in `tests/integration/conftest.py`.

1. **Passing.** Invoke absent, stubs installed: a module importing `Collection`, `Context`, `Exit`
   and `task` and calling `Collection.from_module`, `add_task`, `c.run` and `result.exited` reports
   **only** `reportMissingModuleSource`. Baseline was 4 errors + 9 warnings.
2. **Passing.** Invoke installed, stubs installed: the same module, plus
   `Collection.configuration()` and `Collection` reached through both `invoke` and
   `invoke.collection`, reports nothing at all. This is the regression test for both rejected
   shapes.

The three added after section 5 now live in the pytest suite rather than in a scratchpad — they were
`checks/verify.py` for one day and became `tests/` in 073c0d1 — and are each mechanical rather than
written from imagination. Where each one is: 2a is `test_the_stub_package_is_internally_consistent`,
2b the whole of `tests/unit/test_reexports.py` plus
`test_every_reexported_name_resolves_without_invoke_installed`, 2c the `USAGE_PROBE` in
`tests/integration/test_consumer_integration.py`, 2d
`tests/integration/test_attributes_integration.py`.

2a. **Passing.** Type-check the stub package against itself, `include`-ing the `invoke-stubs`
directory as source. This is what found `Failure` and `Promise.__exit__`, and it is the cheapest of
the three — no venv, no consumer, one config file.

2b. **Passing, both configurations.** Import every name `__init__.pyi` re-exports — 42 of them,
generated by parsing that file so the list cannot drift from it. Clean with invoke installed; only
`reportMissingModuleSource` without.

2c. **Passing.** Call into the classes the consumer probes only named — `Config`, `Program`,
`Executor`, `FilesystemLoader`, `Parser`, `ParserContext`, `Argument`, `Responder`,
`FailingResponder`, `Local` — plus the edge cases the review turned up (`config["timeout"] = 30`,
`c.cd(Path(...))`, `Config(project_location=Path(...))`).

2d. **Passing.** Compare each stub class against the attributes invoke assigns to `self`, which is
the generator gap from section 5 turned into a standing check: it also catches an invoke release
adding an attribute to a class already stubbed here.

[PITFALL: **A check written to catch a known defect has to be shown failing on it.** 2d shipped
broken — it tested declaration by substring, so `Result.exited` matched the identically-named
`__init__` parameter one indent level deeper and a deleted attribute read as present. It was caught
by putting two known defects back into `runners.pyi` and watching which checks fired: three did, and
the one written specifically for that defect did not. It parses both sides now, and follows base
classes so `warned_about_pty_fallback`, declared once on `Runner`, is not reported against `Local`.
The negative test is the point — a check nobody has seen fail is a check nobody has tested.]

3. **Run 2026-09-07, and passing — but it cost the consumer 14 casts.** `repo-tasks`'
   `inv quality.type-check` is the only consumer with a real suite, and a session working in that
   repo took 0.2.0 and ran it: 37 `reportAny` errors first, all on `ns.collections["<name>"]`, then
   15 gate steps green and 616 tests passing once those lookups took `cast(Collection, ...)`. What
   this section originally recorded — that its `tests/unit/test_types.py` assertions were mirrored
   into probe 2 and pass there — covered the contract but not the suite, which is exactly the gap
   that showed up. The `Lexicon` question that raised is settled and shipped in 0.3.0; why it went
   that way rather than to a plain `dict` is `contributing/stub-decisions.md`. Reported by the
   now-retired `plans/2026-09-07-consumer-verification-of-0-2-0.md`.
4. **Run 2026-09-12, and passing — the outcome measure for the whole plan.** `ingesta` went straight
   from 0.1.0 to 0.3.0 in its own session, and `reportUnnecessaryTypeIgnoreComment` named **71**
   stale rules, not the 59 predicted: a browser-driving tier had been added to its task modules
   since the count, and `tasks/web.py` alone held 44. Suppressed lines went 80 → 33, removed in one
   commit with the lock bump, gate green on 1174 tests. What they were is what this plan was for —
   `Context` under `TYPE_CHECKING`, `c: Context` task parameters, and `c.run(...)` results now
   typed. Re-read 2026-09-28 in its `tasks/`: every suppression left is the irreducible
   `reportMissingModuleSource` from the pitfall in Context, the `repo_tasks` import (unresolvable
   there by design) plus four `ns.add_collection` lines downstream of it, or unrelated `typer` and
   `telethon` calls. **None is attributable to these stubs.** Also a negative result: the 0.2.0
   `Collection.collections[...]` cost that took `repo-tasks` 14 casts did not appear, since nothing
   there indexes a collection's members — the 0.2.0 → 0.3.0 churn was `repo-tasks`-shaped, not
   general. Reported by the now-retired
   `plans/2026-09-12-ingesta-took-0-3-0-and-what-it-removed.md`.
5. **Run 2026-09-07, and passing.** mypy 2.3.1 `--strict`, both environments, no issues — and a test
   in the integration tier rather than a one-off, per the paragraph replacing the `UNVERIFIED` tag
   in section 4.

2e. **Passing, and it found 19 missing attributes.** 2d globbed the stub root, so `parser/` was
outside every run above; recursive, it reported `ParserContext` missing six attributes, `Argument`
nine, and the three parser classes four more. Declared in 0.3.0. The check was right and its reach
was not, which is a different failure from the one the pitfall above records and reads identically
from the outside: both are a green check that proves less than it appears to.

## Migrated to

- `contributing/stub-decisions.md`, "Why ship a `.pyi` per module rather than declare the classes in
  `__init__.pyi`?": the inlining rejection and its class-identity diagnostic, why shipping a module
  means declaring all of it, the transitive closure and where it stops, and the consumer's
  71-suppression outcome (verification item 4).
- Same file, "Why does `py.typed` still say `partial`?": section 4's measurement both ways, the
  `invoke.env` cost of emptying the marker, why the modules had to come before any marker flip, and
  mypy agreeing.
- Same file, "How do I prove a stub change actually fixed something?": the `Failure` re-export
  pitfall, and the one about a hand-edited site-packages that stopped being evidence.
- `AGENTS.md` already had, and keeps: the `--createstub` gap for `self` attributes, the
  invoke-in-the-consumer-venv pitfall, and the four departures from upstream, including
  `DataProxy.__setitem__`, `Promise.__exit__` and `PathLike[str]` from section 5. `README.md`
  already had the irreducible `reportMissingModuleSource`. The self-test (2a), the re-export tests
  (2b), the usage probe (2c) and the attribute checks (2d and 2e) are the test suite, which already
  says what each one covers.
- The live `DEFERRED` on dropping `allowedUntypedLibraries: ["invoke"]` is filed for `repo-tasks`,
  which owns the canonical config, as `2026-09-28-drop-the-invoke-untyped-library-allowance.md` in
  its store mirror.

Deliberately not migrated: the surface counts (16 submodules, 59 names, 160 members), which were
true of invoke 3.0.3 and are a verification log rather than a reason; the Files-touched list, which
is in git; and the `program.pyi`/`loader.pyi` import cycle, now fixed in code, where each imports
from the defining module.
