"""finalize_niagara_effect_types.py - align owned universal systems to ENV_StorybookAmbientVFX.

Idempotent: sets effect type only on systems that do not already carry it, saves
each, then read-backs effect_type + diagnostics per system (evidence standard).

Run from Tools/ with the editor open (Monolith at :9316):
    python Tools/finalize_niagara_effect_types.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

EFFECT_AMBIENT = "/Game/EnvSandbox/VFX/EffectTypes/ENV_StorybookAmbientVFX.ENV_StorybookAmbientVFX"

SYSTEMS = [
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_DustShafts",
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_PollenSparkle",
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_Fireflies",
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_LeafDrift",
]


def nq(action, params, timeout=180):
    return monolith("niagara_query", {"action": action, "params": params}, timeout=timeout)


def ok(action, params):
    r = nq(action, params)
    if r.startswith("ERROR:"):
        print(f"  !! {action} FAILED: {r[:200]}")
    return r


def current_effect_type(path) -> str:
    s = ok("get_system_summary", {"asset_path": path})
    try:
        return str((json.loads(s).get("system_properties") or {}).get("effect_type", "null"))
    except Exception:
        return f"unparseable:{s[:120]}"


def main() -> int:
    failures = 0
    for path in SYSTEMS:
        name = path.rsplit("/", 1)[-1]
        before = current_effect_type(path)
        print(f"== {name}  (before: {before})")
        if "ENV_StorybookAmbientVFX" in before:
            print("  already ambient; skipping write")
            continue
        ok("set_effect_type", {"asset_path": path, "effect_type": EFFECT_AMBIENT})
        ok("save_system", {"asset_path": path})
        ok("request_compile", {"asset_path": path})
        time.sleep(2)
        after = current_effect_type(path)
        print(f"  verify: effect_type={after}")
        if "ENV_StorybookAmbientVFX" not in after:
            failures += 1
        r = ok("get_system_diagnostics", {"asset_path": path})
        try:
            d = json.loads(r)
            errs = d.get("error_count", -1)
            warns = d.get("warning_count", -1)
            print(f"  diagnostics: errors={errs} warnings={warns}")
            if errs not in (0, -1) or warns not in (0, -1):
                failures += 1
        except Exception:
            print("  diagnostics raw:", r[:300])
            failures += 1
    print(f"\nDone. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())