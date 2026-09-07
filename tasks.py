"""Dogfoods the same quality tasks every other repo in the family gets — see README.md.

Unlike every other consumer, repo-tasks is a dev dependency here rather than only the globally
`uv tool install`ed tool, so this import resolves and `ns` is typed — no suppressions. The family's
usual reason for keeping it out is that it brings invoke with it and a second `inv` on PATH shadows
the global tool with one that cannot import `repo_tasks`; that one can, because repo-tasks is in
this project's own environment.

It also means this repo type-checks its own `tasks.py` through the stubs it ships, which is the
narrowest possible dogfood of the thing being distributed."""

from repo_tasks import ns

__all__ = ["ns"]
