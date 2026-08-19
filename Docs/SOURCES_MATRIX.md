# Sources Matrix — every `Content/` folder mapped to its credit row

**Purpose:** the single coverage map behind `Tools/credits_gate.py`. Every top-level
`Content/` directory must have at least one row below. A directory with no row is a
credits gap and fails the gate. Commit this update alongside any new asset import.

Status values:
- `verified` — creator + URL + licence recorded
- `first-party` — owner work (`fromage3900`); no attribution required
- `pending` — source awaits owner confirmation; **no name is guessed here**
- `n/a` — technical/mirror/derived content (no independent creative origin)

| Path (Content/) | Source / pack | Creator | URL | License | Status |
|---|---|---|---|---|---|
| `Audio` | Electric Dreams ambience + Kenney/Beatscribe/Junkala CC0 packs | Epic Games + Kenney + Beatscribe + Juhani Junkala | https://fab.com/s/7ee8c5704aaa · https://kenney.nl | UE-Only + CC0 | verified |
| `Asmbly` | Electric Dreams Environment — assembly kit | Epic Games | https://fab.com/s/7ee8c5704aaa | UE-Only | verified |
| `Brushify - Floating Islands` | Brushify – Floating Islands | Joe Garth (Brushify Ltd) | https://www.fab.com/listings/097af450-268d-4691-9502-aeb3714fbda7 | Marketplace EULA | verified |
| `Custom` | First-party Blender/custom work + ED sequence copy | fromage3900 + Epic Games | first-party · https://fab.com/s/7ee8c5704aaa | Owner + UE-Only | verified |
| `EnvSandbox` (Cathedral / OrnamentMusical / SDF-SKU2 suite) | First-party art & material suite | fromage3900 | first-party | Owner | verified |
| `EnvSandbox` (Textures/BlingVol3) | Bling Vol 3 rhinestone texture set (internal Substance pack) | fromage3900 | first-party | Owner | verified |
| `EnvSandbox` (Library/Migrated/MagiciansLibrary) | Magician's Library Environment & VFX Pack | Coreb Games | https://www.fab.com/listings/25a46fa5-1f75-44e0-806c-026cfc1d45f8 | Marketplace EULA | verified |
| `EnvSandbox` (Meshes/Environment — ~760-module assembled kit) | Assembled modular environment mega-kit (castle/interiors/nature/siege; components: carrot_fbx, FoodProps, confectionary + more) | Assembled by fromage3900 · components per-pack | https://www.artstation.com/marketplace | Per-component (ArtStation/CC0) | verified |
| `Greybox_Kit` | First-party greybox + Melusina's house props | fromage3900 | first-party | Owner | verified |
| `Library` | Magician's Library (migrated) + CC0 staged sets | Coreb Games + CC0 creators | https://www.fab.com/listings/25a46fa5-1f75-44e0-806c-026cfc1d45f8 · https://kenney.nl | Marketplace EULA + CC0 | verified |
| `Megascans` | Megascans library | Quixel (Epic Games) | https://quixel.com/megascans | Megascans/Fab terms | verified |
| `Melodia` | First-party characters, narrative, UI, audio | fromage3900 | first-party | Owner | verified |
| `Textures` | Shared textures: EnvRnd/Epic sample + 70 Japanese Ornament Alphas (Jonas Ronnegard) + first-party | Epic Games + Quixel + Jonas Ronnegard + fromage3900 | first-party · https://quixel.com/megascans · https://www.artstation.com/marketplace/p/NNDo/zbrush-sp-70-japanese-ornament-alphas | Mixed (UE-only/ArtStation/CC0) | verified |
| `TurnBasedJRPGTemplate` | Turn-Based jRPG Template | Phoenix Market | https://www.fab.com/listings/fe140454-1e7f-49eb-bd29-cf5588ce3ed1 | Marketplace EULA | verified |
| `UI` | Widget style sheet JSON | fromage3900 (first-party authored in-project; verify owner before shipping) | first-party | Owner | pending |
| `Widgets` | Command/Enemy/Results phase widgets | fromage3900 (first-party authored in-project; verify owner before shipping) | first-party | Owner | pending |
| `UltraDynamicSky` | Ultra Dynamic Sky | Everett Gunther | https://ultradynamicsky.com · https://www.fab.com/listings/84fda27a-c79f-49c9-8458-82401fb37cfb | Marketplace EULA | verified |
| `_PROJECT` | First-party project content (Melusina's house etc.) | fromage3900 | first-party | Owner | verified |
| `_ThirdParty` | Reference/mirror copies (stock template reference) | N/A — technical mirror | N/A | n/a | n/a |
| `__ExternalActors__` / `__ExternalObjects__` | Level actors derived from covered sources (ED level, first-party levels) | Epic Games + fromage3900 | https://fab.com/s/7ee8c5704aaa | mixed | verified |
| `Python` (_Content/Python_) | Tooling scripts | first-party | first-party | Owner | verified |
| `MelodiaIntegration` | First-party C++ bridge blueprints & config (narrative→JRPG) | fromage3900 | first-party | Owner | verified |
| `Cinematics` | Melusina water-hair flip cache + GC | fromage3900 | first-party | Owner | verified |
| `NPCs` | SakuraDreamer + GMM/VRoid staged characters | GMM creator + SSS LLC (Zunko family) | https://hub.vroid.com · https://zunko.jp | Per-model / SSS terms | verified |
| `Content` (nested mirror dir) | Duplicate-tree mirror (`Content/Content`) | N/A — technical mirror | N/A | n/a | n/a |
| `Saved` | Working editor data (caches, quarantines) | N/A — working data | N/A | n/a | n/a |
| `Imports` (staging) | Kenney / Quaternius / KayKit / BOOTH / Beatscribe / etc. | per-pack creators (see `Imports/<pack>/PROVENANCE.md`) | https://github.com/fromage3900/MelodiaMelusinaV2/tree/main/Imports | CC0 / BOOTH / per-creator | verified |
| `Actor_BP` | Gameplay actor & controller blueprints (template-derived + first-party) | fromage3900 + Phoenix Market (template) | first-party · https://www.fab.com/listings/fe140454-1e7f-49eb-bd29-cf5588ce3ed1 | Owner + Marketplace EULA | verified |
| `Blueprints` / `Game_BP` / `DataStuctures` | Template framework blueprints & data structures | Phoenix Market (template) | https://www.fab.com/listings/fe140454-1e7f-49eb-bd29-cf5588ce3ed1 | Marketplace EULA | verified |
| `Characters` | Melusina + Zunko-family + GMM/VRoid cast | fromage3900 + SSS LLC + でし丸 | first-party · https://zunko.jp | Owner + SSS/per-model terms | verified |
| `Art` | Environment-art platform own content | fromage3900 | first-party | Owner | verified |
| `ArtOfShader` | Art of Shader — Stylized Post Process Pack | Sameek Kundu | https://forums.unrealengine.com/t/art-of-shader-stylized-post-process-pack/142950 | Marketplace EULA (vfxMed distribution) | verified |
| `Assets` | Catch-all asset folder (unassessed) | **UNKNOWN — awaiting sweep** | TBD | TBD | pending |
| `Alphas_Sparkles` | VFX sparkle alpha textures (origin unconfirmed) | **UNKNOWN — awaiting sweep** | TBD | TBD | pending |
| `Genshin_Shader_v1_1` | Genshin-style shader experiments (origin unconfirmed) | **UNKNOWN — awaiting sweep** | TBD | TBD | pending |
| `Magical` | Magical/VFX dressing (origin unconfirmed) | **UNKNOWN — awaiting sweep** | TBD | TBD | pending |
| `SurrealRocks` | Rock/cliff dressing (origin unconfirmed) | **UNKNOWN — awaiting sweep** | TBD | TBD | pending |
| `IMPERFECTER_-_Post_Process_Toolkit_v1.3.1___40_5.6__5.7_` | IMPERFECTER – Post Process Toolkit | Hubert Mika | https://www.fab.com/listings/40b5efe7-b147-4265-b06b-0c62b5337475 | Marketplace EULA | verified |
| `IMPERFECTER_-_Post_Process_Toolkit_v1_3_1___40_5_6__5_7_` | IMPERFECTER – Post Process Toolkit (duplicate copy of v1.3.1) | Hubert Mika | https://www.fab.com/listings/40b5efe7-b147-4265-b06b-0c62b5337475 | Marketplace EULA | verified |
| `MooaToonSamples` | MooaToon — cinematic toon rendering toolkit (samples) | Jason Ma (JasonMa0012) | https://github.com/JasonMa0012/MooaToon · https://mooatoon.com | MooaToon open-source licence | verified |
| `MSPresets` | MetaSound presets (MSS_JRPG master chain) | fromage3900 | first-party | Owner | verified |
| `CustomAudio` | Custom audio edits over staged CC0 packs | fromage3900 | first-party | Owner | verified |
| `MaterialFunctions` / `MaterialLayers` / `Materials` / `Substrate` / `Stylization` / `SmartAssets` | Material suite + engine scaffolding (SDF/Universal spine) | fromage3900 | first-party | Owner | verified |
| `PhysicalMaterials` / `RVTDecals` / `PCG` | Physics/RVT/PCG system data | fromage3900 | first-party | Owner | verified |
| `Landscape` | Landscape layers/splines (first-party sculpting) | fromage3900 | first-party | Owner | verified |
| `Levels` | First-party level builds + Electric Dreams sample level | fromage3900 + Epic Games | first-party · https://fab.com/s/7ee8c5704aaa | Owner + UE-Only | verified |
| `Meshes` | First-party mesh exports (unversioned art set) | fromage3900 | first-party | Owner | verified |
| `Collections` / `Developers` / `Experiments` / `Tests` / `Input` / `Data` / `FX` / `Effects` | First-party tooling, data, FX, test content | fromage3900 | first-party | Owner | verified |
| `Exports` | Generated Blender export artefacts | fromage3900 | first-party | Owner | verified |
| `Surfaces_CC0` | CC0 surface/trimsheet textures (collective CC0 community) | CC0 community (see CREDITS.md CC0 rows) | https://opengameart.org | CC0 | verified |
| `Sakura` | Sakura level art direction (human-owned boundary) | fromage3900 | first-party | Owner | verified |
| `ZenForestTest_sharedassets` | ZenForest test work (built on ED + first-party assets) | fromage3900 + Epic Games | first-party · https://fab.com/s/7ee8c5704aaa | Owner + UE-Only | verified |
| `_QuarantinePostProcess_20260801` | Quarantined post-process experiments | fromage3900 | first-party | Owner | verified |
| `kenney_fantasy-ui-borders` | UI borders pack | Kenney | https://kenney.nl/assets/fantasy-ui-borders | CC0 | verified |
| `magicianlabatory` | Magician's Library Environment & VFX Pack | Coreb Games | https://www.fab.com/listings/25a46fa5-1f75-44e0-806c-026cfc1d45f8 | Marketplace EULA | verified |
| `Greybox_Kit` (ZenTrim wand/streetlamp re-topo) | First-party re-topo + material pass | fromage3900 | first-party | Owner | verified |
