"""Host-side Monolith repair for ProceduralDungeon Level Blueprint parents."""
from __future__ import annotations

import json

from gmm.core.mcp_client import MonolithClient

ROOT = "/Game/Melodia/Roguelike/Rooms"
LEVELS = [
    "L_MelodiaGrove", "L_WhisperingGrove", "L_EverburningClearing",
    "L_BossArena", "L_TokenShrine", "L_AbandonedCache",
    "L_StarlightReverie", "L_BlessingAltar",
]


def main() -> None:
    client = MonolithClient(timeout=120)
    rows = []
    for name in LEVELS:
        path = f"{ROOT}/{name}"
        loaded = client.call_action("editor", "load_level", {"path": path})
        try:
            reparented = client.call_action("blueprint", "reparent_blueprint", {
                "asset_path": "$current",
                "new_parent_class": "/Script/ProceduralDungeon.RoomLevel",
            })
            compiled = client.call_action("blueprint", "compile_blueprint", {"asset_path": "$current"})
            saved = client.run_python(
                "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()",
                mode="execute_statement",
            )
            error = ""
        except Exception as exc:
            reparented = compiled = saved = {}
            error = str(exc)
        rows.append({"level": path, "loaded": loaded, "reparented": reparented,
                     "compiled": compiled, "saved": saved, "error": error})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
