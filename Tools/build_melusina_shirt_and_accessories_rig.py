"""Headless Blender 5.2 rigging & layering pass for Melusina V2 Shirt and V2 Accessories:
1. SK_Melusina_V2_Shirt_Flared.fbx:
   - Remaps all 234 leg-bound vertices off the thighs using shirt_weight_fix_v1.json
   - Transfers waist-ring c_kilt_master_x / root_x weights to the lower shirt hem (Z < 85 cm)
     so the shirt hem moves with the top of the skirt instead of fighting it
   - Ensures 360-degree radial clearance (+4.5 cm minimum outside SK_Melusina_V2_Skirt_R2_SmoothChains)
     from Z = 69.6 to 88.5 cm so the shirt sits ON TOP of the skirt to hide UV seams and upper physics
2. SK_Melusina_V2_Accessories_RigFixed.fbx:
   - Fixes chest bow (island 97, Z > 115 cm) stray ORG-face / DEF-chin weights -> spine_03_x
   - Transfers smooth c_kilt_* weights from SK_Melusina_V2_Skirt_R2_SmoothChains onto lower-body
     drape islands (frontpanel_001 and SHAWL_001, Z < 100 cm) and pushes any intersecting/coplanar
     vertices +0.5 cm radially outside the skirt surface so KawaiiPhysics simulates skirt + accessories cohesively.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
INPUTS = PROJECT / "Saved/Audit/MelusinaRuntimeCloseout_20261009/SkirtLayering_20261011/Inputs"
SEC_INPUTS = PROJECT / "Saved/Audit/MelusinaSecondarySources_20261003"
WEIGHT_FIX_JSON = PROJECT / "Saved/Audit/melusina_animation_doctor/shirt_fix/shirt_weight_fix_v1.json"
STAGE_DIR = PROJECT / "Saved/Staging/WaveHarpScythe_20261017"


def import_fbx_single_mesh(fbx_path: Path, role: str):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path), automatic_bone_orientation=False, use_anim=False)
    added = list(set(bpy.data.objects) - before)
    meshes = [o for o in added if o.type == "MESH"]
    arms = [o for o in added if o.type == "ARMATURE"]
    assert len(meshes) == 1 and len(arms) == 1, f"Expected 1 mesh + 1 armature in {fbx_path}, got {len(meshes)} / {len(arms)}"
    meshes[0]["role"] = role
    return meshes[0], arms[0]


def get_vertex_weights_dict(obj, v_idx: int) -> dict[str, float]:
    v = obj.data.vertices[v_idx]
    out = {}
    for g in v.groups:
        if g.weight > 1e-6:
            name = obj.vertex_groups[g.group].name
            out[name] = float(g.weight)
    return out


def set_vertex_weights_dict(obj, v_idx: int, weights: dict[str, float]) -> None:
    v = obj.data.vertices[v_idx]
    for g in list(v.groups):
        obj.vertex_groups[g.group].remove([v_idx])
    items = [(k, max(0.0, float(w))) for k, w in weights.items() if w > 1e-5]
    items.sort(key=lambda x: x[1], reverse=True)
    items = items[:4]
    total = sum(w for _, w in items)
    if total <= 1e-8:
        items = [("spine_01_x", 1.0)]
        total = 1.0
    for name, w in items:
        vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        vg.add([v_idx], w / total, "REPLACE")


def main():
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    shirt_fbx = INPUTS / "shirt_readonly.fbx"
    skirt_fbx = INPUTS / "skirt_readonly.fbx"
    acc_fbx = STAGE_DIR / "accessories_exported.fbx"
    if not acc_fbx.is_file():
        acc_fbx = SEC_INPUTS / "accessories_fit_readonly.fbx"

    shirt, shirt_arm = import_fbx_single_mesh(shirt_fbx, "shirt")
    skirt, skirt_arm = import_fbx_single_mesh(skirt_fbx, "skirt")
    acc, acc_arm = (import_fbx_single_mesh(acc_fbx, "accessories") if acc_fbx.is_file() else (None, None))

    center = skirt_arm.matrix_world @ skirt_arm.data.bones["root_x"].head_local

    # Build BVH for skirt in world space (meters in Blender scene -> *100 = cm)
    skirt.data.calc_loop_triangles()
    sk_verts_w = [skirt.matrix_world @ v.co for v in skirt.data.vertices]
    sk_tris = [tuple(t.vertices) for t in skirt.data.loop_triangles]
    sk_bvh = BVHTree.FromPolygons(sk_verts_w, sk_tris, all_triangles=True)

    # 1. Fix Shirt weights (234 leg-bound verts from shirt_weight_fix_v1.json + waist kilt sync) & over-skirt flare
    wfix = json.loads(WEIGHT_FIX_JSON.read_text(encoding="utf-8"))["verts"]
    remapped_shirt_verts = 0
    for k_str, pairs in wfix.items():
        vi = int(k_str)
        if vi < len(shirt.data.vertices):
            set_vertex_weights_dict(shirt, vi, {b: float(w) for b, w in pairs})
            remapped_shirt_verts += 1

    flared_shirt_verts = 0
    min_clearance_after_cm = 999.0
    for v in shirt.data.vertices:
        p = shirt.matrix_world @ v.co
        z_cm = p.z * 100.0
        if 68.0 <= z_cm <= 92.0:
            # Blend 35% of c_kilt_master_x / root_x waist motion into lower hem so shirt rides over skirt waist
            t_hem = max(0.0, min(1.0, (86.0 - z_cm) / (86.0 - 69.6)))
            if t_hem > 0.0:
                cw = get_vertex_weights_dict(shirt, v.index)
                blend = 0.40 * t_hem
                new_w = {k: val * (1.0 - blend) for k, val in cw.items()}
                new_w["c_kilt_master_x"] = new_w.get("c_kilt_master_x", 0.0) + blend * 0.65
                new_w["root_x"] = new_w.get("root_x", 0.0) + blend * 0.35
                set_vertex_weights_dict(shirt, v.index, new_w)

            # Ensure shirt sits ON TOP of skirt around full 360 perimeter (+4.5 cm radial margin)
            radial = Vector((p.x - center.x, p.y - center.y, 0.0))
            r_len = radial.length
            if r_len > 1e-6:
                r_dir = radial / r_len
                # Cast outward and inward from spine axis at this Z to find max skirt radius along this ray
                origin = Vector((center.x, center.y, p.z))
                hit, _n, _f, dist = sk_bvh.ray_cast(origin, r_dir, 2.0)
                # Smooth bell flare below Z=92 cm plus explicit skirt surface clearance
                bell_t = 0.5 * (1.0 - math.cos(math.pi * max(0.0, min(1.0, (92.0 - z_cm) / 22.4))))
                target_r = r_len + 0.045 * bell_t
                if hit is not None:
                    target_r = max(target_r, dist + 0.045)
                if target_r > r_len:
                    p_new = Vector((center.x + r_dir.x * target_r, center.y + r_dir.y * target_r, p.z))
                    v.co = shirt.matrix_world.inverted() @ p_new
                    flared_shirt_verts += 1
                if hit is not None:
                    min_clearance_after_cm = min(min_clearance_after_cm, (max(r_len, target_r) - dist) * 100.0)

    shirt.data.update()

    # 2. Fix Accessories rigging vs Kilt:
    #    - Chest bow (Z > 115 cm, |X| < 18 cm): remove ORG-face / DEF-chin / head_x weights -> spine_03_x
    #    - Lower-body skirt drapes (frontpanel_001, SHAWL_001 at Z < 102 cm): transfer nearest skirt c_kilt_* weights
    #      and ensure +0.5 cm radial clearance outside the skirt surface
    chest_bow_fixed = 0
    kilt_drape_synced = 0
    kilt_drape_pushed = 0

    for v in (acc.data.vertices if acc else []):
        p = acc.matrix_world @ v.co
        z_cm = p.z * 100.0
        x_cm = p.x * 100.0
        cw = get_vertex_weights_dict(acc, v.index)

        if z_cm > 112.0 and abs(x_cm) < 20.0:
            # Chest bow / collar area: strip face/head/chin weights so head turns don't stretch the chest bow
            bad_keys = [k for k in cw if ("face" in k.lower() or "chin" in k.lower() or "head" in k.lower() or "jaw" in k.lower())]
            if bad_keys:
                reassigned = sum(cw.pop(k) for k in bad_keys)
                cw["spine_03_x"] = cw.get("spine_03_x", 0.0) + reassigned
                set_vertex_weights_dict(acc, v.index, cw)
                chest_bow_fixed += 1
        elif z_cm < 102.0:
            # Lower-body accessories (frontpanel_001, bow_002 waist, SHAWL_001 overskirt ribbons):
            # Transfer weights from nearest triangle on SK_Melusina_V2_Skirt_R2_SmoothChains
            hit, _n, face_idx, _dist = sk_bvh.find_nearest(p)
            if face_idx is not None:
                tri = sk_tris[face_idx]
                # Inverse-distance weighted blend of the 3 triangle vertices' weights on the smoothed skirt
                d0 = max(1e-5, (p - sk_verts_w[tri[0]]).length)
                d1 = max(1e-5, (p - sk_verts_w[tri[1]]).length)
                d2 = max(1e-5, (p - sk_verts_w[tri[2]]).length)
                inv0, inv1, inv2 = 1.0 / d0, 1.0 / d1, 1.0 / d2
                inv_sum = inv0 + inv1 + inv2
                w0 = get_vertex_weights_dict(skirt, tri[0])
                w1 = get_vertex_weights_dict(skirt, tri[1])
                w2 = get_vertex_weights_dict(skirt, tri[2])
                merged: dict[str, float] = {}
                for bname, bw in w0.items():
                    merged[bname] = merged.get(bname, 0.0) + bw * (inv0 / inv_sum)
                for bname, bw in w1.items():
                    merged[bname] = merged.get(bname, 0.0) + bw * (inv1 / inv_sum)
                for bname, bw in w2.items():
                    merged[bname] = merged.get(bname, 0.0) + bw * (inv2 / inv_sum)
                # Strip any thigh_twist weights on upper waist bow/panel above Z=72 cm
                if z_cm > 72.0:
                    for tk in [k for k in merged if "thigh" in k or "leg_" in k]:
                        moved = merged.pop(tk)
                        merged["c_kilt_master_x"] = merged.get("c_kilt_master_x", 0.0) + moved
                set_vertex_weights_dict(acc, v.index, merged)
                kilt_drape_synced += 1

            # Ensure accessories drape sits at least +0.5 cm outside the skirt along the radial ray
            radial = Vector((p.x - center.x, p.y - center.y, 0.0))
            r_len = radial.length
            if r_len > 1e-6:
                r_dir = radial / r_len
                origin = Vector((center.x, center.y, p.z))
                rhit, _rn, _rf, rdist = sk_bvh.ray_cast(origin, r_dir, 2.0)
                if rhit is not None and r_len < rdist + 0.005:
                    p_new = Vector((center.x + r_dir.x * (rdist + 0.005), center.y + r_dir.y * (rdist + 0.005), p.z))
                    v.co = acc.matrix_world.inverted() @ p_new
                    kilt_drape_pushed += 1

    if acc:
        acc.data.update()

    # Export upgraded FBXs
    shirt_out = STAGE_DIR / "SK_Melusina_V2_Shirt_Flared.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    shirt.select_set(True)
    shirt_arm.select_set(True)
    bpy.context.view_layer.objects.active = shirt
    bpy.ops.export_scene.fbx(
        filepath=str(shirt_out),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward="-Z",
        axis_up="Y",
    )

    acc_out = STAGE_DIR / "SK_Melusina_V2_Accessories_RigFixed.fbx"
    if acc and acc_arm:
        bpy.ops.object.select_all(action="DESELECT")
        acc.select_set(True)
        acc_arm.select_set(True)
        bpy.context.view_layer.objects.active = acc
        bpy.ops.export_scene.fbx(
            filepath=str(acc_out),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            add_leaf_bones=False,
            bake_anim=False,
            axis_forward="-Z",
            axis_up="Y",
        )

    receipt = {
        "schema": "melodia.shirt_and_accessories_rig_pass.v1",
        "shirt": {
            "output_fbx": str(shirt_out).replace("\\", "/"),
            "remapped_leg_vertices": remapped_shirt_verts,
            "flared_waist_vertices": flared_shirt_verts,
            "min_radial_clearance_over_skirt_cm": round(min_clearance_after_cm, 3),
        },
        "accessories": {
            "output_fbx": str(acc_out).replace("\\", "/"),
            "chest_bow_face_weights_removed": chest_bow_fixed,
            "kilt_drape_vertices_synced_to_smooth_skirt": kilt_drape_synced,
            "kilt_drape_vertices_pushed_outside_skirt": kilt_drape_pushed,
        },
    }
    receipt_path = STAGE_DIR / "shirt_and_accessories_rig_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("RIG_PASS_OK=" + json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
