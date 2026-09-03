"""Native-sweep delete of verified dead island expressions on the Universal master.

Uses unreal.MaterialEditingLibrary.delete_material_expression (the same native
path the review's Stage 3 sweep used) — Monolith's material_query delete_*
actions crash the editor on this material (observed 2026-08-16, twice).

Deletes ONLY nodes from Saved/Audit/verified_dead_islands.json that are still
present, in batches of N with recompile+save between batches. Every deletion is
idempotent (already-deleted nodes are skipped).

Run in the UE editor (Monolith editor_query run_python):
  Content/Python/sweep_universal_islands.py
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ASSET = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
VERIFIED = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "verified_dead_islands.json"
BATCH = 8


def main() -> int:
    if not VERIFIED.exists():
        print("SWEEP_RESULT []")
        return 1
    targets = json.loads(VERIFIED.read_text(encoding="utf-8"))

    material = unreal.load_asset(ASSET)
    if material is None:
        print("SWEEP_RESULT []")
        return 1

    exprs = unreal.MaterialEditingLibrary.get_material_expressions(material) or []
    by_name = {str(e.get_name()): e for e in exprs}
    present = [n for n in targets if n in by_name]
    print(f"targets={len(targets)} present={len(present)}")

    deleted: list[str] = []
    failed: list[str] = []
    for i in range(0, len(present), BATCH):
        batch = present[i:i + BATCH]
        for name in batch:
            expr = by_name.get(name)
            if expr is None:
                continue
            try:
                unreal.MaterialEditingLibrary.delete_material_expression(material, expr)
                deleted.append(name)
            except Exception as exc:  # noqa: BLE001
                unreal.log_error(f"[sweep] {name}: {exc}")
                failed.append(name)
        try:
            unreal.MaterialEditingLibrary.recompile_material(material)
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
        print(f"batch done: deleted_so_far={len(deleted)} failed={len(failed)}")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    unreal.log(f"[sweep_universal_islands] deleted={len(deleted)} failed={failed}")
    print(f"SWEEP_RESULT {json.dumps({'deleted': deleted, 'failed': failed})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
