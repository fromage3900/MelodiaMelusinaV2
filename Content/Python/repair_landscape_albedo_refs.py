"""Replace stale landscape albedo references with project-local valid assets."""
from __future__ import annotations

import json
from pathlib import Path

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "landscape_albedo_refs.json"
ALBEDOS = {
    "Rock_Albedo": "/Game/EnvSandbox/Textures_Shared/sbs_-_seamless_abstract_pack_-_512x512/512x512/Texture_512x512_1.Texture_512x512_1",
    "Grass_Albedo": "/Game/EnvSandbox/Textures/Melusina/Grass/T_Grass_BaseColor.T_Grass_BaseColor",
    "Mud_Albedo": "/Game/EnvSandbox/Textures/Melusina/Soil/T_Soil_BaseColor.T_Soil_BaseColor",
    "Path_Albedo": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_5_-_512x512.Marble_5_-_512x512",
}


def main() -> dict:
    import unreal

    import portfolio_texture_catalog as catalog
    import importlib
    catalog = importlib.reload(catalog)

    material = unreal.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Could not load {MASTER}")
    changes = catalog.apply_master_defaults(material, MASTER, force=True)
    saved = bool(changes)
    result = {"master": MASTER, "changes": changes, "saved": bool(saved), "ok": bool(saved)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Landscape albedo refs: " + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
