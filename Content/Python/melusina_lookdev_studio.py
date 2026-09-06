# -*- coding: utf-8 -*-
"""Melusina lookdev studio — controlled rig for matching the Blender EEVEE reference.

Reference: ._site_aside_untracked/melusina_beauty_eevee_20260715_01.png
  lavender/periwinkle hair · warm brown skin · pink bodice + sleeves
  layered pink/navy skirt w/ treble-clef motif · pink boots · soft rim light

Reuses the 3-point + rim rig, Nikki PPV contract and cine-camera framing from
Content/Python/build_material_render_studio_grid.py (setup_lights/setup_ppv/
setup_camera). Deliberately NO SkyAtmosphere / UltraDynamicSky — the studio
doctrine is controlled light, which is what makes frames comparable to an
offline render.

The CineCamera sets auto_activate_for_player=Player0, so PIE views THROUGH it.
That avoids the character's third-person boom, which collapses inside her mesh.

Run (one editor, serialized):
    exec(open(r"<repo>/Content/Python/melusina_lookdev_studio.py").read())
    build_melusina_studio()      # once
    # then start PIE and:
    shoot("iter03_note")
"""
import os
import unreal

LEVEL = "/Game/EnvSandbox/Materials/RenderStudio/L_Melusina_Lookdev"
MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
OUT = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/lookdev"


def _les():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _find(label):
    for a in _les().get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def build_melusina_studio():
    """Idempotent: spawn subject, 3-point rig, PPV and cine camera if absent."""
    made = []

    # Subject
    if not _find("Lookdev_Melusina"):
        sk = unreal.load_asset(MESH)
        if not sk:
            print(f"[studio] mesh missing: {MESH}")
            return
        a = _les().spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.skeletal_mesh_component.set_skinned_asset_and_update(sk)
        a.set_actor_label("Lookdev_Melusina")
        made.append("Lookdev_Melusina")

    # 3-point + rim, values lifted from build_material_render_studio_grid.setup_lights
    rig = [
        ("Lookdev_Key",  unreal.Vector(0, 0, 2600),      unreal.Rotator(-50, 0, 0),    6.0, (1.00, 0.97, 0.92), 5600.0),
        ("Lookdev_Fill", unreal.Vector(-1800, -2000, 1200), unreal.Rotator(-20, 40, 0),  2.5, (0.85, 0.90, 1.00), 6500.0),
        ("Lookdev_Rim",  unreal.Vector(2000, -1500, 800), unreal.Rotator(-15, -140, 0), 1.4, (1.00, 0.80, 0.70), 4500.0),
    ]
    for label, loc, rot, intensity, rgb, temp in rig:
        if _find(label):
            continue
        a = _les().spawn_actor_from_class(unreal.DirectionalLight, loc, rot)
        if a is None:
            continue
        c = a.light_component
        c.set_editor_property("intensity", intensity)
        # light_color is a Color (8-bit) property; the LinearColor setter method is the
        # supported path. set_editor_property with a LinearColor raises NativizeProperty.
        c.set_light_color(unreal.LinearColor(*rgb, 1.0), False)
        try:
            c.set_editor_property("use_temperature", True)
            c.set_editor_property("temperature", temp)
        except Exception:
            pass
        a.set_actor_label(label)
        made.append(label)

    # PPV — manual exposure so frames are comparable run to run
    if not _find("Lookdev_PPV"):
        a = _les().spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
        if a:
            a.set_editor_property("unbound", True)
            pp = a.settings
            pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            pp.set_editor_property("auto_exposure_bias", 11.0)
            pp.set_editor_property("bloom_intensity", 0.18)
            pp.set_editor_property("vignette_intensity", 0.15)
            a.set_actor_label("Lookdev_PPV")
            made.append("Lookdev_PPV")

    # Cine camera — auto-activates for Player0 so PIE renders through it
    if not _find("Lookdev_Cam"):
        a = _les().spawn_actor_from_class(
            unreal.CineCameraActor, unreal.Vector(0, -320, 105), unreal.Rotator(-4, 90, 0))
        if a:
            a.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
            cam = a.get_cine_camera_component()
            cam.set_editor_property("current_focal_length", 55.0)
            a.set_actor_label("Lookdev_Cam")
            made.append("Lookdev_Cam")

    ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print(f"[studio] created={made or 'nothing (all present)'} saved={ok}")


# WORKING CAPTURE RECIPE (verified 2026-09-03).
#
# Do NOT use PIE + take_high_res_screenshot for this: in a freshly created level it
# writes the same 38,667-byte black frame every call regardless of lighting or
# exposure. capture_scene_preview renders reliably and isolates the character, which
# is what you want when matching an offline render.
#
# Camera must be on the +Y side. From -Y she is backlit to silhouette.
#
#   monolith editor_query capture_scene_preview
#     asset_path  /Game/Melodia/Characters/Melusina/SK_Melusina
#     asset_type  skeletal_mesh
#     resolution  [1100, 1500]
#     camera      {"location": [0, 260, 95], "rotation": [-4, -90, 0], "fov": 42}
#     output_path <repo>/Saved/Audit/lookdev/melusina_<tag>.png
#
# OPEN DELTAS vs melusina_beauty_eevee_20260715_01.png (iter07 baseline):
#   1. HAIR ABSENT — she renders bald. Biggest gap; check groom/hair mesh + opacity.
#   2. Bodice renders GREY, reference is pink/lavender with heart + scroll embroidery.
#   3. Skirt trim renders GOLD/YELLOW, reference is pink/lavender.
#   4. Stockings render BLACK, reference is white.
#   5. Boots too dark/desaturated (purple vs reference pink).
# Already correct: skirt panels, hat, skin tone, bow silhouette.

CAPTURE = {
    "asset_path": "/Game/Melodia/Characters/Melusina/SK_Melusina",
    "asset_type": "skeletal_mesh",
    "resolution": [1100, 1500],
    "camera": {"location": [0, 260, 95], "rotation": [-4, -90, 0], "fov": 42},
}


def shoot(tag="iter"):
    """PIE HighResShot path — kept for level captures; unreliable in new levels."""
    os.makedirs(OUT, exist_ok=True)
    out = f"{OUT}/melusina_{tag}.png"
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, out)
    print(f"[studio] -> {out}")
    return out
