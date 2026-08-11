"""Audit Melusina material slots, effective Albedo, and texture weighting."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved/Audit/melusina_material_slots_current.json"
BODY = "/Game/Melodia/Characters/Melusina/SK_Melusina"
HAIR = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
HAIR_MI = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
TOON_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
WATER_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"


def _audit_mesh(unreal, path: str, require_albedo: bool) -> list[dict]:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    rows: list[dict] = []
    if not mesh:
        return rows
    for index, slot in enumerate(mesh.get_editor_property("materials") or []):
        material = slot.get_editor_property("material_interface") if slot else None
        name = str(slot.get_editor_property("material_slot_name")) if slot else str(index)
        parent = material.get_editor_property("parent") if isinstance(material, unreal.MaterialInstanceConstant) else None
        albedo = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, "Albedo") if isinstance(material, unreal.MaterialInstanceConstant) else None
        weight = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, "TextureWeight") if isinstance(material, unreal.MaterialInstanceConstant) else 0.0
        row = {
            "slot": index, "slot_name": name,
            "material": material.get_path_name() if material else None,
            "parent": parent.get_path_name() if parent else None,
            "albedo": albedo.get_path_name() if albedo else None,
            "albedo_resolves": bool(albedo and unreal.EditorAssetLibrary.does_asset_exist(albedo.get_path_name().split(".")[0])),
            "texture_weight": float(weight),
        }
        row["ok"] = bool(material and parent and (not require_albedo or (row["albedo_resolves"] and row["texture_weight"] > 0.0)))
        rows.append(row)
    return rows


def main() -> dict:
    import unreal

    body = _audit_mesh(unreal, BODY, True)
    hair = _audit_mesh(unreal, HAIR, False)
    body_ok = len(body) == 33 and all(row["ok"] and row["parent"].startswith(TOON_MASTER) for row in body)
    hair_ok = len(hair) == 4 and all(
        row["material"].startswith(HAIR_MI) and row["parent"].startswith(WATER_MASTER) for row in hair if row["material"] and row["parent"]
    )
    failures = []
    failures.extend(f"body slot {r['slot']} {r['slot_name']} ignores or lacks Albedo" for r in body if not r["ok"])
    if len(body) != 33:
        failures.append(f"expected 33 body slots, found {len(body)}")
    if not hair_ok:
        failures.append("all four hair slots do not resolve to MI_Melusina_WaterHair")
    result = {
        "body_mesh": BODY, "hair_mesh": HAIR,
        "body_slots": len(body), "hair_slots": len(hair),
        "procedural_exceptions": [],
        "body_ok": body_ok, "hair_ok": hair_ok,
        "failures": failures, "ok": body_ok and hair_ok and not failures,
        "body": body, "hair": hair,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Melusina material audit: " + json.dumps({"body_slots": len(body), "hair_slots": len(hair), "ok": result["ok"]}))
    return result


if __name__ == "__main__":
    main()
