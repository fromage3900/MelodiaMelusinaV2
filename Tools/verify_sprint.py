#!/usr/bin/env python3
"""Verify properties on BP_MelusinaJRPGCharacter and smoke character."""
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
    '# Test 1: Smoke character CDO (C++)',
    'smoke_cdo = unreal.get_default_object(unreal.load_class("/Script/MelodiaCore.MelodiaSmokeCharacter"))',
    'if smoke_cdo:',
    '    print("=== AMelodiaSmokeCharacter CDO ===")',
    '    for pn in ["SprintSpeedMultiplier", "MoveSpeedScale", "BaseWalkSpeed", "JumpWindupTime", "CoyoteTime", "JumpBufferTime", "FallGravityScale", "bEnableSkirtClothSimulation"]:',
    '        try:',
    '            val = smoke_cdo.get_editor_property(pn) if hasattr(smoke_cdo, "get_editor_property") else getattr(smoke_cdo, pn, "NOT_FOUND")',
    '            print("  " + pn + " = " + str(val))',
    '        except Exception as e:',
    '            print("  " + pn + ": " + str(e)[:60])',
    'else:',
    '    print("Smoke CDO not found")',
    '',
    '# Test 2: BP_MelusinaJRPGCharacter CDO',
    'bp = unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter")',
    'if bp:',
    '    print("\\n=== BP_MelusinaJRPGCharacter ===")',
    '    # Try to get the generated class',
    '    try:',
    '        gen_cls = bp.generated_class',
    '        print("generated_class: " + str(gen_cls))',
    '    except Exception as e:',
    '        print("generated_class error: " + str(e)[:60])',
    '        gen_cls = None',
    '    # Try BP class path',
    '    bp_cls = unreal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter._C")',
    '    if bp_cls:',
    '        print("BP_C loaded")',
    '        cdo = unreal.get_default_object(bp_cls)',
    '        if cdo:',
    '            for pn in ["SprintSpeedMultiplier", "MoveSpeedScale", "MaxWalkSpeed", "JumpZVelocity"]:',
    '                try:',
    '                    val = cdo.get_editor_property(pn) if hasattr(cdo, "get_editor_property") else getattr(cdo, pn, "NOT_FOUND")',
    '                    print("  CDO." + pn + " = " + str(val))',
    '                except Exception as e:',
    '                    print("  CDO." + pn + ": " + str(e)[:60])',
]

result = monolith("editor_query", {"action":"run_python","command":"\n".join(lines)})
print(result)
