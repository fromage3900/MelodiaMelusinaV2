#!/usr/bin/env python3
"""
Enhanced Live Gameplay Metrics Dashboard for PIE.
Polls Monolith (localhost:9316) for live UE character state, log markers, and
server health, then generates a self-contained HTML file with animated beat
circle, live log feed, loop flow diagram, session counter, and collapsible
per-system details.

Usage:
    python Tools/metrics_dashboard.py              # Single snapshot
    python Tools/metrics_dashboard.py --watch      # Regenerate every 2s
    python Tools/metrics_dashboard.py --open       # Open in browser after write
"""

import json, os, sys, time, urllib.request, webbrowser
from pathlib import Path
from datetime import datetime

MONOLITH = "http://127.0.0.1:9316/mcp"
OUT_PATH  = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/metrics_dashboard.html")
PIE_CLASS = "BP_MelodiaJRPGGameInstance"
LOG_MARKER = "MELUSINA_LOOP"
LOG_MARKER_PROBE = "MELUSINA_LOOP_PROBE"

# ── Monolith RPC ──────────────────────────────────────────────────────

def monolith(action, args=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": action, "arguments": args or {}}}
    try:
        req = urllib.request.Request(MONOLITH, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode())
    except Exception:
        return {}

# ── Data collectors ───────────────────────────────────────────────────

def get_health():
    r = monolith("monolith_status", {})
    if isinstance(r, dict) and r.get("result", {}).get("content"):
        try:
            s = json.loads(r["result"]["content"][0]["text"])
            return s
        except:
            pass
    return {"server_running": False, "pid": "?", "version": "?",
            "uptime_seconds": 0, "start_time": ""}

def get_logs():
    r = monolith("editor_query", {"action": "tail_log", "count": 80})
    if isinstance(r, dict) and r.get("result", {}).get("content"):
        try:
            return json.loads(r["result"]["content"][0]["text"])
        except:
            pass
    return []

def get_pie_props():
    r = monolith("pie_get_object_properties", {
        "class_name": PIE_CLASS,
        "properties": [
            "GroundSpeed",
            "bShouldMove",
            "CurrentAnimationState",
            "AnimationBlendingWeight",
            "CharacterActionState",
            "SessionElapsedSeconds"
        ]
    })
    if isinstance(r, dict) and r.get("result", {}).get("content"):
        try:
            return json.loads(r["result"]["content"][0]["text"])
        except:
            pass
    return {}

# ── Helpers ───────────────────────────────────────────────────────────

def extract_log_markers(lines):
    markers = []
    if isinstance(lines, list):
        for line in lines:
            if LOG_MARKER in str(line) or LOG_MARKER_PROBE in str(line):
                markers.append(str(line))
    return markers[-30:]  # keep last 30

def derive_loop_step(markers):
    """Return which step of the persona-lite loop is currently highlighted."""
    combined = "\n".join(markers)
    if "Save" in combined or "save_complete" in combined:
        return 5
    if "Travel" in combined or "KaleidoNave" in combined:
        return 4
    if "Result" in combined or "victory" in combined or "defeat" in combined:
        return 3
    if "Battle" in combined or "StartSession" in combined:
        return 2
    if "Quill" in combined or "dialogue" in combined or "QuillScript" in combined:
        return 1
    return 0  # New Game / idle

def session_duration(health):
    s = health.get("uptime_seconds", 0)
    if not isinstance(s, (int, float)):
        return "0s"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {sec}s"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"

# ── HTML Generator ─────────────────────────────────────────────────────

def generate_html(health, props, log_markers, step_idx):
    server_up = bool(health.get("server_running", False))
    uptime = health.get("uptime_seconds", 0)
    beat_delay = -(uptime % 2) / 2  # cycle every 2s, synced to uptime
    session = session_duration(health)
    now = datetime.now().strftime("%H:%M:%S")

    gs = props.get("GroundSpeed", "?")
    bsm = props.get("bShouldMove", "?")
    anim = props.get("CurrentAnimationState", "?")
    blend = props.get("AnimationBlendingWeight", "?")
    action = props.get("CharacterActionState", "?")

    log_rows = ""
    for line in log_markers:
        safe = json.dumps(line)[1:-1]
        log_rows += f"<div>[MELUSINA_LOOP] {safe}</div>"

    steps = ["New Game", "Quill Dialogue", "Battle", "Result", "KaleidoNave", "Save"]
    step_icons = ["\U0001f5fa", "\U0001f4ac", "\u2694\ufe0f", "\U0001f3c6", "\U0001f30c", "\U0001f4be"]
    flow = ""
    for i, (s, ico) in enumerate(zip(steps, step_icons)):
        cls = "active" if i == step_idx else "waiting"
        flow += f'<span class="step {cls}">{ico} {s}</span>'
        if i < len(steps) - 1:
            flow += '<span class="arrow">\u2192</span>'

    # Collapsible system details
    details_blocks = """
    <details>
      <summary>\u2694\ufe0f Battle System</summary>
      <div class="detail-content">
        <div class="stat-row">
          <span class="stat-label">Encounter ID</span>
          <span class="stat-value">melodia_smoke_encounter</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Pipeline</span>
          <span class="stat-value">StartSession \u2192 SubmitRatedInput \u2192 ConsumePendingRequest</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Shards</span>
          <span class="stat-value">TryGrantShards(Forte)</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Highway</span>
          <span class="stat-value">WBP_MelodiaRhythmHighway</span>
        </div>
      </div>
    </details>
    <details>
      <summary>\U0001f4ac Quill System</summary>
      <div class="detail-content">
        <div class="stat-row">
          <span class="stat-label">Interpreter</span>
          <span class="stat-value">QuillScriptInterpreter</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Notification Tokens</span>
          <span class="stat-value">melodia:battle, melodia:quest, melodia:flag, melodia:travel, melodia:reward</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Resume Gate</span>
          <span class="stat-value">Pending N seconds \u2192 auto-resume</span>
        </div>
      </div>
    </details>
    <details>
      <summary>\U0001f30c Travel System</summary>
      <div class="detail-content">
        <div class="stat-row">
          <span class="stat-label">Allowlisted Level</span>
          <span class="stat-value">KaleidoNave</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Travel Trigger</span>
          <span class="stat-value">melodia:travel:KaleidoNave</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Config</span>
          <span class="stat-value">DA_MelodiaIntegrationConfig</span>
        </div>
      </div>
    </details>
    <details>
      <summary>\U0001f4be Save System</summary>
      <div class="detail-content">
        <div class="stat-row">
          <span class="stat-label">Save Game Class</span>
          <span class="stat-value">BP_JRPGSaveGame</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Narrative Record</span>
          <span class="stat-value">melodiaNarrativeRecord field</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Save Policy</span>
          <span class="stat-value">On checkpoint + interval</span>
        </div>
      </div>
    </details>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="2">
<title>Melodia Live Metrics Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0b0a13;
    color: #f2d69e;
    margin: 0; padding: 20px;
  }}
  .header {{
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #38293b; padding-bottom: 15px; margin-bottom: 20px;
  }}
  .title {{ font-size: 26px; color: #78ebff; letter-spacing: 1px; }}
  .subtitle {{ font-size: 13px; color: #666; }}
  .meta {{ font-size: 12px; color: #555; text-align: right; }}

  .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .card {{
    background: #1a1520; border: 1px solid #38293b; border-radius: 8px; padding: 14px;
  }}
  .card h3 {{ margin: 0 0 8px 0; color: #78ebff; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}

  .stat-row {{ display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #15101a; font-size: 13px; }}
  .stat-label {{ color: #777; }}
  .stat-value {{ color: #f2d69e; font-weight: bold; }}
  .stat-value.good {{ color: #22c55e; }}
  .stat-value.bad  {{ color: #ef4444; }}

  /* ── Beat ring ─────────────────────────────────── */
  .beat-container {{ text-align: center; padding: 10px 0; }}
  .beat-ring {{
    width: 100px; height: 100px; border-radius: 50%;
    border: 3px solid #38293b; margin: 0 auto 8px;
    position: relative;
    background: radial-gradient(circle, rgba(120,235,255,0.06) 0%, transparent 70%);
  }}
  .beat-dot {{
    width: 18px; height: 18px; border-radius: 50%;
    background: #78ebff; position: absolute;
    top: 50%; left: 50%; margin: -9px 0 0 -9px;
    animation: beat 1s ease-in-out infinite;
    box-shadow: 0 0 20px rgba(120,235,255,0.4);
  }}
  @keyframes beat {{
    0%, 100% {{ transform: scale(1); opacity: 0.5; }}
    50% {{ transform: scale(1.2); opacity: 1; }}
  }}
  .beat-label {{ font-size: 11px; color: #555; }}

  /* ── Loop flow ─────────────────────────────────── */
  .loop-flow {{
    display: flex; align-items: center; justify-content: center;
    flex-wrap: wrap; gap: 6px; padding: 16px;
    background: #1a1520; border: 1px solid #38293b; border-radius: 8px;
    margin-bottom: 20px;
  }}
  .step {{
    padding: 6px 14px; border-radius: 16px; font-size: 12px; font-weight: bold;
    white-space: nowrap;
  }}
  .step.active {{ background: #22c55e33; border: 1px solid #22c55e; color: #22c55e; animation: pulse 1.5s ease-in-out infinite; }}
  .step.waiting {{ background: #1a1520; border: 1px solid #38293b; color: #555; }}
  .arrow {{ color: #444; font-size: 16px; }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 0.7; box-shadow: 0 0 4px rgba(34,197,94,0.2); }}
    50% {{ opacity: 1; box-shadow: 0 0 14px rgba(34,197,94,0.5); }}
  }}

  /* ── Log feed ──────────────────────────────────── */
  .log-feed {{
    font-size: 11px; background: #0b0a13; padding: 10px; border-radius: 4px;
    max-height: 180px; overflow-y: auto; color: #555;
    border: 1px solid #1a1520; margin-bottom: 20px;
  }}
  .log-feed div {{ padding: 1px 0; }}
  .log-feed .marker {{ color: #78ebff; }}

  /* ── Collapsible details ─────────────────────── */
  details {{
    background: #1a1520; border: 1px solid #38293b; border-radius: 6px;
    margin-bottom: 8px; padding: 10px 14px;
  }}
  summary {{
    cursor: pointer; color: #78ebff; font-weight: bold; font-size: 13px;
    letter-spacing: 0.5px;
  }}
  .detail-content {{ padding-top: 10px; }}

  .footer {{ text-align: center; color: #444; font-size: 11px; margin-top: 20px; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="title">\U0001f3b5 Melodia Live Metrics</div>
    <div class="subtitle">Gameplay Loop Dashboard &middot; PIE Telemetry</div>
  </div>
  <div class="meta">Updated {now} &middot; PID {health.get("pid","?")} &middot; v{health.get("version","?")}</div>
</div>

<div class="loop-flow">{flow}</div>

<div class="grid">

  <div class="card">
    <h3>\U0001f3b5 Beat Engine</h3>
    <div class="beat-container">
      <div class="beat-ring" style="animation-delay: {beat_delay}s;">
        <div class="beat-dot" style="animation-delay: {beat_delay}s;"></div>
      </div>
      <div class="beat-label">Uptime: {session}</div>
    </div>
    <div class="stat-row">
      <span class="stat-label">Server</span>
      <span class="stat-value {'good' if server_up else 'bad'}">{'UP' if server_up else 'DOWN'}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Session</span>
      <span class="stat-value good">PIE Active</span>
    </div>
  </div>

  <div class="card">
    <h3>\U0001f3c3 Character Stats</h3>
    <div class="stat-row">
      <span class="stat-label">GroundSpeed</span>
      <span class="stat-value">{gs}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">bShouldMove</span>
      <span class="stat-value {'good' if str(bsm)=='True' else 'bad' if str(bsm)=='False' else ''}">{bsm}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Animation State</span>
      <span class="stat-value">{anim}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Blending Weight</span>
      <span class="stat-value">{blend}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Action State</span>
      <span class="stat-value">{action}</span>
    </div>
  </div>

  <div class="card">
    <h3>\U0001f4ca Session Info</h3>
    <div class="stat-row">
      <span class="stat-label">PIE Uptime</span>
      <span class="stat-value good">{session}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Loop Phase</span>
      <span class="stat-value">{steps[step_idx]}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Markers Captured</span>
      <span class="stat-value">{len(log_markers)}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Poll Interval</span>
      <span class="stat-value">2s</span>
    </div>
  </div>

</div>

<div class="card" style="margin-bottom:16px;">
  <h3>\U0001f4dd Live Log Feed — MELUSINA_LOOP Markers</h3>
  <div class="log-feed">{log_rows}</div>
</div>

{details_blocks}

<div class="footer">
  Auto-refreshes every 2s &middot; <a href="#" onclick="location.reload()" style="color:#78ebff;">Refresh now</a>
  &middot; Generated by metrics_dashboard.py
</div>

</body>
</html>"""
    return html

# ── Main ────────────────────────────────────────────────────────────────

def generate():
    health = get_health()
    lines = get_logs()
    props = get_pie_props()
    markers = extract_log_markers(lines)
    step = derive_loop_step(markers)
    html = generate_html(health, props, markers, step)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    return html

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced Live Gameplay Metrics Dashboard")
    parser.add_argument("--watch", action="store_true", help="Regenerate every 2s")
    parser.add_argument("--open", action="store_true", help="Open in browser")
    args = parser.parse_args()

    if args.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                generate()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard refreshed: {OUT_PATH}")
                if args.open and not hasattr(main, "_opened"):
                    webbrowser.open(str(OUT_PATH))
                    main._opened = True
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        generate()
        print(f"Dashboard: {OUT_PATH}")
        if args.open:
            webbrowser.open(str(OUT_PATH))

if __name__ == "__main__":
    main()
