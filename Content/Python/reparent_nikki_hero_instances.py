"""Reparent NikkiHero instances to Universal master for portfolio captures.

Run headless:
  python Content/Python/reparent_nikki_hero_instances.py

Run in-editor:
  py Content/Python/reparent_nikki_hero_instances.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

UNIVERSAL_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "nikki_hero_reparent.json"

NIKKI_HERO_INSTANCES = [
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SpaceCathedral",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_BioGrotto",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_BaroqueCastle",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_CosmicOrrery",
]


def reparent_instances() -> dict:
    """Reparent all NikkiHero instances to Universal master."""
    import unreal
    
    results = []
    universal = unreal.load_asset(UNIVERSAL_MASTER)
    
    if not universal:
        return {"error": "Universal master not found", "reparented": []}
    
    for inst_path in NIKKI_HERO_INSTANCES:
        name = inst_path.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(inst_path):
            results.append({"instance": name, "status": "not_found"})
            continue
        
        inst = unreal.load_asset(inst_path)
        if not inst:
            results.append({"instance": name, "status": "load_failed"})
            continue
        
        # Check current parent
        current_parent = None
        try:
            current_parent = inst.parent
        except Exception:
            pass
        
        # Reparent
        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, universal)
        results.append({
            "instance": name,
            "status": "reparented",
            "old_parent": str(current_parent) if current_parent else "none",
            "new_parent": UNIVERSAL_MASTER,
        })
    
    # Save all modified assets
    for inst_path in NIKKI_HERO_INSTANCES:
        if unreal.EditorAssetLibrary.does_asset_exist(inst_path):
            inst = unreal.load_asset(inst_path)
            if inst:
                unreal.EditorAssetLibrary.save_loaded_asset(inst)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "universal_parent": UNIVERSAL_MASTER,
        "reparented": results,
    }
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    return report


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
        report = reparent_instances()
        print(json.dumps(report, indent=2))
        raise SystemExit(0)
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            raise SystemExit(1)
        log = PROJECT_ROOT / "Saved" / "Logs" / "nikki_hero_reparent.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/reparent_nikki_hero_instances.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"NikkiHero reparent -> {log}")
        raise SystemExit(subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode)
