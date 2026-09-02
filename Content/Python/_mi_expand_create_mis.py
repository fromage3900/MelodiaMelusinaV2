"""Create MI_Copernicus_<Variant> for all 30 Copernicus cymatic variants.

Every variant on disk ships BaseColor/Emissive/Height/Iridescence/Metallic/
Normal/ORM/Opacity/Roughness (some animated). Parents M_Master_Toon_Universal,
wires the canonical slots (Albedo/NormalMap/ORM/HeightMap/EmissiveMap +
Iridescence/OpacityMask where the master exposes them), sets schema-compliant
scalar defaults, then saves.

Channel->slot map (matches existing MI_Copernicus_* binaries):
  BaseColor   -> Albedo          (LayerA_TextureWeight=1, TextureWeight=1)
  Normal      -> NormalMap       (NormalStrength=1, sRGB off via texture asset)
  ORM         -> ORM
  Height      -> HeightMap
  Emissive    -> EmissiveMap
  Iridescence -> Iridescence     (where master exposes; else skipped)
  Opacity     -> OpacityMask     (where master exposes; else skipped)
  Roughness   -> (packed in ORM channel -> skip standalone)
  Metallic    -> (packed in ORM channel -> skip standalone)

Animated variants (81/117/153 pngs): use the BASE (no .N suffix) frame.
Only the first frame is wired to the static MI. Runtime material instancing /
MPC-driven flipbook is out of scope here.

Run in-editor:
  UnrealEditor-Cmd.exe BS_GodFile.uproject
    -ExecutePythonScript="Content/Python/_mi_expand_create_mis.py"
    -unattended -nullrhi

Manifest: Saved/Audit/copernicus_mi_create.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
SRC_ROOT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic"
DEST_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_mi_create.json"

TEX_ROOT = "/Game/EnvSandbox/Textures/Copernicus"

# Channel -> (master slot, sRGB on import already handled at texture asset level)
CHANNEL_SLOTS = {
    "BaseColor":   "Albedo",
    "Normal":      "NormalMap",
    "ORM":         "ORM",
    "Height":      "HeightMap",
    "Emissive":    "EmissiveMap",
    "Iridescence": "Iridescence",
    "Opacity":     "OpacityMask",
    # Roughness/Metallic intentionally skipped — ORM packs them
}

SERIAL_DEFAULTS = {
    "TextureWeight": 1.0,
    "LayerA_TextureWeight": 1.0,
    "UVScale": 1.0,
    "Roughness": 0.70,
    "Metallic": 0.0,
    "NormalStrength": 1.0,
    "NormalPower": 1.0,
    "TriplanarBlend": 0.0,
    "TriplanarTiling": 256.0,
    "LayerA_ParallaxScale": 1.0,
    "LayerA_NormalStrength": 1.0,
    "Iridescence": 0.5,
    "EmissiveStrength": 1.0,
    "HeightStrength": 1.0,
}


def base_png_for_channel(variant: str, channel: str) -> str | None:
    """Pick the BASE frame (no .N suffix) PNG for a given channel.
    PNG stem: T_Cymatic_<Variant>_<Channel>[.N].png -> asset stem."""
    tex_dir = f"{TEX_ROOT}/{variant}"
    if not unreal.EditorAssetLibrary.does_directory_exist(tex_dir):
        return None
    # List assets, find exact base match first, then fall back to any .N
    assets = unreal.EditorAssetLibrary.list_assets(tex_dir, recursive=False)
    target = f"T_Cymatic_{variant}_{channel}"
    # exact base frame first
    for a in assets:
        stem = a.rsplit("/", 1)[-1].split(".", 1)[0]
        if stem == target:
            return a
    # fall back to .1 first animated frame
    for a in assets:
        stem = a.rsplit("/", 1)[-1].split(".", 1)[0]
        if stem.startswith(target + "."):
            return a
    return None


def parameter_names(master) -> dict[str, set]:
    """Enumerate master parameter names by kind."""
    out: dict[str, set] = {"scalar": set(), "vector": set(), "texture": set(),
                           "switch": set(), "bool": set()}
    if master is None:
        return out
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(master)
    except Exception:
        return out
    for e in exprs or []:
        cls = type(e).__name__
        try:
            name = str(e.get_editor_property("parameter_name"))
        except Exception:
            continue
        if cls == "MaterialExpressionScalarParameter":
            out["scalar"].add(name)
        elif cls == "MaterialExpressionVectorParameter":
            out["vector"].add(name)
        elif cls == "MaterialExpressionStaticSwitchParameter":
            out["switch"].add(name)
        elif cls == "MaterialExpressionStaticBoolParameter":
            out["bool"].add(name)
        elif "Texture" in cls and "Parameter" in cls:
            out["texture"].add(name)
    return out


def create_mi(variant: str, master, params: dict[str, set]) -> dict:
    name = f"MI_Copernicus_{variant}"
    path = f"{DEST_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return {"variant": variant, "name": name, "status": "exists"}

    inst = unreal.EditorAssetLibrary.create_asset(
        name, DEST_DIR, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew(),
    )
    if inst is None:
        return {"variant": variant, "name": name, "status": "create_failed"}

    inst.set_editor_property("parent", master)

    wired = {}
    for channel, slot in CHANNEL_SLOTS.items():
        if slot not in params["texture"]:
            continue
        tex = base_png_for_channel(variant, channel)
        if tex is None:
            continue
        obj = unreal.load_asset(tex)
        if obj is None:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                inst, slot, obj
            )
            wired[slot] = tex
        except Exception as exc:
            print(f"[CREATE] wire fail {name}.{slot}: {exc}")

    # Schema scalar defaults
    applied_scalars = {}
    for pname, val in SERIAL_DEFAULTS.items():
        if pname not in params["scalar"]:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                inst, pname, float(val)
            )
            applied_scalars[pname] = val
        except Exception:
            pass

    # Ensure bLayerA_Active=True + LayerA_TextureWeight=1 (Atlantis-proven)
    for switch in ("bLayerA_Active", "bUseTextureLayerA"):
        if switch in params["switch"]:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                    inst, switch, True
                )
            except Exception:
                pass

    # Save
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(inst, True)
        status = "created"
    except Exception:
        status = "created_save_failed"

    return {
        "variant": variant, "name": name, "path": path, "status": status,
        "textures": wired, "scalars": applied_scalars,
    }


def main() -> int:
    master = unreal.EditorAssetLibrary.load_asset(MASTER)
    if master is None:
        print(f"[CREATE] ERROR master missing: {MASTER}")
        return 1
    params = parameter_names(master)
    print(f"[CREATE] master params -> scalars={len(params['scalar'])} "
          f"textures={len(params['texture'])} switches={len(params['switch'])}")

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_DIR):
        unreal.EditorAssetLibrary.make_directory(DEST_DIR)

    variants = sorted(
        d.name for d in SRC_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )
    print(f"[CREATE] {len(variants)} variants on disk -> create MIs")

    results = []
    counts = {"created": 0, "exists": 0, "failed": 0}
    for v in variants:
        r = create_mi(v, master, params)
        results.append(r)
        s = r["status"]
        if s == "created":
            counts["created"] += 1
        elif s == "exists":
            counts["exists"] += 1
        else:
            counts["failed"] += 1
        print(f"[CREATE] {s:24s} {r['name']}  wires={len(r.get('textures', {}))}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "dest_dir": DEST_DIR,
        "master_params": {k: sorted(v) for k, v in params.items()},
        "counts": counts,
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[CREATE] === {counts} === report -> {REPORT} ===")
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())