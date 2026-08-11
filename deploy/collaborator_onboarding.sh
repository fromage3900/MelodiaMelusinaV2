#!/usr/bin/env bash
# Collaborator Onboarding Script
# Usage: ./deploy/collaborator_onboarding.sh [tier]
# Tiers: lightweight | full | docs
# Default: lightweight

set -euo pipefail

TIER="${1:-lightweight}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "$TIER" in
  lightweight|full|docs)
    ;;
  *)
    echo "Unknown tier: $TIER"
    echo "Supported: lightweight, full, docs"
    exit 1
    ;;
esac

echo "==> Tier: $TIER"
echo "==> Repo: $REPO_DIR"

cd "$REPO_DIR"

if [ "$TIER" = "full" ]; then
  echo "==> Full clone workflow"
  git lfs install
  git lfs pull
  echo "==> Onboarding complete for tier: $TIER"
  exit 0
fi

if [ "$TIER" = "docs" ]; then
  echo "==> Docs/code-only workflow"
  git lfs install || true
  echo "==> Onboarding complete for tier: $TIER"
  exit 0
fi

echo "==> Lightweight collaborator workflow"
git lfs install

echo "==> Enabling sparse checkout"
git sparse-checkout init --cone || true
git sparse-checkout set \
  Content/Melodia/Levels \
  Content/EnvSandbox \
  Content/MelodiaIntegration \
  Content/TurnBasedJRPGTemplate \
  Plugins/MelodiaCore/Source \
  Docs \
  Source \
  Config \
  Tools \
  deploy \
  specs || true

echo "==> Pulling targeted LFS assets for level/material/integration work"
git lfs pull --include="Content/Melodia/**,Content/EnvSandbox/**,Content/MelodiaIntegration/**,Content/TurnBasedJRPGTemplate/**" || true

echo "==> Onboarding complete for tier: $TIER"
if [ -f "$REPO_DIR/deploy/validate_setup.ps1" ]; then
  echo "Run: powershell -ExecutionPolicy Bypass -File .\\deploy\\validate_setup.ps1"
else
  echo "Validation script not found; continuing without it."
fi
