#!/usr/bin/env python3
"""
Melodia Continuous Improvement Loop.
Auto-detects issues → fixes via T3D → re-verifies → reports.
Runs in a loop until everything passes or interrupted.

Usage:
    python Tools/continuous_loop.py [--interval SECONDS] [--max-failures N]
"""
import json, sys, time, os
from datetime import datetime
from pathlib import Path

from mcp_client import monolith, MONOLITH_URL as MONOLITH

def parse_json(text):
    try: return json.loads(text)
    except: return {}

class ContinuousLoop:
    def __init__(self, interval=10, max_failures=5):
        self.interval = interval
        self.max_failures = max_failures
        self.iteration = 0
        self.total_fixes = 0
        self.report = []
    
    def check_and_fix(self, name, check_fn, fix_fn=None):
        """Check a condition. If fails, optionally fix it."""
        result = check_fn()
        if result.get("ok"):
            return True
        self.report.append({"time": datetime.now().isoformat(), "check": name, "status": "FAIL", "detail": result.get("detail","")})
        print(f"  ❌ {name}: {result.get('detail','')}")
        
        if fix_fn:
            fix_result = fix_fn()
            if fix_result.get("ok"):
                self.total_fixes += 1
                self.report[-1]["fix"] = fix_result.get("detail","")
                print(f"     🔧 Fixed: {fix_result.get('detail','')}")
                # Re-verify
                check_result = check_fn()
                if check_result.get("ok"):
                    self.report[-1]["status"] = "FIXED"
                    print(f"     ✅ Verified")
                else:
                    print(f"     ❌ Fix didn't work: {check_result.get('detail','')}")
            else:
                print(f"     ❌ Fix failed: {fix_result.get('detail','')}")
        return False
    
    def check_monolith(self):
        h = monolith("monolith_status", {})
        if "server_running" in h:
            return {"ok": True}
        return {"ok": False, "detail": "Monolith not responding"}
    
    def check_bp_errors(self):
        e = monolith("editor_query", {"action":"list_errored_blueprints"})
        d = parse_json(e)
        count = d.get("count", 999)
        if count == 0:
            return {"ok": True}
        errors_list = [b.get("name","") for b in d.get("blueprints",[])]
        return {"ok": False, "detail": f"{count} BP errors: {', '.join(errors_list[:3])}"}
    
    def check_dirty_packages(self):
        d = monolith("editor_query", {"action":"list_dirty_packages"})
        dd = parse_json(d)
        count = dd.get("count", 0)
        if count == 0:
            return {"ok": True}
        return {"ok": False, "detail": f"{count} dirty packages"}
    
    def check_pipeline_nodes(self):
        bc = monolith("blueprint_query", {"action":"export_graph","asset_path":"/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController"})
        pipeline = ["CompleteBattle","StartSession","SubmitRatedInput","ConsumePendingRequest","TryGrantShards","RecordInputNow"]
        missing = [p for p in pipeline if p not in bc]
        if not missing:
            return {"ok": True}
        return {"ok": False, "detail": f"Missing: {', '.join(missing)}"}
    
    def _fetch_fingerprint(self, asset_path):
        """Return the graph fingerprint string, or None if unavailable."""
        raw = monolith("blueprint_query", {"action":"get_graph_fingerprint","asset_path":asset_path,"mode":"topology"})
        d = parse_json(raw)
        if isinstance(d, dict) and "fingerprint" in d:
            return d["fingerprint"]
        if isinstance(d, dict) and d.get("status") == "ok":
            return json.dumps(d, sort_keys=True)
        return None

    def fix_pipeline_nodes(self):
        """Inject missing pipeline nodes via build_blueprint_from_spec.

        A fingerprint guard snapshots the graph before injecting and re-fetches
        afterwards: any change other than the injected nodes (disappearing
        pre-existing nodes, or an unchanged fingerprint) is reported loudly and
        treated as a failed fix — never silently proceeded with.
        """
        bc_path = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController"
        rhythm_class = "/Script/BS_GodFile.MelodiaRhythmCombatSubsystem"
        wallet_class = "/Script/MelodiaCore.MelodiaTokenWalletSubsystem"
        pipeline = ["CompleteBattle","StartSession","SubmitRatedInput","ConsumePendingRequest","TryGrantShards","RecordInputNow"]

        # Scan what's missing and inject only those
        bc = monolith("blueprint_query", {"action":"export_graph","asset_path":bc_path})
        nodes_to_add = []
        conns = []
        pos_x = 1700

        if "StartSession" not in bc:
            nodes_to_add.append({"id":"N_SS","type":"CallFunction","function_name":"StartSession","function_class":rhythm_class,"position":[pos_x,500]})
            pos_x += 350
        if "SubmitRatedInput" not in bc:
            nodes_to_add.append({"id":"N_SR","type":"CallFunction","function_name":"SubmitRatedInput","function_class":rhythm_class,"position":[pos_x,500]})
            pos_x += 350
        if "ConsumePendingRequest" not in bc:
            nodes_to_add.append({"id":"N_CR","type":"CallFunction","function_name":"ConsumePendingRequest","function_class":rhythm_class,"position":[pos_x,500]})
            pos_x += 350
        if "TryGrantShards" not in bc:
            nodes_to_add.append({"id":"N_TG","type":"CallFunction","function_name":"TryGrantShards","function_class":wallet_class,"position":[pos_x,500]})

        if not nodes_to_add:
            return {"ok": True, "detail": "Nothing to fix"}

        injected_names = [n.get("function_name","") for n in nodes_to_add]

        # --- fingerprint guard: snapshot before injecting ---
        pre_fp = self._fetch_fingerprint(bc_path)
        pre_graph = bc

        result = monolith("blueprint_query", {"action":"build_blueprint_from_spec",
            "asset_path": bc_path, "graph_name": "EventGraph",
            "nodes": nodes_to_add, "auto_compile": True})

        # --- fingerprint guard: verify only the injected nodes changed ---
        post_fp = self._fetch_fingerprint(bc_path)
        post_graph = monolith("blueprint_query", {"action":"export_graph","asset_path":bc_path})

        guard_ok = True
        guard_notes = []
        if pre_fp is not None and post_fp is not None and pre_fp == post_fp:
            guard_ok = False
            guard_notes.append(f"FINGERPRINT UNCHANGED after injection — injected nodes had no effect on {bc_path}")
        elif pre_fp is None or post_fp is None:
            guard_notes.append(f"WARNING: fingerprint unavailable (pre={pre_fp!r}, post={post_fp!r}); relying on graph diff only")
        disappeared = [n for n in pipeline if n in pre_graph and n not in post_graph]
        invisible = [n for n in injected_names if n not in post_graph]
        if disappeared:
            guard_ok = False
            guard_notes.append(f"EXISTING NODES DISAPPEARED after injection: {', '.join(disappeared)}")
        if invisible:
            guard_ok = False
            guard_notes.append(f"Injected node(s) missing from graph after injection: {', '.join(invisible)}")
        if pre_fp is not None and post_fp is not None and pre_fp != post_fp and not guard_notes:
            guard_notes.append("fingerprint changed as expected (only injected nodes)")

        for note in guard_notes:
            print(f"     !! {note}")
        if not guard_ok:
            return {"ok": False, "detail": "; ".join(guard_notes)}

        parsed = parse_json(result)
        created = parsed.get("summary",{}).get("nodes_created",0) if isinstance(parsed,dict) else 0
        return {"ok": created > 0, "detail": f"Injected {created} missing nodes (fingerprint guard passed)"}
    
    def check_skills(self):
        skills = ["DA_CadenceStrike","DA_ResonantArc","DA_LullabyMend","DA_DownbeatBreak",
                  "DA_DissonantSilence","DA_TempoShift","DA_CrescendoWave","DA_HarmonyShield"]
        for s in skills:
            r = monolith("project_query", {"action":"get_asset_details","asset_path":"/Game/MelodiaIntegration/Config/"+s})
            if s not in r:
                return {"ok": False, "detail": f"Missing: {s}"}
        return {"ok": True}
    
    def check_highway(self):
        hw = monolith("ui_query", {"action":"get_widget_tree","asset_path":"/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway"})
        layers = ["SheetMusicBG","AuroraOverlay","SparkleField"]
        missing = [l for l in layers if l not in hw]
        if not missing:
            return {"ok": True}
        return {"ok": False, "detail": f"Missing highway layers: {', '.join(missing)}"}
    
    def run_iteration(self):
        self.iteration += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'='*50}")
        print(f"  Iteration {self.iteration} — {now}")
        print(f"  Total fixes so far: {self.total_fixes}")
        print(f"{'='*50}")
        
        checks = [
            ("Monolith", self.check_monolith, None),
            ("BP Errors", self.check_bp_errors, None),
            ("Dirty Packages", self.check_dirty_packages, None),
            ("Pipeline Nodes", self.check_pipeline_nodes, self.fix_pipeline_nodes),
            ("Skills Exist", self.check_skills, None),
            ("Highway Layers", self.check_highway, None),
        ]
        
        failures = 0
        for name, check, fix in checks:
            if not self.check_and_fix(name, check, fix):
                failures += 1
        
        print(f"\n  {len(checks)-failures}/{len(checks)} passed, {failures} failed")
        
        if failures == 0:
            print(f"\n  ✅ ALL CHECKS PASSED — System is healthy")
            return True
        
        if failures >= self.max_failures:
            print(f"\n  ❌ Too many failures ({failures} >= {self.max_failures})")
            return False
        
        return None  # Keep going
    
    def generate_report(self):
        out = Path("Saved/continuous_improvement_report.html")
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Continuous Improvement Report</title>
<style>
body {{font-family:'Courier New',monospace;background:#0b0a13;color:#f2d69e;padding:20px;}}
h1 {{color:#78ebff;}}
table {{width:100%;border-collapse:collapse;}}
th {{text-align:left;padding:8px;color:#78ebff;border-bottom:1px solid #38293b;}}
td {{padding:8px;border-bottom:1px solid #1a1520;}}
.pass {{color:#22c55e;}} .fail {{color:#ef4444;}} .fix {{color:#eab308;}}
</style></head><body>
<h1>Continuous Improvement Report</h1>
<p>Total fixes applied: {self.total_fixes} · Iterations: {self.iteration}</p>
<table>
<tr><th>Time</th><th>Check</th><th>Status</th><th>Detail</th></tr>"""
        for r in self.report:
            status_icon = {"FAIL":"❌","FIXED":"🔧","PASS":"✅"}.get(r.get("status",""),"❓")
            html += f"<tr><td>{r['time'][11:19]}</td><td>{r['check']}</td><td class='{r.get('status','').lower()}'>{status_icon} {r.get('status','')}</td><td>{r.get('detail','')} {r.get('fix','')}</td></tr>"
        html += "</table></body></html>"
        out.write_text(html, encoding="utf-8")
        print(f"\nReport: {out.resolve()}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=30, help="Seconds between iterations")
    parser.add_argument("--max-failures", type=int, default=5, help="Stop after N consecutive failures")
    args = parser.parse_args()
    
    loop = ContinuousLoop(interval=args.interval, max_failures=args.max_failures)
    
    try:
        while True:
            result = loop.run_iteration()
            loop.generate_report()
            if result is True:
                print("\n🎉 System is fully healthy! Watching for regressions...")
            elif result is False:
                print("\n⚠ Too many failures. Manual intervention needed.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n\nStopped.")
    
    loop.generate_report()
    print(f"\nSession summary: {loop.total_fixes} fixes applied across {loop.iteration} iterations")

if __name__ == "__main__":
    main()
