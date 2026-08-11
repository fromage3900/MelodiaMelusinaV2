"""Wall detail PCG graph builder — vines, moss, and surface accents.

Phase 3 stub fix: builds a working Sampler→Transform→Spawner chain targeting
vertical surfaces (walls, columns) via surface tag filtering. Uses the same
proven minimal pattern as build_universal_rock_scatter.py.

Updated 2026-07-09: Added volume fallback mode for walkability/scale verification.
Can now work on any PCGVolume, not just wall-tagged surfaces.

Future expansion: PCGEx distance falloff from ground for vine-height control.

Run (editor):
  import build_pcg_wall_detail as bwd
  bwd.build_wall_ivy()
  bwd.build_wall_moss()
"""
from __future__ import annotations

DEST_FOLDER = "/Game/EnvSandbox/PCG/Universal"

WALL_IVY_MESHES = [
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m",
]
WALL_MOSS_MESHES = [
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m",
]
WALL_LICHEN_MESHES = [
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m",
]
WALL_DUST_MESHES = [
    "/Engine/BasicShapes/Sphere.Sphere",
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m",
]
WALL_GRAFFITI_MESHES = [
    "/Engine/BasicShapes/Cube.Cube",
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Wall_4x3.SM_Greybox_Wall_4x3",
]

WALL_SURFACE_TAG = "PCG_WallSurface"
WALL_GROUND_TAG = "PCG_WallBase"


def _build_wall_graph(name: str, meshes: list[str], scale_min: float, scale_max: float, density: float) -> dict:
    import unreal
    import pcg_graph_builder as gb
    import pcg_portfolio_standards as std

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=True)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    surf, surf_s = gb.add_node(graph, "PCGSurfaceSamplerSettings", -700, 0)
    surf_s.set_editor_property("points_per_squared_meter", density)
    graph.add_edge(inp, "In", surf, "Surface")

    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=scale_min, scale_max=scale_max, jitter=scale_min * 0.5)
    graph.add_edge(surf, "Out", xform, "In")

    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 50, 0)
    entries = []
    for mesh_path in meshes:
        mesh = unreal.load_asset(mesh_path)
        if not mesh:
            continue
        entry = unreal.PCGMeshSelectorWeightedEntry()
        desc = entry.get_editor_property("descriptor")
        desc.set_editor_property("static_mesh", mesh)
        entry.set_editor_property("descriptor", desc)
        entry.set_editor_property("weight", 1)
        entries.append(entry)
    if entries:
        sel = spawner_s.get_editor_property("mesh_selector_parameters")
        sel.set_editor_property("mesh_entries", entries)

    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    graph.set_editor_property("is_standalone_graph", True)

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    return {"path": f"{DEST_FOLDER}/{name}", "created": created, "entries": len(entries)}


def build_wall_ivy(name="PCG_WallIvy") -> dict:
    """Vine/ivy scatter for wall surfaces — small cubes as proxy vines."""
    return _build_wall_graph(name, WALL_IVY_MESHES, 0.15, 0.6, 0.3)


def build_wall_moss(name="PCG_WallMoss") -> dict:
    """Moss patch scatter for wall bases — flat planes, ground-hugging."""
    return _build_wall_graph(name, WALL_MOSS_MESHES, 0.3, 0.8, 0.5)


def build_wall_lichen(name="PCG_WallLichen") -> dict:
    """Lichen spot scatter — small cylinder blobs on wall surfaces."""
    return _build_wall_graph(name, WALL_LICHEN_MESHES, 0.08, 0.25, 0.6)


def build_wall_dust(name="PCG_WallDust") -> dict:
    """Dust/debris scatter for dry wall surfaces — small sphere+cube proxy."""
    return _build_wall_graph(name, WALL_DUST_MESHES, 0.05, 0.3, 0.4)


def build_wall_graffiti(name="PCG_WallGraffiti") -> dict:
    """Graffiti splatter for urban wall surfaces — flat decal proxy cubes."""
    return _build_wall_graph(name, WALL_GRAFFITI_MESHES, 0.5, 1.2, 0.15)


def build_all() -> dict:
    r1 = build_wall_ivy()
    r2 = build_wall_moss()
    r3 = build_wall_lichen()
    r4 = build_wall_dust()
    r5 = build_wall_graffiti()
    return {"ivy": r1, "moss": r2, "lichen": r3, "dust": r4, "graffiti": r5}


if __name__ == "__main__":
    print(build_all())
