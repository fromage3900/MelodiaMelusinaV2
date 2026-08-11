#!/usr/bin/env bash
set -euo pipefail

# validate_collaborator_setup.sh
# Checks collaborator environment: git, LFS, sparse checkout, disk usage, key folders.
# Usage: ./validate_collaborator_setup.sh [repo_dir]
# Default repo_dir: BS_GodFile

REPO_DIR="${1:-BS_GodFile}"
ERRORS=0

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "FAIL: .git missing in $REPO_DIR"
  exit 2
fi

echo "==> Repo: $REPO_DIR"
cd "$REPO_DIR"

echo "==> Git status"
git status --short --branch || true

echo "==> Git LFS"
git lfs version || true
git lfs ls-files | head -n 5 || true

echo "==> Sparse checkout"
if git sparse-checkout list >/dev/null 2>&1; then
  git sparse-checkout list
else
  echo "Sparse checkout not active"
fi

echo "==> Key directories"
for d in Content Docs Source Plugins Config deploy; do
  if [ -d "$d" ]; then
    echo "OK: $d"
  else
    echo "FAIL: $d missing"
    ERRORS=$((ERRORS+1))
  fi
done

echo "==> Disk usage"
du -sh . 2>/dev/null || true

echo "==> Validation complete. Errors: $ERRORS"
if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi
exit 0