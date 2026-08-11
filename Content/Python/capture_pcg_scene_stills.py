"""Synchronous, non-PIE SceneCapture2D stills for the PCG proof levels."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path


PROOFS = (
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ResonanceCathedral",
        "Resonance Cathedral Overview Camera",
        "PCG_Hero_ResonanceCathedral_SceneStill.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ArpeggioBridge",
        "Arpeggio Bridge Overview Camera",
        "PCG_Hero_ArpeggioBridge_SceneStill.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_BellTreeGarden",
        "BellTreeGarden Overview Camera",
        "PCG_Hero_BellTreeGarden_SceneStill.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_XylophoneTrail",
        "Xylophone Trail Overview Camera",
        "PCG_Hero_XylophoneTrail_SceneStill.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_CrystalHarpGrove",
        "Crystal Harp Grove Overview Camera",
        "PCG_Hero_CrystalHarpGrove_SceneStill.png",
    ),
)


def _fov(camera, fallback: float = 40.0) -> float:
    try:
        if "Resonance Cathedral" in str(camera.get_actor_label()):
            return 70.0
    except Exception:
        pass
    try:
        component = camera.get_cine_camera_component()
        focal = float(component.get_editor_property("current_focal_length") or 0.0)
        if focal > 0.0:
            return math.degrees(2.0 * math.atan(18.0 / focal))
    except Exception:
        pass
    return fallback


def capture() -> dict:
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    output_dir = Path(unreal.Paths.project_saved_dir()) / "Audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for level_path, camera_label, filename in PROOFS:
        if not level_editor.load_level(level_path):
            raise RuntimeError(f"could not load proof level: {level_path}")
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        # Proof maps intentionally keep interactive actors separate from
        # generated static branches. Re-run the host once after load so the
        # still reflects the current graph/profile instead of any stale
        # serialized ISM state from an earlier authoring pass.
        for actor in actor_subsystem.get_all_level_actors() or []:
            component = actor.get_component_by_class(unreal.PCGComponent)
            if not component:
                continue
            # Reset the local generated state without removing the component
            # shell, then allow four editor recook ticks for static spawners.
            # A direct generate on a freshly loaded UE 5.8 PCG component can
            # report Generated=True while still owning zero live ISMs.
            try:
                component.cleanup_local(False)
            except Exception:
                pass
            for _ in range(4):
                try:
                    component.generate_local(True)
                except Exception:
                    pass
                try:
                    component.generate(True)
                except Exception:
                    pass
                time.sleep(0.8)
        time.sleep(0.8)
        actors = actor_subsystem.get_all_level_actors() or []
        camera = next((actor for actor in actors if actor.get_actor_label() == camera_label), None)
        if camera is None:
            raise RuntimeError(f"overview camera missing: {camera_label}")

        width, height = 1920, 1080
        render_target = unreal.RenderingLibrary.create_render_target2d(
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),
            width,
            height,
            unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
            False,
        )
        if not render_target:
            raise RuntimeError(f"render target creation failed: {level_path}")

        capture_actor = actor_subsystem.spawn_actor_from_class(
            unreal.SceneCapture2D.static_class(),
            camera.get_actor_location(),
            camera.get_actor_rotation(),
        )
        if not capture_actor:
            raise RuntimeError(f"SceneCapture2D spawn failed: {level_path}")
        try:
            components = capture_actor.get_components_by_class(unreal.SceneCaptureComponent2D)
            if not components:
                raise RuntimeError(f"SceneCapture2D component missing: {level_path}")
            component = components[0]
            component.set_editor_property("texture_target", render_target)
            component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            component.set_editor_property("capture_every_frame", False)
            component.set_editor_property("capture_on_movement", False)
            component.set_editor_property("fov_angle", _fov(camera))
            component.capture_scene()
            output_path = output_dir / filename
            unreal.RenderingLibrary.export_render_target(
                unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),
                render_target,
                str(output_dir),
                filename,
            )
            rows.append({"level": level_path, "camera": camera_label, "output": str(output_path)})
        finally:
            actor_subsystem.destroy_actor(capture_actor)

    result = {"ok": True, "pie": False, "captures": rows}
    unreal.log(f"[PCG Scene Stills] {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(json.dumps(capture(), indent=2))
