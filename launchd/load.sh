#!/usr/bin/env bash
# Install and start OmniParser FastAPI via macOS launchd (user agent).
set -euo pipefail

LABEL="com.omniparser.server"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE_PLIST="${SCRIPT_DIR}/${LABEL}.plist"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
INSTALLED_PLIST="${LAUNCH_AGENTS_DIR}/${LABEL}.plist"
DOMAIN="gui/$(id -u)"

resolve_python() {
	if [[ -n "${OMNIPARSER_PYTHON:-}" && -x "${OMNIPARSER_PYTHON}" ]]; then
		echo "${OMNIPARSER_PYTHON}"
		return
	fi
	if [[ -x "${HOME}/miniconda3/envs/omni/bin/python" ]]; then
		echo "${HOME}/miniconda3/envs/omni/bin/python"
		return
	fi
	if [[ -x "${HOME}/anaconda3/envs/omni/bin/python" ]]; then
		echo "${HOME}/anaconda3/envs/omni/bin/python"
		return
	fi
	if command -v conda >/dev/null 2>&1; then
		local py
		py="$(conda run -n omni python -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
		if [[ -n "${py}" && -x "${py}" ]]; then
			echo "${py}"
			return
		fi
	fi
	echo "ERROR: Cannot find conda env 'omni' python." >&2
	echo "Set OMNIPARSER_PYTHON=/path/to/python and retry." >&2
	exit 1
}

PYTHON_BIN="$(resolve_python)"
CONDA_BIN_DIR="$(dirname "${PYTHON_BIN}")"

mkdir -p "${PROJECT_ROOT}/logs" "${LAUNCH_AGENTS_DIR}"

sed \
	-e "s|@PROJECT_ROOT@|${PROJECT_ROOT}|g" \
	-e "s|@PYTHON_BIN@|${PYTHON_BIN}|g" \
	-e "s|@CONDA_BIN_DIR@|${CONDA_BIN_DIR}|g" \
	"${TEMPLATE_PLIST}" > "${INSTALLED_PLIST}"

# Stop previous registration if present (ignore errors).
launchctl bootout "${DOMAIN}" "${INSTALLED_PLIST}" 2>/dev/null || true

launchctl bootstrap "${DOMAIN}" "${INSTALLED_PLIST}"
launchctl enable "${DOMAIN}/${LABEL}" 2>/dev/null || true
launchctl kickstart -k "${DOMAIN}/${LABEL}"

LAN_IP=""
for iface in en0 en1; do
	ip="$(ipconfig getifaddr "${iface}" 2>/dev/null || true)"
	if [[ -n "${ip}" ]]; then
		LAN_IP="${ip}"
		break
	fi
done

echo "Installed: ${INSTALLED_PLIST}"
echo "Python:    ${PYTHON_BIN}"
echo "Project:   ${PROJECT_ROOT}"
echo "Listen:    0.0.0.0:8000 (all interfaces, LAN OK)"
echo "Local:     curl http://127.0.0.1:8000/probe/"
if [[ -n "${LAN_IP}" ]]; then
	echo "LAN:       curl http://${LAN_IP}:8000/probe/"
else
	echo "LAN:       run: ipconfig getifaddr en0  then use http://<that-ip>:8000/"
fi
echo "Logs:      ${PROJECT_ROOT}/logs/omniparser.{stdout,stderr}.log"
echo "Status:    launchctl print ${DOMAIN}/${LABEL}"
