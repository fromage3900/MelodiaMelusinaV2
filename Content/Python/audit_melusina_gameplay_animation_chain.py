"""Read-only audit of Melusina exploration and JRPG battle animation chains."""
import json
import re
import sys
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved" / "Audit" / "melusina_gameplay_animation_chain.json"
ASSETS = {
    "exploration": "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
    "exploration_abp": "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current",
    "battle": "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation",
    "locomotion_blendspace": "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion",
}
CANONICAL_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
BATTLE_ANIMATION_FIELDS = (
    ("introAnimationMontage", "intro_animation_montage", True),
    ("IdleAnimationMontage", "idle_animation_montage", True),
    ("idleAnimation", "idle_animation", True),
    ("dieAnimation", "die_animation", True),
    ("dashForwardAnimation", "dash_forward_animation", True),
    ("dashBackwardAnimation", "dash_backward_animation", True),
    ("attackAnimationMontage", "attack_animation_montage", True),
    ("getHitAnimationMontage", "get_hit_animation_montage", True),
    ("itemUseAnimationMontage", "item_use_animation_montage", True),
    ("stunAnimationMontage", "stun_animation_montage", True),
    ("victoryAnimationMontage", "victory_animation_montage", False),
)


def path(value):
    return value.get_path_name().split(".")[0] if value else ""


def prop(obj, *names):
    for name in names:
        try:
            value = obj.get_editor_property(name)
            if value is not None:
                return value
        except Exception:
            pass
    return None


def read_prop(obj, *names):
    """Return (found, value); distinguish an unreadable field from a null asset."""
    if obj is None:
        return False, None
    for name in names:
        try:
            return True, obj.get_editor_property(name)
        except Exception:
            pass
    return False, None


def normalized_component_name(raw_name):
    suffix = "_GEN_VARIABLE"
    return raw_name[:-len(suffix)] if raw_name.endswith(suffix) else raw_name


def load(asset_path):
    return unreal.EditorAssetLibrary.load_asset(asset_path)


def bp_cdo(asset_path):
    bp = load(asset_path)
    if not bp:
        return None, None, None
    # Discovery must never compile, reconstruct or save the owner Blueprint.
    generated = bp.generated_class()
    return bp, generated, unreal.get_default_object(generated) if generated else None


def component_row(comp, evidence):
    raw_name = comp.get_name()
    mesh = prop(comp, "skeletal_mesh_asset", "skeletal_mesh")
    anim_class = prop(comp, "anim_class")
    skeleton = prop(mesh, "skeleton") if mesh else None
    return {
        "component": normalized_component_name(raw_name),
        "raw_name": raw_name,
        "object_path": comp.get_path_name(),
        "class": comp.get_class().get_name(),
        "mesh": path(mesh),
        "skeleton": path(skeleton),
        "anim_class": anim_class.get_path_name() if anim_class else "",
        "animation_mode": str(prop(comp, "animation_mode")),
        "evidence": evidence,
    }


def component_contract(asset_path):
    bp, generated, cdo = bp_cdo(asset_path)
    rows = []
    for comp in list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []:
        rows.append(component_row(comp, "CDO_TEMPLATE"))
    scs_errors = []
    if bp:
        try:
            subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            library = unreal.SubobjectDataBlueprintFunctionLibrary
            for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
                obj = library.get_object(library.get_data(handle))
                if not obj or not isinstance(obj, unreal.SkeletalMeshComponent):
                    continue
                rows.append(component_row(obj, "SCS_TEMPLATE"))
        except Exception as exc:
            scs_errors.append("SCS template extraction failed: %s" % exc)
    parent = prop(bp, "parent_class")
    preferred_names = ("MelusinaPresentationMesh", "CharacterMesh0")
    body = next((row for preferred in preferred_names for evidence in ("SCS_TEMPLATE", "CDO_TEMPLATE")
                 for row in rows if row["component"] == preferred and row["evidence"] == evidence), None)
    errors = list(scs_errors)
    if not bp or not generated or not cdo:
        errors.append("Blueprint/CDO binding extraction missing: %s" % asset_path)
    if not body:
        errors.append("Required battle body binding missing: expected MelusinaPresentationMesh or CharacterMesh0")
    elif not body["skeleton"]:
        errors.append("Required battle body skeleton missing: %s" % body["component"])
    elif body["skeleton"] != CANONICAL_SKELETON:
        errors.append("Battle body skeleton mismatch: expected %s, target %s" % (CANONICAL_SKELETON, body["skeleton"]))
    if body and not body["anim_class"]:
        errors.append("Required battle body AnimClass missing: %s" % body["component"])
    elif body and body["anim_class"]:
        body_anim_skeleton = target_skeleton(body["anim_class"].split(".")[0])
        if not body_anim_skeleton:
            errors.append("Required battle body AnimClass skeleton missing: %s" % body["anim_class"])
        elif body_anim_skeleton != CANONICAL_SKELETON:
            errors.append("Battle body AnimClass skeleton mismatch: expected %s, target %s" % (CANONICAL_SKELETON, body_anim_skeleton))
    anim_class_paths = sorted({row["anim_class"].split(".")[0] for row in rows if row["anim_class"]})
    anim_class_dependencies = []
    for anim_class in anim_class_paths:
        anim_class_dependencies.append({"asset": anim_class, "class": "AnimBlueprint", "skeleton": target_skeleton(anim_class)})
        anim_class_dependencies.extend(dependencies(anim_class))
    return {
        "loads": bool(bp and generated and cdo),
        "generated_class": generated.get_path_name() if generated else "",
        "parent_class": parent.get_path_name() if parent else "",
        "skeletal_components": rows,
        "body_component": body,
        "anim_class_dependencies": anim_class_dependencies,
        "expected_skeleton": CANONICAL_SKELETON,
        "binding_missing": body is None,
        "errors": errors,
    }


registry = unreal.AssetRegistryHelpers.get_asset_registry()
options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=False,
    include_hard_management_references=False,
)


def dependencies(asset_path):
    package = unreal.Name(asset_path)
    deps = [str(item) for item in registry.get_dependencies(package, options)]
    rows = []
    for dep in sorted(set(deps)):
        data = registry.get_asset_by_object_path(unreal.Name(f"{dep}.{dep.rsplit('/', 1)[-1]}"))
        class_name = str(data.asset_class_path.asset_name) if data and data.is_valid() else ""
        if class_name in {"AnimSequence", "AnimMontage", "BlendSpace", "AimOffsetBlendSpace", "AnimBlueprint", "SkeletalMesh", "Skeleton"}:
            tag = data.get_tag_value("Skeleton") or data.get_tag_value("TargetSkeleton") or ""
            match = re.search(r"(/Game/[A-Za-z0-9_/]+)", str(tag))
            rows.append({"asset": dep, "class": class_name, "skeleton": match.group(1) if match else ""})
    return rows


def target_skeleton(asset_path):
    if not asset_path:
        return None
    data = registry.get_asset_by_object_path(unreal.Name(f"{asset_path}.{asset_path.rsplit('/', 1)[-1]}"))
    if not data or not data.is_valid():
        return None
    tag = data.get_tag_value("Skeleton") or data.get_tag_value("TargetSkeleton") or ""
    match = re.search(r"(/Game/[A-Za-z0-9_/]+)", str(tag))
    return match.group(1) if match else None


def find_live_actor(world, generated):
    if not world or not generated:
        return None
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, generated)
        return actors[0] if actors else None
    except Exception:
        return None


def battle_animation_edges(bp, generated, cdo, world):
    """Reflect the 11 inherited BP_UnitBase animation fields; defaults are potential bindings."""
    live = find_live_actor(world, generated)
    consumer = "BP_MelusinaSwordsman_Presentation"
    edges, errors, rows = [], [], []
    for reflected_name, python_name, required in BATTLE_ANIMATION_FIELDS:
        found, value = read_prop(live, python_name, reflected_name) if live else (False, None)
        evidence = "PIE_LIVE_INSTANCE_BINDING" if found else "EDITOR_CDO_POTENTIAL_NOT_EXECUTED"
        if not found:
            found, value = read_prop(cdo, python_name, reflected_name)
        target = path(value) or None if found else None
        skeleton = target_skeleton(target) if target else None
        if not found:
            errors.append("Battle animation field unreadable: %s" % reflected_name)
        row = {
            "source": ASSETS["battle"],
            "target": target,
            "consumer": consumer,
            "field": reflected_name,
            "required": required,
            "expected_skeleton": CANONICAL_SKELETON if required or target else None,
            "target_skeleton": skeleton,
            "evidence": evidence,
            "field_read": found,
        }
        edges.append(row)
        rows.append({"field": reflected_name, "target": target, "target_skeleton": skeleton, "required": required, "evidence": evidence})
    return edges, rows, errors


def reference_manifest(roots):
    """Registry-only expansion; never load hundreds of animation assets."""
    queue = list(roots)
    rows = {}
    traversable = {"Blueprint", "AnimBlueprint", "AnimSequence", "AnimMontage", "AnimComposite", "BlendSpace", "BlendSpace1D", "AimOffsetBlendSpace", "AimOffsetBlendSpace1D", "PoseAsset", "Skeleton", "SkeletalMesh", "IKRigDefinition", "IKRetargeter", "ControlRigBlueprint", "LevelSequence", "DataAsset", "PrimaryDataAsset", "DataTable", "UserDefinedStruct", "UserDefinedEnum"}
    while queue:
        package = queue.pop()
        if package in rows:
            continue
        data = registry.get_asset_by_object_path(package + "." + package.rsplit("/", 1)[-1])
        if not data.is_valid():
            continue
        kind = str(data.asset_class_path.asset_name)
        if package not in roots and kind not in traversable:
            continue
        hard = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True, include_soft_package_references=False)
        soft = unreal.AssetRegistryDependencyOptions(include_hard_package_references=False, include_soft_package_references=True)
        row = {"class": kind, "hard_dependencies": sorted(str(x) for x in registry.get_dependencies(package, hard)), "soft_dependencies": sorted(str(x) for x in registry.get_dependencies(package, soft))}
        rows[package] = row
        queue.extend(p for p in row["hard_dependencies"] + row["soft_dependencies"] if p.startswith("/Game/") and p not in rows)
    return {"registry_loading": registry.is_loading_assets(), "assets": rows}


def native_pose_edges():
    """Loaded native defaults, plus exact traversal animation callsites.

    Live component overrides win when this audit runs in PIE. A source callsite
    is potential reachability, never proof that a montage actually executed.
    """
    edges = []
    root = ASSETS["exploration"]
    cls = getattr(unreal, "MelodiaWaveHarpCombatComponent", None)
    component = unreal.get_default_object(cls) if cls else None
    evidence = "EDITOR_NATIVE_CDO_POTENTIAL_NOT_EXECUTED"
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world:
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        pawn = pc.get_controlled_pawn() if pc else None
        if pawn and cls:
            live = pawn.get_component_by_class(cls)
            if live:
                component, evidence = live, "PIE_LIVE_COMPONENT_BINDING"
    wave_fields = (
        ("cast_stance_anim", "CastStanceAnim"),
        ("cast_shoot_anim", "CastShootAnim"),
        ("charge_draw_anim", "ChargeDrawAnim"),
        ("charge_hold_anim", "ChargeHoldAnim"),
        ("charge_fire_anim", "ChargeFireAnim"),
    )
    for python_field, reflected_field in wave_fields:
        found, value = read_prop(component, python_field, reflected_field) if component else (False, None)
        target = path(value) or None if found else None
        edges.append({
            "source": root,
            "target": target,
            "consumer": "MelodiaWaveHarpCombatComponent",
            "field": reflected_field,
            "required": True,
            "expected_skeleton": CANONICAL_SKELETON,
            "target_skeleton": target_skeleton(target),
            "evidence": "PIE_LIVE_COMPONENT_BINDING" if evidence == "PIE_LIVE_COMPONENT_BINDING" else evidence,
            "field_read": found,
        })
    traversal = ROOT / "Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp"
    traversal_found = False
    if traversal.is_file():
        for number, line in enumerate(traversal.read_text(encoding="utf-8").splitlines(), 1):
            for target in re.findall(r'TEXT\("(/Game/[A-Za-z0-9_/]+)(?:\.[A-Za-z0-9_]+)?"\)', line):
                data = registry.get_asset_by_object_path(target + "." + target.rsplit("/", 1)[-1])
                if data.is_valid() and str(data.asset_class_path.asset_name) in {"AnimSequence", "AnimMontage"}:
                    traversal_found = True
                    edges.append({
                        "source": root,
                        "target": target,
                        "consumer": "MelodiaTraversalComponent",
                        "field": "DashRollMontage",
                        "required": True,
                        "expected_skeleton": CANONICAL_SKELETON,
                        "target_skeleton": target_skeleton(target),
                        "evidence": "SOURCE_CALLSITE_POTENTIAL_ONLY",
                        "source_file": traversal.relative_to(ROOT).as_posix(),
                        "line": number,
                    })
    if not traversal_found:
        edges.append({
            "source": root, "target": None, "consumer": "MelodiaTraversalComponent",
            "field": "DashRollMontage", "required": True,
            "expected_skeleton": CANONICAL_SKELETON, "target_skeleton": None,
            "evidence": "SOURCE_CALLSITE_MISSING",
        })
    return edges


world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
exploration = component_contract(ASSETS["exploration"])
battle = component_contract(ASSETS["battle"])
battle_bp, battle_generated, battle_cdo = bp_cdo(ASSETS["battle"])
battle_edges, battle_fields, battle_field_errors = battle_animation_edges(battle_bp, battle_generated, battle_cdo, world)
report = {
    "evidence": "EDITOR_CDO_AND_REGISTRY; PIE bindings only where explicitly labeled",
    "exploration": exploration,
    "battle": battle,
    "battle_animation_fields": battle_fields,
    "exploration_animation_dependencies": dependencies(ASSETS["exploration_abp"]) + dependencies(ASSETS["locomotion_blendspace"]),
    "battle_animation_dependencies": dependencies(ASSETS["battle"]) + battle["anim_class_dependencies"],
    "assets": ASSETS,
}

# Extend the existing animation gate, rather than introduce another verifier.
sys.path.insert(0, str(ROOT / "Tools"))
import melusina_anim_gate
import importlib
importlib.reload(melusina_anim_gate)
policy = json.loads((ROOT / "specs/anim_presets/melusina_locomotion_blend.json").read_text(encoding="utf-8"))["runtime_reference_policy"]
reference_graph = reference_manifest(policy["roots"])
native_edges = native_pose_edges()
native_edges.extend(battle_edges)
# Expand native targets too: their notifies/linked assets can themselves be stale.
native_targets = [edge["target"] for edge in native_edges if edge.get("target")]
native_graph = reference_manifest(native_targets)
reference_graph["assets"].update(native_graph["assets"])
reference_graph["registry_loading"] = reference_graph["registry_loading"] or native_graph["registry_loading"]
report["runtime_reference_graph"] = reference_graph
report["native_pose_edges"] = native_edges
report["retired_reference_gate"] = melusina_anim_gate.check_runtime_references(reference_graph, policy, native_edges)
report["retired_reference_gate"]["errors"].extend(battle["errors"])
report["retired_reference_gate"]["errors"].extend(battle_field_errors)

# Evaluate compatibility against the body skeleton configured on each character.
for key, dep_key in (("exploration", "exploration_animation_dependencies"), ("battle", "battle_animation_dependencies")):
    body_rows = report[key]["skeletal_components"]
    if key == "battle":
        body = report[key]["body_component"]
    else:
        body = next((row for row in body_rows if row["component"] == "CharacterMesh0"), body_rows[0] if body_rows else None)
    body_skeleton = body["skeleton"] if body else ""
    incompatible = [row for row in report[dep_key] if row["skeleton"] and body_skeleton and row["skeleton"] != body_skeleton]
    if key == "battle":
        incompatible.extend({"asset": row["target"], "class": "serialized_animation_field", "skeleton": row["target_skeleton"], "field": row["field"], "evidence": row["evidence"]}
                            for row in battle_fields if row["target"] and row["target_skeleton"] and row["target_skeleton"] != CANONICAL_SKELETON)
    report[key]["body_skeleton"] = body_skeleton
    report[key]["incompatible_animation_assets"] = incompatible
    report[key]["skeleton_compatible"] = bool(body_skeleton == CANONICAL_SKELETON and not incompatible) if key == "battle" else (not incompatible if body_skeleton else None)
    report[key]["component_binding_scope"] = "CDO components and read-only SCS templates; no Blueprint compile/reconstruct/save"

for row in report["battle"]["incompatible_animation_assets"]:
    report["retired_reference_gate"]["errors"].append(
        "Battle animation skeleton mismatch for %s: expected %s, target %s" %
        (row.get("field") or row["asset"], CANONICAL_SKELETON, row["skeleton"])
    )
report["retired_reference_gate"]["ok"] = not report["retired_reference_gate"]["errors"]
gate_errors = report["retired_reference_gate"]["errors"]
report["contract_summary"] = {
    "ok": report["retired_reference_gate"]["ok"],
    "missing": [error for error in gate_errors if "missing" in error.lower() or "no target" in error.lower() or "unreadable" in error.lower()],
    "mismatches": [error for error in gate_errors if "mismatch" in error.lower() or "disagrees" in error.lower()],
    "errors": gate_errors,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_ANIMATION_AUDIT: " + json.dumps({
    "exploration_anim_class": next((r["anim_class"] for r in report["exploration"]["skeletal_components"] if r["component"] == "CharacterMesh0"), ""),
    "exploration_dependencies": len(report["exploration_animation_dependencies"]),
    "exploration_compatible": report["exploration"]["skeleton_compatible"],
    "battle_anim_class": report["battle"]["body_component"]["anim_class"] if report["battle"]["body_component"] else "",
    "battle_dependencies": len(report["battle_animation_dependencies"]),
    "battle_compatible": report["battle"]["skeleton_compatible"],
    "retired_reference_gate_ok": report["retired_reference_gate"]["ok"],
    "retired_reference_violations": report["retired_reference_gate"]["violations"],
    "visual_completion": False,
}))
