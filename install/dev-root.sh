#!/usr/bin/env bash
# The dev VM steps that need root. Run once, from a clone of this repo:
#
#   sudo bash install/dev-root.sh
#
# Installs the sandbox's packages, lets bubblewrap create user namespaces under Ubuntu's AppArmor
# restriction, and turns on lingering so your user's tmux sessions and services survive logout.
# Safe to run again.
set -euo pipefail

if [ "$(id -u)" != 0 ]; then
  echo "Run this with sudo: sudo bash install/dev-root.sh" >&2
  exit 1
fi
TARGET_USER="${SUDO_USER:?run this through sudo, not as root directly}"

echo "== 1. Sandbox packages: bubblewrap and socat"
apt-get install -y bubblewrap socat

echo "== 2. AppArmor profile for /usr/bin/bwrap"
if [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo 0)" = 1 ] \
    && [ ! -f /etc/apparmor.d/bwrap ]; then
  cat > /etc/apparmor.d/bwrap <<'EOF'
abi <abi/4.0>,
include <tunables/global>

profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,

  include if exists <local/bwrap>
}
EOF
  systemctl reload apparmor
else
  echo "   not needed, or already present"
fi

echo "== 3. Lingering for $TARGET_USER"
loginctl enable-linger "$TARGET_USER"

echo
echo "Done. Next, as $TARGET_USER: bash install/install-dev.sh"
