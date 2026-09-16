# Melodia Melusina — Current State

**This is the only status document.** If any other file states what works, what is open, or what
to do next, that file is wrong: fix this one instead. Update it in the same commit as the change it
describes. Handoffs, plans, receipts and session notes go in the commit or PR message, never in a
new file.

**Updated:** 2026-09-16 · **Engine:** UE 5.8 · Blender 5.2 LTS · C++20 · Python 3.11
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
| Rhythm grade affects authoritative JRPG combat | **LIVE PROVEN** - `FMelodiaRhythmGradeBoundaryTest`, the `rhython_grade_to_result` ledger row, and `MelodiaRhythmCombatSubsystem` verify Q/W/O/P grade data reaches the stock skill damage path | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp`, authored `UMelodiaRhythmSkillDefinition` / skill data | New rhythm skills, attacks, patterns, grade-driven damage, healing or resource effects | A second damage formula, rhythm combat authority, or bespoke boss combat framework |
| Wardrobe, traversal and gameplay capability hooks | **LIVE PROVEN + RESTART PROVEN baseline** - `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, [`P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`](Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md), and the restart slot proof pass | `Plugins/MelodiaWardrobe/`, `UMelodiaWardrobeSubsystem`, `MelodiaTraversalComponent`, wardrobe catalog manifests | Outfit abilities, traversal gates, creature/world relationships and battle/rhythm affordances | A new outfit inventory, equipment owner, traversal capability registry, or cosmetic-only workaround |
| Music-as-key world unlock | **LIVE PROVEN (scoped)** - the coinsheet receipt records one idempotent Piano phrase -> typed world result -> visible route; [`music_world_key_real_input_2026-08-31.json`](Docs/Evidence/music_world_key_real_input_2026-08-31.json) and [`P0_REAL_INPUT_PROBE_2026-09-09.json`](Docs/Evidence/P0_REAL_INPUT_PROBE_2026-09-09.json) provide route/input evidence | `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_MusicManager.uasset`, `MelodiaMusicClockSubsystem`, Quill world-result path, `Content/Python/build_pcg_piano.py` | Musical world puzzles, phrase-locked routes, keys, shrines and side-quest progression | A new puzzle framework, second music clock, or one-off door/route authority |
| Choral Sheep companion and Harmonize | **LIVE PROVEN (PIE behavior); visual fleece response still owed** - [`CHORAL_SHEEP_MORNING_PROBE_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_MORNING_PROBE_2026-09-13.json), [`CHORAL_SHEEP_ABP_LOCOMOTION_PROOF_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_ABP_LOCOMOTION_PROOF_2026-09-13.json), and [`CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json) plus current Sheep assets prove definition -> begin -> ramp -> decay and locomotion; the receipts explicitly leave the lit fleece capture open | `Content/Melodia/Companions/ChoralSheep/`, `BP_ChoralSheep`, `DA_ChoralSheepDefinition`, `MelodiaCompanionComponent`, `TryBeginHarmonize` | Creature Episodes, companion abilities, creature reactions and harmony moments | A new companion framework, ad-hoc creature state, or rig reopening without a current defect |
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
| Nikki-derived toon/material path | **PRESENT / ASSET + SOURCE PROVEN; scoped live use** - `M_Master_Toon_Character.uasset` and `M_Master_Toon_Universal.uasset` are tracked; Sheep proof binds `MI_ChoralSheep_Body` to the approved character master with Chladni as a child | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Character.uasset`, `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset`, `Content/Melodia/Companions/ChoralSheep/`, [`CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json`](Docs/Evidence/CHORAL_SHEEP_RETARGET_DEFORMATION_PROOF_2026-09-13.json) | Author new hero, creature, outfit and biome material variants while keeping the current toon identity | A new master-material architecture or replacing the Nikki-derived base with a parallel shader |
| Audio-reactive presentation and cymatics driver | **SOURCE + SCOPED LIVE PROVEN** - the audio palette writer and read-only Cymatics runtime are scoped-live proven; the dedicated driver writer is source/asset proven and remains a separate material contract. Sea Above pulse/mode/amplitude automation is `PASS` with one audio writer | `MelodiaAudioReactivePresentationSubsystem.*`, `MelodiaCymaticsSubsystem.*`, `MelodiaCymaticsWriterSubsystem.*`, `Content/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.uasset`, `Content/Melodia/Cymatics/MPC_Cymatics_Driver.uasset`, `Docs/Evidence/P0_SEA_ABOVE_CYMATICS_LIVE_2026-09-01.json` | Audio-reactive materials, Chladni response, beat/mode/tension-driven water, Niagara and surface presentation | A second audio writer, a second MPC contract, or a new master shader for each variant |
| Chladni/cymatic shader automation | **PRESENT / SOURCE PROVEN; consumer-specific visual proof varies** - `Source/MelodiaShader/Shaders/` contains the shader module; Chladni sampling and material automation scripts are present; use the current PPV/material receipts for visual proof | `Source/MelodiaShader/Shaders/`, `Content/Python/assign_toon_profiles.py`, existing MPC contracts | Reactive shader/material variants and automated parameter application within the frozen identity | Hand-guessed parameters, per-widget/per-material constants, or a new universal master |
| Frozen PPV, Niagara and flipbook presentation stack | **OWNER-APPROVED / LIVE PROVEN scoped** - [`PPV_STENCIL_PIE_2026-09-13.json`](Docs/Evidence/PPV_STENCIL_PIE_2026-09-13.json) and the current identity record in this file prove the frozen visual boundary; canonical Niagara effect types and companion VFX assets are tracked, while visual work remains asset-specific | Frozen `PPV_NikkiDream` stack, `Content/Melodia/VFX/EffectTypes/ET_Melodia_CharacterFX.uasset`, `Content/Melodia/Companions/ChoralSheep/VFX/`, `Tools/Houdini/sea_above_reef/shorewake_animated_flipbook.py`, `Content/Python/import_flipbooks.py`, `UMelodiaAudioReactivePresentationSubsystem` | Storybook identity, audio-reactive VFX, canonical Niagara effects, flipbook shimmer and polished captures | A new post-process identity, duplicate Niagara framework, or a “fancy VFX” system outside the canonical stack |

#### UI authoring

| Capability | Status / evidence level | Canonical entry points | What it enables creatively | Use this instead of rebuilding |
|---|---|---|---|---|
| Melodia UI artist skill and existing Quill UI chain | **PRESENT / SOURCE-TOOL PROVEN; audit workflow established** - both agent skill copies define the token SSOT, Quill widgets, audit and editor apply workflow; current state records the read-only inventory of 144 widget Blueprints / 955 styled widgets | [`.claude/skills/melodia-ui-artist/SKILL.md`](.claude/skills/melodia-ui-artist/SKILL.md), [`.agents/skills/melodia-ui-artist/SKILL.md`](.agents/skills/melodia-ui-artist/SKILL.md), `melodia-design-system/tokens.json`, [`ui_style_audit.py`](Tools/ui_style_audit.py), `Content/Melodia/UI/Quill/`, `Content/Python/assign_melodia_quill_presentation.py` | UI polish, new dialogue/selection screens and authored screens that match the current identity | A new widget framework, manual style guesses, or hand-editing `.uasset`; load the skill first |

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

### WHAT TO REACH FOR

| User asks for... | Reach for... |
|---|---|
| New boss | Quill + Phoenix/JRPG + existing rhythm seam + authored skill/data |
| Side quest | Chapter scaffold + Quill + stable IDs + existing reward/save owners |
| New rhythm ability | Existing rhythm execution + JRPG Skill/command path |
| Musical biome | Cymatics -> Resonance/PCG data -> UE PCG + material/Niagara consumers; remember the broader World Field Bus is scaffolded |
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

### Stabilization — 2026-09-13

| Item | Source / evidence | Remaining owner decision or proof |
|---|---|---|
| Branch archaeology | `Docs/Evidence/BRANCH_LEDGER_2026-09-13.json` inventories both remotes and all four open V2 PRs. `Tools/guard_collapsed_paths.py` blocks re-additions deleted by `08a608bc`, including renames; runs on every PR. | Approve the ledger's close/archive candidates; reconcile unique files only. No PR or remote branch closed by this pass. #201 was superseded by merged #213 (owner report). |
| Identity canon | `UMelodiaIntegrationConfig` now exposes one runtime-owned core identity record: P0 player, Choral Sheep definition, hero stencil 4, ordered frozen PPV stack with weights, and character/ambient Niagara effect types. `Melodia.Wiring.CoreIdentity.Canon` reads that same config and resolves every reference. | Owner approved the narrow asset closure: 52 previously ignored packages (68.76 MiB), including the seven canonical Frozen PPV assets, `ET_Melodia_CharacterFX`, all recursive dependencies, and the three WaveHarp_R07 meshes. Closed-editor UE 5.8 Development build passed all 460 actions. Never substitute the unfrozen originals. |
| Chapter reuse | `Tools/scaffold_chapter.py`, `Chapters/_template/{quill,maps,encounters,rewards}`, and four-beat `03_tide_listening` source. Generator validates gated IDs against the actual DA before writing; numbered chapter folders are automatically tested. | Full QSC contract FAILS on existing SkiffDeparture `quest.shorewake.passage`, `flag.shorewake.passage`, `reward.skiff_passage`. Resolve those IDs and reward binding through the canonical DA in the editor; import the example and prove both choices/revisit/save-load in `MelodiaIntegrationMap`. Scaffold regression passes; no PIE claim. |
| UI staleness | Read-only `melodia-ui-artist` audit: rhythm HUD and four Quill widgets have palette colours. P0 candidates: `BP_MelodiaBattleUI` RhythmGradeText/SongPickLabel white; stock `BP_BattleUI` KeyboardLegend `#F2D69E`; `WBP_MainMenu` near-palette text; `WBP_MenuButton` label `#F2D69E`. | Editor reopened externally during audit; ownership pending, no widgets changed. Remaining candidates include `BP_MelodiaDefeatDialogue` near-black text, `BP_MelodiaVictoryDialogue` zero-alpha text (check runtime bindings), Foundation parchment/button styling. White image tints and transparent shadows are not automatically defects. |
| G: saved-state mirror | `Tools/mirror_saved_project.ps1` defaults to dry-run; scoped `/MIR`, destination/junction checks, cache/binary/Blender-autosave exclusions. Includes Content (Frozen + Cinematics), Config, Source, Plugins, Saved/Audit, Chapters, specs, Tools and design tokens. Dry logs: `%TEMP%/melodia-mirror-20260913/`. | Proposed destination `G:/BS_GodFile_Mirror/20260913`; initial dry run 119.75 GiB / 55,549 files plus project descriptor, zero failures/extras. Real run awaits owner approval and a saved, closed, stable source. This mirrors the saved local tree, including uncommitted assets; it is not a claim that local tree equals main. |

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
- **VFX / materials still owed:** Melusina sprite sizes 0.03–0.10 look metre-scale (owner look call);
  sort/shadow sweep on the remaining `VFX/Systems/**` sprite systems; golden-run spec names
  `/Game/L_Melodia_Dreamstate`, which does not exist.
- **Eyewear PRs #205 / #194** each touch protected `.gitignore` and add 16 files under `Saved/`; the
  −1,835 lines are a `Tools/registry_baseline.json` regeneration. Owner review before merge.
- **`cleanup/pbr-twin-landing-2026-09-10` resurrects the docs collapse.** Its snapshot `673a5ddf`
  re-adds 830 of the 840 files `08a608bc` deleted, including `Docs/Career`. Never merge it wholesale;
  promote its real work (MK39 skiff GN, Sea Above external actors, HUD tokens) in scoped PRs.
  `Docs/Career` also sits on ~37 remote branches and in `main`'s history; purging it needs an
  owner-approved history rewrite.

---

## 4. Owner queue — now

**Thesis:** Creature → Motif → Harmony → World. **Semester (Humber Fall 2026):** First Dream is the
stable technical proof (protect and polish only). Shorewake Calling is the semester artwork.
Choral Sheep is the capstone lane.

1. **Choral Sheep UE proof.** Verify deformation; bind one C-root fleece response on the approved
   Nikki-derived Cymatics path (`MI_ChoralSheep_Body` → `M_Master_Toon_Character`, Chladni as a
   child, not a replacement shader); capture REST → ROOT_C → hit → REST. Visual lock: Board 06 +
   the two WebPs in `Docs/References/VisualBoards/2026-09-08/ChoralSheep/`. Context:
   `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`.
2. **UE ↔ TD proof.** One real OSC `:9000` and/or Spout connection. Do not rebuild the TD scene.
3. **One 5–10 s AE sequence** — Creature → Motif → Harmony → World. Only then promote to the site.

Then: the 3–5 minute playable Shorewake route (`Chapters/02_shorewake_calling/`), then Issue #51.

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
| Accessory viewer twins (website lane) | Transfer pack [`Docs/Strategy/webgl-kit-viewer-twins-2026-09-16/`](Docs/Strategy/webgl-kit-viewer-twins-2026-09-16/) — Google `<model-viewer>` + Babylon Viewer on the same eyewear `catalog.js`. Cloud cannot push `my-site` (403). Apply there with `git am` the included patch. Not a recruiter-site redesign. |
| `C:/EnvironmentPortfolio/` | workspace folder only; its root Git repo is retired |

**The game repo is private; `my-site` is public.** Never commit personal, school, career, or client documents to either.

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
