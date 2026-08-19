#!/usr/bin/env python3
"""Fix CDO MaxWalkSpeed back to 420, keep SprintSpeedMultiplier=1.7."""
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
    '# Fix SmokeCharacter: revert MaxWalkSpeed to 420, keep SprintSpeedMultiplier at 1.7',
    'smoke = unreal.load_object(name="/Script/MelodiaCore.MelodiaSmokeCharacter", outer=None)',
    'if smoke:',
    '    cdo = unreal.get_default_object(smoke)',
    '    if cdo:',
    '        cm = cdo.get_editor_property("CharacterMovement")',
    '        if cm:',
    '            cm.set_editor_property("MaxWalkSpeed", 420)',
    '            print("SmokeCharacter MaxWalkSpeed: 420")',
    '        sp = cdo.get_editor_property("SprintSpeedMultiplier")',  
    '        print("SprintSpeedMultiplier: " + str(sp))',
    '        # Re-set to 1.7 to be sure',
    '        cdo.set_editor_property("SprintSpeedMultiplier", 1.7)',
    '        sp2 = cdo.get_editor_property("SprintSpeedMultiplier")',
    '        print("After set: " + str(sp2))',
    '',
    '# Fix BP_MelusinaJRPGCharacter: MaxWalkSpeed should stay 600 (stock template default)',
    'bpg = unreal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C")',
    'if bpg:',
    '    cdo = unreal.get_default_object(bpg)',
    '    if cdo:',
    '        cm = cdo.get_editor_property("CharacterMovement")',
    '        if cm:',
    '            # Keep at 600 for JRPG, the sprint is handled differently',
    '            cm.set_editor_property("MaxWalkSpeed", 600)',
    '            print("\\nBP_MelusinaJRPGCharacter MaxWalkSpeed: 600")',
    '    unreal.EditorAssetLibrary.save_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter")',
    '    print("BP saved")',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
