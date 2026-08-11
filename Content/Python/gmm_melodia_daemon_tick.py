"""GMM Melodia subpackage daemon — enemies + skills content staging."""
from __future__ import annotations

from gmm.daemon.generators import MELODIA_GENERATORS
from gmm.daemon.shared import run_tick

DAEMON = "melodia"
LABEL = "GMM melodia"

TASKS = [
    {"id": "enemy_forte", "desc": "Add Forte-element enemy (Fire Drake)", "file": "gmm/melodia/enemies.py"},
    {"id": "enemy_umbral", "desc": "Add Umbral-element enemy (Shadow Wraith)", "file": "gmm/melodia/enemies.py"},
    {"id": "enemy_arcane", "desc": "Add Arcane-element enemy (Arcane Golem)", "file": "gmm/melodia/enemies.py"},
    {"id": "enemy_gale", "desc": "Add Gale-element enemy (Storm Falcon)", "file": "gmm/melodia/enemies.py"},
    {"id": "enemy_tide", "desc": "Add Tide-element enemy (Abyssal Kraken)", "file": "gmm/melodia/enemies.py"},
    {"id": "skills_l10", "desc": "Add skills level 10-14 (5 new)", "file": "gmm/melodia/skills.py"},
    {"id": "skills_l15", "desc": "Add skills level 15-19 (5 new)", "file": "gmm/melodia/skills.py"},
    {"id": "skills_l20", "desc": "Add skills level 20-24 (5 new)", "file": "gmm/melodia/skills.py"},
    {"id": "skills_l25", "desc": "Add skills level 25-30 (5 new)", "file": "gmm/melodia/skills.py"},
]

SMOKE_MODULES = ["gmm.tests.test_data_registry"]


def _smoke_extra() -> dict:
    from gmm.melodia.enemies import audit_enemy_summary
    summary = audit_enemy_summary()
    return {"ok": summary.get("count", 0) > 0, "enemy_count": summary.get("count")}


def main() -> int:
    return run_tick(
        DAEMON, TASKS, MELODIA_GENERATORS, SMOKE_MODULES,
        smoke_extra=_smoke_extra, label=LABEL,
    )


if __name__ == "__main__":
    raise SystemExit(main())
