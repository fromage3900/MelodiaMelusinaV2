"""GMM JRPG bridge daemon — template audit, enum maps, UE scaffold checklist."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gmm.daemon.generators import JRPG_GENERATORS
from gmm.daemon.shared import PROJECT_ROOT, PYTHON_DIR, PY, run_tick

DAEMON = "jrpg_bridge"
LABEL = "GMM jrpg_bridge"

TASKS = [
    {"id": "catalog_audit", "desc": "Run JRPG template disk audit", "file": "Saved/Audit/jrpg_template_catalog.json"},
    {"id": "action_map_expand", "desc": "Expand ACTION_TYPE handler map", "file": "gmm/game/jrpg_bridge.py"},
    {"id": "equip_crosswalk", "desc": "E_EquipmentType to DT crosswalk", "file": "gmm/game/jrpg_equip_crosswalk.json"},
    {"id": "quest_save_mapping", "desc": "S_PlayerUnitData to SaveSlot mapping", "file": "gmm/game/jrpg_save_mapping.json"},
    {"id": "bridge_registry", "desc": "Export JRPG bridge registry JSON", "file": "Saved/Audit/jrpg_bridge_registry.json"},
    {"id": "ue_scaffold_checklist", "desc": "UE scaffold checklist", "file": "Docs/MELODIA_JRPG_RHYTHM_SCAFFOLD.md"},
]


def _run_audit() -> str:
    script = PROJECT_ROOT / "Content" / "Python" / "audit_jrpg_template.py"
    env = {**dict(__import__("os").environ), "PYTHONPATH": PYTHON_DIR}
    proc = subprocess.run(
        [str(PY), str(script)], capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT),
    )
    out_path = PROJECT_ROOT / "Saved" / "Audit" / "jrpg_template_catalog.json"
    if out_path.is_file():
        return out_path.read_text(encoding="utf-8")
    raise RuntimeError(proc.stderr or proc.stdout or "audit failed")


def _gen_bridge_registry() -> str:
    from gmm.game.jrpg_bridge import bridge_summary
    import jrpg_template_catalog as cat

    data = {
        "bridge": bridge_summary(),
        "template_root": cat.TPL,
        "battle_assets": [a.name for a in cat.BATTLE_ASSETS[:12]],
        "struct_assets": [a.name for a in cat.STRUCT_ASSETS],
    }
    out = PROJECT_ROOT / "Saved" / "Audit" / "jrpg_bridge_registry.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out.read_text(encoding="utf-8")


GENERATORS = {
    **JRPG_GENERATORS,
    "catalog_audit": _run_audit,
    "bridge_registry": _gen_bridge_registry,
}

SMOKE_MODULES: list[str] = []


def _smoke_extra() -> dict:
    from gmm.game.jrpg_bridge import bridge_summary
    summary = bridge_summary()
    catalog = PROJECT_ROOT / "Saved" / "Audit" / "jrpg_template_catalog.json"
    return {
        "ok": summary.get("action_types", 0) >= 5,
        "catalog_exists": catalog.is_file(),
        "summary": summary,
    }


def main() -> int:
    return run_tick(
        DAEMON, TASKS, GENERATORS, SMOKE_MODULES,
        smoke_extra=_smoke_extra, label=LABEL,
    )


if __name__ == "__main__":
    raise SystemExit(main())
