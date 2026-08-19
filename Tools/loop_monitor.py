#!/usr/bin/env python3
"""
Melodia Gameplay Loop Monitor — live status dashboard for the persona-lite loop.
Shows what's connected, what's firing, and where it's breaking.

Usage:
    python Tools/loop_monitor.py          # Quick check
    python Tools/loop_monitor.py --watch  # Live-update every 2 seconds
    python Tools/loop_monitor.py --html   # Generate HTML dashboard
"""
import json, sys, os, time, subprocess, webbrowser
from pathlib import Path
from datetime import datetime

MONOLITH = "http://127.0.0.1:9316/mcp"

def monolith(action, args=None):
    import urllib.request
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": action, "arguments": args or {}}}
    try:
        req = urllib.request.Request(MONOLITH, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def check_step(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    return f"{icon} {name}" + (f" — {detail}" if detail else "")

def scan_bp(asset_path):
    """Scan a Blueprint for function call nodes by keyword. Return raw text for regex search."""
    data = monolith("blueprint_query", {"action": "export_graph", "asset_path": asset_path})
    if isinstance(data, dict) and "error" in data:
        return str(data)
    if isinstance(data, dict) and data.get("result", {}).get("content"):
        return data["result"]["content"][0].get("text", "")
    return str(data)

def has_function(graph_text, keyword):
    """Check if a graph text contains a specific function call via regex."""
    import re
    match = re.search(keyword, graph_text, re.IGNORECASE)
    if match:
        # Try to find the node ID nearby
        start = max(0, match.start() - 200)
        snippet = graph_text[start:match.end() + 50]
        return True, snippet[:80]
    return False, None

def check_loop():
    """Check every step of the persona-lite loop."""
    results = []
    
    # 1. Editor status
    health = monolith("monolith_status", {})
    if isinstance(health, dict) and health.get("result", {}).get("content"):
        status = json.loads(health["result"]["content"][0].get("text", "{}"))
        up = status.get("server_running", False)
        results.append(check_step("Monolith server", up, f"v{status.get('version','?')}"))
    else:
        results.append(check_step("Monolith server", False, "DOWN"))
    
    # 2. Dirty packages
    dirty = monolith("editor_query", {"action": "list_dirty_packages"})
    if isinstance(dirty, dict) and dirty.get("result", {}).get("content"):
        dirty_text = dirty["result"]["content"][0].get("text", "{}")
        try:
            dirty_data = json.loads(dirty_text)
            count = dirty_data.get("count", 0) if isinstance(dirty_data, dict) else 0
            results.append(check_step("No dirty packages", count == 0, f"{count} dirty" if count else ""))
        except:
            results.append(check_step("No dirty packages", False))
    
    # 3. BP Errors
    errors = monolith("editor_query", {"action": "list_errored_blueprints"})
    if isinstance(errors, dict) and errors.get("result", {}).get("content"):
        err_text = errors["result"]["content"][0].get("text", "{}")
        try:
            err_data = json.loads(err_text)
            count = err_data.get("count", 0)
            results.append(check_step("Zero BP errors", count == 0, f"{count} errors" if count else ""))
        except:
            results.append(check_step("Zero BP errors", False))
    
    # 4. Scan key Blueprints
    bps = {
        "Battle→Narrative (CompleteBattle)": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "RegisterSkill": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
        "StartSession": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "RecordInputNow": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "ConsumePendingRequest": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "TryGrantShards": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "MelodiaNoteHighway": "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    }
    
    # Cache graph data
    graphs = {}
    for name, path in bps.items():
        if path not in graphs:
            graphs[path] = scan_bp(path)
    
    # Check each
    for name, path in bps.items():
        graph = graphs.get(path, {})
        found, nid = has_function(graph, name.split("(")[0].strip())
        results.append(check_step(name, found, f"node: {nid}" if found else "MISSING"))
    
    # 5. Config check
    config = monolith("project_query", {"action": "get_asset_details", 
                                         "asset_path": "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"})
    if isinstance(config, dict) and config.get("result", {}).get("content"):
        config_text = config["result"]["content"][0].get("text", "")
        has_encounter = "melodia_smoke_encounter" in config_text
        has_travel = "KaleidoNave" in config_text
        results.append(check_step("Config: smoke encounter allowlisted", has_encounter))
        results.append(check_step("Config: KaleidoNave allowlisted", has_travel))
    
    # 6. Tag check — does the BP_InteractionBattle CDO have the tag?
    tag_check = monolith("blueprint_query", {"action": "get_cdo_properties",
                                              "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle"})
    if isinstance(tag_check, dict) and tag_check.get("result", {}).get("content"):
        tag_text = tag_check["result"]["content"][0].get("text", "")
        has_tag = "melodia_smoke_encounter" in tag_text
        results.append(check_step("BP_InteractionBattle has smoke tag", has_tag))
    
    # 7. Build status
    build = monolith("editor_query", {"action": "get_build_summary"})
    if isinstance(build, dict) and build.get("result", {}).get("content"):
        build_text = build["result"]["content"][0].get("text", "")
        try:
            build_data = json.loads(build_text)
            err_count = build_data.get("total_errors", 0)
            results.append(check_step("Build: zero errors", err_count == 0, f"{err_count} errors" if err_count else ""))
        except:
            results.append(check_step("Build: zero errors", False))
    
    return results

def display_results(results):
    """Display results as a formatted terminal dashboard."""
    total = len(results)
    passed = sum(1 for r in results if r.startswith("✅"))
    failed = total - passed
    
    print("\n" + "=" * 60)
    print("  Melodia Gameplay Loop Monitor")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for r in results:
        print(f"  {r}")
    
    print("=" * 60)
    pct = (passed / total * 100) if total > 0 else 0
    print(f"  {passed}/{total} connected ({pct:.0f}%)")
    
    if failed > 0:
        print("\n  ❗  Missing connections detected — the loop WILL break here:")
        for r in results:
            if r.startswith("❌"):
                name = r.split("—")[0].replace("❌ ", "").strip()
                print(f"     • {name}")
        print()
    
    return passed == total


def generate_html(results):
    """Generate a self-contained HTML dashboard."""
    passed = sum(1 for r in results if r.startswith("✅"))
    total = len(results)
    pct = (passed / total * 100) if total > 0 else 0
    
    rows_html = ""
    for r in results:
        icon = "✅" if r.startswith("✅") else "❌"
        name = r.split("—")[0].replace("✅ ", "").replace("❌ ", "").strip()
        detail = r.split("—")[-1].strip() if "—" in r else ""
        color = "#22c55e" if icon == "✅" else "#ef4444"
        rows_html += f"""
        <tr>
            <td style="font-size:24px">{icon}</td>
            <td style="padding:8px">{name}</td>
            <td style="color:{color}">{detail}</td>
        </tr>"""
    
    color = "#22c55e" if pct >= 80 else "#eab308" if pct >= 50 else "#ef4444"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Melodia Loop Monitor</title>
<style>
  body {{ font-family: 'Courier New', monospace; background: #0b0a13; color: #f2d69e; margin:0; padding:20px; }}
  h1 {{ color: #78ebff; font-size: 28px; margin-bottom: 5px; }}
  .sub {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; padding: 8px; color: #78ebff; border-bottom: 1px solid #38293b; }}
  td {{ padding: 8px; border-bottom: 1px solid #1a1520; }}
  .stat {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
  .loop-diagram {{ 
    background: #1a1520; border: 1px solid #38293b; border-radius: 8px; 
    padding: 20px; margin: 20px 0; text-align: center; font-size: 18px;
  }}
  .step {{ display: inline-block; padding: 8px 16px; margin: 4px; border-radius: 4px; }}
  .connected {{ background: #22c55e33; border: 1px solid #22c55e; }}
  .missing {{ background: #ef444433; border: 1px solid #ef4444; }}
  .arrow {{ color: #555; margin: 0 8px; }}
</style>
</head>
<body>
<h1>♫ Melodia — Persona-Lite Loop Monitor</h1>
<div class="sub">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · <span class="stat" style="background:{color}22;color:{color}">{passed}/{total} connected ({pct:.0f}%)</span></div>

<div class="loop-diagram">
  <span class="step {'connected' if 'CompleteBattle' in str(results) else 'missing'}">New Game</span>
  <span class="arrow">→</span>
  <span class="step">Quill Dialogue</span>
  <span class="arrow">→</span>
  <span class="step">Battle Intent</span>
  <span class="arrow">→</span>
  <span class="step {'connected' if 'CompleteBattle' in str(results) else 'missing'}">Battle</span>
  <span class="arrow">→</span>
  <span class="step">CompleteBattle</span>
  <span class="arrow">→</span>
  <span class="step">Quill Resume</span>
  <span class="arrow">→</span>
  <span class="step">KaleidoNave</span>
</div>

<table>
<tr><th></th><th>Connection</th><th>Status</th></tr>
{rows_html}
</table>

<p style="color:#555;margin-top:20px;font-size:12px">
  Auto-refresh: <button onclick="location.reload()">Refresh</button>
  · Generated by Melodia Loop Monitor
</p>
</body>
</html>"""
    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Melodia Gameplay Loop Monitor")
    parser.add_argument("--watch", action="store_true", help="Live-update every 2 seconds")
    parser.add_argument("--html", action="store_true", help="Generate HTML dashboard")
    parser.add_argument("--open", action="store_true", help="Open HTML dashboard in browser")
    args = parser.parse_args()
    
    if args.html or args.open:
        results = check_loop()
        html = generate_html(results)
        out_path = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/loop_monitor.html")
        out_path.write_text(html, encoding="utf-8")
        print(f"Dashboard written to: {out_path}")
        if args.open:
            webbrowser.open(str(out_path))
        return 0 if all(r.startswith("✅") for r in results) else 1
    
    if args.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                results = check_loop()
                display_results(results)
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
    else:
        results = check_loop()
        all_ok = display_results(results)
        return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
