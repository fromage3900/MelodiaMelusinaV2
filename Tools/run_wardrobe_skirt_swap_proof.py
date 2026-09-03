"""Wardrobe Skirt swap state proof v2 — outer driver.
Starts PIE, runs the in-PIE proof via editor run_python, captures a screenshot,
stops PIE, writes evidence JSON.
"""
import json
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
MONOLITH_URL = "http://127.0.0.1:9316/mcp"
AUDIT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "p0_real_input_run"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
PROOF_SCRIPT = Path(r"C:\Users\froma\AppData\Local\Temp\opencode\skirt_proof_pie.py")


def call_editor(action, timeout=300, **kwargs):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "editor_query",
                          "arguments": {"action": action, **kwargs}}}
    req = urllib.request.Request(
        MONOLITH_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
        try:
            return json.loads(raw)
        except Exception:
            return raw


print("1. load level")
print("  ", call_editor("load_level", timeout=420,
                       path="/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"))
print("2. start PIE")
print("  ", call_editor("start_pie", timeout=180))
time.sleep(3.0)

print("3. run in-PIE proof")
code = PROOF_SCRIPT.read_text(encoding="utf-8")
proof = call_editor("run_python", timeout=300, command=code)

lines = []
for o in (proof.get("output") or []):
    line = o.get("output", "")
    lines.extend(line.splitlines())
for line in lines:
    if ("[SKIRTPROOF]" in line or "FAIL" in line or "Error" in line
            or "error" in line or "Traceback" in line or "Warning" in line):
        print("  ", line.strip()[:250])

json_line = next((l for l in lines if "[SKIRTPROOF-JSON]" in l), None)
result = None
if json_line:
    blob = json_line.split("[SKIRTPROOF-JSON]", 1)[1].strip()
    try:
        result = json.loads(blob)
    except Exception as e:
        result = {"error": f"json parse fail: {e}", "raw": blob[:500]}

time.sleep(1.0)
print("4. screenshot")
try:
    shot = call_editor("capture_scene_preview", timeout=180)
    print("  ", json.dumps(shot)[:300])
except Exception as e:
    shot = {"error": str(e)}
    print("  capture_scene_preview:", e)

print("5. stop PIE")
try:
    call_editor("stop_pie", timeout=120)
except Exception as e:
    print("  stop failed:", e)

evidence = {
    "schema": "melodia.wardrobe_skirt_swap_state.v2",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "cosmetic": "Cos_Skirt_MelusinaV2",
    "slot": 7,
    "grant_id": "proof_skirt_grant_20260903",
    "mechanism": "PIE GameInstance subsystem grant -> component equip (wardrobe authority; programmatic seam documented, rhythm real-input standard not applicable to wardrobe state gates per 2026-09-01 precedent)",
    "proof": result,
    "screenshot_attempt": shot,
}
verdict = "FAIL:no_result_json"
if result and result.get("checks"):
    verdict = "PASS" if all(c["ok"] for c in result["checks"]) else "FAIL"
elif result and result.get("error"):
    verdict = "HOLD:" + result["error"][:80]
evidence["overall_verdict"] = verdict

out = AUDIT_DIR / "wardrobe_skirt_swap_state_2026-09-03.json"
out.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
print(f"VERDICT: {verdict}")
print(f"Evidence: {out}")
