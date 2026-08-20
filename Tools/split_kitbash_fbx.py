#!/usr/bin/env python3
"""Split a monolithic KitBash3D FBX into per-object FBXs Unreal can actually ingest.

WHY
---
`Imports/KitBash3D_Atlantis/Source/Atlantis.fbx` is a single 3.0 GB scene holding every
model in the kit as nodes. Unreal's FBX importer loads the whole scene into memory before
writing any asset, so importing it aborted the editor at
`GenericPlatformMemory.cpp:300` -- out of memory -- after 38 minutes, having written
nothing.

The Kenney kit in the same ingest run succeeded because it is 105 small FBXs: the importer
never holds more than one at a time. Same script, opposite memory profile. So the fix is
not to chunk the *import*, it is to make the unit on disk smaller than the unit of memory.

Chunking here also means a failed piece costs one object, not 38 minutes.

Blender is used rather than Unreal because it streams the FBX rather than building the
whole scene graph in engine memory first, and because a failure here cannot take the
editor down with it.

TEXTURES ARE NOT TOUCHED
------------------------
`Textures 4K/` (424 PNG) is imported separately by the existing ingest path, which already
authors toon material instances from `atlantis_toon.material_map.json`. Exporting textures
per chunk would duplicate ~12 GB.

USAGE
-----
    blender --background --factory-startup \
        --python Tools/split_kitbash_fbx.py -- \
        --fbx "C:/EnvironmentPortfolio/Imports/KitBash3D_Atlantis/Split/Atlantis.fbx" \
        --out "C:/EnvironmentPortfolio/Imports/KitBash3D_Atlantis/Split" \
        --inspect-only

Drop `--inspect-only` to write. `--batch N` groups N objects per FBX (default 1).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time

import bpy

PREFIX = "KB3D_ATL_"
# Matches the variant token (single uppercase letter) that follows the family name,
# e.g. "BldgSmPort_A" out of "BldgSmPort_A_RocksB". The family name itself is
# free-form CamelCase, so we don't hardcode it -- we just anchor on "_<Letter>_"
# or "_<Letter>" at end of string, which is the strict convention observed in
# actual object names (KB3D_ATL_BldgSmPort_A_RocksB, KB3D_ATL_BldgLgPalace_A_ShrubsA, ...).
_VARIANT_RE = re.compile(r"^(.+?_[A-Z])(?:_.+)?$")


def group_key_for(name: str) -> str:
    """Return the prefix group for an object name, or '_Unmatched' if it doesn't
    follow the KB3D_ATL_<Family>_<Variant>_<Part> convention."""
    if not name.startswith(PREFIX):
        return "_Unmatched"
    rest = name[len(PREFIX):]
    m = _VARIANT_RE.match(rest)
    if not m:
        return "_Unmatched"
    return m.group(1)


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name: str, default=None):
    a = args()
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main() -> int:
    fbx = opt("--fbx")
    out = opt("--out")
    batch = int(opt("--batch", "1"))
    inspect_only = "--inspect-only" in args()
    group_by_prefix = "--group-by-prefix" in args()

    if not fbx or not os.path.isfile(fbx):
        print(f"ABORT: --fbx not found: {fbx}")
        return 2

    size_gb = os.path.getsize(fbx) / (1024 ** 3)
    print(f"source     : {fbx}")
    print(f"size       : {size_gb:.2f} GB")
    mode_desc = "INSPECT" if inspect_only else ("SPLIT-BY-PREFIX" if group_by_prefix else "SPLIT")
    print(f"mode       : {mode_desc}  batch={batch}")

    clear_scene()
    t0 = time.time()
    print("importing (this is the slow part)...", flush=True)
    try:
        bpy.ops.import_scene.fbx(filepath=fbx, use_custom_normals=True,
                                 ignore_leaf_bones=True, automatic_bone_orientation=True)
    except Exception as exc:  # noqa: BLE001 - want the real reason in the log
        print(f"ABORT: import failed: {exc}")
        return 1
    print(f"imported in {time.time() - t0:.0f}s", flush=True)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    tris = sum(len(o.data.loop_triangles) or len(o.data.polygons) for o in meshes)
    print(f"mesh objects: {len(meshes)}")
    print(f"polygons    : {tris}")

    report = {
        "source": fbx, "size_gb": round(size_gb, 2),
        "mesh_objects": len(meshes), "polygons": tris,
        "batch": batch, "inspect_only": inspect_only, "chunks": [],
    }

    # Largest first: if the run dies, it dies on the object most likely to be the
    # problem, and the cheap ones are already on disk.
    meshes.sort(key=lambda o: len(o.data.polygons), reverse=True)
    print("\nheaviest objects:")
    for o in meshes[:10]:
        print(f"  {len(o.data.polygons):>9}  {o.name}")

    if inspect_only:
        _write(report)
        print("\nINSPECT ONLY. Nothing written.")
        return 0

    os.makedirs(out, exist_ok=True)

    if group_by_prefix:
        report["mode"] = "group-by-prefix"
        by_key: dict[str, list] = {}
        for o in meshes:
            by_key.setdefault(group_key_for(o.name), []).append(o)
        # Stable, readable ordering; keep _Unmatched last.
        keys = sorted(k for k in by_key if k != "_Unmatched")
        if "_Unmatched" in by_key:
            keys.append("_Unmatched")

        print(f"\n{len(keys)} groups found:")
        for k in keys:
            print(f"  {k:<40} {len(by_key[k]):>5} objects")

        for idx, key in enumerate(keys):
            group = by_key[key]
            for o in bpy.context.scene.objects:
                o.select_set(False)
            for o in group:
                o.select_set(True)
            bpy.context.view_layer.objects.active = group[0]

            safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
            path = os.path.join(out, f"{safe}.fbx")

            t_export = time.time()
            try:
                bpy.ops.export_scene.fbx(
                    filepath=path, use_selection=True, object_types={"MESH"},
                    use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True,
                    add_leaf_bones=False, bake_anim=False, path_mode="STRIP",
                    axis_forward="-Z", axis_up="Y", global_scale=1.0,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"ABORT: export failed for group {key}: {exc}", flush=True)
                _write(report)
                return 1

            polys = sum(len(o.data.polygons) for o in group)
            size_bytes = os.path.getsize(path) if os.path.isfile(path) else 0
            report["chunks"].append({
                "name": key,
                "file": os.path.basename(path),
                "objects": len(group),
                "polygons": polys,
                "size_bytes": size_bytes,
            })
            print(f"  [{idx + 1}/{len(keys)}] {key} -> {os.path.basename(path)} "
                  f"({len(group)} obj, {polys} tris, {size_bytes / 1e6:.1f} MB, "
                  f"{time.time() - t_export:.1f}s)", flush=True)

        _write(report)
        print(f"\ndone: {len(keys)} group files in {out}")
        return 0

    groups = [meshes[i:i + batch] for i in range(0, len(meshes), batch)]
    print(f"\nwriting {len(groups)} FBX(s) -> {out}", flush=True)

    for idx, group in enumerate(groups):
        for o in bpy.context.scene.objects:
            o.select_set(False)
        for o in group:
            o.select_set(True)
        bpy.context.view_layer.objects.active = group[0]

        name = group[0].name if batch == 1 else f"chunk_{idx:04d}"
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        path = os.path.join(out, f"{safe}.fbx")

        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True, object_types={"MESH"},
            use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True,
            add_leaf_bones=False, bake_anim=False, path_mode="STRIP",
            axis_forward="-Z", axis_up="Y", global_scale=1.0,
        )
        report["chunks"].append({"file": os.path.basename(path),
                                 "objects": [o.name for o in group],
                                 "polygons": sum(len(o.data.polygons) for o in group)})
        if idx % 25 == 0 or idx == len(groups) - 1:
            print(f"  [{idx + 1}/{len(groups)}] {os.path.basename(path)}", flush=True)

    _write(report)
    print(f"\ndone: {len(groups)} files in {out}")
    return 0


def _write(report: dict) -> None:
    p = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/kitbash_fbx_split.json"
    try:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"audit: {p}")
    except OSError as exc:
        print(f"WARN audit not written: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
