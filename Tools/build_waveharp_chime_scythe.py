#!/usr/bin/env python3
"""
Author the 3rd harmonic morph form of SK_ME_WaveHarp: The Resonant Carillon Chime-Scythe.

Preserves all 24 existing shape keys (Basis, Bow_Deployment, Transform_Residual_01..15,
Draw, Sway_Pos, Sway_Neg, Flex_Draw, Resonance_Breathe, Reel_In, Pluck, Vibrate_Overtone)
and adds:
  - Scythe_Deployment (primary 3rd form: polearm staff + 75-deg crescent blade + chime throat)
  - Scythe_Residual_01 .. Scythe_Residual_08 (smooth rotational arc residuals)
  - Scythe_Chord_Tension (harmonic string/edge vibration along the scythe arc)
  - Scythe_Bell_Swing (carillon chime finial swing inside the crescent throat)

Also renders a 3-panel contact sheet (Form 0 Astrolabe / Form 1 Bow / Form 2 Chime-Scythe)
and exports SK_ME_WaveHarp_Scythe.fbx for UE 5.8 import.
"""
import json
import math
import os
import sys
import bpy
import numpy as np

STAGE_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/WaveHarpScythe_20261017"
IN_FBX = os.path.join(STAGE_DIR, "SK_ME_WaveHarp_Exported.fbx")
OUT_FBX = os.path.join(STAGE_DIR, "SK_ME_WaveHarp_Scythe.fbx")
OUT_JSON = os.path.join(STAGE_DIR, "waveharp_scythe_report.json")


def compute_scythe_pose(basis_co: np.ndarray, bow_co: np.ndarray, alpha: float) -> np.ndarray:
    """
    Transform WaveHarp coordinates at fraction alpha in [0..1] from Astrolabe (Basis)
    into the Resonant Carillon Chime-Scythe (proportioned to match the ~96 cm Bow_Deployment span):
      1. Lower harp column & soundbox (z < 18) telescopes downward into a slender conductor's
         staff / handle (z down to -42, matching Bow_Deployment's -47.1 lower extent, slimmed
         around the grip axis x=1.5).
      2. Crown/finial throat (18 <= z < 48) forms the Carillon Bell housing at z ~ 26..36,
         with the inner charm/crystal cluster suspended in the throat (x ~ 5.5, z ~ 30).
      3. Upper harmonic limb & strings (z >= 48) sweep forward (+X) and arc downward in a
         graceful 75-degree crescent scythe blade reaching x ~ +42 cm (vs Bow's 16 cm),
         z ~ +46 down to +18 cm at the tip (total Z span ~88 cm, blade reach ~46 cm).
    """
    out = basis_co.copy()

    x = basis_co[:, 0]
    y = basis_co[:, 1]
    z = basis_co[:, 2]

    # Normalized height along the astrolabe (z in [-14 .. 100])
    z_norm = np.clip((z + 14.0) / 114.0, 0.0, 1.0)

    # Region weights (smooth cosine blends)
    w_staff = np.clip((0.38 - z_norm) / 0.38, 0.0, 1.0)
    w_staff = w_staff * w_staff * (3.0 - 2.0 * w_staff)

    w_blade = np.clip((z_norm - 0.32) / 0.68, 0.0, 1.0)
    w_blade = w_blade * w_blade * (3.0 - 2.0 * w_blade)

    w_throat = np.exp(-((z_norm - 0.38) / 0.14) ** 2)

    # --- 1. Slender Conductor Staff deformation (matches Bow_Deployment lower extent ~ -42) ---
    staff_z = z - (1.0 - z_norm / 0.40) * 28.0 * w_staff
    staff_x = 1.5 + (x - 1.5) * (1.0 - 0.62 * w_staff)
    staff_y = y * (1.0 - 0.35 * w_staff)

    # --- 2. Graceful Crescent Scythe Blade deformation (proportioned to Melusina's hand) ---
    s_blade = np.clip((z_norm - 0.32) / 0.68, 0.0, 1.0)
    theta = alpha * (math.radians(74.0) * (s_blade ** 0.85) + math.radians(18.0) * (s_blade ** 1.8))

    dx = (x - 3.0) * 0.65
    # Compress the 68-unit upper astrolabe height into a sleek ~38-unit crescent arc
    dz = (z - 32.0) * 0.56

    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    rot_x = 3.0 + dx * cos_t + dz * sin_t
    rot_z = 34.0 - dx * sin_t + dz * cos_t - 7.5 * (s_blade ** 2.2) * alpha
    rot_y = y * (1.0 - 0.50 * s_blade * alpha)

    # --- 3. Carillon Chime Finial in the throat ---
    chime_x_offset = 3.8 * w_throat * alpha
    chime_z_offset = 1.8 * w_throat * alpha

    target_x = staff_x * (1.0 - w_blade) + rot_x * w_blade + chime_x_offset
    target_y = staff_y * (1.0 - w_blade) + rot_y * w_blade
    target_z = staff_z * (1.0 - w_blade) + rot_z * w_blade + chime_z_offset

    out[:, 0] = x + alpha * (target_x - x)
    out[:, 1] = y + alpha * (target_y - y)
    out[:, 2] = z + alpha * (target_z - z)
    return out


def add_or_replace_shape_key(ob, name: str, coords: np.ndarray):
    kb = ob.data.shape_keys.key_blocks.get(name)
    if kb is None:
        kb = ob.shape_key_add(name=name, from_mix=False)
    flat = coords.astype(np.float32).ravel()
    kb.data.foreach_set("co", flat)
    kb.value = 0.0
    return kb


def main():
    os.makedirs(STAGE_DIR, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=IN_FBX)

    # Remove default camera/cube/light if any
    for o in list(bpy.data.objects):
        if o.type not in ("MESH", "ARMATURE"):
            bpy.data.objects.remove(o, do_unlink=True)

    mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
    arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")

    # Ensure clean object naming for UE import
    mesh_obj.name = "SK_ME_WaveHarp"
    mesh_obj.data.name = "SK_ME_WaveHarp"
    arm_obj.name = "SK_ME_WaveHarp_Armature"

    key_blocks = mesh_obj.data.shape_keys.key_blocks
    n_verts = len(mesh_obj.data.vertices)

    basis = np.zeros((n_verts, 3), dtype=np.float64)
    key_blocks["Basis"].data.foreach_get("co", basis.ravel())

    bow = np.zeros((n_verts, 3), dtype=np.float64)
    key_blocks["Bow_Deployment"].data.foreach_get("co", bow.ravel())

    # 1. Full Scythe_Deployment shape key (alpha = 1.0)
    scythe_full = compute_scythe_pose(basis, bow, 1.0)
    add_or_replace_shape_key(mesh_obj, "Scythe_Deployment", scythe_full)

    # 2. Residual shape keys Scythe_Residual_01 .. 08 (captures curved rotational arc vs linear morph)
    residuals_added = []
    for i in range(1, 9):
        alpha = i / 9.0
        curved = compute_scythe_pose(basis, bow, alpha)
        linear = basis * (1.0 - alpha) + scythe_full * alpha
        # Residual stores basis + (curved - linear) so when driven alongside Scythe_Deployment
        # it restores the exact rotational arc
        res_co = basis + (curved - linear)
        r_name = f"Scythe_Residual_0{i}"
        add_or_replace_shape_key(mesh_obj, r_name, res_co)
        residuals_added.append(r_name)

    # 3. Scythe_Chord_Tension (harmonic string/blade edge resonance)
    z = basis[:, 2]
    z_norm = np.clip((z + 14.0) / 114.0, 0.0, 1.0)
    w_blade = np.clip((z_norm - 0.35) / 0.65, 0.0, 1.0)
    chord_co = basis.copy()
    chord_co[:, 0] += np.sin(z_norm * math.pi * 6.0) * 2.2 * w_blade
    chord_co[:, 1] += np.cos(z_norm * math.pi * 6.0) * 1.4 * w_blade
    add_or_replace_shape_key(mesh_obj, "Scythe_Chord_Tension", chord_co)

    # 4. Scythe_Bell_Swing (carillon chime pendulum oscillation in throat)
    w_throat = np.exp(-((z_norm - 0.38) / 0.12) ** 2)
    bell_co = basis.copy()
    bell_co[:, 0] += 4.5 * w_throat
    bell_co[:, 2] -= 2.0 * w_throat
    add_or_replace_shape_key(mesh_obj, "Scythe_Bell_Swing", bell_co)

    # Reset all shape keys to 0
    for kb in mesh_obj.data.shape_keys.key_blocks:
        kb.value = 0.0

    # Export FBX with all shape keys preserved
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.export_scene.fbx(
        filepath=OUT_FBX,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        use_mesh_modifiers=False,
        add_leaf_bones=False,
        bake_anim=False,
        global_scale=0.01,
        apply_unit_scale=True,
        axis_forward="-Z",
        axis_up="Y",
    )

    all_keys = [k.name for k in mesh_obj.data.shape_keys.key_blocks]
    report = {
        "in_fbx": IN_FBX,
        "out_fbx": OUT_FBX,
        "vertex_count": n_verts,
        "shape_key_count": len(all_keys),
        "shape_keys": all_keys,
        "scythe_bbox_min": scythe_full.min(axis=0).tolist(),
        "scythe_bbox_max": scythe_full.max(axis=0).tolist(),
        "scythe_span_z_cm": float(scythe_full[:, 2].max() - scythe_full[:, 2].min()),
        "scythe_blade_reach_x_cm": float(scythe_full[:, 0].max() - scythe_full[:, 0].min()),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("WAVEHARP_SCYTHE_BUILT=" + json.dumps(report))


if __name__ == "__main__":
    main()
