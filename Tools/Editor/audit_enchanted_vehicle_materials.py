"""
Audit the enchanted-vehicle material sets (offline, no editor).

Now that the un-smudged LFS pointer stubs are restored, both sets are readable:
  A) /Game/KitBash_EnchantedVehicles/M_KB3D_ECV_<Stem>   (72) - referenced by the 172 vehicle meshes
  B) /Game/Melodia/Imported/EnchantedVehicles/MI_KB3D_ECV_<Stem> (73) - referenced by nothing

For each instance: parent master, routed texture maps, expected maps for the stem,
and whether the routed texture is the stem's own map.

Usage: python Tools/Editor/audit_enchanted_vehicle_materials.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SET_A = ROOT / "Content" / "KitBash_EnchantedVehicles"        # M_KB3D_ECV_*  (mesh-facing)
SET_B = ROOT / "Content" / "Melodia" / "Imported" / "EnchantedVehicles"  # MI_KB3D_ECV_*
TEX_DIR = ROOT / "Content" / "KitBash_EnchantedVehicles"
OUT = ROOT / "Saved" / "Audit" / "enchanted_vehicle_materials_audit.json"

MASTER_UNIVERSAL = "M_Master_Toon_Universal"
MASTER_ALPHA = "M_Master_Toon_Universal_Alpha"

MAP_SUFFIXES = ("basecolor", "normal", "roughness", "metallic", "height",
                "ao", "orm", "emissive", "opacity", "refraction")

GAME_PATH_RE = re.compile(rb"/Game/[A-Za-z0-9_\./\-]+")


def _strings(data: bytes) -> list[str]:
    out = []
    for m in GAME_PATH_RE.finditer(data):
        s = m.group(0).decode("ascii", "ignore").rstrip(".")
        slash, dot = s.rfind("/"), s.rfind(".")
        if dot > slash:
            s = s[:dot]
        out.append(s)
    return out


def _stem(mi_name: str) -> str:
    s = mi_name
    if s.startswith("MI_"):
        s = s[3:]
    if s.startswith("M_"):
        s = s[2:]
    for suf in ("_Toon",):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s


def _audit_file(path: Path) -> dict:
    data = path.read_bytes()
    paths = _strings(data)
    textures, parents = [], []
    for p in sorted(set(paths)):
        name = p.rsplit("/", 1)[-1]
        if "/KitBash_EnchantedVehicles/" in p and name.startswith("KB3D_ECV_"):
            textures.append(p)
        elif "/Masters/" in p:
            parents.append(p)

    routed = {}
    for t in textures:
        name = t.rsplit("/", 1)[-1]
        for suf in MAP_SUFFIXES:
            if name.endswith("_" + suf):
                routed[suf] = t.rsplit("/", 1)[-1]
                break

    txt = data.decode("ascii", "ignore")
    row = {
        "file": path.name,
        "folder": path.parent.name,
        "stem": _stem(path.stem),
        "parent": parents[0].rsplit("/", 1)[-1] if parents else None,
        "parent_refs": sorted({p.rsplit("/", 1)[-1] for p in parents}),
        "routed_maps": sorted(routed),
        "routed_detail": routed,
        "bytes": len(data),
        "blend_masked": "BLEND_Masked" in txt,
        "two_sided": "TWO_SIDED" in txt,
        "uses_opacity_map": "bUseOpacityMap" in txt,
        "has_weight_param": "LayerA_TextureWeight" in txt,
        "has_shadowdream": "ShadowDreamStrength" in txt,
    }
    return row


def main() -> int:
    # texture availability per stem
    tex_by_stem: dict[str, set[str]] = {}
    for t in TEX_DIR.glob("KB3D_ECV_*.uasset"):
        n = t.stem
        for suf in MAP_SUFFIXES:
            if n.endswith("_" + suf):
                tex_by_stem.setdefault(n[: -(len(suf) + 1)], set()).add(suf)
                break

    sets = {}
    for label, folder, prefix in (("A_meshfacing", SET_A, "M_"), ("B_orphaned", SET_B, "MI_")):
        rows = []
        if folder.exists():
            for f in sorted(folder.glob(f"{prefix}KB3D_ECV*.uasset")):
                rows.append(_audit_file(f))
        for r in rows:
            avail = tex_by_stem.get(r["stem"], set())
            r["expected_maps"] = sorted(avail - {"refraction"})
            r["missing_maps"] = sorted(set(r["expected_maps"]) - set(r["routed_maps"]))
            r["unexpected_maps"] = sorted(set(r["routed_maps"]) - set(r["expected_maps"]))
            wrong = {k: v for k, v in r["routed_detail"].items()
                     if v != f"{r['stem']}_{k}"}   # stem already carries the KB3D_ECV_ prefix
            r["wrong_texture_for_stem"] = wrong
            r["parent_ok"] = r["parent"] == MASTER_UNIVERSAL
            r["needs_alpha_look"] = ("opacity" in avail) or ("refraction" in avail)
            r["status"] = (
                "ok" if r["parent_ok"] and not r["missing_maps"] and not wrong
                else "needs_work")
        sets[label] = rows

    a_by_stem = {r["stem"]: r for r in sets["A_meshfacing"]}
    b_by_stem = {r["stem"]: r for r in sets["B_orphaned"]}
    overlap = sorted(set(a_by_stem) & set(b_by_stem))
    divergent = []
    for stem in overlap:
        a, b = a_by_stem[stem], b_by_stem[stem]
        diffs = {}
        for key in ("parent", "routed_maps", "blend_masked", "two_sided",
                    "uses_opacity_map", "missing_maps"):
            if a.get(key) != b.get(key):
                diffs[key] = {"A": a.get(key), "B": b.get(key)}
        if diffs:
            divergent.append({"stem": stem, "diffs": diffs})

    summary = {
        "generated": "2026-10-21",
        "set_A_meshfacing": {
            "path": str(SET_A.relative_to(ROOT)).replace("\\", "/"),
            "count": len(sets["A_meshfacing"]),
            "parents": {},
            "status": {},
        },
        "set_B_orphaned": {
            "path": str(SET_B.relative_to(ROOT)).replace("\\", "/"),
            "count": len(sets["B_orphaned"]),
            "parents": {},
            "status": {},
        },
        "stems_only_in_A": sorted(set(a_by_stem) - set(b_by_stem)),
        "stems_only_in_B": sorted(set(b_by_stem) - set(a_by_stem)),
        "A_vs_B_divergent": divergent,
        "duplicate_stem_instances": {},
    }
    for label in ("set_A_meshfacing", "set_B_orphaned"):
        for r in sets["A_meshfacing" if label.endswith("A_meshfacing") else "B_orphaned"]:
            summary[label]["parents"][str(r["parent"])] = \
                summary[label]["parents"].get(str(r["parent"]), 0) + 1
            summary[label]["status"][r["status"]] = \
                summary[label]["status"].get(r["status"], 0) + 1

    for label in ("A_meshfacing", "B_orphaned"):
        seen: dict[str, list[str]] = {}
        for r in sets[label]:
            seen.setdefault(r["stem"], []).append(r["file"])
        summary["duplicate_stem_instances"][label] = {k: v for k, v in seen.items() if len(v) > 1}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"summary": summary, "instances": sets}, indent=2), encoding="utf-8")

    print("set A (mesh-facing) :", summary["set_A_meshfacing"]["count"],
          "parents:", summary["set_A_meshfacing"]["parents"], "status:", summary["set_A_meshfacing"]["status"])
    print("set B (orphaned)    :", summary["set_B_orphaned"]["count"],
          "parents:", summary["set_B_orphaned"]["parents"], "status:", summary["set_B_orphaned"]["status"])
    print("stems only in A:", summary["stems_only_in_A"])
    print("stems only in B:", summary["stems_only_in_B"])
    print("duplicates A:", summary["duplicate_stem_instances"]["A_meshfacing"])
    print("duplicates B:", summary["duplicate_stem_instances"]["B_orphaned"])
    print(f"A vs B divergent stems: {len(divergent)}")
    for d in divergent[:25]:
        print("   ", d["stem"], "->", json.dumps(d["diffs"]))
    print("receipt:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
