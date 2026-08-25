#!/usr/bin/env python3
"""
fix_save_defect2.py - Fix slot name mismatch across save system.

Changes:
  1. BP_SavePointBase:   replace ToString(index) slot name with "MelodiaJRPGSlot0"
  2. WBP_SaveLoadPanel:  change "MelusinaSlot0" -> "MelodiaJRPGSlot0"
  3. WBP_MainMenu:       already "MelodiaJRPGSlot0" - verify only
"""

import json, os, subprocess, sys, time, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
PROXY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "Plugins", "Monolith", "Binaries", "monolith_proxy.exe")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _start_proxy():
    proc = subprocess.Popen(
        [PROXY], cwd=PROJECT_ROOT, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    time.sleep(2)
    return proc


def monolith(method, args, timeout=30):
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": method, "arguments": args}
    })
    req = urllib.request.Request(
        MCP_URL, data=body.encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode())
    return data.get("result", {}).get("content", [{}])[0].get("text", "")


def check(err, label):
    if err.startswith("ERROR"):
        print(f"  FAIL: {label} - {err[:200]}")
    else:
        print(f"  OK: {label}")


def fix_bp_savepointbase_slot_name(proxy_proc):
    """Fix BP_SavePointBase: override slotName via set_pin_default + disconnect old path."""
    bp = "/Game/TurnBasedJRPGTemplate/Blueprints/Interactables/BP_SavePointBase"

    # Step 1: Disconnect ToString.ReturnValue -> SaveGame.slotName
    r = monolith("blueprint_query", {
        "action": "disconnect_pins",
        "asset_path": bp,
        "graph_name": "EventGraph",
        "source_node_id": "K2Node_CallFunction_1",
        "source_pin_name": "ReturnValue",
        "target_node_id": "K2Node_CallFunction_6",
        "target_pin_name": "slotName"
    })
    check(r, "Disconnect ToString.ReturnValue -> SaveGame.slotName")

    # Step 2: Set slotName pin default to "MelodiaJRPGSlot0"
    r = monolith("blueprint_query", {
        "action": "set_pin_default",
        "asset_path": bp,
        "graph_name": "EventGraph",
        "node_id": "K2Node_CallFunction_6",
        "pin_name": "slotName",
        "default_value": "MelodiaJRPGSlot0"
    })
    check(r, "Set SaveGame.slotName = MelodiaJRPGSlot0")

    # Compile
    r = monolith("blueprint_query", {
        "action": "compile_blueprint",
        "asset_path": bp
    })
    check(r, "Compile BP_SavePointBase")
    try:
        parsed = json.loads(r) if r else {}
        if isinstance(parsed, dict):
            errs = parsed.get("error_count", parsed.get("errors", "?"))
            print(f"  Compile errors: {errs}")
    except (json.JSONDecodeError, TypeError):
        print(f"  Compile: {r[:200]}")


def fix_wbp_saveloadpanel_slot_name(proxy_proc):
    """Fix WBP_SaveLoadPanel: change MelusinaSlot0 -> MelodiaJRPGSlot0."""
    widget = "/Game/Melodia/UI/WBP_SaveLoadPanel"

    # Use editor Python to find and change the pin
    python_code = r'''
import unreal

widget_path = "/Game/Melodia/UI/WBP_SaveLoadPanel"
widget = unreal.load_asset(widget_path)
if not widget:
    print("ERROR: could not load widget")
else:
    wc = unreal.load_asset(widget_path + "_C")
    if not wc:
        print("ERROR: could not load widget class")
    else:
        found = False
        for graph in unreal.BlueprintEditorUtils.get_all_graphs(wc):
            for node in graph.get_nodes():
                for pin in node.get_pins():
                    val = pin.get_default_as_string()
                    if val and "MelusinaSlot0" in val:
                        print("Found MelusinaSlot0 at node=" + node.get_name() + " pin=" + pin.get_name())
                        pin.set_default_value("MelodiaJRPGSlot0")
                        print("Changed to MelodiaJRPGSlot0")
                        found = True
        if not found:
            print("MelusinaSlot0 not found - already fixed or in different location")

# Also compile
unreal.BlueprintEditorUtils.compile_blueprint(unreal.load_asset(widget_path))
print("Compiled WBP_SaveLoadPanel")
'''.strip()

    r = monolith("editor_query", {
        "action": "run_python",
        "script": python_code
    }, timeout=60)
    check(r, "Fix WBP_SaveLoadPanel slot name")
    if len(r) > 500:
        print(f"  Result: {r[:500]}")
    else:
        print(f"  Result: {r}")


def verify_wbp_mainmenu(proxy_proc):
    """Verify WBP_MainMenu already uses MelodiaJRPGSlot0."""
    text = monolith("project_query", {
        "action": "export_asset_text",
        "asset_path": "/Game/Melodia/UI/WBP_MainMenu"
    })
    if "MelodiaJRPGSlot0" in text:
        print("  WBP_MainMenu: MelodiaJRPGSlot0 present - OK")
    else:
        print("  WBP_MainMenu: MelodiaJRPGSlot0 NOT FOUND - checking...")
        if "MelusinaSlot0" in text:
            print("  WBP_MainMenu: has MelusinaSlot0 - needs fix")
        else:
            idx = text.find("JRPGSlot")
            if idx >= 0:
                print(f"  Found JRPGSlot at offset {idx}: {text[idx:idx+50]}")

    # Check CreateCanonicalJRPGSlot function for slot name
    functions = monolith("blueprint_query", {
        "action": "get_functions",
        "asset_path": "/Game/Melodia/UI/WBP_MainMenu"
    })
    print(f"  WBP_MainMenu functions: {functions[:500]}")


def main():
    proxy = _start_proxy()
    try:
        print("=" * 60)
        print("Defect 2: Fix slot name mismatch - unify to MelodiaJRPGSlot0")
        print("=" * 60)

        print("\n--- Part A: BP_SavePointBase ---")
        fix_bp_savepointbase_slot_name(proxy)

        print("\n--- Part B: WBP_SaveLoadPanel ---")
        fix_wbp_saveloadpanel_slot_name(proxy)

        print("\n--- Part C: Verify WBP_MainMenu ---")
        verify_wbp_mainmenu(proxy)

        print("\nDefect 2 fix applied.")
    finally:
        proxy.stdin.close()
        proxy.wait(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
