"""GMM Game subpackage daemon — equipment, config, tests, quest stub."""
from __future__ import annotations

from gmm.daemon.generators import GAME_GENERATORS
from gmm.daemon.shared import run_tick

DAEMON = "game"
LABEL = "GMM game"

TASKS = [
    {"id": "equip_weapons", "desc": "Add 5 rare weapons", "file": "gmm/game/equipment_catalog.py"},
    {"id": "equip_armors", "desc": "Add 5 rare armors", "file": "gmm/game/equipment_catalog.py"},
    {"id": "game_cfg_patch", "desc": "GAME_CFG wiring patch for battle_manager", "file": "gmm/game/battle_manager.py"},
    {"id": "test_save_manager", "desc": "Add save_manager unit tests", "file": "gmm/tests/test_save_manager.py"},
    {"id": "test_battle_edge", "desc": "Add battle_manager edge case tests", "file": "gmm/tests/test_battle_manager.py"},
    {"id": "quest_stub", "desc": "Quest manager stub (BP_QuestManager)", "file": "gmm/game/quest_manager.py"},
]

SMOKE_MODULES = [
    "gmm.tests.test_battle_manager",
    "gmm.tests.test_player_state",
    "gmm.tests.test_rhythm_clock",
]


def main() -> int:
    return run_tick(DAEMON, TASKS, GAME_GENERATORS, SMOKE_MODULES, label=LABEL)


if __name__ == "__main__":
    raise SystemExit(main())
