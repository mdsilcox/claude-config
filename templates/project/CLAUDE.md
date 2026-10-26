# <project>: <one line on what it is>

<!-- Keep this under 150 lines. Commands, timings, gotchas and pointers only: Claude can read the
code, so no overviews, file tours, style rules (the formatter handles those) or pasted code. Add a
line only after a real, repeated mistake. Delete these comments. -->

## Must not miss
- Tests in tests/acceptance/ are the spec. Drafts until on main; after that never edited, only retired with `git rm` when a request contradicts them (see the global CLAUDE.md).
- Run the fast check before every commit and paste its summary.

## Commands (dev VM unless marked Windows)
- Fast check (about 20 s; the Stop hook runs it): `uv run pytest tests/unit -q -x && uv run ruff check .`
- Full suite (about 12 min): `uv run pytest`. Run once before a merge, never in a loop.
- Dev server: `uv run uvicorn app.main:app --reload --port 8010` (one port per worktree)
- Windows: `<the build that needs MSVC, .NET or the real game>`

## Gotchas (one line per real mistake, with the fix)
- <...>

## Pointers
- Spec: docs/SPEC.md. Decisions: docs/decisions/.
- Module map and interfaces: docs/architecture.md (read before editing app/services/).

## Compact instructions
Keep the modified-file list, failing test names and the current plan step.
