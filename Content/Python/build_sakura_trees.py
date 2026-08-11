"""PCG cherry blossom tree builder for L_SakuraPath.

Generates tree instances using PCGCreatePointsSettings with computed trunk +
canopy points. Each tree is a cluster: a cylindrical trunk and a spherical
canopy of small petal/plane cards.

Three size variants: small (2-3m), medium (4-6m), large (7-10m).

Run (editor):
  import build_sakura_trees as bst
  bst.build_all()
"""
from __future__ import annotations

import math
import random

DEST_FOLDER = "/Game/EnvSandbox/PCG/Styles/Sakura"

TRUNK_MESH = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Pillar_03.SM_Greybox_Pillar_03"
CANOPY_MESH = "/Engine/BasicShapes/Sphere.Sphere"
BRANCH_MESH = "/Engine/BasicShapes/Cylinder.Cylinder"

TREE_VARIANTS = {
    "small": {"trunk_h": (200, 300), "trunk_r": (8, 14), "canopy_r": (80, 140), "canopy_count": (4, 8)},
    "medium": {"trunk_h": (400, 600), "trunk_r": (14, 22), "canopy_r": (140, 220), "canopy_count": (8, 16)},
    "large": {"trunk_h": (700, 1000), "trunk_r": (22, 35), "canopy_r": (220, 350), "canopy_count": (14, 28)},
}


def _make_tree_points(unreal, rng: random.Random, variant: str, base_x: float, base_y: float, base_z: float) -> list:
    cfg = TREE_VARIANTS[variant]
    trunk_h = rng.uniform(*cfg["trunk_h"])
    trunk_r = rng.uniform(*cfg["trunk_r"])
    canopy_r = rng.uniform(*cfg["canopy_r"])
    canopy_n = rng.randint(*cfg["canopy_count"])

    points = []

    # Trunk
    trunk_scale = (trunk_r * 2, trunk_r * 2, trunk_h)
    p = unreal.PCGPoint()
    loc = unreal.Vector(base_x, base_y, base_z + trunk_h * 0.5)
    p.set_editor_property("transform", unreal.Transform(loc, unreal.Rotator(0, rng.uniform(0, 360), 0), unreal.Vector(*trunk_scale)))
    p.set_editor_property("density", 1.0)
    points.append(p)

    # Canopy spheres clustered around trunk top
    for _ in range(canopy_n):
        theta = rng.uniform(0, math.tau)
        phi = rng.uniform(0, math.pi * 0.4)
        r = rng.uniform(canopy_r * 0.3, canopy_r * 0.85)
        cx = base_x + math.cos(theta) * r * 0.6
        cy = base_y + math.sin(theta) * r * 0.6
        cz = base_z + trunk_h + rng.uniform(0, canopy_r * 0.5)
        sz = rng.uniform(canopy_r * 0.2, canopy_r * 0.5)

        p2 = unreal.PCGPoint()
        p2.set_editor_property("transform", unreal.Transform(
            unreal.Vector(cx, cy, cz),
            unreal.Rotator(rng.uniform(-30, 30), rng.uniform(0, 360), rng.uniform(-30, 30)),
            unreal.Vector(sz, sz, sz),
        ))
        p2.set_editor_property("density", 1.0)
        points.append(p2)

    return points


def _make_orchard_points(unreal, rng_seed: int, count: int, spread_radius: float) -> list:
    rng = random.Random(rng_seed)
    variants = list(TREE_VARIANTS.keys())
    weights = {"small": 0.4, "medium": 0.4, "large": 0.2}

    all_points = []
    for i in range(count):
        variant = rng.choices(variants, weights=[weights[v] for v in variants])[0]
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(0, spread_radius)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        z = 0
        tree_points = _make_tree_points(unreal, rng, variant, x, y, z)
        all_points.extend(tree_points)
    return all_points


def build_sakura_tree_graph(name="PCG_Sakura_TreeOrchard", pool_seed=4242, tree_count=30, spread=5000, force=True):
    """Build a PCG graph that spawns a sakura tree orchard from CreatePoints."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-600, 0)
    out.set_node_position(800, 0)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-300, 0)

    pts = _make_orchard_points(unreal, pool_seed, tree_count, spread)
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(100, 0)

    trunk_mesh = unreal.EditorAssetLibrary.load_asset(TRUNK_MESH)
    canopy_mesh = unreal.EditorAssetLibrary.load_asset(CANOPY_MESH)

    entries = []
    for mesh, name_bit, weight in [
        (trunk_mesh, "Trunk", 1),
        (canopy_mesh, "Canopy", 3),
    ]:
        if not mesh:
            continue
        entry = unreal.PCGMeshSelectorWeightedEntry()
        desc = entry.get_editor_property("descriptor")
        desc.set_editor_property("static_mesh", mesh)
        mi_path = "/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Bark"
        if name_bit == "Canopy":
            mi_path = "/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Petals"
        mat = unreal.EditorAssetLibrary.load_asset(mi_path) if unreal.EditorAssetLibrary.does_asset_exist(mi_path) else None
        if mat:
            for prop in ("override_materials", "material_overrides"):
                try:
                    desc.set_editor_property(prop, [mat])
                    break
                except Exception:
                    continue
        entry.set_editor_property("descriptor", desc)
        entry.set_editor_property("weight", weight)
        entries.append(entry)

    if entries:
        sel = spawn_settings.get_editor_property("mesh_selector_parameters")
        sel.set_editor_property("mesh_entries", entries)

    graph.add_edge(create_node, "Out", spawn_node, "In")
    graph.add_edge(spawn_node, "Out", out, "Out")
    graph.set_editor_property("is_standalone_graph", True)

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {tree_count} trees ({len(pts)} points), saved")
    return {"path": f"{DEST_FOLDER}/{name}", "tree_count": tree_count, "point_count": len(pts)}


def build_all() -> dict:
    r = build_sakura_tree_graph()
    return {"orchard": r}


if __name__ == "__main__":
    print(build_all())
