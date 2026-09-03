"""Route real-or-neutral maps onto every textured MI (2026-08-14 deep pass).

Every mesh-referenced MI with TextureWeight=1.0 and a real Albedo currently
inherits the master's noise defaults for NormalMap/ORM/HeightMap/RoughnessMap/
MetallicMap (the sbs_-_ / Marble packs). Those defaults are sampled once each
in the master and feed the final normal/roughness/metallic chains, so textured
surfaces pick up abstract noise maps.

Fix per MI, per core map:
  1. If the MI already overrides the map -> keep (author or earlier pass).
  2. If the MI's pack provides a real map for this slot -> route it
     (AvatarGarden atlas normals/metallics/AO).
  3. Else route the neutral utility texture
     (/Game/EnvSandbox/Textures/Utility/T_Neutral_*).

Neutral set (imported 2026-08-14):
  NormalMap    -> T_Neutral_Normal (128,128,255 flat)
  ORM          -> T_Neutral_ORM (white: AO=1, R=0, M=0)
  HeightMap    -> T_Neutral_Height (128 grey, no displacement)
  RoughnessMap -> T_Neutral_Roughness (160 grey)
  MetallicMap  -> T_Neutral_Metallic (black)

Run in the UE editor (Monolith run_python): route_neutral_maps.main()
Writes: Saved/Audit/neutral_map_routing_2026-08-14.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "neutral_map_routing_2026-08-14.json"
UTIL = "/Game/EnvSandbox/Textures/Utility"
ROOTS = ["/Game/EnvSandbox/Meshes", "/Game/EnvSandbox/Library", "/Game/Library"]

NOISE_MARKERS = ("sbs_-_", "DefaultTexture", "Black.Black", "/Marble/", "Marble_")
NEUTRAL = {
    "NormalMap": f"{UTIL}/T_Neutral_Normal",
    "ORM": f"{UTIL}/T_Neutral_ORM",
    "HeightMap": f"{UTIL}/T_Neutral_Height",
    "RoughnessMap": f"{UTIL}/T_Neutral_Roughness",
    "MetallicMap": f"{UTIL}/T_Neutral_Metallic",
    "EmissiveMap": f"{UTIL}/T_Neutral_ORM",  # white would glow - use black instead
}
# EmissiveMap neutral should be BLACK (no emission), not white.
NEUTRAL["EmissiveMap"] = f"{UTIL}/T_Neutral_Metallic"

# per-pack real-map sources keyed by exact texture asset names
AG = "/Game/EnvSandbox/Textures/PackTextures/AvatarGarden"
GOTHIC = "/Game/EnvSandbox/Textures/PackTextures/GothicCastle"


def used_mi_paths():
    used = set()
    for root in ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            a = unreal.load_asset(p)
            if a is None:
                continue
            cls = a.get_class().get_name()
            if cls not in ("StaticMesh", "SkeletalMesh"):
                continue
            for s in (getattr(a, "static_materials", None) or getattr(a, "materials", None) or []):
                mm = getattr(s, "material_interface", None)
                if mm is not None and mm.get_class().get_name() == "MaterialInstanceConstant":
                    used.add(mm.get_path_name().split(".")[0])
    return used


def real_map_for(mi_path, map_name, albedo_path):
    """Return a real map path when the pack has one for this slot, else None."""
    if map_name == "NormalMap":
        # AvatarGarden: atlas normal shares the albedo stem
        if AG in str(albedo_path) and albedo_path:
            stem = albedo_path.rsplit("/", 1)[-1].split(".")[0]
            nstem = stem.replace("_albedo", "_normal").replace("_Albedo", "_Normal")
            cand = f"{AG}/{nstem}"
            if unreal.EditorAssetLibrary.does_asset_exist(cand):
                return cand
        if GOTHIC in str(albedo_path) and albedo_path:
            stem = albedo_path.rsplit("/", 1)[-1].split(".")[0]
            nstem = stem.replace("_BaseColor", "_Normal")
            cand = f"{GOTHIC}/{nstem}"
            if unreal.EditorAssetLibrary.does_asset_exist(cand):
                return cand
    if map_name == "MetallicMap":
        if AG in str(albedo_path) and albedo_path:
            stem = albedo_path.rsplit("/", 1)[-1].split(".")[0]
            mstem = stem.replace("_albedo", "_metallic")
            cand = f"{AG}/{mstem}"
            if unreal.EditorAssetLibrary.does_asset_exist(cand):
                return cand
    return None


def main():
    used = used_mi_paths()
    rows = []
    n_fixed = 0
    n_real = 0
    n_neutral = 0
    for mi_path in sorted(used):
        mi = unreal.load_asset(mi_path)
        if mi is None:
            continue
        ov = {}
        for e in (mi.get_editor_property("texture_parameter_values") or []):
            info = e.get_editor_property("parameter_info")
            n = str(info.get_editor_property("name"))
            v = e.get_editor_property("parameter_value")
            ov[n] = v.get_path_name() if v else None
        tw = None
        for e in (mi.get_editor_property("scalar_parameter_values") or []):
            info = e.get_editor_property("parameter_info")
            if str(info.get_editor_property("name")) == "TextureWeight":
                tw = e.get_editor_property("parameter_value")
        if tw != 1.0:
            continue
        alb = ov.get("Albedo")
        if not alb or any(mk in alb for mk in NOISE_MARKERS):
            continue  # not a real textured MI (flat/procedural)
        changes = {}
        for map_name, neutral_path in NEUTRAL.items():
            cur = ov.get(map_name)
            if cur and not any(mk in cur for mk in NOISE_MARKERS):
                continue  # already real
            real = real_map_for(mi_path, map_name, alb)
            if real:
                changes[map_name] = {"to": "real", "path": real}
                n_real += 1
            else:
                changes[map_name] = {"to": "neutral", "path": neutral_path}
                n_neutral += 1
        if not changes:
            continue
        for map_name, info in changes.items():
            t = unreal.load_asset(info["path"])
            if t is not None:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, map_name, t)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        n_fixed += 1
        rows.append({"mi": mi_path, "changes": changes})
    payload = {
        "generated": "2026-08-14",
        "summary": {"mi_fixed": n_fixed, "real_map_routes": n_real,
                    "neutral_routes": n_neutral},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[neutral] fixed={n_fixed} real={n_real} neutral={n_neutral}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
