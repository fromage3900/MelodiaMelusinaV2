# recipes/houdini_foundry — staged Foundry Day bakes

| | |
|---|---|
| **Purpose** | One small JSON per deterministic bake. The same pattern as `recipes/*.v1.json` for World Compiler, one layer upstream. |
| **Authority** | Recipes describe work; the source named in `source.path` executes it; the UE owner in `ue_target` consumes it. `status: staged` means **never cooked from this recipe**. |
| **Status** | STAGED 2026-09-24 — all validate offline; none has been cooked. |

| Recipe | Gate | Source | Exists on main? |
|---|---|---|---|
| `hda_engine_smoke_arpeggio_stair.v1.json` | 1 | `Content/Python/create_hda_arpeggio_stair.py` | script yes; `.hda` no |
| `crystal_cathedral_6bay_harmony.v1.json` | 2 | `Tools/Houdini/cathedral/build_crystal_cathedral.py` | yes (OBJ outputs are not) |
| `field_atlas_sea_above_test_tile.v1.json` | 3–4 | `hda/HDA_Foundry_FieldAtlas_1.0.hda` | no — author at college |
| `deposition_glitter_pile_reference.v1.json` | 6 | `hda/HDA_Foundry_Deposition_1.0.hda` | no — author at college |
| `bake_farm_first_workload.v1.json` | 10 | request over the cathedral + tile recipes | — |

Flow, volumetric ecology, ocean intelligence, Copernicus-field and Vellum recipes are written **at the gate that needs them** (see `Docs/Houdini/FoundryDay_2026-09-24/`), not pre-invented.
