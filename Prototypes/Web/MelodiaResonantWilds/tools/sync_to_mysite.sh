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

# MelodiaMelusinaV2 often stores PWA icons as Git LFS pointers (≈129 B). Never copy those
# over real PNGs already on my-site. Also exclude them from rsync when the source is a stub.
is_lfs_pointer() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  # Pointers begin `version https://git-lfs.github.com/spec/...` — need >20 bytes.
  head -c 64 "$f" 2>/dev/null | grep -q 'git-lfs'
}

ICON_EXCLUDES=()
for icon in icon-192.png icon-512.png; do
  if is_lfs_pointer "$ROOT/$icon"; then
    ICON_EXCLUDES+=(--exclude "$icon")
    echo "Skip source $icon (Git LFS pointer) — keeping destination PNG if present."
  fi
done

EXCLUDES=(
  --exclude 'node_modules/'
  --exclude 'package.json'
  --exclude 'package-lock.json'
  --exclude '.DS_Store'
  --exclude 'tools/sync_to_mysite.sh'
  "${ICON_EXCLUDES[@]}"
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

def is_lfs_pointer(path):
  try:
    with open(path, 'rb') as fh:
      return b'git-lfs' in fh.read(64)
  except OSError:
    return False

# Never copy Melodia LFS pointer icons over real my-site PNGs.
for icon in ('icon-192.png', 'icon-512.png'):
  if is_lfs_pointer(os.path.join(src, icon)):
    exclude_files.add(icon)
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
skipped_lfs = 0
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
    src_f = os.path.join(root, f)
    if is_lfs_pointer(src_f):
      skipped_lfs += 1
      continue
    shutil.copy2(src_f, os.path.join(out, f))
    copied += 1
msg = ('Full mirror' if delete else 'Overlay') + f' via python ({copied} files) {src} -> {dst}'
if skipped_lfs:
  msg += f' (skipped {skipped_lfs} LFS pointer file(s))'
print(msg)
PY
fi

# Final guard: if dest icons somehow became LFS stubs, scream before the owner commits.
for icon in icon-192.png icon-512.png; do
  if is_lfs_pointer "$DEST/$icon"; then
    echo "WARN: $DEST/$icon looks like a Git LFS pointer — restore the real PNG from my-site HEAD before commit." >&2
  fi
done

echo "Next: cd $(dirname "$DEST") && git status && commit + push my-site main,"
echo "then hard-refresh https://fromage3900.github.io/my-site/resonant-wilds/"
echo "Confirm SW cache name resonant-wilds-v16-*-painterly-cel in Application → Cache Storage."
echo "Live URL is Nikki-by-default (no query). Low-end escape: ?lite=1"
