"""Smoke tests for the interaction and party systems.

Run with:
    python -m gmm.interaction_smoke
    or from Unreal Editor Python console:
        import gmm.interaction_smoke; gmm.interaction_smoke.run_smoke()
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def smoke_interaction() -> dict:
    """Run smoke tests for interaction system."""
    from gmm.game.interaction import (
        InteractionManager, InteractableType, InteractionResult
    )
    
    errors = []
    
    # Test 1: Door interaction
    print("1. Testing door interaction...")
    InteractionManager.register_interactable("door_01", InteractableType.DOOR, {"door_id": "door_01"})
    result = InteractionManager.interact("player", "door_01")
    if result.result != InteractionResult.SUCCESS:
        errors.append(f"Door interaction failed: {result.result}")
    print(f"   Door open: {result.interaction_data.get('now_open', False)}")
    
    # Test 2: Harvest node
    print("2. Testing harvest node interaction...")
    InteractionManager.register_interactable(
        "harvest_01", InteractableType.HARVEST_NODE,
        {"node_id": "harvest_01", "resource_type": "golden_token", "amount": 5}
    )
    result = InteractionManager.interact("player", "harvest_01")
    if result.result != InteractionResult.SUCCESS:
        errors.append(f"Harvest interaction failed: {result.result}")
    print(f"   Harvested: {result.interaction_data.get('harvested_amount', 0)} {result.interaction_data.get('resource_type', 'unknown')}")
    
    # Test 3: Harvest cooldown
    print("3. Testing harvest cooldown...")
    for _ in range(3):
        result = InteractionManager.interact("player", "harvest_01")
    if result.result != InteractionResult.COOLDOWN:
        errors.append(f"Harvest cooldown not triggered: {result.result}")
    print(f"   Cooldown triggered correctly")
    
    # Test 4: Door locked state
    print("4. Testing locked door...")
    InteractionManager.register_interactable(
        "locked_door", InteractableType.DOOR,
        {"door_id": "locked_door", "is_locked": True}
    )
    result = InteractionManager.interact("player", "locked_door")
    if result.result != InteractionResult.LOCKED:
        errors.append(f"Locked door not detected: {result.result}")
    print(f"   Locked state: {result.result.name}")
    
    summary = InteractionManager.instance()._interactables
    print(f"   Registered interactables: {len(summary)}")
    
    return {"errors": errors, "ok": len(errors) == 0}


def smoke_party() -> dict:
    """Run smoke tests for party system."""
    from gmm.game.party import Party, create_companion, COMPANION_ARCHETYPES
    
    errors = []
    
    # Test 1: Create party
    print("1. Testing party creation...")
    party = Party()
    if party.MAX_SIZE != 3:
        errors.append(f"Party max size wrong: {party.MAX_SIZE}")
    print(f"   Max party size: {party.MAX_SIZE}")
    
    # Test 2: Create companion
    print("2. Testing companion creation...")
    companion = create_companion("companion_01", "SakuraDreamer", level=2)
    if not companion:
        errors.append("Failed to create companion")
    else:
        print(f"   Created: {companion.character_name} (Lv.{companion.level})")
        print(f"   Element: {companion.element}, HP: {companion.max_hp}")
    
    # Test 3: Add to party
    print("3. Testing party add...")
    if companion:
        ok = party.add_member(companion)
        if not ok:
            errors.append("Failed to add companion to party")
        print(f"   Added to party: {ok}, members: {len(party.members)}")
    
    # Test 4: Create all archetypes
    print("4. Testing all companion archetypes...")
    for archetype_name in COMPANION_ARCHETYPES:
        c = create_companion(f"test_{archetype_name}", archetype_name)
        if c:
            print(f"   {c.character_name}: ({c.element}) HP:{c.max_hp} SP:{c.max_sp} SPD:{c.speed}")
        else:
            errors.append(f"Failed to create archetype: {archetype_name}")
    
    return {"errors": errors, "ok": len(errors) == 0}


def run_smoke() -> dict:
    """Run all smoke tests."""
    return {
        "interaction": smoke_interaction(),
        "party": smoke_party(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run interaction/party smoke tests.")
    parser.add_argument("--json-out", default="", help="Optional JSON report path.")
    args = parser.parse_args()
    
    report = run_smoke()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Interaction system: {'PASS' if report['interaction']['ok'] else 'FAIL'}")
    print(f"Party system: {'PASS' if report['party']['ok'] else 'FAIL'}")
    
    if args.json_out:
        text = json.dumps(report, indent=2)
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    
    return 0 if (report["interaction"]["ok"] and report["party"]["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())