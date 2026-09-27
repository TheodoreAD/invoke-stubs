---
status: landed
updated: 2026-09-28
---

# Whether this repo gets CI

## Context

This repo has no `.github/` directory, so it has no CI and no workflows. A push to `main` is a
release, because consumers install it by git URL, so the local gate and integration tier are the
only evidence behind every release. It does carry a `zizmor.yml`, a workflow-linter config that the
shared configs pull in, with no workflows to lint.

Found in the 2026-09-13 consumer-sweep plan, retired 2026-09-28: the family's sweep item "add a
`security.yml` calling `security-reusable.yml`" cannot be done here until this question is answered,
and every other consumer's sweep is checked by a green CI run afterwards, which this one cannot be.

## Open questions

Whether CI is worth running for a stubs-only package whose whole gate takes about 7 seconds locally:
yes, the user decided 2026-09-28, asking that it be built from the family's prior art. For: the
integration tier's claims (invoke present or absent, basedpyright and mypy agreeing) are checked on
every push rather than whenever someone remembers, and the security workflow item can be done.
Against, and accepted: one more thing to keep current across the family.

## Outcome

Built 2026-09-28 and green on its first push (`763c099`): CI run 36353747515 passed 54 unit and 20
integration tests on 3.11.16 in 27s, and Security run 36353748531 passed.

- **`ci.yml`** follows the scaffoldapy template's shape. The one change is taken from
  power-user-linux-setup, the other repo that pins repo-tasks in its own lock: a
  `.github/ci-bootstrap.sh` that syncs `.venv` and lets `dev-env.setup` put it on `GITHUB_PATH`, in
  place of the template's `bootstrap-repo-tasks.sh`. It runs `inv quality.check`, the read-only half
  CI runs everywhere in the family, rather than `quality.precommit` as recommended above. It adds
  `concurrency` and `timeout-minutes` from repo-tasks' own `ci.yml`. It uses one interpreter,
  because stub content does not vary by the checker's interpreter.
- **`security.yml`** is the family caller, pinned to the v0.5.0 commit rather than the family's
  `d17c607`. The workflow file is identical between the two, but the family's `# 2026-08-31` comment
  predates repo-tasks' tags and the new pin-comment check reports it as untrue. Filed for
  `repo-tasks` as `2026-09-28-security-pin-date-comments-now-read-as-untrue.md`.
- `ci.check-actions` flagged `setup-uv` v10.0.1 as behind, so it is at v10.2.0, one minor ahead of
  the rest of the family.
- The job ran locally first with `inv test.workflows --job quality` (act, 163s, passed).
- "Set up by the repo-tasks tooling": no such task exists (`inv --list ci` has only `check-actions`
  and `status`), so the files were written from the template by hand.

## Migrated to

- The workflows themselves, whose comments carry each decision above.
- `AGENTS.md`, Build & test: what CI runs, and `inv test.workflows` for local runs.
- Deliberately not migrated: the run annotations, a setup-uv cache race between the two simultaneous
  first runs, and GitHub's notice that `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. The
  notice applies to the whole family, not to this repo.
