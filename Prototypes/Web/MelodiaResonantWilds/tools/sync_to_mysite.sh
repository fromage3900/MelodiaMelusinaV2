#!/usr/bin/env bash
# Owner-machine publish helper: mirror this prototype into fromage3900/my-site/resonant-wilds/
# Cloud agents cannot push my-site (403). Run from a machine with write access.
#
# Default = OVERLAY (keeps Tripo gallery GLBs / asset-gallery that live only on my-site).
# Pass --delete for a full rsync mirror that removes destination-only files.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DELETE=0
DEST=""
for arg in "$@"; do
  case "$arg" in
    --delete) DELETE=1 ;;
    -h|--help)
      echo "Usage: $0 [--delete] /path/to/my-site/resonant-wilds" >&2
      exit 0
      ;;
    *)
      if [[ -z "$DEST" ]]; then DEST="$arg"; else
        echo "Unexpected arg: $arg" >&2; exit 2
      fi
      ;;
  esac
done

if [[ -z "$DEST" ]]; then
  echo "Usage: $0 [--delete] /path/to/my-site/resonant-wilds" >&2
  exit 2
fi

mkdir -p "$DEST"

EXCLUDES=(
  --exclude 'node_modules/'
  --exclude 'package.json'
  --exclude 'package-lock.json'
  --exclude '.DS_Store'
  --exclude 'tools/sync_to_mysite.sh'
)

if command -v rsync >/dev/null 2>&1; then
  if [[ "$DELETE" -eq 1 ]]; then
    rsync -a --delete "${EXCLUDES[@]}" "$ROOT/" "$DEST/"
    echo "Full mirror (with --delete) $ROOT -> $DEST"
  else
    rsync -a "${EXCLUDES[@]}" "$ROOT/" "$DEST/"
    echo "Overlay (no delete) $ROOT -> $DEST"
  fi
else
  # Cloud / minimal images often lack rsync — Python overlay preserves dest-only files.
  python3 - "$ROOT" "$DEST" "$DELETE" <<'PY'
import os, shutil, sys
src, dst, delete = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
exclude_dirs = {'node_modules'}
exclude_files = {'package.json', 'package-lock.json', '.DS_Store'}
exclude_paths = {'tools/sync_to_mysite.sh'}
if delete:
  for child in list(os.listdir(dst)):
    if child == '.git':
      continue
    p = os.path.join(dst, child)
    if os.path.isdir(p):
      shutil.rmtree(p)
    else:
      os.unlink(p)
copied = 0
for root, dirs, files in os.walk(src):
  rel = os.path.relpath(root, src)
  dirs[:] = [d for d in dirs if d not in exclude_dirs]
  out = dst if rel == '.' else os.path.join(dst, rel)
  os.makedirs(out, exist_ok=True)
  for f in files:
    if f in exclude_files:
      continue
    rel_f = f if rel == '.' else os.path.join(rel, f).replace('\\', '/')
    if rel_f in exclude_paths:
      continue
    shutil.copy2(os.path.join(root, f), os.path.join(out, f))
    copied += 1
print(('Full mirror' if delete else 'Overlay') + f' via python ({copied} files) {src} -> {dst}')
PY
fi

# Do not overwrite my-site PNG icons with MelodiaMelusinaV2 LFS pointer stubs.
for icon in icon-192.png icon-512.png; do
  if head -c 20 "$DEST/$icon" 2>/dev/null | grep -q 'git-lfs'; then
    echo "WARN: $DEST/$icon looks like a Git LFS pointer — restore the real PNG from my-site HEAD before commit." >&2
  fi
done

echo "Next: cd $(dirname "$DEST") && git status && commit + push my-site main,"
echo "then hard-refresh https://fromage3900.github.io/my-site/resonant-wilds/"
echo "Confirm SW cache name resonant-wilds-v12-*-playground-toys in Application → Cache Storage."
