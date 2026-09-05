"""Deterministic level captures for look-dev A/B work.

Why this exists rather than take_high_res_screenshot: that call needs a game
viewport and silently produces no file from an editor-only session. A
SceneCapture2D rendered to a render target works headlessly and is repeatable,
which is what an A/B comparison needs.

Usage (editor Python console):

    import lookdev_capture as lc; lc.capture('before.png', (0, -120000, 45000), -22, 90)

Rotation is passed as explicit pitch/yaw -- never build a Rotator positionally,
`unreal.Rotator(a, b, c)` is (roll, pitch, yaw) and getting that wrong is what
leaves the viewport rolled on its side.
"""
import unreal

W, H = 1280, 720
RT_PATH = "/Game/EnvSandbox/Temp/RT_LookdevCapture"
LABEL = "TEMP_LookdevCapture"


def _render_target(width=W, height=H):
    rt = unreal.load_asset(RT_PATH)
    if rt is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        rt = tools.create_asset("RT_LookdevCapture", "/Game/EnvSandbox/Temp",
                                unreal.TextureRenderTarget2D,
                                unreal.TextureRenderTargetFactoryNew())
    rt.set_editor_property("size_x", width)
    rt.set_editor_property("size_y", height)
    rt.set_editor_property("render_target_format",
                           unreal.TextureRenderTargetFormat.RTF_RGBA8)
    return rt


def cleanup():
    """Remove any capture actors left behind by an interrupted run."""
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    stale = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.SceneCapture2D) if a.get_actor_label().startswith(LABEL)]
    for a in stale:
        unreal.EditorLevelLibrary.destroy_actor(a)
    return len(stale)


def capture(out_name, location, pitch, yaw, fov=70.0, width=W, height=H):
    """Render the current level from a fixed camera to Saved/Audit/<out_name>."""
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()

    rt = _render_target(width, height)

    rot = unreal.Rotator()
    rot.roll = 0.0
    rot.pitch = float(pitch)
    rot.yaw = float(yaw)

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D, unreal.Vector(*location), rot)
    actor.set_actor_label(LABEL)
    try:
        comp = actor.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("fov_angle", float(fov))
        comp.set_editor_property("capture_source",
                                 unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property("capture_every_frame", False)
        comp.set_editor_property("capture_on_movement", False)
        comp.capture_scene()

        out_dir = unreal.Paths.project_saved_dir() + "Audit"
        unreal.RenderingLibrary.export_render_target(world, rt, out_dir, out_name)
    finally:
        # always remove the temp actor, even if the capture raised
        unreal.EditorLevelLibrary.destroy_actor(actor)

    print("WROTE Saved/Audit/%s" % out_name)
    return "Saved/Audit/" + out_name
