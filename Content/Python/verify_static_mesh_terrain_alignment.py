"""Post-apply verification for the SeaAbove static-mesh terrain sweep."""

import sweep_static_meshes_to_landscape as sweep


sweep.APPLY = False
sweep.REPORT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/sea_above_static_mesh_terrain_sweep_post_2026-09-04.json"


if __name__ == "__main__":
    print(sweep.run())

