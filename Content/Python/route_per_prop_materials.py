"""Route proper maps/colors onto per-prop mesh materials.

For every prop under Content/EnvSandbox/Meshes/Environment/<prop>/Materials/:
  1. If the prop has Textures/ (imported colormap from its GLB): set Albedo =
     that colormap + TextureWeight=1.0 on every per-prop MIC.
  2. Else the source GLB is flat-color (unlit baseColorFactor): set BaseTint =
     the GLB material's color on the MIC whose name matches the GLB material
     name, keep TextureWeight at authored value (0 = flat tint path).

Writes Saved/Audit/per_prop_routing.json (dry-run safe: --dry-run).
"""
from __future__ import annotations

import json
import struct
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
IMPORTS = ROOT / "Imports" / "Environment"
OUT = ROOT / "Saved" / "Audit" / "per_prop_routing.json"


def glb_materials(glb: Path) -> dict[str, tuple[float, float, float]]:
    """Return {material_name: (r,g,b)} baseColorFactor for a GLB."""
    try:
        data = glb.read_bytes()
        idx = data.find(b"JSON")
        if idx < 0:
            return {}
        ln = struct.unpack("<I", data[idx - 4:idx])[0]
        js = json.loads(data[idx + 4:idx + 4 + ln].decode("utf-8", "ignore"))
        out = {}
        for m in js.get("materials") or []:
            name = m.get("name")
            fac = (m.get("pbrMetallicRoughness") or {}).get("baseColorFactor") or [1, 1, 1, 1]
            if name:
                out[name] = (fac[0], fac[1], fac[2])
        return out
    except Exception:
        return {}


def find_source_glb(prop: str) -> Path | None:
    for pack_dir in IMPORTS.iterdir():
        if not pack_dir.is_dir():
            continue
        glbs = list(pack_dir.rglob(f"{prop}.glb"))
        if glbs:
            return glbs[0]
        gltfs = list(pack_dir.rglob(f"{prop}.gltf"))
        if gltfs:
            return gltfs[0]
    return None


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    lib = unreal.MaterialEditingLibrary
    rows = []
    textured = colored = skipped = 0

    props = sorted(p for p in ENV_DIR.iterdir() if p.is_dir() and (p / "Materials").exists())
    for prop_dir in props:
        prop = prop_dir.name
        mats = sorted((prop_dir / "Materials").glob("*.uasset"))
        if not mats:
            continue
        tex_dir = prop_dir / "Textures"
        colormaps = sorted(tex_dir.glob("*.uasset")) if tex_dir.exists() else []
        glb = find_source_glb(prop) if not colormaps else None
        glb_colors = glb_materials(glb) if glb else {}

        for mpath in mats:
            game = "/Game/EnvSandbox/Meshes/Environment/" + prop + "/Materials/" + mpath.stem
            inst = unreal.load_asset(game)
            if not isinstance(inst, unreal.MaterialInstanceConstant):
                skipped += 1
                continue
            if colormaps:
                tex = unreal.load_asset(
                    "/Game/EnvSandbox/Meshes/Environment/" + prop + "/Textures/" + colormaps[0].stem
                )
                if tex:
                    if not dry:
                        lib.set_material_instance_texture_parameter_value(inst, "Albedo", tex)
                        lib.set_material_instance_scalar_parameter_value(inst, "TextureWeight", 1.0)
                        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
                    rows.append({"path": game, "mode": "textured", "albedo": colormaps[0].name})
                    textured += 1
            elif glb_colors:
                color = glb_colors.get(mpath.stem) or glb_colors.get(prop)
                if color:
                    if not dry:
                        lib.set_material_instance_vector_parameter_value(
                            inst, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0)
                        )
                        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
                    rows.append({"path": game, "mode": "flat_color", "color": color, "source_glb": glb.name})
                    colored += 1
            else:
                skipped += 1

    report = {
        "generated": "2026-08-13",
        "dry_run": dry,
        "rows": rows,
        "summary": {"textured": textured, "flat_color": colored, "skipped": skipped},
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"textured: {textured} | flat_color: {colored} | skipped: {skipped}")
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
