---
status: idea
updated: 2026-09-28
source_repo: github.com-personal/repo-tasks
source_session: 44be2918-1669-4d16-9f77-56535cc6ddeb.jsonl
source_moment: 2026-09-28T11:15:00Z
source_plan:
---

# Sweep to repo-tasks v0.6.0

## Context

repo-tasks v0.6.0 was released 2026-09-28 (tag on `a2d9cf5`, CI/Security/Canary green), and this
machine's global tool is already at v0.6.0. Two of its changes originated here:

- **`pyrightconfig.json` drops `allowedUntypedLibraries: ["invoke"]`.** This repo's own retired plan
  asked for it. The family was checked: nothing imports an invoke module the stubs leave undeclared.
- **uv and gh output is forced plain wherever repo-tasks parses it.** Found from this repo's sweep
  under a Claude Code `FORCE_COLOR=3`, where check-currency dropped every behind entry. The hadolint
  false positive found in the same sweep is fixed too: an excluded latest reads as excluded.

Also in it: `zizmor.yml` disables the `self-repository` audit (actionlint and act reject its fix),
and there are gitflow PR-mode fixes, irrelevant here. The sequence is repo-tasks'
`contributing/consumer-sweep.md`, "The sweep".

## This repo's drift

`inv consumers.diff` from repo-tasks, 2026-09-28:

- **Config files behind: `pyrightconfig.json`, `zizmor.yml`.**
- **Security caller pinned to `9398008`** (v0.5.0), while `security-reusable.yml` was last changed
  at `d17c607`. The file is byte-identical between the two, as this repo's own pin-comment finding
  established. So this is diff noise rather than a real lag. Re-pin to v0.6.0's `a2d9cf5` with
  `# v0.6.0` if `ci.check-actions` should see it current.

## Recommended direction

Run the sweep per the doc. After `configs.pull`, the gate should pass with no
`allowedUntypedLibraries` at all, since this repo is the stubs themselves. A failure here would be
the most informative one in the family.
