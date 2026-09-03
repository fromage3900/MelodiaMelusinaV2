"""tag_kaleido_encounter.py

Verify and (optionally) wire the KaleidoNave encounter on the placed `AMelodiaEncounterTrigger`
actor so the C++ battle adapter can find the stock JRPG battle actor.

ACTUAL MECHANISM (source-verified 2026-08-03):
    1. `AMelodiaEncounterTrigger::StartEncounterForPlayer()` / `OnTriggerOverlap()` call
       `TryStartStockJRPGBattle()`.
    2. That builds `EncounterId = "Encounter_<EnemyId>"` and calls
       `UMelodiaExternalJRPGBridgeSubsystem::StartTaggedJRPGBattle(EncounterId)`.
    3. The bridge searches the world for an actor with the tag `Encounter_<EnemyId>`.
    4. If exactly one match IS found, it runs that actor's `StartBattle` (stock contract).
    5. If NO tag match, the bridge falls back to *any* actor exposing the stock battle contract
       (`StartBattle` + `offLevelBattleData` + `OnBattleOver`), and logs a fallback notice.
    6. Independently, the battle request can also be driven by the narrative subsystem's
       `OnBattleRequested` -> `UMelodiaExternalJRPGBridgeSubsystem` (the production
       battle-start owner; it aborts the pending encounter when no tag matches).

CONCLUSION: The tag is OPTIONAL. The battle can start via the stock-contract fallback even if
no actor is tagged. The literal tag is `Encounter_<EnemyId>` (NOT `melodia_smoke_encounter`).

What this script does (reads + optional writes):
    - Finds the `AMelodiaEncounterTrigger` actor in the loaded level and reports its `EnemyId`.
    - Computes the expected encounter tag `Encounter_<EnemyId>`.
    - Reports whether any actor in the level already carries that tag (the direct match path).
    - Reports whether a stock battle-contract actor exists (the fallback path).
    - OPTIONALLY (--apply) adds the tag `Encounter_<EnemyId>` to the stock battle actor so the
      bridge can find it directly, instead of relying on the fallback.

Usage:
    Run inside the Unreal editor via the Monolith MCP server (uses `unreal` under the hood).
    Read-only audit by default; pass --apply only after confirming the battle actor is correct.

Safety:
    - Default (read-only): does NOT mutate any asset or actor.
    - --apply only touches the chosen actor's `Tags` array in the live level and validates
      read-back before reporting success.
"""

import unreal  # noqa: F401  (imported inside the editor runtime)

LEVEL = "L_KaleidoNave"
# Candidate labels for the placed encounter trigger (overlap volume that owns EnemyId).
TRIGGER_LABELS = ["MelodiaEncounterTrigger", "BP_InteractionBattle", "BP_Battle",
                  "BP_InteractionBattle_C", "BP_InteractionBattle_C_0", "BattleTrigger"]


def find_actors_by_label(level_actors, label):
    """Return actors whose label contains `label` (case-insensitive)."""
    return [a for a in level_actors if label.lower() in a.get_actor_label().lower()]


def has_stock_battle_contract(actor):
    """True if the actor exposes the stock JRPG battle contract used by the bridge fallback."""
    return (actor.find_function("StartBattle") and
            actor.find_property("offLevelBattleData") is not None and
            actor.find_property("OnBattleOver") is not None)


def main(apply=False):
    editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not editor_subsystem:
        unreal.log_error("[TAG_KALEIDO] EditorActorSubsystem unavailable.")
        return False

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world:
        level_name = world.get_name()
        if level_name != LEVEL:
            unreal.log_warning(f"[TAG_KALEIDO] Current level is '{level_name}', expected '{LEVEL}'. "
                               f"Running against current level anyway.")
    else:
        unreal.log_warning("[TAG_KALEIDO] No editor world; audit may be incomplete.")

    level_actors = editor_subsystem.get_all_level_actors()

    # 1) Find the encounter trigger (owns EnemyId).
    trigger = None
    for label in TRIGGER_LABELS:
        matches = find_actors_by_label(level_actors, label)
        if matches:
            trigger = matches[0]
            unreal.log(f"[TAG_KALEIDO] Found encounter trigger '{trigger.get_actor_label()}'.")
            break

    if not trigger:
        unreal.log_warning("[TAG_KALEIDO] No encounter trigger found in level. "
                           "Cannot compute the expected encounter tag.")
        return False

    # 2) Read EnemyId from the trigger.
    enemy_id = trigger.get_editor_property("EnemyId")
    if not enemy_id or enemy_id == unreal.Name("None"):
        unreal.log_warning("[TAG_KALEIDO] Encounter trigger has EnemyId = None. "
                           "Set EnemyId on the trigger (or skip the tag; the stock-contract "
                           "fallback works without it).")
        return False

    encounter_tag = f"Encounter_{enemy_id}"
    unreal.log(f"[TAG_KALEIDO] Actor EnemyId = '{enemy_id}'; expected bridge tag = '{encounter_tag}'.")

    # 3) Audit: does any actor already carry the tag? Does a stock-contract actor exist?
    tagged_actors = [a for a in level_actors if encounter_tag in a.get_actor_tags()]
    contract_actors = [a for a in level_actors if has_stock_battle_contract(a)]

    if tagged_actors:
        unreal.log(f"[TAG_KALEIDO] Direct-match path OK: {len(tagged_actors)} actor(s) tagged "
                   f"'{encounter_tag}' -> {[a.get_actor_label() for a in tagged_actors]}.")
    else:
        unreal.log(f"[TAG_KALEIDO] No actor tagged '{encounter_tag}' (direct-match path empty).")

    if contract_actors:
        unreal.log(f"[TAG_KALEIDO] Fallback path OK: {len(contract_actors)} actor(s) expose the "
                   f"stock battle contract -> {[a.get_actor_label() for a in contract_actors]}.")
    else:
        unreal.log_warning("[TAG_KALEIDO] No stock battle-contract actor found. The battle "
                           "cannot start via either path.")

    if not apply:
        unreal.log("[TAG_KALEIDO] Read-only audit complete. Re-run with --apply to tag the "
                   "stock battle actor with the expected encounter tag.")
        return bool(tagged_actors or contract_actors)

    # 4) --apply: tag the stock battle actor (prefer the tagged-candidate path).
    if tagged_actors:
        unreal.log("[TAG_KALEIDO] --apply: tag already present; nothing to do.")
        return True

    if not contract_actors:
        unreal.log_error("[TAG_KALEIDO] --apply: no stock battle-contract actor to tag. "
                         "Manual wiring required.")
        return False

    target = contract_actors[0]
    tags = list(target.get_actor_tags())
    if encounter_tag not in tags:
        tags.append(encounter_tag)
        target.set_actor_tags(tags)

    applied = encounter_tag in list(target.get_actor_tags())
    unreal.log(f"[TAG_KALEIDO] Verification: tag '{encounter_tag}' present on "
               f"'{target.get_actor_label()}' = {applied}.")
    if not applied:
        unreal.log_error("[TAG_KALEIDO] Tag not confirmed on read-back. Check actor write access.")
        return False

    unreal.log(f"[TAG_KALEIDO] SUCCESS: '{encounter_tag}' applied to '{target.get_actor_label()}'.")
    return True


if __name__ == "__main__":
    import sys
    apply = "--apply" in sys.argv
    ok = main(apply=apply)
    unreal.log(f"[TAG_KALEIDO] Completed with {'SUCCESS' if ok else 'FAILURE'}.")
