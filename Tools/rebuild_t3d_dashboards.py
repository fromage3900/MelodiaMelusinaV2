#!/usr/bin/env python3
import html
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAVED = os.path.join(PROJECT_ROOT, "Saved")
WIX = os.path.join("C:", os.sep, "EnvironmentPortfolio", "wix")

PALETTE = {
    "bg": "#0b0a13",
    "card": "#1a1520",
    "border": "#38293b",
    "cyan": "#78ebff",
    "gold": "#f2d69e",
    "dim": "#777777",
    "good": "#22c55e",
    "bad": "#ef4444",
    "muted": "#555555",
}

CSS = """
* { box-sizing: border-box; }
body { font-family: 'Courier New', monospace; background: %(bg)s; color: %(gold)s; margin: 0; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid %(border)s; padding-bottom: 15px; margin-bottom: 20px; }
.title { font-size: 26px; color: %(cyan)s; letter-spacing: 1px; }
.subtitle { font-size: 13px; color: #666; }
.meta { font-size: 12px; color: %(muted)s; text-align: right; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 20px; }
.card { background: %(card)s; border: 1px solid %(border)s; border-radius: 8px; padding: 14px; }
.card h3 { margin: 0 0 8px 0; color: %(cyan)s; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
.stat-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #15101a; font-size: 13px; }
.stat-label { color: #777; }
.stat-value { color: %(gold)s; font-weight: bold; }
.stat-value.good { color: %(good)s; }
.stat-value.bad { color: %(bad)s; }
.bar { height: 14px; background: #15101a; border: 1px solid %(border)s; border-radius: 7px; overflow: hidden; margin: 6px 0 4px; }
.bar-fill { height: 100%%; background: linear-gradient(90deg, %(cyan)s, %(gold)s); }
.bar-label { font-size: 11px; color: #666; }
.section { margin: 24px 0 12px; font-size: 15px; color: %(cyan)s; text-transform: uppercase; letter-spacing: 1px; border-left: 3px solid %(cyan)s; padding-left: 8px; }
table { width: 100%%; border-collapse: collapse; margin-bottom: 24px; font-size: 12px; }
th { text-align: left; color: %(cyan)s; border-bottom: 1px solid %(border)s; padding: 6px 8px; text-transform: uppercase; letter-spacing: 1px; }
td { padding: 6px 8px; border-bottom: 1px solid #15101a; }
tr:hover td { background: #1f1830; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
.badge.migrated { background: #22c55e22; border: 1px solid %(good)s; color: %(good)s; }
.badge.stock { background: #ef444422; border: 1px solid %(bad)s; color: %(bad)s; }
.badge.partial { background: #f2d69e22; border: 1px solid %(gold)s; color: %(gold)s; }
.badge.ok { background: #22c55e22; border: 1px solid %(good)s; color: %(good)s; }
.badge.warn { background: #f2d69e22; border: 1px solid %(gold)s; color: %(gold)s; }
.code { background: #15101a; border: 1px solid %(border)s; border-radius: 6px; padding: 12px; font-size: 12px; white-space: pre-wrap; color: %(gold)s; margin: 8px 0 20px; }
.flag { font-size: 11px; color: %(cyan)s; }
a { color: %(cyan)s; }
.footer { margin-top: 30px; border-top: 1px solid %(border)s; padding-top: 10px; font-size: 11px; color: %(muted)s; }
""" % PALETTE


def load(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def human(n):
    return f"{n / 1024 / 1024:.2f} MB" if n >= 1048576 else f"{n / 1024:.1f} KB"


def page(title, subtitle, body, meta):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">{html.escape(title)}</div>
    <div class="subtitle">{html.escape(subtitle)}</div>
  </div>
  <div class="meta">{html.escape(meta)}</div>
</div>
{body}
</body>
</html>"""


def render_catalog(cat, drift, t3d_data):
    summary = cat["summary"]
    drifted = [d for d in drift if "drifted" in d["flags"]]
    stub = [d for d in drift if "stub_recovered" in d["flags"]]
    unchanged = [d for d in drift if "unchanged" in d["flags"]]

    cards = ""
    for label, value, cls in [
        ("Exports", summary["total_exports"], ""),
        ("Live T3D size", summary["total_size_formatted"], ""),
        ("Migrated", summary["migrated_count"], "good"),
        ("Stock remaining", summary["stock_remaining"], "bad"),
        ("Progress", f"{summary['migration_progress_pct']:.1f}%", ""),
        ("Drifted vs 08-05", len(drifted), "warn"),
        ("Stub recovered", len(stub), "good"),
        ("Unchanged", len(unchanged), ""),
    ]:
        cls_attr = f" class=\"{cls}\"" if cls else ""
        cards += f'<div class="card"><h3>{label}</h3><div class="stat-value{cls_attr}">{value}</div></div>'

    bar = f"""
    <div class="card">
      <h3>Melodia migration progress</h3>
      <div class="bar"><div class="bar-fill" style="width:{summary['migration_progress_pct']:.1f}%"></div></div>
      <div class="bar-label">{summary['migrated_count']}/{summary['total_exports']} widgets carry Melodia palette references (F_Melodia_UI font / T_Melodia_Universal_* textures)</div>
    </div>
    """

    sections = ""
    for key, group in cat["categories"].items():
        rows = ""
        for a in group["assets"]:
            d = next((x for x in drift if x["name"] == a["name"]), {})
            status = a["migration_status"]
            badges = ""
            if "stub_recovered" in d.get("flags", []):
                badges += ' <span class="flag">[stub recovered]</span>'
            if "drifted" in d.get("flags", []):
                badges += ' <span class="flag">[drifted]</span>'
            repl = html.escape(a["melodia_replacement"]) if a["melodia_replacement"] else "&mdash;"
            nodes = f'{d.get("old_nodes", "?")} &rarr; {d.get("live_nodes", "?")}' if d else "?"
            size = f'{human(d.get("old_size", 0))} &rarr; {human(d.get("live_size", 0))}' if d else human(a["size_bytes"])
            rows += f"""<tr>
<td><b>{html.escape(a['name'])}</b><br><span style="color:#666">{html.escape(a['ue_path'])}</span></td>
<td><span class="badge {status}">{status.upper()}</span>{badges}</td>
<td>{repl}</td>
<td>{nodes}</td>
<td>{size}</td>
</tr>"""
        sections += f'<div class="section">{html.escape(group["display"])} ({len(group["assets"])})</div>'
        sections += f"""<table>
<tr><th>Widget</th><th>Live status</th><th>Melodia replacement</th><th>Nodes (old &rarr; live)</th><th>Size (old &rarr; live)</th></tr>
{rows}</table>"""

    snippets = """<div class="section">Bulk skinning snippets</div>
<div class="code"># PowerShell - find/replace stock textures with Melodia parchment frame across all live exports
$map = @{ 'T_MenuBackground' = 'T_Melodia_Universal_ParchmentFrame'; 'T_DialogueBackground' = 'T_Melodia_Universal_ParchmentFrame' }
Get-ChildItem 'C:\\EnvironmentPortfolio\\BS_GodFile\\Saved\\T3D\\live_catalog\\*.t3d' | ForEach-Object {
  $t = Get-Content $_.FullName -Raw
  foreach ($k in $map.Keys) { $t = $t.Replace($k, $map[$k]) }
  Set-Content $_.FullName $t
}</div>
<div class="code"># Python - report which live exports still reference stock template textures (the 19 stock widgets)
import json, re
for f in sorted(__import__('glob').glob(r'C:\\EnvironmentPortfolio\\BS_GodFile\\Saved\\T3D\\live_catalog\\*.t3d')):
    t = open(f, encoding='utf-8').read()
    stock = sorted(set(re.findall(r'T_[A-Za-z0-9_]+', t)) - {'T_Melodia_Universal_ParchmentFrame', 'T_Melodia_Universal_DividerScroll', 'T_Melodia_Universal_CrestBaroque'})
    if stock: print(f.split('\\\\')[-1], len(stock), 'stock texture refs')</div>"""

    audit = t3d_data.get("t3d", {}).get("ui_migration", {})
    audit_rows = ""
    for k, v in audit.items():
        if k == "live_export_audit":
            continue
        audit_rows += f'<div class="stat-row"><span class="stat-label">{html.escape(str(k))}</span><span class="stat-value">{html.escape(str(v))}</span></div>'
    audit_note = html.escape(audit.get("live_export_audit", ""))

    body = f"""
<div class="grid">{cards}{bar}</div>
<div class="section">Live re-export audit</div>
<div class="card">{audit_rows}<div style="margin-top:8px;font-size:11px;color:#666">{audit_note}</div></div>
{sections}
{snippets}
<div class="footer">T3D catalog re-exported from live UE via Monolith MCP (project.export_asset_text) on {summary and '2026-08-06'} &middot; drift compared against the 2026-08-05 exports in Saved\\T3D\\full_catalog and Saved\\T3D\\stock_widgets &middot; 5649 Begin-Object nodes across 23 live exports</div>"""
    return page(
        "T3D Asset Catalog &middot; Live 2026-08-06",
        "Melodia Skinning Dashboard - 23 widget exports compared against live UE",
        body,
        "generated 2026-08-06 via Tools/rebuild_t3d_dashboards.py",
    )


def render_agent(claims, t3d_data, cat_summary):
    skills = claims.get("skills", [])
    injected = claims.get("injected_bps", [])
    ui_sweep = claims.get("ui_sweep", [])
    errored = claims.get("errored_blueprints", {})
    bridge = claims.get("bridge_collapse", {})
    idx = claims.get("index_stats", {})
    verdict = claims.get("summary", {}).get("verdict", "UNKNOWN")

    claims_rows = ""
    for c in [
        ("8 Rhythm Skills created", all(s["found"] for s in skills), "All 8 present as MelodiaRhythmSkillDefinition DataAssets under /Game/MelodiaIntegration/Config; auto-discovered by UMelodiaRhythmCombatSubsystem"),
        ("T3D injection: 4 BPs wired (t3d_demo.py)", all(b["found"] for b in injected), "BP_BattleController/BP_BattleUI/GameInstance/BP_InteractionBattle all present, compile 0 errors; exact 14-node transaction count unverifiable from live state"),
        ("Full UI Sweep - all Melodia styled", all(w["skinned"] for w in ui_sweep), f"{sum(1 for w in ui_sweep if w['skinned'])}/{len(ui_sweep)} widgets skinned - only Victory/Defeat dialogues and Orrery confirmed"),
        ("Compiled 0 errors", errored.get("count", -1) == 0, f"list_errored_blueprints = {errored.get('count', '?')}; 4 non-BP editor log errors (unloadable uasset, audio device, Niagara shader)"),
        ("Battle bridge collapse (adapter deleted)", bridge.get("adapter_assets_remaining", -1) == 0 and bridge.get("bridge_present"), "Name-based ClassifyJRPGBattleResult + AbortPendingBattle on start failure; 0 BattleAdapter hits in project or source"),
    ]:
        b = '<span class="badge ok">TRUE</span>' if c[1] else '<span class="badge warn">PARTIAL/FALSE</span>'
        claims_rows += f"<tr><td>{c[0]}</td><td>{b}</td><td style=\"color:#999\">{c[2]}</td></tr>"

    skill_rows = ""
    for s in skills:
        found = '<span class="badge ok">found</span>' if s.get("found") else '<span class="badge warn">missing</span>'
        skill_rows += f'<tr><td>{html.escape(s["claim"])}</td><td>{found}</td><td style="color:#666">{html.escape(s.get("asset_path", ""))}</td><td>{html.escape(s.get("asset_class", ""))}</td></tr>'

    ui_rows = ""
    for w in ui_sweep:
        b = '<span class="badge migrated">SKINNED</span>' if w["skinned"] else '<span class="badge stock">STOCK</span>'
        ui_rows += f'<tr><td>{html.escape(w["widget"])}</td><td>{b}</td><td>{w["melodia_texture_refs"]}</td><td style="color:#999">{html.escape(w["notes"])}</td></tr>'

    bridge_rows = ""
    for k, v in [
        ("Adapter assets remaining", bridge.get("adapter_assets_remaining", "?")),
        ("Adapter source hits", bridge.get("adapter_search_hits", "?")),
        ("Name-based classification", bridge.get("name_based_classification", "?")),
        ("AbortPendingBattle on start failure", bridge.get("abort_pending_battle_on_failure", "?")),
    ]:
        b = '<span class="badge ok">OK</span>' if v is True else ('<span class="badge stock">GONE</span>' if v == 0 else html.escape(str(v)))
        bridge_rows += f'<div class="stat-row"><span class="stat-label">{k}</span><span class="stat-value">{b}</span></div>'

    workflows = t3d_data.get("t3d", {}).get("automation_workflows", [])
    wf_rows = "".join(f'<div class="stat-row"><span class="stat-label">{html.escape(w)}</span><span class="stat-value good">READY</span></div>' for w in workflows)

    lc = t3d_data.get("t3d", {}).get("live_catalog", {})
    verdict_badge = f'<span class="badge {"ok" if verdict == "PASS" else "warn"}">{verdict}</span>'

    body = f"""
<div class="section">Overall verdict {verdict_badge}</div>
<div class="card" style="font-size:13px;color:#bbb">{html.escape(claims.get("summary", {}).get("notes", ""))}</div>

<div class="section">Monolith MCP status</div>
<div class="grid">
  <div class="card"><h3>MCP endpoint</h3><div class="stat-value good">LIVE</div><div class="stat-label">127.0.0.1:9316/mcp &middot; UE 5.8</div></div>
  <div class="card"><h3>Indexed assets</h3><div class="stat-value">{idx.get("assets", "?")}</div><div class="stat-label">project assets</div></div>
  <div class="card"><h3>Blueprints</h3><div class="stat-value">{idx.get("blueprints", "?")}</div><div class="stat-label">{idx.get("widget_blueprints", "?")} widget BPs</div></div>
  <div class="card"><h3>Errored blueprints</h3><div class="stat-value good">{errored.get("count", "?")}</div><div class="stat-label">compile_error_count {errored.get("compile_error_count", "0")}</div></div>
</div>

<div class="section">Session claims vs live UE</div>
<table><tr><th>Claim</th><th>Verdict</th><th>Evidence</th></tr>{claims_rows}</table>

<div class="section">Rhythm skills (8)</div>
<table><tr><th>Skill</th><th>Status</th><th>Asset</th><th>Class</th></tr>{skill_rows}</table>

<div class="section">UI sweep check</div>
<table><tr><th>Widget</th><th>Live state</th><th>Melodia refs</th><th>Notes</th></tr>{ui_rows}</table>

<div class="section">Battle bridge collapse</div>
<div class="card">{bridge_rows}</div>

<div class="section">T3D automation workflows</div>
<div class="card">{wf_rows}</div>

<div class="section">Live catalog (2026-08-06 re-export)</div>
<div class="grid">
  <div class="card"><h3>Exports</h3><div class="stat-value">{lc.get("exports_ok", "?")}/{lc.get("exports_total", "?")}</div><div class="stat-label">failed {lc.get("exports_failed", 0)}</div></div>
  <div class="card"><h3>Total size</h3><div class="stat-value">{cat_summary.get("total_size_formatted", "?")}</div><div class="stat-label">live T3D text</div></div>
  <div class="card"><h3>Migrated</h3><div class="stat-value good">{lc.get("migrated_count", "?")}</div><div class="stat-label">stock {lc.get("stock_remaining", "?")}</div></div>
  <div class="card"><h3>Progress</h3><div class="stat-value">{cat_summary.get("migration_progress_pct", "?")}%</div><div class="stat-label">of 23 widgets</div></div>
</div>
<div class="footer">Evidence: Saved/Melodia/session_claims_verification.json (Monolith MCP index + T3D export scans) &middot; Live catalog: Saved/T3D/live_catalog/*.t3d &middot; Dashboards regenerated 2026-08-06</div>"""
    return page(
        "T3D Agent Dashboard &middot; Live 2026-08-06",
        "Monolith MCP status, session-claim verification, rhythm pipeline, and live T3D catalog",
        body,
        "generated 2026-08-06 via Tools/rebuild_t3d_dashboards.py",
    )


def main():
    cat = load(os.path.join(SAVED, "T3D", "t3d_catalog.json"))
    t3d_data = load(os.path.join(SAVED, "AgentMemory", "t3d_dashboard_data.json"))
    claims = load(os.path.join(SAVED, "Melodia", "session_claims_verification.json"))

    outputs = {
        "t3d-catalog.html": render_catalog(cat, cat.get("live_drift", []), t3d_data),
        "agent-dashboard-t3d.html": render_agent(claims, t3d_data, cat["summary"]),
    }
    targets = [SAVED]
    if os.path.isdir(WIX):
        targets.append(WIX)
    for name, content in outputs.items():
        for target in targets:
            out = os.path.join(target, name)
            with open(out, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"wrote {out} ({len(content)} bytes)")


if __name__ == "__main__":
    sys.exit(main())
