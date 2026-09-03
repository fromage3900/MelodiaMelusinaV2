"""Live PIE driver and assertions for the authored stock-skill rhythm seam.

The probe invokes the same BattleController events used by the stock UI, then
observes native rhythm state, HUD state, damage, and turn progression. It never
applies combat effects itself.

EVIDENCE BOUNDARY: this probe calls the subsystem and stock controller events
DIRECTLY (on_skill_selected_handler / use_skill / register_lane_hit). It does
not press real keys through BP_BattleUI::OnKeyDown, so a green run proves the
native seam works when invoked -- NOT that a player pressing Q/W/O/P sees the
highway. Gate evidence for `runtime` requires the real-input path
(Docs/ECHO/campaign_01_rhythm_damage_delta.md); a probe-only run is a HOLD.
"""

import unreal


SKILL_CLASS_PATH = (
    "/Game/Experiments/MelodiaJRPG/Skills/"
    "BP_MelusinaPetalCadence.BP_MelusinaPetalCadence_C"
)


def log(message):
    unreal.log(f"RHYTHM_GATE {message}")


def game_world():
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        raise RuntimeError("PIE game world is unavailable")
    return world


def actors_by_class_name(fragment):
    return [
        actor
        for actor in unreal.GameplayStatics.get_all_actors_of_class(
            game_world(), unreal.Actor
        )
        if fragment in actor.get_class().get_name()
    ]


def exactly_one(fragment):
    actors = actors_by_class_name(fragment)
    if len(actors) != 1:
        raise RuntimeError(
            f"Expected exactly one live {fragment} actor, found {len(actors)}"
        )
    return actors[0]


def rhythm_subsystem():
    subsystem = unreal.MelodiaRhythmCombatSubsystem.get(game_world())
    if not subsystem:
        raise RuntimeError("Melodia rhythm combat subsystem is unavailable")
    return subsystem


def music_clock():
    clock = unreal.MelodiaMusicClockSubsystem.get(game_world())
    if not clock:
        raise RuntimeError("Melodia music clock subsystem is unavailable")
    return clock


def rhythm_hud():
    return unreal.MelodiaRhythmHUDWidget.find_first(game_world())


def object_name(value):
    return value.get_name() if value else "None"


def read_state():
    controller = exactly_one("BP_BattleController_C")
    enemy = exactly_one("BP_BossEnemy_C")
    player = exactly_one("BP_MelusinaSwordsman_Presentation_C")
    subsystem = rhythm_subsystem()
    clock = music_clock()
    hud = rhythm_hud()
    music_time = clock.get_music_time()
    current_skill = controller.get_editor_property("currentSkill")
    current_attacker = controller.get_editor_property("currentAttackingUnit")
    battle_ui = controller.get_editor_property("battleUI")
    deferred_skill = subsystem.get_deferred_skill()
    notes = getattr(hud, "highway_notes", []) if hud else []
    return {
        "controller": controller,
        "enemy": enemy,
        "player": player,
        "subsystem": subsystem,
        "clock": clock,
        "hud": hud,
        "music_time": music_time,
        "current_skill": current_skill,
        "current_attacker": current_attacker,
        "battle_ui": battle_ui,
        "deferred_skill": deferred_skill,
        "enemy_hp": enemy.get_editor_property("currentHP"),
        "player_hp": player.get_editor_property("currentHP"),
        "turn": controller.get_editor_property("currentTurn"),
        "battle_over": controller.get_editor_property("isBattleOver"),
        "battle_result": controller.get_editor_property("battleResult"),
        "session_id": subsystem.get_active_session_id(),
        "session_active": subsystem.is_session_active(),
        "multiplier": subsystem.get_pending_damage_multiplier(),
        "hud_active": bool(getattr(hud, "note_highway_active", False)) if hud else False,
        "hud_notes": len(notes),
        "judgment": str(getattr(hud, "last_judgment_text", "")) if hud else "",
    }


def log_state(label):
    state = read_state()
    music_time = state["music_time"]
    log(
        f"STATE label={label} clock_valid={music_time.valid} "
        f"clock_source={music_time.source} bpm={music_time.tempo_bpm:.3f} "
        f"beat={music_time.total_beats:.3f} session={state['session_id']} "
        f"active={state['session_active']} attacker={object_name(state['current_attacker'])} "
        f"battle_ui={object_name(state['battle_ui'])} "
        f"skill={object_name(state['current_skill'])} "
        f"deferred={object_name(state['deferred_skill'])} "
        f"hud={object_name(state['hud'])} highway={state['hud_active']} "
        f"notes={state['hud_notes']} judgment={state['judgment']} "
        f"multiplier={state['multiplier']:.3f} enemy_hp={state['enemy_hp']} "
        f"player_hp={state['player_hp']} turn={state['turn']} "
        f"battle_over={state['battle_over']} result={state['battle_result']}"
    )
    return state


complete_state = {"count": 0, "grade": None, "hits": 0, "misses": 0}
bridge_result_state = {"count": 0, "raw_result": None}


def on_rhythm_complete(grade, hit_count, miss_count):
    complete_state["count"] += 1
    complete_state["grade"] = grade
    complete_state["hits"] = hit_count
    complete_state["misses"] = miss_count
    multiplier = rhythm_subsystem().get_pending_damage_multiplier()
    log(
        f"COMPLETE count={complete_state['count']} grade={grade} "
        f"hits={hit_count} misses={miss_count} multiplier={multiplier:.3f}"
    )


def on_bridge_battle_ended(raw_result):
    bridge_result_state["count"] += 1
    bridge_result_state["raw_result"] = raw_result
    log(
        f"BRIDGE_COMPLETE count={bridge_result_state['count']} "
        f"raw_result={raw_result}"
    )


def prepare_petal_cadence():
    state = read_state()
    controller = state["controller"]
    enemy = state["enemy"]
    subsystem = state["subsystem"]
    if (
        not state["current_attacker"]
        or "BP_MelusinaSwordsman_Presentation_C"
        not in state["current_attacker"].get_class().get_name()
        or not state["battle_ui"]
    ):
        raise RuntimeError("Stock battle is not yet at a controllable player turn")
    if state["battle_over"]:
        raise RuntimeError("Stock battle ended before the player turn")
    if state["enemy_hp"] <= 1:
        raise RuntimeError("Stock boss stats have not initialized yet")

    # Keep the callback strongly referenced for delayed PIE probes.
    unreal.__dict__["_rhythm_gate_complete_callback"] = on_rhythm_complete
    subsystem.on_rhythm_complete.add_callable(on_rhythm_complete)

    gi = unreal.GameplayStatics.get_game_instance(game_world())
    bridge = unreal.MelodiaExternalJRPGBridgeSubsystem.get_game_instance_subsystem(gi)
    if not bridge:
        raise RuntimeError("Production stock-JRPG bridge is unavailable")
    unreal.__dict__["_rhythm_gate_bridge_complete_callback"] = on_bridge_battle_ended
    bridge.on_jrpg_battle_ended.add_callable(on_bridge_battle_ended)

    skill_class = unreal.load_class(None, SKILL_CLASS_PATH)
    if not skill_class:
        raise RuntimeError(f"Missing stock Melusina skill class: {SKILL_CLASS_PATH}")

    baseline = {
        "skill_class": skill_class,
        "enemy_hp": state["enemy_hp"],
        "turn": state["turn"],
        "controller": controller,
        "enemy": enemy,
        "subsystem": subsystem,
        "min_enemy_hp": state["enemy_hp"],
        "last_enemy_hp": state["enemy_hp"],
        "last_turn": state["turn"],
        "initial_attacker": object_name(state["current_attacker"]),
        "last_attacker": object_name(state["current_attacker"]),
        "attacker_changed": False,
        "damage_seen": False,
    }
    unreal.__dict__["_rhythm_gate_baseline"] = baseline

    log(
        f"PREPARED enemy_hp={baseline['enemy_hp']} turn={baseline['turn']} "
        f"clock_valid={state['music_time'].valid} bpm={state['music_time'].tempo_bpm:.3f}"
    )


def sample_post_skill(label):
    """Sample stock damage/turn state without requiring actors to survive battle end."""
    baseline = unreal.__dict__["_rhythm_gate_baseline"]
    enemies = actors_by_class_name("BP_BossEnemy_C")
    controllers = actors_by_class_name("BP_BattleController_C")

    enemy_hp = None
    if len(enemies) == 1:
        enemy_hp = enemies[0].get_editor_property("currentHP")
        baseline["last_enemy_hp"] = enemy_hp
        baseline["min_enemy_hp"] = min(baseline["min_enemy_hp"], enemy_hp)
        baseline["damage_seen"] = baseline["min_enemy_hp"] < baseline["enemy_hp"]

    turn = None
    battle_over = None
    battle_result = None
    if len(controllers) == 1:
        turn = controllers[0].get_editor_property("currentTurn")
        battle_over = controllers[0].get_editor_property("isBattleOver")
        battle_result = controllers[0].get_editor_property("battleResult")
        current_attacker = controllers[0].get_editor_property("currentAttackingUnit")
        baseline["last_attacker"] = object_name(current_attacker)
        baseline["attacker_changed"] = (
            baseline["last_attacker"] != baseline["initial_attacker"]
        )
        baseline["last_turn"] = turn

    subsystem = rhythm_subsystem()
    log(
        f"POST label={label} enemy_hp={enemy_hp} "
        f"min_enemy_hp={baseline['min_enemy_hp']} "
        f"damage_seen={baseline['damage_seen']} turn={turn} "
        f"attacker={baseline['last_attacker']} "
        f"attacker_changed={baseline['attacker_changed']} "
        f"battle_over={battle_over} result={battle_result} "
        f"session={subsystem.get_active_session_id()} "
        f"active={subsystem.is_session_active()} "
        f"deferred={object_name(subsystem.get_deferred_skill())} "
        f"multiplier={subsystem.get_pending_damage_multiplier():.3f} "
        f"bridge_count={bridge_result_state['count']} "
        f"bridge_result={bridge_result_state['raw_result']}"
    )
    return baseline


def observe_selected_skill():
    controller = exactly_one("BP_BattleController_C")
    spawned_skill = controller.get_editor_property("currentSkill")
    if not spawned_skill:
        raise RuntimeError("Stock controller did not spawn the selected skill")
    log(f"SELECTED skill={object_name(spawned_skill)} class={spawned_skill.get_class().get_name()}")
    return spawned_skill


def start_petal_cadence():
    prepare_petal_cadence()
    state = read_state()
    controller = state["controller"]
    enemy = state["enemy"]
    skill_class = unreal.__dict__["_rhythm_gate_baseline"]["skill_class"]

    # These are the same two stock controller events reached by the BattleUI:
    # choose a skill class, then confirm its target.
    controller.on_skill_selected_handler(skill_class)
    observe_selected_skill()

    controller.use_skill(enemy)
    log_state("after_use_skill")


def press_lane(lane_index):
    subsystem = rhythm_subsystem()
    grade = subsystem.register_lane_hit(lane_index)
    hud = rhythm_hud()
    log(
        f"INPUT lane={lane_index} grade={grade} "
        f"hits={subsystem.get_session_hit_count()} "
        f"misses={subsystem.get_session_miss_count()} "
        f"judgment={str(getattr(hud, 'last_judgment_text', '')) if hud else ''}"
    )
    return grade


def assert_enabled_start():
    state = log_state("enabled_start_assert")
    if not state["music_time"].valid:
        raise RuntimeError("128 BPM musical time is unavailable")
    if abs(state["music_time"].tempo_bpm - 128.0) > 0.1:
        raise RuntimeError(
            f"Expected 128 BPM, got {state['music_time'].tempo_bpm:.3f}"
        )
    if not state["session_active"] or state["session_id"] == 0:
        raise RuntimeError("Rhythm-enabled stock skill did not start a session")
    if not state["deferred_skill"]:
        raise RuntimeError("Rhythm-enabled stock skill was not deferred")
    if not state["hud"] or not state["hud_active"] or state["hud_notes"] == 0:
        raise RuntimeError("Visible rhythm highway has no active notes")


def assert_enabled_complete():
    baseline = unreal.__dict__["_rhythm_gate_baseline"]
    sample_post_skill("enabled_complete_assert")
    subsystem = rhythm_subsystem()
    if complete_state["count"] != 1:
        raise RuntimeError(
            f"Expected exactly one OnRhythmComplete, got {complete_state['count']}"
        )
    if complete_state["hits"] < 1:
        raise RuntimeError("Rhythm-enabled input did not register a hit")
    if subsystem.is_session_active() or subsystem.get_deferred_skill():
        raise RuntimeError("Rhythm session/deferred skill did not clear")
    if not baseline["damage_seen"]:
        raise RuntimeError("Deferred stock skill did not apply damage")
    if abs(subsystem.get_pending_damage_multiplier() - 1.0) > 0.001:
        raise RuntimeError("Damage multiplier did not clean up after application")
    if (
        baseline["last_turn"] == baseline["turn"]
        and not baseline["attacker_changed"]
        and bridge_result_state["count"] == 0
    ):
        raise RuntimeError("Stock battle turn did not advance after the skill")
    if bridge_result_state["count"] > 1:
        raise RuntimeError(
            "Stock battle completion relayed more than once: "
            f"{bridge_result_state['count']}"
        )


def assert_disabled_immediate():
    state = log_state("disabled_immediate_assert")
    if state["music_time"].valid:
        raise RuntimeError("Rhythm-disabled A/B unexpectedly has musical time")
    if state["session_active"] or state["session_id"] != 0:
        raise RuntimeError("Rhythm-disabled A/B started a rhythm session")
    if state["deferred_skill"]:
        raise RuntimeError("Rhythm-disabled A/B deferred the stock skill")
    if state["hud_active"]:
        raise RuntimeError("Rhythm-disabled A/B activated the highway")


def assert_disabled_complete():
    baseline = unreal.__dict__["_rhythm_gate_baseline"]
    sample_post_skill("disabled_complete_assert")
    subsystem = rhythm_subsystem()
    if complete_state["count"] != 0:
        raise RuntimeError(
            "Rhythm-disabled A/B emitted an OnRhythmComplete callback"
        )
    if not baseline["damage_seen"]:
        raise RuntimeError("Rhythm-disabled stock skill did not apply base damage")
    if subsystem.is_session_active() or subsystem.get_deferred_skill():
        raise RuntimeError("Rhythm-disabled A/B retained rhythm session state")
    if abs(subsystem.get_pending_damage_multiplier() - 1.0) > 0.001:
        raise RuntimeError("Rhythm-disabled A/B did not retain identity damage")
    if bridge_result_state["count"] > 1:
        raise RuntimeError(
            "Disabled-path stock battle completion relayed more than once: "
            f"{bridge_result_state['count']}"
        )


def assert_typed_result_once():
    sample_post_skill("typed_result_assert")
    if bridge_result_state["count"] != 1:
        raise RuntimeError(
            "Expected exactly one typed stock battle completion relay, "
            f"got {bridge_result_state['count']}"
        )


unreal.__dict__["_rhythm_gate_start"] = start_petal_cadence
unreal.__dict__["_rhythm_gate_prepare"] = prepare_petal_cadence
unreal.__dict__["_rhythm_gate_observe_selected"] = observe_selected_skill
unreal.__dict__["_rhythm_gate_press"] = press_lane
unreal.__dict__["_rhythm_gate_state"] = log_state
unreal.__dict__["_rhythm_gate_assert_enabled_start"] = assert_enabled_start
unreal.__dict__["_rhythm_gate_assert_enabled_complete"] = assert_enabled_complete
unreal.__dict__["_rhythm_gate_assert_disabled_immediate"] = assert_disabled_immediate
unreal.__dict__["_rhythm_gate_assert_disabled_complete"] = assert_disabled_complete
unreal.__dict__["_rhythm_gate_sample_post_skill"] = sample_post_skill
unreal.__dict__["_rhythm_gate_assert_typed_result_once"] = assert_typed_result_once

log("PROBE_READY")
