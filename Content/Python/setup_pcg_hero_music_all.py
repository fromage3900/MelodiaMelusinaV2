"""Build all additive hero music proof levels in a reviewed order."""
from __future__ import annotations


def build_all() -> dict:
    import importlib
    import build_pcg_control_alias_layer as aliases
    import setup_pcg_hero_resonance_cathedral_level as cathedral
    import setup_pcg_hero_arpeggio_bridge_level as bridge
    import setup_pcg_hero_bell_tree_garden_level as bell
    import setup_pcg_hero_xylophone_trail_level as xylophone
    import setup_pcg_hero_crystal_harp_grove_level as harp
    importlib.reload(aliases)
    importlib.reload(cathedral)
    importlib.reload(bridge)
    importlib.reload(bell)
    importlib.reload(xylophone)
    importlib.reload(harp)

    return {
        "control_aliases": aliases.build_control_alias_graph(),
        "cathedral": cathedral.build_level(),
        "bridge": bridge.build_level(),
        "bell_tree_garden": bell.build_level(),
        "xylophone_trail": xylophone.build_level(),
        "crystal_harp_grove": harp.build_level(),
        "scale_world": {
            "builder_script": "setup_pcg_scale_world_pipeline.py",
            "offline_runner": "run_pcg_scale_world_build.py",
            "canonical_cell_size_cm": 25600,
        },
        "production_maps_touched": False,
        "promotion": "recipes only after proof approval",
    }


if __name__ == "__main__":
    print(build_all())
