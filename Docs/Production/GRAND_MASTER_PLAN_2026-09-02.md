# Melodia — Grand Master Plan

**Date:** 2026-09-02
**Status:** CANONICAL — integrates all active research, plans, and workflows
**Sources:** `melusinashouseplan.md`, `MELODIA_STUDIO_DEEP_INTAKE_2026-09-02.md`, `EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`, `TODO.md`, `GRANDMASTER_MASTER_PLAN_V2.md`, `LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md`, `BLENDER_MELODIA_COCKPIT.md`, `Tools/Moho/README.md`

---

# 𝄞 Part I — Product Vision

## 1. Thesis

Melodia Melusina is an **evergreen single-player Rhythm-JRPG** that can grow for years without requiring the original journey to remain unfinished.

> **There will sometimes be more journey. There will never need to be more journey.**

## 2. Release Structure

| Tier | Definition |
|------|-----------|
| **Volume** | Major emotionally complete journey |
| **Movement** | Thematic act that permanently changes understanding |
| **Chapter** | Named unit with clear question, mechanical focus, location, visual signature, persistent change, exit image |
| **Episode** | Compact adventure inside a Chapter |
| **Reverie / Interlude** | Small intimate unit, often no combat |
| **Monolith Event** | Rare assumption-breaking culmination |

## 3. Volume I — Four Movements (52 chapters)

| Movement | Theme | Tentpoles |
|----------|-------|-----------|
| I — The First Answer | Intimacy → resonance → departure | First Dream, Resonant Weave, Choral Sheep, Sea Above, Shorewake, Starskiff |
| II — The World Reads Back | Fashion becomes language | Mara Elletra Vell, Seam Map, Hemlands, cymatic fabric-geography, Faraway Mother |
| III — The Category Error | Matter/space stop obeying categories | Iris Fen, Catalyze, God That Molts, Glasswing, Horizon Eater |
| IV — The Shape We Choose | Identity, interpretation, Convergence | House of Measures, Seam Oracle, Refuse the Measure, Last Dress, homecoming |

---

# ♫ Part II — Current State of the Art

## 4. Toolchain (Active)

| Tool | Version | Role |
|------|---------|------|
| Unreal Engine | 5.8 | Runtime authority, gameplay, PIE, packaging |
| Blender | 5.2.1 LTS | Environment authoring, Geometry Nodes, audio terrain |
| Houdini | 22.0.368 | Reusable geometry, masks, LODs, scatter |
| SpeedTree | — | Core plant authority |
| Gaea | — | Terrain generation |
| Copernicus | — | Houdini GPU texture/mask |
| Melodia Studio | v1.5.0 | 173 GN builders, 12 sections |
| Kawaii GN | — | 15 character/prop generators |
| Brutalist GN | — | 4 architecture generators |
| Monolith MCP | — | 1330+ UE editor actions |
| Rider | 2026.2.1 | C++/Unreal IDE |
| Moho | — | Planned: 2D animation/vector authoring |

## 5. Emerging Tech Index (PRESENT — do NOT rebuild)

| System | Path |
|--------|------|
| SpeedTree | `Content/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.uasset` |
| Houdini 22 | `Plugins/HoudiniEngine/` |
| Copernicus | `Tools/Houdini/copernicus/` |
| Gaea | `Plugins/GaeaUnrealTools/` |
| PCG + toolkit | `Plugins/PCGExtendedToolkit/` |
| Monolith | `Plugins/Monolith/` (1330+ actions) |
| Audio-Reactive presentation | `Source/.../MelodiaAudioReactivePresentationSubsystem` |
| Music clock | `Source/.../MelodiaMusicClockSubsystem` |
| Cymatics/Chladni | `Source/.../MelodiaCymaticsSubsystem` |
| Cymatic Sanctuary | `Docs/Tools/puzzle-sandbox/index.html` |
| MelodiaCymaticsWriterSubsystem | Single-writer for MPC_Cymatics_Driver |
| Claireon | `.claireon/` (gitignored, re-clone required on laptop) |
| NNERuntimeORT | `Plugins/NNERuntimeORT/` (gitignored, re-clone required) |
| onnx model | `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx` |

## 6. SCAFFOLDED (extend, don't duplicate)

| System | Source Files |
|--------|--------------|
| MelodiaCaptureRenderSubsystem | `Source/.../MelodiaCaptureRenderSubsystem.h/.cpp` |
| MelodiaDressingSubsystem | `Source/.../MelodiaDressingSubsystem.h/.cpp` |
| MelodiaVisualRepresentationSubsystem | `Source/.../MelodiaVisualRepresentationSubsystem.h/.cpp` |
| MelodiaVegetationGrowthSubsystem | `Source/.../MelodiaVegetationGrowthSubsystem.h/.cpp` |

## 7. WATCH (needs explicit owner task)

| System | Where |
|--------|-------|
| Magpie (generative renderer) | `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md` |
| Neural shaders/materials | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §neural |
| Procedura | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Procedura |
| RTX Kit / NvRTX | `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03` §14 |

---

# ♬ Part III — Melodia Studio / GN Workflows

## 8. Architecture

**Three-layer system:**

| Layer | Files | Purpose |
|-------|-------|---------|
| Melodia Studio | 30 Python files | Main addon (MIDI→world, terrain, dressing) |
| Surreal Arch | 120 Python files | 173 GN builders, 12 sections |
| Kawaii + Brutalist GN | ~40 files | Specialized generators |

**173 GN builders** across: Set Dressing (39), Structures (12), Musical Notation (7+), Castle Kit, Ornament, Magic Effects.

## 9. Top-of-the-Line GN Workflows

### 9.1 MIDI-Driven World Generation
- Parse MIDI → extract notes → generate heightfields
- Beatgrid merging (transpose +36 semitones)
- Walkable terrain with instanced dressing
- Single source of truth: `Tools/BlenderAddons/melodia_studio/core/field.py`

### 9.2 Audio Terrain Pipeline
**Scripts:** `Tools/audio_terrain_pipeline.py` + `Content/Python/import_audio_terrain_handoff.py`  
**Status:** ✅ Validated

```powershell
# Dry run
python Tools/audio_terrain_pipeline.py --audio Content/Melodia/Characters/Itako/Audio/ita_battle_debuff_01.wav --times 0 15 30 --output Saved/AudioTerrain --dry-run

# Full run
python Tools/audio_terrain_pipeline.py --audio Content/Melodia/Characters/Itako/Audio/ita_battle_debuff_01.wav --times 0 15 30 --output Saved/AudioTerrain
```

**3 builders:** `MEL_audio_spectrum_terrain`, `MEL_audio_spectrum_towers`, `MEL_audio_radial_field`  
**3 profiles:** preview (1×1, 128m), region (4×4, 256m), continent (16×16, 512m)

### 9.3 Sea Above AAA Presets
**Script:** `Tools/stage_melodia_aaa_presets.py`  
**Status:** ✅ Validated

```powershell
python Tools/stage_melodia_aaa_presets.py --audio Content/Melodia/Characters/Metan/Audio/met_bond_01.wav --output Saved/MelodiaPresetReview/Melodia_AAA_Preset_Review.blend --export
```

**10 presets:** false horizon, bell ribs, membrane, reveal gallery, bell anatomy chamber, false horizon observatory, harpsichord hero, violin reliquary, organ cathedral, lute vault

### 9.4 Procedural Architecture Grammar
- Metric massing from footprints
- Floors, bays, openings, roof outlines
- Facade/socket points for kitbashing
- Borromini-inspired concave→convex→concave façade rhythm
- Rococo rocaille: C/S curves, shell fan, pearl strings, controlled asymmetry

### 9.5 Greybox System
- Mesh Boolean DIFFERENCE for hollow rooms
- Tileable corridors with optional end caps
- T/X junctions for level design
- Modular stack: base → shaft → lantern ring → dome cap → crest

### 9.6 Preset Library
- 42 builders × 173 looks
- STUDIO_LABELS for organization
- Review Queue for visual QA
- Solo Object isolate, Ivy (Bagapie) scatter

### 9.7 Blender Melodia Cockpit
**File:** `Docs/BLENDER_MELODIA_COCKPIT.md`  
**Purpose:** Central command reference for Blender production pipelines

| Pipeline | Import Script | UE Destination |
|----------|---------------|----------------|
| Ornament FBX | `Content/Python/import_ornament_fbx.py` | `/Game/EnvSandbox/Meshes/Ornament/` |
| Musical FBX | `… --musical --prep` | `/Game/EnvSandbox/Meshes/OrnamentMusical/` |
| Musical Kitbash | `Content/Python/package_musical_ornament_kitbash.py` | Products + web JSON |
| Gothic 15 Kitbash | `watch_ornament_export_and_package.py --also-import` | Poll → UE import → ZIP |
| Headless Kitbash | `run_ornament_kitbash_pipeline.ps1 -ImportFromKitbash` | Cmd import + prep + package |

**Audit outputs:**
- Gothic: `Saved/Audit/ornament_fbx_import.json`
- Musical: `Saved/Audit/musical_ornament_fbx_import.json` / `musical_ornament_bake_manifest.json`

---

# 𝄞 Part IV — Melusina's House Build Plan

## 10. Design Thesis

**Round Baroque, not a generic cottage.** The architecture swells, answers, curls, and repeats motifs instead of stacking rectangles under fantasy decoration.

### Historical Grammar (ingredients, not reconstruction)
- **Borromini / San Carlo:** concave→convex→concave façade rhythm
- **Rococo:** rocaille vocabulary — broken-shell, marine, acanthus, S/C curves, controlled asymmetry

### Melodia Palette
| Color | Hex |
|-------|-----|
| blush plaster | #F7D6E7 |
| pearl | #F6F0E8 |
| powder blue | #9CC6E6 |
| roof blue | #6E8AAF |
| lavender | #A8A0DD |
| rose accent | #E7A5C9 |
| warm brass | #C6A15A |

## 11. Working Scale

| Parameter | Start Value | Range |
|-----------|-------------|-------|
| overall width | 13.2 m | 12.5–14.0 m |
| overall depth | 9.8 m | 9.0–11.0 m |
| main wall height | 3.42 m | 3.35–3.50 m |
| loft spring | 2.9 m | 2.8–3.0 m |
| main ridge | 8.4 m | 8.0–8.8 m |
| tower top | 10.5 m | 10.0–11.0 m |
| porch depth | 1.8 m | 1.7–1.9 m |
| front door | 1.15 × 2.35 m | ±10% |
| wall thickness | 0.30 m | 0.28–0.32 m |
| façade wave amplitude | 0.65 m | 0.55–0.75 m |
| eave overhang | 0.58 m | 0.50–0.65 m |
| main roof rise | 2.55 m | 2.3–2.8 m |
| shingle module | 0.28 × 0.36 m | ±10% |
| shingle overlap | 40% | 35–45% |
| trim profile radius | 0.05 m | 0.03–0.08 m |
| baluster spacing | 0.32 m | 0.30–0.34 m |
| tower diameter | 1.8 m | 1.6–2.0 m |
| secondary ornament omit | 20% | 15–25% |

## 12. GN Node Groups (Canonical Names)

```
GN_MH_00_MasterAssembly
GN_MH_01_FoundationPorch
GN_MH_02_CurvedWallShell
GN_MH_03_RoofRibbon
GN_MH_04_ScallopShingles
GN_MH_05_WindowDoorKit
GN_MH_06_TowerChimney
GN_MH_07_RocailleTrim
GN_MH_08_RailingBalusters
GN_MH_09_AwningsDrapes
GN_MH_10_FoliageScatter
GN_MH_11_InteriorShell
GN_MH_12_MusicalOrnamentPass
```

## 13. Step-by-Step Build Order

| Step | Work | Gate |
|------|------|------|
| 0 | Protect project, new .blend, MCP connect | Scene info verified |
| 1 | Draw curves (footprint, façade) | Silhouette reads in top/front |
| 2 | Foundation + porch | Curved deck, shell-finial stairs |
| 3 | Curved wall shell | concave→convex→concave in clay |
| 4 | Window/door family | One reusable kit, no bespoke holes |
| 5 | Roof ribbon system | Three roofs read as one family |
| 6 | Scallop shingles | Rows stable, instances not exploded |
| 7 | Tower + rails + rocaille | Silhouette unmistakably Melodia |
| 8 | Drapes + flowers + materials | Color balance matches refs |
| 9 | Polish + screenshots + parameter audit | Front/3q/side all agree |

## 14. Master Controls (Exposed Parameters)

```
Facade Wave
Wall Height
Wall Thickness
Roof Main Rise
Roof Curl
Eave Overhang
Tower Height
Tower Diameter
Shingle Density / Scale
Trim Density
Ornament Asymmetry
Flower Density
Random Seed
Show Interior
Show Set Dressing
LOD / Preview Density
```

## 15. Materials

| Material | Direction |
|----------|-----------|
| `M_MH_PearlPlaster_Pink` | warm blush plaster, gentle roughness breakup, faint pearl |
| `M_MH_Roof_IridescentBlue` | blue/lavender/rose color shift, scallop tiles readable |
| `M_MH_GoldBrass` | aged warm gold, polished edges, darker recesses |
| `M_MH_WoodWarm` | honey/walnut structural wood, modest wear |
| `M_MH_LavenderFabric` | soft lavender/mauve, slightly translucent edge |
| `M_MH_AquaGlass` | warm interior emission behind aqua/opalescent glass |

## 16. Interior Layout

```
MAIN LEVEL
  center      entry + sitting / circular rug
  left        music / prayer nook
  right       kitchen + pantry
  rear/right  curved stair
  porch       social / sea-facing extension

UPPER
  left/center sleeping loft
  center/right writing desk / field-journal worktable
  right tower lookout niche
```

---

# ♪ Part V — Production Phases

## Phase 1 — Close the Runtime (NOW)

**Goal:** restart-safe save, repeat-load-safe reward

- [ ] Re-cut persistence from stale PR #54 onto fresh branch
- [ ] Audit `RestoreNarrativeRecord` for partial mutation
- [ ] Add intrinsic candidate validation before canonical mutation
- [ ] Add repeat-load equality + idempotency tests
- [ ] Trace Starskiff durable facts vs derived/transient state
- [ ] Trace Convergence ownership the same way
- [ ] Extend save schema only after durable facts are locked
- [ ] Run full process restart proof
- [ ] Run packaged-build proof

**Hard no's:** no Phoenix rewrite, no second SaveGame authority, no persisted live rhythm session, no imported frameworks, no remote Gifts backend before local persistence is boringly reliable.

## Phase 2 — Make Chapters Cheap (NEXT)

**Goal:** new Chapter = content, not engine surgery

- [ ] Lock one canonical Chapter-package template
- [ ] Require 7 authoring questions per package
- [ ] Require stable IDs + idempotent intents/rewards
- [ ] Validate offline → PIE → restart/load → packaged

## Phase 3 — Volume I Content

### Movement I — The First Answer
- [ ] First Dream polish + canonical package
- [ ] Resonant Weave / outfit-as-gameplay proof
- [ ] Choral Sheep / music-creature relationship
- [ ] Sea Above Monolith Event
- [ ] Shorewake + Starskiff departure

### Movement II — The World Reads Back
- [ ] Mara Elletra Vell owner canonization
- [ ] Seam Map / clothing-as-language package
- [ ] Hemlands / Pleated Range / Embroidered Basin
- [ ] Cymatic fabric-geography integration
- [ ] Faraway Mother / The Blink Monolith Event

### Movement III — The Category Error
- [ ] Iris Fen owner canonization
- [ ] Keep `Catalyze` narrow: material-state/world interaction
- [ ] Create God That Molts progression package
- [ ] Reconcile Horizon Eater ordering
- [ ] Prototype Glasswing / Wayfold with authored spatial tricks
- [ ] Horizon Eater Event integration

### Movement IV — The Shape We Choose
- [ ] House of Measures chapter family
- [ ] Seam Oracle: silhouette × rhythm behavior × Convergence
- [ ] `Refuse the Measure` as constrained outfit reinterpretation
- [ ] Last Dress of the Sea world-scale synthesis
- [ ] Homecoming / `The First Time She Is Not Late`

## Phase 4 — Evergreen

- [ ] Keep content/reward IDs globally stable
- [ ] Keep save schemas versioned and migratable
- [ ] Keep claimed intents/rewards exactly-once forever
- [ ] Starskiff mailbox/archive as local presentation contract
- [ ] Design remote manifest only after packaged single-player closure
- [ ] Default Gifts to permanent/archiveable
- [ ] Never make combat/narrative depend on network

---

# ♬ Part VI — Two-PC Development Workflow

## Lane A — JetBrains Gateway
- Rider backend on laptop → thin client on main PC via SSH
- Full Rider intelligence without UE on main PC

## Lane B — VS Code Remote SSH
- Lightweight scripts/docs on laptop
- Faster connection than Gateway

## Lane C — UBA Distributed Compilation
- Laptop as compile worker when VS 2022 installed
- Both machines need same UE + VS toolchain

## Lane D — Git Branch Handoff
- `collab/laptop/<task>` branches
- LFS locks for binary assets
- Each workstation gets its own clone

## Lane E — Hermes Orchestration
- Main PC dispatches via `delegate_task`
- Laptop runs unattended test/report lanes

---

# 𝄞 Part VII — Laptop Workstation Setup & Offload Plan

## 1. Hardware Record

| Component | Measurement | Consequence |
|---|---|---|
| Model | Acer Nitro AN515-51 | Use the measured profile, not the product family name |
| Memory | 15.9 GB RAM; 2 x 8 GB at 2133 MHz | Worker-first; keep heavy applications in separate modes |
| CPU | Intel Core i5-7300HQ; 4 cores / 4 threads; 2.50 GHz | Good for bounded scripts and serial asset jobs |
| GPU | NVIDIA GeForce GTX 1050 Ti; 4 GB VRAM | Asset inspection, modest viewport; not primary renderer |
| System drive | `C:` 14.5 GB free of 237.4 GB | Do not place UE, caches, or project clone here |
| Work drive | `P:` 251.4 GB free of 931.5 GB | Preferred for project clone, staged jobs, outputs |

## 2. Worker Role Assignment

**Primary lanes (active):**
- Blender background exports and procedural generation
- Mesh, material, texture, animation staging outside live UE Content/
- Offline manifests, hashes, validation reports
- Source/docs, Rider/VS Code, deterministic tests
- Three.js/web prototypes, asset preparation

**Planned lane (scaffolded):**
- Moho source/job staging (requires licensed Moho + automation path)

## 3. Moho Scaffold

**File:** `Tools/Moho/README.md` + `run_moho_worker.ps1`

Moho is a planned authoring lane — the repo contains **no** Moho plugin, automation API, executable contract, or native Moho project format. The scaffold currently performs only safe staging and inventory checks; it does not launch Moho.

**Next integration gate (before adding real execution):**
1. Licensed Moho version and install path
2. Supported command-line, scripting, or UI automation entry point
3. Accepted source and export formats
4. Deterministic output and failure semantics
5. Review and Unreal handoff rules

## 4. Install Order

1. Windows Update + GPU driver + AC power
2. Git + Git LFS (`git lfs install`)
3. Clone lightweight checkout:
   ```bash
   GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaMelusinaV2-Laptop
   cd MelodiaMelusinaV2-Laptop
   git config core.autocrlf false
   git config core.hooksPath .githooks
   git lfs install
   bash deploy/collaborator_onboarding.sh lightweight .
   ```
4. Visual Studio C++ toolchain (import `.vsconfig`)
5. Rider (open `BS_GodFile.uproject`)
6. VS Code (lightweight scripts/docs)
7. Unreal Engine 5.8 via Epic Launcher
8. Blender 5.2.1 LTS

## 5. Git Handoff Protocol

**Laptop (finish task):**
```bash
git status --short --branch
git add <specific-files>
git commit -m "describe the laptop task"
git push -u origin collab/laptop/<short-task-name>
```

**Main PC (consume):**
```bash
git fetch origin
git switch main
git pull --ff-only
git merge --ff-only origin/collab/laptop/<short-task-name>
```

**LFS lock for binary assets:**
```bash
git lfs lock <path/to/asset>
```

**Machine-local state (never copy as source):** `Saved/`, `Intermediate/`, `Binaries/`, `.rider/`, `.idea/`, `DerivedDataCache/`

## 6. Acceptance Checklist

- [x] RAM/GPU/CPU/SSD/free-space measurements recorded
- [x] Laptop profile selected: worker-first
- [x] Windows/GPU driver/power setup complete
- [x] Git + Git LFS installed
- [x] Lightweight sparse checkout complete
- [x] `core.hooksPath` = `.githooks`
- [x] Rider opens `BS_GodFile.uproject`
- [x] VS Code opens scripts/docs
- [x] Blender 5.2.1 LTS validated (audio terrain + presets)
- [ ] `.vsconfig` toolchain installed
- [ ] `validate_setup.ps1 -SkipServices -CheckLfsHydration` passes
- [ ] Closed-editor plugin build completes
- [ ] Small `collab/laptop/...` branch pushed and consumed
- [ ] UE 5.8 installed and launched (manual via Epic Launcher)

---

# ♪ Part VIII — Definition of Progress

A successful session leaves:

- one restart-safe save
- one repeat-load-safe reward
- one Chapter that reuses existing owners
- one old location that remembers what happened there
- one Monolith Event that reinterprets mechanics we already own
- one new Voyage an old save can enter cleanly

> **The goal is to spend more time making journeys and less time reopening the engine underneath them.** ♪

---

# ♫ Part IX — Laptop Onboarding Status

| Item | Status |
|------|--------|
| `SOUL.md` | Written at `C:\Users\brenn\AppData\Local\hermes\SOUL.md` |
| Two-PC workflow | Committed (`9a73c4c3`) |
| MASTER_INDEX | Committed (`d68fb4fb`) |
| Grand Master Plan | Committed (`2acddef9`) |
| Worktree | Clean (LFS cosmetic drift only) |
| LFS | 3479/3479 uassets hydrated |
| Rider | 2026.2.1 installed |
| Blender | 5.2.1 LTS installed & validated |
| Epic Launcher | Installed & running |
| Python | 3.11.9 installed |
| Git push | Succeeded (verified via GitHub) |
| VS 2022 | ❌ Manual UAC required |
| UE 5.8 | ❌ Install via Epic Launcher |
| OpenSSH Server | ❌ Manual admin install |
| C++ compiler | ❌ Blocked on VS 2022 |

---

> **House rule:** make the architecture sing before decorating it with notes. ♪

---

## Appendix A — Branch Inventory

| Branch | Commit | Content |
|--------|--------|---------|
| `docs/2026-09-02-melusinashouseplan` | `b700326e` | melusinashouseplan + Blender 5.2 cockpit reference |
| `docs/2026-09-02-grand-master-plan` | `2acddef9` | Canonical integrated plan (this document) |
| `collab/laptop/workstation-health` | `30039e8c` | Laptop art worker + Moho scaffold |
| `collab/laptop/integration-batch-2026-09-02` | `c0c4148c` | 22-commit integration batch (onboarding, workflow, index, deprecated archival) |

## Appendix B — Document Cross-Reference

| Document | Relationship |
|----------|--------------|
| `melusinashouseplan.md` | Source for Part IV (House Build Plan) |
| `MELODIA_STUDIO_DEEP_INTAKE_2026-09-02.md` | Source for Part III (GN Workflows) |
| `EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` | Source for Part II (Toolchain State) |
| `LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md` | Source for Part VII (Laptop Setup) |
| `BLENDER_MELODIA_COCKPIT.md` | Source for §9.7 (Cockpit Reference) |
| `GRANDMASTER_MASTER_PLAN_V2.md` | Source for Part I (Product Vision) |
