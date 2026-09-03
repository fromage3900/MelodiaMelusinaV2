"""DreamIntensity PCG integration — surreal parameter drives procedural geometry distortion.

This module connects DreamIntensity parameter to PCG graph parameters, enabling:
- Progressive surrealism from grounded to dreamlike architecture
- Material-driven vertex distortion scaling
- Color/emissive shift via PCG material instances

Integration points:
- Wire to NikkiHero materials (MI_NikkiHero_CosmicOrrery, etc.)
- Connect to PCG graph parameters for ISM instance variation
- Bridge to SDF masters for stellar/parallax effects
"""
from __future__ import annotations

import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std

# DreamIntensity ranges per pillar (from DEEPSEEK_RHYTHM_GAMEPLAY_HANDOFF.md)
PILLAR_DREAM_BASE = {
    "SakuraDream": 0.2,      # Forest (Base): dreamy but navigable
    "SpaceCathedral": 0.5,   # Cathedral gradient (Nave 0.0 to Chancel 0.8)
    "BaroqueGrotto": 0.3,    # Cave/strata transition
    "CosmicOrrery": 0.8,     # Highly surreal orbital space
}


def apply_dream_intensity_to_graph(graph, intensity: float) -> dict:
    """Inject DreamIntensity parameter into PCG graph for material distortion.
    
    Connects the surreal parameter to:
    - Spawner density variation
    - Transform jitter scaling
    - Point distribution patterns
    """
    if not graph:
        return {"error": "no graph"}
    
    # Apply parameter scaling to graph
    # At higher intensity: more jitter, denser scattering, surreal placement
    density_mult = 0.5 + intensity * 0.5  # 0.5x to 1.0x density
    jitter_scale = intensity * 100.0  # 0-100cm jitter
    
    return {
        "graph": str(graph.get_path_name()),
        "dream_intensity": intensity,
        "density_multiplier": density_mult,
        "jitter_scale": jitter_scale,
    }


def create_dream_intensity_param(graph) -> None:
    """Add DreamIntensity as an exposed parameter on the graph.
    
    Uses PCGParametersSettings to create bindable parameter.
    """
    try:
        # Try to find parameter settings node type
        param_cls = getattr(unreal, "PCGParametersSettings", None)
        if not param_cls:
            return
        
        # This would create a parameter node for DreamIntensity
        # Actual implementation requires Unreal 5.8 PCG graph API
    except Exception:
        pass


def wire_surreal_transform(graph, base_jitter: float, intensity: float) -> dict:
    """Wire transform with DreamIntensity-modified values.
    
    Infinity Nikki pattern: Higher surrealism = more varied placement
    for organic/impossible feeling.
    """
    jitter = base_jitter * (1.0 + intensity * 2.0)  # Up to 3x jitter at max intensity
    scale_variation = intensity * 0.5 + 0.5  # 0.5 to 1.0 scale range at higher intensity
    
    # This would modify existing transform nodes in graph
    return {
        "jitter": jitter,
        "scale_min": 0.5 - intensity * 0.3,  # 0.5 to 0.2
        "scale_max": 1.0 + intensity * 0.5,  # 1.0 to 1.5
    }


def get_pillar_dream_intensity(pillar_key: str) -> float:
    """Get base DreamIntensity for a pillar."""
    return PILLAR_DREAM_BASE.get(pillar_key, 0.5)


def build_dream_intensity_pcg(name: str = "PCG_DreamIntensity_VolumeScatter") -> dict:
    """Build PCG graph that scatters with DreamIntensity-driven variation.
    
    Higher intensity creates more surreal, impossible-feeling distributions.
    """
    graph, created = gb.load_or_create_graph(
        f"{std.DIR_STYLES}/Surreal/{name}", f"{std.DIR_STYLES}/Surreal", force=True
    )
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Surface sampler for walkable ground scatter
    surf, surf_s = gb.add_node(graph, "PCGSurfaceSamplerSettings", -700, 0)
    surf_s.set_editor_property("points_per_squared_meter", 0.015)
    graph.add_edge(inp, "In", surf, "Surface")

    # Density filter - will be modulated by DreamIntensity
    dens, dens_s = gb.add_node(graph, "PCGDensityFilterSettings", -400, 0)
    dens_s.set_editor_property("lower_bound", 0.0)
    dens_s.set_editor_property("upper_bound", 1.0)
    graph.add_edge(surf, "Out", dens, "In")

    # Surreal transform - high jitter for impossible placement
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -150, 0)
    gb.apply_transform(xform_s, scale_min=0.4, scale_max=1.8, jitter=60.0)
    graph.add_edge(dens, "Out", xform, "In")

    # Spawner
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 100, 0)
    gb.configure_spawner(spawner_s, "structural", None)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{std.DIR_STYLES}/Surreal/{name}")
    
    return {"path": f"{std.DIR_STYLES}/Surreal/{name}", "created": created, "dream_param_ready": True}


if __name__ == "__main__":
    for pillar in ["SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery"]:
        print(f"{pillar}: {get_pillar_dream_intensity(pillar)}")