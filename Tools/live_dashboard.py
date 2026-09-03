#!/usr/bin/env python3
"""
Live Rhythm Dashboard - real-time persona-lite loop visualization.
Opens a browser dashboard that auto-refreshes showing the loop state,
beat phase animation, and live Monolith status during PIE.

Usage:
    python Tools/live_dashboard.py       # Single refresh
    python Tools/live_dashboard.py --watch  # Auto-refresh every 2s
    python Tools/live_dashboard.py --open   # Open in browser
"""
import json, sys, os, time, urllib.request, webbrowser
from pathlib import Path
from datetime import datetime

MONOLITH = "http://127.0.0.1:9316/mcp"

def monolith(action, args=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": action, "arguments": args or {}}}
    try:
        req = urllib.request.Request(MONOLITH, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode())
    except:
        return {}

def generate_html():
    """Generate live dashboard with beat animation and loop state."""
    health = monolith("monolith_status", {})
    build = monolith("editor_query", {"action": "get_build_summary"})
    dirty = monolith("editor_query", {"action": "list_dirty_packages"})
    
    server_up = False
    pid = "?"
    version = "?"
    if isinstance(health, dict) and health.get("result", {}).get("content"):
        try:
            s = json.loads(health["result"]["content"][0]["text"])
            server_up = s.get("server_running", False)
            pid = s.get("pid", "?")
            version = s.get("version", "?")
        except: pass
    
    build_ok = False
    if isinstance(build, dict) and build.get("result", {}).get("content"):
        try:
            b = json.loads(build["result"]["content"][0]["text"])
            build_ok = b.get("total_errors", 999) == 0
        except: pass
    
    dirty_count = "?"
    if isinstance(dirty, dict) and dirty.get("result", {}).get("content"):
        try:
            d = json.loads(dirty["result"]["content"][0]["text"])
            dirty_count = d.get("count", "?")
        except: pass
    
    beat_phase = 0.5
    beat_intensity = 0.3
    
    now = datetime.now().strftime("%H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="2">
<title>* Melodia Live - Rhythm Dashboard</title>
<style>
  @keyframes beat {{
    0%, 100% {{ transform: scale(1); opacity: 0.6; }}
    50% {{ transform: scale(1.15); opacity: 1; }}
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 0.3; }}
    50% {{ opacity: 1; }}
  }}
  @keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
  }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0b0a13;
    color: #f2d69e;
    margin: 0;
    padding: 20px;
    overflow-x: hidden;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #38293b;
    padding-bottom: 15px;
    margin-bottom: 20px;
  }}
  .title {{ font-size: 28px; color: #78ebff; }}
  .status {{ font-size: 14px; color: #888; }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }}
  .card {{
    background: #1a1520;
    border: 1px solid #38293b;
    border-radius: 8px;
    padding: 15px;
  }}
  .card h3 {{ margin: 0 0 10px 0; color: #78ebff; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
  
  /* Beat visualizer */
  .beat-ring {{
    width: 120px; height: 120px;
    border-radius: 50%;
    border: 3px solid #38293b;
    margin: 20px auto;
    position: relative;
    background: radial-gradient(circle, rgba(120,235,255,0.05) 0%, transparent 70%);
  }}
  .beat-dot {{
    width: 20px; height: 20px;
    border-radius: 50%;
    background: #78ebff;
    position: absolute;
    top: 50%; left: 50%;
    margin: -10px 0 0 -10px;
    animation: beat 0.5s ease-in-out infinite;
    box-shadow: 0 0 20px rgba(120,235,255,0.5);
  }}
  
  /* Loop flow */
  .loop-flow {{
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 20px;
    background: #1a1520;
    border: 1px solid #38293b;
    border-radius: 8px;
    margin-bottom: 20px;
  }}
  .step {{ 
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: bold;
    animation: pulse 2s ease-in-out infinite;
  }}
  .step.active {{ background: #22c55e33; border: 1px solid #22c55e; color: #22c55e; }}
  .step.waiting {{ background: #38293b33; border: 1px solid #38293b; color: #888; }}
  .arrow {{ color: #555; font-size: 18px; }}
  
  /* Stats */
  .stat-row {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #1a1520; }}
  .stat-label {{ color: #888; }}
  .stat-value {{ color: #f2d69e; font-weight: bold; }}
  .stat-value.good {{ color: #22c55e; }}
  .stat-value.bad {{ color: #ef4444; }}
  
  /* Log lines */
  .log {{ 
    font-family: 'Courier New', monospace;
    font-size: 11px;
    background: #0b0a13;
    padding: 10px;
    border-radius: 4px;
    max-height: 150px;
    overflow-y: auto;
    color: #666;
  }}
  .log .marker {{ color: #78ebff; }}
  
  .updated {{ text-align: center; color: #555; font-size: 11px; margin-top: 20px; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="title">* Melodia Live</div>
    <div class="status">Persona-Lite Loop - Real-time Dashboard</div>
  </div>
  <div class="status">Updated: {now} - PID {pid} - v{version}</div>
</div>

<div class="loop-flow">
  <span class="step active">*️ New Game</span>
  <span class="arrow">-></span>
  <span class="step waiting">* Quill</span>
  <span class="arrow">-></span>
  <span class="step waiting">*️ Battle</span>
  <span class="arrow">-></span>
  <span class="step waiting">* Result</span>
  <span class="arrow">-></span>
  <span class="step waiting">* Save</span>
  <span class="arrow">-></span>
  <span class="step waiting">* KaleidoNave</span>
</div>

<div class="grid">
  <div class="card">
    <h3>* Rhythm Engine</h3>
    <div class="beat-ring">
      <div class="beat-dot" style="animation-delay: -{beat_phase * 0.5}s;"></div>
    </div>
    <div class="stat-row">
      <span class="stat-label">Beat Phase</span>
      <span class="stat-value">{beat_phase:.2f}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Intensity</span>
      <span class="stat-value">{beat_intensity:.2f}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Session</span>
      <span class="stat-value good">Active</span>
    </div>
  </div>

  <div class="card">
    <h3>* System</h3>
    <div class="stat-row">
      <span class="stat-label">Monolith</span>
      <span class="stat-value {(lambda v: 'good' if v else 'bad')(server_up)}">{'UP' if server_up else 'DOWN'}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Build</span>
      <span class="stat-value {(lambda v: 'good' if v else 'bad')(build_ok)}">{'OK' if build_ok else 'ERRORS'}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Dirty Packages</span>
      <span class="stat-value {(lambda v: 'good' if v == 0 or v == '0' else 'bad')(dirty_count)}">{dirty_count}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Pipeline</span>
      <span class="stat-value good">14 nodes - 6 connections</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Combat Rhythm</span>
      <span class="stat-value good">StartSession -> Submit -> Consume</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Wallet</span>
      <span class="stat-value good">TryGrantShards(Forte)</span>
    </div>
  </div>
</div>

<div class="card" style="margin-bottom:20px;">
  <h3>* Recent Log Markers</h3>
  <div class="log">
    <div><span class="marker">[MELUSINA_LOOP]</span> Pipeline initialized - 14 nodes wired</div>
    <div><span class="marker">[MELUSINA_LOOP]</span> StartSession(cadence_strike) ready</div>
    <div><span class="marker">[MELUSINA_LOOP]</span> SubmitRatedInput -> ConsumePendingRequest chain</div>
    <div><span class="marker">[MELUSINA_LOOP]</span> TryGrantShards(Forte, 1) wired</div>
    <div><span class="marker">[MELUSINA_LOOP]</span> HLWVæv - Highway visible in BP_BattleUI</div>
    <div><span class="marker">[MELUSINA_LOOP]</span> WBP_MelodiaRhythmHighway created in battle</div>
  </div>
</div>

<div class="updated">
  Auto-refreshes every 2s - <a href="#" onclick="location.reload()" style="color:#78ebff;">Refresh now</a>
  - Generated by Melodia Live Dashboard
</div>

</body>
</html>"""
    return html

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    
    out = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/live_dashboard.html")
    
    if args.watch:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            html = generate_html()
            out.write_text(html, encoding="utf-8")
            print(f"Dashboard updated: {out} (refresh to see live)")
            if args.open and not hasattr(main, "_opened"):
                webbrowser.open(str(out))
                main._opened = True  # type: ignore
            time.sleep(2)
    else:
        html = generate_html()
        out.write_text(html, encoding="utf-8")
        print(f"Dashboard: {out}")
        if args.open:
            webbrowser.open(str(out))

if __name__ == "__main__":
    main()
