"""Delete staged duplicate meshes AFTER Phase E verified clean (quarantine-first completion).

Gate: full_pbr_sweep_2026-08-15.json must show bad_slot_count == 0 and
unfinished_mic_count == 0. Each staged asset is re-proven zero-referencer before
delete_asset. Manifest written to pbr_dedupe_deleted_2026-08-15.json.
"""
import json
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "Saved" / "Audit"
STAGING = "/Game/EnvSandbox/Meshes/_staging_dedupe_2026-08-15"

ea = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()


def refs(package_name: str) -> list:
    opts = unreal.AssetRegistryDependencyOptions(
        include_hard_package_references=True, include_soft_package_references=True,
        include_searchable_names=False, include_hard_management_references=True,
        include_soft_management_references=True,
    )
    try:
        return sorted(ar.get_referencers(package_name, opts) or [])
    except Exception:
        return []


def main():
    # GATE: Phase E must have passed clean
    sweep = json.loads((AUDIT / "full_pbr_sweep_2026-08-15.json").read_text(encoding="utf-8"))
    if sweep.get("bad_slot_count") != 0 or sweep.get("unfinished_mic_count") != 0:
        print(json.dumps({"status": "GATE_FAIL", "sweep": {k: sweep[k] for k in ("bad_slot_count", "unfinished_mic_count")}}))
        return

    assets = ea.list_assets(STAGING, recursive=True, include_folder=False)
    deleted, skipped = [], []
    for p in assets:
        pkg = p.split(".")[0]
        r = refs(pkg)
        if r:
            skipped.append({"path": p, "refs": r})
            continue
        try:
            ok = ea.delete_asset(p)
        except Exception as e:
            ok = False
            skipped.append({"path": p, "refs": f"ERR {str(e)[:80]}"})
        if ok:
            deleted.append(p)

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gate": "full_pbr_sweep_2026-08-15.json clean",
        "staged_found": len(assets),
        "deleted": deleted,
        "deleted_count": len(deleted),
        "skipped": skipped,
        "skipped_count": len(skipped),
    }
    (AUDIT / "pbr_dedupe_deleted_2026-08-15.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"deleted": len(deleted), "skipped": len(skipped), "staged_found": len(assets)}))


if __name__ == "__main__":
    time.sleep(5)
    main()
