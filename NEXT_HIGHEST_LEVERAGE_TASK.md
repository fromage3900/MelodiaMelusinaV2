# Next Highest-Leverage Tasks

> Updated 2026-07-14 after Melodia game-systems deep review. Current SSOT for gameplay-system issues: [Docs/MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md](Docs/MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md).
> Previous 2026-07-09 portfolio-capture priorities remain below, but MelodiaCore gameplay correctness is now the highest leverage path for the playable vertical slice.
> Pipeline hardening SSOT and agent handoff prompt: [Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md](Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md).


## Today - 2026-07-14 (Melodia game systems)

These are C++/runtime tasks unless explicitly marked as test/docs. Do not edit `Content/Python/gmm` to "fix" runtime behavior; use it only as parity evidence.

1. **GS-001 - Fix multiplicative modifier stacking.** `UMelodiaCombatStateComponent::EvaluateModifier` must evaluate stacked `mul` modifiers as repeated multiplication/exponentiation, not `Value * Stacks`.
2. **GS-002 - Respect permanent modifier duration.** `TickModifiers` must keep `duration_turns < 0` modifiers alive.
3. **GS-003 - Make AV the battle-session turn authority.** Store player/enemy AV, consume `CalculateAVCost`, `Speed` modifiers, and generated delay fractions to decide the next actor.
4. **GS-004 - Restore ultimate as an interrupt economy.** Ultimate should be fireable during active battle when ready and should not force an enemy turn unless AV says so.
5. **GS-006 - Fix roguelike run phase/event ordering.** Set `Generating` before broadcasting stage recipe so completion callbacks are not dropped.
6. **GS-007 - Prove reward -> exit -> next stage.** Clarify `CommitRewardAndAdvance` and prove the two-stage loop in PIE.
7. **GS-005 - Wire remaining modifier stat hooks.** `UltGain`, `SPGain`, `Speed`, and `RhythmWindow` need real runtime effects or an explicit deferral.
8. **AssetPassport hardening lane.** Seed one passport each for NPC, room/environment, gameplay asset, and material/VFX; add a no-mutation validator/checklist so agents can scale asset creation without source-of-truth drift.

Acceptance gate: `Melodia.CoreRules.*` automation covers modifier stack semantics and the new AV/ultimate behavior, then a PIE smoke proves victory -> reward -> exit -> second encounter.

> Rewritten 2026-07-09 (post WP-pillar fix, commit `2f64a0f`). Supersedes the 2026-07-09-morning version (capture-spine steps from it that still matter are folded into P0 below).
> Ranked by (portfolio impact ├ù unblock factor) ├╖ effort. Full long-term plan: [Docs/ECOSYSTEM_UNIFICATION_PLAN.md](Docs/ECOSYSTEM_UNIFICATION_PLAN.md).

## Today ΓÇö 2026-07-11 (monetization + site)

SSOT: [Docs/MONETIZATION_TODAY_2026-07-11.md](Docs/MONETIZATION_TODAY_2026-07-11.md). **`store_live` stays false** until screenshots + Gumroad.

1. **Ornament store screenshots (6)** ΓÇö highest revenue leverage; FBX 15/15 + preview ZIP already on disk.
2. **Re-pack sell ZIP from current SurrealArch KitbashExport FBXs** ΓÇö preview ZIP is undersized vs live meshes.
3. **Gumroad create + upload** ΓåÆ then flip `store_live` + gh-pages.
4. **Website honesty pass** ΓÇö shop gates, Stage passport proof, Props Mini as next SKU (this session).
5. **Claude songcraft ΓåÆ C++ resolve** ΓÇö core gameplay loop (parallel; not a store SKU).
6. **Pillar hero captures** ΓÇö still the top *portfolio landscape* lever when the editor is free (P0 below).

## What changed 2026-07-09 (context for ranking)

The four WP pillar levels are now **actually** production-ready ΓÇö WP=true, per-pillar displaced terrain (483ΓÇô685cm relief), PCG verified live: SakuraDream 2015 / SpaceCathedral 642 / BaroqueGrotto 1085 / CosmicOrrery 6171 instances, all saved. Four root-cause bugs fixed (WP detection, `clear_graph_nodes` no-op, SurfaceSampler-on-mesh ΓåÆ MeshSampler variants, squared perlin frequency). `M_Master_Toon_Universal` deep-reviewed: **healthy** ΓÇö the 916ΓåÆ1015 expression growth is 32 gated, default-off feature commits; the "26 broken texture refs" are ~23 validator false positives (TextureObject-pin-fed) + 3 real-but-dormant empty samplers; the duplicate switch trios are benign hygiene debt. MelodiaCore plugin (source-only, unbuilt) was killing every unattended boot ΓÇö disabled in the .uproject.

## P0 ΓÇö Directly gates the portfolio (Infinity Nikki Aesthetic)

1. **Hero captures on the 4 pillars.** Snap `Cam_Hero_Establishing` to real content per level (terrain now has actual relief and scatter aligned with Nikki style genomes like `NikkiFlorawish` and `NikkiStoneville`). Run `render_exporter.py --all-heroes` to capture the dream-palette landscapes, then website ingest (`my-site-clean/tools/ingest_unreal_portfolio.ps1` + `validate_portfolio.ps1`). This is THE task ΓÇö everything else feeds it.
2. **Reparent `MI_NikkiHero_*`** (scratch master ΓåÆ `M_Master_Toon_Universal`) and **fix `MI_Show_CelestialNebula` BSS texture refs** ΓÇö both appear in pillar hero frames. Verify each via `capture_material_grid`; save with `only_if_is_dirty=False` + disk-timestamp check.
3. **Verify Melusina Dress/Hair Physics & Alignment:** Spot-test hair mesh (`SK_MelusinaHair`) and skirt collision constraints on `BP_Melusina` within `L_PCGTest_Forest` to verify they respect slope alignment and cozy animation velocity curves.
4. **Minimal MRQ preset, one pillar, single-frame EXR.** Largest visible quality jump over viewport PNGs; recruiters see this stylized lighting first.

## P1 ΓÇö Melodia Studio + GMM foundation

5. **Lock the shared family contract.** Implement the pure-Python `gmm.family` scaffold, versioned manifest fixture, role/style registry, provenance shape, and schema validator described in [Docs/MELODIA_GMM_FAMILY_ARCHITECTURE_PLAN.md](Docs/MELODIA_GMM_FAMILY_ARCHITECTURE_PLAN.md). This is the highest-leverage bridge between Blender authoring and UE integration.
6. **Correct and verify the Melodia GN stack.** Fix actual Blender modifier reordering, connect stack `enabled` to modifier visibility, change the stack tab to `Melodia Studio`, then run a Blender 5.1 register/build/export/unregister smoke test.
7. **Add a dry-run GMM manifest importer.** It must validate units, transforms, roles, style IDs, asset paths, and provenance without mutating Unreal. Use it to establish the first `musical_ornament` vertical slice.
8. **Verify the Blender ΓåÆ UE handoff.** Export one manifest and world artifact from Melodia Studio, import it in GMM/UE, and compare bounds/counts/material hints in a deterministic test stage. Live Link is optional feedback, not the source of truth.
9. **Define daemon artifact hygiene.** Separate `_staging/gmm_daemon/` evidence and PID files from source deliverables; every daemon tick must report a real validation gate.

## P1 ΓÇö Ecosystem & Styling Hygiene (Phase 1 of the unification plan)

5. **Masters/ folder cleanup + retire `M_Master_Toon_Unified` / `M_Master_Simple_Universal`** (reparent instances ΓåÆ verify ΓåÆ archive). 28 assets sit in Masters/, only ~7 are masters; `M_SpaceParallax_Test` is still on disk despite the 07-09 "deleted" changelog claim.
6. **Decide `M_Master_Toon_Cosmic`** (new 2026-07-09, 12 MI_Cosmic instances): fold into Universal's existing Celestial/DreamPalette family, or explicitly bless it as the Cosmic style master in ECOSYSTEM_UNIFICATION_PLAN. Ambiguity here is exactly how master sprawl restarts.
7. **Collapse duplicate switch trios** (`bWeather_Active`├ù3, `bCelestialUsesDreamPalette`├ù3 ΓÇö one switch node feeding 3 consumers each) and **fix or delete `TextureSample_0/1/2`** (dormant black-out if `bTriplanar` ever flips on).
8. **Fix `validate_material` false positives** (skip samples whose TextureObject input pin is connected ΓÇö Monolith C++; remember the Live Coding patch doesn't persist across editor restarts) ΓÇö then re-run the library audit. The standing "72 missing refs" figure predates all of this and must be re-measured before anyone acts on it.

## P2 ΓÇö PCG Library Truthing & Genome Alignment (Phase 2)

9. **Graph validation gate** (`Saved/Audit/pcg_graph_health.json`): per graph ΓÇö node-count sanity (no duplicate chains), every spawner has ΓëÑ1 mesh entry, generate-on-test-stage ISM within declared band. Ensure compliance with the 8 Infinity Nikki genome presets in 4 families (`NikkiFlorawish`, `NikkiStoneville`, `NikkiHeartcraft`, `NikkiMirage`).
10. **Replace greybox scatter meshes role-by-role.** `SCATTER_MESHES.grass` is literally a 1m greybox cube; the 54 migrated prop folders (`Library/Migrated/`) remain 100% unwired. One role at a time with a template-stage visual check.
11. **Spline-blocked graphs** (~13 + `BalconyEx`/`NaveVaultEx`) via the proven `BP_PathSplineProvider` direct-host pattern.

## P3 ΓÇö Parked (needs human-at-keyboard or source reading)

- PCGExCreateShapes crash trio (`AtriumEx`/`ColonnadeEx`/`RotundaEx`): in-editor parameter trace; keep quarantined, never batch-generate.
- PCGEx Collections stagingΓåÆselector contract (needs PCGEx source read) ΓÇö or delete `PCG/Collections/`.
- Blender surreal-architecture generator ΓåÆ UE world.json/HISM bridge end-to-end verification (biggest untapped scale lever for the cathedral/Escher goal).
- MeshTerrain actor adoption per pillar (no Python authoring API; in-editor step; GeometryScript seeds are tagged `MeshTerrain_Seed`).

## Standing rules (unchanged)

- `L_SakuraPath` art pass is human-owned. No lights/cameras spawned or screenshots taken in user levels ΓÇö data verification only.
- No force-push of `main` (244-commit local/remote divergence).
- Kick + verify in **separate calls** for all async editor work; honest pass criteria (assert targets, not step completion) everywhere.
- Treat every aesthetic update with a whimsical, cozy, stylized-gameplay mindset (the "Infinity Nikki" developer discipline).
