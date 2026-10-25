---
name: verify
description: Run the project's fast check (FAST_CHECK) and report the result. Claude Code runs a skill named verify before each commit that changes more than docs or tests.
---

From the project root, run the fast check:

    bash -c "$FAST_CHECK"

If `FAST_CHECK` is empty or unset, run the checks the project's CLAUDE.md names instead. If it names none, say so in one line and carry on.

- If it passes, say so in one line with its summary, for example "212 passed in 18 s".
- If it fails, fix the failures this change caused, then run it again. If a failure predates the change or can't be fixed now, say so plainly. Don't commit over a failure without the owner's say-so.
- Never edit acceptance tests to make them pass.
