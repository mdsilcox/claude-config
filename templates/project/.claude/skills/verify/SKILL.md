---
name: verify
description: Run this project's fast check and report the result. Claude Code runs a skill named verify before each commit that changes more than docs or tests.
---

Run the fast check from the project root:

    bash -c "$FAST_CHECK"

- If it passes, say so in one line with its summary, for example "212 passed in 18 s".
- If it fails, fix the failures this change caused and run it again. If a failure predates the change or can't be fixed now, stop and say so plainly. Don't commit over a failure without the owner's say-so.
- Never edit acceptance tests to make them pass.
