#!/usr/bin/env bash
set -euo pipefail

# validate_collaborator_setup.sh
# Usage: ./validate_collaborator_setup.sh [repo_dir] [ue|blender]
# The default UE mode validates the project/plugin-capable lightweight tier.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="${1:-$PROJECT_ROOT}"
MODE="${2:-ue}"
ERRORS=0
WARNINGS=0

case "$MODE" in
  ue|blender) ;;
  *)
    echo "Usage: $0 [repo_dir] [ue|blender]"
    exit 2
    ;;
esac

if ! git -C "$REPO_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "FAIL: Git checkout not found at $REPO_DIR"
  exit 2
fi

REPO_ROOT="$(git -C "$REPO_DIR" rev-parse --show-toplevel)"
echo "==> Repo: $REPO_ROOT"
echo "==> Mode: $MODE"
cd "$REPO_ROOT"

echo "==> Git status"
git status --short --branch || true

echo "==> Git LFS"
if git lfs version; then
  git lfs ls-files --long | awk 'NR <= 5 { print }'
else
  echo "FAIL: Git LFS is unavailable"
  ERRORS=$((ERRORS + 1))
fi

echo "==> Sparse checkout"
if git sparse-checkout list >/dev/null 2>&1; then
  git sparse-checkout list
else
  echo "Sparse checkout not active"
fi

check_required_path() {
  local path="$1"
  if [ -e "$path" ]; then
    echo "OK: $path"
  else
    echo "FAIL: required path missing: $path"
    ERRORS=$((ERRORS + 1))
  fi
}

echo "==> Key directories"
if [ "$MODE" = "ue" ]; then
  KEY_DIRECTORIES=(Content Docs Source Plugins Config deploy RawArt/MelusinasHouse Docs/References/MelusinasHouse)
else
  KEY_DIRECTORIES=(Content/Python Docs deploy Tools RawArt/MelusinasHouse Docs/References/MelusinasHouse)
fi
for d in "${KEY_DIRECTORIES[@]}"; do
  check_required_path "$d"
done

if [ "$MODE" = "blender" ]; then
  echo "==> Blender-only addon/discovery paths"
  for d in deploy/surreal_arch deploy/surreal_world deploy/surreal_os deploy/surreal_greybox; do
    check_required_path "$d"
  done
  check_required_path "deploy/surreal_architecture_gen.py"
  check_required_path "deploy/sync_workstation.ps1"
  check_required_path "deploy/install_melodia_studio.ps1"
  check_required_path "AGENT_START_HERE.md"
  check_required_path "Docs/Art/VISUAL_REFERENCE_INDEX.md"
  check_required_path "Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md"
  check_required_path "Docs/References/MelusinasHouse/REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg"
  check_required_path "Docs/References/MelusinasHouse/REF_02_GEOMETRY_NODES_BUILD_SHEET.jpg"
  check_required_path "Docs/References/MelusinasHouse/REF_03_CUTAWAY_INTERIOR_FLOW.jpg"
  check_required_path "RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend"

  house_blend="RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend"
  if [ -f "$house_blend" ] && head -n 1 "$house_blend" 2>/dev/null | grep -q "git-lfs.github.com/spec"; then
    echo "FAIL: canonical house Blender source is still an LFS pointer: $house_blend"
    ERRORS=$((ERRORS + 1))
  fi
else
  MANIFEST="$PROJECT_ROOT/deploy/collaborator_ue_manifest.txt"
  check_required_path "BS_GodFile.uproject"
  check_required_path "$MANIFEST"

  SPARSE_PATHS=()
  PLUGIN_PATHS=()
  LFS_ROOTS=()
  if [ -f "$MANIFEST" ]; then
    while read -r record first second; do
      case "$record" in
        SPARSE) SPARSE_PATHS+=("$first") ;;
        PLUGIN) PLUGIN_PATHS+=("$second") ;;
        LFS) LFS_ROOTS+=("${first%/**}") ;;
      esac
    done < <(awk 'NF && $1 !~ /^#/ { print $1, $2, $3 }' "$MANIFEST")
  fi

  echo "==> Required sparse paths"
  for sparse_path in "${SPARSE_PATHS[@]}"; do
    check_required_path "${sparse_path#/}"
  done

  echo "==> Required project plugin manifests"
  for plugin_manifest in "${PLUGIN_PATHS[@]}"; do
    check_required_path "$plugin_manifest"
    plugin_root="${plugin_manifest%/*}"
    check_required_path "$plugin_root/Source"
    if compgen -G "$plugin_root/Binaries/Win64/*.dll" > /dev/null; then
      echo "OK: $plugin_root/Binaries/Win64 (compiled plugin binaries)"
    else
      echo "WARN: $plugin_root has no Win64 DLL; run the closed-editor UE 5.8 build"
      WARNINGS=$((WARNINGS + 1))
    fi
  done

  echo "==> Required LFS hydration"
  while read -r object_id state tracked_file; do
    [ -n "$tracked_file" ] || continue
    for lfs_root in "${LFS_ROOTS[@]}"; do
      case "$tracked_file" in
        "$lfs_root"/*)
          if [ "$state" = "-" ]; then
            echo "FAIL: LFS pointer is not hydrated: $tracked_file"
            ERRORS=$((ERRORS + 1))
          fi
          break
          ;;
      esac
    done
  done < <(git lfs ls-files --long)
fi

echo "==> Git object usage"
git count-objects -vH || true

echo "==> Validation complete. Errors: $ERRORS; Warnings: $WARNINGS"
if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi
exit 0
