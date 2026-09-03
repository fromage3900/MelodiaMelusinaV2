# P0 Ship-Night — Working Baseline (2026-08-28, 21:0x)

> **DO NOT STRAY FROM THIS BASELINE.** Everything below is verified on disk or in the
> engine log at the timestamp given. Return values from Monolith were NOT trusted (see
> Finding 2) — every claim here was confirmed by file mtime, on-disk grep, or engine log.

## Session state at capture

| | |
|---|---|
| Branch | `feature/p0-phase1-allowlist-quill-trigger` |
| HEAD at capture | `6dfb8c58` (`feat(lookdev): import Shorewake and Starskiff texture sets`) |
| Editor PID | 64492 (relaunched 20:52 after the 20:51 crash) |
| Monolith | v0.20.3, port 9316, UE 5.8 CL-55116800 |
| Crash count since relaunch | 0 |

## Gate state

| Gate | State | Evidence |
|---|---|---|
| `battle_integration_map` | pass | 2026-08-27 live PIE |
| `hud_single_writer` | pass | runtime widget identity |
| `music_world_key` | **PASS (bridge path), 5/5** | `Saved/Audit/music_world_key/p0_2026-08-28/assertions.json` |
| `static_gates` | **fail — blocked on owner decision** | 16 drifted assets, not the 2 the old doc claims |
| `rhythm_owner` | open | needs real Q/W/O/P input in `MelodiaIntegrationMap` |
| `rhythm_grade_to_result` | open | needs grade-delta on same skill/target |
| `wardrobe_equip_roundtrip` | open | needs full process restart |
| `wardrobe_gameplay_hook` | open | needs Glide on/off with equip |

### music_world_key caveat (important)

Proven by broadcasting `OnPatternCompleted` directly: delegate -> `HandlePatternCompleted`
-> `CommitWorldChallenge` -> narrative record, 5/5 deterministic, one commit per run.
**This does NOT meet Sol's plan bar**, which requires driving the phrase through real
gameplay overlap/input. The bridge contract is proven; the player-input link is not.

## What changed tonight (all verified on disk)

### Wiring
- `DA_MelodiaIntegrationConfig`: `WorldChallengeIds` was **EMPTY** -> `challenge.first_resonance_echo`;
  `NarrativeFlagIds` += `challenge.first_resonance_echo.completed`. Without this the bridge
  fails closed with `UnknownChallenge` while *looking* correctly wired.
- `MelodiaIntegrationMap`: `APCGHeroMusicGraphHost` ("Melodia Integration - Hero Music Host")
  at PlayerStart+600, carrying `MelodiaPCGNarrativeChallengeBridgeComponent`.
- `MelodiaIntegrationMap`: `OceanologyInfiniteOcean` parked at **Z=-5000** + `OceanologyManager0`.
  Parked deliberately: ground is Z~20, PlayerStart Z=112 — an ocean at Z=0 would flood the
  battle map and break the three gates still to be tested there. Raise it only for water lookdev.
- `L_PCG_Hero_WaterGameplayProof`: `OceanologyInfiniteOcean` + manager (legacy UE water left in place).

### Materials (9 landscapes + 18 reef meshes off placeholder)
- 4x `SM_Gaea_*_1025` : WorldGridMaterial -> authored `MI_Gaea_*_Substrate`
- `SM_SeaAbove_LiquidCathedral_257` : WorldGridMaterial -> `MI_SeaAbove_LiquidCathedral_Substrate`
  (that MI was a 0-override stub; populated to **36/36** from `MI_Gaea_LiquidCathedral_Substrate`)
- 4x `SM_Terrain_*` : `MI_Flat_stone` -> new `MI_Terrain_*_Substrate`
- 18 reef meshes -> 5 new instances (`MI_SeaAbove_CoralSkin`, `_CoralSkin_2S`, `_Kelp`, `_Sand`, `_WetRock`)
- `SeaAbove_ObservationCliff_Prototype` : `DefaultMaterial` -> `MI_SeaAbove_WetRock`
- `MI_ChoralSheep_Body` built on `M_Master_Toon_Character` (Albedo/Normal/RoughnessMap, 4096^2)

### Texture import defects corrected (22)
- 18 reef masks/LUTs were importing **sRGB** when they are non-colour data -> linear + `TC_MASKS`,
  Effects LOD group per `IMPORT_QUEUE.md`. Most important: `T_SeaAbove_KelpSway_LUT` drives WPO
  via `(rgb*2-1)`; an sRGB decode makes the sway displacement numerically wrong.
- 4x ChoralSheep data maps (Roughness/Metallic/Alpha/Displacement) -> linear + `TC_MASKS`.
- 4x `H_GroundTexture_Out` : `TC_EDITOR_ICON` -> `TC_DEFAULT`.

### Gaea
- `Content/Landscape/sssssssssssssss` -> **`Gaea_VolcanicCrater`** (133 assets, 0 redirectors).
  Node set is Volcano_Base/Crater/Outcrops/Sandstone/Dead_Soil — **no Snow, no Glacier nodes**.
- The AuroraGlacier `.terrain` IS a real glacier graph (8 Snow, 1 Glacier) but has **0 map files
  at source** — it has never exported. Not a naming problem; nothing was ever rendered.

## Findings that will bite the next session

1. **PIE teardown is async.** `load_level` immediately after `stop_pie` crashed the editor at
   20:51 (`EXCEPTION_ACCESS_VIOLATION` via `HandleRunPython` -> `PythonScriptPlugin` -> `UnrealEd`).
   Poll `is_in_play_in_editor()` until False first. Teardown measured at 1s, 5/5.
2. **Monolith return values lie.** Three confirmed cases: `save_loaded_asset` -> False while
   writing; `stop_pie` -> `stopped:false` while stopping; `save_current_level` -> False while
   saving. **Always verify by mtime / on-disk grep / log.**
3. **2,719 read-only `.uasset` files under `Content`.** Saves against them fail and the Python
   API returns False rather than raising. Cleared only for ChoralSheep (14) and
   `DA_MelodiaIntegrationConfig`. The rest remain read-only — this will silently eat work.
4. **`Content/Landscape` is gitignored** (`.gitignore:110 Content/*`). All 133 Gaea assets are
   untracked and will not survive a clone. `.gitignore` is never-touch; owner decision.
5. **`static_gates` drift is 16 assets, not 2.** The P0 doc is stale. `verify_baseline.py --update`
   rewrites the whole baseline — no partial accept — so blessing it accepts all 16.
   Owner said "intended; expansion was needed for P0" but was answering about 2.
   Unreviewed: 3x Impressionist functions ~tripled; `M_Master_Toon_Unified` got *smaller*.
6. **`BP_OceanologyInfiniteOcean` is deprecated** — engine refuses to spawn it. Use the native
   `OceanologyInfiniteOcean` class.
7. **Narrative record does not persist across PIE sessions.** Every run began `pre_completed=false`.
   Idempotency is within-session only.
