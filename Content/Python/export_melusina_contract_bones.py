"""Export the live 465-bone Melusina contract for Blender-side validation."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
SKELETON_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
MAP_PATH = ROOT / "specs" / "anim_presets" / "melusina_arp_to_contract_bones.json"
OUT_PATH = ROOT / "specs" / "anim_presets" / "melusina_contract_bones.json"


def main() -> int:
    skeleton = unreal.load_asset(SKELETON_PATH)
    if not skeleton:
        unreal.log_error(f"Melusina contract skeleton not found: {SKELETON_PATH}")
        return 2
    names = [str(name) for name in skeleton.get_reference_pose().get_bone_names()]
    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    payload = {
        "schema": "melodia.melusina_contract_bones.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skeleton": SKELETON_PATH,
        "target_bone_count": len(names),
        "bone_names": names,
        "semantic_map": mapping.get("semantic_map", {}),
        "drop": mapping.get("drop", []),
        "units": "centimeters",
        "name_style": "underscore",
        "source": "Unreal reference pose; used for Blender preflight only",
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"Exported {len(names)} Melusina contract bones to {OUT_PATH}")
    return 0 if len(names) == 465 else 1


if __name__ == "__main__":
    raise SystemExit(main())
