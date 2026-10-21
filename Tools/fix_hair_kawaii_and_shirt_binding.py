"""Fix Melusina hair KawaiiPhysics head/face/neck/shoulder colliders (cm scale),
tune skirt KawaiiPhysics on ABP_Melusina_Current, and bind ShirtMesh/HatMesh in DA_MelodiaCosmeticCatalog.

Does NOT load/switch levels or touch L_MelusinaMorning dirty external actors.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())


def clear_readonly(asset_path: str) -> None:
    if asset_path.startswith("/Game/"):
        rel = asset_path.replace("/Game/", "Content/") + ".uasset"
    elif asset_path.startswith("/MelodiaWardrobe/"):
        rel = asset_path.replace("/MelodiaWardrobe/", "Plugins/MelodiaWardrobe/Content/") + ".uasset"
    else:
        return
    disk = PROJECT / rel
    if disk.is_file():
        os.chmod(disk, stat.S_IWRITE)


def fix_hair_limits() -> dict:
    da_path = "/Game/Melodia/Characters/Melusina/Physics/DA_Melusina_HairCollisionLimits"
    da = unreal.load_asset(da_path)
    if not da:
        return {"ok": False, "error": "DA_Melusina_HairCollisionLimits not found"}

    info = {"asset": da_path, "updated_fields": []}
    for prop_name in ("spherical_limits",):
        try:
            spheres = list(da.get_editor_property(prop_name))
        except Exception:
            continue
        if spheres:
            s0 = spheres[0]
            s0.set_editor_property("offset_location", unreal.Vector(0.0, -4.5, 4.0))
            s0.set_editor_property("radius", 17.5)
            spheres[0] = s0
            da.set_editor_property(prop_name, spheres)
            info["updated_fields"].append(prop_name)

    for prop_name in ("capsule_limits",):
        try:
            caps = list(da.get_editor_property(prop_name))
        except Exception:
            continue
        if len(caps) >= 3:
            presets = [
                (unreal.Vector(0.0, -7.5, -4.0), 13.5, 14.0),
                (unreal.Vector(0.0, 2.0, -14.0), 9.5, 22.0),
                (unreal.Vector(0.0, 6.0, -28.0), 14.5, 24.0),
            ]
            for idx, (loc, rad, length) in enumerate(presets):
                c = caps[idx]
                c.set_editor_property("offset_location", loc)
                c.set_editor_property("radius", rad)
                c.set_editor_property("length", length)
                caps[idx] = c
            da.set_editor_property(prop_name, caps)
            info["updated_fields"].append(prop_name)

    clear_readonly(da_path)
    info["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(da, False))
    return info


def fix_hair_abp() -> dict:
    abp_path = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
    abp = unreal.load_asset(abp_path)
    klass = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    if not abp or not klass:
        return {"ok": False, "error": "ABP or AnimGraphNode_KawaiiPhysics unavailable"}
    nodes = list(abp.get_nodes_of_class(klass))
    if not nodes:
        return {"ok": False, "error": "No KawaiiPhysics nodes in ABP_Melusina_WaterHair"}
    graph_node = nodes[0]
    node = graph_node.get_editor_property("node")
    settings = node.get_editor_property("physics_settings")
    settings.damping = 0.28
    settings.stiffness = 0.16
    settings.world_damping_location = 0.65
    settings.world_damping_rotation = 0.65
    settings.limit_angle = 36.0
    settings.radius = 3.2
    node.set_editor_property("physics_settings", settings)
    graph_node.set_editor_property("node", node)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    clear_readonly(abp_path)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(abp, False))
    return {
        "asset": abp_path,
        "saved": saved,
        "settings": {
            "damping": float(settings.damping),
            "stiffness": float(settings.stiffness),
            "world_damping_location": float(settings.world_damping_location),
            "world_damping_rotation": float(settings.world_damping_rotation),
            "limit_angle": float(settings.limit_angle),
            "radius": float(settings.radius),
        },
    }


def fix_cosmetic_catalog() -> dict:
    cat_path = "/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog"
    cat = unreal.load_asset(cat_path)
    if not cat:
        return {"ok": False, "error": "DA_MelodiaCosmeticCatalog not found"}
    shirt_flared = unreal.load_asset("/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Shirt_Flared")
    hat_fixed = unreal.load_asset("/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Hat_Fixed")
    skirt_smooth = unreal.load_asset("/Game/Melodia/Characters/Melusina/Outfits/V2/Polish_20260920/SK_Melusina_V2_Skirt_R2_SmoothChains")
    cosmetics = list(cat.get_editor_property("cosmetics"))
    entries = []
    changed = []
    for i, entry in enumerate(cosmetics):
        props = [p for p in dir(entry) if not p.startswith("_")]
        mesh_prop = "skeletal_mesh" if "skeletal_mesh" in props else ("mesh" if "mesh" in props else None)
        id_prop = "cosmetic_id" if "cosmetic_id" in props else ("item_id" if "item_id" in props else None)
        cid = str(entry.get_editor_property(id_prop)) if id_prop else str(i)
        mesh = entry.get_editor_property(mesh_prop) if mesh_prop else None
        mpath = str(mesh.get_path_name()) if mesh else ""
        entries.append({"index": i, "id": cid, "mesh_prop": mesh_prop, "mesh": mpath})
        if mesh_prop and ("SK_Melusina_V2_Shirt." in mpath or "shirt" in cid.lower()) and shirt_flared and mpath != str(shirt_flared.get_path_name()):
            entry.set_editor_property(mesh_prop, shirt_flared)
            cosmetics[i] = entry
            changed.append((cid, str(shirt_flared.get_path_name())))
        elif mesh_prop and ("SK_Melusina_V2_Hat." in mpath) and hat_fixed and mpath != str(hat_fixed.get_path_name()):
            entry.set_editor_property(mesh_prop, hat_fixed)
            cosmetics[i] = entry
            changed.append((cid, str(hat_fixed.get_path_name())))
        elif mesh_prop and ("SK_Melusina_V2_Skirt." in mpath) and skirt_smooth and mpath != str(skirt_smooth.get_path_name()):
            entry.set_editor_property(mesh_prop, skirt_smooth)
            cosmetics[i] = entry
            changed.append((cid, str(skirt_smooth.get_path_name())))

    saved = False
    if changed:
        cat.set_editor_property("cosmetics", cosmetics)
        clear_readonly(cat_path)
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(cat, False))
    return {"asset": cat_path, "entries": entries, "changed": changed, "saved": saved}


def main():
    report = {
        "hair_limits": fix_hair_limits(),
        "hair_abp": fix_hair_abp(),
        "cosmetic_catalog": fix_cosmetic_catalog(),
    }
    print("HAIR_AND_SHIRT_FIX=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
