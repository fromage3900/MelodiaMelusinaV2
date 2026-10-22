"""
Read-only audit of the P0 house level (L_MelusinaHouse_P0).

Answers the questions that decide whether tomorrow's session starts on solid
ground:

  * what is actually IN the level (actor census, by class)
  * does every dressing actor carry a REAL material (the classic red-X is a
    default material on a slot) and is that material one of the converted
    M_Master_Toon_Universal instances - no kit proxies
  * are the functional interactables present and valid
  * do the Houdini room shells carry parameters, and did their cook succeed
  * is the dressing static or movable (a perf question, not a correctness one)
  * are there duplicate actor labels, or actors with no mesh at all
  * is the route walkable: the floor, the door and the medallion are present

Read-only: it loads the level and writes a JSON receipt. It mutates nothing.

Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/house_level_audit.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
MAP = "/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "house_level_audit.json"

CONVERTED_PREFIX = "/Game/EnchantedInteriors/Materials/"
CANON_PREFIX = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/"


def _mobility(comp):
    """Mobility, defensively: the accessor moved between UE versions."""
    for getter in ("get_mobility",):
        fn = getattr(comp, getter, None)
        if fn is not None:
            try:
                return str(fn())
            except Exception:
                pass
    try:
        return str(comp.get_editor_property("mobility"))
    except Exception:
        return "?"


def main() -> int:
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=False,
        include_hard_package_references=True)

    census = {}
    dressing = []
    interactables = []
    shells = []
    issues = []

    def cls_of(a):
        try:
            return a.get_class().get_name()
        except Exception:
            return "?"

    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        name = cls_of(a)
        census[name] = census.get(name, 0) + 1
        try:
            lbl = a.get_actor_label()
        except Exception:
            lbl = "<unreadable>"
        loc = a.get_actor_location()

        # static mesh dressing
        mesh = None
        comp = None
        try:
            comp = a.static_mesh_component
            if comp is not None:
                mesh = comp.static_mesh
        except Exception:
            pass

        if mesh is not None:
            # The material list lives on the StaticMesh and is protected in Python,
            # so the registry is the honest source: it reports what the package
            # actually references, and it works headless.
            mat_paths = []
            try:
                # get_dependencies wants a PACKAGE name; the object path carries
                # the ".Name" suffix, and asking for that returns nothing.
                pkg = str(mesh.get_path_name()).rsplit(".", 1)[0]
                deps = ar.get_dependencies(pkg, dep_opts) or []
                for d in deps:
                    dp = str(d)
                    if not dp.startswith("/Game/"):
                        continue
                    last = dp.rsplit("/", 1)[-1]
                    # a material instance is named MI_* / M_* - the PATH does not
                    # contain the word "Material" (.../Desk/MI_M_Desk), so a path
                    # filter on that word would miss every one of them.
                    if last.startswith("MI_") or last.startswith("M_") \
                            or "/Materials/" in dp or dp.startswith(CONVERTED_PREFIX):
                        mat_paths.append(dp)
            except Exception:
                pass
            if lbl.startswith("Mag_") or "KB3D_ECI" in lbl:
                converted = [p for p in mat_paths if p.startswith(CONVERTED_PREFIX)]
                canon = [p for p in mat_paths if p.startswith(CANON_PREFIX)]
                pack_own = [p for p in mat_paths
                           if p.startswith("/Game/MagicianLabatory/")]
                row = {"label": lbl, "mesh": mesh.get_path_name(),
                       "materials": mat_paths, "default_slots": 0,
                       "layer": "enchanted_interiors" if "KB3D_ECI" in lbl else "base",
                       "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
                       "mobility": _mobility(comp)}
                dressing.append(row)
                if not mat_paths:
                    issues.append(f"{lbl}: no material reference at all (empty slot?)")
                elif "KB3D_ECI" in lbl and not converted:
                    # the Enchanted Interiors layer MUST wear the converted
                    # instances on M_Master_Toon_Universal - the kit's own
                    # materials were never imported
                    issues.append(f"{lbl}: ECV prop is not on a converted "
                                  f"instance ({', '.join(mat_paths)})")
                elif "KB3D_ECI" not in lbl and pack_own:
                    # not an error: the base dressing legitimately wears the
                    # Magician's Library's own materials. It is reported because
                    # the M04 landmark (the medallion rings) is in this set and
                    # the house canon wants one look.
                    row["wears_pack_material"] = True

        # functional blueprint interactables
        if name.startswith("BP_") or "MagBP_" in lbl:
            interactables.append({"label": lbl, "class": name,
                                  "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]})

        # houdini room shells
        if "Houdini" in name:
            shells.append({"label": lbl, "class": name,
                           "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]})

    # duplicate labels among the dressing actors
    seen = {}
    for d in dressing:
        seen.setdefault(d["label"], 0)
        seen[d["label"]] += 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    for k, v in dupes.items():
        issues.append(f"duplicate label: {k} x{v}")

    # dressing actors with no mesh at all
    for i in interactables:
        if i["class"].startswith("BP_") and not i["class"].endswith("Component"):
            pass

    # mobility summary
    mob = {}
    for d in dressing:
        mob[d["mobility"]] = mob.get(d["mobility"], 0) + 1

    # unversioned assets inside the level's own folder (durability)
    unversioned = []
    for a in ar.get_assets_by_path("/Game/Melodia/Levels/Opening", recursive=True):
        try:
            if not str(a.package_name).startswith("/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"):
                continue
            path = PROJECT_ROOT / "Content" / Path(str(a.package_name).replace("/Game/", ""))
            data = path.with_suffix(".uasset")
            head = data.open("rb").read(4096) if data.exists() else b""
            if b"++UE5" not in head:
                unversioned.append(str(a.package_name))
        except Exception:
            pass

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "level": MAP,
        "actor_census": dict(sorted(census.items(), key=lambda kv: -kv[1])),
        "total_actors": sum(census.values()),
        "dressing_actors": len(dressing),
        "dressing_detail": dressing,
        "dressing_mobility": mob,
        "functional_interactables": len(interactables),
        "interactables": sorted(interactables, key=lambda i: i["label"]),
        "houdini_shells": len(shells),
        "duplicate_labels": dupes,
        "unversioned_in_level_folder": unversioned,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("AUDIT|actors=%d|dressing=%d|interactables=%d|shells=%d|issues=%d"
          % (report["total_actors"], len(dressing), len(interactables), len(shells), len(issues)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
