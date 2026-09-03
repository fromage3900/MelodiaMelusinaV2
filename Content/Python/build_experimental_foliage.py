"""Experimental PCG grass-card foliage scatter.

Real content chain, all newly wired this session:
  T_FoliageCards_grass1 (real alpha-cutout grass card texture, previously
  authored but never used by any material) -> M_ToonFoliage (small
  BLEND_MASKED, two_sided toon foliage master -- structurally correct,
  but its params were unrenamed defaults ("Param"/"Param_1"/"Param")
  until this session; renamed to Albedo/OpacityMaskTexture/Tint and
  wired to the real texture + a green tint) -> MI_ExperimentalGrassCard
  (new instance) -> /Engine/BasicShapes/Plane as the card mesh (MVP --
  a single flat card, not yet a cross-quad; upgrading to a real
  GeometryScript-authored cross-quad card is the natural next expansion,
  see the proven procedural-mesh recipe used for SM_FloatingIsland_01).

Uses the same minimal proven Sampler->Transform->Spawner chain as
build_universal_rock_scatter.py (NOT pcg_graph_builder.wire_scatter_chain,
which is confirmed broken -- see that script's docstring for why).

Run inside the editor (Monolith run_python):
  import build_experimental_foliage as bef
  bef.build_grass_scatter()
"""
from __future__ import annotations

DEST_FOLDER = "/Game/EnvSandbox/PCG/Universal"
CARD_MESH = "/Engine/BasicShapes/Plane.Plane"
CARD_MATERIAL = "/Game/EnvSandbox/Materials/Instances/Environment/MI_ExperimentalGrassCard"


def build_grass_scatter(name="PCG_ExperimentalFoliage_Grass", force=True):
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()

    sampler, sampler_s = gb.add_node(graph, "PCGVolumeSamplerSettings", -700, 0)
    sampler_s.set_editor_property("voxel_size", unreal.Vector(80, 80, 80))
    sampler_s.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", sampler, "Volume")

    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.6, scale_max=1.3, jitter=30.0)
    xform_s.set_editor_property("rotation_min", unreal.Rotator(0, 0, 0))
    xform_s.set_editor_property("rotation_max", unreal.Rotator(0, 359.0, 0))
    graph.add_edge(sampler, "Out", xform, "In")

    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 50, 0)
    mesh = unreal.EditorAssetLibrary.load_asset(CARD_MESH)
    mat = unreal.EditorAssetLibrary.load_asset(CARD_MATERIAL)
    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", mesh)
    for prop in ("override_materials", "material_overrides"):
        try:
            desc.set_editor_property(prop, [mat])
            break
        except Exception:
            continue
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawner_s.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built, Plane card + MI_ExperimentalGrassCard, sampler -> transform -> spawner")
    return {"path": f"{DEST_FOLDER}/{name}"}


if __name__ == "__main__":
    print(build_grass_scatter())
