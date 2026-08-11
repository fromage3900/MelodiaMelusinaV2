#!/usr/bin/env bash
set -euo pipefail

# Collaborator Onboarding Script
# Usage: ./collaborator_onboarding.sh [tier] [repo_dir]
# Tiers: lightweight | full | docs
# Default: lightweight

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TIER="${1:-lightweight}"
REPO_DIR="${2:-$PROJECT_ROOT}"

case "${TIER,,}" in
  lightweight|full|docs)
    TIER="${TIER,,}"
    ;;
  *)
    echo "Unknown tier: $TIER"
    echo "Supported: lightweight, full, docs"
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
  git lfs install
  git lfs pull
  exit 0
fi

if [ "$TIER" = "docs" ]; then
  echo "==> Docs/code-only workflow"
  git lfs install || true
  exit 0
fi

echo "==> Lightweight collaborator workflow"
git lfs install

echo "==> Enabling sparse checkout"
git sparse-checkout init --cone || true
git sparse-checkout set \
  Content/Melodia/Levels \
  Content/EnvSandbox \
  Plugins/MelodiaCore/Source \
  Docs \
  Source \
  Config \
  deploy || true

echo "==> Pulling targeted LFS assets for level/material work"
git lfs pull --include="*.umap" || true
git lfs pull --include="Content/EnvSandbox/Levels/*.umap" || true
git lfs pull --include="Content/Melodia/Levels/*.umap" || true
git lfs pull --include="Content/EnvSandbox/Meshes/*.uasset" || true
git lfs pull --include="Content/EnvSandbox/Materials/*.uasset" || true

echo "==> Onboarding complete for tier: $TIER"
if [ -f "$REPO_DIR/deploy/validate_setup.ps1" ]; then
  echo "Run: powershell -ExecutionPolicy Bypass -File .\\deploy\\validate_setup.ps1 -SkipServices"
fi
