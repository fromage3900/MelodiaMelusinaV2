"""Smoke tests for roguelike systems - deterministic tests without UE editor."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from gmm.game.roguelike import (
    generate_floor,
    select_random_enemy,
    get_room_template,
    ROOM_TEMPLATES,
    ARTIFACTS,
    BLESSINGS,
)


def test_floor_generation() -> dict:
    """Test deterministic floor generation."""
    results = []
    
    for seed in [1337, 4242, 99999]:
        random.seed(seed)
        floors = [generate_floor(i, seed) for i in range(1, 11)]
        results.append({
            "seed": seed,
            "floors_1_10": floors,
            "boss_floors": [i for i in range(1, 11) if "boss" in floors[i-1]],
        })
    
    return {"floors_generated": len(results), "samples": results}


def test_room_templates() -> dict:
    """Verify room templates exist and have valid data."""
    checks = {}
    
    for room_id, template in ROOM_TEMPLATES.items():
        checks[room_id] = {
            "has_display_name": bool(template.display_name),
            "has_enemy_pool": bool(template.enemy_pool) or template.is_shop_room or template.is_treasure_room,
            "is_shop": template.is_shop_room,
            "is_treasure": template.is_treasure_room,
            "is_boss": template.is_boss_room,
            "enemy_count": len(template.enemy_pool),
        }
    
    return {"room_templates": checks, "all_valid": all(c["has_display_name"] for c in checks.values())}


def test_artifact_system() -> dict:
    """Test artifact data and modifier references."""
    from gmm.game.modifiers import modifier_registry_summary
    
    modifier_ids = set(modifier_registry_summary()["ids"])
    
    checks = {}
    for artifact_id, artifact in ARTIFACTS.items():
        checks[artifact_id] = {
            "has_modifier": artifact.modifier_id in modifier_ids,
            "has_cost": artifact.cost_golden_tokens > 0,
            "modifier_id": artifact.modifier_id,
        }
    
    return {"artifacts": checks, "all_valid": all(c["has_modifier"] for c in checks.values())}


def test_blessing_system() -> dict:
    """Test blessing data and costs."""
    checks = {}
    total_token_cost = 0
    
    for blessing_id, blessing in BLESSINGS.items():
        checks[blessing_id] = {
            "has_cost": blessing.token_cost > 0,
            "cost": blessing.token_cost,
            "has_effect_type": bool(blessing.effect_type),
        }
        total_token_cost += blessing.token_cost
    
    return {
        "blessings": checks,
        "total_token_cost_all": total_token_cost,
        "all_valid": all(c["has_cost"] for c in checks.values()),
    }


def test_enemy_selection() -> dict:
    """Test random enemy selection from rooms."""
    results = []
    
    for room_id in ["standard", "elite", "boss"]:
        enemies = set()
        for seed in range(100):
            random.seed(seed)
            enemy = select_random_enemy(room_id, seed)
            if enemy:
                enemies.add(enemy)
        
        results.append({
            "room_id": room_id,
            "unique_enemies": list(enemies),
            "enemy_count": len(enemies),
        })
    
    return {"selections": results}


def run_smoke(seed: int = 20260714) -> dict:
    """Run all roguelike smoke tests."""
    return {
        "ok": True,
        "seed": seed,
        "floor_generation": test_floor_generation(),
        "room_templates": test_room_templates(),
        "artifacts": test_artifact_system(),
        "blessings": test_blessing_system(),
        "enemy_selection": test_enemy_selection(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run roguelike smoke tests.")
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--json-out", default="", help="Optional JSON report path.")
    args = parser.parse_args()

    report = run_smoke(seed=args.seed)
    text = json.dumps(report, indent=2)
    print(text)

    # Verify all checks passed
    ok = (
        report["room_templates"]["all_valid"]
        and report["artifacts"]["all_valid"]
        and report["blessings"]["all_valid"]
    )

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())