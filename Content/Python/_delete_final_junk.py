import unreal
import json

# ============================================================
# FINAL CLEANUP - Delete remaining junk pieces
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

junk_labels = ["SeaAbove_ObservationCliff_Prototype", "SM_Starskiff_Dock_Blockout_P0"]
deleted = []

for a in actors:
    label = a.get_actor_label()
    if label in junk_labels:
        unreal.EditorLevelLibrary.destroy_actor(a)
        deleted.append(label)

print(f"Deleted {len(deleted)} junk pieces:")
for d in deleted:
    print(f"  {d}")

# Verify final state
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
print(f"\nFinal SMA count: {len(sma)}")

unreal.EditorLevelLibrary.save_current_level()
print("Saved.")
