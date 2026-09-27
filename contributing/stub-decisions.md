# Why the stubs say what they say

Settled decisions and the options they beat. `AGENTS.md` states the rules; this file is why they are
those rules, so a later session re-opening one starts from what was already measured rather than
from the argument.

Organised by the question you arrive with.

## Why ship a `.pyi` per module rather than declare the classes in `__init__.pyi`?

Because inlining forks class identity, and the fork shows up where invoke **is** installed — the
configuration that was clean before.

Both shapes were measured in 2026-09, on basedpyright 1.39.10 and invoke 3.0.3, with invoke absent
in one virtualenv and installed in the other. Declaring `class Collection` directly in
`__init__.pyi` fixed the invoke-absent case: 4 errors and 9 warnings down to the one irreducible
`reportMissingModuleSource`. With invoke installed, it broke code that type-checked the day before:

```
Argument of type "Collection" cannot be assigned to parameter "coll" of type "Collection"
  "invoke.Collection" is not assignable to "invoke.collection.Collection"
```

One class reached by two import paths becomes two nominal types, and the diagnostic calls both of
them `Collection`, so it is about as hard to read as the failure could be. Declaring more cannot fix
it, because the extra declarations are the cause. Sibling modules keep one identity.

**Shipping a module means declaring all of it.** A `.pyi` shadows invoke's module whole, and members
are not merged. A `collection.pyi` holding only `from_module`, `add_task` and `add_collection`
turned `Collection.configuration()`, which `repo-tasks`' suite calls, into
`Cannot access attribute "configuration"`. So the real question was which modules to ship, and the
answer is a transitive closure rather than a list. `collection` needs `parser`, since `to_contexts`
returns `ParserContext`. `context` needs `runners` for `Result`, plus `config` and `watchers`.
`runners` and `exceptions` need `util`. The closure stops at `util`: its `Lexicon`, and `parser`'s
`ParseMachine`, are **declared** here rather than imported from invoke's vendored packages. Neither
forks an identity, because the vendored paths are not shipped and so nothing else resolves them.

What that bought, measured in the one consumer carrying the suppressions: it took 0.3.0 and deleted
71 of them, and the only invoke-related diagnostic left is `reportMissingModuleSource`.

## Why does `py.typed` still say `partial`?

The plan was to empty it once every re-exported module existed. It went the other way when that was
tested.

**The benefit it was supposed to bring had already arrived.** Going non-partial was meant to let
consumers drop `allowedUntypedLibraries: ["invoke"]`. With the modules shipped, the marker still
`partial` and that setting removed, a consumer probing the whole surface (`Collection`, `Config`,
`Context`, `MockContext`, `Result`, `UnexpectedExit`, `Local`, `.body`) came back with 0 errors and
0 warnings. The modules made the stubs authoritative. The marker had nothing to do with it.

**And emptying it has a cost.** In that same environment, `from invoke.env import Environment`
type-checks under `partial` and becomes `reportMissingImports` under a non-partial marker, because
`env` is not shipped and nothing is left to fall back to. That one import is the whole visible
difference between the two markers. Avoiding it would mean declaring `env`, `completion`, `main`,
`__main__`, `_version` and the vendored packages, including vendored yaml, the largest thing in the
distribution. All that work would only remove an error that emptying the marker created.

It is also why the order mattered back when non-partial was still the plan. **Under `partial`, each
new module is safe on its own**, because anything not yet shipped falls back to invoke. With the
marker emptied before `config.pyi` and `context.pyi` existed, a consumer with invoke installed lost
`Config` and `Context`: two errors and four warnings on imports that had been clean a moment before.

mypy 2.3.1 `--strict` reads the marker and the module shadowing the same way, so this does not rest
on one checker's reading of PEP 561. `tests/integration/test_mypy_integration.py` keeps that true.

## Why is `Lexicon` generic when invoke's is a bare `dict`?

Because the alternative is that every consumer casts, and casts spread.

invoke's vendored `Lexicon` subclasses `dict` with no value type, so `ns.collections["build"]` is
`Any`. The first consumer to take 0.2.0 — `repo-tasks`, the only one with a real suite — hit **37
`reportAny` errors** on that alone, all on `ns.collections["<name>"]` lookups, and closed them with
`cast(Collection, ...)` in 14 places. That is cheap per site and self-perpetuating: nothing flags a
redundant cast once the stub improves, so the next consumer copies the shape rather than noticing it
is unnecessary.

**The option it beat** was declaring the two `Collection` attributes as plain
`dict[str, Collection]` and `dict[str, Task[Any]]`. Smaller change, same win at the two call sites
that actually hurt. Two things ruled it out:

- `Lexicon`'s attribute access (`ns.collections.build`) and `.aliases_of()` are real members of the
  runtime object, and a `dict` declaration makes valid code fail. That is the same argument that
  widened `DataProxy.__setitem__` to `Any` rather than transcribing invoke's `str` — a stub that
  rejects working code is worse than one that diverges from upstream's annotation.
- The value type is equally knowable at four further sites (`ParserContext.args` and `.flags`,
  `Program.args`, `Parser.contexts`, `ParseMachine.contexts`), so the `dict` answer would have to be
  taken again at each. One generic parameter answers all six.

**What it costs, accepted:** a fourth deliberate departure from invoke's source, which a
regeneration reverts. Hence the comment in `util.pyi` and the list in `AGENTS.md` — the comment
stops a regeneration reverting it silently, the list is what someone weighing a _fifth_ departure
reads.

The homogeneity claim is checked, not assumed: in invoke 3.0.3's own source, `add_task` only ever
stores a `Task`, `add_collection` only ever a `Collection`, and `ParserContext.args[main] = arg`
only ever an `Argument`. Read from the source, because the annotations are the thing under
suspicion.

## How do I prove a stub change actually fixed something?

Not by calling the thing. **`Any` satisfies every call and every annotated assignment**, so a probe
written the way a consumer would use the API passes against the exact defect it was written for. A
usage case doing `ns.collections["x"].configuration()` was green before and after the fix.

Use `assert_type`, and then confirm the check by breaking it: putting `Lexicon[Any]` back produced
three diagnostics — two `assert_type` mismatches and the `reportAny` that cost the consumer its
casts — which is what shows the probe is testing the property you think it is.

That is the general rule behind two of this repo's tests, and it has been learned twice here. The
other time, an attribute-parity check shipped comparing declarations by substring, so
`Result.exited` matched an identically-named `__init__` parameter and a deleted attribute read as
present; three other checks caught the defect it was written for, and it did not. **A check nobody
has seen fail is a check nobody has tested.**

A probe written from what consumers use tests the names you thought of. `from invoke import Failure`
shipped broken in the first release with the full module set. invoke's `__init__.py` re-exports it
from `.runners`, although `.exceptions` defines it, and the generated `runners.pyi` did not carry
it. That name got worse: before, it resolved by falling back to invoke's real `runners`, and after,
it failed with invoke installed or absent. No hand-written probe listed it. That is why the
re-export tests generate their list by parsing `__init__.pyi`.

And a probe has to run in an environment built for that run. The first non-partial measurement
reported 6 errors and 27 warnings, and every one came from a virtualenv whose stub files had been
swapped by hand a dozen times. `uv pip install --reinstall-package` did not clean it, and a diff of
the one file under suspicion came back identical. In a fresh virtualenv, with the same package and
the same marker, there were 0 errors. The integration tier builds its virtualenvs fresh for this
reason.

A third form of the same thing: a check is only as good as its reach. The attribute check globbed
the stub root, not `**/*.pyi`, so the `parser/` subpackage sat outside every run from the day it
shipped — 19 missing attributes across five classes, found the moment the glob changed. A green
check that cannot see half the package looks identical from the outside to one that can.
