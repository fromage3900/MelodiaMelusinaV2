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

## School run order: P0, Faraway Mother, Glitter Pile

These are three related authoring lanes with separate proof gates. A Houdini bake does not certify the P0 player route or Faraway's live field return.

1. **Gate 0 — license and tool probe.** Run `python Tools/Houdini/foundry/houdini_foundry.py probe --out Saved/Audit/houdini_foundry/probe_school.json`. Record the resolved Houdini/Hython version and license. If Hython or the required license is unavailable, stop before authoring or cooking an HDA.
2. **P0 / Sea Above — one FieldAtlas test tile.** Validate and plan only `field_atlas_sea_above_test_tile.v1.json`; author the missing HDA at school; bake the single recipe tile. Its first UE consumer is the existing read-only debug material/decal or one existing PCG graph sample. Do not rebake the level or treat this as P0 route proof. P0 still closes through the fresh-slot route in `specs/p0/core_p0_dream_golden_run.v1.json`.

   ```powershell
   python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json
   python Tools/Houdini/foundry/houdini_foundry.py plan recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json --out Saved/Audit/houdini_foundry/p0_field_atlas_plan.json
   ```

3. **Faraway Mother — deterministic field substrate, then live return.** Rehearse the authored genome with the existing demo delta; this delta is a fixture for deterministic mission planning, not an owner-exported gameplay result. Extend the existing `Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py` family to meet the 1024² field, PCG cross-check, coordinate contract, hash manifest, and preview requirements in `Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md`. The current script emits an 8-bit RGBA PNG and preview; that is a prototype input, not the complete field pack.

   ```powershell
   python Tools/universe_foundry.py validate --genome specs/universe/faraway_mother.world_genome.v1.json --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json
   python Tools/universe_foundry.py compile --genome specs/universe/faraway_mother.world_genome.v1.json --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json --out Saved/UniverseFoundry/faraway_mother/school_mission/mission.json
   & "<Houdini22>/bin/hython.exe" Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py --res 1024 --seed 3900 --mode-n 3 --mode-m 5 --out-dir Saved/Audit/houdini_faraway_mother
   ```

   Then follow the spec's existing TD replay → `OUT_SHOW_FIELD` → UE alignment → shared fabric/Niagara/Heart Gate presentation checks. Unreal retains gameplay and save authority.
4. **Gate 6 — Glitter Pile.** Validate and plan `deposition_glitter_pile_reference.v1.json`, author the missing HDA, and bake one seeded reference pile. Keep the 200,000-grain source as offline work: static resting bulk is a baked mesh/fields; only the bounded shell sample (maximum 5,000 live grains) feeds Niagara. Create one `/Game/Melodia/HoudiniFoundry/Deposition/NS_GlitterPileLoop` with an `ActiveShellLoop` emitter and one `MI_GlitterPileLoop` using `M_Glitter_Enhanced_Master` by default. Reference the Petal loop/settle lifecycle for behavior, and retain `NS_Morning_GlitterGlint` as the separate glint accent. Keep Petal atlas/material assignments on Petal effects; add no Niagara framework, glitter master, MPC writer, or audio bridge. Check three complete cycles plus pause/resume/restart for stable particle count and rest-pile alignment.

   ```powershell
   python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/deposition_glitter_pile_reference.v1.json
   python Tools/Houdini/foundry/houdini_foundry.py plan recipes/houdini_foundry/deposition_glitter_pile_reference.v1.json --out Saved/Audit/houdini_foundry/glitter_pile_plan.json
   ```
5. **Close only the proof that was actually run.** Verify each bake manifest with `houdini_foundry.py verify`. P0 route, Faraway TD-to-UE field return, and Glitter Niagara/material behavior each require their own live evidence; leave `CURRENT_STATE.md` unchanged until those gates are observed.

The durable contracts are the existing recipes, `specs/p0/core_p0_dream_golden_run.v1.json`, and `Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md`. Add a new recipe only when another named gate needs one; keep large caches and unbounded frame sequences out of Git.
