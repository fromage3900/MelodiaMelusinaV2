"""Phase E (binding-safe) — re-census mesh slots + unfinished MIs after quarantine.

Mirrors fix_pbr_pipeline.phase_e semantics but uses only APIs verified in this
UE 5.8 binding (AssetRegistry + load_asset + object property reads), since
MaterialEditingLibrary parameter getters are absent here.
"""
import json
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "Saved" / "Audit"
ENV = "/Game/EnvSandbox/Meshes/Environment"
STAGING = "/Game/EnvSandbox/Meshes/_staging_dedupe_2026-08-15"

ea = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()

BAD_MARKERS = ("NONE", "WorldGridMaterial", "MI_Universal_", "/ImportedPacks/MI_Env")


def list_assets(root: str, recursive=True):
    return ea.list_assets(root, recursive=recursive, include_folder=False)


def class_name(path: str) -> str:
    try:
        d = ea.find_asset_data(path)
        return str(d.asset_class_path.asset_name) if d and d.is_valid() else ""
    except Exception:
        return ""


def main():
    bad, unfinished = [], []
    meshes_seen = 0
    for root in (ENV, "/Game/EnvSandbox/Library/Migrated", "/Game/Library/Migrated"):
        if not ea.does_directory_exist(root):
            continue
        for p in list_assets(root):
            cls = class_name(p)
            if cls in ("StaticMesh", "SkeletalMesh"):
                meshes_seen += 1
                a = unreal.load_asset(p)
                if a is None:
                    continue
                mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
                for i, s in enumerate(mats):
                    mat = getattr(s, "material_interface", None)
                    mp = mat.get_path_name() if mat else "NONE"
                    if any(m in mp for m in BAD_MARKERS):
                        bad.append({"path": p, "slot": i, "name": str(getattr(s, "material_slot_name", "")), "mat": mp})
            elif cls == "MaterialInstanceConstant" and "/Meshes/Environment/" in p and "/ImportedPacks/" not in p:
                mic = unreal.load_asset(p)
                if not mic:
                    continue
                try:
                    parent = mic.get_editor_property("parent")
                    if parent is None:
                        continue
                    # LayerA convention check via direct override-array read (binding-safe)
                    vals = mic.get_editor_property("scalar_parameter_values")
                    tw = None
                    la = None
                    for v in vals:
                        name = v.get_editor_property("parameter_info").get_editor_property("name")
                        sv = str(name)
                        if sv == "LayerA_TextureWeight":
                            la = v.get_editor_property("parameter_value")
                        elif sv == "TextureWeight":
                            tw = v.get_editor_property("parameter_value")
                    ok = True
                    if la is not None and la != 1.0:
                        ok = False
                    if not ok:
                        unfinished.append(p)
                except Exception:
                    continue

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "Phase E binding-safe re-census after Phase D quarantine (718 twins staged)",
        "bad_slots": bad,
        "bad_slot_count": len(bad),
        "unfinished_mics": unfinished,
        "unfinished_mic_count": len(unfinished),
        "meshes_scanned": meshes_seen,
        "staging": STAGING,
        "note": "staged assets excluded from census by location (outside scan roots)",
    }
    (AUDIT / "full_pbr_sweep_2026-08-15.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k in ("bad_slot_count", "unfinished_mic_count", "meshes_scanned")}))


if __name__ == "__main__":
    time.sleep(5)
    main()
