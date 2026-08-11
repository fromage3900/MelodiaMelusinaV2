"""Regenerate all hero graphs from the tagged PCG_Control snapshot.

Discrete controls intentionally take this On-Demand route: count, spacing,
rise, and decorative sampling become new deterministic PCG points, while the
render controls are copied into the hero profiles and mesh descriptors.
"""
from __future__ import annotations

from dataclasses import asdict


def regenerate() -> dict:
    import unreal
    import pcg_hero_music_control as control
    import build_pcg_control_alias_layer as aliases
    import build_pcg_hero_resonance_cathedral as cathedral
    import build_pcg_hero_arpeggio_bridge as bridge
    import build_pcg_hero_bell_tree_garden as bell_tree_garden
    import build_pcg_hero_xylophone_trail as xylophone

    snapshot = control.read_control_snapshot(unreal)
    overrides = asdict(snapshot)
    alias_result = aliases.build_control_alias_graph()
    cathedral_result = cathedral.build_resonance_cathedral_graph(overrides)
    bridge_result = bridge.build_arpeggio_bridge_graph(overrides)
    bell_result = bell_tree_garden.build_bell_tree_garden_graph(overrides)
    xylophone_result = xylophone.build_xylophone_trail_graph(overrides)
    generated_hosts = []
    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
        for actor in actors:
            if not any("PCG_HeroMusicHost" == str(tag) for tag in (actor.tags or [])):
                continue
            component = actor.get_component_by_class(unreal.PCGComponent)
            if component:
                component.generate(True)
                generated_hosts.append(actor.get_actor_label())
    except Exception as exc:
        generated_hosts.append(f"generation_error:{exc}")
    return {
        "snapshot": overrides,
        "control_aliases": alias_result,
        "cathedral": cathedral_result,
        "bridge": bridge_result,
        "bell_tree_garden": bell_result,
        "xylophone_trail": xylophone_result,
        "generated_hosts": generated_hosts,
        "workflow": "tagged PCG_Control snapshot -> deterministic point rebuild -> On-Demand PCG generation",
    }


if __name__ == "__main__":
    print(regenerate())
