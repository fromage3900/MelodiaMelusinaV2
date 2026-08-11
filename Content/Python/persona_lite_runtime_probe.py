"""PIE probe for the production Quill -> stock JRPG adapter path.

This script observes and drives only existing gameplay authorities. It does not
create a battle/session/save implementation and is intended for Monolith's
run_pie_smoke staged Python hook.
"""
import unreal

ENCOUNTER = "melodia_smoke_encounter"
QUILL_ASSET = "/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke"


def mark(message):
    unreal.log(f"MELUSINA_LOOP_PROBE {message}")


world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    raise RuntimeError("PIE game world is unavailable")

gi = unreal.GameplayStatics.get_game_instance(world)
if not gi:
    raise RuntimeError("PIE game instance is unavailable")

narrative = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(world)
bridge = unreal.MelodiaExternalJRPGBridgeSubsystem.get_game_instance_subsystem(gi)
if not narrative or not bridge:
    raise RuntimeError("Production Melodia narrative/bridge subsystems are unavailable")

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
tagged = [actor for actor in actors if ENCOUNTER in [str(tag) for tag in actor.tags]]
mark(f"tagged_count={len(tagged)} tagged_classes={[actor.get_class().get_name() for actor in tagged]}")
if len(tagged) != 1:
    raise RuntimeError(f"Expected exactly one {ENCOUNTER} actor, found {len(tagged)}")

pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
mark(f"exploration_pawn={pawn.get_class().get_name() if pawn else 'None'}")

asset = unreal.load_asset(QUILL_ASSET)
if not asset:
    raise RuntimeError(f"Missing authored Quill asset: {QUILL_ASSET}")

interpreters = unreal.GameplayStatics.get_all_actors_of_class(
    world, unreal.QuillscriptInterpreter
)
if len(interpreters) != 1:
    raise RuntimeError(
        "Canonical PIE probe requires exactly one Monolith-spawned "
        f"QuillscriptInterpreter, found {len(interpreters)}"
    )
interpreter = interpreters[0]

# Keep strong references for delayed Monolith probes.
unreal.__dict__["_melusina_loop_interpreter"] = interpreter
unreal.__dict__["_melusina_loop_tagged_actor"] = tagged[0]


def mark_statement_played(_interpreter, played_index, statement):
    mark(
        f"statement index={played_index} type={statement.type} "
        f"source={statement.source_line}"
    )


unreal.__dict__["_melusina_loop_statement_callback"] = mark_statement_played
interpreter.on_statement_played.add_callable(mark_statement_played)

drive_state = {"option_presented": False, "option_selected": False, "step": 0}


def get_runtime_services():
    live_world = unreal.EditorLevelLibrary.get_game_world()
    if not live_world:
        raise RuntimeError("PIE game world became unavailable")
    live_gi = unreal.GameplayStatics.get_game_instance(live_world)
    live_narrative = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(
        live_world
    )
    live_bridge = unreal.MelodiaExternalJRPGBridgeSubsystem.get_game_instance_subsystem(
        live_gi
    )
    if not live_narrative or not live_bridge:
        raise RuntimeError("Production narrative/bridge services became unavailable")
    return live_narrative, live_bridge


def mark_interpreter_state(phase):
    index_getter = getattr(interpreter, "get_current_statement_index", None)
    proceed_getter = getattr(interpreter, "get_can_proceed", None)
    statement_getter = getattr(interpreter, "get_current_statement", None)
    index = index_getter() if index_getter else "unavailable"
    can_proceed = proceed_getter() if proceed_getter else "unavailable"
    statement = statement_getter() if statement_getter else None
    statement_type = getattr(statement, "type", "unavailable")
    source_line = getattr(statement, "source_line", "unavailable")
    mark(
        f"{phase} step={drive_state['step']} "
        f"index={index} can_proceed={can_proceed} "
        f"type={statement_type} source={source_line}"
    )


def drive_one_quill_step():
    live_narrative, live_bridge = get_runtime_services()
    if live_narrative.is_battle_pending() or live_bridge.is_jrpg_battle_active():
        return

    drive_state["step"] += 1
    mark_interpreter_state("before_step")

    # The first advance presents the script's authored choice. Quillscript's
    # Next() intentionally waits there; the selected FStatement must be sent
    # back through OptionSelected() before the target label can execute.
    if not drive_state["option_presented"]:
        interpreter.next()
        drive_state["option_presented"] = True
        mark("option_presented")
        mark_interpreter_state("after_step")
        return

    if not drive_state["option_selected"]:
        options = interpreter.get_options_set()
        if not options:
            raise RuntimeError("Authored Quill choice was not available after advance")
        interpreter.option_selected(options[0])
        drive_state["option_selected"] = True
        mark(f"option_selected={options[0].text}")
        mark_interpreter_state("after_step")
        return

    interpreter.next()
    mark_interpreter_state("after_step")


def assert_quill_battle_started():
    live_narrative, live_bridge = get_runtime_services()
    mark(
        "after_quill "
        f"pending={live_narrative.is_battle_pending()} "
        f"encounter={live_narrative.get_pending_encounter_id()} "
        f"bridge_active={live_bridge.is_jrpg_battle_active()} "
        f"bridge_encounter={live_bridge.get_active_encounter_id()} "
        f"actor={tagged[0].get_name()} class={tagged[0].get_class().get_name()}"
    )
    if not live_narrative.is_battle_pending():
        raise RuntimeError("Authored Quill execution did not produce a pending battle")
    if not live_bridge.is_jrpg_battle_active():
        raise RuntimeError("Production bridge did not enter the stock JRPG battle path")


unreal.__dict__["_melusina_loop_step"] = drive_one_quill_step
unreal.__dict__["_melusina_loop_assert_started"] = assert_quill_battle_started
interpreter.start(asset)
mark("quill_started")
