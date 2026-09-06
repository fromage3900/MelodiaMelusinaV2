"""Universal garment harmonic-vocabulary uniqueness validator (2026-09-02).

Gate for the shared Chladni (m,n) mode vocabulary contract: no two garment
layers / water zones / drapery tiers may share a mode (the "no two articles
vibrate alike" rule). Catches the 2026-09-02 night defect where 3 of 4
singing-water zones collided with garment modes.

Reads the authoritative mode tables from the two source scripts and the system
manifest, reports any duplicate or invalid (m==n allowed; m,n >=1) mode as FAIL.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/universal_garment_vocab_check.py
Exit 0 = unique vocabulary; 1 = collisions found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))

GARMENT_SCRIPT = PROJECT / "Tools/Houdini/sea_above_reef/shorewake_cymatic_garment.py"
WATER_SCRIPT = PROJECT / "Tools/PCG/build_singing_water_veil_ecosystem.py"
WATER_KIT = PROJECT / "Tools/Houdini/sea_above_reef/singing_water_veil_kit.py"
SYSTEM_JSON = PROJECT / "Saved/Audit/universal_garment/universal_garment_system.json"


def parse_modes(path, key_hint):
    """Extract dict name->(m,n) by exec-ing just the literal table definition."""
    src = path.read_text(encoding="utf-8")
    ns = {}
    # find the dict literal following the given assignment and eval it
    import re
    for m in re.finditer(r"(MODE_BY_?LAYER|MODE_BY_ZONE|ZONE_MODE|MODES)\s*=\s*\{(.*?)\}", src, re.S):
        name = m.group(1)
        try:
            vals = eval("{" + m.group(2) + "}", {"__builtins__": {}}, ns)
        except Exception as e:
            return {key_hint: ("PARSE_ERROR", str(e))}
        return vals
    return {}


def main():
    vocab = {}
    # garment
    g = parse_modes(GARMENT_SCRIPT, "garment")
    # water ecosystem
    w = parse_modes(WATER_SCRIPT, "water")
    # water kit
    wk = parse_modes(WATER_KIT, "waterkit")

    # merge with domain tags for the report
    domains = {}
    for domain, d in (("garment", g), ("water_zone", w), ("water_kit", wk)):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (tuple, list)) and len(v) == 2:
                    domains[k] = (domain, tuple(v))

    # ---- registry cross-check (the real drift risk) ----
    # The gate must score the registry (universal_garment_system.json),
    # not just the code literals. If a lane edits one without the other,
    # report a REGISTRY_DRIFT FAIL so the fork cannot pass silently.
    registry_issues = []
    try:
        reg = json.loads(SYSTEM_JSON.read_text(encoding="utf-8"))
        reg_body = reg.get("vocab_contract") or reg.get("body", reg)  # modes live under vocab_contract
        reg_map = {}
        for piece, mode in (reg_body.get("garment_modes") or {}).items():
            reg_map[piece] = ("garment", tuple(mode))
        for zone, mode in (reg_body.get("water_zones") or {}).items():
            reg_map[zone] = ("water_zone", tuple(mode))
        for name, (reg_domain, reg_mode) in reg_map.items():
            code_entry = domains.get(name)
            if code_entry is None:
                registry_issues.append(
                    f"REGISTRY_ONLY {name} mode {reg_mode} not present in code tables")
            elif code_entry[1] != reg_mode:
                registry_issues.append(
                    f"REGISTRY_DRIFT {reg_domain}.{name}: registry {reg_mode} "
                    f"!= code {code_entry[1]}")

            # a registry piece must also stay unique within its own domain
    except Exception as e:  # pragma: no cover - defensive
        registry_issues.append(f"REGISTRY_UNREADABLE {e}")

    collisions = {}
    seen = {}
    for name, (domain, mode) in domains.items():
        if mode in seen:
            collisions.setdefault(mode, []).append(seen[mode])
            collisions[mode].append((domain, name))
        else:
            seen[mode] = (domain, name)
        # invalid: mode 0 or negative
        if mode[0] < 1 or mode[1] < 1:
            print(f"FAIL {domain}.{name} invalid mode {mode}")
            return 1

    for issue in registry_issues:
        print(f"FAIL {issue}")

    result = {
        "schema": "melodia.universal_garment_vocab_check.v1",
        "seed": 20260902,
        "article_count": len(domains),
        "unique_modes": len(seen),
        "collisions": {f"{m[0]}x{m[1]}": [f"{d}.{n}" for d, n in v] for m, v in collisions.items()},
        "registry_crosscheck": {
            "issues": registry_issues,
            "pass": not registry_issues,
            "checked_registry": str(SYSTEM_JSON),
        },
        "pass": not collisions and not registry_issues,
    }
    print(f"[vocab] {len(domains)} articles | {len(seen)} unique modes | "
          f"{len(collisions)} collisions | {len(registry_issues)} registry issues")
    if collisions:
        for m, v in result["collisions"].items():
            print(f"  COLLISION {m}: {v}")
    out = PROJECT / "Saved/Audit/universal_garment/garment_vocab_check.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[vocab] wrote {out}")
    if not collisions and not registry_issues:
        print("[vocab] PASS — vocabulary unique + registry in lockstep")
    return 0 if (not collisions and not registry_issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())