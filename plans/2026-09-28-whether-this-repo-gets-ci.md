---
status: idea
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

[NEEDS CLARIFICATION: is CI worth running for a stubs-only package whose whole gate takes about 7
seconds locally? For: the integration tier's claims (invoke present or absent, basedpyright and mypy
agreeing) would be checked on every push rather than whenever someone remembers, and the security
workflow item could be done. Against: one sole contributor who always runs the gate before pushing,
and one more thing to keep current across the family.]

## Recommended direction

If yes: the smallest workflow that runs `inv quality.precommit` and `inv test.integration` on 3.11,
plus the family's `security.yml` caller, set up by the repo-tasks tooling rather than written by
hand.
