#!/usr/bin/env python3
"""
fix_save_defect1.py - Fix BP_MelodiaJRPGGameInstance::OnNewGameStarted exec chain.

Defect: OnNewGameStarted event runs only RegisterSkill x3 and terminates.
The stock CreateSaveGameObject -> Set jRPGSaveGame_0 chain is reachable ONLY
via Array_Add (AddInteractions) -> UToolMenus::Get, which is editor-only.

Fix:
  1. Disconnect OnNewGameStarted.then -> RegisterSkill[0].execute
  2. Connect   OnNewGameStarted.then -> CreateSaveGameObject.execute
  3. Remove    UToolMenus::Get node
  4. Connect   Set shouldLoadGame_0.then -> RegisterSkill[0].execute
  5. Compile
"""

import json, os, subprocess, sys, time, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
BP_PATH = "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance"

PROXY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Plugins", "Monolith", "Binaries", "monolith_proxy.exe"
)
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


def main():
    proxy = _start_proxy()
    try:
        print("=" * 60)
        print("Defect 1: Fix BP_MelodiaJRPGGameInstance OnNewGameStarted exec chain")
        print("=" * 60)

        # Step 1: Disconnect OnNewGameStarted.then -> RegisterSkill[0].execute
        r = monolith("blueprint_query", {
            "action": "disconnect_pins",
            "asset_path": BP_PATH,
            "graph_name": "EventGraph",
            "source_node_id": "K2Node_CustomEvent_2",
            "source_pin_name": "then",
            "target_node_id": "K2Node_CallFunction_46",
            "target_pin_name": "execute"
        })
        check(r, "Disconnect OnNewGameStarted.then -> RegisterSkill")

        # Step 2: Connect OnNewGameStarted.then -> CreateSaveGameObject.execute
        r = monolith("blueprint_query", {
            "action": "connect_pins",
            "asset_path": BP_PATH,
            "graph_name": "EventGraph",
            "source_node_id": "K2Node_CustomEvent_2",
            "source_pin_name": "then",
            "target_node_id": "K2Node_CallFunction_1",
            "target_pin_name": "execute"
        })
        check(r, "Connect OnNewGameStarted.then -> CreateSaveGameObject")

        # Step 3: Disconnect Array_Add.then -> UToolMenus::Get
        r = monolith("blueprint_query", {
            "action": "disconnect_pins",
            "asset_path": BP_PATH,
            "graph_name": "EventGraph",
            "source_node_id": "K2Node_CallArrayFunction_2",
            "source_pin_name": "then",
            "target_node_id": "K2Node_CallFunction_77",
            "target_pin_name": "execute"
        })
        check(r, "Disconnect Array_Add.then -> UToolMenus::Get")

        # Remove the UToolMenus node
        r = monolith("blueprint_query", {
            "action": "remove_node",
            "asset_path": BP_PATH,
            "graph_name": "EventGraph",
            "node_id": "K2Node_CallFunction_77"
        })
        check(r, "Remove UToolMenus::Get node")

        # Step 4: Connect Set shouldLoadGame_0.then -> RegisterSkill[0].execute
        r = monolith("blueprint_query", {
            "action": "connect_pins",
            "asset_path": BP_PATH,
            "graph_name": "EventGraph",
            "source_node_id": "K2Node_VariableSet_9",
            "source_pin_name": "then",
            "target_node_id": "K2Node_CallFunction_46",
            "target_pin_name": "execute"
        })
        check(r, "Connect Set shouldLoadGame_0.then -> RegisterSkill[0].execute")

        # Step 5: Compile
        r = monolith("blueprint_query", {
            "action": "compile_blueprint",
            "asset_path": BP_PATH
        })
        check(r, "Compile BP_MelodiaJRPGGameInstance")

        # Check compile result
        try:
            parsed = json.loads(r) if r else {}
            if isinstance(parsed, dict):
                errors = parsed.get("error_count", parsed.get("errors", "unknown"))
                print(f"  Compile result errors: {errors}")
        except (json.JSONDecodeError, TypeError):
            print(f"  Compile raw: {r[:300]}")

        print("\nDefect 1 fix applied.")
    finally:
        proxy.stdin.close()
        proxy.wait(timeout=5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
