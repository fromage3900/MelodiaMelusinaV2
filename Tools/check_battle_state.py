#!/usr/bin/env python3
"""Check battle maps, rhythm systems, and run PIE tests."""
import json, sys, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
def monolith(tool, args, timeout=30):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode())
    result = data.get("result",{})
    if result.get("isError"):
        return "ERROR:" + result.get("content",[{}])[0].get("text","")
    return result.get("content",[{}])[0].get("text","")

lines = [
    'import unreal',
    '# Check battle maps',
    'maps = [',
    '    "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",',
    '    "/Game/EnvSandbox/Environments/L_KaleidoNave",',
    '    "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate",',
    '    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",',
    '    "/Game/Melodia/Levels/Opening/L_MelusinaMorning2",',
    ']',
    'print("=== Maps ===")',
    'for p in maps:',
    '    a = unreal.EditorAssetLibrary.load_asset(p)',
    '    print("  " + p + ": " + ("FOUND" if a else "MISSING"))',
    '# Check battle BPs',
    'print("\\n=== Battle BPs ===")',
    'for bp_name in ["BP_BattleController", "BP_MelodiaBattleUI", "BP_InteractionBattle", "BP_BattleBase", "BP_OffLevelBattle", "BP_MelodiaJRPGGameMode"]:',
    '    bp = unreal.EditorAssetLibrary.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/" + bp_name) if bp_name not in ["BP_MelodiaJRPGGameMode"] else unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Blueprints/" + bp_name)',
    '    print("  " + bp_name + ": " + ("FOUND" if bp else "MISSING"))',
    '# Check rhythm assets',
    'print("\\n=== Rhythm Systems ===")',
    'rhythm = [',
    '    "/Game/Melodia/UI/WBP_MelodiaRhythmHighway",',
    '    "/Game/MelodiaIntegration/MIDI/Melodia_Battle_00",',
    '    "/Game/MelodiaIntegration/Config/DA_MelodiaSongs",',
    '    "/Game/Melodia/Blueprints/Rhythm/BP_MelodiaRhythmSubsystem",',
    ']',
    'for p in rhythm:',
    '    a = unreal.EditorAssetLibrary.load_asset(p)',
    '    print("  " + p + ": " + ("FOUND" if a else "MISSING"))',
    '# Check Melusina combat presentation',
    'print("\\n=== Combat Presentation ===")',
    'for bp_name in ["BP_MelusinaSwordsman_Presentation", "BP_MelusinaPetalCadence", "BP_SirSkyboundRefrain"]:',
    '    bp = unreal.EditorAssetLibrary.load_asset("/Game/Experiments/MelodiaJRPG/" + bp_name) if bp_name.startswith("BP_Melusina") else unreal.EditorAssetLibrary.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Skills/" + bp_name)',
    '    print("  " + bp_name + ": " + ("FOUND" if bp else "MISSING"))',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
