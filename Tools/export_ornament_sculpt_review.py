# -*- coding: utf-8 -*-
"""Stage gothic + musical ornament FBXs into a sculpt-review folder and blend.

Inputs (already baked):
  KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx
  KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx

Outputs:
  Products/_Staging/OrnamentSculptReview_<stamp>/Gothic/
  Products/_Staging/OrnamentSculptReview_<stamp>/Musical/
  Products/_Staging/OrnamentSculptReview_<stamp>/OrnamentSculptReview.blend
  Products/_Staging/OrnamentSculptReview_<stamp>/MANIFEST.json
  Products/_Staging/OrnamentSculptReview_<stamp>/README.md

Also refreshes Products/*/FBX copies.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
GOTHIC_SRC = ROOT / "KitbashExport" / "OrnamentalMeshes"
MUSICAL_SRC = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
GOTHIC_PROD = ROOT / "Products" / "OrnamentKitbash" / "FBX"
MUSICAL_PROD = ROOT / "Products" / "MusicalOrnamentKitbash" / "FBX"


def log(msg: str) -> None:
    print(f"[sculpt-review] {msg}", flush=True)


def stamp_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return ROOT / "Products" / "_Staging" / f"OrnamentSculptReview_{stamp}"


def copy_fbx(src: Path, dst: Path) -> list[dict]:
    dst.mkdir(parents=True, exist_ok=True)
    rows = []
    for fbx in sorted(src.glob("SM_Orn_*.fbx")):
        target = dst / fbx.name
        shutil.copy2(fbx, target)
        rows.append({"name": fbx.name, "bytes": target.stat().st_size, "path": str(target)})
        log(f"copy {fbx.name} -> {target} ({target.stat().st_size} bytes)")
    return rows


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.collections):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def ensure_coll(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def import_grid(fbx_files: list[Path], coll_name: str, start_x: float = 0.0) -> int:
    col = ensure_coll(coll_name)
    n = 0
    spacing = 3.5
    for i, path in enumerate(fbx_files):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(path), automatic_bone_orientation=True)
        new = [o for o in bpy.data.objects if o not in before]
        x = start_x + (i % 5) * spacing
        y = (i // 5) * spacing
        for o in new:
            if o.type != "MESH":
                continue
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            o.location = (x, y, 0.0)
            o.name = path.stem
            n += 1
    return n


def write_readme(out: Path, gothic_n: int, musical_n: int) -> None:
    text = f"""# Ornament sculpt review pack

Generated for Melodia kitbash sculpt / polish passes.

## Folders
- `Gothic/` — {gothic_n} SM_Orn_* (SKU #1 ornamental kitbash)
- `Musical/` — {musical_n} SM_Orn_* (sibling musical kitbash)
- `OrnamentSculptReview.blend` — all meshes in a grid for Blender sculpt review

## Workflow
1. Open the `.blend` in Blender 5.1 (or import FBX into ZBrush / your sculpt tool).
2. Sculpt / remesh / polish per mesh — keep `SM_Orn_*` names.
3. Export updated FBX back into the matching folder (`Gothic/` or `Musical/`).
4. Copy finals into:
   - `KitbashExport/OrnamentalMeshes/` (gothic)
   - `KitbashExport/MusicalOrnamentalMeshes/` (musical)
5. Then UE import + store screenshots.

## Materials
Meshes ship with Base + Trim slots (`M_Orn_Base` / `M_Orn_Trim` on gothic regen).
Feel free to replace for sculpt viz; restore slots before sell ZIP.

## Do not
- Mix third-party JRO ornaments into this pack
- Flip `store_live` until sculpt pass + 6 screenshots land
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def run() -> dict:
    out = stamp_dir()
    out.mkdir(parents=True, exist_ok=True)
    gothic_dst = out / "Gothic"
    musical_dst = out / "Musical"

    gothic = copy_fbx(GOTHIC_SRC, gothic_dst)
    musical = copy_fbx(MUSICAL_SRC, musical_dst)

    # Refresh product FBX mirrors
    GOTHIC_PROD.mkdir(parents=True, exist_ok=True)
    MUSICAL_PROD.mkdir(parents=True, exist_ok=True)
    for row in gothic:
        shutil.copy2(row["path"], GOTHIC_PROD / row["name"])
    for row in musical:
        shutil.copy2(row["path"], MUSICAL_PROD / row["name"])

    clear_scene()
    g_files = sorted(gothic_dst.glob("SM_Orn_*.fbx"))
    m_files = sorted(musical_dst.glob("SM_Orn_*.fbx"))
    ng = import_grid(g_files, "Gothic_Review", start_x=0.0)
    nm = import_grid(m_files, "Musical_Review", start_x=20.0)
    blend = out / "OrnamentSculptReview.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    log(f"saved blend {blend} meshes={ng}+{nm}")

    write_readme(out, len(gothic), len(musical))
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(out),
        "blend": str(blend),
        "gothic_count": len(gothic),
        "musical_count": len(musical),
        "gothic": gothic,
        "musical": musical,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    log(f"done -> {out}")
    return manifest


if __name__ == "__main__":
    run()
