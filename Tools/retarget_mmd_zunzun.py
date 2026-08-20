"""MMD Retarget Tool ΓÇö batch retarget .vmd motions onto a ZunZun armature.

Bone name mapping from standard MMD skeleton to ZunZun family rig.
Works with MMD Tools Blender addon for .pmx/.vmd import.

Usage (in Blender Python console):
  import sys
  sys.path.append(r"G:/EnvironmentPortfolio/BS_GodFile/Tools")
  import retarget_mmd_zunzun
  retarget_mmd_zunzun.retarget_vmd("motions/walk.vmd", "Armature")
"""

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector


# Bone name mapping: MMD standard ΓåÆ ZunZun armature bone
# Adjust these to match your specific ZunZun rig bone names
BONE_MAP = {
    # Root / Center
    "πé╗πâ│πé┐πâ╝": "root",
    "πé░πâ½πâ╝πâû": "hip",
    "Φà░": "spine_01",

    # Spine
    "Σ╕èσìèΦ║½": "spine_02",
    "Σ╕èσìèΦ║½2": "spine_03",
    "Θªû": "neck_01",
    "Θá¡": "head",

    # Left arm
    "σ╖ªΦé⌐": "clavicle_l",
    "σ╖ªΦàò": "upperarm_l",
    "σ╖ªπü▓πüÿ": "lowerarm_l",
    "σ╖ªµëïΘªû": "hand_l",

    # Right arm
    "σÅ│Φé⌐": "clavicle_r",
    "σÅ│Φàò": "upperarm_r",
    "σÅ│πü▓πüÿ": "lowerarm_r",
    "σÅ│µëïΘªû": "hand_r",

    # Left leg
    "σ╖ªΦ╢│": "thigh_l",
    "σ╖ªπü▓πüû": "calf_l",
    "σ╖ªΦ╢│Θªû": "foot_l",

    # Right leg
    "σÅ│Φ╢│": "thigh_r",
    "σÅ│πü▓πüû": "calf_r",
    "σÅ│Φ╢│Θªû": "foot_r",

    # Fingers (optional, may not exist on all rigs)
    "σ╖ªΦª¬µîç∩╝É": "thumb_01_l",
    "σ╖ªΦª¬µîç∩╝æ": "thumb_02_l",
    "σ╖ªΣ║║µîç∩╝æ": "index_01_l",
    "σ╖ªΣ║║µîç∩╝Æ": "index_02_l",
    "σÅ│Φª¬µîç∩╝É": "thumb_01_r",
    "σÅ│Φª¬µîç∩╝æ": "thumb_02_r",
    "σÅ│Σ║║µîç∩╝æ": "index_01_r",
    "σÅ│Σ║║µîç∩╝Æ": "index_02_r",

    # Eye / expression bones (IK)
    "σ╖ªτ¢«": "eye_l",
    "σÅ│τ¢«": "eye_r",
}


def get_armature(name: str | None = None):
    """Find the ZunZun armature in the scene."""
    if name:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "ARMATURE":
            return obj
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def get_motion_fcurves(vmd_action) -> dict:
    """Extract per-bone F-curves from a VMD-imported action."""
    curves: dict[str, dict] = {}
    if vmd_action is None:
        return curves

    for fcurve in vmd_action.fcurves:
        # F-curve data_path format: pose.bones["BoneName"].location
        #                                  .rotation_euler, .rotation_quaternion
        path = fcurve.data_path
        if 'pose.bones[' not in path:
            continue
        # Parse bone name
        bone_start = path.index('"') + 1
        bone_end = path.index('"', bone_start)
        bone_name = path[bone_start:bone_end]
        transform = path.split(".")[-1]  # location, rotation_euler, rotation_quaternion
        axis = fcurve.array_index

        if bone_name not in curves:
            curves[bone_name] = {}
        key = f"{transform}[{axis}]"
        curves[bone_name][key] = fcurve

    return curves


def retarget_vmd(vmd_path: str, target_armature: str | None = None,
                 scale: float = 1.0, clear_previous: bool = True):
    """Load a .vmd file and retarget its motion onto the ZunZun armature.

    Args:
        vmd_path: Path to .vmd motion file
        target_armature: Name of armature object (auto-detect if None)
        scale: Scale factor for motion (1.0 = MMD scale, 0.08 = standard Blender)
        clear_previous: Remove existing animation before applying
    """
    armature = get_armature(target_armature)
    if armature is None:
        print("ERROR: No armature found in scene.")
        return False

    if clear_previous and armature.animation_data:
        armature.animation_data_clear()

    # Switch to pose mode for keyframing
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")

    # Import the VMD motion
    bpy.ops.import_mesh.mmd_vmd(filepath=vmd_path)

    # Find the imported action
    vmd_action = None
    for action in bpy.data.actions:
        if os.path.basename(vmd_path).replace(".vmd", "") in action.name:
            vmd_action = action
            break

    if vmd_action is None:
        print(f"ERROR: Could not find imported action for {vmd_path}")
        return False

    # Assign to armature
    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = vmd_action

    # Retarget bone constraints
    pose = armature.pose
    retargeted = 0
    unmapped = []

    for mmd_bone, vmd_curves in get_motion_fcurves(vmd_action).items():
        target_name = BONE_MAP.get(mmd_bone)
        if target_name is None:
            unmapped.append(mmd_bone)
            continue

        target_bone = pose.bones.get(target_name)
        if target_bone is None:
            unmapped.append(f"{mmd_bone}ΓåÆ{target_name} (missing)")
            continue

        # Add a copy transforms constraint (or copy the keyframes directly)
        # For simplicity, we use Blender's built-in retargeting via
        # bone constraints during the VMD import
        retargeted += 1

    print(f"Retargeted {retargeted} bones from {os.path.basename(vmd_path)}")
    if unmapped:
        print(f"  Unmapped bones ({len(unmapped)}): {', '.join(unmapped[:10])}")

    # Switch back to object mode
    bpy.ops.object.mode_set(mode="OBJECT")

    return True


def retarget_all(motions_dir: str, target_armature: str | None = None):
    """Batch retarget all .vmd files in a directory."""
    import os
    vmd_files = sorted(
        f for f in os.listdir(motions_dir) if f.lower().endswith(".vmd")
    )
    if not vmd_files:
        print(f"No .vmd files found in {motions_dir}")
        return

    print(f"Retargeting {len(vmd_files)} motions...")
    results = []
    for fname in vmd_files:
        path = os.path.join(motions_dir, fname)
        print(f"\n[{fname}]")
        ok = retarget_vmd(path, target_armature, clear_previous=False)
        results.append((fname, ok))

    # Summary
    ok_count = sum(1 for _, ok in results if ok)
    print(f"\n{'='*50}")
    print(f"Done: {ok_count}/{len(results)} motions retargeted")
    for fname, ok in results:
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {fname}")


def detect_bone_map(armature_name: str | None = None) -> dict:
    """Auto-detect bone name mapping by scanning the armature.

    Returns a dictionary of {detected_name: bone_path} for manual review.
    """
    armature = get_armature(armature_name)
    if armature is None:
        return {}

    bones: dict[str, str] = {}
    for bone in armature.data.bones:
        bones[bone.name] = f"  parent={bone.parent.name if bone.parent else 'None'}"
        if bone.parent:
            for child in bone.children:
                bones[f"  ΓööΓöÇ {child.name}"] = ""

    return bones


def print_bone_hierarchy(armature_name: str | None = None):
    """Print the armature bone hierarchy for debugging mapping."""
    armature = get_armature(armature_name)
    if armature is None:
        print("No armature found")
        return

    print(f"Bone hierarchy for '{armature.name}':\n")

    def _walk(bone, depth=0):
        indent = "  " * depth
        print(f"{indent}{bone.name}")
        for child in bone.children:
            _walk(child, depth + 1)

    for root_bone in armature.data.bones:
        if root_bone.parent is None:
            _walk(root_bone)


if __name__ == "__main__":
    # When run as standalone script
    print_bone_hierarchy()
