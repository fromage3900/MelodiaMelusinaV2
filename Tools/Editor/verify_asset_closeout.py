"""
Consolidated closeout verification for the 2026-10-21 asset work.

Runs the two offline audits and checks the end state of every decision taken:
  * the deprecated M_Master_Toon_Universal_Alpha master is gone
  * the 73 orphaned duplicate vehicle instances are gone
  * the vehicle set the meshes use is 100% on M_Master_Toon_Universal with every
    map routed
  * the Enchanted Interiors pack is in Content/, converted, and every mesh
    material slot resolves to one of the 80 converted instances
  * how much of the pack is stamped for UE 5.8 (stamped packages are NOT loaded
    by the registry scan, which is what stops the editor build storm)

Run: python Tools/Editor/verify_asset_closeout.py
Writes Saved/Audit/asset_closeout_verification.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "asset_closeout_verification.json"
STAMP = b"++UE5+Release-5.8"


def run(script: str) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "Tools" / "Editor" / script)],
                       capture_output=True, text=True, cwd=str(ROOT))
    return {"exit": p.returncode, "stdout_tail": p.stdout[-400:] if p.stdout else ""}


def stamped(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            return STAMP in fh.read(4096)
    except Exception:
        return False


def main() -> int:
    results = {}

    print("running the two audits ...")
    results["vehicle_audit"] = run("audit_enchanted_vehicle_materials.py")
    results["interiors_audit"] = run("audit_enchanted_interiors_materials.py")

    veh = ROOT / "Saved" / "Audit" / "enchanted_vehicle_materials_audit.json"
    itc = ROOT / "Saved" / "Audit" / "enchanted_interiors_audit.json"
    veh_j = json.loads(veh.read_text(encoding="utf-8")) if veh.exists() else {}
    itc_j = json.loads(itc.read_text(encoding="utf-8")) if itc.exists() else {}

    alpha = ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters" / "M_Master_Toon_Universal_Alpha.uasset"
    orphan_dir = ROOT / "Content" / "Melodia" / "Imported" / "EnchantedVehicles"
    pack = ROOT / "Content" / "EnchantedInteriors"

    pack_files = list(pack.rglob("*.uasset")) if pack.exists() else []
    pack_stamped = sum(1 for f in pack_files if stamped(f))
    mi_files = list((pack / "Materials").glob("*.uasset")) if (pack / "Materials").exists() else []
    scratch = Path(r"C:\EnvironmentPortfolio\Staging\ECI_scratch\Content\EnchantedInteriors")

    a = veh_j.get("summary", {}).get("set_A_meshfacing", {})
    b = veh_j.get("summary", {}).get("set_B_orphaned", {})
    its = itc_j.get("summary", {})

    checks = [
        {"check": "deprecated Alpha master deleted",
         "ok": not alpha.exists(), "detail": str(alpha.name)},
        {"check": "73 orphaned duplicate vehicle instances deleted",
         "ok": not orphan_dir.exists() or not list(orphan_dir.glob("*.uasset")),
         "detail": f"{len(list(orphan_dir.glob('*.uasset'))) if orphan_dir.exists() else 0} left"},
        {"check": "vehicle set A (mesh-facing) 72/72 on M_Master_Toon_Universal",
         "ok": a.get("parents", {}).get("M_Master_Toon_Universal") == 72 and a.get("count") == 72,
         "detail": json.dumps(a.get("parents", {}))},
        {"check": "vehicle set A fully routed (no needs_work)",
         "ok": a.get("status", {}).get("needs_work", 1) == 0 and a.get("count") == 72,
         "detail": json.dumps(a.get("status", {}))},
        {"check": "interiors: 80 stems / 80 instances / 0 issues",
         "ok": its.get("stems") == 80 and its.get("instances") == 80 and its.get("with_issues") == 0,
         "detail": json.dumps({k: its.get(k) for k in ("stems", "instances", "clean", "with_issues")})},
        {"check": "interiors: no unresolved material refs across the pack",
         "ok": its.get("unresolved_ref_count") == 0,
         "detail": f"{its.get('meshes_and_actors_checked', 0)} meshes+actors checked, "
                   f"{its.get('unresolved_ref_count', '?')} unresolved"},
        {"check": "interiors: the 80 converted instances are in Content/",
         "ok": len(mi_files) == 80, "detail": f"{len(mi_files)} instance files"},
        {"check": "interiors pack present in Content/",
         "ok": len(pack_files) > 0, "detail": f"{len(pack_files)} uasset files"},
        {"check": "pack stamped for UE 5.8 (stamped packages are not loaded by the scan)",
         "ok": pack_stamped == len(pack_files) and pack_stamped > 0,
         "detail": f"{pack_stamped}/{len(pack_files)} stamped"},
        {"check": "two 7.7 GB meshes still staged out of Content/",
         "ok": all(n not in {f.name for f in pack_files} for n in
                   ("KB3D_ECI_IntNecromancersLair_A_NicheA.uasset",
                    "KB3D_ECI_IntNecromancersLair_A_NicheC.uasset")),
         "detail": "they need the raised pagefile before they can be built"},
    ]

    report = {
        "generated": "2026-10-21",
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "total": len(checks),
        "all_ok": all(c["ok"] for c in checks),
        "scratch_remaining_files": len(list(scratch.rglob("*.uasset"))) if scratch.exists() else 0,
        "audit_exits": {k: v["exit"] for k, v in results.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print()
    for c in checks:
        print(("  PASS  " if c["ok"] else "  FAIL  ") + c["check"] + "  --  " + str(c["detail"]))
    print(f"\n{report['passed']}/{report['total']} checks passed -> {OUT}")
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
