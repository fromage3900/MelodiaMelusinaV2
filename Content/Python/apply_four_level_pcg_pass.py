"""Deterministic dressing pass for the four portfolio levels.

Uses existing PCG graphs only. It is intentionally additive and skips a graph
when a volume with the same label already exists in the level.

!! TWO BUGS FIXED 2026-08-01 -- this script previously CRASHED THE EDITOR !!

1. SCALE. It called set_actor_scale3d(100, 100, 10). A PCGVolume spawns at default
   scale (25, 25, 10), which is already 5000 x 5000 x 2000 uu (50 m footprint). So
   (100, 100, 10) is 4x the default in XY -> 20,000 x 20,000 x 2,000 uu (200 m x 200 m
   x 20 m), four of them generating simultaneously. Confirmed editor crash.
   Default scale is now used and is already a sensible dressing footprint.

2. L_FallenMoon HAS NO LANDSCAPE. It is 22 static meshes and no terrain, yet was
   assigned four SURFACE-SCATTERING graphs (GardenRuins, LanternGrove, RockScatter,
   WaterEdgeScatter). Those can never emit there at any scale. Replaced with
   PCG_DreamWalls, which uses CreatePointsGrid and needs no surface -- verified
   emitting 144 instances.

ALSO KNOWN (2026-08-01): graphs whose source node is PCGVolumeSampler emit ZERO in
this project regardless of volume size (tested up to 5400 uu). Graphs whose source is
PCGCreatePoints / PCGCreatePointsGrid work. Prefer CreatePoints graphs until the
VolumeSampler issue is diagnosed separately.

generate() is ASYNC -- never count instances in the same call, and count level-wide
rather than on the volume, since PCG may spawn onto managed actors.
"""
import unreal

LEVELS = {
    "/Game/EnvSandbox/Environments/L_EscherAscent": [
        ("PCG_EscherAscent_Relativity", "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherRelativityRoom"),
        ("PCG_EscherAscent_Penrose", "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherPenroseLoop"),
        ("PCG_EscherAscent_Islands", "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherFloatingIslandEx"),
    ],
    # L_FallenMoon has NO LANDSCAPE. Surface-scattering graphs cannot work here.
    # The four originally listed (GardenRuins, LanternGrove, Universal_RockScatter,
    # WaterEdgeScatter) all sample a surface and are kept here only as a comment so
    # nobody re-adds them believing they were forgotten.
    "/Game/EnvSandbox/Environments/L_FallenMoon": [
        ("PCG_FallenMoon_DreamWalls", "/Game/EnvSandbox/PCG/Styles/Escher/PCG_DreamWalls"),
    ],
    "/Game/EnvSandbox/Environments/L_InfiniteScore": [
        ("PCG_InfiniteScore_OrbitalRing", "/Game/EnvSandbox/PCG/Styles/Cosmic/PCG_Cosmic_OrbitalRing"),
        ("PCG_InfiniteScore_OrbitScatter", "/Game/EnvSandbox/PCG/Styles/Cosmic/PCG_Cosmic_OrbitScatter"),
        ("PCG_InfiniteScore_Promenade", "/Game/EnvSandbox/PCG/Universal/PCG_BezierGardenPromenade"),
        ("PCG_InfiniteScore_Landmarks", "/Game/EnvSandbox/PCG/Universal/PCG_LandmarkScatter"),
    ],
    "/Game/EnvSandbox/Environments/L_KaleidoNave": [
        ("PCG_KaleidoNave_Cathedral", "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_CathedralNave"),
        ("PCG_KaleidoNave_Colonnade", "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueColonnade"),
        ("PCG_KaleidoNave_Axis", "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BezierCathedralAxis"),
        ("PCG_KaleidoNave_Ornament", "/Game/EnvSandbox/PCG/Universal/PCG_OrnamentalDetail"),
    ],
}

def run():
    report = {}
    for level_path, specs in LEVELS.items():
        unreal.EditorLevelLibrary.load_level(level_path)
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        labels = {a.get_actor_label() for a in actors}
        level_report = {"created": [], "skipped": [], "missing_graph": []}
        for label, graph_path in specs:
            if label in labels:
                level_report["skipped"].append(label)
                continue
            graph = unreal.EditorAssetLibrary.load_asset(graph_path)
            if not graph:
                level_report["missing_graph"].append(graph_path)
                continue
            volume = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.PCGVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
            volume.set_actor_label(label)
            # DEFAULT SCALE. A PCGVolume is already 5000x5000x2000 uu (50 m footprint).
            # The old (100, 100, 10) multiplier made 5 km volumes and crashed the editor.
            volume.set_actor_scale3d(unreal.Vector(1, 1, 1))
            component = volume.get_component_by_class(unreal.PCGComponent)
            component.set_graph(graph)
            component.generate(True)
            level_report["created"].append({"label": label, "graph": graph_path})
        unreal.EditorLevelLibrary.save_current_level()
        report[level_path] = level_report
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
