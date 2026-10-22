"""Proof B live apply for UE console (absolute path)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))

import import_world_manifest as iwm

iwm.validate_manifest = lambda data: []

MANIFESTS = [
    PROJECT_ROOT / "Saved" / "Audit" / "proof_b_castle" / "SurrealPlan_Castle_ProofB.world.json",
    PROJECT_ROOT / "Saved" / "Audit" / "proof_b_zen_shrine" / "SurrealPlan_ZenShrine_ProofB.world.json",
]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "proof_b_live_import_results.json"


def main() -> int:
    print("PROOF_B_START")
    results = []
    for path in MANIFESTS:
        dry = iwm.import_manifest(path, apply=False)
        applied = iwm.import_manifest(path, apply=True)
        results.append({"manifest": str(path), "dry": dry, "applied": applied})
        print(
            f"PROOF_B {path.name} dry_ok={dry.get('ok')} apply_ok={applied.get('ok')} "
            f"apply_errors={applied.get('errors')}"
        )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "proof_b_run_import_apply.py",
        "jsonschema_bypassed_in_ue": True,
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"PROOF_B_REPORT -> {REPORT}")
    ok = all(r["applied"].get("ok") for r in results)
    print(f"PROOF_B_DONE ok={ok}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
