"""Package Melodia Musical Ornament Kitbash (sibling SKU).

Usage:
  python Content/Python/package_musical_ornament_kitbash.py
  python Content/Python/package_musical_ornament_kitbash.py --zip
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from musical_ornament_kitbash_catalog import (
    FBX_EXPORT_DIR,
    LAUNCH_PRICE_USD,
    LIST_PRICE_USD,
    MESHES,
    PRODUCT_ID,
    PRODUCT_NAME,
    PRODUCT_ROOT,
    PRODUCT_TAGLINE,
    STORE_TAGS,
    as_product_dict,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_CATALOG = PROJECT_ROOT / "my-site-clean" / "generated" / "musical_ornament_kitbash_catalog.json"
BAKE_MANIFEST = PROJECT_ROOT / "Saved" / "Audit" / "musical_ornament_bake_manifest.json"


def _license_text() -> str:
    return """Melodia Musical Ornament Kitbash — License
Copyright (c) 2026 Brennan Shepherd

COMMERCIAL LICENSE (single-seat indie / studio)

You MAY:
  - Use meshes in commercial games, films, archviz, and client work
  - Modify meshes and materials
  - Include in shipped builds

You MAY NOT:
  - Resell or redistribute source FBX/UAssets raw
  - List this pack on another marketplace
  - Use in AI training datasets for mesh generation products

Credit appreciated: "Brennan Shepherd / Melodia Musical Ornament Kitbash"
"""


def _readme_text() -> str:
    lines = [
        f"# {PRODUCT_NAME}",
        "",
        PRODUCT_TAGLINE,
        "",
        "## Contents",
        "",
        "- `FBX/` — 10 celestial sheet-music static meshes (7 + 3 Melody Tokens)",
        "- `Docs/` — README + license",
        "",
        "## Mesh list (10)",
        "",
    ]
    for m in MESHES:
        lines.append(f"- `{m.asset_name}` ({m.tier}) — {m.description}")
    lines.extend(
        [
            "",
            "## Unreal import",
            "",
            "1. Import FBX from `FBX/` into `/Game/EnvSandbox/Meshes/OrnamentMusical`",
            "2. Or in editor: `py Content/Python/import_ornament_fbx.py --musical --prep`",
            "3. Assign stylized masters to slots **Base** and **Trim**",
            "",
            "## Scale",
            "",
            "Centimeter kitbash scale. Treble clef ~2 m tall; note heads jewelry-to-prop scale.",
            "Scale 0.25–0.5 for interior dressing.",
            "",
            "## Sibling SKU",
            "",
            "Gothic architecture pack (`melodia-ornamental-architecture-kitbash-v1`) is separate.",
            "Not Melodia Game UI `T_Melodia_*` PNG alphas (2D Batch N).",
            "",
        ]
    )
    return "\n".join(lines)


def build_product_folder(*, make_zip: bool = False) -> Path:
    PRODUCT_ROOT.mkdir(parents=True, exist_ok=True)
    (PRODUCT_ROOT / "FBX").mkdir(exist_ok=True)
    (PRODUCT_ROOT / "Docs").mkdir(exist_ok=True)
    (PRODUCT_ROOT / "listings").mkdir(exist_ok=True)
    (PRODUCT_ROOT / "releases").mkdir(exist_ok=True)

    (PRODUCT_ROOT / "Docs" / "README.md").write_text(_readme_text(), encoding="utf-8")
    (PRODUCT_ROOT / "Docs" / "LICENSE.txt").write_text(_license_text(), encoding="utf-8")

    if FBX_EXPORT_DIR.is_dir():
        for fbx in FBX_EXPORT_DIR.glob("SM_Orn_*.fbx"):
            dest = PRODUCT_ROOT / "FBX" / fbx.name
            shutil.copy2(fbx, dest)

    catalog = as_product_dict()
    catalog["generated_at"] = datetime.now(timezone.utc).isoformat()
    catalog["product_folder"] = str(PRODUCT_ROOT.resolve())
    if BAKE_MANIFEST.is_file():
        catalog["bake_manifest"] = str(BAKE_MANIFEST)
        bake = json.loads(BAKE_MANIFEST.read_text(encoding="utf-8"))
        catalog["bake_ok"] = bake.get("ok")
        catalog["bake_fail"] = bake.get("fail")

    fbx_count = len(list((PRODUCT_ROOT / "FBX").glob("*.fbx")))
    catalog["fbx_count"] = fbx_count

    (PRODUCT_ROOT / "product_manifest.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
    )
    WEB_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    WEB_CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    tags = " ".join(f"#{t}" for t in STORE_TAGS[:8])
    listing = f"""# Gumroad — {PRODUCT_NAME}

## Price
Launch ${LAUNCH_PRICE_USD} → list ${LIST_PRICE_USD}

## Tags
{tags}

## Body
{PRODUCT_TAGLINE}

7 celestial sheet-music ornaments (treble clef, notes, staff rail, filigree corner/divider, pearl jewel).
FBX for Unreal 5.8+. Sibling to the gothic ornamental architecture pack.

Store live stays false until ZIP is purchasable.
"""
    (PRODUCT_ROOT / "listings" / "gumroad.md").write_text(listing, encoding="utf-8")

    if make_zip:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        zip_path = PRODUCT_ROOT / "releases" / f"Melodia_Musical_Ornament_Kitbash_v1_{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for folder in ("FBX", "Docs"):
                base = PRODUCT_ROOT / folder
                for file in base.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(PRODUCT_ROOT))
        catalog["release_zip"] = str(zip_path.resolve())
        (PRODUCT_ROOT / "product_manifest.json").write_text(
            json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
        )
        print(f"ZIP: {zip_path}")

    print(f"Product: {PRODUCT_ROOT}  fbx={fbx_count}  id={PRODUCT_ID}")
    print(f"Web:     {WEB_CATALOG}")
    return PRODUCT_ROOT


def main() -> int:
    make_zip = "--zip" in sys.argv
    build_product_folder(make_zip=make_zip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
