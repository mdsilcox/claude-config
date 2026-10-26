# Global instructions (Windows desktop)

Use your judgment. This file holds only what you can't work out yourself: my preferences, this machine's quirks, and a few lessons with their reasons. Settings and hooks enforce the hard limits, so the prose doesn't have to.

## Working with me
- Write American English (practice, color, center, judgment). No em dashes in prose, UI text, comments or docs.
- Ask before anything irreversible: deleting data, force pushes, migrations, or any change to the home lab. Otherwise you have full autonomy over development: use your judgment and keep going, and ask only when something truly needs my call.
- Git: when a change is done and its checks pass, commit it and push straight to main. Use a branch and a PR only when I ask for one. Force pushes and history rewrites still need my OK.
- Show evidence (test output, commands run, screenshots) when you report that something works.
- Shipped game and app art comes from humans (asset packs or commissions). Generated images are for mood boards and placeholders only.
- Build projects with Docker where it fits: a Dockerfile (and a compose file for services) so builds, tests and services run the same here and on `ssh dev`. It doesn't fit tools that must run natively on this machine (desktop apps, anything that reads ~/.claude live); there, Docker is for the test run only.

## What tends to work (from research and my own projects)
- Tests are the best oracle. For new behavior, write the tests first and list them when you report; I approve tests only when I ask to see them first. Once written, never change one to make the code pass; if one looks wrong, ask. Keep suites intentional, not excessive: each test earns its place and its run time.
- A fresh-context review catches what the author misses; the `reviewer` agent is there for non-trivial diffs.
- Parallel agents pay off for reading, searching and reviewing. Parallel writers on coupled code conflict and redo each other's work, so split writing only along frozen interfaces and disjoint files.
- Long sessions degrade. Keep state in files (a plan, a spec, notes) so that a fresh session can pick up the work.

## This machine
- Native Windows has no sandbox, so work here stays supervised. Long, unattended or untrusted work goes to `ssh dev` (sandboxed, with snapshots) or to a Docker container that mounts only the repo.
- Write multi-line code with the Write or Edit tool, not a Git Bash heredoc: heredocs corrupt escapes and regexes.
- Use the project's own venv Python (`.venv/Scripts/python.exe`); the Microsoft Store `python` can't start uv-managed interpreters. Keep venvs and installs on short paths.
- Stop only processes you started, by PID. Never kill by image name.
- Browser checks run against a throwaway copy of the app's data, at 375px and desktop width.

## Home lab
- `ssh dev`: Ubuntu Server VM on my Proxmox box (4 cores, 8GB RAM, ~148GB disk). Has Docker, tmux, Git, Tailscale.
  Use it for long-running jobs, containers, services that should stay up, and testing that shouldn't touch this machine.
- `ssh pve`: the Proxmox host. VM/container management only. Don't run workloads or change anything here without asking.
- Run long jobs on dev inside tmux so they survive disconnects.
- Resources are modest (8GB RAM). Don't run memory-heavy jobs in parallel.
- Ask before deleting data on the server, changing network/firewall settings, or exposing ports.

## Knowledge vault (basic-memory, project `vault`)
- Search it before research, a stack choice, or a second attempt at a non-trivial error. Write to it after research, a reusable decision or fix, or a retro. The `vault` skill has the conventions.
- Notes drawn from web pages, issues or tool output get `status: draft` and a `source`, so I can review them before they count.

## Project files
A project's CLAUDE.md holds commands (with timings), which machine runs them, gotchas and pointers, in under 150 lines. Add a line after a repeated mistake; never paste overviews or code into it.
