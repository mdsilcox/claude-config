#!/usr/bin/env bash
# Set up Claude Code on the dev VM from this claude-config repo. Run as your own user, from a clone:
#
#   DRY_RUN=1 bash install/install-dev.sh   # print the steps only
#   bash install/install-dev.sh
#
# The steps that need root are in install/dev-root.sh (run it with sudo). Backs up the ~/.claude files
# it replaces; leaves ~/.claude.json, credentials and projects/ alone. Safe to run again.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
C="$HOME/.claude"
BACKUP="$C/backups/pre-claude-config-$(date +%Y%m%d-%H%M%S)"
VAULT="$HOME/knowledge-vault-data"
VAULT_REMOTE="https://github.com/mdsilcox/knowledge-vault-data.git"
export PATH="$HOME/.local/bin:$PATH"

step() { printf '\n== %s\n' "$*"; }
live() { [ -z "${DRY_RUN:-}" ]; }

if ! command -v bwrap >/dev/null || ! command -v socat >/dev/null; then
  echo "Note: bubblewrap or socat is missing. Run 'sudo bash install/dev-root.sh' too: until then Claude Code"
  echo "won't start here, because the sandbox is set to fail closed."
fi

step "1. Claude Code (native installer, stable channel)"
if ! command -v claude >/dev/null; then
  if live; then curl -fsSL https://claude.ai/install.sh | bash -s stable; fi
fi

step "2. Global config (old files backed up to $BACKUP)"
if live; then
  mkdir -p "$BACKUP"
  for f in CLAUDE.md settings.json agents skills hooks tools templates; do
    if [ -e "$C/$f" ]; then cp -a "$C/$f" "$BACKUP/"; fi
  done
  mkdir -p "$C/hooks" "$C/agents" "$C/skills" "$C/templates"
  cp -a "$REPO/shared/hooks/." "$C/hooks/"
  cp -a "$REPO/shared/agents/." "$C/agents/"
  cp -a "$REPO/shared/skills/." "$C/skills/"
  cp -a "$REPO/templates/." "$C/templates/"
  cp "$REPO/dev/CLAUDE.md" "$C/CLAUDE.md"
  cp "$REPO/dev/settings.json" "$C/settings.json"   # last, so its hooks already exist
fi

step "3. tmux settings for Claude Code"
if ! grep -qs 'allow-passthrough' "$HOME/.tmux.conf"; then
  if live; then cat "$REPO/install/tmux.conf" >> "$HOME/.tmux.conf"; fi
fi

step "4. Read-only vault: basic-memory and the MCP server"
if ! command -v uv >/dev/null; then
  if live; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi
fi
if ! command -v basic-memory >/dev/null; then
  if live; then uv tool install "basic-memory==0.24.1"; fi
fi
if [ ! -d "$VAULT/.git" ]; then
  echo "   Not cloned yet. The vault repo is private, so clone it once by hand:"
  echo "     git config --global credential.helper store"
  echo "     git clone $VAULT_REMOTE $VAULT"
  echo "   (user: mdsilcox; password: a fine-grained token with Contents read on knowledge-vault-data)"
  echo "   then run this script again to register it with basic-memory."
elif live; then
  if ! basic-memory project list 2>/dev/null | grep -qw vault; then
    basic-memory project add vault "$VAULT"
    basic-memory project default vault
  fi
  if ! claude mcp get basic-memory >/dev/null 2>&1; then
    claude mcp add -s user basic-memory -- "$HOME/.local/bin/basic-memory" mcp
  fi
fi

cat <<'EOF'

Done. Still to do on dev, if not done yet:
  1. sudo bash install/dev-root.sh   sandbox packages, AppArmor profile, lingering
  2. claude auth login               a full claude.ai login (never set ANTHROPIC_API_KEY here)
  3. the vault clone above, then rerun this script
  4. claude doctor; then in a repo, start claude and check /sandbox and /status
EOF
