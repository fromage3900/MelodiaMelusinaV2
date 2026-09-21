# -*- coding: utf-8 -*-
"""Faraway Mother Stage 2 — wire MI_Mother_* + Copernicus Faraway sheets from live cymatic PNGs.
Parents: silk/velvet -> M_Master_Nikki; opaque -> M_Master_Toon_Universal; alpha lace -> M_Master_Toon_Universal_Alpha.
Consume MPC_Cymatics_Driver only (never write). LV_FarawayMother_Prototype only. No Morning.
"""
from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "faraway_mother_stage2_mi_2026-09-21.json"
CYM = Path(unreal.Paths.project_saved_dir()) / "Audit" / "copernicus_cymatic"
TEX_ROOT = "/Game/EnvSandbox/Textures/Copernicus/Faraway"
MI_P2 = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2"
MI_COP = "/Game/EnvSandbox/Materials/Instances/Copernicus"

PARENTS = {
    "nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "alpha": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha",
}
# Fallbacks if EnvSandbox masters missing
PARENT_FALLBACKS = {
    "nikki": [
        "/Game/Melodia/_PROJECT/Materials/Masters/M_Master_Nikki",
        "/Game/Melodia/Materials/Masters/M_Master_Nikki",
    ],
    "universal": [
        "/Game/Melodia/_PROJECT/Materials/Masters/M_Master_Toon_Universal",
        "/Game/Melodia/Materials/Masters/M_Master_Toon_Universal",
    ],
    "alpha": [
        "/Game/Melodia/_PROJECT/Materials/Masters/M_Master_Toon_Universal_Alpha",
        "/Game/Melodia/Materials/Masters/M_Master_Toon_Universal_Alpha",
    ],
}

# Suite binding: Mother MI -> (family, parent_key, sheen, pastel)
SUITE = {
    "MI_Mother_Mantle": ("FarawayNightVelvet", "nikki", 0.40, 0.55),
    "MI_Mother_Gown": ("FarawayCelestialSilk", "nikki", 0.55, 0.65),
    "MI_Mother_Veil": ("FarawayAquaLace", "alpha", 0.45, 0.60),
    "MI_Mother_Corset": ("FarawayGildedRidge", "universal", 0.35, 0.50),
}

ACTOR_MI = {
    "FM_Ridge_HeadSilhouette_01": "MI_Mother_Mantle",
    "FM_Ridge_Fabric_02": "MI_Mother_Gown",
    "FM_Hair_Cascade_03": "MI_Mother_Veil",
    "FM_Ridge_Fabric_04": "MI_Mother_Gown",
    "FM_Valley_Shoulder_05": "MI_Mother_Corset",
    "FM_Valley_Torso_06": "MI_Mother_Corset",
    "FM_Haze_Limbs_07": None,  # already Copernicus MoonChiffon — rebind that MI only
}

MAP_SUFFIX = {
    "BaseColor": "_BaseColor",
    "Normal": "_Normal",
    "ORM": "_ORM",
    "Roughness": "_Roughness",
    "Metallic": "_Metallic",
    "Height": "_Height",
    "Emissive": "_Emissive",
    "Sheen": "_Sheen",
    "Iridescence": "_Iridescence",
    "Opacity": "_Opacity",
    "AO": "_AO",
}

# Common param name aliases on Melodia masters
TEX_PARAM_CANDIDATES = {
    "BaseColor": ["BaseColor", "Base Color", "Albedo", "Diffuse", "Color"],
    "Normal": ["Normal", "NormalMap", "Normal Map"],
    "ORM": ["ORM", "OcclusionRoughnessMetallic", "PackedORM"],
    "Roughness": ["Roughness", "RoughnessMap"],
    "Metallic": ["Metallic", "MetallicMap"],
    "Height": ["Height", "HeightMap", "Displacement"],
    "Emissive": ["Emissive", "EmissiveMap", "Emissive Color"],
    "Sheen": ["SheenMask", "Sheen", "SheenMap", "FabricSheen"],
    "Opacity": ["Opacity", "OpacityMask", "Alpha"],
}

SCALAR_SHEEN = ["NikkiPearlSheen", "PearlSheen", "SheenAmount", "FabricSheen"]
SCALAR_PASTEL = ["NikkiPastelStrength", "PastelStrength", "NikkiPastel"]


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _ensure_dir(game_path):
    if not EAL.does_directory_exist(game_path):
        EAL.make_directory(game_path)


def _find_parent(key):
    paths = [PARENTS[key]] + PARENT_FALLBACKS.get(key, [])
    for p in paths:
        if EAL.does_asset_exist(p):
            return p, EAL.load_asset(p)
    return None, None


def _import_texture(png: Path, dest_path: str):
    if EAL.does_asset_exist(dest_path):
        return dest_path, EAL.load_asset(dest_path), "existed"
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = str(Path(dest_path).parent).replace("\\", "/")
    if not task.destination_path.startswith("/"):
        # dest_path is /Game/...
        parts = dest_path.rsplit("/", 1)
        task.destination_path = parts[0]
        task.destination_name = parts[-1]
    else:
        task.destination_name = dest_path.rsplit("/", 1)[-1]
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if EAL.does_asset_exist(dest_path):
        return dest_path, EAL.load_asset(dest_path), "imported"
    # try without T_ prefix mismatch
    return dest_path, None, "import_failed"


def _set_tex(mi, logical, tex):
    if not tex:
        return False
    for name in TEX_PARAM_CANDIDATES.get(logical, [logical]):
        try:
            if MEL.set_material_instance_texture_parameter_value(mi, name, tex):
                return True
        except Exception:
            try:
                MEL.set_material_instance_texture_parameter_value(mi, unreal.Name(name), tex)
                return True
            except Exception:
                pass
    return False


def _set_scalar(mi, candidates, value):
    for name in candidates:
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, name, float(value))
            return name
        except Exception:
            try:
                MEL.set_material_instance_scalar_parameter_value(mi, unreal.Name(name), float(value))
                return name
            except Exception:
                pass
    return None


def _ensure_mi(name, parent_path, parent_asset):
    path = f"{MI_P2}/{name}"
    if EAL.does_asset_exist(path):
        mi = EAL.load_asset(path)
        try:
            MEL.set_material_instance_parent(mi, parent_asset)
        except Exception:
            pass
        return path, mi, "reused"
    _ensure_dir(MI_P2)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = asset_tools.create_asset(name, MI_P2, unreal.MaterialInstanceConstant, factory)
    if not mi:
        return path, None, "create_failed"
    try:
        MEL.set_material_instance_parent(mi, parent_asset)
    except Exception:
        pass
    EAL.save_asset(path)
    return path, mi, "created"


def _wire_family(mi, family, sheen, pastel):
    report = {"family": family, "textures": {}, "scalars": {}}
    folder = CYM / family
    if not folder.exists():
        report["error"] = f"missing_folder:{folder}"
        return report
    _ensure_dir(TEX_ROOT + "/" + family)
    for logical, suf in MAP_SUFFIX.items():
        # T_Cymatic_<Family><suf>.png
        png = folder / f"T_Cymatic_{family}{suf}.png"
        if not png.exists():
            # try without T_Cymatic_ prefix variants
            alts = list(folder.glob(f"*{suf}.png"))
            png = alts[0] if alts else None
        if not png or not Path(png).exists():
            report["textures"][logical] = "missing_png"
            continue
        dest = f"{TEX_ROOT}/{family}/T_Cymatic_{family}{suf}"
        dpath, tex, st = _import_texture(Path(png), dest)
        ok = _set_tex(mi, logical, tex)
        report["textures"][logical] = {"path": dpath, "import": st, "bound": ok}
    sn = _set_scalar(mi, SCALAR_SHEEN, sheen)
    sp = _set_scalar(mi, SCALAR_PASTEL, pastel)
    report["scalars"]["sheen"] = {"name": sn, "value": sheen}
    report["scalars"]["pastel"] = {"name": sp, "value": pastel}
    try:
        MEL.update_material_instance(mi)
        report["updated"] = True
    except Exception as e:
        report["updated"] = str(e)
    return report


def _apply_to_actors(mi_by_name):
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    applied = []
    for a in svc.get_all_level_actors():
        lab = _lab(a)
        if lab not in ACTOR_MI:
            continue
        mi_name = ACTOR_MI[lab]
        if mi_name is None:
            # haze: keep Copernicus MoonChiffon path if present on mesh
            applied.append({"actor": lab, "skipped": "uses_MoonChiffon"})
            continue
        mi = mi_by_name.get(mi_name)
        if not mi:
            applied.append({"actor": lab, "error": "mi_missing"})
            continue
        ok = False
        try:
            # StaticMeshActor
            smc = a.get_component_by_class(unreal.StaticMeshComponent)
            if smc:
                smc.set_material(0, mi)
                ok = True
        except Exception as e:
            applied.append({"actor": lab, "error": str(e)})
            continue
        applied.append({"actor": lab, "mi": mi_name, "ok": ok})
    return applied


def _save_all(paths):
    pkgs = []
    for p in paths:
        try:
            pkgs.append(EAL.load_asset(p))
        except Exception:
            pass
    try:
        unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, False)
        return True, len(pkgs)
    except Exception as e:
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            return True, "dirty"
        except Exception as e2:
            return False, f"{e}|{e2}"


def main():
    report = {
        "schema": "melodia.faraway_mother.stage2_mi.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype",
        "mpc_policy": "consume_only",
        "parents": {},
        "mis": {},
        "alabaster_fix": {},
        "applied": [],
        "ok": False,
    }
    # resolve parents
    parents = {}
    for k in ("nikki", "universal", "alpha"):
        path, asset = _find_parent(k)
        report["parents"][k] = path
        parents[k] = asset
        if not asset:
            report["error"] = f"missing_parent:{k}"
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("STAGE2_ERR missing parent", k)
            return 1

    mi_by_name = {}
    saved_paths = []
    for mi_name, (family, pkey, sheen, pastel) in SUITE.items():
        path, mi, st = _ensure_mi(mi_name, PARENTS[pkey], parents[pkey])
        entry = {"path": path, "status": st}
        if not mi:
            entry["error"] = "no_mi"
            report["mis"][mi_name] = entry
            continue
        entry["wire"] = _wire_family(mi, family, sheen, pastel)
        mi_by_name[mi_name] = mi
        saved_paths.append(path)
        report["mis"][mi_name] = entry

    # Fix AlabasterDrape under-wire (tiny MI)
    alb_path = f"{MI_COP}/MI_Copernicus_FarawayAlabasterDrape"
    if EAL.does_asset_exist(alb_path):
        alb = EAL.load_asset(alb_path)
        try:
            MEL.set_material_instance_parent(alb, parents["nikki"])
        except Exception:
            pass
        report["alabaster_fix"] = _wire_family(alb, "FarawayAlabasterDrape", 0.50, 0.60)
        saved_paths.append(alb_path)
    else:
        report["alabaster_fix"] = {"error": "mi_missing"}

    # MoonChiffon sheen touch for haze actor
    moon_path = f"{MI_COP}/MI_Copernicus_FarawayMoonChiffon"
    if EAL.does_asset_exist(moon_path):
        moon = EAL.load_asset(moon_path)
        report["moonchiffon"] = _wire_family(moon, "FarawayMoonChiffon", 0.45, 0.55)
        saved_paths.append(moon_path)

    report["applied"] = _apply_to_actors(mi_by_name)
    ok_save, n = _save_all(saved_paths)
    report["save"] = {"ok": ok_save, "detail": n}
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        # also force packages
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["ok"] = all(
        (v.get("status") in ("created", "reused")) for v in report["mis"].values()
    )
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("STAGE2_MI " + json.dumps({
        "ok": report["ok"],
        "mis": list(report["mis"]),
        "applied": len(report["applied"]),
        "out": str(OUT),
    }))
    unreal.log("STAGE2_MI wrote " + str(OUT))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
