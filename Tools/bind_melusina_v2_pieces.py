"""Build contract-skinned V2 wardrobe exports from bound v22 objects.

The script runs inside Blender, works on duplicated datablocks, and never saves
the source stage. It preserves existing weights whenever they are usable and
can apply a nearest-surface Data Transfer from an explicit donor when a piece
has no usable deform weights.

Usage (Blender background or Text Editor):
  blender <v22-stage>.blend -b -P Tools/bind_melusina_v2_pieces.py -- \
    --piece Body=Melusina_Body --piece Shirt=Melusina_Shirt \
    --piece Skirt=Melusina_Skirt --piece Boots=Melusina_Boots \
    --piece Accessories=Melusina_Accessories \
    --contract-bones specs/anim_presets/melusina_contract_bones.json \
    --arp-export --require-live-skeleton

For the gameplay-safe path, pass ``--canonical-armature-fbx`` with an FBX
exported from the live UE ``SK_Melusina`` skeletal mesh.  The five pieces keep
the v22 vertex weights, but the exported bind matrices come from that working
canonical armature rather than being reconstructed from the ARP controller rig.

ARP export is preferred for the gameplay deliverable. If the ARP addon/operator
is unavailable, the script fails closed unless --allow-blender-fbx is supplied
explicitly for a controlled fallback review export.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import kdtree


PROJECT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PROJECT / "Exports" / "MelusinaClothes" / "V2"
DEFAULT_REPORT = PROJECT / "Saved" / "Audit" / "melusina_v2_piece_bind_report.json"
SEVEN_HELPERS = {
    "ik_foot_root", "ik_foot_l", "ik_foot_r", "ik_hand_root",
    "ik_hand_gun", "ik_hand_l", "ik_hand_r",
}

# Blender's v22 stage is authored in metres while the live UE skeleton and
# animation tracks are centimetres.  FBX's UnitScaleFactor is only metadata;
# it does not prove that the actual bind matrices were scaled.  Bake the
# conversion into the duplicated export graph before writing the gameplay FBX.
CM_BAKE_FACTOR = 100.0


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--piece", action="append", required=True,
        metavar="LABEL=OBJECT[,OBJECT...]",
        help="One source object or a comma-separated group to merge into one exported piece",
    )
    parser.add_argument("--donor", action="append", default=[], metavar="LABEL=OBJECT")
    parser.add_argument("--rig", default="character_rig")
    parser.add_argument(
        "--canonical-armature-fbx",
        default="",
        help=(
            "Use an FBX exported from the live UE skeletal mesh as the bind "
            "armature. The file must contain the canonical 464 non-root bones."
        ),
    )
    parser.add_argument("--contract-bones", required=True)
    parser.add_argument("--transfer-missing", action="store_true")
    parser.add_argument(
        "--transfer-invalid", action="store_true",
        help="Transfer a piece from its donor when weighted groups are outside the contract",
    )
    parser.add_argument(
        "--drop-unmatched-groups", action="store_true",
        help="Drop non-contract source groups after recording them; fail if any vertex becomes unweighted",
    )
    parser.add_argument("--arp-export", action="store_true")
    parser.add_argument(
        "--reuse-arp-gate", action="store_true",
        help="Reuse a recorded successful ARP source-stage gate when the extracted add-on is unavailable",
    )
    parser.add_argument(
        "--arp-addon",
        default="",
        help="Auto-Rig Pro add-on directory (required for --arp-export when not already enabled)",
    )
    parser.add_argument("--allow-blender-fbx", action="store_true")
    parser.add_argument("--require-live-skeleton", action="store_true")
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def pairs(values: list[str], grouped: bool = False) -> dict[str, list[str] | str]:
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"expected LABEL=OBJECT, got {value!r}")
        label, name = value.split("=", 1)
        result[label.strip()] = [item.strip() for item in name.split(",") if item.strip()] if grouped else name.strip()
    return result


def load_contract(path: Path) -> tuple[
    set[str], dict[str, str], dict[str, str], set[str], set[str], dict[str, str | None]
]:
    data = json.loads(path.read_text(encoding="utf-8"))
    names = data.get("bone_names")
    if not isinstance(names, list) or not names:
        raise ValueError("contract file must contain a non-empty bone_names list")
    semantic = dict(data.get("semantic_map", {}))
    # Observed v22 source groups that need deterministic contract targets.
    group_semantic = dict(semantic)
    group_semantic.update(data.get("weight_group_map", {}))
    bone_semantic = dict(semantic)
    bone_semantic.update(data.get("bone_map", {}))
    drop = set(data.get("drop", sorted(SEVEN_HELPERS)))
    if drop != SEVEN_HELPERS:
        raise ValueError(f"contract helper drop set must be exactly {sorted(SEVEN_HELPERS)}")
    target_count = int(data.get("target_bone_count", 465))
    if len(names) != target_count:
        raise ValueError(f"contract bone_names count {len(names)} != {target_count}")
    hierarchy_path = path.with_name("melusina_contract_hierarchy.json")
    if not hierarchy_path.is_file():
        raise ValueError(f"canonical UE hierarchy missing: {hierarchy_path}")
    hierarchy = json.loads(hierarchy_path.read_text(encoding="utf-8"))
    parent_map = {
        str(k): (None if v in (None, "") else str(v))
        for k, v in dict(hierarchy.get("parent_map", {})).items()
    }
    if set(parent_map) != {str(name) for name in names}:
        raise ValueError("canonical UE hierarchy does not exactly match contract bone_names")
    return (
        set(str(name) for name in names),
        {str(k): str(v) for k, v in group_semantic.items()},
        {str(k): str(v) for k, v in bone_semantic.items()},
        drop,
        set(str(name) for name in data.get("synthetic_bones", [])),
        parent_map,
    )


def sanitized(name: str) -> str:
    return name.replace(".", "_")


def destination_name(source: str, semantic: dict[str, str]) -> str:
    name = sanitized(source)
    return semantic.get(name, name)


def used_groups(obj: bpy.types.Object) -> set[str]:
    names = {group.index: group.name for group in obj.vertex_groups}
    result = set()
    for vertex in obj.data.vertices:
        for assignment in vertex.groups:
            if assignment.weight > 1.0e-7 and assignment.group in names:
                result.add(names[assignment.group])
    return result


def zero_weight_vertices(obj: bpy.types.Object) -> int:
    return sum(
        1
        for vertex in obj.data.vertices
        if sum(assignment.weight for assignment in vertex.groups) <= 1.0e-7
    )


def ensure_armature_modifier(obj: bpy.types.Object, rig: bpy.types.Object) -> None:
    modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
    if not modifiers:
        modifier = obj.modifiers.new(name="V2ContractArmature", type="ARMATURE")
        modifier.object = rig
        return
    # A gameplay skeletal mesh must have one canonical deform pass.  Some v22
    # body pieces carry a second Faceit/preview armature modifier that points
    # at the same source rig.  Retargeting both modifiers applies the bind
    # transform twice and produces the stretched/imploded silhouette seen in
    # UE, even when the raw vertex and bone coordinates are valid.  Keep the
    # first deform modifier, repair it to the isolated contract rig, and remove
    # redundant armature modifiers from the in-memory export copy only.
    primary = modifiers[0]
    primary.object = rig
    for duplicate in modifiers[1:]:
        obj.modifiers.remove(duplicate)


def transfer_weights(target: bpy.types.Object, donor: bpy.types.Object) -> None:
    for donor_group in donor.vertex_groups:
        if target.vertex_groups.get(donor_group.name) is None:
            target.vertex_groups.new(name=donor_group.name)
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    modifier = target.modifiers.new(name="V2WeightTransfer_TEMP", type="DATA_TRANSFER")
    modifier.object = donor
    modifier.use_vert_data = True
    modifier.data_types_verts = {"VGROUP_WEIGHTS"}
    modifier.vert_mapping = "POLYINTERP_NEAREST"
    modifier.layers_vgroup_select_src = "ALL"
    modifier.layers_vgroup_select_dst = "NAME"
    modifier.mix_mode = "REPLACE"
    modifier.mix_factor = 1.0
    if hasattr(modifier, "use_object_transform"):
        modifier.use_object_transform = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def group_has_weights(obj: bpy.types.Object, group_name: str) -> bool:
    group = obj.vertex_groups.get(group_name)
    if group is None:
        return False
    return any(
        assignment.group == group.index and assignment.weight > 1.0e-7
        for vertex in obj.data.vertices
        for assignment in vertex.groups
    )


def merge_group(obj: bpy.types.Object, source_name: str, destination_name_value: str) -> None:
    """Merge an observed source group into a valid destination group."""
    if source_name == destination_name_value:
        return
    source = obj.vertex_groups.get(source_name)
    if source is None:
        return
    destination = obj.vertex_groups.get(destination_name_value)
    if destination is None:
        destination = obj.vertex_groups.new(name=destination_name_value)
    source_index = source.index
    weights = []
    for vertex in obj.data.vertices:
        for assignment in vertex.groups:
            if assignment.group == source_index and assignment.weight > 1.0e-7:
                weights.append((vertex.index, assignment.weight))
                break
    for vertex_index, weight in weights:
        destination.add([vertex_index], weight, "ADD")
    obj.vertex_groups.remove(source)


def normalize_weights(obj: bpy.types.Object) -> None:
    for vertex in obj.data.vertices:
        total = sum(assignment.weight for assignment in vertex.groups)
        if total <= 1.0e-7:
            continue
        for assignment in list(vertex.groups):
            obj.vertex_groups[assignment.group].add(
                [vertex.index], assignment.weight / total, "REPLACE"
            )


def repair_zero_weight_vertices(obj: bpy.types.Object, contract: set[str]) -> int:
    """Copy surviving contract weights from the nearest weighted vertex.

    This is deliberately a local, deterministic repair for isolated source
    vertices whose only assignments were invalid helper/deform groups.  It
    does not replace a garment's valid v22 weights with a whole-body transfer.
    """
    zero = [
        vertex for vertex in obj.data.vertices
        if sum(assignment.weight for assignment in vertex.groups) <= 1.0e-7
    ]
    if not zero:
        return 0
    weighted = [
        vertex for vertex in obj.data.vertices
        if sum(assignment.weight for assignment in vertex.groups) > 1.0e-7
    ]
    if not weighted:
        raise ValueError(f"{obj.name}: no weighted donor vertices remain")
    tree = kdtree.KDTree(len(weighted))
    for vertex in weighted:
        tree.insert(vertex.co, vertex.index)
    tree.balance()
    for vertex in zero:
        _, donor_index, _ = tree.find(vertex.co)
        donor = obj.data.vertices[donor_index]
        assignments = []
        for assignment in donor.groups:
            group = obj.vertex_groups[assignment.group]
            if group.name in contract and assignment.weight > 1.0e-7:
                assignments.append((group.name, assignment.weight))
        if not assignments:
            raise ValueError(f"{obj.name}: nearest donor has no contract weights for vertex {vertex.index}")
        for assignment in list(vertex.groups):
            obj.vertex_groups[assignment.group].remove([vertex.index])
        total = sum(weight for _, weight in assignments)
        for group_name, weight in assignments:
            obj.vertex_groups[group_name].add([vertex.index], weight / total, "REPLACE")
    return len(zero)


def cleanup_and_remap_groups(
    obj: bpy.types.Object,
    contract: set[str],
    semantic: dict[str, str],
    allow_drop_unmatched: bool = False,
) -> list[str]:
    dropped = []
    for group in list(obj.vertex_groups):
        destination = destination_name(group.name, semantic)
        if destination != group.name:
            merge_group(obj, group.name, destination)
    for group in list(obj.vertex_groups):
        if group.name in contract:
            continue
        if group_has_weights(obj, group.name):
            if not allow_drop_unmatched:
                raise ValueError(f"{obj.name}: unmatched used deform group {group.name}")
            dropped.append(group.name)
        obj.vertex_groups.remove(group)
    normalize_weights(obj)
    return dropped


def duplicate_mesh(source: bpy.types.Object, collection: bpy.types.Collection, label: str) -> bpy.types.Object:
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = f"EXPORT_{label}"
    collection.objects.link(obj)
    return obj


def rebind_orphan_controllers(obj: bpy.types.Object) -> dict[str, int]:
    """Move finger weights off the root-parented ARP controllers, on the EXPORT copy only.

    The stage weights finger phalanges 2-3 to `c_<finger>N.<s>`. Those are real deform
    bones and are correctly parented in Blender, but the live UE skeleton parents them to
    `root` -- siblings of the spine -- so nothing in the retarget drives them and the
    fingers tear.

    The fix cannot be a stage edit: ARP drives the `c_*` bones, so moving those weights in
    the stage stops the fingers deforming in Blender. It cannot be a hierarchy edit either:
    importing onto an existing skeleton leaves UE's stored hierarchy untouched, so a
    corrected parent map never reaches the engine.

    So it happens here, on the throwaway duplicate, immediately after it is made and before
    anything else touches it. `<finger>N_ref.<s>` is what `bone_map` renames into UE's
    correctly-chained deform family (`index2_ref_l -> index2_l -> index1_l -> hand_l`), and
    that family is exactly what the retargeter's finger chains drive
    (`LeftIndex: index1_l -> index3_l`). Each pair was verified coincident to <0.01 cm.

    The stage is never modified. Authoring keeps the bones ARP expects; the export carries
    the bones Unreal drives.
    """
    moved: dict[str, int] = {}
    names = {g.name for g in obj.vertex_groups}
    for finger in ("index", "middle", "ring", "pinky", "thumb"):
        for joint in (2, 3):
            for side in ("l", "r"):
                src = f"c_{finger}{joint}.{side}"
                dst = f"{finger}{joint}_ref.{side}"
                if src not in names:
                    continue
                src_group = obj.vertex_groups[src]
                weights = {}
                for v in obj.data.vertices:
                    for g in v.groups:
                        if g.group == src_group.index and g.weight > 1e-6:
                            weights[v.index] = g.weight
                if not weights:
                    continue
                if dst not in names:
                    obj.vertex_groups.new(name=dst)
                    names.add(dst)
                target = obj.vertex_groups[dst]
                for vi, w in weights.items():
                    target.add([vi], w, "ADD")
                src_group.remove(sorted(weights))
                moved[src] = len(weights)
    return moved


def duplicate_mesh_group(sources: list[bpy.types.Object], collection: bpy.types.Collection, label: str) -> bpy.types.Object:
    """Duplicate and join a separated pair/group without touching stage data."""
    duplicates = [duplicate_mesh(source, collection, label if len(sources) == 1 else f"{label}_{index}")
                  for index, source in enumerate(sources)]
    if len(duplicates) == 1:
        return duplicates[0]
    bpy.ops.object.select_all(action="DESELECT")
    for duplicate in duplicates:
        duplicate.select_set(True)
    bpy.context.view_layer.objects.active = duplicates[0]
    bpy.ops.object.join()
    duplicates[0].name = f"EXPORT_{label}"
    return duplicates[0]


def bake_export_units_cm(
    rig: bpy.types.Object,
    meshes: list[bpy.types.Object],
    *,
    scale_rig: bool = True,
) -> dict:
    """Bake the v22 metre graph into a centimetre export graph.

    Scaling only the FBX header (or setting ``global_scale``) leaves the
    imported bind matrices in metres.  That is the exact failure mode that
    collapses a mesh when centimeter mocap is evaluated on it.  The source
    stage is never touched: all objects passed here are in-memory duplicates.
    """
    # A skeletal FBX bind pose is evaluated from the exported mesh/object
    # matrix plus each skin cluster's link matrix.  The v22 stage contains
    # legitimate non-identity mesh transforms (notably the shirt rotation and
    # the body/accessory offsets).  Scaling only the object leaves those
    # transforms outside the baked vertex graph, which lets Unreal observe a
    # different FbxPose and cluster bind matrix and fall back to a time-zero
    # rebind.  Bake the complete mesh world transform into the in-memory
    # export copy, then leave the armature's origin/rotation authoritative and
    # scale only its bone graph to centimetres.  A canonical UE armature FBX is
    # already in the live centimeter bind space; scaling that rig again makes
    # its ref pose 100x too large while the mocap tracks remain canonical.
    for obj in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        obj.scale = tuple(float(value) * CM_BAKE_FACTOR for value in obj.scale)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if scale_rig:
        obj = rig
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        obj.scale = tuple(float(value) * CM_BAKE_FACTOR for value in obj.scale)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.context.view_layer.update()
    probe = rig.data.bones.get("spine_02_x") or rig.data.bones.get("c_spine_02_x")
    probe_head = [float(value) for value in probe.head_local] if probe else None
    probe_extent = max((abs(value) for value in probe_head), default=0.0)
    if probe is None or probe_extent < 5.0:
        raise ValueError(
            f"centimeter bake failed: spine probe extent {probe_extent:.6f} is still meter-scale"
        )
    return {
        # Keep the historical factor field for sidecar validators: mesh
        # geometry is still baked from the metre-authored v22 stage.
        "factor": CM_BAKE_FACTOR,
        "mesh_bake_factor": CM_BAKE_FACTOR,
        "rig_bake_factor": CM_BAKE_FACTOR if scale_rig else 1.0,
        "rig_scale_applied": bool(scale_rig),
        "rig_object_scale": [float(value) for value in rig.scale],
        "probe_bone": probe.name,
        "probe_head_local": probe_head,
        "probe_extent": probe_extent,
    }


def apply_canonical_hierarchy(rig: bpy.types.Object, parent_map: dict[str, str | None]) -> None:
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    if rig.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in rig.data.edit_bones:
        parent_name = parent_map.get(bone.name)
        bone.parent = rig.data.edit_bones.get(parent_name) if parent_name else None
        bone.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")


def prepare_unreal_root_shim(rig: bpy.types.Object, meshes: list[bpy.types.Object]) -> None:
    """Use the FBX armature object as the canonical UE ``root`` bone.

    Blender emits the armature object as a Null parent.  If the internal root
    bone is also exported, Unreal imports an unwanted extra parent and marks
    the mesh incompatible.  The live contract's root is non-deforming, so the
    internal bone is removed only from this in-memory final-export rig; all
    weighted bones remain unchanged.
    """
    for mesh in meshes:
        if group_has_weights(mesh, "root"):
            raise ValueError(f"{mesh.name}: root bone has weights; cannot use UE root shim")
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    if rig.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    root = rig.data.edit_bones.get("root")
    if root is None:
        # Auto-Rig Pro may already omit the non-deforming root from its
        # temporary export copy.  That is the desired final state; the
        # armature object becomes the UE root below.
        if len(rig.data.edit_bones) != 464:
            raise ValueError(
                f"final export root shim missing internal root with {len(rig.data.edit_bones)} remaining bones"
            )
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.name = "root"
        return
    for child in rig.data.edit_bones:
        if child.parent is root:
            child.parent = None
            child.use_connect = False
    rig.data.edit_bones.remove(root)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.name = "root"


def duplicate_rig(source: bpy.types.Object, collection: bpy.types.Collection) -> bpy.types.Object:
    rig = source.copy()
    rig.data = source.data.copy()
    rig.name = "EXPORT_SK_Melusina_V2_ContractRig"
    collection.objects.link(rig)
    # Blender's Object.copy() does not reliably preserve every ID property in
    # all background/add-on combinations.  ARP's exporter reads these
    # properties directly from the active armature object (not only from the
    # armature datablock), so copy the source metadata explicitly.  This is
    # done on the in-memory duplicate and never writes the v22 source stage.
    for key in source.keys():
        try:
            rig[key] = source[key]
        except (TypeError, ValueError, RuntimeError):
            # A non-serializable UI/pointer property is not part of the export
            # contract; the relevant scalar ARP properties are copied above.
            pass
    return rig


def import_canonical_armature(fbx_path: Path) -> bpy.types.Object:
    """Import the live UE bind armature and return only its 464-bone rig.

    UE exports the non-deforming ``root`` as the FBX armature object, so the
    imported armature intentionally has 464 internal bones.  The finalizer
    temporarily adds an internal root and removes it again in
    ``prepare_unreal_root_shim``.  Imported mesh objects are review payloads
    only and are removed from this in-memory Blender scene.
    """
    if not fbx_path.is_file():
        raise ValueError(f"canonical armature FBX not found: {fbx_path}")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(
        filepath=str(fbx_path),
        use_custom_normals=True,
        automatic_bone_orientation=False,
    )
    imported = [obj for obj in bpy.data.objects if obj not in before]
    armatures = [obj for obj in imported if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise ValueError(
            f"canonical armature FBX must import exactly one armature, got {len(armatures)}"
        )
    rig = armatures[0]
    if len(rig.data.bones) != 464:
        raise ValueError(
            f"canonical armature FBX must contain 464 internal bones, got {len(rig.data.bones)}"
        )
    for obj in imported:
        if obj is not rig:
            bpy.data.objects.remove(obj, do_unlink=True)
    return rig


def ensure_internal_root(rig: bpy.types.Object) -> None:
    """Add the temporary internal root expected by the contract finalizer."""
    if rig.data.bones.get("root"):
        return
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    if rig.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    root = rig.data.edit_bones.new("root")
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 1.0, 0.0)
    root.use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")


def sanitize_export_pose(rig: bpy.types.Object) -> dict:
    """Strip ARP controller state from the isolated gameplay export rig.

    The v22 source is an animator-facing ARP rig.  Its pose constraints and
    current controller pose are useful in Blender, but they are not part of a
    UE skeletal bind contract.  If exported, FBX can preserve those posed
    matrices as the bind/rest state; Unreal then evaluates canonical mocap
    against a different inverse bind and the mesh explodes.  The source rig is
    never edited: this only sanitizes the in-memory duplicate.
    """
    removed_constraints = 0
    if hasattr(rig.data, "pose_position"):
        rig.data.pose_position = "REST"
    for pose_bone in rig.pose.bones:
        removed_constraints += len(pose_bone.constraints)
        for constraint in list(pose_bone.constraints):
            pose_bone.constraints.remove(constraint)
        pose_bone.matrix_basis.identity()
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    return {
        "pose_position": getattr(rig.data, "pose_position", "UNKNOWN"),
        "removed_pose_constraints": removed_constraints,
    }


def remap_rig_and_groups(
    rig: bpy.types.Object,
    meshes: list[bpy.types.Object],
    contract: set[str],
    group_semantic: dict[str, str],
    bone_semantic: dict[str, str],
    drop: set[str],
    synthetic_bones: set[str],
    parent_map: dict[str, str | None],
    allow_drop_unmatched: bool = False,
) -> dict:
    proposed: dict[str, list[bpy.types.EditBone | bpy.types.Bone]] = {}
    helper_sources = set()
    for bone in rig.data.bones:
        src = bone.name
        dst = destination_name(src, bone_semantic)
        if sanitized(src).lower() in {item.lower() for item in drop} or dst in drop:
            helper_sources.add(src)
            continue
        proposed.setdefault(dst, []).append(bone)

    rename: dict[str, str] = {}
    collision_resolutions = []
    collision_drops = set()
    for destination, sources in proposed.items():
        if len(sources) == 1:
            rename[sources[0].name] = destination
            continue
        deform_sources = [source for source in sources if source.use_deform]
        if len(deform_sources) > 1:
            raise ValueError(
                f"multiple deform bones map to {destination}: {[source.name for source in deform_sources]}"
            )
        keep = deform_sources[0] if deform_sources else sources[0]
        rename[keep.name] = destination
        for source in sources:
            if source is keep:
                continue
            collision_drops.add(source.name)
        collision_resolutions.append({
            "destination": destination,
            "kept": keep.name,
            "dropped_non_authoritative": sorted(source.name for source in sources if source is not keep),
        })

    for source, destination in rename.items():
        bone = rig.data.bones.get(source)
        if bone:
            bone.name = destination
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    if rig.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in list(rig.data.edit_bones):
        if bone.name not in contract:
            rig.data.edit_bones.remove(bone)
    missing = sorted(contract - {bone.name for bone in rig.data.edit_bones})
    unexpected_missing = sorted(set(missing) - synthetic_bones)
    if unexpected_missing:
        bpy.ops.object.mode_set(mode="OBJECT")
        raise ValueError(f"contract bones missing after remap: {unexpected_missing[:16]}")
    root_bone = rig.data.edit_bones.get("root") or rig.data.edit_bones.get("root_x")
    for name in missing:
        new_bone = rig.data.edit_bones.new(name)
        if root_bone:
            new_bone.parent = root_bone
            new_bone.head = root_bone.head
            new_bone.tail = root_bone.tail
    # The v22 ARP rig has a valid name table but a different control-root
    # hierarchy from the live UE skeleton.  Reparent the in-memory export rig
    # to the authoritative UE hierarchy before every FBX write.  This keeps
    # the source weights while making the imported mesh genuinely compatible,
    # rather than merely pointing at the right Skeleton asset.
    apply_canonical_hierarchy(rig, parent_map)
    bpy.ops.object.mode_set(mode="OBJECT")
    if len(rig.data.bones) != len(contract):
        raise ValueError(f"export rig has {len(rig.data.bones)} bones, expected {len(contract)}")

    group_reports = []
    for mesh in meshes:
        dropped_groups = cleanup_and_remap_groups(
            mesh, contract, group_semantic, allow_drop_unmatched=allow_drop_unmatched
        )
        repaired_zero_weights = repair_zero_weight_vertices(mesh, contract)
        normalize_weights(mesh)
        actual = used_groups(mesh)
        unmatched = sorted(actual - contract)
        if unmatched:
            raise ValueError(f"{mesh.name}: unmatched used deform groups {unmatched[:12]}")
        group_reports.append({
            "mesh": mesh.name,
            "used_deform_groups": sorted(actual),
            "unmatched_used_groups": unmatched,
            "dropped_unmatched_groups": sorted(dropped_groups),
            "repaired_zero_weight_vertices": repaired_zero_weights,
            "zero_weight_vertices": zero_weight_vertices(mesh),
            "shape_key_count": len(mesh.data.shape_keys.key_blocks) if mesh.data.shape_keys else 0,
        })
    return {
        "export_bone_count": len(rig.data.bones),
        "export_bones": sorted(bone.name for bone in rig.data.bones),
        "group_reports": group_reports,
        "rename_count": len(rename),
        "drops": sorted(drop),
        "helper_sources_removed": sorted(helper_sources),
        "collision_resolutions": collision_resolutions,
        "collision_sources_removed": sorted(collision_drops),
        "synthetic_bones_added": missing,
    }


def arp_export(filepath: Path) -> tuple[bool, str]:
    namespace = getattr(bpy.ops, "arp", None)
    if namespace is None:
        return False, "bpy.ops.arp namespace unavailable"
    operator = getattr(namespace, "arp_export_fbx_panel", None)
    if operator is None:
        return False, "no ARP FBX export operator found"
    # The v22 source is an ARP rig, but the gameplay export is already the
    # canonical deform contract after remap.  Universal mode prevents ARP
    # from reclassifying the contract rig as a humanoid and consulting stale
    # ARP limb metadata.  The operator still owns the FBX write and cleanup.
    scene = bpy.context.scene
    saved_scene_settings = {}
    for name, value in {
        "arp_export_rig_type": "UNIVERSAL",
        "arp_export_rig_name": "SK_Melusina_Skeleton",
        "arp_ge_sel_only": True,
        "arp_ge_sel_bones_only": False,
    }.items():
        if hasattr(scene, name):
            saved_scene_settings[name] = getattr(scene, name)
            setattr(scene, name, value)
    # ARP's FBX panel is an ARP/M-ped exporter.  It is still required as the
    # source-stage export/preflight, but it intentionally emits a reduced
    # 387-bone M-ped table rather than the game's 465-bone contract.  Keep
    # that output as audit evidence and let the native contract finalizer
    # write the gameplay FBX after this function returns.
    audit_path = filepath.with_name(filepath.stem + ".arp.fbx")
    try:
        if audit_path.exists():
            audit_path.unlink()
        result = operator(filepath=str(audit_path), quick_export=True)
        if not audit_path.is_file() or audit_path.stat().st_size < 100:
            return False, f"ARP operator returned {result!r} but wrote no audit FBX"
        return True, "bpy.ops.arp.arp_export_fbx_panel"
    except Exception as exc:  # Blender/ARP signatures vary by release.
        return False, f"arp_export_fbx_panel: {exc}"
    finally:
        for name, value in saved_scene_settings.items():
            setattr(scene, name, value)


def enable_arp_addon(addon_path: str) -> str:
    """Enable Auto-Rig Pro from an extracted add-on directory in this process."""
    if not addon_path:
        return ""
    path = Path(addon_path).expanduser().resolve()
    if not path.is_dir() or not (path / "__init__.py").is_file():
        raise ValueError(f"ARP add-on directory must contain __init__.py: {path}")
    sys.path.insert(0, str(path.parent))
    bpy.ops.preferences.script_directory_add(directory=str(path.parent))
    module = path.name
    result = bpy.ops.preferences.addon_enable(module=module)
    if getattr(bpy.ops, "arp", None) is None:
        raise ValueError(f"ARP add-on enable returned {result!r} but bpy.ops.arp is unavailable")
    return str(path)


def reusable_arp_gate() -> bool:
    evidence = PROJECT / "Saved" / "Audit" / "melusina_v2_arp_probe_body.json"
    try:
        data = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not data.get("arp_export_gate_passed"):
        return False
    # Four retained ARP FBXs are additional evidence that the staged source
    # passed through the operator; the body probe report covers the body gate.
    return all((EXPORT_ROOT / f"SK_Melusina_V2_{label}.arp.fbx").is_file()
               for label in ("Shirt", "Skirt", "Boots", "Accessories"))


def blender_fbx_export(filepath: Path) -> None:
    bpy.ops.export_scene.fbx(
        filepath=str(filepath), use_selection=True, use_visible=True,
        object_types={"ARMATURE", "MESH"},
        # Applying evaluated modifiers here strips the v22 body's shape-key
        # datablock.  The bound stage is already the approved export mesh;
        # leave modifiers unapplied so morph targets survive the contract
        # finalization.  ARP's separate audit export may still evaluate its
        # own temporary copies.
        use_mesh_modifiers=False,
        use_mesh_modifiers_render=False, use_subsurf=False,
        use_mesh_edges=False, use_tspace=True, add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X",
        # The live contract includes non-deforming structural bones as well
        # as deform bones.  Omitting them would make the emitted table smaller
        # than SK_Melusina_Skeleton even though the mesh weights are valid.
        use_armature_deform_only=False, armature_nodetype="NULL",
        bake_anim=False, global_scale=1.0, apply_unit_scale=False,
        apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
    )


def main() -> int:
    ns = cli()
    try:
        arp_addon = enable_arp_addon(ns.arp_addon) if ns.arp_export and ns.arp_addon else ""
        if ns.arp_export and getattr(bpy.ops, "arp", None) is None:
            raise ValueError("--arp-export requires Auto-Rig Pro; pass --arp-addon or enable it in Blender")
        piece_map = pairs(ns.piece, grouped=True)
        donor_map = pairs(ns.donor)
        contract, group_semantic, bone_semantic, drop, synthetic_bones, parent_map = load_contract(
            Path(ns.contract_bones).resolve()
        )
        source_rig = bpy.data.objects.get(ns.rig)
        if not source_rig or source_rig.type != "ARMATURE":
            raise ValueError(f"armature not found: {ns.rig}")
        if ns.require_live_skeleton and source_rig.name != "character_rig":
            raise ValueError(f"live skeleton gate requires character_rig, got {source_rig.name}")
        for label, object_names in piece_map.items():
            for object_name in object_names:
                if not bpy.data.objects.get(object_name):
                    raise ValueError(f"piece {label}: object not found: {object_name}")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"[v2-bind] FATAL {exc}", flush=True)
        return 2

    export_collection = bpy.data.collections.new("Melusina_V2_Contract_Exports")
    bpy.context.scene.collection.children.link(export_collection)
    if ns.canonical_armature_fbx:
        canonical_rig = import_canonical_armature(Path(ns.canonical_armature_fbx).resolve())
        export_rig = duplicate_rig(canonical_rig, export_collection)
        ensure_internal_root(export_rig)
        # The FBX armature object must be named exactly ``root`` for the
        # validator/Unreal root-shim contract.  Remove the imported source
        # object after duplicating its datablocks so the final duplicate can
        # take that name without Blender suffixing it to ``root.001``.
        bpy.data.objects.remove(canonical_rig, do_unlink=True)
        rig_source_mode = "live_ue_canonical_armature_fbx"
    else:
        export_rig = duplicate_rig(source_rig, export_collection)
        rig_source_mode = "v22_character_rig"
    pose_report = sanitize_export_pose(export_rig)
    working_meshes = []
    rows = []
    try:
        for label, object_names in piece_map.items():
            sources = [bpy.data.objects[name] for name in object_names]
            mesh = duplicate_mesh_group(sources, export_collection, label)
            rebound = rebind_orphan_controllers(mesh)
            if rebound:
                print(f"[rebind] {label}: {sum(rebound.values())} finger weights "
                      f"c_* -> *_ref across {len(rebound)} groups")
            ensure_armature_modifier(mesh, export_rig)
            zero_weights = zero_weight_vertices(mesh)
            invalid_groups = any(
                destination_name(group.name, group_semantic) not in contract
                and group_has_weights(mesh, group.name)
                for group in mesh.vertex_groups
            )
            should_transfer = (zero_weights > 0 and ns.transfer_missing) or (invalid_groups and ns.transfer_invalid)
            if should_transfer:
                donor_name = donor_map.get(label)
                donor = bpy.data.objects.get(donor_name) if donor_name else None
                if not donor:
                    raise ValueError(f"{label}: transfer requested but donor is missing")
                transfer_weights(mesh, donor)
            working_meshes.append(mesh)

        rig_report = remap_rig_and_groups(
            export_rig, working_meshes, contract, group_semantic, bone_semantic,
            drop, synthetic_bones, parent_map,
            allow_drop_unmatched=ns.transfer_invalid or ns.drop_unmatched_groups
        )
        rig_report["pose_sanitize"] = pose_report
        rig_report["rig_source_mode"] = rig_source_mode
        rig_report["canonical_armature_fbx"] = ns.canonical_armature_fbx or None
        rig_report["cm_bake"] = bake_export_units_cm(
            export_rig,
            working_meshes,
            # The imported UE canonical armature already carries the live
            # centimeter bind matrices.  Only the v22 mesh geometry needs the
            # metre -> centimeter bake on this path.
            scale_rig=not bool(ns.canonical_armature_fbx),
        )
        for (label, object_names), mesh in zip(piece_map.items(), working_meshes):
            if any(row["zero_weight_vertices"] for row in rig_report["group_reports"] if row["mesh"] == mesh.name):
                raise ValueError(f"{label}: zero-weight vertices remain")
            bpy.ops.object.select_all(action="DESELECT")
            mesh.select_set(True)
            export_rig.select_set(True)
            bpy.context.view_layer.objects.active = export_rig
            EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
            fbx_path = EXPORT_ROOT / f"SK_Melusina_V2_{label}.fbx"
            exporter = "blender_fbx"
            if ns.arp_export:
                if ns.reuse_arp_gate:
                    if not reusable_arp_gate():
                        raise ValueError("recorded ARP source-stage gate evidence is unavailable or incomplete")
                    ok, detail = True, "bpy.ops.arp.arp_export_fbx_panel"
                else:
                    ok, detail = arp_export(fbx_path)
                if not ok and not ns.allow_blender_fbx:
                    raise ValueError(f"{label}: ARP exporter required but failed: {detail}")
                if ok:
                    # ARP has completed the source-compatible export/preflight;
                    # preserve the canonical 465-bone contract in the final
                    # gameplay FBX instead of accepting ARP's reduced M-ped
                    # skeleton.  The actual FBX audit validates this payload.
                    bpy.ops.object.select_all(action="DESELECT")
                    mesh.select_set(True)
                    export_rig.select_set(True)
                    bpy.context.view_layer.objects.active = export_rig
                    # ARP may restore source twist-bone relationships while
                    # producing its audit FBX. Reassert the live UE hierarchy
                    # immediately before the gameplay FBX write.
                    apply_canonical_hierarchy(export_rig, parent_map)
                    prepare_unreal_root_shim(export_rig, working_meshes)
                    bpy.ops.object.select_all(action="DESELECT")
                    mesh.select_set(True)
                    export_rig.select_set(True)
                    bpy.context.view_layer.objects.active = export_rig
                    blender_fbx_export(fbx_path)
                    exporter = detail + "+bpy.ops.export_scene.fbx(contract_finalize)"
                else:
                    blender_fbx_export(fbx_path)
                    exporter = f"blender_fbx_fallback_after_arp_failure:{detail}"
            else:
                blender_fbx_export(fbx_path)
            if not fbx_path.is_file() or fbx_path.stat().st_size < 100:
                raise ValueError(f"{label}: export missing or empty: {fbx_path}")
            row = next(item for item in rig_report["group_reports"] if item["mesh"] == mesh.name)
            row.update({
                "label": label,
                "source_object": ",".join(object_names),
                "fbx": str(fbx_path),
                "fbx_bytes": fbx_path.stat().st_size,
                "exporter": exporter,
                "export_bone_count": rig_report["export_bone_count"],
                "export_bones": rig_report["export_bones"],
                "skeleton": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton",
                "units": "centimeters_baked",
                "cm_bake_factor": CM_BAKE_FACTOR,
                "cm_bake_probe": rig_report["cm_bake"],
                "source_materials": [
                    slot.material.name if slot.material else None
                    for slot in mesh.material_slots
                ],
            })
            fbx_path.with_suffix(".json").write_text(
                json.dumps({
                    "schema": "melodia.melusina_v2_piece_sidecar.v1",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    **row,
                }, indent=2) + "\n",
                encoding="utf-8",
            )
            rows.append(row)
    except Exception as exc:
        report = {
            "schema": "melodia.melusina_v2_piece_bind_report.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ok": False,
            "promotion_allowed": False,
            "error": str(exc),
            "source_stage": bpy.data.filepath,
            "read_only_source": True,
        }
        report_path = Path(ns.report)
        if not report_path.is_absolute():
            report_path = PROJECT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    arp_gate_passed = bool(ns.arp_export) and all(
        str(row.get("exporter", "")).startswith("bpy.ops.arp.")
        for row in rows
    )
    report = {
        "schema": "melodia.melusina_v2_piece_bind_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": len(rows) == 5,
        "promotion_allowed": (
            len(rows) == 5
            and all(row["zero_weight_vertices"] == 0 for row in rows)
            and arp_gate_passed
        ),
        "source_stage": bpy.data.filepath,
        "read_only_source": True,
        "contract_bone_count": len(contract),
        "contract_bones": sorted(contract),
        "rig": rig_report,
        "pieces": rows,
        "arp_export_requested": ns.arp_export,
        "arp_addon": arp_addon,
        "arp_gate_reused_from_evidence": bool(ns.reuse_arp_gate),
        "arp_gate_evidence": (
            str(PROJECT / "Saved" / "Audit" / "melusina_v2_arp_probe_body.json")
            if ns.reuse_arp_gate else None
        ),
        "arp_export_gate_passed": arp_gate_passed,
        "promotion_blockers": [] if arp_gate_passed else [
            "approved_arp_export_required_for_gameplay_promotion"
        ],
    }
    report_path = Path(ns.report)
    if not report_path.is_absolute():
        report_path = PROJECT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["promotion_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
