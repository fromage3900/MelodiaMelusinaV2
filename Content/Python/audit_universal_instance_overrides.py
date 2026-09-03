"""Stage-0 gate for the M_Master_Toon_Universal professional trim
(Docs/Production/UNIVERSAL_MASTER_NODE_REVIEW.md plan, approved 2026-07-03).

Scans every MaterialInstanceConstant parented (directly or transitively) to
M_Master_Toon_Universal and reports:

  1. REMOVAL BLOCKERS -- instances that override any parameter in the
     to-be-removed families (Madoka*, Itto*, SkinWrap*, Character
     skin/hair/eye params) with a non-neutral value. These get reported to
     the user BEFORE removal; nothing is silently changed.
  2. GATE USERS -- instances with non-neutral values in the families that
     Stage 2 puts behind new static switches (Celestial, Weather, Sparkle,
     FairyDust, Henshin). These instances need their gate flipped ON when
     the switches land, so their look is preserved.

Modeled on audit_material_parameters.py / sync_all_material_instances.py.
Read-only: no saves, no mutations.

Run inside the editor (Monolith run_python):
  import audit_universal_instance_overrides as a
  a.run()
"""
from __future__ import annotations

import fnmatch
import json
import os

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT_PATH = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\universal_instance_overrides.json"

# Families slated for removal (Stage 3). Patterns match parameter names.
REMOVAL_PATTERNS = [
    "Madoka*", "Itto*", "SkinWrap*",
    # Character family (skin/hair/eyes) -- names from the family inventory
    "Skin*", "Hair*", "Eye*", "Cheek*",
]
# Families that get Stage-2 switches; non-neutral use here => flip gate ON.
GATE_FAMILIES = {
    "bCelestial_Active": ["Galaxy*", "Nebula*", "Constellation*", "Star*", "Cosmic*", "Celestial*"],
    "bWeather_Active": ["Moss*", "Snow*", "Wet*"],
    "bSparkle_Active": ["Sparkle*"],
    "bFairyDust_Active": ["Fairy*"],
    "bHenshin_Active": ["Henshin*", "Motif*", "Wipe*"],
}


def _matches(name: str, patterns) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def _master_chain(inst) -> bool:
    """True if inst's parent chain reaches the master."""
    import unreal
    seen = 0
    p = inst.get_editor_property("parent")
    while p is not None and seen < 8:
        if p.get_path_name().split(".")[0] == MASTER:
            return True
        p = p.get_editor_property("parent") if isinstance(p, unreal.MaterialInstanceConstant) else None
        seen += 1
    return False


def run() -> dict:
    import unreal

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True)

    report = {"master": MASTER, "instances_scanned": 0,
              "removal_blockers": {}, "gate_users": {}, "errors": []}

    for ad in assets:
        pkg = str(ad.package_name)
        if not pkg.startswith("/Game/"):
            continue
        try:
            inst = unreal.EditorAssetLibrary.load_asset(pkg)
        except Exception:
            continue
        if inst is None or not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        if not _master_chain(inst):
            continue
        report["instances_scanned"] += 1

        overridden = []
        for sp in inst.get_editor_property("scalar_parameter_values"):
            overridden.append((str(sp.get_editor_property("parameter_info").get_editor_property("name")),
                               float(sp.get_editor_property("parameter_value"))))
        for vp in inst.get_editor_property("vector_parameter_values"):
            overridden.append((str(vp.get_editor_property("parameter_info").get_editor_property("name")), "vector"))

        blockers = [(n, v) for n, v in overridden
                    if _matches(n, REMOVAL_PATTERNS)
                    and not (isinstance(v, float) and abs(v) < 1e-4)]
        if blockers:
            report["removal_blockers"][pkg] = blockers

        for gate, pats in GATE_FAMILIES.items():
            hits = [(n, v) for n, v in overridden
                    if _matches(n, pats)
                    and not (isinstance(v, float) and abs(v) < 1e-4)]
            if hits:
                report["gate_users"].setdefault(gate, {})[pkg] = hits

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"scanned {report['instances_scanned']} universal-parented instances")
    print(f"removal blockers: {len(report['removal_blockers'])} instance(s)")
    for pkg, b in report["removal_blockers"].items():
        print("  BLOCKER:", pkg, "->", b[:6])
    for gate, users in report["gate_users"].items():
        print(f"gate {gate}: {len(users)} instance(s) need it ON")
    print("full report:", OUT_PATH)
    return report


if __name__ == "__main__":
    run()
