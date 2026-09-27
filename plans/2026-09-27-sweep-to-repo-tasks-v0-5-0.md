---
status: landed
updated: 2026-09-28
source_repo: github.com-personal/repo-tasks
source_session: bcf810d6-38c7-48d3-adfe-2ff30399d4c9.jsonl
source_moment: 2026-09-27
source_plan:
---

# Sweep to repo-tasks v0.5.0

## Context

`repo-tasks` `v0.5.0` was released 2026-09-27 and this machine's global tool is on it. Run the sweep
as `repo-tasks`' `contributing/consumer-sweep.md`, "The sweep", describes it. The store plan already
filed here, `2026-09-13-repo-tasks-consumer-sweep.md`, is the earlier sweep and may fold into this
one.

What `v0.5.0` adds that this sweep uses:

- `inv deps.check-currency`, run after `inv deps.lock`: which `repo-tasks-quality` entries the lock
  holds behind their latest release. It skips the manifest's own `invoke-stubs` entry here, as
  `configs.diff` and `ensure-deps` already do.
- `inv configs.check-include`: tracked Python no pyright `include` entry covers.
- Also new: `inv dist.check-isolated`, the pin-comment check in `inv ci.check-actions`,
  `inv repo-tasks.status --latest`, `docker.logout`/`helm.logout`, `venv.sync --extra/--group`.

## Evidence

Measured 2026-09-27 from `repo-tasks`' session, read-only in this tree (`git status` clean after),
with the installed `v0.5.0` tool.

**`inv configs.check-include`: clean.** Every tracked `.py` is covered by the shipped globs.

**`inv deps.check-currency`: 6 of 13 manifest entries behind** (13 because its own entry is
excluded). `basedpyright` 1.39.10 (latest 1.40.1), `ruff` 0.16.6 (0.16.9), `shfmt-py` 4.1.0 (4.2.0),
`actionlint-py` 1.7.12.24 (1.7.12.25), `zizmor` 1.30.0 (1.30.1), `hadolint-py` 2.14.0.1 (2.15.1.2).

## Recommended direction

The smallest sweep of the five: run it as documented, take the lags with
`inv deps.lock --package <name>`, and stamp last.

## Outcome

Run 2026-09-28, folding in `2026-09-13-repo-tasks-consumer-sweep.md`, which scores its own
predictions. Commits in order: `6a92376` moves the pin from 0.2.0 to 0.5.0, `772433c` pulls
`ruff.toml`, `pyrightconfig.json` and `pytest.ini` (the other three pulled identical), `7121b0c`
takes five of the six lags, and `4ffb972` updates the docs. `configs.check-include` was clean.
`stamp` is a no-op here, since this repo pins through its lock. The gate and the integration tier
were green on Python 3.11.

Two findings:

- **`hadolint-py` stays at 2.14.0.1.** The dev group excludes 2.15.1.2 (`!=2.15.1.2`), so the sixth
  lag is a deliberate choice.
- **`deps.check-currency` reported "0 of 13 behind" when six were.** The harness shell exports
  `FORCE_COLOR`, uv then colors the `(latest: …)` clause even when piped, and the parser drops every
  colored line. Filed for `repo-tasks` as `2026-09-28-check-currency-misreads-colored-uv-output.md`.
  The lags above came from the raw `uv tree --outdated` output instead.

## Migrated to

- Nothing new for this repo's docs beyond the `AGENTS.md` and `pyproject.toml` rewording in
  `4ffb972`. Both findings are about `repo-tasks`, and the actionable one is filed there.
