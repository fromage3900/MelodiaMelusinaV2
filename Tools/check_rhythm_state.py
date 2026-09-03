#!/usr/bin/env python3
"""Check rhythm system state and DA_MelodiaSongs config."""
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
    '# Check DA_MelodiaSongs',
    'da = unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Config/DA_MelodiaSongs")',
    'if da:',
    '    print("DA_MelodiaSongs FOUND")',
    '    for p in dir(da):',
    '        if not p.startswith("_"):',
    '            try:',
    '                v = da.get_editor_property(p)',
    '                print("  " + p + " = " + str(v)[:100])',
    '            except:',
    '                pass',
    'else:',
    '    print("DA_MelodiaSongs MISSING")',
    '',
    '# Check Harmonix plugin availability',
    'print("\\n=== Harmonix/MIDI check ===")',
    'for cls_name in ["HarmonixPlayer", "MidiClockManager", "MusicClockSubsystem", "SynthComponent"]:',
    '    try:',
    '        cls = getattr(unreal, cls_name, None)',
    '        print("  " + cls_name + ": " + ("AVAILABLE" if cls else "NOT_IN_UNREAL_MODULE"))',
    '    except:',
    '        print("  " + cls_name + ": ERROR")',
    '',
    '# Check BP_BattleController graph for rhythm wires',
    'print("\\n=== BP_BattleController rhythm check ===")',
    'bp = unreal.EditorAssetLibrary.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController")',
    'if bp:',
    '    bpg = unreal.load_asset(bp.get_path_name() + "._C")',
    '    if not bpg:',
    '        bpg = unreal.load_asset(bp.get_path_name() + "_C")',
    '    if bpg:',
    '        print("  BP_BattleController_C loaded")',
    '        # Search for rhythm-related functions',
    '        for graph in unreal.BlueprintEditorUtils.get_all_graphs(bpg):',
    '            gname = graph.get_name()',
    '            if "ythm" in gname.lower() or "song" in gname.lower() or "beat" in gname.lower() or "skil" in gname.lower():',
    '                print("  Rhythm graph: " + gname)',
    '        print("  Total graphs: " + str(len(unreal.BlueprintEditorUtils.get_all_graphs(bpg))))',
    '    else:',
    '        print("  BP_BattleController_C not found")',
    '',
    '# Check WBP_MelodiaRhythmHighway alternative paths',
    'print("\\n=== Rhythm Highway search ===")',
    'for alt_path in [',
    '    "/Game/Melodia/UI/WBP_MelodiaRhythmHighway",',
    '    "/Game/Melodia/UI/WBP_RhythmHighway",',
    '    "/Game/MelodiaIntegration/UI/WBP_MelodiaRhythmHighway",',
    '    "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI",',
    ']:',
    '    a = unreal.EditorAssetLibrary.load_asset(alt_path)',
    '    print("  " + alt_path + ": " + ("FOUND" if a else "MISSING"))',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
