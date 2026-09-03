"""Apply healthy stable tileable texture defaults to the four Melodia masters.

Phase 1 of the master-material polish. For each master:
  - force-wire catalog defaults (neutral normal/ORM/roughness/metallic/emissive
    first, real packs next) via portfolio_texture_catalog.apply_master_defaults
  - replace banned /Engine placeholder refs (DefaultTexture, Black.Black etc.)
  - scan and report banned / unwired / wrong_role violations
  - recompile + save, print a machine-parseable RESULT line

Run in the UE editor (Monolith editor_query run_python):
  run_python -> Content/Python/apply_healthy_master_defaults.py
"""
from __future__ import annotations

import json

import unreal

MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
]


def apply_to(material_path: str) -> dict:
    # Monolith run_python keeps a persistent interpreter: force-reload so this
    # run sees the latest catalog edits on disk.
    import importlib

    import material_lib as lib
    import portfolio_texture_catalog as catalog

    lib = importlib.reload(lib)
    catalog = importlib.reload(catalog)

    if not unreal.EditorAssetLibrary.does_asset_exist(material_path):
        return {"asset": material_path, "error": "asset_missing"}

    material = unreal.load_asset(material_path)
    if material is None:
        return {"asset": material_path, "error": "load_failed"}

    wired = catalog.apply_master_defaults(material, material_path, force=True)
    violations = catalog.scan_master_texture_violations(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    unreal.log(f"[healthy_defaults] {material_path} wired={len(wired)} violations={violations}")
    return {"asset": material_path, "wired": wired, "violations": violations}


def main() -> int:
    results = []
    for path in MASTERS:
        try:
            results.append(apply_to(path))
        except Exception as exc:  # noqa: BLE001 - one master failing must not stop the rest
            unreal.log_error(f"[healthy_defaults] {path}: {exc}")
            results.append({"asset": path, "error": str(exc)})
    # Machine-parseable sentinel line (Tools/ readers grep for this).
    print(f"HEALTHY_DEFAULTS_RESULT {json.dumps(results, default=str)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
