"""Audit TurnBasedJRPGTemplate on disk and emit catalog JSON.

  python Content/Python/audit_jrpg_template.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jrpg_template_catalog import as_catalog_dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DISK_ROOT = PROJECT_ROOT / "Content" / "_ThirdParty" / "TurnBasedJRPGTemplate"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "jrpg_template_catalog.json"
WEB_OUT = PROJECT_ROOT / "my-site-clean" / "generated" / "jrpg_template_catalog.json"


def _count_uassets(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not root.is_dir():
        return counts
    for folder in root.iterdir():
        if folder.is_dir():
            counts[folder.name] = len(list(folder.rglob("*.uasset")))
    counts["total"] = len(list(root.rglob("*.uasset")))
    return counts


def main() -> int:
    catalog = as_catalog_dict()
    catalog["generated_at"] = datetime.now(timezone.utc).isoformat()
    catalog["disk_exists"] = DISK_ROOT.is_dir()
    catalog["disk_counts"] = _count_uassets(DISK_ROOT)

    # Verify key battle assets on disk
    key_names = [
        "BP_BattleController", "BP_BattleBase", "S_UnitStats", "S_PlayerUnitData",
        "E_EquipmentType", "E_ActionType", "BP_BattleUI", "BP_TurnOrderUI",
    ]
    found = []
    missing = []
    for name in key_names:
        hits = list(DISK_ROOT.rglob(f"{name}.uasset")) if DISK_ROOT.is_dir() else []
        if hits:
            found.append({"name": name, "path": str(hits[0].relative_to(PROJECT_ROOT))})
        else:
            missing.append(name)
    catalog["key_assets"] = {"found": found, "missing": missing}
    catalog["ready_for_bridge"] = catalog["disk_exists"] and not missing

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_OUT.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"JRPG_TEMPLATE_AUDIT -> {OUT}")
    print(f"  uassets: {catalog['disk_counts'].get('total', 0)}")
    print(f"  ready:   {catalog['ready_for_bridge']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
