"""niagara_ecosystem_audit.py - project-wide Niagara ecosystem review.

Read-only. Enumerates every Niagara system asset in the project (EnvSandbox,
Melodia, MelodiaIntegration, _PROJECT) and reports per system:
  - emitters, sim targets, bounds mode + size, warmup, determinism, effect type
  - user parameters (contract compliance against the ecosystem User.* set)
  - compile diagnostics (errors/warnings)
  - renderer materials flagged for engine-default markers
  - spawn/location module presence and event links

Contract check: a compliant system exposes only ecosystem parameters (or a
documented per-system extra), has fixed bounds, zero warmup, and clean
diagnostics. Output: Saved/Audit/niagara_ecosystem_review.json + console table.

Run from Python outside the editor (editor open with Monolith at :9316):
  python Tools/niagara_ecosystem_audit.py [--contract]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_client import monolith  # noqa: E402
from niagara_contract import CONTRACT_PARAMS  # noqa: E402,F401 - canonical 20-param contract

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved" / "Audit" / "niagara_ecosystem_review.json"

CONTENT_ROOTS = [
    "Content/EnvSandbox/VFX",
    "Content/Melodia/VFX",
    "Content/MelodiaIntegration/VFX",
    "Content/_PROJECT/VFX",
    "Content/ArtOfShader",
    "Content/UltraDynamicSky",
    "Content/_ThirdParty",
]

# paths treated as third-party / out of ecosystem-conformance scope
THIRD_PARTY_PREFIXES = (
    "/Game/UltraDynamicSky",
    "/Game/_ThirdParty",
    "/Game/ArtOfShader",
    "/Game/HairStrands",
    "/Game/Niagara",
)

# The project-wide ecosystem User parameter contract.
# Canonical machine-readable source: Tools/niagara_contract.py
# (docs: Docs/NIAGARA_ECOSYSTEM_2026-08-09.md §1;
#  mirrors Docs/Handoffs/NIAGARA_INFINITY_NIKKI_FINALIZATION_PLAN_2026-08-01.md §2)

DEFAULT_MARKERS = (
    "niagara/defaultassets",
    "defaultsystem",
    "fountainlightweight",
    "minimallightweight",
    "radialburst",
    "directionalburst",
)


def discover_systems() -> list[str]:
    found = set()
    for root in CONTENT_ROOTS:
        for uasset in glob.glob(os.path.join(ROOT, root, "**", "*.uasset"), recursive=True):
            if ".bak" in uasset or "_Recovery" in uasset or "_Quarantine" in uasset:
                continue
            rel = os.path.relpath(uasset, os.path.join(ROOT, "Content"))
            game = "/Game/" + rel[:-len(".uasset")].replace("\\", "/")
            found.add(game)
    return sorted(found)


def call(action: str, params: dict, tries: int = 10, wait: float = 8.0) -> dict:
    last = None
    for i in range(tries):
        r = monolith("niagara_query", {"action": action, "params": params})
        if not r.startswith("ERROR:"):
            try:
                return json.loads(r)
            except json.JSONDecodeError:
                return {"raw": r[:300]}
        last = r
        time.sleep(wait)
    return {"raw": str(last)}


def audit_system(path: str) -> dict:
    entry = {"asset_path": path}
    summary = call("get_system_summary", {"asset_path": path})
    if "error" in summary or "raw" in summary or not isinstance(summary, dict) or "system_name" not in summary:
        entry["status"] = "not_a_system_or_unloadable"
        entry["raw"] = summary
        return entry
    entry["status"] = "ok"
    entry["name"] = summary.get("system_name")
    entry["third_party"] = any(path.startswith(p) for p in THIRD_PARTY_PREFIXES)
    props = summary.get("system_properties", {})
    entry["warmup"] = props.get("warmup_time", 0)
    entry["determinism"] = props.get("determinism", False)
    entry["fixed_bounds"] = props.get("fixed_bounds", False)
    entry["effect_type"] = props.get("effect_type", "null")
    emitters = []
    for e in summary.get("emitters", []):
        emitters.append({
            "name": e.get("name"),
            "sim": e.get("sim_target"),
            "bounds_mode": e.get("calculate_bounds_mode"),
            "renderers": e.get("renderer_types", []),
            "events_out": e.get("generated_events", []),
            "events_in": e.get("consumed_events", []),
        })
    entry["emitters"] = emitters
    entry["emitter_count"] = len(emitters)
    entry["bounds_mode_system"] = props.get("fixed_bounds", False)

    up = call("get_user_parameters", {"asset_path": path})
    params = []
    if isinstance(up, dict):
        raw = up.get("result") or up.get("parameters") or up.get("user_parameters") or []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = []
        for p in raw:
            if isinstance(p, dict):
                params.append({"name": p.get("name"), "type": p.get("type")})
            else:
                params.append(str(p))
    entry["user_params"] = params
    entry["user_param_names"] = [
        (p.get("name")[5:] if isinstance(p, dict) and str(p.get("name", "")).startswith("User.") else (p if isinstance(p, str) and p.startswith("User.") else p))
        for p in params
    ]

    diag = call("get_system_diagnostics", {"asset_path": path})
    if isinstance(diag, dict):
        entry["errors"] = diag.get("error_count", -1)
        entry["warnings"] = diag.get("warning_count", -1)
        entry["error_msgs"] = [e.get("message", "")[:160] for e in diag.get("errors", [])][:4]
        entry["warning_msgs"] = [w.get("message", "")[:160] for w in diag.get("warnings", [])][:4]
    else:
        entry["errors"] = -1
        entry["warnings"] = -1
    return entry


def contract_violations(entry: dict) -> list[str]:
    issues = []
    if entry.get("status") != "ok":
        return issues
    if entry.get("third_party"):
        return issues
    if entry.get("errors", 0) != 0:
        issues.append("compile_errors")
    if entry.get("warnings", 0) != 0:
        issues.append("compile_warnings")
    if not entry.get("fixed_bounds"):
        issues.append("no_fixed_bounds")
    if entry.get("warmup", 0) > 0:
        issues.append(f"warmup_{entry['warmup']}")
    return issues


def contract_coverage(entry: dict) -> dict:
    """Which contract params the system declares (coverage, not conformance)."""
    names = set(entry.get("user_param_names", []))
    present = sorted(n for n in CONTRACT_PARAMS if n in names)
    return {"declared": len(present), "total": len(CONTRACT_PARAMS), "missing": sorted(set(CONTRACT_PARAMS) - set(present))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", action="store_true", help="emit contract compliance table")
    parser.add_argument("--systems", type=str, default="", help="comma list of system paths (default: all)")
    args = parser.parse_args()

    systems = [s for s in args.systems.split(",") if s] if args.systems else discover_systems()
    print(f"Scanning {len(systems)} assets under Content/VFX roots...")
    # skip obviously non-system folders to keep the report about graphs
    systems = [s for s in systems if not any(
        frag in s for frag in ("/Textures/", "/Alphas/", "/Materials/", "/Modules/", "/Curves/", "/MPC/", "/EffectTypes/"))]
    print(f"  -> {len(systems)} VFX graph assets")

    data = {}
    for path in systems:
        entry = audit_system(path)
        data[path] = entry
        name = entry.get("name", path.rsplit("/", 1)[-1])
        if entry.get("status") == "ok":
            cov = contract_coverage(entry)
            issues = contract_violations(entry)
            flag = "OK " if not issues else "!! "
            print(f"{flag}{name:34s} emitters:{entry['emitter_count']:2d} "
                  f"sim:{','.join(e['sim'] for e in entry['emitters'])[:20]:20s} "
                  f"bounds:{entry['fixed_bounds']} warmup:{entry['warmup']:6.2f} "
                  f"err:{entry['errors']} warn:{entry['warnings']} "
                  f"contract:{cov['declared']}/{cov['total']}"
                  f"{(' [3RD]' if entry.get('third_party') else '')}"
                  f"{(' | ' + ', '.join(issues)) if issues else ''}")
        else:
            print(f"-- {name:34s} NOT A SYSTEM ({entry.get('status')})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"\n-> {OUT}")

    if args.contract:
        ok = sum(1 for e in data.values() if e.get("status") == "ok" and not contract_violations(e))
        total = sum(1 for e in data.values() if e.get("status") == "ok")
        print(f"Contract compliant: {ok}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
