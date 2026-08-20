#!/usr/bin/env python3
"""Static audit of the First Dream battle path.

Runs without the editor by reading config files and checking disk assets.
If Monolith (port 9316) is reachable, it also performs live registry checks.
Output: Saved/Audit/battle_static_<timestamp>.json
"""
from __future__ import annotations

import configparser
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SAVED = PROJECT / "Saved"
AUDIT_DIR = SAVED / "Audit"
MCP = "http://127.0.0.1:9316/mcp"

# Config-driven or canonical assets for the First Dream battle path.
CONFIG_ASSETS = [
    ("/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode", "GameMode"),
    ("/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance", "GameInstance"),
    ("/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController", "PlayerController"),
    ("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController", "BattleController"),
    ("/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI", "BattleUI"),
    ("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI", "LegacyBattleUI"),
    ("/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro", "MorningIntro"),
    ("/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig", "IntegrationConfig"),
]

LEVEL_ASSETS = [
    ("/Game/EnvSandbox/Environments/L_KaleidoNave", "KaleidoNave"),
    ("/Game/Melodia/Levels/Opening/L_MelusinaMorning", "MelusinaMorning"),
]

NARRATIVE_ASSETS = [
    ("/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke", "QuillSmoke"),
]

SOURCE_FILES = [
    ("Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.cpp", "BridgeSubsystem"),
    ("Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp", "NarrativeSubsystem"),
    ("Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPostBattleLibrary.cpp", "PostBattleLibrary"),
]


def asset_path_to_disk(asset_path: str, ext: str = ".uasset") -> Path:
    """Convert /Game/... asset path to Content/... disk path with given extension."""
    rel = asset_path.lstrip("/")
    if rel.startswith("Game/"):
        rel = rel[5:]
    return (PROJECT / "Content" / rel.replace("/", os.sep)).with_suffix(ext)


def check_disk_asset(asset_path: str, ext: str = ".uasset") -> dict[str, Any]:
    path = asset_path_to_disk(asset_path, ext)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {"path": str(path.relative_to(PROJECT)), "exists": exists, "size": size}


def read_game_maps_settings() -> dict[str, Any]:
    cfg = configparser.ConfigParser(strict=False)
    cfg.optionxform = str
    engine_ini = PROJECT / "Config" / "DefaultEngine.ini"
    cfg.read(engine_ini, encoding="utf-8-sig")
    section = "/Script/EngineSettings.GameMapsSettings"
    if not cfg.has_section(section):
        return {"error": f"{engine_ini} missing [{section}]"}
    keys = ["GlobalDefaultGameMode", "GameDefaultMap", "EditorStartupMap", "GameInstanceClass"]
    return {k: cfg.get(section, k, fallback=None) for k in keys}


def read_maps_to_cook() -> list[str]:
    game_ini = PROJECT / "Config" / "DefaultGame.ini"
    section = "/Script/UnrealEd.ProjectPackagingSettings"
    key = "+MapsToCook"
    maps = []
    in_section = False
    for raw_line in game_ini.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_section = line[1:-1] == section
            continue
        if not in_section:
            continue
        if line.startswith(key):
            entry = line[len(key):].lstrip("= ").strip()
            # Handle FilePath="/Game/...")
            if "=" in entry:
                _, value = entry.split("=", 1)
                entry = value.strip().strip('"').rstrip(")").rstrip('"')
            maps.append(entry)
    return maps


def monolith_reachable() -> bool:
    try:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
        req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def monolith_call(tool: str, args: dict[str, Any]) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    result = data.get("result", {})
    if result.get("isError"):
        raise RuntimeError(result.get("content", [{}])[0].get("text", "unknown"))
    text = result.get("content", [{}])[0].get("text", "")
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {"raw": text}


def live_level_check(level_path: str) -> dict[str, Any] | None:
    """Return actor/tag counts for a level via Monolith."""
    if not monolith_reachable():
        return None
    command = (
        "import unreal\n"
        f"level = unreal.EditorAssetLibrary.load_asset('{level_path}')\n"
        "actors = unreal.EditorLevelLibrary.get_all_level_actors()\n"
        "tagged = [a for a in actors if a.actor_has_tag('melodia_smoke_encounter')]\n"
        "controllers = [a for a in actors if 'BP_BattleController' in a.get_class().get_name()]\n"
        f"print('__RESULT__{{\"actors\":' + str(len(actors)) + ', \"tagged\":' + str(len(tagged)) + ', \"controllers\":' + str(len(controllers)) + '}}')"
    )
    try:
        raw = monolith_call("editor_query", {"action": "run_python", "command": command})
        output = raw.get("output", [])
        for item in output:
            text = item.get("output", "") if isinstance(item, dict) else str(item)
            for line in str(text).splitlines():
                if line.startswith("__RESULT__"):
                    return json.loads(line[len("__RESULT__"):])
        return {"error": "no result marker", "raw": raw}
    except Exception as exc:
        return {"error": str(exc)}


def main() -> int:
    stamp = int(time.time())
    report: dict[str, Any] = {
        "timestamp": stamp,
        "monolith_reachable": monolith_reachable(),
        "game_maps_settings": read_game_maps_settings(),
        "maps_to_cook": read_maps_to_cook(),
        "assets": {},
        "levels": {},
        "narrative": {},
        "source_files": {},
        "live_checks": {},
        "notes": [],
    }

    for asset_path, label in CONFIG_ASSETS + NARRATIVE_ASSETS:
        report["assets"][label] = check_disk_asset(asset_path)
    for asset_path, label in LEVEL_ASSETS:
        report["levels"][label] = check_disk_asset(asset_path, ext=".umap")

    for rel_path, label in SOURCE_FILES:
        full = PROJECT / rel_path
        report["source_files"][label] = {
            "path": rel_path,
            "exists": full.exists(),
            "size": full.stat().st_size if full.exists() else 0,
        }

    if report["monolith_reachable"]:
        for asset_path, label in LEVEL_ASSETS:
            report["live_checks"][label] = live_level_check(asset_path)
    else:
        report["notes"].append("Monolith unreachable; live level actor/tag counts skipped. Re-run when editor+Monolith are free.")

    # Inferred config consistency checks.
    game_maps = report["game_maps_settings"]
    if game_maps.get("GlobalDefaultGameMode") and "BP_MelodiaJRPGGameMode" not in game_maps["GlobalDefaultGameMode"]:
        report["notes"].append("GlobalDefaultGameMode is not BP_MelodiaJRPGGameMode.")
    if game_maps.get("GameInstanceClass") and "BP_MelodiaJRPGGameInstance" not in game_maps["GameInstanceClass"]:
        report["notes"].append("GameInstanceClass is not BP_MelodiaJRPGGameInstance.")

    cooked = report["maps_to_cook"]
    if "/Game/EnvSandbox/Environments/L_KaleidoNave" not in cooked:
        report["notes"].append("L_KaleidoNave is missing from MapsToCook.")
    if "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate" in cooked:
        report["notes"].append("L_Melodia_Dreamstate is still in MapsToCook despite being deleted (may be intentional for cook coverage).")
    if "/Game/ZenForestTest" in cooked:
        report["notes"].append("ZenForestTest is still in MapsToCook despite route retarget to KaleidoNave (may be intentional for cook coverage).")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / f"battle_static_{stamp}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    print(f"\nreport: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
