#!/usr/bin/env python3
"""Scan BP_BattleController for dead islands via Monolith export."""
import json, sys, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
def monolith(tool, args, timeout=60):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode())
    result = data.get("result",{})
    if result.get("isError"):
        return "ERROR:" + result.get("content",[{}])[0].get("text","")
    return result.get("content",[{}])[0].get("text","")

# Export BP_BattleController as text and search for UToolMenus
print("=== Searching BP_BattleController for UToolMenus ===")
text = monolith("project_query", {"action":"export_asset_text","asset_path":"/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController"})
if text and "ERROR" not in text:
    tm_count = text.count("UToolMenus")
    tm_count += text.count("ToolMenus")
    print("ToolMenus/UToolMenus references: " + str(tm_count))
    if tm_count > 0:
        for i, line in enumerate(text.split("\\n")):
            if "UToolMenus" in line or "ToolMenus" in line:
                print("  L" + str(i) + ": " + line.strip()[:120])
    else:
        print("  None found - already cleaned")
    fc_count = text.count("Begin Object Class=/Script/Engine.K2Node_CallFunction")
    print("Total function call nodes: " + str(fc_count))
else:
    print("Export failed: " + str(text)[:200])

# Also check the EventGraph specifically
print("\n=== Exporting EventGraph ===")
eg = monolith("blueprint_query", {"action":"export_graph","asset_path":"/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController","graph_name":"EventGraph"})
if eg and "ERROR" not in eg:
    print("EventGraph exported (" + str(len(eg)) + " chars)")
    if "UToolMenus" in eg or "ToolMenus" in eg:
        print("  WARNING: UToolMenus still present!")
    else:
        print("  OK: No UToolMenus in EventGraph")
else:
    print("Export EventGraph failed: " + str(eg)[:200])

# Also check BP_MelodiaJRPGGameInstance  
print("\n=== BP_MelodiaJRPGGameInstance EventGraph ===")
eg2 = monolith("blueprint_query", {"action":"export_graph","asset_path":"/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance","graph_name":"EventGraph"})
if eg2 and "ERROR" not in eg2:
    if "UToolMenus" in eg2 or "ToolMenus" in eg2:
        print("  WARNING: UToolMenus still present!")
    else:
        print("  OK: No UToolMenus in EventGraph")
else:
    print("Export failed: " + str(eg2)[:200])

# Check kaleido encounter
print("\n=== KaleidoNave encounter tags ===")
kaleido = monolith("editor_query", {"action":"run_python","command":"import unreal; level = unreal.EditorAssetLibrary.load_asset('/Game/EnvSandbox/Environments/L_KaleidoNave'); actors = unreal.EditorLevelLibrary.get_all_level_actors() if hasattr(unreal.EditorLevelLibrary, 'get_all_level_actors') else []; print('Actors: ' + str(len(actors))); ta = [a for a in actors if a.actor_has_tag('melodia_smoke_encounter')]; print('Tagged melodia_smoke_encounter: ' + str(len(ta)))"})
print(kaleido[:500])
