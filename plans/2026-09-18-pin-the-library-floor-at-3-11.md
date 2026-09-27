---
status: idea
updated: 2026-09-18
source_repo: github.com-personal/repo-tasks
source_session: 14237e4b-3a66-4207-8a3a-882552c86680.jsonl
source_moment: 2026-09-18T09:40:00Z
source_plan: plans/2026-08-29-python-floor-in-the-shipped-configs.md
---

# This repo is library tier and develops two minor versions above its own floor

## Context

The family's Python version tiers were settled 2026-09-18; the rules are
`scaffoldapy/plans/2026-09-18-python-version-tier-rules.md` (in the store until that repo absorbs
it). This repo is **library tier**, by the most direct test there is: it is a `repo-tasks-quality`
manifest entry, spliced into every consumer's `dependency-groups.dev` as
`invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`, and therefore resolved into other
projects' environments. Its floor is their floor.

The tier's settings are `requires-python = ">=3.11"`, `.python-version` of `3.11`, a dev venv on
3.11, and a CI matrix starting at 3.11.

## Evidence

Measured read-only 2026-09-13 across the personal account:

| declared `requires-python` | `.python-version` | actual `.venv` |
| -------------------------- | ----------------- | -------------- |
| `>=3.11`                   | **absent**        | **3.14.5**     |

So the declaration is right and nothing holds the development environment to it. Seven of the nine
personal Python repos were in that state; `repo-tasks` is the only one that has been corrected, and
its correction is the worked example — `inv venv.pin`, `inv venv.recreate`, and its full gate green
on 3.11.15.

[PITFALL: **a declared floor nothing runs at is not a tested floor.** The same measurement across
the family found three repos whose code used `typing.override` (3.12+, PEP 698) under a declared
3.11 floor, two of them in code shipped in a wheel, all three green because the type checker and the
test suite were agreeing about an interpreter neither had been asked to check. Expect this repo to
turn up something similar rather than to move cleanly.]

## Recommended direction

1. `inv venv.pin` — write `.python-version` from the declared floor rather than by hand.
2. `inv venv.recreate` — rebuild `.venv` on 3.11.
3. `inv quality.precommit` — and read whatever it now says, because this is the first time anything
   here will have run at the floor.
4. Check the CI matrix starts at 3.11, and add the upper versions only if the type-stub content
   genuinely varies by interpreter.

[PITFALL: **steps 1–2 do not hold while `UV_PYTHON` is exported machine-wide.** It outranks
`.python-version` entirely, so a bare `uv run` or `uv sync` here rebuilds the venv at 3.14 and the
pin silently stops meaning anything. Filed for `power-user-linux-setup` as
`2026-09-13-uv-python-defeats-every-library-floor.md`. Do this after that lands, or expect to redo
it.]

[PITFALL: this repo is also the one consumer that is itself a `repo-tasks-quality` entry, so
`configs.ensure-deps` would splice it into its own dev group. Closed producer-side 2026-09-13 in
`repo-tasks` `6f44aec`, which skips the manifest entry naming the project it is running in — but
only for a consumer whose installed `repo-tasks` carries that commit. The skip line in
`configs.diff` output is how to tell.]
