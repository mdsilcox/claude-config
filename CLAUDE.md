# claude-config: my Claude Code setup for the Windows desktop and the dev VM

## Must not miss
- Change the setup here, then reinstall. Never edit `~/.claude` directly: the next install overwrites it.
- Hooks use only the standard library and must run on both machines: Windows (Git Bash, the hooks venv Python) and dev (python3).

## Commands
- Fast check (about 2 s; the Stop hook runs it): `uv run --no-project python -m unittest discover -s tests -q`
- Install on Windows: `powershell -ExecutionPolicy Bypass -File install\install-windows.ps1` (add `-DryRun` to preview)
- Install on dev: `cd ~/claude-config && git pull && bash install/install-dev.sh` (root steps: `sudo bash install/dev-root.sh`)
- After an install, validate the settings with `claude doctor`.

## Gotchas
- settings.json is strict JSON: no comments and no trailing commas.
- Hook commands in `windows/settings.json` use absolute `C:/Users/mikha` paths and the hooks venv; `dev/settings.json` uses `/home/mdsilcox` and `python3`.

## Pointers
- README.md: the design, decisions and known limits.
- docs/research-2026-10.md: the evidence behind them.
