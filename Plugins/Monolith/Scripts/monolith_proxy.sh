#!/usr/bin/env bash
# Monolith MCP Proxy launcher (macOS / Linux).
# Finds Python automatically and runs the proxy.
# Usage in .mcp.json:
#   {"mcpServers": {"monolith": {"command": "Plugins/Monolith/Scripts/monolith_proxy.sh"}}}

set -eu

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROXY_PY="$SCRIPT_DIR/monolith_proxy.py"

if [ ! -f "$PROXY_PY" ]; then
	echo "[monolith-proxy] ERROR: proxy script not found at $PROXY_PY" 1>&2
	exit 1
fi

# Prefer python3 (standard on macOS 12+ and most Linux distros), fall back to python.
if command -v python3 >/dev/null 2>&1; then
	exec python3 "$PROXY_PY" "$@"
fi

if command -v python >/dev/null 2>&1; then
	# Some systems still ship only `python`; require Python 3.8+.
	if python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
		exec python "$PROXY_PY" "$@"
	fi
fi

echo "[monolith-proxy] ERROR: Python 3.8+ not found. Install from https://python.org or your package manager." 1>&2
exit 1
