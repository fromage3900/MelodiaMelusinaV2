"""Build a genuinely working rock-scatter graph using the real rock meshes
already in pcg_portfolio_standards.SCATTER_MESHES["rock"] and a proven
Input->VolumeSampler->Transform->Spawner->Output chain, the same minimal
pattern verified working elsewhere this session (PCG_BaroqueEntryEx, 845
instances).

Does NOT use pcg_graph_builder.wire_scatter_chain() -- that helper is
broken in two ways, confirmed live 2026-07-02:
  1. Its PCGDensityFilterSettings step keeps points only within
     [lower_bound, upper_bound], but PCGVolumeSamplerSettings' default
     output point density is 1.0 -- with upper_bound < 1.0 (the density_mult
     path always produces upper < 0.95), every point gets filtered out.
     Confirmed: minimal sampler->spawner gave 1200 instances; the same
     graph with wire_scatter_chain's density filter added gave 0.
  2. Its PCGSelfPruningSettings step sets properties that don't exist on
     this engine build (unreal.PCGSelfPruningType.LARGEST_TO_SMALLEST
     doesn't exist -- real values are LARGE_TO_SMALL/SMALL_TO_LARGE/etc --
     and 'pruning_type' itself isn't a valid property name either).
  wire_scatter_chain needs a real fix pass (correct density-filter
  semantics, correct property names) before any other script should call
  it -- not attempted here, this script sidesteps it entirely.

Deliberately does NOT wire PCGCol_Environment_Rocks/PCGCol_Environment_
GroundCover -- inspected 2026-07-02 and found to contain mismatched
placeholder content ("GroundCover" = wall segments + a marble slab
outline; "Rocks" = a broken null-mesh entry + a placeholder cube), not
appropriate scatter content despite the names. Flagged for the Nikki-lens
portfolio cleanup pass rather than force-wired in as-is.

Run inside the editor (Monolith run_python):
  import build_universal_rock_scatter as burs
  burs.build_rock_scatter()
"""
from __future__ import annotations

DEST_FOLDER = "/Game/EnvSandbox/PCG/Universal"


def build_rock_scatter(name="PCG_Universal_RockScatter", force=True):
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()

    sampler, sampler_s = gb.add_node(graph, "PCGVolumeSamplerSettings", -700, 0)
    sampler_s.set_editor_property("voxel_size", unreal.Vector(300, 300, 300))
    sampler_s.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", sampler, "Volume")

    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.7, scale_max=1.6, jitter=40.0)
    graph.add_edge(sampler, "Out", xform, "In")

    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 50, 0)
    if not gb.configure_spawner(spawner_s, "rock", None):
        raise RuntimeError("configure_spawner failed for role 'rock'")
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built, sampler -> transform -> spawner")
    return {"path": f"{DEST_FOLDER}/{name}"}


if __name__ == "__main__":
    print(build_rock_scatter())
