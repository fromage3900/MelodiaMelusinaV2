#!/usr/bin/env bash
# Owner-machine publish helper: mirror this prototype into fromage3900/my-site/resonant-wilds/
# Cloud agents cannot push my-site (403). Run from a machine with write access.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-}"
if [[ -z "$DEST" ]]; then
  echo "Usage: $0 /path/to/my-site/resonant-wilds" >&2
  exit 2
fi

mkdir -p "$DEST"
rsync -a --delete \
  --exclude 'node_modules/' \
  --exclude 'package.json' \
  --exclude 'package-lock.json' \
  --exclude '.DS_Store' \
  --exclude 'tools/sync_to_mysite.sh' \
  "$ROOT/" "$DEST/"

echo "Mirrored $ROOT -> $DEST"
echo "Next: cd $(dirname "$DEST") && git status && commit + push my-site main,"
echo "then hard-refresh https://fromage3900.github.io/my-site/resonant-wilds/"
echo "Confirm SW cache name resonant-wilds-v11-* in Application → Cache Storage."
