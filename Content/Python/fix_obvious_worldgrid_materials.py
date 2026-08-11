"""Replace only confirmed WorldGrid slots with the canonical neutral toon MI."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
REPORT = ROOT / "Saved/Audit/worldgrid_material_fix.json"
NEUTRAL = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Universal_Default.MI_Universal_Default"
TARGETS = (
    "/Game/Melodia/Enemies/StoneGolem/zundapalupdate2.zundapalupdate2",
    "/Game/EnvSandbox/SM_MelodyToken.SM_MelodyToken",
)


def main() -> int:
    replacement = unreal.EditorAssetLibrary.load_asset(NEUTRAL)
    if not replacement:
        raise RuntimeError(f"Missing canonical neutral material: {NEUTRAL}")

    changed = []
    for path in TARGETS:
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if not mesh:
            raise RuntimeError(f"Missing target mesh: {path}")
        slots = list(mesh.get_editor_property("static_materials") or [])
        if not slots:
            raise RuntimeError(f"Target has no material slots: {path}")
        material = slots[0].get_editor_property("material_interface")
        if material and "WorldGrid" not in material.get_path_name():
            continue
        slots[0].set_editor_property("material_interface", replacement)
        mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        changed.append({"mesh": path, "slot": 0, "material": NEUTRAL})

    report = {"ok": True, "replacement": NEUTRAL, "changed": changed}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
