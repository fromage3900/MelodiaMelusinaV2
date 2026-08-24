import json

from melodia_mesh_terrain_source import TerrainSourceSpec, export_mesh_terrain_source


def test_metric_mesh_and_manifest_are_scaled_for_mesh_terrain(tmp_path):
    spec = TerrainSourceSpec(
        center_lat=34.384,
        center_lon=135.857,
        width_m=120.0,
        depth_m=60.0,
        samples_x=4,
        samples_y=3,
    )
    manifest_path = tmp_path / "terrain_source.json"
    obj_path = tmp_path / "terrain_source.obj"
    manifest = export_mesh_terrain_source(
        spec,
        [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
        obj_path=obj_path,
        manifest_path=manifest_path,
    )

    lines = obj_path.read_text(encoding="utf-8").splitlines()
    assert sum(line.startswith("v ") for line in lines) == 12
    assert sum(line.startswith("f ") for line in lines) == 12
    assert manifest["geometry"]["width_m"] == 120.0
    assert manifest["geometry"]["depth_m"] == 60.0
    assert manifest["geometry"]["vertex_count"] == 12
    assert manifest["geometry"]["triangle_count"] == 12
    assert manifest["unreal"]["target"] == "Mesh Terrain"
    assert manifest["unreal"]["import_scale_cm_per_meter"] == 100.0
    assert manifest["unreal"]["classic_landscape_used"] is False
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["validation"]["placeholder_terrain"] is False
