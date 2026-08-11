"""Apply the explicit Blender-metre -> UE-centimetre point-scale correction.

This is a one-shot migration for the portfolio PCG graphs. It changes point or
transform-node scale only; locations, rotations, graph topology, and volume
locations are preserved.
"""
import unreal

GRAPHS = [
    "/Game/EnvSandbox/PCG/Universal/PCG_GardenRuins",
    "/Game/EnvSandbox/PCG/Universal/PCG_LanternGrove",
    "/Game/EnvSandbox/PCG/Universal/PCG_Universal_RockScatter",
    "/Game/EnvSandbox/PCG/Universal/PCG_WaterEdgeScatter",
    "/Game/EnvSandbox/PCG/Universal/PCG_BezierGardenPromenade",
    "/Game/EnvSandbox/PCG/Universal/PCG_LandmarkScatter",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_CathedralNave",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueColonnade",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BezierCathedralAxis",
    "/Game/EnvSandbox/PCG/Universal/PCG_OrnamentalDetail",
]

def _scaled_transform(t):
    s = t.scale3d
    t.set_editor_property("scale3d", unreal.Vector(s.x * 100.0, s.y * 100.0, s.z * 100.0))
    return t

def run():
    report = {}
    for path in GRAPHS:
        graph = unreal.EditorAssetLibrary.load_asset(path)
        if not graph:
            report[path] = {"status": "missing"}
            continue
        points_changed = 0
        nodes_changed = 0
        for node in graph.nodes:
            settings = node.get_settings()
            if isinstance(settings, unreal.PCGCreatePointsSettings):
                points = settings.get_editor_property("points_to_create")
                for point in points:
                    point.set_editor_property("transform", _scaled_transform(point.get_editor_property("transform")))
                    points_changed += 1
                settings.set_editor_property("points_to_create", points)
            elif isinstance(settings, unreal.PCGTransformPointsSettings):
                lo = settings.get_editor_property("scale_min")
                hi = settings.get_editor_property("scale_max")
                settings.set_editor_property("scale_min", unreal.Vector(lo.x * 100.0, lo.y * 100.0, lo.z * 100.0))
                settings.set_editor_property("scale_max", unreal.Vector(hi.x * 100.0, hi.y * 100.0, hi.z * 100.0))
                nodes_changed += 1
        unreal.EditorAssetLibrary.save_asset(path)
        report[path] = {"status": "scaled", "points": points_changed, "transform_nodes": nodes_changed}
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
