"""Load MelusinaMorning (user green) + live road/spire measure. READ + load only, no greybox spawn yet."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"

def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    notes = []
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    before = world.get_name() if world else None
    notes.append(f"before={before}")
    if before != "L_MelusinaMorning":
        try:
            ok = les.load_level(MAP)
            notes.append(f"load_level={ok}")
        except Exception as e:
            notes.append(f"load_level err={e}")
            try:
                unreal.EditorLoadingAndSavingUtils.load_map(MAP)
                notes.append("load_map_ok")
            except Exception as e2:
                notes.append(f"load_map err={e2}")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    after = world.get_name() if world else None
    notes.append(f"after={after}")
    print("LOAD " + json.dumps({"before": before, "after": after, "notes": notes}, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
