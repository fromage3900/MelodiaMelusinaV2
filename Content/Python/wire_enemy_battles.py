import unreal
import math

e = unreal.EditorLevelLibrary
level = e.get_editor_world()
if not level:
    print("No editor world")
    quit()

# Find all enemy pawns
all_actors = e.get_all_level_actors()
enemy_pawns = [a for a in all_actors if a.get_class().get_name().startswith("BP_") and ("AverageEnemy" in a.get_name() or "WeakEnemy" in a.get_name())]
print(f"Found {len(enemy_pawns)} enemy pawns")

# Find all battle actors with melodia_smoke_encounter tag
battle_actors = [a for a in all_actors if a.get_class().get_name() == "BP_InteractionBattle_C" and a.actor_has_tag("melodia_smoke_encounter")]
print(f"Found {len(battle_actors)} tagged battle actors")
for b in battle_actors:
    print(f"  {b.get_name()} at {b.get_actor_location()}")

# Find all interaction detectors
interaction_detectors = [a for a in all_actors if a.get_class().get_name() == "BP_InteractionDetector_C"]
print(f"Found {len(interaction_detectors)} interaction detectors")
for d in interaction_detectors:
    print(f"  {d.get_name()} at {d.get_actor_location()}")

# Helper for vector distance
def vec_dist(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)

# For each enemy pawn, find nearest battle and interaction detector
for pawn in enemy_pawns:
    pawn_loc = pawn.get_actor_location()
    
    # Find nearest battle
    nearest_battle = None
    min_dist = 1e9
    for b in battle_actors:
        dist = vec_dist(pawn_loc, b.get_actor_location())
        if dist < min_dist:
            min_dist = dist
            nearest_battle = b
    
    # Find nearest interaction detector
    nearest_detector = None
    min_dist = 1e9
    for d in interaction_detectors:
        dist = vec_dist(pawn_loc, d.get_actor_location())
        if dist < min_dist:
            min_dist = dist
            nearest_detector = d
    
    print(f"\n{pawn.get_name()}:")
    if nearest_battle:
        print(f"  nearest battle: {nearest_battle.get_name()} ({min_dist:.0f} units)")
    else:
        print(f"  nearest battle: NONE")
    
    if nearest_detector:
        print(f"  nearest detector: {nearest_detector.get_name()} ({min_dist:.0f} units)")
    else:
        print(f"  nearest detector: NONE")
    
    if nearest_battle:
        # Set battle property on pawn instance
        pawn.set_editor_property('battle', nearest_battle)
        print(f"  Set battle -> {nearest_battle.get_name()}")
    
    print(f"  Need to add InteractionActor ChildActorComponent in Blueprint")

print("\nDone")