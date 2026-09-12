# HoudiniEngine Deep Intake — Worldgen Quick Wins for MelodiaMelusina

**Date:** 2026-08-28
**Author:** build agent (deep intake)
**Status:** research / analysis only — no edits to gameplay code

---

## 1. What HoudiniEngine is (plugin inventory)

- **SideFX Houdini Engine for UE 5.8** — `Plugins/HoudiniEngine`
- **Version:** 3.0 / H22.0.368 (`HoudiniEngine.uplugin`)
- **Modules:**
  - `HoudiniEngine` (Editor, Default)
  - `HoudiniEngineEditor` (Editor, PostEngineInit)
  - `HoudiniEngineRuntime` (Runtime, Default) ← this is the one that ships
- **Dependency:** `PCG` plugin enabled by default (UE 5.8 Procedural Content Generation)
- **Shipping posture:** `BS_GodFile.uproject` currently has `HoudiniEngine` enabled (the
  `f89fccd5` whole-file churn). Confirm with the owner whether it stays enabled in
  packaged builds — it is Editor+Runtime, so it *can* ship, but it is a non-trivial
  binary. The BOM + reindent on the `.uproject` should be reverted regardless.

### Runtime workhorse classes (what actually ships)
| Class | What it does |
|---|---|
| `UHoudiniAssetComponent` | Attaches an HDA to an actor; bakes its outputs (mesh, landscape, foliage, volume) into the level at runtime. **The single most important class for quick wins.** |
| `UHoudiniAssetActor` | Spawns an HDA as a world actor |
| `UHoudiniAssetBlueprintComponent` | Blueprint-accessible wrapper of `UHoudiniAssetComponent` |
| `UHoudiniInput` | Drives HDA parameters at runtime (world / landscape / geo / curve / object inputs) |
| `UHoudiniHandleComponent` | Manipulates HDA handles (transform, pivot) at runtime |
| `UHoudiniNodeSyncComponent` | KineFX skeletal-mesh sync (NodeSync path) |
| `UHoudiniAssetStateTypes` | Cook-state machine (never-cook, cooking, cooked, error) |
| `HoudiniCookable` | Marks a UAsset as cookable via Houdini |

### Worldgen-specific runtime capabilities
| Capability | Class / Header | What it means for Melodia |
|---|---|---|
| Landscape baking | `HoudiniBakeLandscape`, `HoudiniLandscapeTranslator`, `HoudiniLandscapeSplineTranslator`, `HoudiniLandscapeRuntimeUtils` | Bake HDA-authored terrain into a UE Landscape at runtime |
| HLOD generation | `HoudiniHLODLayerUtils` | The `L_PCG_Hero_ScaleWorldProof_HLODLayer_Instanced/.Merged.uasset` assets already exist — Houdini can regenerate them |
| World Partition Data Layers | `HoudiniDataLayerUtils` | Switch env layers (day/night/mood) — project already uses `DL_Lighting_Day/Night` |
| Level Instance baking | `HoudiniLevelInstanceUtils`, `HoudiniBakeLevelInstanceUtils` | Bake PCG assemblies (`PCGAssemblies/*`) as Level Instances for streaming |
| Foliage scattering | `HoudiniFoliageTools`, `HoudiniFoliageUtils`, `HoudiniInstancedActorComponent` | Scatter piano-key / crystal / bell motifs from HDA point clouds |
| Mesh / material / parameter | `HoudiniMeshTranslator`, `HoudiniMaterialTranslator`, `HoudiniParameter*` | Runtime variation of HDA inputs (tempo → density, style → palette) |
| CSG / BSP | `HBSPOps`, `HCsgUtils` | Boolean carving of rock / architecture shapes |
| Geometry collection | `HoudiniGeometryCollectionTranslator`, `HoudiniGeoImporter` | Import destructible / fracture meshes |
| Output translation | `HoudiniOutputTranslator` | Route HDA outputs to the right Unreal asset type |
| Asset state | `HoudiniAssetStateTypes`, `HoudiniEngineManager` | Cook / cancel / pause HDA sessions at runtime |

### Input types (how a worldgen HDA receives data)
- **World Input** — world-space placement
- **Landscape Input** — landscape-guided placement
- **Geo Input** — geometry-guided placement
- **Curve Input** — curve-guided instancing (the `copy_to_curve.1.0.hda` example)
- **Object Input** — object-guided placement
- **Instance Input** — instance-based placement

### Pipeline tooling
- **PDG** (Procedural Dependency Graph) — batch worldgen, generate variants, cook in parallel
- **Python API** (`Content/PCG/HoudiniEngineV2/asyncprocessor.py`) — full Python control over HDA cooking, async processing
- **NodeSync** — KineFX skeletal mesh sync (the `KineFXToUnreal.hda` / `UnrealToKineFX.hda` examples)
- **Built-in HDAs:** `rock_generator`, `he_sop_boolean`, `he_sop_curve_instancer`, `he_sop_polyreduce`

---

## 2. How the project's worldgen is already wired

### The music-as-key system (Source-built, not yet live-proven)
```
PCG-spawned piano keys / note nodes
        │
        ▼
APCGHeroMusicGraphHost  ──OnPatternCompleted──►  UMelodiaPCGWaterGameplayBridgeComponent  (LIVE: pattern → water state)
        │                                          UMelodiaPCGNarrativeChallengeBridgeComponent  (SOURCE ONLY: pattern → flag + reward)
        ▼
OnNoteJudged  ──►  UMelodiaRhythmReactivitySubsystem  ──►  material bus / OSC
```

- **`PCGHeroMusic.h`** — complete hero music system: nodes, scoring, `FPCGHeroMusicNoteEvent`, `FPCGHeroMusicScoreState`, `APCGHeroMusicGraphHost` with `OnPatternCompleted` + `OnNoteJudged` multicast delegates
- **`PCGMusicSequencer.h`** — step-grid music: 16 steps × 4 lanes, `APCGMusicStepGrid` with `OnStepActivated`/`OnStepDeactivated`
- **`PCGPianoKeyboard.h`** — piano input path
- **Sub-classes:** `APCGResonanceCathedralHost` (4 stations), `APCGArpeggioBridgeHost` (completion gate), `APCGBellTreeGardenHost` (18 bells × 3 branches), `APCGBellTreeGardenNode` (bell geometry)

### Musical Hero PCG levels (`Content/EnvSandbox/PCG/Musical/Hero`)
| Level | Profile | Status |
|---|---|---|
| `L_PCG_Hero_ArpeggioBridge` | `DA_Hero_ArpeggioBridgeProfile` | Has `APCGArpeggioBridgeHost` + `CompletionGate` |
| `L_PCG_Hero_BellTreeGarden` | `DA_Hero_BellTreeGardenProfile` | `APCGBellTreeGardenHost` |
| `L_PCG_Hero_CrystalHarpGrove` | `DA_Hero_CrystalHarpGroveProfile` | — |
| `L_PCG_Hero_ResonanceCathedral` | `DA_Hero_ResonanceCathedralProfile` | `APCGResonanceCathedralHost` |
| `L_PCG_Hero_XylophoneTrail` | `DA_Hero_XylophoneTrailProfile` | — |
| `L_PCG_Hero_ScaleWorldProof` | — | Has HLOD layer assets |
| `L_PCG_Hero_WaterGameplayProof` | — | Water gameplay proof |

### PCG ecosystem (`Content/PCG/`)
- **Graphs:** Ditch, Forest, FX, Ground, LargeAssembly, SmallAssembly, SplineExample
- **Styles:** Alpine, Baroque, Cosmic, Cyberpunk, Desert, Escher, Grotto, **Sakura** (note: Sakura is a style in the PCG ecosystem but is NOT the Sakura hero — it's a foliage/architectural style), WP
- **Universal portfolio:** `PCG_MelodiaForest`, `PCG_MelodiaForest_Landscape`, `PCG_Melodia_Universal_Scatter`, `PCG_RockScatter`, `PCG_FoliageDensity`, `PCG_GardenRuins`, `PCG_LanternGrove`, `PCG_BezierGardenPromenade`, `PCG_BlossomPath`, `PCG_ClusteringScatter`, `PCG_LandmarkScatter`, `PCG_OrnamentalArch`, `PCG_OrnamentalDetail`, `PCG_PortfolioEnvironment`, `PCG_PortfolioTerraceBezier`, `PCG_BezierSplineGarden`, `PCG_BezierPathPortfolio`, `PCG_BezierGardenPromenade`, `PCG_MeadowBloom`, `PCG_MeadowFalloff`, `PCG_GreyboxBlockout`, `PCG_LanternGrove`
- **Collections:** `SMC_Greybox_ScatterKit`, `SMC_Portfolio_ScatterKit`
- **Control:** `BP_MelodiaPCGControl.uasset`, `BP_PathSplineProvider.uasset`
- **Editor lib:** `PCGScaleWorldEditorLibrary` — exports a level to a `UPCGDataAsset`
- **Live preview:** `PCGControlLivePreviewComponent` — debounced regeneration on control knob changes

### The two bridges (the convergence seam)
1. **`UMelodiaPCGWaterGameplayBridgeComponent`** — LIVE. Listens to `APCGHeroMusicGraphHost::OnNoteJudged` + `OnPatternCompleted`, routes into water state via `FGameplayTag` network (`WaterNetworkId`, `TargetWaterNodeId`, `ResonanceChannel`, `GradeStrength`). Uses `FGameplayTag` (not raw `FName`).
2. **`UMelodiaPCGNarrativeChallengeBridgeComponent`** — SOURCE ONLY. Same event listeners, but commits `ChallengeId` + `CompletionFlagId` + `RewardId` + `CompletionIntentId` via `UMelodiaNarrativeSubsystem::CommitWorldChallenge`. **No host actor attaches it.** This is the `music_world_key` blocker.

---

## 3. Quick wins for shipping tonight

Ranked by impact × speed × risk. All are **editor-bound, no C++ change required**.

### 🔴 Tier 1 — Do this first (one action unblocks a P0 gate)

#### 1. Wire the music-world-key narrative bridge  ← highest impact
- **What:** Attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to an `APCGHeroMusicGraphHost` inside one of the Hero levels (e.g., `L_PCG_Hero_ArpeggioBridge`).
- **Why it matters:** This is the documented blocker for `music_world_key`. The closeout plan says verbatim: *"Level wiring is the whole blocker; no code is needed."* The `OnPatternCompleted` event already fires from `APCGHeroMusicGraphHost`; the bridge just needs to be a component on the host actor.
- **What it unlocks:** `music_world_key` gate → a completed pattern commits `challenge.first_resonance_echo` (flag + reward `reward.first_resonance_echo`) via the narrative subsystem. This is the Zelda-ocarina reading: play the phrase, the door opens.
- **Risk:** Low — the bridge component is already compiled and the events exist. Just need a Blueprint or Level Blueprint to `Add Component` of the bridge class onto the host.
- **After:** live PIE proof + `record_gate.py music_world_key pass`.

#### 2. Revert the `.uproject` BOM + reindent
- **What:** `git checkout -- BS_GodFile.uproject`, then hand-apply only the `HoudiniEngine` enabled entry.
- **Why:** The diff is 331 ins / 327 del; ignoring whitespace it's a UTF-8 BOM + full reindent + the actual HoudiniEngine change. The BOM/reindent is noise that will churn every diff forever.
- **Risk:** Zero — revert noise, keep the one real change. Confirm with owner that HoudiniEngine should ship-enable.

#### 3. Decide tracked-vs-ignored for `Plugins/HoudiniEngine/` and Choral Sheep FBXs
- **What:** Add `.gitignore` entries or track them intentionally.
- **Why:** Currently everything is untracked. The `Plugins/HoudiniEngine/` tree is ~hundreds of MB of binaries. The Choral Sheep FBXs include an unskinned source mesh.
- **Risk:** Low — just decide and document.

---

### 🟠 Tier 2 — Low-effort, high-visual-polish (editor-only)

#### 4. Bake existing PCG style variants as runtime HDA outputs
- **What:** Take one of the already-authored PCG style graphs (e.g., `PCG_Cosmic_OrbitalRing` / `PCG_Cosmic_OrbitScatter`, or the Baroque column/bridge ensembles) and author them as HDAs. Bake at runtime via `UHoudiniAssetComponent`.
- **Why:** The existing PCG graphs are point-array graphs that already produce assemblies. Houdini can re-bake them with parameter variation (tempo → density, style → palette) so each playthrough's world is subtly different.
- **Quick path:** Use the `HoudiniInput` runtime parameter system to expose `Density`, `Style`, `Seed` as HDA parameters driven by the music tempo (from `UMelodiaMusicClockSubsystem`).
- **Risk:** Medium — requires HDA authoring in SideFX Houdini (or the built-in `rock_generator` / `he_sop_curve_instancer`). But the PCG graphs already exist as the "authoritative pattern set."

#### 5. HoudiniEngine foliage scattering for musical motifs
- **What:** Use `HoudiniFoliageTools` / `HoudiniInstancedActorComponent` to scatter musical-themed elements (piano keys, crystal shards, bell fragments, star-charm debris) across the Hero levels.
- **Why:** The `SMC_Portfolio_ScatterKit` already exists. Houdini can instance these at runtime with musical parameter variation — more notes = denser scattering, higher grade = brighter motifs.
- **Quick path:** Drop the `SMC_Portfolio_ScatterKit` assets into an HDA scatter node, bind count to the music score state, bake via `UHoudiniAssetComponent`.
- **Risk:** Low — scattering is a well-understood Houdini pattern and the assets are already authored.

#### 6. Refresh HLOD via `HoudiniHLODLayerUtils`
- **What:** The `L_PCG_Hero_ScaleWorldProof_HLODLayer_Instanced.uasset` and `L_PCG_Hero_ScaleWorldProof_HLODLayer_Merged.uasset` already exist. Use `HoudiniHLODLayerUtils` to regenerate them after any landscape/foliage changes.
- **Why:** HLOD is a shipping requirement for open worlds. The assets exist but may be stale after PCG changes.
- **Risk:** Low — just a refresh pass.

#### 7. Runtime HDA baking for "music shapes the world" feedback
- **What:** When a pattern completes, bake a small HDA (crystal, musical motif, doorframe) at the completion gate location via `UHoudiniAssetComponent`.
- **Why:** This is the visual payoff for the rhythm gameplay — the player plays the phrase, and the world *bakes into existence* around the gate. Directly supports the OMORI shape ("music opens doors").
- **Quick path:** Pre-author a small HDA (a gateframe / crystal / doorway). On `OnPatternCompleted`, spawn a `UHoudiniAssetActor` at `APCGArpeggioBridgeHost::CompletionGate` location with the HDA.
- **Risk:** Medium — requires a small HDA author, but it's a self-contained visual effect.

---

### 🟡 Tier 3 — Strategic expansion (worth planning, not tonight)

#### 8. PCG → HDA pipeline
- Author the existing PCG style graphs (Baroque, Cosmic, etc.) as HDAs so they can be baked at runtime with parameter variation. This connects music tempo directly to worldgen parameters.

#### 9. Data Layer mood switching via `HoudiniDataLayerUtils`
- Switch environmental Data Layers (`DL_Lighting_Day/Night`, `DL_PCG_Foliage`) based on musical state (major/minor, tempo band). The project already has the Data Layer infrastructure.

#### 10. PDG batch worldgen
- Use PDG to batch-generate PCG style variants for the different musical instruments, each with its own aesthetic. A background process that pre-bakes variants for shipping.

---

## 4. Architecture fit check (do not break the convergence seams)

Per `ORCHESTRA_CONVERGENCE_2026-08-20.md` and `ORCHESTRA_CONTRACT_2026-08-20.md`:

| Rule | Houdini quick-win compliance |
|---|---|
| QuillScript owns narrative | ✅ Houdini does not touch Quill |
| TurnBased JRPG template owns combat | ✅ Houdini does not touch combat |
| `UMelodiaNarrativeSubsystem` is the narrow Quill bridge | ✅ The bridge commits *through* the narrative subsystem |
| MelodiaCore assets are presentation-only | ✅ Houdini worldgen is presentation + worldgen, not combat |
| Music opens doors, never deals damage | ✅ The bridge only commits flags + rewards |
| One writer per UI surface | ✅ Houdini doesn't touch UI |
| `FGameplayTag` over raw `FName` | ⚠️ The water bridge uses tags; the narrative bridge uses `FName`. If Houdini feeds the bridge, keep using `FName` (it's the narrative record path) |
| `TRACE_CPUPROFILER_EVENT_SCOPE` on tick loops | ✅ Wrap any Houdini cook loops |

---

## 5. Recommended tonight's plan

```text
1. Revert .uproject BOM/reindent; hand-apply HoudiniEngine enable entry (5 min)
2. Wire UMelodiaPCGNarrativeChallengeBridgeComponent onto APCGHeroMusicGraphHost
   in L_PCG_Hero_ArpeggioBridge (30 min — Blueprint + Level Blueprint)
3. Live PIE proof: play the ArpeggioBridge pattern → confirm narrative challenge commits
   (flag + reward via UMelodiaNarrativeSubsystem)
4. Record gate: record_gate.py music_world_key pass
5. (Optional) Bake one PCG style as an HDA + scatter musical motifs via
   UHoudiniAssetComponent (1-2 h, visual polish)
6. Refresh HLOD on ScaleWorldProof via HoudiniHLODLayerUtils (15 min)
7. Decide tracked-vs-ignored for Plugins/HoudiniEngine + Choral Sheep FBXs
```

**The single highest-leverage action is #2.** The `music_world_key` gate is blocked purely by level wiring — no code, no HDA, no build. A Blueprint `Add Component` of the bridge class onto the existing `APCGHeroMusicGraphHost` unblocks it.

---

## 6. Open questions for the owner

1. **Should HoudiniEngine ship-enable in packaged builds?** It is Editor + Runtime, so it *can*, but it's a large binary. The `.uproject` change should be minimal and clean.
2. **Are the Hero levels' `APCGHeroMusicGraphHost` actors already placed and functional in PIE?** The bridge needs a live host to bind to.
3. **Is there an authored HDA in the project already?** I did not find any `.hda` files under `Content/` — the built-in tool HDAs (`rock_generator`, etc.) are under `Plugins/HoudiniEngine/Content/Tools/`.
4. **Does the team have a SideFX Houdini license** for authoring custom HDAs? The runtime bakes ship without it; authoring requires it.
5. **Is the `flag.first_dream.quest.completed` / `reward.first_resonance_echo` / `quest.first_dream` ID set in `DA_MelodiaIntegrationConfig`?** The bridge defaults to `challenge.first_resonance_echo` / `challenge.first_resonance_echo.completed` / `reward.first_resonance_echo` — these need to be allowlisted before the bridge can commit.
