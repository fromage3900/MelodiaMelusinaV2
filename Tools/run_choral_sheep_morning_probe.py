"""Choral Sheep morning-level integration probe (L_MelusinaMorning).

Flow (ONE PIE session, map file never saved):
  1. load L_MelusinaMorning (editor, no save) + PIE
  2. summon BP_ChoralSheep at player (PIE-only actor; vanishes on stop)
  3. REST window 25s  -> operator screenshots CF_A01 idle
  4. ApplyChoralSheepDefinition expect True (DA role fix verification)
  5. TryBeginHarmonize expect True -> sample CurrentHarmonizeWeight ramp
  6. HARMONIZE window 30s -> operator screenshots CF_A02/CF_A03
  7. EndCompanionInteraction -> decay sample -> stop PIE -> evidence JSON

Usage: python Tools/run_choral_sheep_morning_probe.py
Evidence: Docs/Evidence/CHORAL_SHEEP_MORNING_PROBE_<date>.json
"""

from mcp_client import post_envelope
import json
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
MONOLITH_URL = "http://127.0.0.1:9316/mcp"
MAP = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"


def mcall(tool, args):
    p = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": tool, "arguments": args}}
    return post_envelope(json.dumps(p).encode(), timeout=90)


def ed(action, **kw):
    raw = mcall("editor_query", {"action": action, **kw})
    if isinstance(raw, dict) and "error" in raw:
        return raw
    try:
        result = raw.get("result", {})
        content = result.get("content") or []
        text = content[0].get("text", "") if content else ""
        return json.loads(text) if text else raw
    except Exception:
        return {"_raw": raw}


def call_fn(target, function, args=None, component_name=None):
    kw = {"function": function, "args": args or {}, "allow_non_callable": True,
          "class_name": target}
    if component_name:
        kw["component_name"] = component_name
    return ed("pie_call_function", **kw)


def get_props(target, properties, component_name=None):
    kw = {"properties": properties, "class_name": target}
    if component_name:
        kw["component_name"] = component_name
    return ed("pie_get_object_properties", **kw)


def weight_of(s):
    try:
        props = s.get("properties", s)
        return float(props.get("CurrentHarmonizeWeight", -1))
    except Exception:
        return -1.0


evidence = {"schema": "melodia.choral_sheep.morning_probe.v1",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "map": MAP, "steps": {}, "assertions": {}}

print("1. Loading " + MAP + " (no save)")
print("  " + str(ed("load_level", path=MAP))[:160])
print("2. Starting PIE (heavy map: poll up to 150s for boot)")
print("  " + str(ed("start_pie"))[:160])


def wait_for_pie(label, probe_fn, timeout_s=150):
    waited = 0
    while waited < timeout_s:
        time.sleep(6)
        waited += 6
        try:
            r = probe_fn()
            if "PIE not running" not in str(r) and "_raw" not in r:
                print("  %s alive after %ds" % (label, waited))
                return r
        except Exception:
            pass
    raise RuntimeError("%s never came alive in PIE" % label)


wait_for_pie("player-pawn",
             lambda: get_props("BP_MelusinaJRPGCharacter", ["CurrentHarmonizeWeight"]))

try:
    print("3. Summon sheep at player (PIE-only, map untouched)")
    summon = ed("run_console_command", command="summon BP_ChoralSheep")
    print("  SUMMON: " + str(summon)[:300])
    time.sleep(2.0)
    resolve = get_props("BP_ChoralSheep", ["CurrentHarmonizeWeight", "HarmonizeFadeSpeed"])
    print("  RESOLVE: " + str(resolve)[:300])
    evidence["steps"]["summon"] = {"console": str(summon)[:300], "resolve": resolve}
    assert "BP_ChoralSheep" in str(resolve), "summoned sheep must resolve"

    print("4. REST window 25s -- SCREENSHOT CF_A01 NOW")
    time.sleep(25.0)

    print("5. ApplyChoralSheepDefinition (DA role-fix verification)")
    applied = call_fn("BP_ChoralSheep", "ApplyChoralSheepDefinition")
    print("  APPLY: " + str(applied)[:300])
    evidence["steps"]["apply_definition"] = applied
    assert applied.get("return_value") is True, "definition must apply (role=Companion)"

    print("6. TryBeginHarmonize")
    begun = call_fn("BP_ChoralSheep", "TryBeginHarmonize", args={"Interactor": None})
    print("  BEGIN: " + str(begun)[:300])
    evidence["steps"]["begin"] = begun
    assert begun.get("return_value") is True, "harmonize must begin"

    print("7. Sampling weight ramp")
    samples = []
    for i in range(5):
        time.sleep(0.8)
        s = get_props("BP_ChoralSheep", ["CurrentHarmonizeWeight"])
        samples.append(s)
    weights = [weight_of(s) for s in samples]
    print("  WEIGHTS: " + str(weights))
    evidence["steps"]["weights"] = weights
    assert weights[-1] > 0.9, "weight must ramp to ~1, got %s" % weights
    evidence["assertions"]["harmonize_weight_ramps"] = True

    print("8. HARMONIZE window 30s -- SCREENSHOT CF_A02/CF_A03 NOW")
    time.sleep(30.0)

    print("9. End + decay check")
    call_fn("BP_ChoralSheep", "EndCompanionInteraction")
    time.sleep(1.5)
    w_after = weight_of(get_props("BP_ChoralSheep", ["CurrentHarmonizeWeight"]))
    print("  WEIGHT_AFTER_END: " + str(w_after))
    evidence["steps"]["decay_weight"] = w_after
    assert w_after < weights[-1], "weight must decay after end"
    evidence["assertions"]["harmonize_weight_decays"] = True

    evidence["overall_verdict"] = "PASS"
    print(">>> MORNING PROOF PASS <<<")
finally:
    print("Stopping PIE (summoned sheep vanishes; map file untouched)")
    print("  " + str(ed("stop_pie"))[:120])

stamp = time.strftime("%Y-%m-%d", time.gmtime())
out = PROJECT_ROOT / "Docs" / "Evidence" / ("CHORAL_SHEEP_MORNING_PROBE_%s.json" % stamp)
out.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
print("Saved " + str(out.relative_to(PROJECT_ROOT)))
