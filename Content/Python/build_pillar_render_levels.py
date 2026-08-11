"""Build the 4 pillar render-test levels (render day 2026-07-03).

Per pillar (Sakura Dream / Space Cathedral / Baroque Castle / Bio Grotto):
  1. Procedural terrain StaticMesh via the PROVEN GeometryScript recipe
     (same as SM_FloatingIsland_01): tessellated rectangle -> perlin
     displacement -> bake StaticMesh asset. Per-pillar noise profile.
     (Landscape actors have no scripting creation path, and GaeaUnrealTools
     stays disabled -- 5.7 build, documented boot-hang. Gaea heightmaps can
     replace these terrains later without touching anything else.)
  2. New level L_Render_<Pillar> with per-pillar lighting mood
     (directional + skylight + sky atmosphere + height fog + cine camera).
  3. Terrain actor with the pillar's MI_NikkiHero_* material.
  4. PCGVolume wired to a proven graph, generation kicked (verify counts in
     a SEPARATE call per the async-settle rule).

Run inside the editor (Monolith run_python), one level per call:
  import build_pillar_render_levels as bl
  bl.build('SakuraDream')   # then SpaceCathedral, BaroqueCastle, BioGrotto
"""
from __future__ import annotations

TERRAIN_DIR = "/Game/_PROJECT/Meshes/RenderTerrains"
LEVEL_DIR = "/Game/_PROJECT/Levels/RenderTests"
HERO_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"

PILLARS = {
    "SakuraDream": {
        "hero": f"{HERO_DIR}/MI_NikkiHero_SakuraDream",
        "noise": [(400.0, 0.00008), (120.0, 0.0004)],   # gentle rolling hills
        "pcg": ["/Game/EnvSandbox/PCG/Styles/Sakura/PCG_SakuraGrove"],
        "sun": {"rot": (-35.0, 210.0), "color": (1.0, 0.85, 0.80), "intensity": 8.0},
        "fog": {"color": (0.95, 0.75, 0.85), "density": 0.015},
    },
    "SpaceCathedral": {
        "hero": f"{HERO_DIR}/MI_NikkiHero_SpaceCathedral",
        "noise": [(900.0, 0.00006), (200.0, 0.0005)],   # dramatic plateaus
        "pcg": ["/Game/EnvSandbox/PCG/Styles/Baroque/PCG_CathedralGrammar_Nave",
                 "/Game/EnvSandbox/PCG/Baroque/PCG_CathedralGrammar_Nave"],
        "sun": {"rot": (-20.0, 250.0), "color": (0.75, 0.78, 1.0), "intensity": 4.0},
        "fog": {"color": (0.45, 0.50, 0.85), "density": 0.03},
    },
    "BaroqueCastle": {
        "hero": f"{HERO_DIR}/MI_NikkiHero_BaroqueCastle",
        "noise": [(600.0, 0.00007), (80.0, 0.0008)],    # stately rises
        "pcg": ["/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueEntryEx",
                 "/Game/EnvSandbox/PCG/Baroque/PCG_BaroqueEntryEx"],
        "sun": {"rot": (-40.0, 160.0), "color": (1.0, 0.92, 0.75), "intensity": 10.0},
        "fog": {"color": (0.95, 0.88, 0.70), "density": 0.01},
    },
    "BioGrotto": {
        "hero": f"{HERO_DIR}/MI_NikkiHero_BioGrotto",
        "noise": [(700.0, 0.0001), (250.0, 0.0006)],    # craggy hollows
        "pcg": ["/Game/EnvSandbox/PCG/Universal/PCG_Universal_RockScatter"],
        "sun": {"rot": (-15.0, 300.0), "color": (0.35, 0.65, 0.70), "intensity": 1.5},
        "fog": {"color": (0.10, 0.45, 0.45), "density": 0.05},
    },
}


def _terrain(name: str, layers) -> str:
    import unreal
    asset_path = f"{TERRAIN_DIR}/SM_Terrain_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return asset_path
    dm = unreal.new_object(unreal.DynamicMesh)
    prim_opts = unreal.GeometryScriptPrimitiveOptions()
    xform = unreal.Transform()
    # 200m x 200m, 128x128 quads
    unreal.GeometryScript_Primitives.append_rectangle_xy(
        dm, prim_opts, xform, 20000.0, 20000.0, 128, 128)
    for mag, freq in layers:
        opts = unreal.GeometryScriptPerlinNoiseOptions()
        base = unreal.GeometryScriptPerlinNoiseLayerOptions()
        base.set_editor_property("magnitude", mag)
        base.set_editor_property("frequency", freq)
        base.set_editor_property("frequency_shift", unreal.Vector(0, 0, 0))
        opts.set_editor_property("base_layer", base)
        sel = unreal.GeometryScriptMeshSelection()
        unreal.GeometryScript_MeshDeformers.apply_perlin_noise_to_mesh(dm, sel, opts)
    unreal.GeometryScript_Normals.recompute_normals(
        dm, unreal.GeometryScriptCalculateNormalsOptions())
    out = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    res = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dm, asset_path, out)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return asset_path


def build(pillar: str) -> dict:
    import unreal
    cfg = PILLARS[pillar]
    report = {"pillar": pillar}

    mesh_path = _terrain(pillar, cfg["noise"])
    report["terrain"] = mesh_path

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_path = f"{LEVEL_DIR}/L_Render_{pillar}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_path):
        les.new_level(level_path)
    else:
        les.load_level(level_path)
    report["level"] = level_path

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

    def spawn(cls, label, loc=(0, 0, 0), rot=(0, 0, 0)):
        if label in existing:
            return existing[label]
        a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
        r = unreal.Rotator()
        r.set_editor_property("pitch", rot[0])
        r.set_editor_property("yaw", rot[1])
        r.set_editor_property("roll", 0.0)
        a.set_actor_rotation(r, False)
        a.set_actor_label(label)
        return a

    # terrain
    t = spawn(unreal.StaticMeshActor, f"Terrain_{pillar}")
    smc = t.static_mesh_component
    smc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(mesh_path))
    smc.set_material(0, unreal.EditorAssetLibrary.load_asset(cfg["hero"]))

    # lighting mood
    sun = spawn(unreal.DirectionalLight, "Sun", (0, 0, 5000),
                (cfg["sun"]["rot"][0], cfg["sun"]["rot"][1]))
    lc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_editor_property("intensity", cfg["sun"]["intensity"])
    lc.set_editor_property("light_color", unreal.Color(
        int(cfg["sun"]["color"][0] * 255), int(cfg["sun"]["color"][1] * 255),
        int(cfg["sun"]["color"][2] * 255), 255))
    spawn(unreal.SkyLight, "Sky", (0, 0, 5000))
    spawn(unreal.SkyAtmosphere, "Atmosphere")
    fog = spawn(unreal.ExponentialHeightFog, "Fog")
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fc.set_editor_property("fog_density", cfg["fog"]["density"])
    fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(*cfg["fog"]["color"], 1.0))

    # camera: elevated 3/4 view looking at origin
    cam = spawn(unreal.CineCameraActor, "RenderCam", (-9000, -9000, 3500), (-15.0, 45.0))

    # PCG volume
    graph = None
    for gp in cfg["pcg"]:
        if unreal.EditorAssetLibrary.does_asset_exist(gp):
            graph = unreal.EditorAssetLibrary.load_asset(gp)
            report["pcg_graph"] = gp
            break
    if graph:
        vol = spawn(unreal.PCGVolume, f"PCG_{pillar}", (0, 0, 500))
        vol.set_actor_scale3d(unreal.Vector(150.0, 150.0, 20.0))
        comp = vol.get_component_by_class(unreal.PCGComponent)
        comp.set_graph(graph)
        comp.generate(True)
        report["pcg"] = "generation kicked"
    else:
        report["pcg"] = "NO GRAPH FOUND: " + str(cfg["pcg"])

    les.save_current_level()
    report["saved"] = True
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(build("SakuraDream"), indent=2))
