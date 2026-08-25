#!/usr/bin/env bash
# BS_GodFile orchestration router — Hermes (architectural orchestrator) delegates
# concrete coding/analysis work to specialized CLIs (Claude Code, Kimi CLI).
#
# Usage:
#   bash deploy/orchestrate/delegate.sh claude  "task text"           [--dir <path>] [--max-turns N] [--readonly]
#   bash deploy/orchestrate/delegate.sh kimi    "task text"           [--dir <path>]
#   bash deploy/orchestrate/delegate.sh status
#
# Hermes decides WHAT and delegates HOW: pick a lane, write the brief, call this
# with the target CLI. The worker runs in its own process/worktree and returns
# structured output. See Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md.
set -uo pipefail

LANE="${1:-}"
shift || true

if [ -z "${LANE:-}" ] || [ "$LANE" = "help" ] || [ "$LANE" = "-h" ]; then
  echo "Usage: delegate.sh <claude|kimi|status> \"<task>\" [--dir PATH] [--max-turns N] [--readonly]"
  exit 0
fi

WORKDIR="."
MAX_TURNS="20"
READONLY=""
BRIEF=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)      WORKDIR="${2:-.}"; shift 2 ;;
    --dir=*)    WORKDIR="${1#--dir=}"; shift ;;
    --max-turns) MAX_TURNS="${2:-20}"; shift 2 ;;
    --max-turns=*) MAX_TURNS="${1#--max-turns=}"; shift ;;
    --readonly) READONLY="--readonly"; shift ;;
    *)          BRIEF="${BRIEF} $1"; shift ;;
  esac
done
BRIEF="$(echo "$BRIEF" | sed 's/^ //')"

if [ "$LANE" != "status" ] && [ -z "$BRIEF" ]; then
  echo "ERR: no task brief supplied for lane '$LANE'"
  exit 1
fi

cd "$WORKDIR" 2>/dev/null || { echo "ERR: cannot cd to $WORKDIR"; exit 2; }

case "$LANE" in
  claude)
    if [ "${READONLY}" = "--readonly" ]; then
      ALLOW="Read"
    else
      ALLOW="Read,Edit,Write,Bash"
    fi
    echo ">>> [hermes->claude] dir=$WORKDIR turns=$MAX_TURNS tools=$ALLOW"
    claude -p "$BRIEF" --allowedTools "$ALLOW" --max-turns "$MAX_TURNS" --output-format text
    ;;
  kimi)
    echo ">>> [hermes->kimi] dir=$WORKDIR"
    kimi -p "$BRIEF" --yolo
    ;;
  status)
    echo "=== CLI availability ==="
    echo -n "claude: "; claude --version 2>&1 | head -1
    echo -n "kimi:   "; kimi --version 2>&1 | head -1
    echo ""
    echo "=== claude auth ==="
    claude auth status --text 2>&1 | head -4
    ;;
  *)
    echo "Unknown lane '$LANE' (claude|kimi|status)"; exit 1 ;;
esac
