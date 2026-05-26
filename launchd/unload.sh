#!/usr/bin/env bash
# Stop OmniParser launchd user agent and remove installed plist.
set -euo pipefail

LABEL="com.omniparser.server"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
INSTALLED_PLIST="${LAUNCH_AGENTS_DIR}/${LABEL}.plist"
DOMAIN="gui/$(id -u)"

if [[ ! -f "${INSTALLED_PLIST}" ]]; then
	echo "Not loaded (plist missing): ${INSTALLED_PLIST}"
	exit 0
fi

launchctl bootout "${DOMAIN}" "${INSTALLED_PLIST}" 2>/dev/null || true
rm -f "${INSTALLED_PLIST}"

echo "Unloaded ${LABEL}"
echo "Removed ${INSTALLED_PLIST}"
