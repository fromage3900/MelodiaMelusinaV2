"""Loaded-default audit and explicit read-only P0 observations for water hair."""
from __future__ import annotations

import json
import hashlib
import struct
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved/Audit/melusina_water_hair_audit.json"
BP = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
INSTANCE = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
EXPECTED = {"GerstnerScale": 0.0, "WaveSpeed": 0.0, "RefractionStrength": 0.0,
            "ShorelineWidth": 0.0, "ShorelineFoam": 0.0, "DepthFadeDistance": 0.0}


def sample_p0_fluid(*, read_pixels: bool = False) -> dict:
    """Read the current P0 pawn without activating, reattaching or changing FX.

    This is distinct from the legacy CDO/material audit below. Reacquire every
    component each call: a stale hair/hat reference must not survive re-equip.
    Optional full render-target readback stalls the GPU; never use it as a
    performance measurement. A changing buffer is not visual droplet acceptance.
    """
    import unreal

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world or "L_MelusinaHouse_P0" not in world.get_path_name():
        return {"status": "NO_P0_GAME_WORLD", "runtime_proven": False}
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    if not pawn or pawn.get_class().get_name() != "BP_MelusinaJRPGCharacter_C":
        return {"status": "WRONG_PAWN", "runtime_proven": False}
    components = {c.get_name(): c for c in pawn.get_components_by_class(unreal.SceneComponent)}
    result = {"status": "OBSERVED_ONLY", "runtime_proven": False,
              "world": world.get_path_name(), "pawn": pawn.get_path_name(),
              "game_seconds": unreal.GameplayStatics.get_time_seconds(world),
              "components": {}, "errors": [],
              "qualification": "One observation; active flags and buffer identity do not establish motion or visible FluidNinja output."}
    combat = next((c for c in pawn.get_components_by_class(unreal.ActorComponent)
                   if c.get_class().get_name() == "MelodiaWaveHarpCombatComponent"), None)
    result["cpp_chorus"] = {"component_present": combat is not None,
                            "enabled": combat.is_water_chorus_enabled() if combat else None,
                            "qualification": "Enabled is a gate, not successful-spawn or pixel-output proof."}
    for name in ("WaterHairFluid", "VFX_HairFlow"):
        component = components.get(name)
        if component is None:
            result["components"][name] = {"present": False}
            continue
        parent = component.get_attach_parent()
        result["components"][name] = {
            "present": True, "class": component.get_class().get_name(),
            "parent": parent.get_name() if parent else None,
            "socket": str(component.get_attach_socket_name()),
            "active": component.is_active(), "visible": component.is_visible(),
            "world_location": list(component.get_world_location().to_tuple()),
        }
        if isinstance(component, unreal.NiagaraComponent):
            asset = component.get_asset()
            result["components"][name].update({"asset": asset.get_path_name() if asset else None,
                                                "paused": component.is_paused()})
            if name == "WaterHairFluid":
                parameters = {}
                for parameter in ("User.SimSpeed", "User.Painter.BrushStrength", "User.Painter.BrushSize"):
                    try:
                        value, valid = component.get_variable_float(parameter)
                        parameters[parameter] = {"value": value, "valid": valid}
                    except Exception as exc:
                        parameters[parameter] = {"error": str(exc)}
                result["components"][name]["observed_parameters"] = parameters
    flow = components.get("VFX_HairFlow")
    if not isinstance(flow, unreal.NiagaraComponent):
        result["status"] = "MISSING_FLOW_RENDERER"
        return result
    try:
        interface = unreal.NiagaraFunctionLibrary.get_data_interface(
            unreal.NiagaraDataInterfaceTexture, flow, "User.NinjaVelocityDensityBuffer")
        if interface is None:
            result["status"] = "MISSING_FLOW_TEXTURE_INTERFACE"
            return result
        texture = interface.get_editor_property("texture")
        result["flow_texture_interface"] = {
            "class": interface.get_class().get_name(),
            "texture_candidate": texture.get_path_name() if texture else None,
            "texture_class": texture.get_class().get_name() if texture else None,
            "texture_user_parameter_binding": interface.get_editor_property("texture_user_parameter").export_text(),
            "qualification": "DI texture property observed; resolve any texture-user binding before calling this the renderer's effective input."}
        result["readback"] = {"status": "NOT_REQUESTED"}
        if read_pixels:
            if not isinstance(texture, unreal.TextureRenderTarget2D):
                result["readback"] = {"status": "NO_RENDER_TARGET_CANDIDATE"}
            else:
                # A single readback per sample, rather than repeated per-pixel
                # GPU flushes. Bound size to the intended small character sim.
                width = texture.get_editor_property("size_x")
                height = texture.get_editor_property("size_y")
                if width * height > 512 * 512:
                    result["readback"] = {"status": "SIZE_LIMIT", "width": width, "height": height}
                else:
                    raw = unreal.RenderingLibrary.read_render_target_raw(world, texture, False)
                    # Python may elide a bool return into Array-or-None, as it
                    # does for collision traces. Keep explicit tuple variants
                    # readable too; never interpret a bool as pixel data.
                    if isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[0], bool):
                        success, pixels = raw
                    elif isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[1], bool):
                        pixels, success = raw
                    else:
                        pixels, success = raw, raw is not None
                    if not success or len(pixels) != width * height:
                        result["readback"] = {"status": "READBACK_FAILED"}
                    else:
                        digest = hashlib.sha256()
                        for colour in pixels:
                            digest.update(struct.pack("<4f", colour.r, colour.g, colour.b, colour.a))
                        result["readback"] = {"status": "SAMPLED_CANDIDATE_RT", "width": width,
                                                "height": height, "pixels": len(pixels), "sha256": digest.hexdigest()}
    except Exception as exc:
        result["status"] = "INCOMPLETE_BINDING_OBSERVATION"
        result["errors"].append(str(exc))
    return result


def main() -> dict:
    """Check loaded defaults/materials. This is not a possessed-pawn PIE test."""
    import unreal

    bp = unreal.EditorAssetLibrary.load_asset(BP)
    generated = bp.generated_class() if bp else None
    cdo = unreal.get_default_object(generated) if generated else None
    components = list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []
    body = next((c for c in components if c.get_name() == "CharacterMesh0"), None)
    hair = next((c for c in components if c.get_name() == "WaterHairMesh"), None)
    mi = unreal.EditorAssetLibrary.load_asset(INSTANCE)
    safe = {}
    if mi:
        for name, expected in EXPECTED.items():
            value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, name)
            safe[name] = {"value": float(value), "expected": expected, "ok": abs(value - expected) < 0.0001}
    runtime_materials = list(hair.get_materials()) if hair else []
    hair_anim_class = hair.get_editor_property("anim_class") if hair else None
    checks = {
        "native_component_exists": bool(hair),
        "mesh_matches": bool(hair and (hair.get_editor_property("skeletal_mesh_asset") or hair.get_editor_property("skeletal_mesh")).get_path_name().startswith(MESH)),
        "attached_to_body": bool(hair and hair.get_attach_parent() is body),
        "copy_pose_anim_class": bool(hair_anim_class and hair_anim_class.get_path_name().startswith(HAIR_ABP)),
        "runtime_slot_count": len(runtime_materials),
        "runtime_slots_use_instance": len(runtime_materials) == 4 and all(m and m.get_path_name().startswith(INSTANCE) for m in runtime_materials),
        "parent_matches": bool(mi and mi.get_editor_property("parent").get_path_name().startswith(PARENT)),
        "safe_overrides": safe,
    }
    failures = [name for name, value in checks.items() if name != "safe_overrides" and not value]
    failures.extend(name for name, value in safe.items() if not value["ok"])
    result = {"blueprint": BP, "instance": INSTANCE, "runtime_component": "WaterHairMesh",
              "proof_scope": "LOADED_BLUEPRINT_DEFAULTS_AND_MATERIAL_ONLY", "runtime_proven": False,
              "checks": checks, "failures": failures, "ok": not failures}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Melusina water hair audit: " + json.dumps({"ok": result["ok"], "failures": failures}))
    return result


if __name__ == "__main__":
    main()
