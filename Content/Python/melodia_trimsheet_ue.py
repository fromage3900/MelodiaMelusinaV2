"""Create MI_TS_Melodia_* instances on M_Master_Toon_Universal from the
Trim Sheet Lab manifest. Companion to setup_trimsheet_instances.py — same
material_lib helpers, same headless/editor dual entry, DIFFERENT source:
textures come from Saved/TrimSheets/out (baked by the Blender addon), not
/Games/Textures/ZenTrim_*.

Run (editor):   py Content/Python/melodia_trimsheet_ue.py
Headless:       python Content/Python/melodia_trimsheet_ue.py
Requires first: import the sheet PNGs — this script does it via
                unreal.AssetImportTask from the manifest paths.

Manifest: Saved/TrimSheets/out/trimsheet_manifest.json (written by the
melodia_ts.bake operator in surreal_arch/trim_sheet_lab.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
TEXTURE_FOLDER = "/Game/Textures/MelodiaTrimSheets"
INSTANCE_FOLDER = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized"
MANIFEST = PROJECT_ROOT / "Saved" / "TrimSheets" / "out" / "trimsheet_manifest.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_trimsheet_ue.json"

# master texture parameter names (zen family contract; verified in
# zen_trim_textures.variant_maps)
CHANNEL_PARAM = {
    "_albedo.png": "Albedo",
    "_normal.png": "NormalMap",
    "_height.png": "HeightMap",
    "_orm.png": "ORM",
    "_emission.png": "EmissiveMap",
}
LAYERB_PARAM = {
    "_albedo.png": "LayerB_Albedo",
    "_normal.png": "LayerB_NormalMap",
    "_height.png": "LayerB_HeightMap",
    "_orm.png": "LayerB_ORM",
}
Srgb = {
    "_albedo.png": True,
    "_normal.png": False,
    "_height.png": False,
    "_orm.png": False,
    "_emission.png": True,
}


def _import_textures(unreal) -> dict[str, str]:
    """Import every baked PNG under TEXTURE_FOLDER as T_<Sheet><Channel>."""
    imported: dict[str, dict[str, str]] = {}
    manifest = json.loads(MANIFEST.read_text())
    out_dir = MANIFEST.parent
    ed = unreal.EditorAssetLibrary
    for sheet in manifest["sheets"]:
        for suffix, param in CHANNEL_PARAM.items():
            png = out_dir / f"{sheet}{suffix}"
            if not png.exists():
                print(f"TRIMSHEET_SKIP missing {png.name}")
                continue
            name = f"T_{sheet}{suffix.removesuffix('.png').replace('_', '')}"
            dest = f"{TEXTURE_FOLDER}/{name}"
            if ed.does_asset_exist(dest):
                imported.setdefault(sheet, {})[param] = f"{dest}.{name}"
                continue
            task = unreal.AssetImportTask()
            task.filename = str(png)
            task.destination_path = TEXTURE_FOLDER
            task.destination_name = name
            task.automated = True
            task.save = True
            try:
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            except Exception as exc:  # noqa: BLE001 - report, keep going
                print(f"TRIMSHEET_IMPORT_FAIL {png.name}: {exc}")
                continue
            if not ed.does_asset_exist(dest):
                print(f"TRIMSHEET_IMPORT_MISS {dest}")
                continue
            tex = ed.load_asset(dest)
            settings = getattr(tex, "srgb", None)
            if settings is not None:
                tex.srgb = Srgb[suffix]
                ed.save_package(dest)
            imported.setdefault(sheet, {})[param] = f"{dest}.{name}"
    return imported


def build() -> list[dict]:
    import material_lib as lib
    import unreal

    if not MANIFEST.exists():
        raise RuntimeError(f"missing manifest {MANIFEST} — run melodia_ts.bake in Blender first")
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master: {MASTER} — run setup_master_universal.py first")

    manifest = json.loads(MANIFEST.read_text())
    imported = _import_textures(unreal)
    results: list[dict] = []
    for sheet, info in manifest["sheets"].items():
        recipe = info["ue"]
        inst = lib.create_material_instance(f"MI_{sheet}", INSTANCE_FOLDER, MASTER)
        for pname, rgba in recipe.get("vectors", {}).items():
            lib.set_instance_vector(inst, pname, rgba)
        scalars = dict(recipe.get("scalars", {}))
        # schema 2: height-compete numbers for the wear Layer B
        for pname, value in (info.get("lerp") or {}).items():
            scalars[pname] = value
        if "emission" in info:
            ev = info["emission"]
            scalars["EmissiveStrength"] = ev.get("strength", 1.5)
            lib.set_instance_vector(inst, "EmissiveTint", ev.get("color", (1, .85, .4, 1)))
        for pname, value in scalars.items():
            lib.set_instance_scalar(inst, pname, value)
        wired = {}
        for param, path in imported.get(sheet, {}).items():
            resolved = lib.set_instance_texture(inst, param, [path])
            if resolved:
                wired[param] = resolved
        # Layer B = shared wear set (set_instance_texture is a no-op when the
        # master lacks the param; no parallel shader authority is created)
        wear = info.get("wear_layer_b")
        if wear:
            for suffix, param in LAYERB_PARAM.items():
                path = imported.get(wear, {}).get(
                    {"_albedo.png": "Albedo", "_normal.png": "NormalMap",
                     "_height.png": "HeightMap", "_orm.png": "ORM"}[suffix])
                if path:
                    resolved = lib.set_instance_texture(inst, param, [path])
                    if resolved:
                        wired[param] = resolved
        lib.save_package(inst)
        results.append({
            "instance": f"MI_{sheet}",
            "path": lib.asset_path(INSTANCE_FOLDER, f"MI_{sheet}"),
            "master": MASTER.split(".")[-1],
            "textures_wired": wired,
            "recipe": recipe,
            "status": "created_or_updated",
        })
    return results


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    if not _in_ue():
        if not UE_CMD.exists():
            print("ERROR: UE 5.8 not found; run inside the editor: py Content/Python/melodia_trimsheet_ue.py")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "melodia_trimsheet_ue.log"
        cmd = [str(UE_CMD), str(UPROJECT), "-run=pythonscript",
               f"-script='{Path(__file__)}'", "-stdout", "-unattended", "-nopause"]
        print("LAUNCH", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        print(proc.stdout[-4000:])
        return 0 if proc.returncode == 0 else 2
    results = build()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=1))
    for r in results:
        print(f"TRIMSHEET_MI {r['instance']} textures={len(r['textures_wired'])} -> {r['path']}")
    print(f"TRIMSHEET_REPORT {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
