"""Focused PIE contract probe for Persona-lite NPC, minimap, and equipment wiring."""
import unreal

world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    raise RuntimeError("PIE world unavailable")

persona = unreal.MelodiaPersonaSubsystem.get(world)
if not persona:
    raise RuntimeError("MelodiaPersonaSubsystem unavailable")

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
by_id = {}
for actor in actors:
    try:
        npc_id = str(actor.get_editor_property("npc_id"))
    except Exception:
        continue
    if npc_id:
        by_id[npc_id] = actor

required = ("SD_02_PetalPriestess", "CW_01_StarWeaver", "MD_01_TwilightDancer")
missing = [npc_id for npc_id in required if npc_id not in by_id]
if missing:
    raise RuntimeError(f"Missing Persona NPCs in PIE: {missing}")

priestess = by_id["SD_02_PetalPriestess"].get_editor_property("interaction")
if not priestess.begin_interaction():
    raise RuntimeError("Petal Priestess interaction did not begin")
state_q1 = str(persona.get_quest_state("melodia_q_echo_01"))
if "ACTIVE" not in state_q1.upper():
    raise RuntimeError(f"Petal Priestess did not activate quest 1: {state_q1}")

# A second interaction routes through the same facade and completes the active quest,
# unlocking the Star Weaver's next chain entry without introducing another authority.
priestess.begin_interaction()
state_q1_complete = str(persona.get_quest_state("melodia_q_echo_01"))
if "COMPLETED" not in state_q1_complete.upper():
    raise RuntimeError(f"Second Priestess interaction did not complete quest 1: {state_q1_complete}")

star = by_id["CW_01_StarWeaver"].get_editor_property("interaction")
if not star.begin_interaction():
    raise RuntimeError("Star Weaver interaction did not begin")
state_q2 = str(persona.get_quest_state("melodia_q_echo_02"))
if "ACTIVE" not in state_q2.upper():
    raise RuntimeError(f"Star Weaver did not activate quest 2: {state_q2}")
visible_tags = {str(marker.actor_tag) for marker in persona.get_visible_minimap_markers()}
if "melodia_smoke_encounter" not in visible_tags:
    raise RuntimeError(f"Quest-gated encounter marker not visible: {sorted(visible_tags)}")

if not persona.request_equip("melusina", "melodia_tuning_fork"):
    raise RuntimeError("Persona equipment request was rejected")

unreal.log(
    "MELODIA_PERSONA_FINAL_PROBE_OK "
    f"q1={state_q1_complete} q2={state_q2} markers={sorted(visible_tags)} equipment_request=accepted"
)
