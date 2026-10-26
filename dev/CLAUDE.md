# Global instructions (dev VM)

Use your judgment. This file holds only what you can't work out yourself: my preferences, this machine's limits, and a few lessons with their reasons. Settings, hooks and the sandbox enforce the hard limits.

## Environment
- This is `dev`, a headless Ubuntu Server VM on my home Proxmox server. Accessed over SSH/Tailscale.
- 8GB RAM shared with Docker containers. Be mindful of memory: two or three Claude sessions at most, and one heavy test suite at a time.
- Long-running services run via Docker Compose. Docker runs outside the sandbox and asks first, so unattended work shouldn't depend on it.
- Ask before deleting data, changing network/firewall settings, or exposing ports.
- `ssh pve` is VM management only. Ask before any snapshot, rollback or other change there, and before a risky unattended run ask me whether to snapshot first.
- Shell commands run in a sandbox: network goes through an allowlist, and plain `ssh` doesn't work inside it, so git remotes here are HTTPS.
- Long runs go in tmux. For unattended work, give `/goal` a condition with a turn limit, and keep progress in files (a spec, a feature list) so a run can resume.

## Working with me
- Write American English (practice, color, center, judgment). No em dashes in prose, UI text, comments or docs.
- Git: when a change is done and its checks pass, commit it and push straight to main. Use a branch and a PR only when I ask for one. Delete working branches, local and on GitHub, once they are merged into main. Force pushes and history rewrites still need my OK. New GitHub repos get `gh repo edit --delete-branch-on-merge`.
- Show evidence (test output, commands run) when you report that something works.
- Stop only processes you started, by PID.

## What tends to work (from research and my own projects)
- Tests are the best oracle. For new behavior, write the tests first and list them when you report; I approve tests only when I ask to see them first. Once written, never change one to make the code pass; if one looks wrong, ask. Keep suites intentional, not excessive: each test earns its place and its run time.
- A fresh-context review (the `reviewer` agent) catches what the author misses.
- Parallel readers pay off; parallel writers on coupled code conflict. Split writing only along frozen interfaces.

## Knowledge vault
The vault is read-only here: search it (basic-memory) before research, a stack choice, or a second attempt at a non-trivial error. Anything worth keeping goes in your final report, and I write it to the vault from the desktop.
