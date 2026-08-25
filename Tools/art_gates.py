#!/usr/bin/env python3
"""art_gates.py - the art-side gate that this project never had.

Every other gate in this repo is Blueprint, UI, or git hygiene. `echo_gates.yml`
runs bp_live_path, graph_reachability, ui_style_audit and bp_sweep; the git hooks
check LFS size and branch names. Nothing has ever checked a material, a mesh, a
texture or an asset name - while the project carries 904 masters, 1268 instances
and a Substrate Toon spine.

`specs/ci_gates.json` has described art budgets since it was written and is read by
nothing: `grep -rn ci_gates` returns AGENTS.md prose and a search index, no code.
Its values were also strings ("max_150"), so no parser could have existed.
`Content/Python/lib_gates.py:25 gate_material_compiles(asset_path, max_ps=...)`
already implements the shader-instruction check correctly and has zero callers.

This file is the caller.

Two halves, because they have different requirements:

  offline  - naming, duplicate short names, Masters/ hygiene, spec sanity.
             Pure disk + git. Runs in CI, runs with the editor closed, runs fast.
  live     - shader instruction counts, material compile status.
             Needs the editor and Monolith on 9316 (lib_gates imports `unreal`).

Offline is the half that can run today on every push. Live is opt-in via --live.

Usage:
    python Tools/art_gates.py --summary          # offline gates, CI form
    python Tools/art_gates.py                    # offline gates, full detail
    python Tools/art_gates.py --live             # + shader budgets (needs editor)
    python Tools/art_gates.py --json out.json    # machine-readable report

Exit codes: 0 = all gates pass, 1 = at least one FAIL, 2 = could not run.
Warnings never fail the build; they are printed and counted.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs" / "ci_gates.json"

# --------------------------------------------------------------------------
# Asset naming.
#
# Grounded in the tracked tree, not invented: the prefixes below are the ones
# that actually dominate `git ls-files 'Content/**/*.uasset'` --
# T_ 285, M_ 181, PCG_ 145, SM_ 121, MI_ 57, BP_ 56, A_ 54, DA_ 21, SK_ 20,
# TP_ 18, L_ 16. Legacy lowercase/vendor prefixes (interiorwalltrim_, zun_,
# rock_, ita_, kir_, ZUN_) are real and numerous, so unknown prefixes WARN
# rather than fail; renaming vendor content is a separate, owner-owned job.
# --------------------------------------------------------------------------
KNOWN_PREFIXES = {
    "T_": "Texture",
    "M_": "Material (master)",
    "MI_": "Material instance",
    "MF_": "Material function",
    "TP_": "Toon profile",
    "SM_": "Static mesh",
    "SK_": "Skeletal mesh",
    "A_": "Animation",
    "AM_": "Anim montage",
    "ABP_": "Anim blueprint",
    "BS_": "Blend space",
    "BP_": "Blueprint",
    "WBP_": "Widget blueprint",
    "DA_": "Data asset",
    "PCG_": "PCG graph",
    "L_": "Level",
    "GC_": "Geometry cache",
    "NS_": "Niagara system",
    "E_": "Enum",
    "S_": "Struct",
}

# Suffixes that mean "work in progress" and must never live in a shipped
# spine folder. Every one of these is currently present in Masters/.
WIP_SUFFIX = re.compile(
    r"_(BACKUP|QUARANTINE|WORK|REPAIR|FALLBACK|RESTORED|PRETRIPLANAR|"
    r"LIVE_RENDER|OLD|TEMP|TMP|COPY|TEST)\b|_\d{8}(_\d{4})?$",
    re.IGNORECASE,
)

# Folders that are a shipped spine: only canonical assets belong here.
SPINE_FOLDERS = [
    "Content/EnvSandbox/Materials/Masters",
    "Content/EnvSandbox/Materials/ToonProfiles",
]


def _git(*args: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  ! git {' '.join(args)} failed: {exc}", file=sys.stderr)
        return []
    if out.returncode != 0:
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def _tracked_uassets() -> list[str]:
    """Tracked .uasset paths. Tracked, not on-disk: CI only ever sees these,
    and a gate that passes locally but not in CI is worse than no gate."""
    return [p for p in _git("ls-files", "Content") if p.endswith(".uasset")]


# --------------------------------------------------------------------------
# Spec
# --------------------------------------------------------------------------
def load_budgets() -> tuple[dict, list[str]]:
    """Parse specs/ci_gates.json into real numbers.

    Accepts both the historical string form ("max_150") and plain numbers, so
    this keeps working whichever way the spec is written.
    """
    notes: list[str] = []
    if not SPEC.exists():
        return {}, [f"{SPEC.relative_to(ROOT)} missing"]
    try:
        raw = json.loads(SPEC.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{SPEC.relative_to(ROOT)} unreadable: {exc}"]

    budgets: dict[str, object] = {}
    for key, val in raw.items():
        if isinstance(val, (int, float)):
            budgets[key] = val
        elif isinstance(val, str):
            m = re.fullmatch(r"(?:max|min)_(\d+(?:\.\d+)?)([km]?)", val.strip(), re.I)
            if m:
                num = float(m.group(1))
                num *= {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
                budgets[key] = int(num) if num.is_integer() else num
            else:
                budgets[key] = val  # categorical: "0_errors", "exact_match", "pass"
        else:
            notes.append(f"unparseable budget {key}={val!r}")
    return budgets, notes


# --------------------------------------------------------------------------
# Offline gates
# --------------------------------------------------------------------------
def gate_spine_hygiene(assets: list[str]) -> dict:
    """No work-in-progress variants and no instances inside a spine folder.

    Nine live variants of the landscape master and four of the Universal master
    sit in Masters/ today -- all loadable, all parentable, all indistinguishable
    from the real one to anything matching on short name.
    """
    wip, misplaced = [], []
    for p in assets:
        folder = str(Path(p).parent).replace("\\", "/")
        if folder not in SPINE_FOLDERS:
            continue
        stem = Path(p).stem
        if WIP_SUFFIX.search(stem):
            wip.append(p)
        if stem.startswith("MI_"):
            misplaced.append(p)
    return {
        "name": "spine_hygiene",
        "passed": not wip and not misplaced,
        "detail": {"wip_variants": sorted(wip), "instances_in_masters": sorted(misplaced)},
        "hint": "Move WIP variants out of the spine folder (Docs/_Superseded or an _Archive "
                "subfolder). Instances belong under Materials/Instances, not Masters/.",
    }


def gate_duplicate_short_names(assets: list[str]) -> dict:
    """No two tracked assets share a short name.

    AGENTS.md already names this defect class: "Duplicate short names. Substring
    assertions pass against either copy." Most audit scripts in this repo match on
    short name, so a duplicate makes them silently non-deterministic about which
    asset they validated.
    """
    by_stem: dict[str, list[str]] = defaultdict(list)
    for p in assets:
        by_stem[Path(p).stem].append(p)
    dupes = {k: sorted(v) for k, v in by_stem.items() if len(v) > 1}
    return {
        "name": "duplicate_short_names",
        "passed": not dupes,
        # `all_stems` is the keying surface and must stay complete -- `duplicates` is
        # truncated for display, and baselining off the truncated view would leave the
        # remaining stems looking brand new on the next run.
        "all_stems": sorted(dupes),
        "detail": {"count": len(dupes), "duplicates": dict(sorted(dupes.items())[:40])},
        "hint": "Rename or delete one copy. Until then, treat every short-name-matching "
                "audit result as unreliable.",
    }


def gate_naming(assets: list[str]) -> dict:
    """Asset prefixes. Unknown prefixes warn; a wrong prefix for a known folder fails.

    CONTRIBUTING.md:78 points at a naming section in PIPELINE.md that does not
    exist, so there has never been an enforceable convention. This encodes the one
    the tree already mostly follows.
    """
    hard, soft = [], []
    for p in assets:
        stem = Path(p).stem
        folder = str(Path(p).parent).replace("\\", "/")
        pref = next((k for k in sorted(KNOWN_PREFIXES, key=len, reverse=True)
                     if stem.startswith(k)), None)
        # Hard rules only where the folder declares the type unambiguously.
        if folder == "Content/EnvSandbox/Materials/ToonProfiles" and not stem.startswith("TP_"):
            hard.append(f"{p}  (ToonProfiles/ requires TP_)")
        elif folder == "Content/EnvSandbox/Materials/Masters" and not stem.startswith("M_"):
            hard.append(f"{p}  (Masters/ requires M_)")
        elif pref is None:
            soft.append(p)
    return {
        "name": "naming",
        "passed": not hard,
        "detail": {"violations": sorted(hard),
                   "unknown_prefix_count": len(soft),
                   "unknown_prefix_sample": sorted(soft)[:15]},
        "hint": "Unknown prefixes are mostly vendor/legacy content and only warn. "
                "Spine folders are strict.",
    }


def gate_spec_sanity(budgets: dict, notes: list[str]) -> dict:
    """The budget spec parses and the numeric budgets are actually numeric."""
    numeric = {k: v for k, v in budgets.items() if isinstance(v, (int, float))}
    return {
        "name": "ci_gates_spec",
        "passed": bool(budgets) and not notes,
        "detail": {"budgets": budgets, "numeric": numeric, "notes": notes},
        "hint": "specs/ci_gates.json must parse and expose numeric budgets for the "
                "live gates to enforce anything.",
    }


# --------------------------------------------------------------------------
# Live gate (needs the editor)
# --------------------------------------------------------------------------
def gate_shader_budgets(budgets: dict, assets: list[str]) -> dict:
    """Shader instruction counts for tracked masters, via Monolith.

    Delegates to Content/Python/lib_gates.gate_material_compiles, which already
    reads MaterialEditingLibrary.get_statistics() and compares against a cap --
    the function that has existed and had no callers.

    Requires exactly one editor on 9316. Per AGENTS.md rule 7 this must never run
    alongside another editor writer, and per the D_DamageType note it must never be
    pointed at Content/TurnBasedJRPGTemplate/Blueprints/Skills/.
    """
    max_ps = budgets.get("shader_instructions")
    if not isinstance(max_ps, (int, float)):
        return {"name": "shader_budgets", "passed": True,
                "detail": {"skipped": "no numeric shader_instructions budget"}, "hint": ""}

    masters = [p for p in assets
               if str(Path(p).parent).replace("\\", "/") == "Content/EnvSandbox/Materials/Masters"]
    if not masters:
        return {"name": "shader_budgets", "passed": True,
                "detail": {"skipped": "no tracked masters"}, "hint": ""}

    try:
        sys.path.insert(0, str(ROOT / "Content" / "Python"))
        import lib_gates  # noqa: PLC0415  (editor-only import, deliberate)
    except ImportError as exc:
        return {"name": "shader_budgets", "passed": False,
                "detail": {"error": f"lib_gates unavailable: {exc}"},
                "hint": "Run inside the editor via Monolith editor_query run_python."}

    over, failed, checked = [], [], 0
    for p in masters:
        game_path = "/Game/" + p[len("Content/"):].rsplit(".uasset", 1)[0]
        r = lib_gates.gate_material_compiles(game_path, max_ps=int(max_ps))
        checked += 1
        d = r.get("detail", {})
        if "error" in d:
            failed.append({"asset": game_path, "error": d["error"]})
        elif not r.get("passed"):
            over.append({"asset": game_path, "ps": d.get("ps"), "cap": int(max_ps)})
    return {
        "name": "shader_budgets",
        "passed": not over and not failed,
        "detail": {"cap": int(max_ps), "checked": checked, "over_budget": over,
                   "load_or_compile_failures": failed},
        "hint": f"Masters over {int(max_ps)} pixel-shader instructions need simplifying "
                "or an explicit, recorded budget exception.",
    }


# --------------------------------------------------------------------------
BASELINE = ROOT / "specs" / "art_gates_baseline.json"


def _violation_keys(gate: dict) -> set[str]:
    """Stable identifiers for the individual violations a gate found."""
    keys: set[str] = set()
    name, d = gate["name"], gate["detail"]
    for p in d.get("wip_variants", []):
        keys.add(f"{name}:wip:{p}")
    for p in d.get("instances_in_masters", []):
        keys.add(f"{name}:mi_in_masters:{p}")
    for p in d.get("violations", []):
        keys.add(f"{name}:naming:{p.split('  (')[0]}")
    for stem in gate.get("all_stems", d.get("duplicates", {})):
        keys.add(f"{name}:dupe:{stem}")
    for item in d.get("over_budget", []):
        keys.add(f"{name}:over:{item.get('asset')}")
    return keys


def apply_baseline(gates: list[dict], baseline: set[str]) -> list[dict]:
    """Ratchet: pre-existing violations are recorded debt, new ones fail the build.

    Landing a linter on a tree with 120 duplicate short names and 11 WIP masters by
    failing everything would just get the gate switched off -- which is how this
    project ended up with ~130 audit scripts none of which run in CI. The baseline
    freezes today's damage and blocks tomorrow's. It is not a compensating mechanism:
    it does not cancel out a defect, it scopes enforcement to new work while the
    existing list stays visible in the output and in the baseline file.

    Shrink it by fixing things and re-running with --write-baseline. Never grow it.
    """
    for g in gates:
        new = _violation_keys(g) - baseline
        g["new_violations"] = sorted(new)
        g["baselined"] = len(_violation_keys(g) & baseline)
        g["passed"] = not new
    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description="Art-side quality gates.")
    ap.add_argument("--summary", action="store_true", help="one line per gate (CI form)")
    ap.add_argument("--live", action="store_true", help="also run editor gates (needs UE + Monolith)")
    ap.add_argument("--json", metavar="PATH", help="write a machine-readable report")
    ap.add_argument("--strict", action="store_true",
                    help="ignore the baseline; fail on every violation (the true state)")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record current violations as accepted debt and exit 0")
    args = ap.parse_args()

    budgets, notes = load_budgets()
    assets = _tracked_uassets()
    if not assets:
        print("art_gates: no tracked .uasset found - is this a git checkout?", file=sys.stderr)
        return 2

    gates = [
        gate_spec_sanity(budgets, notes),
        gate_spine_hygiene(assets),
        gate_duplicate_short_names(assets),
        gate_naming(assets),
    ]
    if args.live:
        gates.append(gate_shader_budgets(budgets, assets))

    if args.write_baseline:
        keys = sorted(k for g in gates for k in _violation_keys(g))
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({
            "_meta": {
                "doc": "Accepted art-gate debt. Shrink this file; never grow it.",
                "written": "run Tools/art_gates.py --write-baseline to regenerate",
                "policy": "A key here means the violation predates the gate. New violations "
                          "fail CI. Removing a key is progress; adding one needs a reason.",
            },
            "accepted": keys,
        }, indent=2), encoding="utf-8")
        print(f"art_gates: baseline written with {len(keys)} accepted violations -> "
              f"{BASELINE.relative_to(ROOT)}")
        return 0

    baseline: set[str] = set()
    if not args.strict and BASELINE.exists():
        try:
            baseline = set(json.loads(BASELINE.read_text(encoding="utf-8")).get("accepted", []))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"art_gates: baseline unreadable ({exc}); running strict", file=sys.stderr)
    if baseline:
        gates = apply_baseline(gates, baseline)

    failed = [g for g in gates if not g["passed"]]

    mode = "strict" if (args.strict or not baseline) else f"baselined ({len(baseline)} accepted)"
    print(f"art_gates - {len(assets)} tracked .uasset, {len(gates)} gates, {mode}")
    for g in gates:
        mark = "[ok]" if g["passed"] else "[FAIL]"
        extra = ""
        if g.get("baselined"):
            extra = f"  ({g['baselined']} pre-existing, {len(g.get('new_violations', []))} new)"
        print(f"  {mark} {g['name']}{extra}")
        if g.get("new_violations"):
            for v in g["new_violations"][:12]:
                print(f"      NEW: {v}")
        if args.summary:
            continue
        for key, val in g["detail"].items():
            if isinstance(val, list) and val:
                print(f"      {key}: {len(val)}")
                for item in val[:12]:
                    print(f"        - {item}")
                if len(val) > 12:
                    print(f"        ... {len(val) - 12} more")
            elif isinstance(val, dict) and val:
                print(f"      {key}: {len(val)}")
                for k2, v2 in list(val.items())[:12]:
                    print(f"        - {k2}: {v2}")
            elif not isinstance(val, (list, dict)):
                print(f"      {key}: {val}")
        if not g["passed"] and g.get("hint"):
            print(f"      -> {g['hint']}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"gates": gates, "asset_count": len(assets)},
                                  indent=2, default=str), encoding="utf-8")
        print(f"  written: {out}")

    if failed:
        print(f"\nart_gates: {len(failed)} gate(s) FAILED: {', '.join(g['name'] for g in failed)}")
        return 1
    print("\nart_gates: all gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
