#!/usr/bin/env python
"""Portfolio Dashboard Generator - Live HTML dashboard for agent monitoring."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_MEMORY_DIR = PROJECT_ROOT / "Saved" / "AgentMemory"
OUTPUT_DIR = PROJECT_ROOT / "my-site-clean" / "wix"


def get_agent_status() -> dict:
    loop_files = {
        "geometry": PROJECT_ROOT / "deploy" / "SURREAL_ARCH_LOOP_STOP",
        "material": PROJECT_ROOT / "deploy" / "MATERIAL_AAA_LOOP.pid",
        "placement": PROJECT_ROOT / "deploy" / "SDF_FACTORY_LOOP.pid",
        "integration": PROJECT_ROOT / "deploy" / "SURREAL_WORLD_LOOP_STOP",
        "qa": PROJECT_ROOT / "Saved" / "Audit" / "hermes_health.json",
    }
    icons = {
        "geometry": "[GEO]", "material": "[MAT]", "placement": "[PLC]",
        "integration": "[INT]", "qa": "[QA]",
    }
    status = {}
    for agent, loop_stop in loop_files.items():
        if loop_stop.exists():
            status[agent] = {"status": "stopped", "icon": icons.get(agent, "[?]")}
            if agent == "qa":
                try:
                    health = json.loads(loop_stop.read_text())
                    status[agent]["blessings"] = health.get("blessings", {}).get("blessings_count", 0)
                except Exception:
                    status[agent]["blessings"] = "?"
        else:
            status[agent] = {"status": "ready", "icon": icons.get(agent, "[?]")}
    return status


def get_pending_evolutions() -> list:
    queue_file = AGENT_MEMORY_DIR / "blessing_evolution_queue.json"
    if queue_file.exists():
        try:
            return json.loads(queue_file.read_text())
        except Exception:
            pass
    return []


def get_recent_evolution_log() -> list:
    log_file = AGENT_MEMORY_DIR / "blessing_evolution_log.json"
    if log_file.exists():
        try:
            log = json.loads(log_file.read_text())
            return log[-10:]
        except Exception:
            pass
    return []


def generate_dashboard_html() -> str:
    agents = get_agent_status()
    pending = get_pending_evolutions()
    evolution_log = get_recent_evolution_log()
    
    agent_cards = ""
    for agent, data in agents.items():
        status_color = "#4ade80" if data["status"] == "ready" else "#f87171"
        blessings_html = '<div class="badge">{} blessings</div>'.format(data["blessings"]) if "blessings" in data else ""
        agent_cards += '''
        <div class="agent-card" style="border-color: {}">
            <div class="agent-icon">{}</div>
            <div class="agent-name">{} Agent</div>
            <div class="status-badge" style="background: {}">{}</div>
            {}
        </div>'''.format(status_color, data['icon'], agent.title(), status_color, data['status'], blessings_html)
    
    pending_html = ""
    for req in pending:
        pending_html += '''
        <div class="pending-item">
            <code>{} blessings</code> 
            focused on <strong>{}</strong>
            <span class="time">{}</span>
        </div>'''.format(req.get('target_count', 5), req.get('element_focus', 'all'), req.get('timestamp', ''))
    
    evolution_html = ""
    for entry in evolution_log:
        req = entry.get('request', {})
        blessings = entry.get('blessings', [])
        evolution_html += '''
        <div class="evolution-item">
            <div>{} blessings generated for {}</div>
            <small>{}</small>
        </div>'''.format(len(blessings), req.get('element_focus', 'all'), entry.get('timestamp', ''))
    
    # CSS without format conflicts - using string concatenation
    css = '''
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #e4e4e4; min-height: 100vh; margin: 0; padding: 20px; }
        .dashboard { max-width: 1200px; margin: 0 auto; }
        h1 { color: #7ddfbd; border-bottom: 2px solid #4a4a6a; padding-bottom: 10px; }
        .section { background: #16213e; border-radius: 12px; padding: 20px; margin: 20px 0; }
        .agents-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .agent-card { background: #1a1a2e; border: 2px solid; border-radius: 8px; padding: 15px; text-align: center; }
        .agent-icon { font-size: 2em; margin-bottom: 10px; }
        .agent-name { font-weight: bold; margin-bottom: 8px; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.85em; display: inline-block; }
        .badge { background: #4a4a6a; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-top: 8px; display: inline-block; }
        .pending-list, .evolution-list { margin-top: 10px; }
        .pending-item, .evolution-item { background: #1a1a2e; padding: 10px; border-radius: 6px; margin: 5px 0; }
        .time { color: #888; font-size: 0.85em; margin-left: 10px; }
        code { background: #4a4a6a; padding: 2px 6px; border-radius: 4px; }
        small { color: #888; }
    </style>'''
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Bridge Dashboard - Melodia Environment</title>''' + css + '''
</head>
<body>
    <div class="dashboard">
        <h1>[Agents] Agent Bridge Dashboard</h1>
        <p>Live monitoring of Melodia Environment agents</p>
        
        <div class="section">
            <h2>Agent Status</h2>
            <div class="agents-grid">
                ''' + agent_cards + '''
            </div>
        </div>
        
        <div class="section">
            <h2>Pending Blessing Evolutions</h2>
            <div class="pending-list">
                ''' + (pending_html if pending_html else '<p>No pending evolutions</p>') + '''
            </div>
        </div>
        
        <div class="section">
            <h2>Recent Evolution History</h2>
            <div class="evolution-list">
                ''' + (evolution_html if evolution_html else '<p>No evolutions yet</p>') + '''
            </div>
        </div>
        
        <footer style="text-align: center; color: #666; margin-top: 30px;">
            Generated: ''' + timestamp + ''' | 
            <a href="https://github.com/fromage3900/environment-portfolio">BS_GodFile</a>
        </footer>
    </div>
</body>
</html>'''
    
    return html


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    html = generate_dashboard_html()
    output_file = OUTPUT_DIR / "agent-dashboard.html"
    output_file.write_text(html, encoding='utf-8')
    
    json_file = AGENT_MEMORY_DIR / "dashboard_data.json"
    data = {
        "timestamp": datetime.now().isoformat(),
        "agents": get_agent_status(),
        "pending_evolutions": get_pending_evolutions(),
        "recent_evolutions": get_recent_evolution_log(),
    }
    json_file.write_text(json.dumps(data, indent=2))
    
    print("Dashboard generated: {}".format(output_file))
    print("Data JSON: {}".format(json_file))


if __name__ == "__main__":
    main()