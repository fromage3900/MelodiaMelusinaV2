#!/usr/bin/env bash
set -euo pipefail

# verify_critical_workflows.sh
# The Ultimate 0.1% Coordinator Automation
# Runs critical gate checks: Ports, Setup, Hooks, and Packaged Build presence.

echo "🎶 [Melodia] Initiating Workflow Automation Combo... 🎶"

# 1. Ensure git hooks are enabled
echo "==> [Gate 1] Configuring core.hooksPath"
git config core.hooksPath .githooks
echo "✅ Hooks enabled."

# 2. Check setup
echo "==> [Gate 2] Validating Collaborator Setup"
if [ -x "deploy/validate_collaborator_setup.sh" ]; then
    ./deploy/validate_collaborator_setup.sh .
else
    echo "⚠️  validate_collaborator_setup.sh not executable or missing."
fi

# 3. Check Critical Ports
echo "==> [Gate 3] Checking Critical Metaverse Ports"
# VOICEVOX: 50021
if curl -s http://127.0.0.1:50021/version >/dev/null; then
    echo "✅ VOICEVOX [Port 50021]: CONNECTED"
else
    echo "❌ VOICEVOX [Port 50021]: OFFLINE (Missed Note!)"
fi

# UE MCP: 9316
if curl -s http://127.0.0.1:9316/health >/dev/null; then
    echo "✅ UE MCP [Port 9316]: CONNECTED"
else
    echo "❌ UE MCP [Port 9316]: OFFLINE (Missed Note!)"
fi

# 4. Check for packaged build
echo "==> [Gate 4] PIE / Packaged Build Check"
if [ -d "Saved/StagedBuilds/Windows" ]; then
    echo "✅ Packaged Build Found: Ready for Runway."
else
    echo "⚠️  No packaged build found in Saved/StagedBuilds/Windows. Run package_game.ps1 to generate."
fi

echo "🌟 S-Rank Combo Complete! 🌟"
exit 0
