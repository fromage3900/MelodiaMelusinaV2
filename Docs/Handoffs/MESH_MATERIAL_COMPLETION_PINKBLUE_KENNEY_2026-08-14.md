# Handoff — Mesh material completion + pink/blue dream ramp + new Kenney packs (2026-08-14)

**Pick up:** `Saved/Audit/{flat_mi_consolidation,art_mesh_texture_routing,cathedral_routing,kenney_new_import,retro_material_routing,kenney_texture_mis,pinkblue_dream_apply,instance_policy_apply,loose_mesh_material_fix2..5,library_mi_reparent_routing,kit_fallback_routing,dead_mi_deletion_2026-08-14}.json`

**Editor:** one UnrealEditor (verify with `Get-Process UnrealEditor`, never trust a PID written here), Monolith `:9316` answering. A D3D12 bindless-descriptor crash killed the earlier session mid-policy-sweep (17:50); the editor was relaunched 14:08 and all passes below re-ran cleanly to completion. A second crash hit 20:30 after the dead-MI deletion completed (audit already written) — the editor was relaunched and continues to boot; the deletion is disk-verified.

---

## 2. Layer-A / noise-rendering sweep (the "still wrong" fix)

The 08-13 routing pass only fixed meshes under `<prop>/StaticMeshes/`; the flat root-level stems (`bed`, `bathroomCabinet`, `arrow`…) still pointed at `_Loose/MI_*` shells with `TextureWeight=1.0` but **no Albedo override** — they rendered the master's noise texture. Fixed in rounds:

| Round | What | Count |
|---|---|---|
| `fix_loose_mesh_materials` | flat-root meshes → shared FlatColors MIs / colormap MIs | 1,024 slots |
| `fix_loose_mesh_materials2` | Library props (SM_*) + colliders/helpers → real `MI_M_*` or flat tint | 50 |
| `reroute_retro_materials` | RetroFantasyKit — canonical GLB material→texture map (`bricks→cobblestoneAlternative`, `stones→cobblestone`…) | 38 fixed + 184 ok |
| `fix_loose_mesh_materials3` | Room* CrystalCrossroads floors + AvatarGarden Palette/Foam (imported the 2 missing AG textures) | 20 |
| `fix_library_mirror_materials` | `/Game/Library` mirror meshes → EnvSandbox `MI_M_*` | 47 |
| `route_library_mi_textures` + `reparent_library_mis` | Library `MI_M_*` were parented to stub `M_*` masters (BaseTint only) → **reparented to `M_Master_Toon_Universal`** + routed `T_*_Base/AO/Normal` + `LayerA_TextureWeight=1.0` | 51 |
| `fix_loose_mesh_materials4/5` | Room16B, SM_Desk2/Wick/Outside_Wall, Melodia helper primitives (Cable/Cube/Cylinder_BS → flat) | 9 |

**Result: 3,859 mesh material slots → 0 noise-rendering, 0 null.** The only remaining "flagged" MIs are authored lookdev (Baroque/Zen fractional TW, Escher procedural) or dead assets — no mesh renders the noise default.

## 3. Kit-folder fallback routing (`route_kit_fallback_materials`)

| Kit | Before | After |
|---|---|---|
| OrnamentMusical (7) | `MI_Env_MusicalInstruments` (shared pack) | each slot → its local `M_Musical*` MI by slot name (`M_MusicalDiv`, `M_MusicalCyan`, `M_MusicalPearlJewel`, `M_Orn_Base`) |
| Ornament (15) | `MI_Env_MedievalBuilder` (KayKit) | new `MI_Ornament_GoldTrim` (Universal parent: gold BaseTint 0.92/0.75/0.42, Metallic 0.65, GildingStrength 0.8, dream ramp) |
| Celestial (6) + MathStructures (2) | `MI_Universal_IridescentShell` (concrete albedo) | new `MI_Celestial_Space` (deep-space BaseTint, Iridescence 0.8, Sparkle 0.4, CelestialStar 0.5, dream ramp) |
| Orrery (2) | `MI_Universal_IridescentShell` | `MI_Celestial_Space` (same family) |
| WPTerrains (4) | `MI_Universal_Default` | `MI_Flat_stone` (flat tint — placeholder terrain) |

Kept intentional lookdev: Celestial rock isles on `SurrealRocks/MI_Material`, Math Lissajous/Trefoil on `MI_Baroque_GildedFiligree`.

## 4. Dead-MI cleanup (`delete_dead_mis`)

**558 MIs deleted** (AssetRegistry zero-referencer proof per asset, 0 kept):
- 499 orphaned `_Loose/MI_*` shells (meshes repointed by rounds above)
- 59 superseded AvatarGarden `MI_<Mesh>_Art` (replaced by per-slot MIs)

Disk-verified: `_Loose` 856→357, AvatarGarden `MI_*_Art` 258→199. Manifest: `dead_mi_deletion_2026-08-14.json`.

---

## 5. Neutral-map sweep (`route_neutral_maps`)

**Deep audit finding:** every mesh-referenced MI with `TextureWeight=1.0` + real Albedo inherited the master's noise defaults (`sbs_-_` abstract/gradient/Perlin/Cracks + SDF Marble) on `NormalMap`/`ORM`/`HeightMap`/`RoughnessMap`/`MetallicMap` — each sampled once in the master, so textured surfaces carried abstract noise maps.

**Fix:** imported 5 neutral utility textures (`/Game/EnvSandbox/Textures/Utility/T_Neutral_{Normal,ORM,Height,Roughness,Metallic}`, 4×4, sRGB off, nearest filter) and routed them onto **1,255 MIs** where the pack lacks a real map; where the pack HAS one (AvatarGarden atlas normals/metallics, GothicCastle), routed the real map (12 real routes). `EmissiveMap` → neutral black (no glow). Result: **0 textured MIs inherit noise defaults** (re-audited). LayerB/C/Stack2/3 defaults remain but are inert (`bLayer*_Active`/`bStack*_Active` all OFF — verified).

## 6. What landed this session

### A. Mesh → material completion (finishing the 2026-08-13 routing work)
| Item | State |
|---|---|
| **AvatarGarden texture routing** | **279 `_Art` meshes / 402 slots** routed to the pack's real PBR atlases (`/Game/EnvSandbox/Textures/PackTextures/AvatarGarden/`, 99 textures). Per-slot MIs created for multi-atlas meshes (`MI_<Mesh>_<Slot>`); single-slot keep `MI_<Mesh>_Art`. Albedo/NormalMap/MetallicMap + `TextureWeight=1.0`. 27 textureless slots (Atlas/Light/FX/Emisive…) got flat tints instead of the master's noise default. |
| **LunarYear textures** | 33 imported to `PackTextures/LunarYear/` (slot-aware sRGB; normal → TC_NORMALMAP). |
| **Flat-color consolidation** | **1,017 per-prop duplicate MICs → 37 shared MIs** at `Instances/Environment/FlatColors/` (`MI_Flat_<name>`). **All 1,017 deleted** after AssetRegistry zero-referencer proof (0 kept). 1,107 mesh slots re-pointed across 542 meshes. |
| **Flat MI material tuning** | 36/37 shared MIs got material-type PBR scalars (`Roughness`/`Metallic` per wood/metal/glass/grass/water…). |
| **Cathedral** | 41/41 meshes off the wrong `MI_Env_MedievalBuilder` → `MI_Cathedral_Stone`/`MI_Cathedral_Rock` using the real GothicCastle stone_wall PBR set (imported 9 maps). |
| **Library sweep** | 60 meshes verified: 0 fallback/null slots. |
| **Global health** | 2,188 Environment+Cathedral static meshes: **0 null material slots**. |

### B. Pink/blue ShadowDream ramp (owner direction: "for all materials")
- **Master defaults** (`M_Master_Toon_Universal`): `ShadowDreamStrength=0.3`, `ShadowSoftness=1.2`, `ShadowDreamTint=(0.82,0.45,0.68)`, Ramp/ShadowRamp Low=(0.85,0.40,0.62) pink, Mid=(0.78,0.55,0.82) lavender, High=(0.60,0.78,0.95) sky blue. Recompiled + saved.
- **Policy v2 updated** (`specs/instance_parameter_policy.json`): new `melodia_shadowdream_pinkblue` palette; `shadowdreamstrength` 0.22 → **0.3**; ramp vectors → pink/blue.
- **Applied**: 1,136 instances / 12,189 params (`pinkblue_dream_apply.json`); policy sweep re-run (1,304 scanned / 3,824 params applied this pass — `instance_policy_apply.json` refreshed 08-14).

### C. Three new Kenney packs imported + materialized
| Pack | Content | State |
|---|---|---|
| `KenneyRetroFantasyKit` | 105 meshes, 10 shared textures | **105/105 meshes** (92 flat + 13 name-collision meshes under `Meshes/Environment/RetroFantasyKit/` to avoid clobbering existing `fence/roof/wall/…`). **222 slots routed / 0 unmatched** → per-slot MIs `RetroFantasyKit/Materials/MI_<mesh>_<slot>` with real pack albedo + `TextureWeight=1.0` + type roughness. |
| `KenneyRetroTexturesFantasy` | 117 albedo textures | **117/117** imported `PackTextures/RetroTexturesFantasy/` (sRGB on). **117 MIs** created `Instances/Environment/RetroTextures/` (Albedo + TW=1 + roughness hint). |
| `KenneyPatternPackExtra` | 84 patterns (Default) | **84/84** imported `PackTextures/PatternPackExtra/`. **84 MIs** created `Instances/Environment/PatternsExtra/`. |

All new MIs parent `M_Master_Toon_Universal` and received the pink/blue dream ramp (ShadowDreamStrength=0.3 verified by re-read).

---

## 2. Editor stability notes (learned the hard way this session)
1. **The 08-14 17:50 crash** was `D3D12BindlessDescriptors.cpp:248` (GPU descriptor heap) during the mass policy sweep — re-run cleanly after relaunch; batch saves (60/pause) kept the editor stable for the 1,136-instance dream pass.
2. **Asset names must not contain `.`** — `p.rsplit("/",1)[-1]` on asset paths keeps the `.AssetName` suffix. Creating `MI_foo.foo` pops a modal "Name may not contain the following characters: ." for **every** asset (201 dialogs). Fix: strip at `.`; never run unguarded name building without a dry-run.
3. `MODAL_OPEN` = dialog, not hang (AGENTS.md 8). A stuck modal can be dismissed with `AppActivate` + `SendKeys("{ENTER}")` per dialog.

## 3. Still open (owner-call)
- 13 retro-fantasy-kit meshes live under `Meshes/Environment/RetroFantasyKit/` (namespaced) because flat stems existed; consider folding into the retro theme scene explicitly.
- Retro textures are albedo-only (no normal/ORM in pack) — fine for stylized, but normal maps could be generated later if the toon look needs relief.
- AvatarGarden `Atlas`-slot props (Carpet/Poster/Table/Bell…) are flat-tinted; the pack ships `Panels.tif`/`Text_Backpanel.tif` if a closer match is wanted.
- No git commit was made this session (untracked `Content/` policy; ask before staging).
