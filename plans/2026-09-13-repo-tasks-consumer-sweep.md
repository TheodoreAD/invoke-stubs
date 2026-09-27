---
status: landed
updated: 2026-09-28
depends_on: [repo-tasks]
---

# This repo is a `repo-tasks` consumer, has never been swept, and is the one `ensure-deps` must not touch

Filed 2026-09-13 from a `repo-tasks` session. Nothing was written to this tree — the measurement
below is read-only, run from outside the repo, and no `pull`, `ensure-deps` or lock ran here.

## Why this arrives as a filing rather than as work already done

`repo-tasks` ships four config files and a `repo-tasks-quality` dependency manifest that every
consumer snapshots and then drifts from. Its `plans/2026-08-25-consumer-transitions.md` has tracked
that drift since 2026-08-25. **This repo was never on its list** — not as unswept, but as unknown,
recorded as a consumer for the first time on 2026-09-13 after three successive membership counts
each derived from a path shape that missed it.

The scope question that followed was put to the user and answered on 2026-09-13: **in scope, but
configs-only.** `configs.pull` + `deps.lock` + gate, and **not `configs.ensure-deps`**, for the
reason below — a restriction that the producer-side fix landed later the same day has since made
conditional rather than permanent. Read the whole of the next section before acting on either.

## The `ensure-deps` block, and this repo already knew about it

`repo-tasks-quality` lists `invoke-stubs @ git+https://github.com/TheodoreAD/invoke-stubs`. So
`configs.diff` run here reports `dependency-groups.dev is missing: invoke-stubs` and its next-steps
block prescribes `configs.ensure-deps` — which would splice a dependency on this repo's own git
remote into this repo's dev group.

**That report is a false positive by design, and this repo had already worked it out.** Its
`pyproject.toml` says so at the `[dependency-groups]` block, in a comment that predates the filing:
the entry is "circular: this repo _is_ that package, and taking the published build as a dev
dependency would shadow the working tree under test with whatever `main` last released. Removed by
hand; ensure-deps is additive and will re-add it on the next run."

So the consumer side of this is settled and documented. What is not settled is the producer side:
`repo-tasks`' plan records the same hazard as an open pitfall wanting "either an exclusion in
`ensure_deps` or a documented 'not here'". The answer already exists here; nothing carries it back.

[PITFALL: **the drift report and the drift are not the same thing here, and one command conflates
them.** For every other consumer `configs.diff` exiting 1 on the dev group means "run ensure-deps".
Here one of its named entries means "do not", permanently. A session that reads the next-steps block
and complies has undone a deliberate hand edit, and `deps.lock` then bakes it into the lock. Read
the `[dependency-groups]` comment before acting on that line.]

[DECISION: **fixed in `repo-tasks` the same day, `6f44aec`.** `ensure_deps` and the drift report
both skip the manifest entry naming the project they are running in, and print why rather than
skipping silently. Derived from the project's own `[project] name` against the entry's bare name —
no exclusion list — so this repo needs no per-sweep special case once it is running a `repo-tasks`
new enough to have it. Verified against this tree before the commit: the missing-entry line and the
`configs.ensure-deps` next step are both gone, `ruff.toml` and `pytest.ini` still reported.]

[PITFALL: **the fix does not reach this repo until its own pin moves, which is the last step it
protects.** `repo_tasks` here resolves from this project's lock, pinned at `0c1f31b` (2026-09-06) —
and the global `uv tool` is `v0.3.0`, also older than the fix. So a sweep run today with either one
still prints the old report. The ordering that follows: **the pin bump is step 1, and the
`ensure-deps` caution below applies to every run made before it.** Confirm with `inv configs.diff` —
once the skip line appears instead of `dependency-groups.dev is missing:
invoke-stubs`, the caution
is spent.]

## What it is behind on (measured 2026-09-13, read-only)

The installed `repo-tasks` **v0.3.0** tool's own `configs.diff`, run from a subprocess that chdirs
in — the same tool version used for all three unswept consumers, so the answers are comparable.

| what                    | state                                                                  |
| ----------------------- | ---------------------------------------------------------------------- |
| `ruff.toml`             | behind: the `sys.path` / `site.addsitedir` bans                        |
| `pytest.ini`            | behind: the starlette `anyio` `filterwarnings` ignore                  |
| `pyrightconfig.json`    | **up to date** — `pythonVersion: "3.11"` and `extraPaths` both present |
| `dprint.json`           | **up to date** — plugin checksums present                              |
| `dependency-groups.dev` | reports `invoke-stubs` missing — see above; nothing to do              |

Two config files, and the lightest of the three unswept consumers. `pyrightconfig.json` being
current matters: it means the `c514bd9` hazard — a derived `pythonVersion` moving the type checker
to the declared floor and failing on syntax above it — **is already discharged here**, unlike in
`ingesta`, where it is a live blocker.

## The other half, which no `configs.diff` can see: the task code is 100 commits behind

This repo is a third flavour. It takes `repo-tasks` as its **own dev dependency**
(`repo-tasks @ git+…`), which the family otherwise avoids because the dependency brings `invoke`
with it and a second `inv` on PATH shadows the global tool with one that cannot import `repo_tasks`
— a problem that does not arise here, because `repo_tasks` is in this project's environment. The
`pyproject.toml` comment lays out what that buys: `tasks.py` type-checks with no suppressions, and
the gate runs from this repo's own venv.

The cost is a second lag nothing reports:

| what             | here                                           | current            |
| ---------------- | ---------------------------------------------- | ------------------ |
| `repo-tasks` rev | `0c1f31b8`, 2026-09-06, version `0.2.0`        | `v0.3.0` and later |
| commits behind   | **100** against `origin/main` as of 2026-09-13 | —                  |

`configs.diff` compares config files and manifest entries; it has no opinion about the version of
the package it is running from. So the pin bump is a sweep step here that does not exist for a
global-tool consumer, and per `repo-tasks`' 2026-09-05 walk-through the **bump belongs above
`configs.diff`** — running `diff` first reports drift against the old shipped configs, and a `pull`
then writes them, giving an identical report before and after the bump, which reads as though the
bump changed nothing.

## The sweep, in order

`repo-tasks`' `contributing/consumer-sweep.md` is the authority; this is the per-repo shape.

1. `inv deps.lock --package repo-tasks` to move the pin, then sync. This is the step a global-tool
   consumer does not have, and it goes first.
2. `inv configs.pull`, then read the diff rather than accepting it.
3. **Skip `configs.ensure-deps` until step 1 has actually landed the fix**, which the skip line in
   `configs.diff` is how you tell. Before that it still prescribes splicing this package into its
   own dev group; after it, `ensure-deps` is safe here for the first time. If it is run by reflex on
   an older tool, remove the `invoke-stubs` entry by hand again before locking.
4. `inv deps.lock`, sync, then the gate, whole.

[PITFALL: `requires-python` must exist before pulling `ruff.toml`, because the shipped copy no
longer carries `target-version` and the linter reads the floor from that field instead. It does
exist here (`>=3.11`), so this is a check that passes rather than a blocker.]

## What no diff can tell you, and has to be read

- ~~**Report-mode wiring.**~~ **Does not apply — checked 2026-09-13.** `tasks.py` is
  `from repo_tasks import ns` with no root `Collection` of its own, and `repo_tasks/__init__.py:66`
  already calls `runner.configure(ns)`. Recorded rather than left as a check, because this is the
  item where "the consumer looks fine" is not evidence: an unwired consumer's output is
  byte-identical to a wired one with the variable unset.
- **The security workflow caller.** Not applicable in the usual sense, and the reason is worth its
  own line: **this repo has no `.github/` directory at all** — no CI, no workflows. It does carry a
  `zizmor.yml`, a workflow-linter config with no workflows to lint. So the family's "add a
  `security.yml` calling `security-reusable.yml`" item cannot be done here without first deciding
  whether this repo has CI at all.
- **The packaged-`tests/` decision.** `configs.pull` writes both config halves but cannot decide
  whether this repo wants `__init__.py` files under `tests/`. Stays deliberate.
- **`venv.check` / `venv.recreate`.** Expect a mismatch on first run if either is invoked — uv
  builds the venv with the newest interpreter satisfying the floor. Pre-existing state made visible,
  not something the sweep broke.

## What this predicts

`configs.diff` exits 1 on two config files and on the `invoke-stubs` entry that must be ignored; the
local gate stays green through the pull, since neither drifted file touches a binary a gate step
shells out to and the starlette `anyio` ignore is inert in a repo whose tests do not import
`fastapi.testclient`.

**There is no CI prediction to make**, which is itself the finding: every other consumer's sweep is
validated by a green run afterwards, and here the local gate is the whole of the evidence. The pin
bump is the one step that could surprise — 100 commits of task code arriving at once, against a gate
this repo runs from its own venv rather than from the global tool.

## How the predictions went (swept 2026-09-28, to v0.5.0)

Run as `2026-09-27-sweep-to-repo-tasks-v0-5-0.md`, which folded this one in.

- **"`configs.diff` exits 1 on two config files and the `invoke-stubs` entry": wrong on both counts,
  and for a reason the prediction could not see.** It was three files: `pyrightconfig.json` had
  drifted too, because v0.5.0 rewrote its include comment after 09-13. And the `invoke-stubs` entry
  was not reported at all. It was skipped with a printed reason, because the pin bump came first and
  carried the producer-side fix. That is the order this plan asked for, and it is why the caution
  about `ensure-deps` never came into play: `ensure-deps` ran and skipped the entry.
- **"The local gate stays green through the pull": right.** Green at every intermediate state.
- **"The pin bump is the one step that could surprise": no surprise.** 0.2.0 to 0.5.0, 170 commits
  of task code, and the gate passed on the first run.
- **"`venv.check` mismatches on first run": right.** It reported 3.14 against a declared 3.11, fixed
  by the floor pin in the same session.

## Migrated to

- The `ensure-deps` self-reference: `AGENTS.md` and the `pyproject.toml` dependency-group comment,
  both reworded 2026-09-28 for repo-tasks 0.4.0 and later.
- The missing CI, which made the security-workflow item impossible: an open plan,
  `2026-09-28-whether-this-repo-gets-ci.md`.
- Deliberately not migrated: the packaged-`tests/` decision, which this plan already recorded as
  staying deliberate and which nothing has reopened; the measured-behind table, now superseded; and
  the report-mode wiring check, recorded above as not applying.
