"""Fixed-frame lookdev A/B rig (editor only).

Every lookdev decision compares two material instances in ONE frame with fixed exposure,
or it is opinion. See Docs/Research/UE58_LOOKDEV_PIPELINE_RESEARCH_2026-09-17.md section 5.

    lookdev_ab_rig.py <pair_id> <mi_a> <mi_b> [mesh] [--cvar name=value ...]

- Scratch map /Game/Melodia/Lookdev/L_Lookdev_ToonAB is created on first run (never a shipped level).
- HDRIBackdrop when the plugin class exists, else SkyLight + DirectionalLight.
- One unbound PostProcessVolume with manual exposure (fixed EV) so A and B share the frame.
- The same mesh twice, 200 cm apart, same rotation; A = current master MI, B = variant MI.
- SceneCapture2D -> ImageWriteBlueprintLibrary.export_to_disk (AutomationLibrary screenshots wrote nothing on 09-17).
- Receipt Saved/Audit/lookdev_ab_<pair>_<date>.json; the verdict field is left for the owner.

Rules honoured: never edits a material or master; never touches the frozen PPV; cvars toggled
here are restored to their prior value before exit.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import unreal

AL = unreal.EditorAssetLibrary
LEVEL_DIR = "/Game/Melodia/Lookdev"
LEVEL_PATH = f"{LEVEL_DIR}/L_Lookdev_ToonAB"
DEFAULT_MESH = "/Game/EnvSandbox/Meshes/Environment/flower_redA/StaticMeshes/flower_redA"
FIXED_EV = -1.5  # manual exposure bias (physical camera off): exposure == 2^bias
SUBJECT_SCALE = 6.0


def _project_dir() -> str:
    return unreal.Paths.project_dir().rstrip("/")


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def ensure_level() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    rec = {"level": LEVEL_PATH}
    if AL.does_asset_exist(LEVEL_PATH):
        rec["created"] = False
        current = _world().get_path_name().split(".")[0] if _world() else ""
        if current != LEVEL_PATH:
            les.load_level(LEVEL_PATH)
        rec["already_open"] = current == LEVEL_PATH
    else:
        if not AL.does_directory_exist(LEVEL_DIR):
            AL.make_directory(LEVEL_DIR)
        rec["created"] = bool(les.new_level(LEVEL_PATH))
    return rec


def _spawn(cls, loc, rot=None, label=None):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator(0, 0, 0))
    if label:
        a.set_actor_label(label)
    return a


def clear_rig():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith("LookdevAB_"):
            eas.destroy_actor(a)
            n += 1
    return n


def build_lighting() -> dict:
    rec = {}
    hdri_cls = getattr(unreal, "HDRIBackdrop", None)
    if hdri_cls is not None:
        try:
            a = _spawn(hdri_cls, unreal.Vector(0, 0, 0), label="LookdevAB_HDRI")
            rec["hdri_backdrop"] = a.get_path_name()
        except Exception as exc:  # plugin class present but blueprint spawn failed
            rec["hdri_backdrop_error"] = str(exc)[:200]
    if "hdri_backdrop" not in rec:
        # Neutral daylight without SkyAtmosphere: SceneCapture2D + SkyAtmosphere filled the RT
        # with black on 09-17 (diag: hiding the atmosphere restored a readable image).
        sun = _spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-45.0, 35.0, 0.0), label="LookdevAB_Sun")
        sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
        sc.set_editor_property("intensity", 8.0)
        sky = _spawn(unreal.SkyLight, unreal.Vector(0, 0, 300), label="LookdevAB_Sky")
        skc = sky.get_component_by_class(unreal.SkyLightComponent)
        skc.set_editor_property("real_time_capture", True)
        skc.set_editor_property("intensity", 1.0)
        rec["fallback_lights"] = [sky.get_path_name(), sun.get_path_name()]
    ppv = _spawn(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), label="LookdevAB_PPV")
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    # Fixed exposure: manual metering with the physical camera OFF, so exposure == 2^bias and a
    # SceneCapture does not need frames to converge. A and B share the frame exactly.
    s.set_editor_property("override_auto_exposure_method", True)
    s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", FIXED_EV)
    ppv.set_editor_property("settings", s)
    rec["ppv"] = {"unbound": True, "exposure": "manual, physical camera off", "bias": FIXED_EV}
    floor = _spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, -1), label="LookdevAB_Floor")
    plane = AL.load_asset("/Engine/BasicShapes/Plane")
    fc = floor.get_component_by_class(unreal.StaticMeshComponent)
    fc.set_static_mesh(plane)
    floor.set_actor_scale3d(unreal.Vector(20, 20, 1))
    return rec


def place_subjects(mesh_path: str, mi_a: str, mi_b: str) -> dict:
    mesh = AL.load_asset(mesh_path)
    if not mesh:
        raise RuntimeError(f"mesh missing: {mesh_path}")
    ma, mb = AL.load_asset(mi_a), AL.load_asset(mi_b)
    if not ma or not mb:
        raise RuntimeError(f"MI missing: {mi_a if not ma else mi_b}")
    out = {"mesh": mesh_path, "a": {}, "b": {}}
    for key, mi, x in (("a", ma, -100.0), ("b", mb, 100.0)):
        act = _spawn(unreal.StaticMeshActor, unreal.Vector(x, 0, 0), unreal.Rotator(0, 0, 0), label=f"LookdevAB_{key.upper()}")
        c = act.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        act.set_actor_scale3d(unreal.Vector(SUBJECT_SCALE, SUBJECT_SCALE, SUBJECT_SCALE))
        slots = c.get_num_materials()
        # Put the MI on every slot so the comparison is the material, not the kit's slot layout.
        for i in range(slots):
            c.set_material(i, mi)
        parent = mi.get_editor_property("parent")
        out[key] = {"mi": mi.get_path_name(), "parent": parent.get_path_name() if parent else None, "slots": slots, "x": x}
    return out


def capture(pair_id: str, stamp: str, cvars: dict) -> list:
    world = _world()
    out_dir = f"{_project_dir()}/Saved/Audit/Screens"
    os.makedirs(out_dir, exist_ok=True)
    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False)
    cam = _spawn(unreal.SceneCapture2D, unreal.Vector(0, -520, 140), label="LookdevAB_Cam")
    comp = cam.get_editor_property("capture_component2d")
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    comp.set_editor_property("fov_angle", 45.0)
    comp.set_editor_property("capture_every_frame", False)
    comp.set_editor_property("capture_on_movement", False)
    # the PPV is unbound, so the capture inherits the manual exposure
    shots = []
    views = {"front": (unreal.Vector(0, -520, 140), unreal.Vector(0, 0, 60)),
             "three_quarter": (unreal.Vector(-380, -380, 200), unreal.Vector(0, 0, 60)),
             "top": (unreal.Vector(0, -1, 700), unreal.Vector(0, 0, 0))}
    for name, (loc, look) in views.items():
        rot = unreal.MathLibrary.find_look_at_rotation(loc, look)
        cam.set_actor_location_and_rotation(loc, rot, False, False)
        comp.capture_scene()
        fn = f"{out_dir}/lookdev_ab_{pair_id}_{name}_{stamp}.png"
        opts = unreal.ImageWriteOptions()
        opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
        opts.set_editor_property("overwrite_file", True)
        opts.set_editor_property("async_", False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, fn, opts)
        shots.append({"view": name, "file": fn, "exists": os.path.exists(fn)})
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(cam)
    return shots


def run(pair_id: str, mi_a: str, mi_b: str, mesh_path: str = DEFAULT_MESH, cvars: dict | None = None) -> dict:
    cvars = cvars or {}
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rec = {
        "schema": "melodia.lookdev_ab.v1",
        "pair_id": pair_id,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": None,  # owner writes ADOPT-as-variant | PARK | REJECT
        "verdict_by": None,
        "rules": ["no material edited", "frozen PPV untouched (this map has its own unbound PPV)", "scratch map only"],
    }
    rec["level"] = ensure_level()
    rec["cleared_prior_rig_actors"] = clear_rig()
    rec["lighting"] = build_lighting()
    rec["subjects"] = place_subjects(mesh_path, mi_a, mi_b)
    world = _world()
    prior = {}
    for k, v in cvars.items():
        try:
            prior[k] = unreal.SystemLibrary.get_console_variable_float_value(k)
        except Exception:
            prior[k] = None
        unreal.SystemLibrary.execute_console_command(world, f"{k} {v}")
    rec["cvars"] = {"set": cvars, "prior": prior}
    try:
        rec["stills"] = capture(pair_id, stamp, cvars)
    finally:
        for k, v in prior.items():
            if v is not None:
                unreal.SystemLibrary.execute_console_command(world, f"{k} {v}")
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    rec["level_saved"] = bool(les.save_current_level())
    receipt = f"{_project_dir()}/Saved/Audit/lookdev_ab_{pair_id}_{stamp}.json"
    with open(receipt, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    rec["receipt"] = receipt
    return rec


def main(argv: list[str]) -> dict:
    args = [a for a in argv if not a.startswith("--cvar")]
    cvars = {}
    for a in argv:
        if a.startswith("--cvar="):
            k, _, v = a[len("--cvar="):].partition("=")
            cvars[k] = v
    if len(args) < 3:
        raise SystemExit(__doc__)
    mesh = args[3] if len(args) > 3 else DEFAULT_MESH
    return run(args[0], args[1], args[2], mesh, cvars)


if __name__ == "__main__":
    result = main(sys.argv[1:])
    unreal.log(json.dumps({k: result[k] for k in ("pair_id", "receipt", "stills")}, indent=1))
