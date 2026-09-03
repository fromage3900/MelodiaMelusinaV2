"""finalize_niagara_bounds.py - set system-level Fixed Bounds on owned systems.

Contract conformance (Tools/niagara_ecosystem_audit.py --contract) requires
SYSTEM-level fixed bounds (UNiagaraSystem::bFixedBounds + FixedBounds box).
The authoring scripts (Tools/author_uni_shells.py, Tools/author_endless_loops.py)
set emitter-level CalculateBoundsMode=Fixed only; this tool promotes the same
box to the system level so the audit reads conformance true.

Rerunnable + idempotent: safe to re-run at any time; sets, saves, compiles,
then prints per-system diagnostics.

Run from Tools/:  python finalize_niagara_bounds.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

# system -> (min, max) system-level bounds box (mirrors each emitter's box)
SYSTEMS = {
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_DustShafts": ([-900, -700, -400], [900, 700, 1800]),
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_PollenSparkle": ([-900, -700, -400], [900, 700, 1800]),
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_Fireflies": ([-1000, -800, -600], [1000, 800, 600]),
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_LeafDrift": ([-1200, -900, -800], [1200, 900, 800]),
    "/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_PetalEndlessLoop": ([-1400, -1000, -1000], [1400, 1000, 1000]),
    "/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop": ([-800, -500, -120], [800, 500, 120]),
}


def nq(action, params, timeout=180):
    return monolith("niagara_query", {"action": action, "params": params}, timeout=timeout)


def ok(action, params):
    r = nq(action, params)
    if r.startswith("ERROR:"):
        print(f"  !! {action} FAILED: {r[:200]}")
    return r


def main() -> int:
    failures = 0
    for path, (bmin, bmax) in SYSTEMS.items():
        print(f"\n== {path.rsplit('/', 1)[-1]}")
        ok("set_fixed_bounds", {"asset_path": path, "min": bmin, "max": bmax})
        ok("save_system", {"asset_path": path})
        ok("request_compile", {"asset_path": path})
        time.sleep(2)
        r = ok("get_system_diagnostics", {"asset_path": path})
        try:
            d = json.loads(r)
            errs = d.get("error_count", -1)
            warns = d.get("warning_count", -1)
            print(f"  diagnostics: errors={errs} warnings={warns}")
            if errs not in (0, -1) or warns not in (0, -1):
                failures += 1
        except Exception:
            print("  diagnostics raw:", r[:400])
            failures += 1
        # verify by re-reading
        s = ok("get_system_summary", {"asset_path": path})
        try:
            props = json.loads(s).get("system_properties", {})
            print(f"  verify: fixed_bounds={props.get('fixed_bounds')} warmup={props.get('warmup_time')}")
            if not props.get("fixed_bounds"):
                failures += 1
        except Exception:
            print("  summary raw:", s[:300])
            failures += 1
    print(f"\nDone. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
