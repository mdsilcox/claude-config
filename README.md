# claude-config

My Claude Code setup for the Windows desktop and the `dev` VM. I rebuilt it from scratch in October 2026 from the research in [docs/research-2026-10.md](docs/research-2026-10.md), which combines eight independent lenses: official docs, practitioners, empirical studies, skeptics, multi-agent work, memory, home lab and security, and my own vault data. The raw research notes are in [docs/research-notes/](docs/research-notes/). Only the dev VM and the knowledge vault carried over unchanged.

## The idea
Give the agent room to reason, and make the hard limits mechanical. The always-loaded files hold only preferences, machine facts and a few lessons with their reasons. There are no procedural playbooks. Anything that must always hold is a permission rule, a hook or the sandbox, so the prose doesn't have to police it.

| Principle | Evidence | Where it lives |
|---|---|---|
| Keep what loads every turn small | Context files barely move success rates and add about 20% cost; rule-following falls off past about 100 rules | A global CLAUDE.md of 543 words on Windows and 355 on dev (the old one was 4,300); a project template under 150 lines |
| Make hard limits mechanical | Prose rules get skipped; Anthropic's advice is "make it a hook" | Deny rules for secrets; ask rules for pushes, deletes, Docker and vault edits; `guard_deletes`; the dev sandbox |
| Verify against approved tests | Agents given human-written tests resolved 89 to 94% of tasks; tests the agents wrote themselves added almost nothing | The Stop hook runs each project's `FAST_CHECK`; the `verify` skill runs before commits |
| Review in a fresh context | Models favor their own output | The `reviewer` agent (Opus, read-only) |
| Parallel readers yes, parallel writers rarely | Multi-agent setups lose on sequential work, and parallel PRs conflict | A one-line lesson with its reason in each global file |
| Autonomy only where a sandbox exists | Native Windows has no sandbox; four Windows drive or profile wipes were reported in Sep and Oct 2026 | Windows stays supervised; dev runs a bubblewrap sandbox that fails closed; Docker on the desktop takes heavy isolated runs |
| Input tokens are the budget | 98% of agent tokens were input in my metered build | `Explore` pinned to Sonnet; the status line shows context use and both plan limits |
| The vault is curated memory | Text planted in memory files attacks future sessions | Web-derived notes start as drafts, edits ask first, and the vault is read-only on dev |

## Layout

```
windows/   CLAUDE.md, settings.json   global files for the desktop
dev/       CLAUDE.md, settings.json   global files for the dev VM (sandbox on)
shared/
  agents/  reviewer (Opus, fresh-context review), Explore (Sonnet search)
  skills/  vault (note conventions), verify (runs FAST_CHECK before commits)
  hooks/   project_setup, guard_deletes, stop_gate, format_on_edit, vault_pull, statusline, quiet_tests
templates/project/   CLAUDE.md, .claude/settings.json, .gitattributes (what project_setup follows)
install/   install-windows.ps1, dev-root.sh (sudo), install-dev.sh, tmux.conf
benchmark/ how to measure this setup on my own tasks
tests/     hook tests (standard library only)
docs/      the research report and raw notes
```

## Decisions (October 2026)

| Decision | Chosen |
|---|---|
| `ANTHROPIC_API_KEY` in the Windows user environment | Renamed to `ANTHROPIC_API_KEY_OFF`, so Claude Code stops billing the API and the value is kept. Move it into the one project's `.env` that needs it, then delete the variable |
| Default effort | Anthropic's default (medium on Opus 5.5), raised per task with `/effort` |
| Orchestra board, Overture, and the lifecycle and orchestration skills | Retired: they boxed the agent's thinking into fixed procedures |
| Docker on dev | Runs outside the sandbox, behind an ask prompt |
| Vault on dev | Read-only (the MCP write tools are denied) |
| Alerts for unattended runs | Remote Control push notifications |
| Where this repo lives | `E:\Backup Desktop\Claude Code Projects\claude-config`, plus the private GitHub repo `mdsilcox/claude-config` |

## Install

**Windows desktop**
1. Preview: `powershell -ExecutionPolicy Bypass -File install\install-windows.ps1 -DryRun`
2. Install with `-RemoveApiKey`. The script backs up the old config to `~/.claude/backups/` first.
3. Restart the desktop app, run `claude doctor` in a new terminal, and check `/status` and `/hooks` in a session.

**dev VM**
1. `git clone https://github.com/mdsilcox/claude-config.git ~/claude-config && cd ~/claude-config`. Or copy it over with `scp`.
2. Run `sudo bash install/dev-root.sh`. It installs the sandbox packages and the AppArmor profile for bubblewrap, and turns on lingering. It also disables Ubuntu's `bwrap-userns-restrict` profile, which on Ubuntu 25.10 and later overrides that profile and makes every sandboxed command fail.
3. Run `bash install/install-dev.sh`: Claude Code, the config, tmux, and basic-memory.
4. Run `claude auth login`, clone the vault (the script prints how), rerun the script, then run `claude doctor`.

**Each project: automatic**
When a session starts in a git repo that has no CLAUDE.md or no `FAST_CHECK`, the `project_setup` hook tells Claude to set it up first. Claude then works out what the template can't know:
- a CLAUDE.md with the real commands and their timings;
- a `FAST_CHECK`, which it times;
- `FORMAT_RULES` for the formatter the project already uses;
- a `.gitattributes`.

It tells you what it set, and doesn't commit. If `FAST_CHECK` was left empty because a project had no tests, the hook reminds Claude once tests appear. To keep a repo out of this, add an empty `.claude/no-auto-setup`. The `verify` skill is global, so projects don't need a copy.

## Known limits
- **Glob deny rules on Linux:** the sandbox can't enforce glob rules such as `Read(//**/.env)` (`claude doctor` warns about this on dev). Claude's Read tool still refuses those files, but a sandboxed `cat .env` isn't blocked. Keep real secrets out of the repos on dev.
- **Credential scrubbing is off on dev:** `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` forces headless `claude -p` runs into default mode, so `--permission-mode auto` stops working, and dev keeps no credentials in environment variables anyway (Git's token is in `~/.git-credentials`, scoped read-only).
- **The guard hook is a tripwire, not a boundary:** a delete hidden inside a script passes it. On Windows, the backstop is backups and keeping unattended work off the machine.

## Maintenance
- **Monthly:** run `/usage`, `/skill-doctor` and `/doctor prompt-audit`, and prune anything that hasn't earned its place.
- **After a major model release, or every three to six months:** rerun the [personal benchmark](benchmark/README.md) and revisit the defaults.
- **Changing the setup:** edit here, commit, and rerun the installer on each machine. Never edit `~/.claude` directly; the next install overwrites it.

## Tests
Run `python -m unittest discover -s tests` from the repo root. The hooks use only the standard library, and the tests pass on Windows (Python 3.12) and on dev (Python 3.14).
