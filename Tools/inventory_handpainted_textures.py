"""Channel-suffix inventory of owner handpainted maps. No copies. No bpy/UE."""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
OUT_JSON = AUDIT / "handpainted_texture_inventory_2026-08-12.json"
OUT_MD = AUDIT / "handpainted_texture_inventory_2026-08-12.md"
SAMPLE_CAP = 80
TOTAL_SAMPLE_CAP = 400

ROOTS = [
    Path(r"G:\MelodiaMelusina"),
    Path(r"G:\MelusinaRigFinalSeparate"),
    ROOT / "Imports",
    ROOT / "Content" / "Melodia" / "Characters" / "Melusina" / "Textures",
    ROOT / "Content" / "Textures",
    ROOT / "Content" / "Greybox_Kit",
    ROOT / "Content" / "EnvSandbox" / "Greybox_Kit",
    ROOT / "Products",
    Path(r"F:\Library"),
]

SKIP_DIR = {
    ".git", "Intermediate", "Saved", "DerivedDataCache", "node_modules",
    "__pycache__", "generated", "_github_deploy", "my-site-clean",
    "Binaries", "Build", ".vs",
    "Brushify - Floating Islands", "Brushify_-_Floating_Islands",
}
SKIP_NAME_SUB = ("komikaze", "sculpt_zenlantern", "cross_hero_", "cross_void_")
EXTS = {".png", ".tga", ".tif", ".tiff", ".exr", ".psd", ".spp", ".bmp", ".jpg", ".jpeg", ".uasset"}
CHANNEL_RE = re.compile(
    r"(basecolor|albedo|diffuse|_normal|_roughness|_metallic|_height|"
    r"displacement|emission|emissive|_orm|handpaint|hand.?paint|"
    r"base.?color|normal.?map|roughness.?map)",
    re.I,
)
CROSS_RE = re.compile(r"(vow.?cross|stylizedcross|crossprop|(^|[/\\_])cross([/\\_.]|$))", re.I)
HATCH_RE = re.compile(r"hatch.?cross", re.I)
LANTERN_RE = re.compile(r"(lantern|kasuga|ishidoro|zen.?lantern|stone.?lantern)", re.I)
WAND_RE = re.compile(r"(wand|fairy.?wand)", re.I)
CHAR_DIR_RE = re.compile(
    r"(melusinafinalrig|melusinabody|actualcompiled|characters[/\\]melusina|"
    r"melusinatextures|melusina_clothes|/melusina/)",
    re.I,
)
CHAR_FILE_RE = re.compile(
    r"(melusina|m_shawl|m_skirt|m_sleeve|m_bow|m_glove|frontpanel|iris|"
    r"t_melusinac_|shirttextured)",
    re.I,
)
TRIM_RE = re.compile(r"zentrim", re.I)
MARKET_RE = re.compile(r"(magicianslibrary|quaternius|_thirdparty|marketplace|brushify)", re.I)
TOKEN_RE = re.compile(r"(melody.?token|melodsy.?token|melodsytoken)", re.I)
TILEABLE_RE = re.compile(r"(melusinatilable|tileable|floralbrick|hybtrimsheet|interiortrimsheet)", re.I)
STRIP_ROOTS = (
    r"g:\melodiamelusina",
    r"g:\melusinarigfinalseparate",
)


def classify(path: Path) -> str:
    blob = str(path).replace("\\", "/").lower()
    name = path.name.lower()
    rel = blob
    for prefix in STRIP_ROOTS:
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
            break
    if MARKET_RE.search(blob):
        return "marketplace_migrated"
    if HATCH_RE.search(name):
        return "false_friend_hatch"
    if TRIM_RE.search(name) or TRIM_RE.search(blob):
        return "trimsheet"
    if TOKEN_RE.search(name) or TOKEN_RE.search(rel):
        return "prop_token"
    if TILEABLE_RE.search(rel) or TILEABLE_RE.search(name):
        return "tileable"
    if CROSS_RE.search(rel) or CROSS_RE.search(name):
        return "prop_cross"
    if LANTERN_RE.search(rel) or LANTERN_RE.search(name):
        return "prop_lantern"
    if WAND_RE.search(rel) or WAND_RE.search(name):
        return "prop_wand"
    if CHAR_FILE_RE.search(name) or CHAR_DIR_RE.search(rel):
        return "character"
    if path.suffix.lower() == ".spp":
        return "substance_source"
    return "other_hero"


def is_hit(path: Path) -> bool:
    name = path.name.lower()
    if any(s in name for s in SKIP_NAME_SUB):
        return False
    ext = path.suffix.lower()
    if ext not in EXTS:
        return False
    if ext in {".spp", ".psd"}:
        return True
    if ext == ".uasset" and not CHANNEL_RE.search(name):
        return False
    if ext in {".jpg", ".jpeg", ".bmp"} and not CHANNEL_RE.search(name):
        return False
    return bool(CHANNEL_RE.search(name) or ext in {".tga", ".tif", ".tiff", ".exr"})


def walk_root(root: Path) -> list[dict]:
    hits: list[dict] = []
    if not root.exists():
        return hits
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR and not d.startswith(".")]
        low = dirpath.lower().replace("\\", "/")
        if any(s in low for s in ("/generated/", "/_github_deploy/", "/my-site-clean/")):
            dirnames[:] = []
            continue
        for fn in filenames:
            p = Path(dirpath) / fn
            if not is_hit(p):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            hits.append({
                "path": str(p),
                "name": p.name,
                "ext": p.suffix.lower(),
                "bytes": st.st_size,
                "class": classify(p),
            })
    return hits


def main() -> None:
    by_class: dict[str, list[dict]] = defaultdict(list)
    missing_roots = []
    scanned = []
    for root in ROOTS:
        if not root.exists():
            missing_roots.append(str(root))
            continue
        scanned.append(str(root))
        for hit in walk_root(root):
            by_class[hit["class"]].append(hit)

    counts = {k: len(v) for k, v in sorted(by_class.items(), key=lambda kv: -len(kv[1]))}
    samples: dict[str, list[dict]] = {}
    remaining = TOTAL_SAMPLE_CAP
    for cls, rows in by_class.items():
        rows_sorted = sorted(rows, key=lambda r: -r["bytes"])
        take = min(SAMPLE_CAP, remaining, len(rows_sorted))
        samples[cls] = [
            {"path": r["path"], "bytes": r["bytes"], "ext": r["ext"]}
            for r in rows_sorted[:take]
        ]
        remaining -= take

    spp_all = [h for rows in by_class.values() for h in rows if h["ext"] == ".spp"]
    spp_all = sorted(spp_all, key=lambda r: -r["bytes"])

    three_hero = [
        {
            "hero": "StylizedCrossProp",
            "named_basecolor": None,
            "wire": r"G:\MelodiaMelusina\MELUSINATILEABLE TEXTURES\bricks\floralbrickgreayscale\Untitled material\Untitled material_BaseColor.png",
            "alt": r"/Game/Textures/ZenTrim_Base4K_BaseColor",
            "do_not_use": "T_Hatch_Cross",
        },
        {
            "hero": "ZenLantern",
            "named_basecolor": None,
            "wire": r"C:\EnvironmentPortfolio\BS_GodFile\Content\Greybox_Kit\SM_SM_StreetLamp_fbm\ZenTrim_Base4K_BaseColor.uasset",
            "alt": r"C:\EnvironmentPortfolio\BS_GodFile\Content\Textures\ZenTrim_Base4K_BaseColor.uasset",
            "do_not_use": "Magicians T_Lantern_*",
        },
        {
            "hero": "StylizedMagicalWand",
            "named_basecolor": None,
            "wire": r"C:\EnvironmentPortfolio\BS_GodFile\Content\Textures\ZenTrim_Base4K_BaseColor.uasset",
            "alt": r"G:\MelodiaMelusina\MELUSINATILEABLE TEXTURES\crystal\crystal_BaseColor.png",
            "mesh": r"C:\EnvironmentPortfolio\BS_GodFile\Content\Greybox_Kit\SM_Retopo_wand.fbx",
        },
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "inventory_only_no_copies",
        "scanned_roots": scanned,
        "missing_roots": missing_roots,
        "counts": counts,
        "total_hits": sum(counts.values()),
        "three_hero": three_hero,
        "samples": samples,
        "substance_projects": [
            {"path": r["path"], "bytes": r["bytes"], "class": r["class"]}
            for r in spp_all[:60]
        ],
        "notes": [
            "Channel-suffix hunt, not SKU filename match.",
            "Komikaze stills skipped. Magicians Library / Brushify classified marketplace_migrated.",
            "T_Hatch_Cross classified false_friend_hatch.",
            "G:\\MelodiaMelusina in the path is not enough to classify as character.",
        ],
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Handpainted texture inventory — 2026-08-12",
        "",
        "Channel-suffix disk hunt. Komikaze plates excluded. No copies (G: nearly full).",
        "",
        f"**Total hits:** {payload['total_hits']}",
        "",
        "| Class | Count |",
        "|-------|------:|",
    ]
    for k, n in counts.items():
        lines.append(f"| {k} | {n} |")
    named_prop = sum(counts.get(k, 0) for k in ("prop_cross", "prop_lantern", "prop_wand"))
    lines.append(f"| prop_cross / prop_lantern / prop_wand | {named_prop} named files |")
    lines += [
        "",
        "## Three hero props — real map paths (no SKU-named BaseColor)",
        "",
        "Komikaze plates are stills. These are the owner maps to wire.",
        "",
        "| Hero | Named `*_BaseColor` on disk | Real map path to use |",
        "|------|-----------------------------|----------------------|",
        "| StylizedCrossProp | none | `G:\\MelodiaMelusina\\MELUSINATILEABLE TEXTURES\\bricks\\floralbrickgreayscale\\Untitled material\\Untitled material_BaseColor.png` or `/Game/Textures/ZenTrim_Base4K_BaseColor`. Not `T_Hatch_Cross`. |",
        "| ZenLantern | none | `C:\\EnvironmentPortfolio\\BS_GodFile\\Content\\Greybox_Kit\\SM_SM_StreetLamp_fbm\\ZenTrim_Base4K_BaseColor.uasset` plus `Content\\Textures\\ZenTrim_Base4K_{BaseColor,Normal,Roughness}.uasset`. Magicians `T_Lantern_*` is marketplace — not yours. |",
        "| StylizedMagicalWand | none | Same ZenTrim set. Mesh `Content\\Greybox_Kit\\SM_Retopo_wand.fbx` (no sibling `.fbm`). Optional crystal: `G:\\MelodiaMelusina\\MELUSINATILEABLE TEXTURES\\crystal\\crystal_BaseColor.png`. |",
        "",
        "Character (already in UE): `Content\\Melodia\\Characters\\Melusina\\Textures\\T_MelusinaC_*` plus staged `Imports\\MelusinaTextures\\`. Source `.spp`: `G:\\MelodiaMelusina\\shirttextured.spp`. `ACTUALCOMPILEDMELUSINATEXTURES` is not on G: tonight.",
    ]
    if missing_roots:
        lines += ["", "## Missing roots", ""]
        lines += [f"- `{p}`" for p in missing_roots]
    for cls in (
        "prop_cross", "prop_lantern", "prop_wand", "prop_token", "tileable",
        "character", "trimsheet", "substance_source",
    ):
        rows = samples.get(cls, [])
        lines += ["", f"## {cls} (largest samples)", ""]
        if not rows:
            lines.append("_none_")
            continue
        for r in rows[:15]:
            mb = r["bytes"] / (1024 * 1024)
            lines.append(f"- `{r['path']}` ({mb:.1f} MB)")
    lines += ["", "## Substance projects (.spp) largest", ""]
    for r in payload.get("substance_projects", [])[:20]:
        mb = r["bytes"] / (1024 * 1024)
        lines.append(f"- `{r['path']}` ({mb:.1f} MB) · {r['class']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"total": payload["total_hits"], "counts": counts, "json": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
