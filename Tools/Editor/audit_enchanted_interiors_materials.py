"""
Offline verification of the Enchanted Interiors conversion (no editor).

Checks:
  1. every stem has a material instance at /Game/EnchantedInteriors/Materials/KB3D_ECI_<Stem>
  2. each instance is parented to M_Master_Toon_Universal
  3. each instance routes the maps its stem actually has (basecolor/normal/arm/emissive/opacity)
  4. every routed texture belongs to its own stem (no cross-wiring)
  5. every material slot referenced by the 1,696 pack meshes resolves to one of those
     instances (no dangling pack-material references left behind)

Usage: python Tools/Editor/audit_enchanted_interiors_materials.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAT_DIR = ROOT / "Content" / "EnchantedInteriors" / "Materials"
TEX_DIR = ROOT / "Content" / "EnchantedInteriors" / "Textures"
GEO_DIR = ROOT / "Content" / "EnchantedInteriors" / "Geometries"
ACT_DIR = ROOT / "Content" / "EnchantedInteriors" / "Actors"
OUT = ROOT / "Saved" / "Audit" / "enchanted_interiors_audit.json"

MASTER = "M_Master_Toon_Universal"
GAME_PATH_RE = re.compile(rb"/Game/[A-Za-z0-9_\./\-]+")
MAP_SUFFIXES = ("basecolor", "normal", "arm", "ao", "metallic", "roughness",
                "height", "emissive", "opacity", "refraction")


def _paths(data: bytes) -> list[str]:
    out = []
    for m in GAME_PATH_RE.finditer(data):
        s = m.group(0).decode("ascii", "ignore").rstrip(".")
        slash, dot = s.rfind("/"), s.rfind(".")
        if dot > slash:
            s = s[:dot]
        out.append(s)
    return out


def main() -> int:
    # stems and their maps, from the textures on disk
    stems: dict[str, set[str]] = {}
    for t in TEX_DIR.glob("KB3D_ECI_*.uasset"):
        n = t.stem
        for suf in MAP_SUFFIXES:
            if n.endswith("_" + suf):
                stems.setdefault(n[: -(len(suf) + 1)], set()).add(suf)
                break

    instances = {}
    if MAT_DIR.exists():
        for f in sorted(MAT_DIR.glob("*.uasset")):
            data = f.read_bytes()
            paths = _paths(data)
            parent = None
            routed = {}
            for p in paths:
                name = p.rsplit("/", 1)[-1]
                if "/Masters/" in p:
                    parent = name
                elif name.startswith("KB3D_ECI_"):
                    for suf in MAP_SUFFIXES:
                        if name.endswith("_" + suf):
                            routed[suf] = name
                            break
            txt = data.decode("ascii", "ignore")
            instances[f.stem] = {
                "file": f.name,
                "parent": parent,
                "routed": routed,
                "blend_masked": "BLEND_Masked" in txt or "Masked" in txt,
                "uses_opacity_map": "UseOpacityMap" in txt or "use_opacity_map" in txt,
                "two_sided": "TWO_SIDED" in txt or "two_sided" in txt,
                "bytes": len(data),
            }

    rows = []
    for stem in sorted(stems):
        expected = stems[stem] - {"refraction"}
        # the stem already carries the pack's own "KB3D_ECI_" prefix, and the
        # instance is created at exactly that name (same path the pack material had)
        inst = instances.get(stem)
        row = {"stem": stem, "expected_maps": sorted(expected),
               "instance": None, "issues": []}
        if inst is None:
            row["issues"].append("NO INSTANCE")
            rows.append(row)
            continue
        row["instance"] = inst["file"]
        row["parent"] = inst["parent"]
        row["routed"] = sorted(inst["routed"])
        if inst["parent"] != MASTER:
            row["issues"].append(f"parent={inst['parent']} (want {MASTER})")
        missing = sorted(set(expected) - set(inst["routed"]))
        if missing:
            row["issues"].append(f"unrouted: {missing}")
        extra = sorted(set(inst["routed"]) - set(expected))
        if extra:
            row["issues"].append(f"unexpected routes: {extra}")
        for suf, tex in inst["routed"].items():
            if tex != f"{stem}_{suf}":   # stem already carries the KB3D_ECI_ prefix
                row["issues"].append(f"{suf} -> {tex} (wrong stem's texture)")
        rows.append(row)

    # mesh + actor material references must resolve to our instances
    inst_paths = {f"/Game/EnchantedInteriors/Materials/{n}" for n in instances}
    unresolved: dict[str, list[str]] = {}
    checked = 0
    for folder in (GEO_DIR, ACT_DIR):
        if not folder.exists():
            continue
        for f in folder.glob("*.uasset"):
            checked += 1
            for p in set(_paths(f.read_bytes())):
                if "/EnchantedInteriors/Materials/" in p:
                    if p not in inst_paths:
                        unresolved.setdefault(p, []).append(f.name)
                elif p.startswith("/Game/EnchantedInteriors/Materials"):
                    unresolved.setdefault(p, []).append(f.name)

    summary = {
        "generated": "2026-10-21",
        "stems": len(stems),
        "instances": len(instances),
        "clean": sum(1 for r in rows if not r["issues"]),
        "with_issues": sum(1 for r in rows if r["issues"]),
        "translucent_stems": sum(1 for s, m in stems.items() if "opacity" in m or "refraction" in m),
        "meshes_and_actors_checked": checked,
        "unresolved_material_refs": {k: v[:5] for k, v in list(unresolved.items())[:20]},
        "unresolved_ref_count": len(unresolved),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"summary": summary, "stems": rows}, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2)[:1600])
    print("receipt:", OUT)
    if summary["with_issues"]:
        print("--- stems with issues (first 25) ---")
        for r in [x for x in rows if x["issues"]][:25]:
            print("  ", r["stem"], "->", r["issues"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
