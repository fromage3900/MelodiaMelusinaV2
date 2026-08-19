#!/usr/bin/env python3
"""Offline gate: no Melusina geometry may be skinned to a bone outside the body chain.

WHY THIS EXISTS
---------------
Corneas separated from Melusina's head during animation while every static capture
looked correct. Three sessions chased it as an iris material/UV defect, then as a
retargeter tuning problem. It was neither.

The cornea section is skinned to the bone `eyes`, whose ancestry is:

    eyes -> MCH-eyes_parent -> root

`MCH-eyes_parent` is a Rigify eye-aim target driven by a CONSTRAINT in Blender.
Constraints do not survive FBX export, so in Unreal it is a plain child of `root` --
a sibling of the entire spine, not a descendant of the pelvis. At the reference pose
everything is coincident, which is why a still frame looks fine. The moment a clip
animates `head_x`, the head moves and the eyes stay behind.

The same shape explains the warped fingers: the second and third phalanges are skinned
to ARP controller bones (`c_index2_l`, `c_middle3_r`, ...) which the export also
flattens onto `root`.

A bone outside the `root_x` (pelvis) subtree can only move if an animation explicitly
keys it. The old V1 mocap clips DO key them -- they were baked in Blender with
constraints evaluated -- so they masked the defect for months. Any freshly retargeted
clip keys only the chained deform bones, and the geometry falls apart.

THE RULE
--------
Every bone that carries skin weight must be a descendant of `root_x`. That makes the
mesh follow the body by hierarchy instead of by hoping the animation happens to key a
constraint-driven helper.

This is a pure data check: it reads the exported skin contract and the serialized bone
hierarchy, both already in the repo. No Blender, no editor, no network.

BASELINE
--------
41 pre-existing violations are recorded in `specs/melusina_skin_topology_baseline.json`
following the same accepted-debt pattern as `specs/art_gates_baseline.json`: only NEW
violations fail. Removing an entry from the baseline is progress. Adding one needs a
reason. Run with `--strict` to see the true, unbaselined state.

Usage:
    python Tools/test_melusina_skin_topology_contract.py
    python Tools/test_melusina_skin_topology_contract.py --strict
    python Tools/test_melusina_skin_topology_contract.py --write-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIERARCHY = ROOT / "specs/anim_presets/melusina_contract_hierarchy.json"
SKIN_REPORT = ROOT / "Saved/Audit/melusina_v2_fbx_contract_FINAL_2026-08-15.json"
# Superseded: melusina_v2_actual_fbx_contract_report_simply_coll_2026-08-15.json, the
# pre-fix export that carried all 41 orphan bindings.
BASELINE = ROOT / "specs/melusina_skin_topology_baseline.json"

# The pelvis. Everything that deforms the character hangs off this in a sane rig.
BODY_ROOT = "root_x"


def ancestry(bone: str, parent_map: dict[str, str | None]) -> list[str]:
    """Bone -> root, cycle-safe."""
    out: list[str] = []
    seen: set[str] = set()
    cur: str | None = bone
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = parent_map.get(cur)
    return out


def collect_violations() -> tuple[list[dict], list[str]]:
    problems: list[str] = []
    if not HIERARCHY.is_file():
        problems.append(f"missing {HIERARCHY.relative_to(ROOT)}")
    if not SKIN_REPORT.is_file():
        problems.append(f"missing {SKIN_REPORT.relative_to(ROOT)}")
    if problems:
        return [], problems

    parent_map = json.loads(HIERARCHY.read_text(encoding="utf-8"))["parent_map"]
    report = json.loads(SKIN_REPORT.read_text(encoding="utf-8"))

    violations: list[dict] = []
    skinned_total = 0
    for check in report.get("checks", []):
        for mesh in check.get("meshes", []):
            for bone in mesh.get("used_deform_groups", []) or []:
                skinned_total += 1
                chain = ancestry(bone, parent_map)
                if bone not in parent_map:
                    violations.append({"mesh": mesh.get("name"), "bone": bone,
                                       "reason": "not in the 465-bone contract"})
                elif BODY_ROOT not in chain:
                    violations.append({"mesh": mesh.get("name"), "bone": bone,
                                       "reason": f"outside {BODY_ROOT}: " + " -> ".join(chain[:4])})

    if not skinned_total:
        problems.append("skin report contained no used_deform_groups - cannot validate")
    return violations, problems


def key(v: dict) -> str:
    return f"{v['mesh']}::{v['bone']}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="ignore the baseline")
    ap.add_argument("--write-baseline", action="store_true", help="record current violations as accepted debt")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    violations, problems = collect_violations()

    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "schema": "melodia.melusina_skin_topology_baseline.v1",
            "policy": ("A key here means the violation predates the gate. NEW violations fail. "
                       "Removing a key is progress; adding one needs a reason."),
            "rule": f"every skinned bone must be a descendant of '{BODY_ROOT}'",
            "accepted": sorted(key(v) for v in violations),
        }, indent=2) + "\n", encoding="utf-8")
        print(f"baseline written: {len(violations)} accepted -> {BASELINE.relative_to(ROOT)}")
        return 0

    accepted: set[str] = set()
    if BASELINE.is_file() and not args.strict:
        accepted = set(json.loads(BASELINE.read_text(encoding="utf-8")).get("accepted", []))

    new = [v for v in violations if key(v) not in accepted]

    if args.json:
        print(json.dumps({"violations": violations, "new": new,
                          "accepted": len(accepted), "problems": problems}, indent=2))
    else:
        for p in problems:
            print(f"FAIL  {p}")
        for v in new:
            print(f"FAIL  {v['mesh']}: '{v['bone']}' {v['reason']}")
        if args.strict and violations:
            print(f"\nstrict: {len(violations)} total violations "
                  f"({len(accepted)} would be baselined)")
            by_mesh: dict[str, int] = {}
            for v in violations:
                by_mesh[v["mesh"]] = by_mesh.get(v["mesh"], 0) + 1
            for m, n in sorted(by_mesh.items()):
                print(f"    {m}: {n}")
        print("validated Melusina skin topology contract")
        print(f"=== {len(violations) - len(new)}/{len(violations)} accepted, "
              f"{len(new)} new, {len(problems)} blockers ===")

    return 0 if (not new and not problems) else 1


if __name__ == "__main__":
    raise SystemExit(main())
