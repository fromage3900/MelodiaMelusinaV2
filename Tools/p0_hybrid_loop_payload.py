"""One PIE step for the P0 hybrid loop. The host writes command.json, then calls this.

Ops: status, step, lock, swing, phrase, lanes, exit, shot.
Nothing is saved. The pawn is never teleported.
"""

from __future__ import annotations

import json
from pathlib import Path


CMD = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/P0HybridLoop_20261017/command.json")
OUT = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/P0HybridLoop_20261017")


def main():
    import unreal

    op = "status"
    shot = ""
    if CMD.is_file():
        data = json.loads(CMD.read_text(encoding="utf-8"))
        op = data.get("op", "status")
        shot = data.get("shot", "")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world is None:
        print("P0_LOOP world=NONE")
        return 2

    pawn = None
    slime = None
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    for actor in actors:
        name = actor.get_name()
        label = actor.get_actor_label() if hasattr(actor, "get_actor_label") else ""
        if pawn is None and "MelusinaJRPG" in name:
            pawn = actor
        if slime is None and ("First Resonance" in label or "FirstResonance" in name or "WorldSlime" in name):
            slime = actor
    if pawn is None:
        print("P0_LOOP pawn=NONE")
        return 2

    combat = pawn.get_component_by_class(unreal.MelodiaWaveHarpCombatComponent)
    dist = pawn.get_distance_to(slime) if slime else -1.0
    loc = pawn.get_actor_location()
    print("P0_LOOP op=%s pawn=%s slime=%s dist=%.1f loc=%s" % (
        op, pawn.get_name(), slime.get_name() if slime else "NONE", dist, loc))

    if op == "step" and slime is not None and dist > 280.0:
        direction = slime.get_actor_location() - pawn.get_actor_location()
        direction.z = 0.0
        pawn.add_movement_input(direction, 1.0, False)
        control = pawn.get_controller()
        if control:
            control.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(pawn.get_actor_location(), slime.get_actor_location()))

    if op == "lock" and combat:
        combat.toggle_lock()
    elif op == "swing" and combat:
        combat.trigger_scythe_melee()
    elif op == "phrase" and combat:
        combat.toggle_sequence()
    elif op == "lanes" and combat:
        for lane in (0, 1, 2, 3):
            combat.register_lane_hit(lane)
    elif op == "exit" and combat:
        combat.toggle_sequence()

    if combat:
        print("P0_STATUS locked=%s step=%s sequence=%s text=%s" % (
            combat.is_combat_locked(), combat.get_scythe_step(), combat.is_in_sequence(), combat.get_status_text()))

    if shot:
        OUT.mkdir(parents=True, exist_ok=True)
        unreal.SystemLibrary.execute_console_command(
            pawn, 'HighResShot filename="%s/%s" 1600x900' % (OUT.as_posix(), shot))
        print("P0_SHOT %s" % shot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
