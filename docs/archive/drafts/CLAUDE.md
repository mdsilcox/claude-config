# Global instructions

## Project context file (every project)

Every project has a project-level `CLAUDE.md` at its root: the shared context that the main agent and every subagent read instead of exploring the codebase. Subagents load it automatically, so it is the cheapest way to onboard them.
- **Create it** when starting work in a project that lacks one (before delegating anything): stack and commands (run, test), directory layout, a services/modules index with the key functions and signatures to call, UI and code conventions (with the one file to copy for each pattern), content rules, how tests fake external services, and where plans and decisions live. Aim for a few hundred lines at most; index and point, don't paste code. Status and progress belong in PROGRESS.md or the milestones doc, not here.
- **Keep it current**: update it at every phase gate or whenever architecture, conventions or key interfaces change, in the same commit. A stale context file is worse than none.

## Delegating to subagents

For independent, well-scoped tasks (a single feature, a page, a test suite, a self-contained refactor), spin up subagents on a lower model, Sonnet 5.5 (`model: "sonnet"`), and run independent ones in parallel. Keep the work that needs judgment yourself: architecture, prompts, cross-cutting design and final review.

- **Start agents from the templates in `~/.claude/agents/`** (pass it as `subagent_type`): `lane-builder` for build lanes, `test-porter` for porting acceptance tests before launch, `browser-checker` for the phone and desktop check after hand-back, `art-reviewer` for every batch of integrated art before the owner sees it, `researcher` for read-only research. The templates carry the model, the shared-tree rules, the time-box, the test-loop rule, the self-check list and the report format, so a brief states only the task. If a template doesn't fit, use `general-purpose` with `model: "sonnet"` and copy those rules into the brief.
- **Parallelize only independent work**, split by shared interfaces, not by file lists; three or four lanes is the usual sweet spot. A chain of dependent steps goes to one agent in order.
- **Review every agent's result before committing**: tests, the diff, and the UI in the browser at 375px and desktop width; score it; send one improvement round to the same agent (SendMessage).
- **Load the `orchestration` skill before planning lanes, writing a lane brief, reviewing a hand-back or touching the Orchestra board.** It holds the full rules: lane naming and coupling, briefs and their "Assumptions and decisions" section, contracts before launch, reuse of existing work, time-boxing and fan-out, the review checklist and scoring, test-loop limits, and the board protocol.

## Project lifecycle (new or larger projects)

Follow the `project-lifecycle` skill, scaled to the project: in Phase 0 propose a small, medium or large track for the user to approve, then discovery phases and build phases on the Orchestra board. Its pitfalls hold in every project. One of them applies to any visual work, lifecycle or not: art comes from humans (one consistent CC0 or bought pack per kind of art, or a commissioned artist), with the owner's sign-off before integrating and an `art-reviewer` pass on every hand-back; AI-generated art is for mood boards and placeholders only.

## Orchestra board

Orchestrated work is tracked on the Orchestra board, a private claude.ai artifact with its own database: https://claude.ai/artifact/Eqis6DgyZMefwhzFM1KNta (one board for all projects). The `orchestration` skill has its data model and when to write. Never write to `inputs`, `approvals`, `controls` or `comments`; those are the user's. Overture is off by default and only for small single-agent plans when the user asks for it (see the `overture` skill).

## Working on the user's machine

- Stop only processes you started, by PID (find it from the port, e.g. `netstat -ano`). Never kill by image name (`taskkill /IM python.exe`, `pkill python`): it takes down the user's own apps and other sessions.
- Browser checks and experiments run on a throwaway copy of the app's data, never on the real database.
- When parallel agents are editing the folder the user's own app runs from, tell the user not to restart it until the gate: a restart loads half-finished work and runs any migration already registered.
- In Git Bash on Windows, non-ASCII text in command-line arguments (curl, sqlite) can arrive as `?`. Send test data with a Python script run with `PYTHONUTF8=1`, and write multi-line code edits with the Edit tool or a script file rather than escaped heredocs.
- The system `python` is the Microsoft Store build, whose child processes can't start uv-managed Pythons; use the project's own venv interpreter (e.g. `.venv/Scripts/python.exe`) for project tools.

## Tooling

- **Test output is trimmed automatically.** A PreToolUse hook (`~/.claude/tools/quiet_tests_hook.py`) routes any plain pytest command through `quiet_tests.py`: a pass shows one summary line, a failure its traceback and summary, with the exit code kept. It only rewrites a command that is nothing but a pytest run. Add `# full-output` to a command to see everything.
- **Library docs: Context7** (MCP server `context7`). Before writing code against a library's API you are not sure of, look up the current docs for the installed version rather than relying on memory.
- **Python code navigation: the `pyright-lsp` plugin.** Prefer the LSP tool (go to definition, find references) over grepping and reading whole files, and read its diagnostics after edits.
- **Art toolkit (experimental): `~/.claude/tools/art/` (README there).** For mood boards and placeholders only. Its ComfyUI, models and rembg were deleted on 2026-10-09; reinstalling them, or any download beyond what's installed, needs the owner's OK.

## Writing defaults (every project)

- English is American spelling: practice (also the verb), color, center, theater, traveler, favorite, judgment.
- No em dashes in English prose, UI text, prompts, comments or docs; use commas, colons or full stops.

## Knowledge vault

One vault of Markdown notes (MCP server `basic-memory`) holds the reusable findings, decisions and research of every project. Load the `vault` skill when starting research or a stack choice, when a problem may have been solved before, and at its writing moments.

## Home lab
- `ssh dev`: Ubuntu Server VM on my Proxmox box (4 cores, 8GB RAM, ~148GB disk). Has Docker, tmux, Git, Tailscale.
  Use it for long-running jobs, containers, services that should stay up, and testing that shouldn't touch this machine.
- `ssh pve`: the Proxmox host. VM/container management only. Don't run workloads or change anything here without asking.
- Run long jobs on dev inside tmux so they survive disconnects.
- Resources are modest (8GB RAM). Don't run memory-heavy jobs in parallel.
- Ask before deleting data on the server, changing network/firewall settings, or exposing ports.
