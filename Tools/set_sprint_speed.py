#!/usr/bin/env python3
"""Set sprint speed on both pawns."""
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
    '',
    '# Fix 1: BP_MelusinaJRPGCharacter (JRPG battle pawn) - set speed to 714 (420*1.7)',
    'bpg = unreal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C")',
    'if bpg:',
    '    cdo = unreal.get_default_object(bpg)',
    '    if cdo:',
    '        cm = cdo.get_editor_property("CharacterMovement")',
    '        if cm:',
    '            old = cm.get_editor_property("MaxWalkSpeed")',
    '            print("BP_MelusinaJRPGCharacter MaxWalkSpeed was: " + str(old))',
    '            cm.set_editor_property("MaxWalkSpeed", 714)',
    '            print("Set to 714")',
    '            # Check parent class',
    '            p = cdo.get_editor_property("GetClass") if hasattr(cdo, "GetClass") else None',
    '',
    '# Fix 2: Also set on exploration pawn via CharacterMovement defaults',
    'smoke = unreal.load_object(name="/Script/MelodiaCore.MelodiaSmokeCharacter", outer=None)',
    'if smoke:',
    '    smoke_cdo = unreal.get_default_object(smoke)',
    '    if smoke_cdo:',
    '        cm_smoke = smoke_cdo.get_editor_property("CharacterMovement")',
    '        if cm_smoke:',
    '            old_smoke = cm_smoke.get_editor_property("MaxWalkSpeed")',
    '            print("\\nSmokeCharacter MaxWalkSpeed was: " + str(old_smoke))',
    '            cm_smoke.set_editor_property("MaxWalkSpeed", 714)',
    '            print("Set to 714")',
    '            old_sp = smoke_cdo.get_editor_property("SprintSpeedMultiplier")',
    '            print("SprintSpeedMultiplier: " + str(old_sp))',
    '    # Save the C++ config - need to save the default config',
    '    try:',
    '        smoke_cdo.save_config()',
    '        print("Saved SmokeCharacter config")',
    '    except Exception as e:',
    '        print("save_config: " + str(e)[:60])',
    '',
    '# Fix 3: Save the BP asset',
    'bp = unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter")',
    'if bp:',
    '    unreal.EditorAssetLibrary.save_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter")',
    '    print("\\nBP asset saved")',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
