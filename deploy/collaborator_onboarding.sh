#!/usr/bin/env bash
set -euo pipefail

# Collaborator Onboarding Script
# Usage: ./collaborator_onboarding.sh [tier] [repo_dir]
# Tiers: lightweight (UE plugins) | blender (Blender-only) | full | docs
# Default: lightweight

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TIER="${1:-lightweight}"
REPO_DIR="${2:-$PROJECT_ROOT}"

case "${TIER,,}" in
  lightweight|blender|full|docs)
    TIER="${TIER,,}"
    ;;
  *)
    echo "Unknown tier: $TIER"
    echo "Supported: lightweight, blender, full, docs"
    exit 1
    ;;
esac

if ! git -C "$REPO_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Repository is not a Git checkout: $REPO_DIR"
  echo "Usage: $0 [lightweight|full|docs] [repo_dir]"
  exit 2
fi

echo "==> Tier: $TIER"
echo "==> Repo: $(git -C "$REPO_DIR" rev-parse --show-toplevel)"

cd "$REPO_DIR"

if [ "$TIER" = "full" ]; then
  echo "==> Full clone workflow"
  git sparse-checkout disable || true
  git lfs install
  git lfs pull
  exit 0
fi

if [ "$TIER" = "blender" ]; then
  echo "==> Blender-only sparse workflow (no Unreal project/plugins)"
  git lfs install
  git sparse-checkout init --no-cone
  git sparse-checkout set --no-cone \
    /deploy/surreal_arch/ \
    /deploy/surreal_world/ \
    /deploy/surreal_os/ \
    /deploy/surreal_greybox/ \
    /deploy/surreal_architecture_gen.py \
    /Content/Python/gmm/ \
    /Content/Python/material_lib.py \
    /Tools/ \
    /Docs/ONBOARDING_LIVE_COLLAB.md \
    /Docs/ZUNZUN_FAMILY_INTEGRATION.md \
    /Docs/ZUNDAMON_DESIGN_BIBLE.md \
    /Docs/ZUNDAMON_NPC_SPEC.md \
    /README.md \
    /DOC_INDEX.md
  echo "==> Blender-only checkout ready"
  echo "Install the addon under Blender 5.2, then use Docs/ONBOARDING_LIVE_COLLAB.md."
  exit 0
fi

if [ "$TIER" = "docs" ]; then
  echo "==> Docs/code-only workflow"
  git lfs install || true
  exit 0
fi

echo "==> Lightweight collaborator workflow"
git lfs install

MANIFEST="$SCRIPT_DIR/collaborator_ue_manifest.txt"
if [ ! -f "$MANIFEST" ]; then
  echo "UE collaborator manifest missing: $MANIFEST"
  exit 3
fi

SPARSE_PATHS=()
LFS_PATHS=()
PLUGIN_PATHS=()
while read -r record path label; do
  case "$record" in
    SPARSE) SPARSE_PATHS+=("$path") ;;
    LFS) LFS_PATHS+=("$path") ;;
    PLUGIN) PLUGIN_PATHS+=("$label") ;;
  esac
done < <(awk 'NF && $1 !~ /^#/ { print $1, $2, $3 }' "$MANIFEST")

echo "==> Enabling UE-capable sparse checkout"
git sparse-checkout init --no-cone
git sparse-checkout set --no-cone "${SPARSE_PATHS[@]}"

echo "==> Hydrating UE plugin and gameplay LFS payloads"
LFS_INCLUDE="$(IFS=,; printf '%s' "${LFS_PATHS[*]}")"
git lfs pull --include="$LFS_INCLUDE"

echo "==> Checking required project and plugin manifests"
REQUIRED_PATHS=("BS_GodFile.uproject")
for sparse_path in "${SPARSE_PATHS[@]}"; do
  REQUIRED_PATHS+=("${sparse_path#/}")
done
REQUIRED_PATHS+=("${PLUGIN_PATHS[@]}")
missing=0
for required_path in "${REQUIRED_PATHS[@]}"; do
  if [ ! -e "$required_path" ]; then
    echo "FAIL: required path missing: $required_path"
    missing=$((missing + 1))
  else
    echo "OK: $required_path"
  fi
done
if [ "$missing" -ne 0 ]; then
  echo "Lightweight UE checkout is incomplete; rerun sparse checkout before opening Unreal."
  exit 4
fi

echo "==> Onboarding complete for tier: $TIER"
echo "Plugins are source-only; compile them before opening the project:"
echo '  "<UE_ROOT>\\Engine\\Build\\BatchFiles\\Build.bat" BS_GodFileEditor Win64 Development -Project="<checkout>\\BS_GodFile.uproject" -NoUBA -MaxParallelActions=1'
if [ -f "$REPO_DIR/deploy/validate_setup.ps1" ]; then
  echo "Validate with:"
  echo "  powershell -ExecutionPolicy Bypass -File .\\deploy\\validate_setup.ps1 -SkipServices -CheckLfsHydration"
fi
