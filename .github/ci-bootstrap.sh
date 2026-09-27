#!/usr/bin/env bash
set -euo pipefail

# CI's equivalent of `inv dev-env.setup` after a fresh clone, and the one place a raw `uv` call is
# unavoidable, since there is no `inv` to bootstrap with yet. This repo pins repo-tasks in its own
# uv.lock rather than taking the global tool, so there is no bootstrap-repo-tasks.sh to run: `uv run`
# syncs .venv from the lock and runs `inv dev-env.setup` inside it, and repo-tasks' venv.py appends
# .venv/bin to GITHUB_PATH, so every later step is a bare `inv <task>`. Same shape as
# power-user-linux-setup's .github/ci-bootstrap.sh, the other repo that pins repo-tasks this way.

command -v uv > /dev/null 2>&1 || {
  echo "uv not found on PATH — install uv first" >&2
  exit 1
}
uv run inv dev-env.setup
