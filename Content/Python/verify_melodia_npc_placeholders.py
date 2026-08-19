"""Read-only verification for the temporary ZenForestTest NPC cast."""
from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


# Must match setup_melodia_npc_placeholders.py. ZenForestTest is the authority
# exploration map (owner, 2026-08-14).
MAP_PATH = os.environ.get("MELODIA_NPC_MAP", "/Game/ZenForestTest")
LABELS = (
    "MelodiaNPC_SD_02_PetalPriestess",
    "MelodiaNPC_CW_01_StarWeaver",
    "MelodiaNPC_MD_01_TwilightDancer",
)
REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Melodia" / "npc_placeholder_verify.json"


def main() -> bool:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
    checks = []
    for label in LABELS:
        actor = actors.get(label)
        interaction = actor.get_editor_property("interaction") if actor else None
        actor_tags = {str(tag) for tag in actor.tags} if actor else set()
        checks.append({
            "label": label,
            "exists": actor is not None,
            "class": actor.get_class().get_path_name() if actor else "",
            "has_interaction": interaction is not None,
            "npc_id": str(actor.get_editor_property("npc_id")) if actor else "",
            "tags": sorted(actor_tags),
            "has_identity_tag": bool(actor and str(actor.get_editor_property("npc_id")) in actor_tags),
            "has_quest_tag": "MelodiaQuestNPC" in actor_tags,
            "has_dialogue": bool(interaction and interaction.get_editor_property("dialogue_lines")),
        })

    report = {"map": MAP_PATH, "checks": checks}
    report["ok"] = all(
        check["exists"] and check["has_interaction"] and check["has_dialogue"]
        and check["has_identity_tag"] and check["has_quest_tag"]
        for check in checks
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"[MelodiaNPCPlaceholderVerify] Wrote {REPORT_PATH}")
    unreal.log(f"[MelodiaNPCPlaceholderVerify] ok={report['ok']}")
    return bool(report["ok"])


if __name__ == "__main__":
    main()
