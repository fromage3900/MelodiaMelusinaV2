#!/usr/bin/env bash
# Collaborator Onboarding — MelodiaMelusinaV2
# Usage: ./deploy/collaborator_onboarding.sh [tier]
# Tiers:
#   docs50      — ≤50 MB docs/source/Python (Echo author/spec text)
#   slice50     — ≤50 MB MelodiaIntegration BP slice
#   placement50 — Universal BP physics placement (target ≤50 MB; EnvSandbox may be missing on cloud)
#   gameplay    — Melodia+EnvSandbox+JRPG (~2 GB)  [alias: lightweight]
#   full        — all LFS
#   docs        — alias of docs50
# Default: docs50

set -euo pipefail

TIER="${1:-docs50}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_DIR="$REPO_DIR/specs/collab_slices"

# Aliases
case "$TIER" in
  docs) TIER=docs50 ;;
  lightweight) TIER=gameplay ;;
esac

case "$TIER" in
  docs50|slice50|placement50|gameplay|full)
    ;;
  *)
    echo "Unknown tier: $TIER"
    echo "Supported: docs50 slice50 placement50 gameplay full"
    exit 1
    ;;
esac

echo "==> Tier: $TIER"
echo "==> Repo: $REPO_DIR (public: https://github.com/fromage3900/MelodiaMelusinaV2)"
echo "==> Tip: git config core.hooksPath .githooks"

cd "$REPO_DIR"
git lfs install || true

apply_manifest() {
  local id="$1"
  local man="$MANIFEST_DIR/${id}.json"
  if [ ! -f "$man" ]; then
    echo "ERROR: missing manifest $man"
    exit 1
  fi
  echo "==> Using manifest $man"
  # sparse paths
  python3 - <<PY
import json
from pathlib import Path
man = json.loads(Path("$man").read_text())
paths = man.get("sparse_checkout", [])
print("\n".join(paths))
PY
  mapfile -t SPARSE < <(python3 - <<PY
import json
from pathlib import Path
man = json.loads(Path("$man").read_text())
for p in man.get("sparse_checkout", []):
    print(p)
PY
)
  git sparse-checkout init --cone || true
  git sparse-checkout set "${SPARSE[@]}" || true

  INCLUDE=$(python3 - <<PY
import json
from pathlib import Path
man = json.loads(Path("$man").read_text())
print(",".join(man.get("lfs_include", [])))
PY
)
  if [ -n "$INCLUDE" ]; then
    echo "==> git lfs pull --include=$INCLUDE"
    git lfs pull --include="$INCLUDE" || true
  fi
  python3 "$REPO_DIR/Tools/lfs_health_audit.py" --manifest "$man" || {
    echo "WARN: manifest budget/required check returned non-zero (see above)."
    # docs50/slice50 should hard-fail on budget; placement50 may miss EnvSandbox on cloud
    if [ "$id" != "placement50" ]; then
      exit 1
    fi
  }
}

if [ "$TIER" = "full" ]; then
  echo "==> Full LFS pull"
  git lfs pull
  echo "==> Onboarding complete for tier: $TIER"
  exit 0
fi

if [ "$TIER" = "gameplay" ]; then
  echo "==> Gameplay tier (~2 GB Melodia+EnvSandbox+JRPG) — not a 50 MB slice"
  git sparse-checkout init --cone || true
  git sparse-checkout set \
    Content/Melodia \
    Content/EnvSandbox \
    Content/MelodiaIntegration \
    Content/TurnBasedJRPGTemplate \
    Plugins/MelodiaCore/Source \
    Docs Source Config Tools deploy specs Content/Python || true
  git lfs pull --include="Content/Melodia/**,Content/EnvSandbox/**,Content/MelodiaIntegration/**,Content/TurnBasedJRPGTemplate/**" || true
  echo "==> Onboarding complete for tier: $TIER"
  exit 0
fi

apply_manifest "$TIER"
echo "==> Onboarding complete for tier: $TIER"
echo "==> Echo: gameplay claims need ledger rows (python Tools/echo_run.py status)"
echo "==> Lock binaries before edit: git lfs lock <path>"
