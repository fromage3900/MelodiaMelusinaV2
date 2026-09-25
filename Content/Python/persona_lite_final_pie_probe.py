"""Focused PIE contract probe for the Zen Forest Persona route.

The Priestess accepts the first echo through Quill.  The legacy quest fields on
UMelodiaNPCInteractionComponent are presentation-only, so this probe drives the
compiled Quill choice and waits for the typed notification to reach Persona.
Stock equipment is intentionally not tested here: ZenForestTest uses a plain
PlayerController; the equipment proof runs on MelodiaIntegrationMap.
"""
import unreal


world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    raise RuntimeError("PIE world unavailable")

persona = unreal.MelodiaPersonaSubsystem.get(world)
if not persona:
    raise RuntimeError("MelodiaPersonaSubsystem unavailable")

# Do not ask every actor for NPC-only properties; WorldSettings raises when it
# does.  Filter to the placeholder class before reading the reflected field.
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
by_id = {}
for actor in actors:
    if actor.get_class().get_name() != "MelodiaNPCPlaceholder":
        continue
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

interpreters = unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.QuillscriptInterpreter
)
if not interpreters:
    raise RuntimeError("Priestess did not create a Quill interpreter")
interpreter = interpreters[0]

# The Priestess scene has authored dialogue before its choice.  Advance until
# Quill presents the option set, then select the first authored option.  The
# target label and its notifications execute through the normal interpreter.
options = []
for _ in range(12):
    options = list(interpreter.get_options_set())
    if options:
        break
    interpreter.next()
if not options:
    raise RuntimeError("Petal Priestess choice was not presented")

selected = str(options[0].text)
interpreter.option_selected(options[0])

# Continue the selected target label.  Quill commands are synchronous, but
# advance until the notification is observed so this also covers label flow.
state_q1 = str(persona.get_quest_state("melodia_q_echo_01"))
for _ in range(12):
    if "ACTIVE" in state_q1.upper():
        break
    interpreter.next()
    state_q1 = str(persona.get_quest_state("melodia_q_echo_01"))
if "ACTIVE" not in state_q1.upper():
    raise RuntimeError(
        f"Petal Priestess choice did not activate quest 1: {state_q1}"
    )

unreal.log(
    "MELODIA_PERSONA_FINAL_PROBE_OK "
    f"q1={state_q1} option={selected!r} equipment=separate_integration_map"
)