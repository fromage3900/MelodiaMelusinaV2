# Melodia Melusina — Current State

**This is the only status document.** If any other file states what works, what is open, or what
to do next, that file is wrong: fix this one instead. Update it in the same commit as the change it
describes. Handoffs, plans, receipts and session notes go in the commit or PR message, never in a
new file.

**Updated:** 2026-09-20 · **Engine:** UE 5.8 · Blender 5.2 LTS · C++20 · Python 3.11
World Compiler live close-out **2026-09-19**: `--skip-scaffold --fx --lookdev` **PASS**. Meadow on **BrushifyIsland_*** SpeedTree + walk dressing — not Sphere3D. Proof `Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-19.json`. Board: `Saved/Audit/Screens/wc_morning_rainbow_bloom_{waterline_dolly,website_oblique,website_top,website_south,south_fix}_2026-09-19.png`.
Morning Niagara rewire **2026-09-19 14:49 disk** + **User-param bind PASS 2026-09-20**: Uni parents off `L_MelusinaMorning` actors; Melodia children `NS_Morning_{PetalDrift,PollenSparkle,PondMist,WindFront,DustShafts}` + parked Glint/Impact. `rewire_morning_fx.py --effect bind-user` bound SpawnRate→`User.PetalSpawnMultiplier` / `MoteSpawnMultiplier` / `MistDensity` and WindFront `Gust_Leader` SpawnBurst `Spawn Count`→`User.WindFrontVisible`. Proof `Saved/Audit/niagara_rewire_bind-user_summary_2026-09-20.json`. No MPC writes. Hue-reveal remains PIE wind only.
**Git 2026-09-20:** Isolated lanes **#257–264 + #266** are on `main`. Closeout `_wt_morning_closeout` tracks `origin/main` after #264 merge `e6e64359`. Morning WC close-out is frozen `--skip-scaffold` (PR #249, merge `dd643af9`). WIP `wip/pre-restart-working-tree-2026-09-19` remains parked recovery at `C:/EnvironmentPortfolio/BS_GodFile` @ `5022ea733` — never dump it, never `git checkout main` onto that dirty tree. Jev is director-only. PhraseBus RecvFrom ingest is LIVE PROVEN; do not revive `Recv()`. Later chapters add new `recipes/*.v1.json` and new `WC_*_Field` / `DT_*` on their own levels, never a second compiler. Frozen PPV, MPCs, `DefaultEngine.ini`, EnvSandbox dumps, `BP_ChoralSheep`, Oceanology, Humber stay parked. Never robocopy/junction/overwrite `harp_bow_pipeline`.
**harp_bow_pipeline recovery 2026-09-20 (late):** an intact pre-junction copy of the Sep 8–12 staged set survived at `D:\_relocated\harp_bow_pipeline`; all 21 `.blend` files were restored to `C:\EnvironmentPortfolio\harp_bow_pipeline` with no overwrites (`verify_blend.py` 21/21 OK, 0 husks) — Rev02, both `pre_rokoko_live` checkpoints, ArcherPose/BowPose, HeldPose, WaveHarp artist files. Rev02 opens in Blender 5.2 (971 objects, all ten cameras, `HERO01_WaveHarp_Staged`, face + grip actions) and renders — proof `harp_bow_pipeline/HERO01_Rev02_recovery_render_proof.png`; receipt `Saved/Audit/mocap/harp_recovery_2026-09-20.json`. D: stays master, G: stays evidence. Never declare a staged `.blend` unrecoverable from one damaged copy — check relocation mirrors + `Tools/mocap/verify_blend.py` first.
**Unique WIP SHAs 2026-09-20:** Cherry-picked onto `origin/main` (closeout): greybox `4afc0e3f4` → `3bbed59be`; Jev recover `f6f49927a` → `de238dd2b`; skirt/hair R2 `b1146a3e7` → `fa1c95df4`; capture evidence `5022ea733` → `b4c9bb64e`. **Skipped as already on main under other SHAs:** `de12afebf` PhraseBus A2, `72a5de6dc` Tools unignore, `c3db66e7c` Niagara/PhraseBus RecvFrom lock. `Docs/P0_TASK_LEDGER.json` kept deleted (#181); greybox/evidence live in CURRENT_STATE + `Docs/Handoffs/CLAIREON_MELUSINA_PHYSICS_BOW_HANDOFF_2026-09-20.md`. RecvFrom Sockets link is on `main` via PR #257.
**Recipe 2026-09-20:** `recipes/morning_rainbow_bloom.v1.json` hero_falloff_cm 2000→1000 and wind `response` 0.5→0.85. Same meadow, not a second compiler. BrushifyIsland flowers + bedroom keepout unchanged.
**Conductor 2026-09-20:** `melodia-conductor` router gained an AWS cost/billing skill row (`aws-cost-billing-audit`). Not a new authority.
**NPC Python 2026-09-20:** Untracked scaffold landed: `Content/Python/npc_vrm_intake.py`, `scaffold_npc.py`, `melusinas_study_phase_b_inventory_2026-09-20.py`. VRM4U import call remains UNVERIFIED. Inventory script is read-only vs the Study blend; it still names the parked WIP path.
**NS_Melusina 2026-09-20:** Untracked `Content/Melodia/VFX/NS_Melusina_{Arc,ChaosDrift,Dust,EntropyDust,EyeSparkle,Globules,ProviderSigil,Ripple,Sigil,Splash,Superposition,SwingTrail}` landed. Skipped `NS_Melusina_Glint` / `NS_Melusina_ImpactBurst` (already on main) and all `NS_Morning_*` / EnvSandbox VFX dumps.
**R1 skirt 2026-09-20:** Landed `SK_Melusina_V2_Skirt_R1_SmoothChains` (+ PhysicsAsset + Skeleton). Unique vs R2 (different path; R1 mesh 7,344,492 bytes vs R2 7,369,072). Live battle skirt remains R2 (`SK_Melusina_V2_Skirt_R2_SmoothChains` in PR #258). Did not overwrite harp_bow_pipeline.
**ChoralSheep unique deltas 2026-09-20:** Landed dirty-vs-main `MI_ChoralSheep_Body` + `MI_ChoralSheep_Body_Chladni_C` and six `NS_ChoralSheep_*` plus BeatStar/WoolMote MIs. **Skipped:** `BP_ChoralSheep` (parked), `NS_Morning_*` (already in #249 / skipped SHA `c3db66e7c`), Morning OFPA, MPC, Frozen PPV, EnvSandbox landscape, `BP_BattleUI`, IntegrationMap.
**Front-door freeze 2026-09-20:** §7 traps expanded. WC bedroom-floor band arc patched to the live BrushifyIsland recipe. Listening Field spec restored from `Tools/listening_field` + `Tools/phrase_bridge`. `.gitignore` `Tools/*` no longer swallows `listening_field` / `phrase_bridge` / `live_source`.
**Listening Field 2026-09-20:** PhraseBus OSC ingest **LIVE PROVEN 2026-09-20 21:58** on the already-open WIP editor (`C:/EnvironmentPortfolio/BS_GodFile/BS_GodFile.uproject`, one Monolith `:9316`). Loaded DLL `Binaries/Win64/UnrealEditor-BS_GodFile.dll` **3,232,768 bytes** mtime **2026-09-20 17:48:36** (`RecvFrom`). PIE `UEDPIE_0_L_MelusinaMorning`; `UMelodiaPhraseBusSubsystem` listening on `127.0.0.1:9000`. `phrase_bridge` sent `,isifsfi` `/melodia/phrase/state` (72 B) + `,ii` `/melodia/phrase/boundary` (40 B). GetCurrentState **bar 0 / energy 0.0 → bar 10 / energy 0.92** (phrase_index 4, CLIMAX, RISING). GameInstance has no Python `get_subsystem`; live instance via `ObjectIterator(MelodiaPhraseBusSubsystem)`. Closeout UBT **PASS 2026-09-20 21:32** on `_wt_morning_closeout` (`UnrealEditor-BS_GodFile.dll` 3,233,280 bytes) after adding private `Sockets` + `Networking` to `BS_GodFile.Build.cs` (`ISocketSubsystem::Get` LNK2019 without them). Did not copy WIP Binaries. Closeout DLL 3,233,280 bytes (21:32, Sockets+Networking) is **not** the loaded binary. Do not open a second editor. Skip AE while Unreal holds GPU3. Choral Sheep consumer is existing `TryBeginHarmonize`. Jev never mutates the editor. Do not UBT while the editor is open. Do not revive `Recv()`.
**Owner-queue proofs 2026-09-20:** Fleece REST vs HIT on the approved Nikki path (`MI_ChoralSheep_Body`→`M_Master_Toon_Character`, child Chladni + `T_Chladni_C_ROOT`). Stills `Saved/Audit/Screens/ship_queue_fleece_{REST,HIT}_v2_clean.png`. 8s beat `Saved/Audit/AE/ship_queue_beat_8s/Melodia_ShipQueue_Beat_8s.mp4`. AE JSX `C:/MelodiaTouchDesigner/ae/ship_queue_creature_motif_harmony_world.jsx` — headless AfterFX dies on GPU3 while Unreal holds the adapter. Do not rebuild the TD scene.
**Pre-collapse docs:** every deleted handoff/plan/report is recoverable with
`git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

---

## 1. What the game is

A solo rhythm-JRPG. QuillScript owns narrative; the TurnBased JRPG template owns party, turns,
damage, inventory and saves. Rhythm timing rides on top of JRPG commands, outfits grant traversal,
and played phrases unlock the world. Shape: OMORI. Music-as-key: Zelda. Wardrobe bar: Infinity
Nikki. Architecture detail: [`SYSTEM_MAP.md`](SYSTEM_MAP.md), [`DATA_FLOW.md`](DATA_FLOW.md).
Settled decisions: [`_DECISION_LOG.md`](_DECISION_LOG.md).

---

## 2. What works — and how strongly it is proven

Evidence ladder (never collapse levels): SOURCE BUILT → LIVE PROVEN → RESTART PROVEN →
PACKAGED PROVEN.

### PROVEN CREATIVE CAPABILITY SURFACE - BUILD WITH THIS NOW

This is the affordance map for a fresh agent. It is not a claim that every possible Chapter or
asset is already finished. `LIVE PROVEN` means a current receipt, ledger row, or PIE proof exercised
the named seam. `RESTART PROVEN` and `PACKAGED PROVEN` are stronger, separate levels. `PRESENT /
SOURCE-TOOL PROVEN` means the source, plugin, generator, or asset family exists and has been checked;
it does not mean a live UE cook or finished content. `SCAFFOLDED` means the contract is useful but
still has a named proof or integration blocker.

**Default:** author content through these seams. Boss battles, new rhythm skills/attacks, side
quests, encounters, creature episodes, outfit abilities, and musical world puzzles are now content
problems. They do not require another gameplay framework or another authority.

#### Gameplay and content authoring

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| QuillScript narrative and encounter authoring | **LIVE PROVEN (scoped)** - authored `MelodiaQuillSmoke` drives the integration proof; the allowlist contract is checked by [`test_qsc_allowlist_contract.py`](Content/Python/Tests/test_qsc_allowlist_contract.py) | `Plugins/QuillScript/`, `Content/MelodiaIntegration/Narrative/*.qsc`, `UMelodiaNarrativeSubsystem`, `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig` | Dialogue, choices, encounter intent, consequence and reward content | A new dialogue runtime, quest authority, or parallel notification bus |
| Chapter scaffold and stable IDs | **SOURCE + CONTRACT PROVEN; existing package has a known validation failure** - [`scaffold_chapter.py`](Tools/scaffold_chapter.py), [`test_scaffold_chapter.py`](Tools/test_scaffold_chapter.py), [`test_melodia_chapter_content_package_contract.py`](Tools/test_melodia_chapter_content_package_contract.py), `Chapters/_template/`; scaffold regression passes, while existing Shorewake IDs still fail the broader QSC contract | `Chapters/_template/{quill,maps,encounters,rewards}`, `Tools/scaffold_chapter.py`, `specs/progression/` | New Chapters, side quests, creature Episodes and reusable encounter/reward packages with gated IDs | A new chapter loader or hand-authored ID convention; validate the IDs and use the scaffold |
| Quill encounter -> JRPG battle -> rhythm -> typed result -> Quill resumes once | **LIVE PROVEN (scoped owner seams)** - [`ue_level_building_coinsheet_2026-09-01.json`](Saved/Audit/ue_level_building_coinsheet_2026-09-01.json) records `battle_integration_map` pass for unavailable/victory/defeat/fled, typed results and exactly-once Quill resume; the separate `rhython_grade_to_result` row proves grade-to-damage. This is not a fresh packaged golden run | `MelodiaExternalJRPGBridgeSubsystem`, `MelodiaNarrativeSubsystem::CompleteBattle` / `ResumeQuillOnce`, `MelodiaIntegrationMap`, `MelodiaQuillSmoke` | Boss battles, normal encounters, authored phase consequences, rewards and checkpoints | A new battle manager, transition graph, combat result type, or second Quill resume path |
| Rhythm grade affects authoritative JRPG combat | **LIVE PROVEN** - `FMelodiaRhythmGradeBoundaryTest`, the `rhython_grade_to_result` ledger row, and `MelodiaRhythmCombatSubsystem` verify Q/W/O/P grade data reaches the stock skill damage path. 2026-09-17: `DA_CrescendoWave`, `DA_DissonantSilence`, `DA_DownbeatBreak`, `DA_HarmonyShield`, `DA_TempoShift` existed fully authored but were never wired into `RegisterSkill` in `BP_MelodiaJRPGGameInstance` (only `DA_CadenceStrike`/`DA_ResonantArc`/`DA_LullabyMend` were) — added the missing `RegisterSkill` calls; live PIE confirms all 8 skill IDs now resolve via `MelodiaRhythmCombatSubsystem::find_skill` on fresh boot. Full in-battle rhythm-prompt UI feel-test still blocked by an unrelated pre-existing `BP_BattleController`/`BP_BattleBase` bug (`battleUI`/`playerUnits` never populate outside the normal encounter-trigger flow, causing a runaway loop in `GetReadyUnitsBasedOnSpeed`) | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp`, authored `UMelodiaRhythmSkillDefinition` / skill data, `Content/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` | New rhythm skills, attacks, patterns, grade-driven damage, healing or resource effects | A second damage formula, rhythm combat authority, or bespoke boss combat framework |
| Wardrobe, traversal and gameplay capability hooks | **LIVE PROVEN + RESTART PROVEN baseline** - `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, [`P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`](Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md), and the restart slot proof pass | `Plugins/MelodiaWardrobe/`, `UMelodiaWardrobeSubsystem`, `MelodiaTraversalComponent`, wardrobe catalog manifests | Outfit abilities, traversal gates, creature/world relationships and battle/rhythm affordances | A new outfit inventory, equipment owner, traversal capability registry, or cosmetic-only workaround |
| Music-as-key world unlock | **LIVE PROVEN (scoped)** - the coinsheet receipt records one idempotent Piano phrase -> typed world result -> visible route; [`music_world_key_real_input_2026-08-31.json`](Docs/Evidence/music_world_key_real_input_2026-08-31.json) and [`P0_REAL_INPUT_PROBE_2026-09-09.json`](Docs/Evidence/P0_REAL_INPUT_PROBE_2026-09-09.json) provide route/input evidence | `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_MusicManager.uasset`, `MelodiaMusicClockSubsystem`, Quill world-result path, `Content/Python/build_pcg_piano.py` | Musical world puzzles, phrase-locked routes, keys, shrines and side-quest progression | A new puzzle framework, second music clock, or one-off door/route authority |
| Choral Sheep companion and Harmonize | **LIVE PROVEN (PIE behavior + REST/HIT fleece stills 2026-09-20)** - 2026-09-13 morning probe plus 2026-09-20 `ApplyChoralSheepDefinition` true / `TryBeginHarmonize` true / weight 1.0→0.0. Visual lock: `MI_ChoralSheep_Body` → `M_Master_Toon_Character`; child `MI_ChoralSheep_Body_Chladni_C` + `T_Chladni_C_ROOT`. REST still is dark wool; HIT still shows blue Chladni contours (`Saved/Audit/Screens/ship_queue_fleece_{REST,HIT}_v2_clean.png`) | `Content/Melodia/Companions/ChoralSheep/`, `BP_ChoralSheep`, `DA_ChoralSheepDefinition`, `MelodiaCompanionComponent`, `TryBeginHarmonize` | Creature Episodes, companion abilities, creature reactions and harmony moments | A new companion framework, ad-hoc creature state, or rig reopening without a current defect |
| Save, checkpoint and reward ownership | **LIVE/RESTART PROVEN for the baseline; long-chain repeat proof remains open** - `UMelodiaNarrativeSubsystem` owns authored checkpoints/consequences and exactly-once transactions; stock JRPG owns its save state; [`ue_level_building_coinsheet_2026-09-01.json`](Saved/Audit/ue_level_building_coinsheet_2026-09-01.json) records wardrobe restore. Issue #51 remains the explicit long-chain gate | `MelodiaNarrativeSubsystem`, `MelodiaSaveRecoverySubsystem`, `MelodiaSaveSlotLibrary`, `BP_JRPGSaveGame`, canonical reward/flag paths | Checkpoints, reward claims, side-quest completion, route restoration and durable episode history | Direct SaveGame writes, duplicate reward registries, or a new save authority |

#### Procedural worldbuilding and musical fields

The productive affordance is real: the proven Sea Above path enriches PCG points with a Resonance
float and packs it into per-instance custom data for material response. Musical/cymatic data can
drive geometry, scatter and material/Niagara response. Use that lane; do not manually place every
instance or invent a new world signal system.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| UE 5.8 PCG and PCG Extended Toolkit | **PRESENT / SOURCE-TOOL PROVEN; LIVE PROVEN in scoped graphs** - `BS_GodFile.uproject` enables `PCG`, `PCGPythonInterop` and `PCGExtendedToolkit`; `Plugins/PCGExtendedToolkit/PCGExtendedToolkit.uplugin` targets UE 5.8; Sea Above receipts and offline contracts cover the current graph path | UE PCG graphs, `Plugins/PCGExtendedToolkit/`, `Content/Python/pcg/`, existing `/Game/EnvSandbox/PCG/` authorities | Procedural biomes, musical architecture, scatter, falloffs and setpieces | Hand-authored actor forests, a new scatter framework, or a parallel PCG graph authority |
| Resonance Ecology processor and instance material bridge | **LIVE PROVEN on 1 Sea Above graph; reusable editor tooling for the remaining graphs** - current state records `PCG_East_PhyllotaxisCourtyard` at 140 instances with Resonance 0.030-0.925 and one custom float; [`SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json`](Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json) records placement/runtime pass and no parallel graph | `Content/Python/pcg/resonance_ecology_processor.py`, `Content/Python/pcg/apply_resonance_to_sea_above.py`, `Content/Python/pcg/test_resonance_ecology.py`, existing Resonance Cathedral/Sea Above graphs | Cymatic ecology bands, musical density, material variants and resonance-driven geometry/scatter | Hardcoded biome bands, per-asset custom scripts, or another PCG enrichment authority |
| World Field Bus Resonance/Tension contract | **SCAFFOLDED / SOURCE CONTRACT - not LIVE PROVEN** - `MelodiaWorldFieldBus.*` defines `ResonanceN/M`, `Tension`, `BeatPulse` and position sampling; [`world_field_bus_probe_2026-09-02.json`](Saved/Audit/world_field_bus_probe_2026-09-02.json) says SCAFFOLD and the PIE note records parameter-name alignment still open | `UWorldFieldBus`, `MelodiaCymaticsSubsystem`, `MelodiaOceanologyWaterBridgeSubsystem` | A shared future field for cymatic water, PCG and material consumers once the contract is closed | Another global bus, guessed MPC parameters, or claiming the current scaffold is a live contract |
| Sea Above musical PCG proof | **LIVE PROVEN (scoped) / not full route certification** - [`SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json`](Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json) is `PLACEMENT_RUNTIME_PASS`; current state records 1 of 9 Resonance Ecology graphs. [`P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json`](Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json) is `PASS_SCOPED`, with visible-frame/focused-player/package work still open | `LV_SeaAbove_Prototype`, existing PCG graph authorities, `Content/Python/pcg/apply_resonance_to_sea_above.py`, `Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` | Author a musical biome or setpiece now, while keeping the uninterrupted player route and visual-capture boundary honest | A new Sea Above world framework or a claim that every graph/consumer is already live |
| Resonant World generator + World Compiler | **SOURCE/TOOL PROVEN + LIVE PROVEN scoped on `L_MelusinaMorning`** — flowers on **BrushifyIsland_*** only; dressing (`brushify_overgrowth` / `brushify_roots` / `brushify_bush`) on `WC_EscherWalk_*` plus island skirts. Bedroom / classic_arch / Sphere3D / `WC_DellFloor` never plantable. 2026-09-18 compile **1090** points (971 flowers + 119 dressing) / **1079** PCG ISMs; `WC_morning_rainbow_bloom_Field` pinned to island AABB. `WC_Lookdev_waterline_dolly` at `[-3100,200,180]` roll 0. No Landscape, no PCG graph rewrite, no MPC/PPV writes. Compile stays CLI. Proof [`world_compiler_morning_rainbow_bloom_proof_2026-09-18.json`](Saved/Audit/world_compiler_morning_rainbow_bloom_proof_2026-09-18.json), close-out [`camera_dressing_closeout_2026-09-18.json`](Saved/Audit/camera_dressing_closeout_2026-09-18.json). Substrate Toon A/B remains PARK. | [`WORLD_COMPILER_CONTRACT.md`](Docs/WorldGen/WORLD_COMPILER_CONTRACT.md) §6.1, `Tools/world_compiler.py`, `Content/Python/world_compiler_ue.py`, `Content/Python/world_compiler_panel.py`, `recipes/morning_rainbow_bloom.v1.json`, `Content/Python/resonant_world_generator.py`, `Tools/terrain_handoff.py`, `Tools/scaffold_chapter.py` | Compile a recipe into PCG-driven dressing (point field + band MIs + signal bindings) without a new authority | A new scatter framework, Python-wired PCG graphs per species, `new_object` ISMs, a second MPC writer, a second compiler inside EUW, Houdini Engine as a live overlay |
| PhraseBus OSC ingest (Listening Field) | **LIVE PROVEN 2026-09-20 21:58** — PIE `UEDPIE_0_L_MelusinaMorning` on the open WIP uproject; UDP `127.0.0.1:9000`; `/melodia/phrase/state` `,isifsfi` 72 B + `/melodia/phrase/boundary` `,ii` 40 B; GetCurrentState **bar 0 / energy 0.0 → bar 10 / energy 0.92** (phrase_index 4, CLIMAX, RISING). Loaded `UnrealEditor-BS_GodFile.dll` **3,232,768 bytes** mtime **2026-09-20 17:48:36** (`RecvFrom`). `Recv()` was the old unconnected-UDP bug, not current debt. | `UMelodiaPhraseBusSubsystem`, `Tools/phrase_bridge/`, [`LISTENING_FIELD_SPEC_2026-09-20.md`](Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md), `Tools/listening_field/jev_director.py` | Live phrase state for existing `TryBeginHarmonize` and Jev director picks | `Recv()` ingest; a second phrase bus or OSC port; `resonant_world_phrase_bridge.py` as Jev; `jev_showcase_bloom` as the director; Jev mutating UE |

#### Houdini, Hython and Copernicus production lane

This is an available production lane, not a research-only idea. The evidence boundary is important:
Houdini 22 Hython is healthy and the Copernicus/HDA generators, manifests and asset families are
present; current `origin/main` does **not** contain a receipt proving a custom HDA cooked and baked
inside UE. License/editor-cook proof remains intentionally unpromoted.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Houdini Engine plugin in UE 5.8 | **PRESENT / SOURCE + PREFLIGHT PROVEN; LIVE UE HDA COOK NOT PROVEN** - [`HoudiniEngine.uplugin`](Plugins/HoudiniEngine/HoudiniEngine.uplugin) is H22.0.368/UE 5.8 and `BS_GodFile.uproject` enables it; [`smoke_houdini_engine_pcg.py`](Content/Python/smoke_houdini_engine_pcg.py) checks the plugin/hython/project; the smoke/spec still record license and editor-cook steps as pending | `Plugins/HoudiniEngine/`, `BS_GodFile.uproject`, `Content/Python/smoke_houdini_engine_pcg.py`, `hda/README.md`, `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` | HDA geometry, procedural stairs/chords, Houdini-authored production geometry and design-time bake to UE meshes/HISM/Nanite | A new UE procedural bridge; use the HDA lane when the license/cook gate is actually available, with PCG/Python as fallback |
| Hython procedural generation and deterministic handoff | **SOURCE/TOOL PROVEN; output families are receipt-backed, not a live UE cook claim** - [`hython_monolith_bridge_report.json`](Saved/Audit/hython_monolith_bridge_report.json) records Houdini 22.0.368, `hou_available`, and a healthy Hython lane; manifests record seeds, outputs and hashes | `Tools/Houdini/`, `Tools/Houdini/copernicus/`, `Content/Python/create_hda_arpeggio_stair.py`, `Saved/Audit/copernicus_cymatic_manifest.json` | Deterministic geometry/HDA generation, seeded variants, reproducible handoff into UE | One-off exported meshes without seed/manifests, or a bespoke procedural backend |
| Copernicus texture/material generation | **PRESENT / SOURCE + OFFLINE ASSET PROVEN; live UE/HDA handoff not proven** - [`copernicus_dress_bake.py`](Tools/Houdini/copernicus/copernicus_dress_bake.py) builds the SOP -> COP network; [`README.md`](Tools/Houdini/copernicus/README.md) documents the COP/ROP path and contracts; Hython and output manifests are audited | `Tools/Houdini/copernicus/copernicus_dress_bake.py`, `copernicus_fabric_sheen.py`, `copernicus_terrain_height_to_nanite.py`, `copernicus_petal_variants.py`, `Content/Python/verify_tex_contract.py` | Dress/fabric sheen, masks, curvature/thickness/AO, terrain-height -> Nanite, petal and material variants | Ad-hoc PIL-only material baking, a new texture pipeline, or making live HDA cooking a hidden dependency |
| Cymatic PBR map families | **PRESENT / SOURCE + ASSET PROVEN; live material import/build remains separate** - [`cymatic_audit_2026-09-01.json`](Saved/Audit/cymatics_audit_2026-09-01.json) and [`cymatics_present_status.json`](Saved/Audit/cymatics_present_status.json) record valid on-disk families and offline wiring while noting live import/build work; `copernicus_cymatic_parallax.py` defines seeded Chladni/cymatic families and nine-map output | `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`, `Saved/Audit/copernicus_cymatic_manifest.json`, `Saved/Audit/copernicus_cymatic/`, `Saved/Audit/cymatics_present_status.json` | Cymatic stone, fabric, sheen, masks, animated/flipbook variants and material dressing | A new master shader or untracked texture family; extend the existing map/MPC contracts |

#### Materials, cymatics, shaders and presentation

The material convention is scalar MPC data, not a new master per effect: `MPC_Melodia_Palette`
is the audio source, `MPC_Cymatics_Driver` is the cymatic driver, and the existing driver fields
include `Cymatic_BassIntensity`, `Cymatic_MidIntensity`, `Cymatic_BeatPulse`,
`Cymatic_EmissiveScale`, `Cymatic_IridescenceShift`, `Cymatic_UVDistortion` and
`Cymatic_ModeN/M`. `WorldField.ResonanceN/M` and `WorldField.Tension` are bus-struct fields, not
MPC parameters; the water bridge maps them to its consumer contract. Extend those existing
contracts and the canonical masters when a new reactive variant is needed.

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Nikki-derived toon/material path | **PRESENT / ASSET + SOURCE PROVEN; scoped live use** - `M_Master_Toon_Character.uasset` and `M_Master_Toon_Universal.uasset` are tracked; Sheep proof binds `MI_ChoralSheep_Body` to the approved character master with Chladni as a child. Live 2026-09-17 marketplace reconvert (fromage disk, not this git tip): Megascans **237/237** MI + Quixel leftovers **2/2** reparented onto `M_Master_Toon_Universal` / `M_ToonFoliage`; Brushify Floating Islands **98** reparented / **13** skipped (sky/cloud/water/FX) / **0** fail (`Content/Brushify - Floating Islands` disk, `/Game/Brushify/...` mount); Enchanted Vehicles Melodia wrappers authored on Universal (mesh slots still stock). **Custom_MS is not the pipeline target.** Receipt: [`TOON_RECONVERT_CLOSEOUT_2026-09-17.md`](Docs/Audits/TOON_RECONVERT_CLOSEOUT_2026-09-17.md) | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Character.uasset`, `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset`, `Content/EnvSandbox/Materials/Masters/M_ToonFoliage.uasset`, `Content/Melodia/Companions/ChoralSheep/`, [`CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json) | Author new hero, creature, outfit and biome material variants while keeping the current toon identity; reparent marketplace MIs onto Universal / ToonFoliage | A new master-material architecture, Quixel Custom_MS overwrite masters, or replacing the Nikki-derived base with a parallel shader |
| Audio-reactive presentation and cymatics driver | **SOURCE + SCOPED LIVE PROVEN** - `UMelodiaAudioReactivePresentationSubsystem` is the sole continuous writer to `MPC_Melodia_Palette`; `UMelodiaCymaticsSubsystem` is read-only; `UMelodiaCymaticsWriterSubsystem` is the sole writer to `MPC_Cymatics_Driver`, reading the palette and publishing derived cymatic lanes. Sea Above pulse/mode/amplitude automation is `PASS` with one audio writer. New source semantics (for example wind direction/strength) must enter through the existing upstream/source-authority path, never by adding a second driver writer | `MelodiaAudioReactivePresentationSubsystem.*`, `MelodiaCymaticsSubsystem.*`, `MelodiaCymaticsWriterSubsystem.*`, `Content/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.uasset`, `Content/Melodia/Cymatics/MPC_Cymatics_Driver.uasset`, `Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` | Audio-reactive materials, Chladni response, beat/mode/tension-driven water, Niagara and surface presentation | A second audio writer, a second MPC contract, or a new master shader for each variant |
| Chladni/cymatic shader automation | **PRESENT / SOURCE PROVEN; consumer-specific visual proof varies** - `Source/MelodiaShader/Shaders/` contains the shader module; Chladni sampling and material automation scripts are present; use the current PPV/material receipts for visual proof | `Source/MelodiaShader/Shaders/`, `Content/Python/assign_toon_profiles.py`, existing MPC contracts | Reactive shader/material variants and automated parameter application within the frozen identity | Hand-guessed parameters, per-widget/per-material constants, or a new universal master |
| Frozen PPV, Niagara and flipbook presentation stack | **OWNER-APPROVED / LIVE PROVEN scoped** - [`PPV_STENCIL_PIE_2026-09-13.json`](Docs/Evidence/PPV_STENCIL_PIE_2026-09-13.json) and the current identity record in this file prove the frozen visual boundary; canonical Niagara effect types and companion VFX assets are tracked, while visual work remains asset-specific. Package B BeatBurst / HybridSparkles / PetalCascade playbooks landed via #232. #239 adds the durable BeatPulse companion-bus, long-form Fix A, SurrealFabric flipbook-master rules, plus the asset-specific BeatPulse/LeafPile receipts; these docs do not promote blocked live polish into runtime proof | Frozen `PPV_NikkiDream` stack, `Content/Melodia/VFX/EffectTypes/ET_Melodia_CharacterFX.uasset`, `Content/Melodia/Companions/ChoralSheep/VFX/`, [`Docs/VFX/README.md`](Docs/VFX/README.md), [`Docs/VFX/Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md`](Docs/VFX/Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md), [`Docs/VFX/Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md`](Docs/VFX/Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md), `Tools/Houdini/sea_above_reef/shorewake_animated_flipbook.py`, `Content/Python/import_flipbooks.py`, `UMelodiaAudioReactivePresentationSubsystem` | Storybook identity, audio-reactive VFX, canonical Niagara effects, flipbook shimmer and polished captures | A new post-process identity, duplicate Niagara framework, or a “fancy VFX” system outside the canonical stack |

#### UI authoring

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Melodia UI artist skill and existing Quill UI chain | **PRESENT / SOURCE-TOOL PROVEN; audit + authoring contract established** - both agent skill copies define the token SSOT, Quill widgets, audit and editor apply workflow; current state records the read-only inventory of 144 widget Blueprints / 955 styled widgets. UE `GameColors` / `KeybindColors` resolve from `tokens.json` (Champagne Gold `#C9A86A`, not Nikki leftover hexes). #239 adds the content-first skill/tooltip/motion contract and machine-readable schema; presentation never replaces gameplay authority | [`.claude/skills/melodia-ui-artist/SKILL.md`](.claude/skills/melodia-ui-artist/SKILL.md), [`.agents/skills/melodia-ui-artist/SKILL.md`](.agents/skills/melodia-ui-artist/SKILL.md), `melodia-design-system/tokens.json`, [`Docs/UI/SKILL_TOOLTIP_MOTION_AUTHORING_2026-09-17.md`](Docs/UI/SKILL_TOOLTIP_MOTION_AUTHORING_2026-09-17.md), [`Docs/UI/skill_content_contract.schema.json`](Docs/UI/skill_content_contract.schema.json), [`generate_melodia_design_tokens.py`](Content/Python/generate_melodia_design_tokens.py), [`ui_style_audit.py`](Tools/ui_style_audit.py), `Content/Melodia/UI/Quill/`, `Content/Python/assign_melodia_quill_presentation.py` | UI polish, new dialogue/selection screens and authored screens that match the current identity | A new widget framework, manual style guesses, or hand-editing `.uasset`; load the skill first |

**Concrete authoring example:**

```text
Quill boss intent (allowlisted encounter ID)
  -> Phoenix skill/action (authored JRPG skill data)
  -> existing rhythm phrase/session
  -> Q/W/O/P grade
  -> Phoenix authoritative damage/result
  -> Quill consequence, reward and checkpoint
```

The current proof covers the owner seams needed for this shape. Author the boss's IDs, skill data,
phrase, dialogue, consequence and reward through those entry points; do not design another battle or
rhythm framework. Keep the packaged golden-run and long-chain persistence gates separate until they
have their own evidence.

**Tutorial instance — Melody Slime first tide (authored 2026-09-18, PIE proof still owed):**
`SlimeTideCurrent` + `Chart_Tide_Wave` transcribed to `DA_MelodySlimeTutorialSongs` ("Tide Wave",
12 eighth-notes, 128 BPM) + `DA_TideWave` (`tide_wave`, auto-discovered by the subsystem scan) +
`BP_MelusinaTidecall` (stock skill, PetalCadence behavior) mapped in `StockSkillRhythmIds` (6/6
entries preserved) + `MelodiaQuillSlimeTutorial` (30 compiled statements, battle/quest/reward/flag
notifies verified) with allowlisted `melodia_slime_tutorial` / `quest.slime_tutorial.first_tide` /
`reward.slime_tutorial.tidecall` / `flag.slime_tutorial.completed`. MorningIntro carries
`mel_perch_01` + `mel_battle_entry` voice cues (compiled). `BP_MelodySlimeTutorialBattle` roster is
`{slime: chance 1.0, lvl 1}` with `fleeChance 100`. Wired 2026-09-18 (commit 593ef613e):
battle actor tagged `melodia_slime_tutorial` (actor package force-added, one-time),
`Morning_QuillTrigger_SlimeTutorial` placed at the battle actor in the persistent level with
`QuillScriptToPlay` resolved to the tutorial QSC, map + 3 external packages saved, dirty 0,
pushed 0 0. Still owed: Tidecall display-text check + the real-input PIE
proof (victory/defeat/flee + exactly-once resume). `MI_MelodySlime_Body` (toon master, Tide tint,
canonical Chladni, `BeatAccent 1.5`) is presentation-ready; the unit still wears the mannequin
until the visual swap is judged. Breath wired 2026-09-18: tick-driven squash-and-stretch on
`SlimeMesh` (`Sin(time)` through mirrored `MapRangeClamped` ±5%, XY swell against Z settle,
parent Tick preserved, 0 errored BPs); beat-pulse rides the existing driver→master path.
Skin bound 2026-09-18: `SlimeMesh.OverrideMaterials[0]` now wears `MI_MelodySlime_Body`
(the mesh slot alone wore plain `Material_002`); master carries the full reactive
vocabulary (`BeatAccent`, `Chladni*`, `HarmonizeActive`, 31 params).

**Zundamon battle unit + Morning exploration platform crossing (authored 2026-09-18):**
`ABP_Zundamon_Battle` (`target_skeleton = SK_Zundamon_Skeleton`, duplicated from the stock
`A_BattleAnimationBlueprint`) plus `AM_Zundamon_Attack`/`AM_Zundamon_GetHit` montages are compiled
and saved. `BP_WeakEnemy`'s `BeginPlay` now sets `SkeletalMeshAsset`/`AnimInstanceClass` to the real
Zundamon mesh/ABP (a per-child graph override, not a CDO write, so the shared `BP_UnitBase` parent
and its other children stay untouched); live PIE confirms `BP_WeakEnemy_C_*` spawns with the real
mesh. **Known gap:** `Content/TurnBasedJRPGTemplate/Blueprints/Units/EnemyUnits/*` is excluded by
`.gitignore` (line 178), so `BP_WeakEnemy`'s wiring cannot be committed — it exists only on this
machine's disk and must be redone if that file is ever lost. `L_MelusinaMorning`'s ~46-piece
`WC_EscherWalk_*` blockout was redesigned into one continuous golden-ratio spiral (φ-scaled radius
per turn, five Fibonacci-fraction clearings) connecting the real `BrushifyIsland` terrain, with
`BP_Starskiff_MK2` relocated to water level at the spiral's base. The four pre-existing, never-wired
`MelodiaMovingPlatform` actors near the spiral's summit spur (previously default blockout values,
`bAutoStart=false`) are now a real crossing: repositioned into a bridge line to a new landing piece,
`bAutoStart=true`, staggered `TravelDuration` (1.6-2.6s) so their vertical ping-pong drifts out of
phase over time — confirmed moving via two live PIE position reads (DedicatedServer net mode, no
relay/Blueprint-graph wiring needed). Zundapal/`BP_Enemy_StoneGolem` also has a real imported mesh
(`SK_Zundapal`, single-node embedded animation, no retarget — 38 vs 82 bones, by design) but
`Content/Melodia/Enemies/**` is entirely outside the `.gitignore` allowlist (owner decision: leave
it out of git for now), so none of that is trackable either.

### WHAT TO REACH FOR

| User asks for... | Reach for... |
|---|---|
| New boss | Quill + Phoenix/JRPG + existing rhythm seam + authored skill/data |
| Side quest | Chapter scaffold + Quill + stable IDs + existing reward/save owners |
| New rhythm ability | Existing rhythm execution + JRPG Skill/command path |
| Musical biome | Cymatics -> Resonance/PCG data -> World Compiler recipe -> UE PCG + material/Niagara consumers; remember the broader World Field Bus is scaffolded |
| Live phrase / Listening Field | PhraseBus `RecvFrom` UDP `:9000` + Jev director-only (`Tools/listening_field/jev_director.py`); Morning WC stays BrushifyIsland `--skip-scaffold` |
| Procedural environment | UE PCG/Python and/or Houdini Engine/Hython, with the current proof label |
| New cymatic material | Copernicus/Hython map family + existing toon/material/MPC contracts |
| Outfit mechanic | Wardrobe subsystem + existing capability/Convergence hooks |
| UI polish or new screen | `melodia-ui-artist` skill + tokens + existing UI ownership |
| Fancy VFX | Canonical Niagara/flipbook/audio-reactive stack |
| Character rig repair | **Only** if current evidence shows an actual rig defect; do not reopen four-month-old rig work by default |

**Sea Above boundary:** the live proof is one Resonance Ecology graph and scoped cymatic/runtime
automation. The processor/apply script, remaining graph bindings, World Field Bus consumers and the
uninterrupted focused-player/package route are reusable or open work, not silently promoted proof.

| Capability | Level | Evidence |
|---|---|---|
| Editor build | SOURCE BUILT | Game + `MelodiaCore` DLLs rebuilt 2026-09-12 21:55 by a Codex UBT run from the local `cleanup/pbr-twin-landing-2026-09-10` working tree — not from `main` |
| Music node → `reward.first_resonance_echo` → Accessories auto-equip → Glide → portal unlocks | LIVE PROVEN 2026-09-01 | `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`, `Saved/Audit/p0_real_input_run/` |
| Wardrobe save → full editor restart → load → outfit restored | RESTART PROVEN 2026-09-01 | slot `P0_Shorewake_Validation`, `LOADED_NARRATIVE_RESTORED` |
| Battle outcomes (victory / defeat / fled / unavailable) return a typed result; Quill resumes exactly once | LIVE PROVEN 2026-08-27 | `MelodiaIntegrationMap`, `MelodiaQuillSmoke` |
| Rhythm grade (Q/W/O/P) scales stock JRPG damage | LIVE PROVEN (owner PIE 2026-08-12/13) | `FMelodiaRhythmGradeBoundaryTest` |
| Audio reactivity on every level | LIVE PROVEN | `b1cac649`; music clock on the GameMode `5fea50c8` |
| Packaged Development route, both legs, 0 fatals | PACKAGED (bounded) | builds at `G:\melodia_packages\P0_Closeout_20260902\`, `P0_Route_20260903\`; not a golden-run certification |
| Starskiff board / move / disembark | LIVE PROVEN (PIE) | `AMelodiaStarskiffPawn` — stabilize only |
| Resonance Ecology PCG enrichment (decision 057) on Sea Above biome graphs | LIVE PROVEN 2026-09-12 — 1 of 9 graphs | #196, #198, #203; `PCG_East_PhyllotaxisCourtyard`: 140 instances, 1 per-instance custom float, Resonance 0.030–0.925. `Content/Python/pcg/apply_resonance_to_sea_above.py` applies it to the rest |
| Choral Sheep on the approved Nikki Cymatics path | LIVE PROVEN 2026-09-12 | `MI_ChoralSheep_Body` → `M_Master_Toon_Character` with `T_Chladni_C_ROOT`; child `MI_ChoralSheep_Body_Chladni_C` |
| Choral Sheep Harmonize (definition → begin → ramp → decay) | LIVE PROVEN (PIE) 2026-09-13 | `L_MelusinaMorning`: `ApplyChoralSheepDefinition` true, `TryBeginHarmonize` true, weight 1.0 → 0.0 after end. Required `DA_ChoralSheepDefinition` role Companion + `NPCId`. `Docs/Evidence/CHORAL_SHEEP_MORNING_PROBE_2026-09-13.json`; fleece not yet captured |
| Choral Sheep mesh → definition → ABP → anims | LIVE PROVEN 2026-09-13 | `SK_ChoralSheep` = 1,000-vert `...FINALCANON...fbx` body (identical rest pose, 118 bones); `ABP_ChoralSheep` Idle/Walk/Run on `Anims/A_Sheep_*` (retargeted via `RTG_MrSheep_To_ChoralSheep`), compile 0/0; applied at runtime by `MelodiaCompanionComponent`. Receipts: `Docs/Evidence/CHORAL_SHEEP_{ABP_LOCOMOTION,RETARGET_DEFORMATION}_PROOF_2026-09-13.json` |
| Choral Sheep follow → Idle/Walk/Run | LIVE PROVEN (PIE) 2026-09-13 | #210: `MelodiaCompanionComponent` writes root `ComponentVelocity` (follow used `SetActorLocation`); `ABP_ChoralSheep` reads `GetOwningActor` velocity (was `TryGetPawnOwner`, null on an Actor). Under `slomo 0.1`: `Speed` 5,970 → 269 cm/s across 26 frames, crossing Walk 10 and Run 120, back to 0. Packed `BakeUV` now UV0 on `SK_ChoralSheep` |
| Frozen PPV stack on `L_MelusinaMorning` | owner-approved 2026-09-13 | `PPV_NikkiDream` → `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen/` (gitignored; backups + report `Saved/Audit/ppv_lookdev_2026-09-13/`). Outline V7 after tonemapping, un-jittered filtered taps; ink misregistration/smear wired, static grain. `DefaultEngine.ini`: `r.TSR.ThinGeometryDetection=1`, `...Coverage.ShadingRange=0` |
| Hero stencil 4 (PP outline skips hull-outlined heroes) | LIVE PROVEN (PIE) 2026-09-13 | #210 body meshes; #211 `UMelodiaHairComponent` + `UMelodiaWardrobeComponent` slots copy the body's custom depth/stencil. PIE on `L_MelusinaMorning` after a full editor build: `CharacterMesh0`, `WaterHairMesh`, `WardrobeSlot_{Shirt,Skirt,Boots,Accessories}` and `BP_ChoralSheep` mesh all read customDepth true / stencil 4 (`Docs/Evidence/PPV_STENCIL_PIE_2026-09-13.json`). Earlier `..._{a,b}.jpg` captures exposed the root cause (`MF_StencilDepthAlpha` returned a 0/1 in-range mask rather than the stencil value); Frozen outline V7.1 now reads `PPI_CustomStencil` directly. **Visual skip confirmed** in `..._{c,d}.jpg`: props keep the dark ink, Melusina (body, hair, dress) and the Sheep carry no post-process line. The shared original `M_PP_StorybookOutline_Premium_Candidate` still has the historical bug |
| P0 / Melusina Niagara hygiene | SOURCE + ASSET 2026-09-13 | 16 systems had ~1 cm fixed bounds (metre values; culling pops) → 300–500 cm; `ET_Melodia_CharacterFX` on 17 hero/gameplay systems; shadows off + view-distance sort on route sprites; dead `WaterSplashEmitter` disabled; duplicate `NS_MagicTrail` + 11 mirrored flipbook materials deleted. Report `Saved/Audit/vfx_pass_2026-09-13/` |
| Shorewake dress on Melusina's 465-bone skeleton | owner-confirmed fixed 2026-09-02 | `SK_ShorewakeDress_Melusina465`, `MI_Melusina_Dress_Shorewake`; not yet captured in-game |

**Active P0 gates — 8/8 pass:** `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`,
`wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, `music_world_key`, `static_gates`,
`battle_integration_map`. Ledger rows live in local `Saved/gate_ledger.json` — append-only, read
the **latest row per gate id**. The Aug 13–14 `runtime` / `save_load` / `repeat_consume` /
`package_launch` passes apply only to that baseline.

Automated tests: 524/524 at the 2026-09-01 captured revision (that total includes tooling suites —
MCP regression, Ollama daemon stress — not only game tests).

---

## 3. Open

### Morning level pass + Jev lane repair — 2026-09-20 (Claireon session)

**Landed on disk, uncommitted.** `recipes/morning_rainbow_bloom.v1.json`: `hero_falloff_cm`
2000→1000 and `palette.wind.response` 0.5→0.85. Outer radius is 1950 cm
(`inner 200 + 7 × 250`), so a 2000 cm falloff never engaged — every band ran at uniform
`density_per_m2 3.5` to the edge, the carpet the compiler contract forbids. `sector_deg` left
at 360° deliberately: four of five lookdev cameras sit south of the anchor looking *across* the
disc, so a wedge would read as a cut edge. Re-run
`Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 --lookdev`.
Wind hue-reveal chain is **proven working** (A/B `Saved/Audit/Screens/world_compiler_morning_wind_*_2026-09-17.png`
shows real hue shift undriven vs driven-east) but those plates are night-lit and predate the
`bedroom_keepout` clearance circle — judge the new weight in morning light, not against them.

**Jev lane repaired, uncommitted.** `typesafe-sdk==0.7.0` was **not installed**, so every Jev call
silently degraded to `classical-fallback` through a swallowed `ImportError` — it read as designed
degradation, not breakage. `Prototypes/JevP0Triage/jev_p0_triage.py` and `select_showcase_identity.py`
were still on the pre-v1 API (`from typesafe import`, `client.ask`, `.selection`, `.probability`);
ported to `typesafe_sdk` / `system_one` / `Choice|Noul|Score` / `.choice` / `.noul`. All 9 prototypes
now scan clean; tests 10/10 and 26/26; both verified `jev-live`. Live triage on real state returned
`HOLD_FOR_OWNER 0.58` / needs-human `0.89` / capture `L0` against gate staleness 38 d and 1914 dirty
files — the classical fallback it had been silently using said the opposite (`RUN_PIE_SMOKE 0.91`).

**Morning audit (read-only; nothing saved).** 647 actors / 465 StaticMeshActors / 456 meshed /
64 unique meshes / **56% greybox** (143 × `SM_Greybox_Cube_1m`). 22 duplicate groups = 88 actors,
every group exactly ×4 at one identical transform on round 100-unit grid coords (paste or script run
four times), 66 redundant; plus 9 empty StaticMeshActors. **Cleanup was executed (647→572, verified
0 duplicate groups / 0 empty) but left unsaved and lost on a level switch — redo it and save in the
same pass.** Vertical layout is fine (79 m span, well layered). Jev ranked greybox dominance top at
0.82 (conf 0.77) but scored it **not** disqualifying (0.32); rated the 83 squashed `WC_EscherWalk_*`
overgrowth actors 0.65 *intentional* — leave them alone.

**Hero corners: three of four dead, and it is graph-side, not placement.** Only MeadowChorus
generates (791). WestRim / EastBank / NorthDress generate 0. Volume geometry is ruled out by test:
all three were moved onto their own cameras' focal centres and grown from 58–138 m³ to 4 800 m³ and
still produced 0, then reverted to original transforms. Causes: `PCG_HeroCorner_WestRim` runs
`GetSplineData` → `PCGExSampleNearestSpline` and the level contains **zero spline actors**;
`PCG_HeroCorner_EastBank` (3 chains) and `PCG_HeroCorner_NorthDress` (18 chains) are
`SurfaceSampler` → `FilterDataByTag` whose filters are not matching (58 distinct tags exist, so tags
are not the shortage). Separately `PCG_Escher_FloatingStairways_Morning` and
`PCG_Escher_PenroseShrine_Morning` have degenerate **0×0×0** bounds.

**Tooling facts for the next session.** `ClaireonSettings.DisabledPIENetModes` was
`['Standalone','ListenServer']`; `Standalone` was removed **in memory only** — Python exposes no
`save_config` on that class, so it reverts on editor restart and must be set in Editor Preferences →
Plugins → Claireon → PIE to persist. Client net mode cannot reach the local player, so PIE proof is
impossible without Standalone. `bAutoSaveBeforeDeferredActions=True` writes an external actor package
into the open level on PIE start. Editor crashed `EXCEPTION_ACCESS_VIOLATION` in
`UnrealEditor-StaticMeshEditor.dll` via Slate at 19:04:39 (open Static Mesh Editor window, not Python).
A ready-to-run in-place greybox→Atlantis swap exists in the session scratchpad — transform-preserving
with bounds-ratio scale compensation and a `LABEL_PREFIX` filter for concurrent dressing; promote to
`Content/Python/` if kept. Jev set-dress direction: `swap_meshes_in_place` 0.81, but manual fixup
expected 0.84, focus on camera frames 0.83, achievable-today 0.91/3 ("one good shot").

### Morning greybox unit defect — found and repaired, 2026-09-20 (Claireon session)

**Root cause: `/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m` has a 1-unit (1 cm) bounding box
despite its "1m" name.** Any script that scales it expecting a 1 m cube produces geometry at 1/100
intended size. This is an asset defect, not a script defect — which is why the split in
`L_MelusinaMorning` fell exactly along authorship: every agent/compiler-placed `WC_*` cluster was
sub-centimetre, while every hand-placed actor (`gate` 435 cm, `monument` 1290 cm, `SM_classic_arch`
2036 cm, walls 604–698 cm) was correctly sized. Positions were always correct; only scale was wrong.

Measured before repair: 189 greybox actors, **146 of them under 10 cm** —
`WC_GreySpire_Helix` treads at 0.6 × 0.4 × 1.0 cm, `WC_GreyRoad_*` at 2.0 cm,
`WC_GreyGrotto_Pillar` 2.5 cm, `WC_WalkPath_Belvedere` 2.0 cm, `WC_GreySpire_Chamber` 5.0 cm.
The spire helix has therefore never been visible in any shot. This corrects the 2026-09-20 audit
entry above, which read "56% greybox" as a *dressing* problem: most of that greybox was invisible.

**Repaired in-editor (see "not in git" below).**
- 88 `WC_GreySpire_Helix` treads: mesh swapped `SM_Greybox_Cube_1m` → `SM_ATL_Palace_Cornice`,
  then sized to the measured spiral and yawed to its tangent — centre (198, 1637), radius 275 cm,
  25 cm rise, 5.30°/step, 68 steps/turn, 1.28 turns, Z 954→3133 (21.8 m). Tread 34 cm run /
  150 cm width / 14 cm thick. It is now an actual walkable staircase.
- 58 remaining sub-10 cm actors rescaled ×100 to authored metre sizes. Roads land at
  2 m × 1 m × 20 cm slabs spaced ~225 cm — they tile into continuous walkable paths, confirming
  the ×100 hypothesis exactly. Level now has **zero** sub-10 cm greybox actors.
- `WC_HeroCorner_NorthDress_Cam` was standing *inside* the spiral (116 cm from centre, radius
  275 cm) — that is why the corner framed nothing usable. Moved to (935, 2153, 1750) looking back
  at the staircase. The other three corners were not touched.

**Two save traps, both hit this session — read before editing actors from Python.**
1. `EditorLoadingAndSavingUtils.save_current_level()` returns `True` and writes **nothing** for a
   World Partition level. Each actor is its own package under `Content/__ExternalActors__/`.
2. Transform/mesh edits made through Python (`set_actor_scale3d`, `set_static_mesh`, …) **do not
   mark their package dirty**, so `save_packages(pkgs, only_dirty=True)` also returns `True` and
   skips everything. Both calls reported success while 157 actor packages sat unwritten on disk.
   The working call is `save_packages(pkgs, False)` — `only_dirty=False` — in chunks of ≤60 to stay
   inside the 30 s MCP socket timeout. Verify by file mtime, never by the return value.

**This level's geometry is not in git and cannot be committed from here.** `.gitignore:224`
ignores `Content/__ExternalActors__/*`, unignoring only `EnvSandbox/Monoliths/**`. All 157 saved
`L_MelusinaMorning` actor packages, and `SM_Greybox_Cube_1m.uasset` itself, are untracked. The
repair is on disk in the editor only. `.gitignore` is on the never-touch list; widening that rule
to cover `Melodia/Levels/` is an owner decision, not an agent one.

**Open:** 101 correctly-sized greybox actors still await the Atlantis mesh swap (roads →
`Floor`/`Base`, grotto pillars → `Columns`, gate → `Arch`, monument → `Fountain`). The underlying
asset defect in `SM_Greybox_Cube_1m` is **not** fixed — it will reproduce on the next script that
scales it. Fix the asset's import scale, or have placement code divide by its measured bounds
rather than assuming 100 units.

### Morning dressing + staging pass — 2026-09-20 (Claireon session, unattended)

Follows the unit-defect repair above. All changes saved and verified by file mtime
(352 actor packages written). Captures: `Saved/Screenshots/MorningDress_2026-09-20/`.

**Atlantis dressing (47 outdoor `WC_*` actors).** Roads and walkpaths (`WC_GreyRoad_*` 22,
`WC_WalkPath_Belvedere*` 13) → `SM_ATL_Palace_FloorA`; `WC_GreyGrotto_Pillar` ×8 →
`ColumnsC` (uniform, matched on height); `WC_GreyGrotto` ×2 → `IvyWallC`;
`WC_GreySpire_Chamber` ×6 → `IvyWallB`. All transform-preserving via bounds-ratio
compensation. House-interior greybox (`wall`, `corner`, `large`, `medium`, `small`,
`GB_Morning*`) deliberately **not** touched. Note prior sessions had already dressed
`WC_PhyloWalk_*` and `WC_SpireRamp_*` in the same Atlantis palette — these picks match it.

**`WC_SpireRamp_Landing` normalised.** All 8 shared one scale (0.573) across three meshes with
very different native bounds, so they ranged 768 cm to **5856 cm** and two were rotated
near-vertical — a 58 m plate 7 m from the NorthDress lens, and the wall-in-the-sky in frame.
All 8 now `FloorA`, flat (pitch/roll zeroed, yaw kept), uniform 766 × 768.

**Spire staircase connected and staged.** Its foot was at Z 954 with the terrace above it at
~1190, so the first ten treads were buried. Raised all 88 by +240 (foot 1194, top 3373). Added
`Morning/Spire/Base`: 4 × `ColumnsC` at 950 cm on a R=470 ring, plus `WC_SpireBase_GateArch_00`
(`ArchC`, 1150 cm) on the south-west approach.

**WestRim belvedere (new).** That corner was clean but empty. Built on the `BrushifyIsland_09`
plateau (flat at Z 1203, the same island the rainbow-bloom field occupies, so meadow + belvedere
now read as one hero location): `PergolaA`, 4 × `ColumnsC`, `FountainA`, 3 × `TreeC` — 9 actors
in `Morning/WestRim/Belvedere`, each ground-locked by line trace.

**World Outliner organised.** 330 actors filed into `Morning/{Spire,Paths,House,Grotto,EscherWalk,
Cameras,Dressing,WestRim}` sub-folders.

**All four hero cameras reframed** (originals recorded here for restore):

| Camera | Original | Now |
|---|---|---|
| NorthDress | (100, 1700, 1410) y37 p−19 — *inside the stairwell* | (−1615, 792, 2150) y25 p6 |
| EastBank | (−2000, 2120, 2925) y−47 p−15 | (2350, 1180, 1850) y168 p−7 |
| WestRim | (−2550, 1480, 2516) y148 p−56 | (−4750, 350, 1780) y25 p−9 |
| MeadowChorus | (−3698, 342, 786) y38 p−20 | (−3450, 880, 1330) y31 p6 |

**Two findings left alone, deliberately, for the owner's call.**
1. `RainbowBloom_R` (folder `Melodia/Morning/Rainbow`) is a HISM of 20 `Petal_petal_mid_2`
   instances at ~199 × 175 × 291 **m** each, actor bounds 608 × 191 × 662 m, centred 12 km south
   at (188, −10755, −1265). Actor scale is 1.0, so the size is baked into the instance transforms.
   At that size it renders as flat untextured magenta. It is authored, not obviously broken, so it
   was not rescaled — but it is the largest single object in the level by an order of magnitude.
   The `WC_morning_rainbow_bloom_Field` PCG output is by contrast healthy (flowers 18–95 cm,
   bushes 1–4 m, overgrowth 2–4 m).
2. The magenta cast over the Brushify islands is **not** a material override — all three island
   actors carry stock unmodified `MI_FloatingMountain_0*`. It therefore comes from the PPV/MPC
   layer, which this handoff puts off-limits, so it was not investigated further.

**Editor note.** A modal dialog *"This asset editor has no docked tabs"* reopens constantly and
blocks MCP on every save; close that asset-editor window. `AutomationLibrary.take_high_res_screenshot`
never wrote a file in this session — `claireon.slate_screenshot(target="level_viewport")` works and
is what produced every capture (it lands under the **engine** Binaries dir, not the project, so copy
it back).

### Melusina skirt and bow attack polish — execution plan, 2026-09-19

Owner target: Unreal gameplay and Unreal renders. Keep `SK_Melusina_V2_Body`,
`ABP_Melusina_Current`, the shared skirt skeleton and wardrobe leader-pose ownership.

1. Capture a baseline in one editor: idle, locomotion/turn/stop, bow draw, release,
   recovery. Read current skirt node, collision limits, animation bindings and weapon sockets.
   The 2026-09-15 tip/warm-up changes are asset evidence only until motion is inspected.
2. Fix observed skirt defects at their cause: collision placement and leg interaction,
   then response/settling only where the capture demonstrates a problem. Preserve authored silhouette.
3. Polish the actual gameplay bow animation binding and grip/string/arrow alignment;
   verify anticipation, draw hold, release, follow-through and recovery in sequence.
4. Capture front/three-quarter and side motion in Unreal, including a full attack and
   locomotion-to-attack transition. Pass requires no visible leg penetration, startup pop,
   persistent oscillation, detached grip, or release/arrow timing mismatch.
5. Save and reread each changed asset; repeat the motion after restart. Keep baseline,
   final clips and machine-readable evidence under `Saved/Audit/`. No completion claim
   from stills or successful property writes alone.

Execution 2026-09-20: V2 is the battle-presentation body; the bound bow montage plays in PIE. Skirt Kawaii uses reversible `SK_Melusina_V2_Skirt_R2_SmoothChains` (rigid vertices 10.93% -> 0.39%). Hair tune `Damping=.18` / `Stiffness=.08` — source rig is still 73 two-bone chains. Proof: `Saved/Screenshots/MelusinaPolish_20260920/`. Do not overwrite `harp_bow_pipeline` husks. `Polish_20260919` clips + `ABP_Melusina_Current` are in git on this PR.

### Repository/status reconciliation — 2026-09-17

- **Historical cleanup lane resolved.** PR #201 was superseded by merged #213; accidental resurrection PR #230 was closed unmerged. `cleanup/pbr-twin-landing-2026-09-10` is provenance only: never use it as a repository-health proxy or wholesale merge source. Salvage named unique work through scoped branches only.
- **September 17 durable landings.** #227 retargeted UE `GameColors` / `KeybindColors` to the design-token SSOT; #229 landed Melusina Morning audits; #231/#232 landed materials/VFX closeout playbooks; #234 landed the materials convergence inventory; #236 corrected marketplace material authority to `M_Master_Toon_Universal` / `M_ToonFoliage` and records the live reconvert counts. Main Echo run #565 is green.
- **Docs review cleanup.** #226 and #228 were closed unmerged after their durable content was selectively salvaged into #239; #233 remains closed unmerged as redundant after #237. Do not reopen the old review branches as status authorities. #239 intentionally keeps the UI authoring contract plus the reusable VFX playbooks/receipts while dropping #228's closeout handoff, bulk inventories/CSVs, graph dump, and duplicate status prose.

### Stabilization — 2026-09-13

| Item | Source / evidence | Remaining owner decision or proof |
|---|---|---|
| Branch archaeology | `Docs/Evidence/BRANCH_LEDGER_2026-09-13.json` remains historical inventory. `Tools/guard_collapsed_paths.py` blocks re-additions deleted by `08a608bc`, including renames, and runs on every PR. | #201 is historical/superseded by merged #213; #230 was closed unmerged on 2026-09-17. Never use `cleanup/pbr-twin-landing-2026-09-10` as a health proxy or merge it wholesale; reconcile named unique files only. |
| Identity canon | `UMelodiaIntegrationConfig` now exposes one runtime-owned core identity record: P0 player, Choral Sheep definition, hero stencil 4, ordered frozen PPV stack with weights, and character/ambient Niagara effect types. `Melodia.Wiring.CoreIdentity.Canon` reads that same config and resolves every reference. | Owner approved the narrow asset closure: 52 previously ignored packages (68.76 MiB), including the seven canonical Frozen PPV assets, `ET_Melodia_CharacterFX`, all recursive dependencies, and the three WaveHarp_R07 meshes. Closed-editor UE 5.8 Development build passed all 460 actions. Never substitute the unfrozen originals. |
| Chapter reuse | `Tools/scaffold_chapter.py`, `Chapters/_template/{quill,maps,encounters,rewards}`, and four-beat `03_tide_listening` source. Generator validates gated IDs against the actual DA before writing; numbered chapter folders are automatically tested. | Full QSC contract FAILS on existing SkiffDeparture `quest.shorewake.passage`, `flag.shorewake.passage`, `reward.skiff_passage`. Resolve those IDs and reward binding through the canonical DA in the editor; import the example and prove both choices/revisit/save-load in `MelodiaIntegrationMap`. Scaffold regression passes; no PIE claim. |
| UI staleness | Read-only `melodia-ui-artist` audit: rhythm HUD and four Quill widgets have palette colours. #227 resolved the shared UE `GameColors` / `KeybindColors` token drift against the design-token SSOT. Remaining P0 candidates include `BP_MelodiaBattleUI` RhythmGradeText/SongPickLabel white, stock `BP_BattleUI` authored text, `WBP_MainMenu`, and `WBP_MenuButton`. | Treat remaining candidates as reachability/runtime-binding checks before edits. `BP_MelodiaDefeatDialogue`, `BP_MelodiaVictoryDialogue`, and Foundation parchment/button styling still need targeted review; white image tints and transparent shadows are not automatically defects. |
| G: saved-state mirror | `Tools/mirror_saved_project.ps1` defaults to dry-run; scoped `/MIR`, destination/junction checks, cache/binary/Blender-autosave exclusions. Includes Content (Frozen + Cinematics), Config, Source, Plugins, Saved/Audit, Chapters, specs, Tools and design tokens. Dry logs: `%TEMP%/melodia-mirror-20260913/`. | Proposed destination `G:/BS_GodFile_Mirror/20260913`; initial dry run 119.75 GiB / 55,549 files plus project descriptor, zero failures/extras. Real run awaits owner approval and a saved, closed, stable source. This mirrors the saved local tree, including uncommitted assets; it is not a claim that local tree equals main. |
| World Compiler close-out (2026-09-19) | Live `--skip-scaffold --fx --lookdev` **PASS**. BrushifyIsland SpeedTree + walk dressing; Niagara children forged/placed; lookdev board recaptured (waterline_dolly / website_oblique / top / south / south_fix). | Hue may still read muted if Cymatics wind scalars stay 0 (do not write MPC). Substrate Toon PARK. Recruiter caption: compiler meadow on Brushify, frozen PPV, hue-reveal unproven until PIE wind. |
| Morning Niagara rewire (2026-09-19) | Disk **14:49** + live bind **PASS 2026-09-20**. `rewire_morning_fx.py --effect bind-user`: Petal/Pollen/Mist/Dust SpawnRate plus WindFront `Gust_Leader` `Spawn Count` → `User.WindFrontVisible`. WC `step_fx_place` writes pack User names. | Hue-reveal is PIE wind only (no MPC). PondMist `*001` cleanup remains. Do not edit EnvSandbox parents. Do not UBT while the editor is open. |
| Git close-out (2026-09-20) | Isolated batches on `feature/morning-closeout-2026-09-20` (PR #249); `origin/main` merged in a clean worktree. Morning umap/OFPA/PCG/ABP kept ours (09-19 rewire + HeroCorners + bow). | Park Frozen/MPC/`DefaultEngine.ini`/Humber/EnvSandbox dumps. Do not dump the WIP dirty tree. Do not merge `feature/b-castle-zen-hism-2026-09-19` as the Niagara tip. |

C++ and its asset closure passed a closed-editor UE 5.8 Development build (460/460 actions).
Offline contract suites: 22/22 PASS; collapse/scaffold regression tests: 2/2 PASS. The broader
QSC failure above is deliberately retained. The owner approved narrowly tracking the three
WaveHarp_R07 meshes and the exact recursive dependency closure; no other Cinematics path is
unignored.

**UI inventory, completed read-only:** 144 widget Blueprints / 955 styled widgets,
108 distinct colours / 73 font-size pairs. Raw inventory is local at
`%TEMP%/melodia-ui-audit-all-0913.json`. The table below lists game-facing authored-text
candidates outside the token palette, not verified runtime defects; check bindings,
animations and active screen reachability before changing values. Transparent shadows and
white texture multipliers are excluded. Third-party ArtOfShader/UltraDynamicSky editor
utilities are outside the game's styling scope.

| Folder | Remaining widget candidates (names relative to folder) |
|---|---|
| `/Game/Melodia/UI/` | `BP_MelodiaDefeatDialogue`, `Foundation/WBP_MelodiaUniversalButton`, `WBP_Battle_Results`, `WBP_BlessingBurden`, `WBP_ComicOrrery`, `WBP_DialogueBubble`, `WBP_MainMenu`, `WBP_MelodiaCurrencyRow`, `WBP_MelodiaOpeningSlideshow`, `WBP_MelodiaSettings`, `WBP_MelodiaTokenWallet`, `WBP_MelodiaWallet_Universal`, `WBP_MenuButton`, `WBP_QuestJournal`, `WBP_SaveLoadPanel`, `WBP_Settings`, `WBP_SkillCodex`, `WBP_UltCutIn` |
| `/Game/MelodiaIntegration/UI/` | `BP_MelodiaBattleUI`, `BP_MelodiaRhythmPrompt` |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | `BP_ActionTimeBar`, `BP_BattleUI`, `BP_CraftBar`, `BP_DamageTextUI`, `BP_ExpBar`, `BP_HPBar`, `BP_MPBar`, `BP_QuestNotification`, `BP_TurnOrderUI`, `BP_UnitClass` |
| Same stock folder, `Dialogues/` | `BP_BuyItemAmountDialogue`, `BP_CraftDetails`, `BP_CraftItemButton`, `BP_CraftItemRecipe`, `BP_DefeatDialogue`, `BP_DialogueButton`, `BP_EquipmentButton`, `BP_EquipmentStatComparison`, `BP_InfoDialogue`, `BP_ItemButton`, `BP_ItemObtainDialogue`, `BP_ItemUseDialogue`, `BP_LevelUpDialogue`, `BP_QuestButton`, `BP_SellItemAmountDialogue`, `BP_ShopBuyDialogue`, `BP_ShopBuyItemButton`, `BP_ShopSellDialogue`, `BP_SkillButton`, `BP_SkillUseDialogue`, `BP_VictoryDialogue`, `BP_YesNoDialogue` |
| Same stock folder, `MainMenu/` | `BP_EquipmentDetails`, `BP_ItemDetails`, `BP_MenuButton`, `BP_PartyUI`, `BP_PauseMenu`, `BP_QuestDetails`, `BP_SaveButton`, `BP_SkillDetails`, `BP_UnitButton`, `BP_UnitDetails`, `BP_UnitDetailsSummary`, `BP_UnitPartyDetails`, `BP_WearEquipmentUI` |

`WBP_MainMenu`, integration `BP_MelodiaBattleUI`, and stock `BP_BattleUI` are tracked.
`WBP_MenuButton` and `Melodia/VFX/EffectTypes/*` are not tracked at this baseline; source
control inclusion requires the owner's scoped `.gitignore` decision before landing them.

- **Issue #51 — long-chain persistence.** Outfit → Starskiff → encounter → rhythm → Convergence →
  reward → save → quit → relaunch → load → load again, with no duplication. Refresh from current
  `main`; do not merge stale PR #54 wholesale. Audit `RestoreNarrativeRecord*` for partial mutation,
  add repeat-load equality tests, and separate durable vs derived Starskiff/Convergence state before
  any save schema v6.
- **Packaged golden run** of `specs/p0/core_p0_dream_golden_run.v1.json` — not certified.
- **Allowlist is relaxed in editor builds** (`bRelaxedAllowlistInEditor`); run one pass with it off
  before any packaged demo.
- **Owner decision:** retire vestigial `melodiaBattleUI` / `MelodiaUI` vars on `BP_BattleController`.
- **Audio reactivity gap:** `M_Master_Toon_Universal_Alpha` has none of the 14 `Cymatic_*`/`Audio*`
  params, so its 109 instances (incl. Melusina `SW_Dress_P01..P48`) cannot react.
- **Sea Above look-dev:** `W_Glacier_Rock` is a near-black Gaea export (re-export); an unidentified
  writer rewrites `MI_Glacier_Landscape_Layered` weights. Pin Ultra Dynamic Sky before trusting any A/B
  capture on `LV_SeaAbove_Prototype`. Measured 2026-09-12: 11 bounded PCG volumes (largest 83×15×17 m),
  not four giant ones. `PCG_East_AtlantisGrove2` is an exact duplicate of `PCG_East_AtlantisGrove`
  (same transform, seed 42, all 193 instance transforms) — delete it. PCG regenerate + save leaves the
  previous generation's spawned actors on disk: `ResonanceCathedral Music Node0–11` exists three times,
  and the 09-01 set is referenced by no volume on `main` or any branch.
- **Choral Sheep — still owed:** foot-slide check against the ABP thresholds 10/5 and 120/100 at real
  frame rate (the background editor ticks PIE at ~3 fps — test in the foreground or under `slomo`);
  lit-level REST → ROOT_C → hit → REST capture; plug the new UVPackmaster normal maps into
  `MI_ChoralSheep_Body` (they now land on UV0 via `deploy/blender/choral_sheep_export_bakeuv.py`).
  `Retarget/SK_MrSheep` is the retarget source at ~100× scale; never place it in a level.
- **VFX / materials still owed:** Package A/B docs are organized on `main`, but docs do not equal saved editor state. Owner Ctrl+S may still be owed for SurrealFabric/flipbook and Brushify packages; Enchanted Vehicles wrappers are ready but mesh material slots still reference stock masters. Melusina sprite sizes 0.03–0.10 still need the owner look call; run the remaining `VFX/Systems/**` sort/shadow sweep. The golden-run spec still names `/Game/L_Melodia_Dreamstate`, which does not exist.
- **Eyewear cleanup resolved:** #194 and #205 are closed unmerged; the scoped editorial salvage landed through #225. Do not reopen their protected `.gitignore` / `Saved/` payloads.
- **Historical cleanup branch guard:** `cleanup/pbr-twin-landing-2026-09-10` still contains the old docs-collapse resurrection, but PR #230 is closed unmerged. Keep the branch only as provenance; never use it as current status, repo health, or a wholesale merge source. Promote named unique work through scoped PRs only.

---

### P0 closeout — plan of record, 2026-09-16

**Every gate reads PASS, but the proof is old.** Latest ledger rows (`Saved/gate_ledger.json`,
latest row per id) are all `pass` and `melodia_system_golden_run_preflight` returns `ready`,
yet `runtime` is 08-13, `save_load` / `repeat_consume` 08-14, `package_launch` 09-03 — before
three weeks of `L_MelusinaMorning` and Melusina rig work. **Issue #51 is the only open P0 item**;
draft PR #144 (refuse incompatible `FMelodiaNarrativeRecord` candidates without resetting the
valid record, plus atomicity and repeat-restore tests) is its implementation. Stale PR #54 stays
closed. Starskiff persistence decision (from #144): persist `flag.sea_above.starskiff_ready` and
the spawn tag only — never `bBoarded`, possession or transform. Boarding contract live proof:
`Saved/Audit/starskiff_boarding_proof_2026-09-10.json`.

**Automation, 2026-09-16 (headless `UnrealEditor-Cmd`, `Melodia.` prefix): 97/99 pass.**
Report: `Saved/Audit/p0_closeout_2026-09-16/automation/`.
- `Melodia.Roguelike.Functional.ThreeStagePhysicalRoute` fails headless only: it expects the
  `Using CommonUI without a CommonGameViewportClient` warning, which needs a real viewport.
- `Melodia.Roguelike.Functional.TwentyFiveGenerationSoak` additionally raised
  `Accessed None ... Title` in `BP_SkillUseDialogue` and a `RecoverableFailure` at
  `RD_MelodiaGrove_V1` **with the uncommitted 2026-09-15 `BP_BattleUI` dead-island cut in place**.
  The same test with the committed `BP_BattleUI` failed only on the viewport expectation. That
  cut is therefore held back uncommitted (rollback: `Docs/Audits/ROLLBACK_BP_BattleUI_2026-09-15.json`).
- Do not run automation through Monolith `editor_query run_automation_tests`: latent tests trip
  `Assertion failed: LatentCommands.IsEmpty()` and crash the editor. Use `UnrealEditor-Cmd`.

**PIE, 2026-09-16 (rebuilt editor, `L_MelusinaMorning`, 18 s):** `ok` — 0 Blueprint runtime
errors, 0 Accessed None, 0 fatals; live pawn `BP_MelusinaJRPGCharacter` on `ABP_Melusina_Current`;
13/14 frames valid. `BP_MelusinaJRPGCharacter` already carries #210's stencil 4 (verified live).
On-screen engine warning: **eye-adaptation exposure −5.4 is outside Lumen's safe range [−4, 16]**
("cached lighting … going to be clipped", `r.EyeAdaptation.CachedLightingPreExposure`) — a look
issue for the Morning PPV/exposure, not a P0 blocker. Stills: `Docs/Evidence/P0_CLOSEOUT_2026-09-16/`.

**Phases**
0. *Land on `main`, editor closed.* Branch reconciled with its origin copy and `main` merged in
   (2026-09-16). Binary picks: frozen PPV MIs kept from the 09-15 lock-in; Choral Sheep
   `A_Sheep_Death/Jump/WalkSlow` + `SK_MrSheep_Skeleton` taken from #209 (the owner's 09-16 save of
   the other sheep takes already matched #209 byte-for-byte); `BP_MelusinaJRPGCharacter` kept from
   the 09-16 save, so #210's `CharacterMesh0` custom-depth **stencil 4** must be re-applied in the
   editor. Then PR to `main`, and rebuild `BS_GodFileEditor` with UBT while the editor is closed.
1. *#51 code.* Rebase #144 onto `main`, headless-test the `Melodia.Integration` suites, merge on
   green. Proposed scope cut: #144 + the restart and packaged proofs are the closure; schema v6 and
   the stale-write guard move to P1 unless an audit finds a real race.
2. *Re-prove on current `main`.* Restart proof (save → quit → relaunch → load, real input) and a
   packaged proof (cook to `G:\melodia_packages\`, omit `-map=`); append fresh ledger rows.
3. *Close.* Refresh this file, run the surviving project/Git health checks (`python Tools/project_health.py` and `python Tools/git_ok.py`), then close #51 with receipts.

**PR cleanup, 2026-09-16:** #215 (VFX flipbook closure) refreshed onto `main`, static + LFS gates
green, merged as `88248226` — all 73 `Content/_PROJECT/VFX` files are LFS-backed on the remote.
#205 (eyewear editorial) is superseded by #223: against current `main` only `eyewear.py` (its later
09-12 19:30 version) and 8 `Tools/eyewear_verify` probes were still unique; close #205 when #223 lands.
The 09-12..09-16 working-branch content lands through #224 (filtered: #181-deleted docs, career/school
files, plan/receipt notes, `DefaultEngine.ini` and 77 unreviewed sweep deletions kept out).

**Not P0:** `Morning_Bed` on `_Scratch/MI_GemstoneTest_Inst`; 13 house meshes on
`M_Material_003`; three of four `PPV_NikkiDream` blendables at weight 0 (intent unconfirmed);
a second, differently-shaped 18-node BellTree generation under `Morning_Dell_Banks`; shirt
dangle bones; `Content/Textures/` allowlist. Reference:
`Docs/MELUSINA_WARDROBE_PHYSICS_PIPELINE_2026-09-15.md`.

**Held for owner sign-off:** the uncommitted `Config/DefaultEngine.ini` edit (drops the dead
`DefaultFeatureAntiAliasing=1`; live `r.AntiAliasingMethod=1` unchanged) — the pre-commit hook
requires `SKIP_PROTECTION=1`. C: had ~17 GB free on 2026-09-16 and LFS briefly failed with
"not enough space"; cook to G:.

## 4. Owner queue — now

**Next session (WC baseline is on `main`):** OSC ingest is live-proven on the open WIP editor. Remaining: AE JSX with Unreal closed, then editor cutover to the clean tree when this session ends. Do not checkout `main` on dirty `BS_GodFile`. Horizon Eater is later, not this queue.

**Thesis:** Creature → Motif → Harmony → World. **Semester (Humber Fall 2026):** First Dream is the
stable technical proof (protect and polish only). Shorewake Calling is the semester artwork.
Choral Sheep is the capstone lane.

1. **Editor cutover.** Point the next Unreal session at the clean checkout (`C:/EnvironmentPortfolio/_wt_morning_closeout` now tracking `main`, or a fresh `origin/main` worktree). One editor, one Monolith `:9316`. Do **not** `git checkout main` inside `C:/EnvironmentPortfolio/BS_GodFile` while the 205-file WIP tree is dirty. Leave `wip/pre-restart-working-tree-2026-09-19` as recovery; uncommitted files stay uncommitted. Copy UltraDynamicSky / Humber / session VFX **outside** git if they must be kept — reset of the old folder is a named later step.
2. **OSC ingest PIE. LIVE PROVEN 2026-09-20 21:58** on the open WIP uproject (`UnrealEditor-BS_GodFile.dll` 3,232,768 bytes, 17:48 `RecvFrom`). GetCurrentState bar 0/energy 0.0 → bar 10/energy 0.92 after `,isifsfi` / `,ii` to UDP `:9000`. Do not open a second Unreal. Do not UBT while the editor is open. Do not rebuild the TD scene. Do not revive `Recv()`. Closeout 21:32 DLL (3,233,280 bytes) still waits on a later cutover.
3. **AE JSX.** Run `C:/MelodiaTouchDesigner/ae/ship_queue_creature_motif_harmony_world.jsx` only after Unreal is closed (GPU3). 8s beat is at `Saved/Audit/AE/ship_queue_beat_8s/Melodia_ShipQueue_Beat_8s.mp4`. Then promote to the site.
4. **Horizon Eater later.** Specs already target `LV_SeaAbove_Prototype`, not Morning. New chapter = new `recipes/*.v1.json` + compile + new `WC_*_Field` / `DT_*` on that level. Morning Brushify field is frozen `--skip-scaffold` regression. No `HE_Filter_*` on `L_MelusinaMorning`. No second compiler. No unfreeze Morning PPV.

Fleece REST vs HIT stills (`Saved/Audit/Screens/ship_queue_fleece_{REST,HIT}_v2_clean.png`) are captured; owner pixel-judge against Board 06 remains. Then: 3–5 minute Shorewake route (`Chapters/02_shorewake_calling/`) → Issue #51. **After those capstone-facing closures**, Issue #221 (`World Engine Slice — persistent compiled movement`) is the next major procedural-worldbuilding milestone; do not pull it ahead of graded proof.

**Task filter:** a task must produce a graded Humber deliverable, a visible portfolio improvement,
or remove a real blocker to one of those (`Docs/Semester/FALL_2026_ACADEMIC_MATRIX.md`).

**Not now:** git archaeology, new frameworks or second authorities, website redesign (showcase soft
freeze since 2026-09-07), or research sweeps. Keep status changes in this file and do not create
another status, handoff, plan, receipt, or session-note document. Oracle / Thirteenth Note
(`Docs/Strategy/ORACLE_*`) is a gated end-of-semester stretch.

---

## 5. How progress is measured

Playable minutes and captured proof — not gates, commits, or documents. As of 2026-09-10 the
authored QuillScript is 16 `.qsc` files, about 500 lines, several of them smoke tests. A session
counts if it adds playable or presentable minutes, or removes a real blocker.

---

## 6. Where things are

| What | Where |
|---|---|
| Game (this repo, **private**, no licence file) | `fromage3900/MelodiaMelusinaV2`, local `C:/EnvironmentPortfolio/BS_GodFile` |
| Website (**public** — serves GitHub Pages; owner decision 2026-09-12) | `fromage3900/my-site` |
| TouchDesigner / AE (private) | `fromage3900/MelodiaTouchDesigner`, `C:/MelodiaTouchDesigner/td/grandmaster_melodia/` |
| AI token treasury (revenue sidecar) | my-site `tools/fromage-webgl-kit/TREASURY_LEDGER.json` — 0 entries, first gate 0/5; never displaces the capstone |
| Accessory / WebGL website lane (isolated) | [`Website/fromage-webgl-kit/`](Website/fromage-webgl-kit/) — floral atelier + commerce embed, DCC `KHR_materials_variants` GLBs. Not the recruiter site. Cloud cannot push `my-site` (403). |
| `C:/EnvironmentPortfolio/` | workspace folder only; its root Git repo is retired |

**The game repo is private; `my-site` is public.** Non-sensitive school/career planning may live only under the explicitly scoped `Humber_FinalYear_Prep/` namespace when the owner wants Git-backed agent access. Never commit student numbers, private account addresses, credentials/tokens, identity or verification documents, payment data, account-recovery data, or client-confidential material. Keep `my-site` recruiter-safe and public-facing only.

- **Route maps:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` →
  `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` →
  `/Game/EnvSandbox/Environments/L_KaleidoNave`; menu `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu`.
- **Systems test level:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` — additive only.
- **Workstations:** Humber lab = primary interactive; home PC = render/bake worker
  (`deploy/render_worker.ps1`); ASUS laptop = auxiliary. `main` is the shared baseline.
  `collab/laptop/longterm` is the laptop Blender/GN lane — never wholesale-merge or delete it
  (`Docs/Production/BRANCH_WORKSTATION_POLICY.md`).
- **Packaging:** cook to `G:` (C: lacks space). `Config/DefaultGame.ini` `MapsToCook` is correct —
  omit `-map=`.
- **Git health:** `python Tools/git_ok.py` — if it prints OK, Git is not the task.
- **Art references:** `Docs/Art/VISUAL_REFERENCE_INDEX.md`. Melusina House GN:
  `MELUSINA_HOUSE_GN_START_HERE.md`.

---

## 7. Traps that keep costing sessions

- **Stale DLL.** Compare `Binaries/Win64/UnrealEditor-BS_GodFile.dll` mtime against the source
  before trusting any PIE result.
- **One editor, one MCP writer** (Monolith port 9316). A second editor logs to
  `Saved/Logs/BS_GodFile_2.log`.
- **Background agents.** OpenCode in Rider (runs a git MCP server), Hermes, and the Melodia
  scheduled tasks (disabled 2026-09-10) have switched branches and committed mid-merge. Check
  before any editor or git work.
- **Material instance writes** need `update_material_instance()` to reach the renderer.
- **Never `load_level` straight after stopping PIE** — teardown is async and crashes the editor.
- **Codex desktop drives the editor too.** `ChatGPT.exe` → `codex.exe` holds its own
  `monolith_proxy.exe`, loads maps, saves, runs `Build.bat BS_GodFileEditor` against an open editor and
  restarts it. `ListAgents`/`SendMessage` do not reach it. Check `monolith_proxy.exe` parents and a
  running `UnrealBuildTool.dll` before closing, rebuilding or PIE-driving.
- **Read-only content files come from Git LFS locking.** `.gitattributes` marks `*.uasset`, `*.umap`,
  `*.blend`, `*.fbx` and 31 more patterns `lockable`, so every checkout, reset or branch switch makes
  them read-only and editor saves fail with "because the file is read-only!". Nobody uses LFS locks
  (`locksverify false`). In each clone or worktree run `git config lfs.setlockablereadonly false`, then
  clear the flag once: `Get-ChildItem Content -Recurse -File | ? IsReadOnly | % { $_.IsReadOnly = $false }`.
- **Monolith `run_python` cannot sleep** — `time.sleep` is intercepted and PCG `generate()` is async, so
  instance counts read in the same call race generation.
- **Headless Blender hangs on user add-ons** — pass `--factory-startup` for `-b` inspection/bake runs.

Stale-agent damage classes (read these before any WC / Jev / Blender / git work):

- **Collapsed docs.** Never resurrect paths deleted in `08a608bc`. CI: `Tools/guard_collapsed_paths.py`. Never wholesale-merge `cleanup/pbr-twin-landing-2026-09-10`. Recover old docs with `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).
- **Bedroom / Sphere3D meadow.** Live Morning field is flowers on `BrushifyIsland_*` only; dressing on `WC_EscherWalk_*` plus island skirts; bedroom keepout in `recipes/morning_rainbow_bloom.v1.json`. Do not plant `SM_classic_arch_*`, `Sphere3D`, `WC_DellFloor`, or invent a second meadow. Older WC-contract bedroom-floor numbers are historical probe notes, not the live recipe.
- **Second authorities.** No second World Compiler, MPC writer, Niagara framework, battle manager, phrase bus, Jev, or Monolith.
- **MPC/PPV writes** to “fix” muted hue or lookdev. Hue-reveal proof is PIE wind, not a writer. Frozen PPV stays frozen.
- **Dirty-tree dump.** Isolated PRs only. Morning closeout is **on `main`** (PR #249). Park Frozen PPV, MPCs, `DefaultEngine.ini`, EnvSandbox dumps, and Humber. Never dump `C:/EnvironmentPortfolio/BS_GodFile` wip onto git. Do not `git checkout main` onto that dirty tree.
- **Horizon Eater later, not a rebuild.** Specs (`specs/horizon_eater/HORIZON_EATER_DESIGN.md`, `Docs/Monoliths/P3_HORIZON_EATER_PLAN_2026-08-29.md`) target `LV_SeaAbove_Prototype`, not Morning. There is no `recipes/horizon_eater_*.json`. Morning recipe + `WC_morning_rainbow_bloom_Field` + `PCG_WorldCompiler_PointField` + `DT_morning_rainbow_bloom_Points` are **read-only regression**; maintenance uses `--skip-scaffold` only. New place = new `world_recipe.v1` + `python Tools/world_compiler.py compile` + same UE driver + a **new** `WC_*_Field` / `DT_*` on the new level. `PCG_HorizonEater_FilterFlow`, Oceanology SLW, fog/LOD, and `Content/Python/add_horizon_eater_mpc_params.py` stay presentation / one-time MPC authoring — not a second World Compiler. Runtime HorizonEat still goes through `UMelodiaAudioReactivePresentationSubsystem`. Never call that script from `world_compiler*.py`. Do not spawn `HE_Filter_*` debug meshes on `L_MelusinaMorning`. Do not unfreeze Morning PPV to “see” the eater.
- **Blender / G: junctions.** Do not robocopy, junction, or overwrite `harp_bow_pipeline`. Open `C:\EnvironmentPortfolio\MELUSINABACKUPBECAUSEAIAGENTSARERETARDED.blend` (Sep 5, verified) or the v22 recovered stage. Sep 8–12 staged set restored 2026-09-20 (21/21 `verify_blend.py`; Rev02 opens + renders — see the recovery bullet up top). Headless Blender: `--factory-startup`.
- **Jev confusion.** Jev (`Tools/listening_field/jev_director.py`) is a director over allowlisted sheep/world/`layout_seed` options. It does not drive UE, compile meadows, or MCP-move actors. `recipes/jev_showcase_bloom.v1.json` is a World Compiler recipe whose name is unrelated.
- **Ghost spec / wrong phrase bridge.** Durable spec is [`Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md`](Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md), restored from the Python schemas. `Content/Python/resonant_world_phrase_bridge.py` is MIDI ecology, not Jev.
- **gitignore `Tools/*` swallowing live lanes.** `Tools/listening_field/`, `Tools/phrase_bridge/`, and `Tools/live_source/` must stay un-ignored (`!Tools/<dir>/` + `!Tools/<dir>/**`). That swallow is why Jev work appeared to “get deleted from git” — it was never tracked. Also keep `!Tools/guard_collapsed_paths.py` and `!Tools/test_guard_collapsed_paths.py`. Do not `git add` Frozen/MPC/EnvSandbox dumps to compensate.
- **Skip `scene_context_cycle`.** Any WC / PCG / Monolith spatial edit requires `scene_context_cycle.begin()` before the first mutation and `end()` after, in the already-open editor. Tools: `Content/Python/scene_context_snapshot.py`, `Content/Python/scene_context_cycle.py`. One editor, Monolith `127.0.0.1:9316` only. Packets under `Saved/Audit/SceneContext/` are ephemeral evidence, not status.
- **UBT while the editor is open / `Recv()` ingest.** Closed-editor builds only. `Recv()` on unconnected UDP kept GetCurrentState at bar 0 / energy 0.0; that is the retired bug, not current debt. Live ingest is **`RecvFrom`** (LIVE PROVEN 2026-09-20). Compare `UnrealEditor-BS_GodFile.dll` mtime before trusting PIE. Do not revive `Recv()`.
- **Retired rainbow_*.py.** `Content/Python/rainbow_*.py` stay gone. Morning scatter is `Tools/world_compiler.py` + `recipes/morning_rainbow_bloom.v1.json` only.

---

## 8. Keeping this healthy

**Docs.** This replaces the front-door contradiction checker: one status document cannot contradict
itself.

- A change that alters project status updates this file **in the same PR** (PR template checkbox).
- No new handoff, plan, receipt, scorecard, or session-note files. That narrative belongs in the
  commit or PR body, where it is already dated and attributed.
- A new doc is only for durable reference — pipeline, contract, spec, runbook, bible, research.
  Name it for what it teaches, not for the day it was written.
- Monthly: re-read §2 and §3 against the current build. Delete any claim you cannot point at
  evidence for. Nothing is lost — `git show 7d271c15:<path>`, tag `docs-precollapse-2026-09-10`.

**Git.** `python Tools/git_ok.py` first; if it prints OK, git is not the task. One branch per
reason, named per `CONTRIBUTING.md`. Never let a background agent commit on your behalf — check for
OpenCode (Rider) and Hermes before editor or git work.

**CI.** The doc-policing steps are gone: `repo_governance_guard.py` and `front_door_health.py`
existed to cross-check front-door docs against each other, which a single document cannot fail. PR
CI still runs the protected-asset guard, the echo manifest, the offline contract suites, and the
health scorecard.

**Hygiene.** This repo is private and `my-site` is public. Personal, school, career, and client
documents live in local-only `C:/EnvironmentPortfolio/_offgame/` and never in either repo.

**Weekly, ten minutes:** is §2 still true, is §4 still what you are actually doing, does `git_ok`
pass, and did anything get written this week that should have been an edit to this file?
