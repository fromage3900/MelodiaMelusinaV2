"""build_material_render_studio_grid.py

Build L_RenderStudio_AllMIs_2026-08-12 under
/Game/EnvSandbox/Materials/RenderStudio — the portfolio beauty level with every
curated MI in family rows, Melodia void-gradient doctrine (never
SkyAtmosphere/UDS), 3-point + rim rig, Nikki PPV contract, and a cine camera
that can see the whole grid.

Reuses mi_preview_studio.py constants (tags, PPV values, void MIs, meshes).
Existing /Game/EnvSandbox/Materials/RenderStudio/Material_Render_Studio world
is NOT modified.

Run (one editor, serialized): Monolith editor_query run_python -> this file
Reads curated MI list from Saved/Audit/curated_mis.json (see
build_material_test_grid.py refresh_curated_mis) and writes
Saved/Audit/render_studio_manifest.json with swatch->actor map + verification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEVEL_PATH = "/Game/EnvSandbox/Materials/RenderStudio/L_RenderStudio_AllMIs_2026-08-12"
STUDIO_MANIFEST = PROJECT_ROOT / "Saved" / "Audit" / "render_studio_manifest.json"
CURATED_JSON = PROJECT_ROOT / "Saved" / "Audit" / "curated_mis.json"
TEMPLATE_STUDIO = "/Game/EnvSandbox/_Template/L_MaterialPreview_Studio"

sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))
import mi_preview_studio as studio  # noqa: E402

SPHERE = studio.SPHERE
GRID_SPACING_X = 300.0
GRID_SPACING_Y = 300.0
ROW_START_X = -2200.0
ROW_START_Y = -1200.0
ROW_START_Z = 80.0
MAX_PER_ROW = 16


def family_rows(entries: list[dict]) -> list[tuple[str, list[dict]]]:
    by_fam: dict[str, list[dict]] = {}
    for e in entries:
        by_fam.setdefault(e["family"], []).append(e)
    order = studio.NIKKI_PRIORITY and ["Showcase", "NikkiHero", "SDF", "Baroque",
                                       "Crystal", "Halftone", "Glitter",
                                       "Water", "Impressionist", "Utility"]
    rest = [f for f in by_fam if f not in order]
    rows = [(f, by_fam[f]) for f in order if f in by_fam]
    rows += [(f, by_fam[f]) for f in rest]
    return rows


def spawn_swatch(location, label: str, material_path: str, scale=1.55):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        return None
    sm = unreal.load_asset(SPHERE)
    if sm is None:
        return None
    comp = actor.static_mesh_component
    comp.set_static_mesh(sm)
    comp.set_material(0, unreal.load_asset(material_path))
    comp.set_editor_property("cast_shadow", True)
    actor.set_actor_label(label)
    actor.set_folder_path("Studio/Swatches")
    actor.set_editor_property("actor_enable_pause", False)
    return actor


def setup_backdrop() -> None:
    """Void gradient plane behind the grid (Melodia doctrine)."""
    mat = unreal.load_asset(studio.MELODIA_VOID_NEUTRAL)
    if mat is None:
        mat = unreal.load_asset(studio.MELODIA_VOID_MI)
    loc = unreal.Vector(-1400.0, 3000.0, 400.0)
    plane = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, loc, unreal.Rotator(0.0, 0.0, 0.0))
    if plane is None:
        return
    pm = unreal.load_asset(studio.PLANE)
    comp = plane.static_mesh_component
    comp.set_static_mesh(pm)
    if mat:
        comp.set_material(0, mat)
    comp.set_world_scale3d(unreal.Vector(12.0, 12.0, 1.0))
    comp.set_editor_property("cast_shadow", False)
    plane.set_actor_label("Backdrop_VoidGradient")
    plane.set_folder_path("Studio/Backdrop")
    plane.set_editor_property("tags", [studio.TAG_BACKDROP])


def setup_lights() -> None:
    def light(cls, loc, rot, intensity, color, tag, temperature=0.0):
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, loc, rot)
        if actor is None:
            return
        comp = actor.light_component if hasattr(actor, "light_component") else None
        if comp is None:
            try:
                comp = actor.get_component_by_class(unreal.LightComponent)
            except Exception:
                comp = None
        if comp is not None:
            comp.set_editor_property("intensity", intensity)
            comp.set_editor_property("light_color", color)
            if temperature and hasattr(comp, "has_editor_property") and comp.has_editor_property("use_temperature"):
                comp.set_editor_property("use_temperature", True)
                comp.set_editor_property("temperature", temperature)
        actor.set_actor_label(tag)
        actor.set_folder_path("Studio/Lights")

    light(unreal.DirectionalLight, unreal.Vector(0, 0, 2600),
          unreal.Rotator(-50.0, 0.0, 0.0), 6.0,
          unreal.LinearColor(1.0, 0.97, 0.92), studio.TAG_KEY_LIGHT, 5600.0)
    light(unreal.DirectionalLight, unreal.Vector(-1800, -2000, 1200),
          unreal.Rotator(-20.0, 40.0, 0.0), 2.5,
          unreal.LinearColor(0.85, 0.9, 1.0), studio.TAG_FILL_LIGHT, 6500.0)
    light(unreal.DirectionalLight, unreal.Vector(2000, -1500, 800),
          unreal.Rotator(-15.0, -140.0, 0.0), 1.4,
          unreal.LinearColor(1.0, 0.8, 0.7), studio.TAG_RIM_LIGHT, 4500.0)


def setup_ppv() -> None:
    try:
        cls = getattr(unreal, "PostProcessVolume")
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, unreal.Vector(0, 0, 0), unreal.Rotator())
        if actor is None:
            return
        actor.set_editor_property("unbound", True)
        pp = actor.settings
        pp.set_editor_property("bloom_intensity", studio.PPV_BLOOM)
        pp.set_editor_property("vignette_intensity", studio.PPV_VIGNETTE)
        pp.set_editor_property("film_grain_intensity", studio.PPV_GRAIN)
        pp.set_editor_property("chromatic_aberration_intensity", studio.PPV_CHROMATIC)
        pp.set_editor_property("auto_exposure_bias", studio.PPV_EXPOSURE_BIAS)
        pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        actor.set_actor_label("PPV_MaterialStudio")
        actor.set_folder_path("Studio/PostProcess")
    except Exception as exc:
        print(f"PPV_WARN|{exc}")


def setup_camera() -> None:
    try:
        cls = unreal.CineCameraActor
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, unreal.Vector(0.0, -2600.0, 500.0),
            unreal.Rotator(-8.0, 0.0, 0.0))
        if actor is None:
            return
        cam = actor.get_cine_camera_component()
        cam.set_editor_property("field_of_view", 60.0)
        actor.set_actor_label("CineCamera_AllMIs")
        actor.set_folder_path("Studio/Camera")
    except Exception as exc:
        print(f"CAM_WARN|{exc}")


def build_studio(entries: list[dict]) -> list[dict]:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        les.load_level(LEVEL_PATH)
    else:
        if unreal.EditorAssetLibrary.does_asset_exist(TEMPLATE_STUDIO):
            unreal.EditorAssetLibrary.duplicate_asset(
                TEMPLATE_STUDIO,
                "/Game/EnvSandbox/Materials/RenderStudio",
                "L_RenderStudio_AllMIs_2026-08-12")
        les.load_level(LEVEL_PATH)

    setup_backdrop()
    setup_lights()
    setup_ppv()
    setup_camera()

    rows = family_rows(entries)
    swatches: list[dict] = []
    for r_idx, (fam, members) in enumerate(rows):
        x = ROW_START_X
        y = ROW_START_Y + r_idx * GRID_SPACING_Y
        for col, e in enumerate(members[:MAX_PER_ROW]):
            loc = unreal.Vector(x + col * GRID_SPACING_X, y, ROW_START_Z)
            label = f"MI_{fam}_{col:02d}"
            actor = spawn_swatch(loc, label, e["path"])
            if actor:
                swatches.append({
                    "label": label,
                    "material": e["path"],
                    "family": fam,
                    "x": loc.x, "y": loc.y, "z": loc.z,
                })
            # wrap long rows (2D row packing)
            if (col + 1) % 8 == 0:
                x += GRID_SPACING_X
                y += GRID_SPACING_Y * 0.5

    saved = unreal.EditorLevelLibrary.save_current_level()
    print(f"STUDIO|swatches={len(swatches)}|rows={len(rows)}|saved={saved}")
    return swatches


def verify_studio(expected: list[dict]) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ok = 0
    mismatched = []
    missing = []
    for exp in expected:
        found = None
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            if actor.get_actor_label() == exp["label"]:
                found = actor
                break
        if found is None:
            missing.append(exp["label"])
            continue
        try:
            mats = found.static_mesh_component.get_materials()
        except Exception:
            mats = []
        if mats and mats[0] and mats[0].get_path_name() == exp["material"]:
            ok += 1
        else:
            mismatched.append({"label": exp["label"], "have": mats[0].get_path_name() if mats and mats[0] else None, "want": exp["material"]})
    return {"matched": ok, "missing": missing, "mismatched": mismatched}


def main() -> int:
    if not CURATED_JSON.is_file():
        print("NO_CURATED|run build_material_test_grid.py refresh first")
        return 1
    entries = json.loads(CURATED_JSON.read_text(encoding="utf-8"))["entries"]
    swatches = build_studio(entries)
    STUDIO_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    verify = verify_studio(swatches)
    STUDIO_MANIFEST.write_text(
        json.dumps({"swatches": swatches, "verify": verify}, indent=2), encoding="utf-8")
    print(f"VERIFY|{json.dumps(verify)}")
    print(f"WROTE|{STUDIO_MANIFEST}")
    return 0 if verify["matched"] == len(swatches) and not verify["mismatched"] else 2


if __name__ == "__main__":
    raise SystemExit(main())