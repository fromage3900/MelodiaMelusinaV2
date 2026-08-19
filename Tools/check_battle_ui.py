#!/usr/bin/env python3
"""Check battle UI and rhythm highway paths."""
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
    '# Check alternative rhythm highway paths',
    'print("=== Rhythm Highway / Battle UI Search ===")',
    'paths = [',
    '    "/Game/Melodia/UI/WBP_MelodiaRhythmHighway",',
    '    "/Game/Melodia/UI/WBP_RhythmHighway",',
    '    "/Game/MelodiaIntegration/UI/WBP_MelodiaRhythmHighway",',
    '    "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI",',
    '    "/Game/Melodia/UI/WBP_BattleUI",',
    '    "/Game/Melodia/UI/WBP_CombatUI",',
    ']',
    'for p in paths:',
    '    a = unreal.EditorAssetLibrary.load_asset(p)',
    '    print("  " + p + ": " + ("FOUND" if a else "MISSING"))',
    '',
    '# Check MelodiaIntegration UI folder',
    'print("\\n=== MelodiaIntegration UI folder ===")',
    'folder = unreal.EditorAssetLibrary.list_assets("/Game/MelodiaIntegration/UI", recursive=False)',
    'if folder:',
    '    for f in folder:',
    '        print("  " + str(f)[:80])',
    'else:',
    '    print("  No assets found")',
    '',
    '# Check Melodia UI folder for battle widgets',
    'print("\\n=== Melodia UI / Battle Widgets ===")',
    'folder2 = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/UI", recursive=False)',
    'if folder2:',
    '    for f in folder2:',
    '        name = str(f)',
    '        if "attle" in name.lower() or "ombat" in name.lower() or "hythm" in name.lower() or "highway" in name.lower():',
    '            print("  " + name[:80])',
    '',
    '# Check BP_BattleController for dead islands',
    'print("\\n=== Battle Controller Graph export spot-check ===")',
    'bp = unreal.EditorAssetLibrary.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController")',
    'if bp:',
    '    # Read CDO for battle state',
    '    bp_c = unreal.load_asset(bp.get_path_name() + "_C")',
    '    if bp_c:',
    '        cdo = unreal.get_default_object(bp_c)',
    '        for pn in ["mainMenuMapName", "battleResult", "currentBattle", "defaultEnemy"]:',
    '            try:',
    '                val = cdo.get_editor_property(pn)',
    '                print("  " + pn + " = " + str(val)[:80])',
    '            except:',
    '                print("  " + pn + ": NOT FOUND")',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
