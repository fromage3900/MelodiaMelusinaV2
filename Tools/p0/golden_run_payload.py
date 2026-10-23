"""One PIE step for the P0 golden run. The host writes command.json, then calls this.

Ops: status, quill_options, quill_pick, travel, save, slot, step, lock, swing, phrase,
lanes, exit, shot.

Every op is defensive: a missing API reports itself instead of killing the run, because
a golden run records what happened, including what did not.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
CMD = ROOT / "Saved/Audit/P0GoldenRun_20261022/command.json"
OUT = ROOT / "Saved/Audit/P0GoldenRun_20261022"


def find_one(actors, predicate):
    for actor in actors:
        try:
            if predicate(actor):
                return actor
        except Exception:  # noqa: BLE001
            continue
    return None


def main():
    import unreal

    op = "status"
    arg = ""
    shot = ""
    if CMD.is_file():
        data = json.loads(CMD.read_text(encoding="utf-8"))
        op = data.get("op", "status")
        arg = str(data.get("arg", ""))
        shot = data.get("shot", "")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world is None:
        print("GOLDEN world=NONE")
        return 2

    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    pawn = find_one(actors, lambda a: "MelusinaJRPG" in a.get_name())
    if pawn is None:
        print("GOLDEN pawn=NONE")
        return 2

    combat = pawn.get_component_by_class(unreal.MelodiaWaveHarpCombatComponent)
    loc = pawn.get_actor_location()
    print("GOLDEN op=%s pawn=%s loc=%s" % (op, pawn.get_name(), loc))

    # ---- the narrative state (the owner of the route) -------------------------
    try:
        # The house's own static getter: the game instance is a Blueprint, so the
        # python wrapper never exposed get_subsystem on it.
        subsystem = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(world)
        record = subsystem.get_narrative_record()
        print("GOLDEN narrative slot=%s phase=%s quests=%s flags=%s" % (
            getattr(record, "slot_id", "?"), getattr(record, "phase", "?"),
            len(getattr(record, "quest_ids", []) or []),
            len(getattr(record, "flags", {}) or {})))
    except Exception as exc:  # noqa: BLE001
        print("GOLDEN narrative=UNAVAILABLE %s" % exc)

    # ---- the ops ------------------------------------------------------------
    try:
        if op == "quill_options":
            # The Quill's own option list, so the choice is READ and then picked.
            quill = find_one(actors, lambda a: "Quill" in a.get_name()
                             or a.get_class().get_name() in ("Quill", "QuillscriptActor"))
            if quill:
                options = quill.get_options_set()
                print("GOLDEN quill=%s options=%d" % (quill.get_name(), len(options)))
                for index, option in enumerate(options):
                    print("GOLDEN option[%d]=%s" % (index, option))
            else:
                print("GOLDEN quill=NONE")
        elif op == "quill_pick" and arg:
            quill = find_one(actors, lambda a: "Quill" in a.get_name()
                             or a.get_class().get_name() in ("Quill", "QuillscriptActor"))
            if quill:
                options = quill.get_options_set()
                index = int(arg)
                if 0 <= index < len(options):
                    quill.option_selected(options[index])
                    print("GOLDEN quill_picked=%d" % index)
                else:
                    print("GOLDEN quill_pick out_of_range=%d of %d" % (index, len(options)))
            else:
                print("GOLDEN quill=NONE")
        elif op == "travel" and arg:
            subsystem = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(world)
            ok = subsystem.request_travel(unreal.Name(arg))
            print("GOLDEN travel %s -> %s" % (arg, ok))
        elif op == "walk_quill":
            # The morning beat is fired by an ARRIVAL TRIGGER: walk the pawn into it.
            trigger = find_one(actors, lambda a: "Morning_QuillTrigger" in (
                a.get_actor_label() if hasattr(a, "get_actor_label") else ""))
            if trigger:
                destination = trigger.get_actor_location()
                direction = destination - pawn.get_actor_location()
                distance = direction.length()
                direction.z = 0.0
                pawn.add_movement_input(direction, 1.0, False)
                control = pawn.get_controller()
                if control:
                    control.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                        pawn.get_actor_location(), destination))
                print("GOLDEN walk_quill trigger=%s dist=%.1f" % (
                    trigger.get_actor_label(), distance))
            else:
                print("GOLDEN walk_quill no_trigger")
        elif op == "actors":
            # The diagnostic: what is actually in this level.
            names = []
            for actor in actors:
                label = actor.get_actor_label() if hasattr(actor, "get_actor_label") else ""
                names.append("%s [%s] (%s)" % (actor.get_name(), label, actor.get_class().get_name()))
            print("GOLDEN actors=%d" % len(names))
            for name in sorted(names):
                print("GOLDEN actor %s" % name)
        elif op == "save":
            # The normal save authority: the JRPG save game object.
            save = unreal.load_object(None, "/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame.BP_JRPGSaveGame_C")
            if save:
                subsystem = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(world)
                synced = subsystem.sync_narrative_record_to_save(save)
                print("GOLDEN save synced=%s" % synced)
            else:
                print("GOLDEN save=NO_OBJECT")
        elif op == "step":
            slime = find_one(actors, lambda a: "FirstResonance" in a.get_name()
                             or "First Resonance" in (a.get_actor_label() if hasattr(a, "get_actor_label") else ""))
            if slime:
                direction = slime.get_actor_location() - pawn.get_actor_location()
                distance = direction.length()
                direction.z = 0.0
                if distance > 280.0:
                    pawn.add_movement_input(direction, 1.0, False)
                control = pawn.get_controller()
                if control:
                    control.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                        pawn.get_actor_location(), slime.get_actor_location()))
                print("GOLDEN step dist=%.1f" % distance)
        elif op in ("lock", "swing", "phrase", "lanes", "exit") and combat:
            if op == "lock":
                combat.toggle_lock()
            elif op == "swing":
                combat.trigger_scythe_melee()
            elif op == "phrase":
                combat.toggle_sequence()
            elif op == "lanes":
                for lane in (0, 1, 2, 3):
                    combat.register_lane_hit(lane)
            elif op == "exit":
                combat.toggle_sequence()
            print("GOLDEN combat_op=%s" % op)
    except Exception as exc:  # noqa: BLE001
        print("GOLDEN op_failed %s: %s" % (op, exc))

    if combat:
        print("GOLDEN_STATUS form=%s stage=%s locked=%s sequence=%s text=%s" % (
            combat.get_form(), combat.get_form_stage(), combat.is_combat_locked(),
            combat.is_in_sequence(), combat.get_status_text()))

    if shot:
        OUT.mkdir(parents=True, exist_ok=True)
        unreal.SystemLibrary.execute_console_command(
            pawn, 'HighResShot filename="%s/%s" 1600x900' % (OUT.as_posix(), shot))
        print("GOLDEN_SHOT %s" % shot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
