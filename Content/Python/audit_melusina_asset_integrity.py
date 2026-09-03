"""Thin Melusina path-ref integrity pass (disk / no editor).

Scopes:
  Content/Characters/Melusina
  Content/Melodia/Characters/Melusina

Pattern: same /Game/... null-terminated path extraction as audit_material_library.py.
Read-only: writes Saved/Audit/melusina_asset_integrity.json only.
Does NOT mutate Melusina shaders, materials, or stage blends.

Run:
  python Content/Python/audit_melusina_asset_integrity.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "Content"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "melusina_asset_integrity.json"

TREES = (
    CONTENT_ROOT / "Characters" / "Melusina",
    CONTENT_ROOT / "Melodia" / "Characters" / "Melusina",
)

CRITICAL_STEMS = (
    "SK_Melusina",
    "BP_Melusina",
    "ABP_Melusina",
    "ABP_Melusina_Current",
)

PATH_RE = re.compile(rb"(/Game/[A-Za-z0-9_./-]+)\x00")
MATERIAL_PREFIX = re.compile(r"^(M_|MI_|MF_|TP_)", re.I)
TEXTURE_NAME = re.compile(
    r"^(T_|Marble_|Perlin_|Voronoi_|Noise_|SDF_)", re.I
)


def asset_game_path(uasset: Path) -> str:
    rel = uasset.relative_to(CONTENT_ROOT).with_suffix("")
    return "/Game/" + rel.as_posix()


def extract_paths(data: bytes) -> set[str]:
    return {m.group(1).decode("ascii", "ignore") for m in PATH_RE.finditer(data)}


def resolve_on_disk(game_path: str) -> Path | None:
    if not game_path.startswith("/Game/"):
        return None
    candidate = CONTENT_ROOT / (game_path.removeprefix("/Game/") + ".uasset")
    return candidate if candidate.exists() else None


def is_texture_ref(ref: str) -> bool:
    name = ref.rsplit("/", 1)[-1]
    return (
        "/Textures/" in ref
        or TEXTURE_NAME.match(name) is not None
        or name.startswith("T_")
    )


def is_material_like_ref(ref: str) -> bool:
    name = ref.rsplit("/", 1)[-1]
    return MATERIAL_PREFIX.match(name) is not None


def scan_tree(root: Path) -> dict:
    if not root.exists():
        return {
            "root": str(root),
            "exists": False,
            "uasset_count": 0,
            "material_count": 0,
            "texture_count": 0,
            "critical_present": {},
            "missing_refs": [],
            "missing_texture_refs": [],
            "missing_material_refs": [],
            "critical_missing_refs": [],
        }

    uassets: dict[str, Path] = {}
    materials: list[str] = []
    textures: list[str] = []
    for p in root.rglob("*.uasset"):
        ap = asset_game_path(p)
        uassets[ap] = p
        stem = p.stem
        if MATERIAL_PREFIX.match(stem):
            materials.append(ap)
        if TEXTURE_NAME.match(stem) or "/textures/" in str(p).lower():
            textures.append(ap)

    critical_present: dict[str, list[str]] = {}
    for stem in CRITICAL_STEMS:
        hits = [ap for ap in uassets if Path(ap).name == stem or Path(ap).name.startswith(stem)]
        critical_present[stem] = sorted(hits)

    missing_refs: list[dict[str, str]] = []
    missing_texture_refs: list[dict[str, str]] = []
    missing_material_refs: list[dict[str, str]] = []
    critical_missing_refs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for ap, p in uassets.items():
        try:
            data = p.read_bytes()
        except OSError:
            continue
        is_critical_source = any(
            Path(ap).name == stem or Path(ap).name.startswith(stem)
            for stem in CRITICAL_STEMS
        ) or MATERIAL_PREFIX.match(Path(ap).name) is not None
        for ref in extract_paths(data):
            if ref == ap:
                continue
            if resolve_on_disk(ref) is not None:
                continue
            key = (ap, ref)
            if key in seen:
                continue
            seen.add(key)
            row = {"source": ap, "target": ref}
            missing_refs.append(row)
            if is_texture_ref(ref):
                missing_texture_refs.append(row)
            if is_material_like_ref(ref):
                missing_material_refs.append(row)
            if is_critical_source and (is_texture_ref(ref) or is_material_like_ref(ref)):
                critical_missing_refs.append(row)

    return {
        "root": str(root),
        "exists": True,
        "uasset_count": len(uassets),
        "material_count": len(materials),
        "texture_count": len(textures),
        "materials": sorted(materials),
        "textures": sorted(textures),
        "critical_present": critical_present,
        "missing_refs": missing_refs,
        "missing_texture_refs": missing_texture_refs,
        "missing_material_refs": missing_material_refs,
        "critical_missing_refs": critical_missing_refs,
        "missing_ref_count": len(missing_refs),
        "missing_texture_ref_count": len(missing_texture_refs),
        "missing_material_ref_count": len(missing_material_refs),
        "critical_missing_ref_count": len(critical_missing_refs),
    }


def pass_fail(trees: list[dict]) -> dict:
    """Pass if both trees exist, critical assets present, zero critical mat/tex missing refs."""
    reasons: list[str] = []
    for t in trees:
        label = Path(t["root"]).as_posix()
        if not t.get("exists"):
            reasons.append(f"missing tree: {label}")
            continue
        if t.get("uasset_count", 0) == 0:
            reasons.append(f"empty tree: {label}")
        crit = t.get("critical_present") or {}
        # Melodia tree is the richer copy; Characters tree may lack some names.
        # Require at least SK_Melusina somewhere in each existing tree that has meshes.
        sk = crit.get("SK_Melusina") or []
        if not sk and t.get("uasset_count", 0) > 0:
            # soft: note only if no skeletal mesh named Melusina at all
            any_sk = any("SK_Melusina" in ap for ap in (t.get("materials") or []))
            if not any_sk:
                # check via critical_present empty lists
                if not any(crit.get(s) for s in ("SK_Melusina", "BP_Melusina")):
                    reasons.append(f"no SK/BP Melusina under {label}")
        if t.get("critical_missing_ref_count", 0) > 0:
            reasons.append(
                f"{t['critical_missing_ref_count']} critical mat/tex missing refs in {label}"
            )
    return {
        "pass": len(reasons) == 0,
        "reasons": reasons,
    }


def print_report(report: dict) -> None:
    print("=" * 60)
    print("Melusina Asset Integrity (disk path-ref)")
    print("=" * 60)
    for t in report["trees"]:
        print(f"\n{t['root']}")
        print(f"  exists={t.get('exists')} uassets={t.get('uasset_count', 0)} "
              f"mats={t.get('material_count', 0)} tex={t.get('texture_count', 0)}")
        print(f"  missing_refs={t.get('missing_ref_count', 0)} "
              f"missing_tex={t.get('missing_texture_ref_count', 0)} "
              f"missing_mat={t.get('missing_material_ref_count', 0)} "
              f"critical_missing={t.get('critical_missing_ref_count', 0)}")
        for stem, hits in (t.get("critical_present") or {}).items():
            print(f"  {stem}: {len(hits)} -> {hits[:3]}")
        for row in (t.get("critical_missing_refs") or [])[:10]:
            print(f"  CRITICAL {row['source'].rsplit('/', 1)[-1]} -> {row['target']}")
    verdict = report["verdict"]
    print(f"\nVERDICT: {'PASS' if verdict['pass'] else 'FAIL'}")
    for r in verdict.get("reasons") or []:
        print(f"  - {r}")
    print(f"\nReport: {REPORT_PATH}")


def main() -> int:
    trees = [scan_tree(root) for root in TREES]
    verdict = pass_fail(trees)
    report = {
        "scope": [str(t) for t in TREES],
        "stop_flags_honored": True,
        "trees": trees,
        "totals": {
            "uasset_count": sum(t.get("uasset_count", 0) for t in trees),
            "material_count": sum(t.get("material_count", 0) for t in trees),
            "texture_count": sum(t.get("texture_count", 0) for t in trees),
            "missing_ref_count": sum(t.get("missing_ref_count", 0) for t in trees),
            "missing_texture_ref_count": sum(
                t.get("missing_texture_ref_count", 0) for t in trees
            ),
            "missing_material_ref_count": sum(
                t.get("missing_material_ref_count", 0) for t in trees
            ),
            "critical_missing_ref_count": sum(
                t.get("critical_missing_ref_count", 0) for t in trees
            ),
        },
        "verdict": verdict,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print_report(report)
    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
