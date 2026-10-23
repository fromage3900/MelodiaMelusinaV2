"""Shorewake dress — 48 LABELED material slots (Substance-ready).

The owner's Substance import arrived merged (one material). This rebuilds the
dress from the source USDZ with ONE LABELED MATERIAL PER PANEL:
  SW_Dress_P01 .. SW_Dress_P48  (P-number follows numeric panel order,
  original dressedit name preserved in the manifest)

Deliverables (Saved/Audit/melusina_lookdev/):
  Shorewake_48MAT.blend            scene with the slotted mesh
  SM_ShorewakeDress_48MAT.fbx      Substance-ready (materials by name)
  dress_materials_manifest.json    slot -> panel mapping + poly counts

Run:  blender -b --factory-startup -noaudio --python dress_48_materials.py
"""

import json
from pathlib import Path

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[3]
USDZ = Path(r"C:\Users\froma\Downloads\melusinashorewake.usdz")
OUT_DIR = PROJECT_ROOT / "Saved/Audit/melusina_lookdev"


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def panel_index(name):
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits) if digits else 999


def main():
    clear()
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.usd_import(filepath=str(USDZ))
    except AttributeError:
        bpy.ops.import_scene.usd(filepath=str(USDZ))
    panels = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    panels.sort(key=lambda o: panel_index(o.name))
    print(f"[48mat] panels found: {len(panels)} "
          f"({panels[0].name} .. {panels[-1].name})")

    mapping = []
    for idx, panel in enumerate(panels, start=1):
        mat_name = f"SW_Dress_P{idx:02d}"
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        panel.data.materials.clear()
        panel.data.materials.append(mat)   # all faces -> slot 0 = this material
        mapping.append({"slot": idx - 1, "material": mat_name,
                        "orig_panel": panel.name,
                        "polys": len(panel.data.polygons),
                        "verts": len(panel.data.vertices)})

    for p in panels:
        p.select_set(True)
    bpy.context.view_layer.objects.active = panels[0]
    bpy.ops.object.join()
    dress = bpy.context.object
    dress.name = "SM_ShorewakeDress_48MAT"
    dress.scale = (100.0, 100.0, 100.0)          # m -> cm (Substance/UE)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()

    # verify: slot count + per-slot face counts
    slots = list(range(len(dress.data.materials)))
    per_slot = {s: 0 for s in slots}
    for poly in dress.data.polygons:
        per_slot[poly.material_index] = per_slot.get(poly.material_index, 0) + 1
    empty = [s for s, n in per_slot.items() if n == 0]
    print(f"[48mat] material slots: {len(slots)} (empty slots: {empty or 'none'})")
    print(f"[48mat] polys: {len(dress.data.polygons)} "
          f"(sum per-slot: {sum(per_slot.values())})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blend_path = OUT_DIR / "Shorewake_48MAT.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[48mat] blend -> {blend_path.name}")

    bpy.ops.object.select_all(action="DESELECT")
    dress.select_set(True)
    fbx_path = OUT_DIR / "SM_ShorewakeDress_48MAT.fbx"
    bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True,
                             add_leaf_bones=False, path_mode="COPY",
                             object_types={"MESH"})
    print(f"[48mat] fbx -> {fbx_path.name} ({fbx_path.stat().st_size} bytes)")

    manifest = {
        "schema": "melodia.shorewake_48mat.v1",
        "source": str(USDZ),
        "scale": "cm applied (x100); Substance import scale to taste",
        "slot_count": len(slots),
        "empty_slots": empty,
        "note": "each slot = one garment panel = one Substance texture set. "
                "Rename slots semantically in Substance if preferred - the "
                "orig_panel column is the cross-reference back to the USDZ.",
        "supersedes": "SK_ShorewakeDress.fbx single-material import for TEXTURING "
                      "(the rigged in-engine dress is unaffected)",
        "mapping": mapping,
    }
    out = OUT_DIR / "dress_materials_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[48mat] manifest -> {out.name}")


if __name__ == "__main__":
    main()
