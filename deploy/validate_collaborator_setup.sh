#!/usr/bin/env bash
set -euo pipefail

# validate_collaborator_setup.sh
# Checks collaborator environment: git, LFS, sparse checkout, disk usage, key folders.
# Usage: ./validate_collaborator_setup.sh [repo_dir]
# Default repo_dir: the checkout containing this script

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="${1:-$PROJECT_ROOT}"
ERRORS=0

if ! git -C "$REPO_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "FAIL: Git checkout not found at $REPO_DIR"
  exit 2
fi

REPO_ROOT="$(git -C "$REPO_DIR" rev-parse --show-toplevel)"
echo "==> Repo: $REPO_ROOT"
cd "$REPO_ROOT"

echo "==> Git status"
git status --short --branch || true

echo "==> Git LFS"
git lfs version || true
git lfs ls-files | awk 'NR <= 5 { print }' || true

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

if [ -f "BS_GodFile.uproject" ]; then
  echo "OK: BS_GodFile.uproject"
else
  echo "WARN: BS_GodFile.uproject missing (docs/code-only tier may omit it)"
fi

echo "==> Disk usage"
du -sh . 2>/dev/null || true

echo "==> Validation complete. Errors: $ERRORS"
if [ "$ERRORS" -ne 0 ]; then
  exit 1
fi
exit 0