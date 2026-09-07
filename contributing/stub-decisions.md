# Why the stubs say what they say

Settled decisions and the options they beat. `AGENTS.md` states the rules; this file is why they are
those rules, so a later session re-opening one starts from what was already measured rather than
from the argument.

Organised by the question you arrive with.

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

A third form of the same thing: a check is only as good as its reach. The attribute check globbed
the stub root, not `**/*.pyi`, so the `parser/` subpackage sat outside every run from the day it
shipped — 19 missing attributes across five classes, found the moment the glob changed. A green
check that cannot see half the package looks identical from the outside to one that can.
