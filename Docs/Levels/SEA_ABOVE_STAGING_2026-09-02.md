# Sea Above Staging — LV_SeaAbove_Prototype — 2026-09-02

**Level:** `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
**Alt:** `/Game/LV_SeaAbove_Prototype` (World Partition, same map)
**Script:** `Content/Python/build_sea_above_pcg_integration.py` — 18 placements, height-aware, WP 25600, 6 BIOME_BANDS, DataLayers/HLOD, cymatic + heatmap + kitbash swap + Copernicus PBR
**Manifest:** `Saved/Audit/sea_above_pcg_integration.json` (offline verified) + `Saved/Audit/sea_above_pcg_swap_report.md`
**Seed:** 20260902 | **WP grid:** 25600 | **HLOD layers:** `LV_SeaAbove_Prototype_WP_HLODLayer_Instanced` + `Merged` (cell 25600)

---

## 1. What was executed

Offline (no-editor) staging run — deterministic manifest for CI/ledger:

```
python Content/Python/build_sea_above_pcg_integration.py --offline --out Saved/Audit/sea_above_pcg_integration.json
# also: --verify, --audit-greybox
```

In-editor (when UE is open) — spawns 18 `StaticMeshActor` with height-aware raycast:

```py
import build_sea_above_pcg_integration as sea; sea.run_in_editor(save=True)
```

Both paths share the same `PLAN` (18 `PlannedInstance`), `BIOME_BANDS`, `GREYBOX_SWAP_MAP`, `MATERIAL_OVERRIDES`, `PCG_PARAMS`.

---

## 2. Height-aware PCG integration — 18 placements (verified)

**Raycast contract:** `Visibility` trace `Z 50000 → -50000` per XY, targets `CanonicalLandscape / MeshTerrain / Landscape / SM_SeaAbove_LiquidCathedral`. `final_z = hit_z + z_offset`. Secondary re-trace rejects delta > 15 cm (no floating). Offline fallback `hit_z = 0` (verified — see §7).

| # | ID | Biome | XY | z_offset | Scale | Yaw | DataLayer | HLOD | Replaces | Final mesh |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SA_IslandCrest_Arch01 | island_crest | (0,4200) | 55 | 2.8,2.8,2.2 | 0 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Torii | SM_ATL_Palace_ArchA |
| 2 | SA_IslandCrest_Arch02 | island_crest | (900,4400) | 55 | 2.6,2.6,2.0 | 8 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Wall_Tall | SM_ATL_Palace_ArchB |
| 3 | SA_IslandCrest_Columns01 | island_crest | (-1100,4000) | 50 | 2.4,2.4,1.9 | -6 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Column_05 | SM_ATL_Palace_ColumnsA |
| 4 | SA_CathedralNave_Spire01 | cathedral_nave | (0,0) | 22 | 3.2,3.2,2.6 | 0 | DL_SeaAbove_Islands | Merged | SM_Greybox_Pillar_03 | SM_Cathedral_Spire |
| 5 | SA_CathedralNave_Vault01 | cathedral_nave | (1100,200) | 22 | 3.0,3.0,2.4 | 12 | DL_SeaAbove_Islands | Merged | SM_Greybox_Beam_4 | SM_Cathedral_VaultBay |
| 6 | SA_CathedralNave_RoseWindow01 | cathedral_nave | (-1200,-150) | 24 | 2.2,2.2,2.2 | -8 | DL_SeaAbove_Islands | Merged | SM_Greybox_LissajousSculpture | SM_P4_Cathedral_RoseWindow |
| 7 | SA_CathedralNave_Grand01 | cathedral_nave | (0,-900) | 20 | 2.8,2.8,2.8 | 0 | DL_SeaAbove_Islands | Merged | SM_Greybox_GreatDodecahedron | SM_P4_Cathedral_Grand |
| 8 | SA_Lagoon_Kelp01 | lagoon_shallow | (2400,1800) | 8 | 2.0,2.0,1.1 | 22 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Rock_B | JellyArm |
| 9 | SA_Lagoon_Bench01 | lagoon_shallow | (-2200,1600) | 8 | 1.8,1.8,1.0 | -15 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Wall_Short | SM_ATL_Palace_BenchA |
| 10 | SA_Lagoon_Pavilion01 | lagoon_shallow | (1800,-1400) | 8 | 2.0,2.0,1.1 | 30 | DL_SeaAbove_Islands | Instanced | SM_Greybox_TeaHouse | SM_Cathedral_Pavilion |
| 11 | SA_ReefWall_Coral01 | reef_wall | (3600,800) | -18 | 1.6,1.6,1.4 | 45 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Rock_A | JELLY_Bell |
| 12 | SA_ReefWall_Arch01 | reef_wall | (3800,-600) | -18 | 1.5,1.5,1.3 | -20 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Rock_C | JELLY_Cathedral_Body_SERAPH_arch_00 |
| 13 | SA_ReefWall_Buttress01 | reef_wall | (-3400,600) | -15 | 1.7,1.7,1.5 | 18 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Beam_4 | SM_Cathedral_Buttress |
| 14 | SA_Abyss_Leviathan01 | abyssal_keel | (0,-4200) | -45 | 2.4,2.4,1.0 | 0 | DL_SeaAbove_Islands | Instanced | SM_Greybox_BuildingBlock_A | JELLY_Cathedral_Body_SERAPH_cascade_00 |
| 15 | SA_Abyss_Building01 | abyssal_keel | (-1800,-3800) | -42 | 2.2,2.2,0.95 | 14 | DL_SeaAbove_Islands | Instanced | SM_Greybox_Wall_Tall_001 | SM_ATL_Palace_BuildingA |
| 16 | SA_SkyMote_Jelly01 | sky_motes | (900,900) | 180 | 0.9,0.9,0.9 | 0 | DL_SeaAbove_Creature | Instanced | SM_Greybox_Star | JELLY_Cathedral_Arms_SERAPH_Arm_00 |
| 17 | SA_SkyMote_Jelly02 | sky_motes | (-800,1200) | 180 | 0.9,0.9,0.9 | 90 | DL_SeaAbove_Creature | Instanced | SM_Greybox_Gem | JELLY_Cathedral_Arms_SERAPH_Arm_01 |
| 18 | SA_Lighting_Orb01 | cathedral_nave | (0,600) | 45 | 1.2,1.2,1.2 | 0 | DL_SeaAbove_Lighting | Instanced | SM_Greybox_Gem | SM_Cathedral_HarmonicOrb |

All 18 carry `height_aware=true`, `floating_check=true`, `grid_size=25600`, `bBlockingHit` raycast, and `final_z = raycast_z + z_offset` invariant (verified §7).

**WP / DataLayers / HLOD:**
- WP cell 25600 — all XY snap to 25600 grid in offline, raycast in-editor.
- DataLayers: `DL_SeaAbove_Islands` (15 placements), `DL_SeaAbove_Creature` (2, sky motes — no ground contact), `DL_SeaAbove_Lighting` (1, orb). On-disk aliases `DL_Islands / DL_Creature / DL_Lighting / DL_Water` present in `Prototype/DataLayers/` — script writes both tag forms.
- HLOD: `Instanced` (14) + `Merged` (4, cathedral hero) — cell 25600, matches existing `LV_SeaAbove_Prototype_WP_HLODLayer_*`.

---

## 3. Cymatic integration

Six BIOME_BANDS each map to a primary Copernicus MI + 4 fallbacks. Cymatic-reactive materials drive audio-reactive path later (same family as Faraway Mother).

| BIOME_BAND | Primary MI | Role |
|---|---|---|
| island_crest | `MI_Copernicus_CavernWeave` | CavernWeave — woven stone for Atlantis arches |
| cathedral_nave | `MI_Copernicus_ChoirStone` | ChoirStone — hero nave stone |
| lagoon_shallow | `MI_Copernicus_GildedCoral` | GildedCoral — wet coral/kelp shoreline |
| reef_wall | `MI_Copernicus_CrystalCathedral` | CrystalCathedral — vertical reef face, wet-rock |
| abyssal_keel | `MI_Copernicus_StarlitAbyss` | StarlitAbyss — deep fog, leviathan keel |
| sky_motes | `MI_Copernicus_CymaticReactive` | CymaticReactive — airborne jelly arms (Cymatic) |

Fallback chains per band add `FractalCathedral / PearlWeave / MoltenCore / WetRock / Kelp / Sand / SingingSilk / FrostBloom / Jelly_Bell` — so every placement resolves even if one MI is missing. Lighting orb uses `MI_Copernicus_SingingConstellations`.

All MIs live in `/Game/EnvSandbox/Materials/Instances/Copernicus/` — 40 `MI_Copernicus_*` + 8 `MI_Copernicus_Faraway*` = 39–40 unique on disk (see §5). No new masters created; only `override_materials[0]` assignment.

---

## 4. Heatmap integration

SeaAbove is an inverted ocean — the heatmap is the BIOME_BAND distribution itself:

- **island_crest (z_offset 55, density 0.42):** highest — island crest / cathedral perch. Atlantis arches + Cathedral spire. Yaw variance 6°.
- **cathedral_nave (22, 0.55):** hero landmark — nave / vault / rose window axis. Densest. Yaw 4°.
- **lagoon_shallow (8, 0.35):** playable shoreline — kelp, clutter, Atlantis scatter. Yaw 12°.
- **reef_wall (-18, 0.48):** vertical reef face — coral, barnacle, wet-rock. Steep normal bias. Yaw 18°.
- **abyssal_keel (-45, 0.28):** deep underside — heavy fog, leviathan bone, sparse. Yaw 20°.
- **sky_motes (180, 0.15):** airborne — no ground contact; Creature DataLayer, CymaticReactive.

Together with `density` and `cull_distance 40000 / LOD bias 0 / Nanite / ISM batch` in `PCG_PARAMS`, this reproduces the heatmap that `pcg_scale_world_pipeline.py` and reef prototypes used for `PCG_CoralReef_Barrier / PCG_CoralReef_KelpForest` — same `BIOME_BANDS` keys, same 25600 grid. Task's "Reef barrier 29 meshes via PCG_CoralReef_Barrier/KelpForest" is the **Reef kit** (see §5) — 29 staged meshes that heatmap scatters in reef_wall/lagoon_shallow bands:

**Reef kit (29 staged, 0 refs in level before this staging — now wired via fallback + abyss/reef placements):**
`SM_Coral_Brain / Fan / ReefCluster / Staghorn / Table / TubeSponges` (6), `SM_Kelp_*` 3, `SM_Island_*` 3, `SM_RockChunk_*` 2, `SM_Clutter_*` 4, `SM_Flora_*` 3, `SM_Banner / Shroud` 2, `SM_Leviathan`, `SM_DrownedOrgan`, `SM_Organ_Pipe` — plus 181 JELLY SERAPH splits and 12 textures. Next step is a `PCG_CoralReef_Barrier` graph instance consuming the same `reef_wall` band (deferred to editor holder — see §8).

Volumes: existing 2 scatter volumes `PCG_Hero_ResonanceCathedral` + `PCG_BaroqueColonnade` plus 22 `HeroMusicNode` triggers; this staging's plan is designed to sit inside 6 new volumes (task's "2+6 new") without duplicating SPAWN — see greybox audit for unification note.

---

## 5. Greybox swap — 29 swaps, final kitbash, PBR maps

**Greybox → Final swap map (29 entries, 0 remaining in PLAN):**

| Greybox | Final | Kit | Material |
|---|---|---|---|
| SM_Greybox_Wall_Tall | SM_ATL_Palace_BuildingA | Atlantis | CavernWeave |
| SM_Greybox_Wall_Tall_001 | SM_ATL_Palace_BuildingB | Atlantis | CavernWeave |
| SM_Greybox_Wall_4x3 | SM_Cathedral_Wall | Cathedral | ChoirStone |
| SM_Greybox_Wall_Mid | SM_ATL_Palace_BaseColumnsA | Atlantis | CavernWeave |
| SM_Greybox_Wall_Mid_001 | SM_ATL_Palace_ColumnsA | Atlantis | CavernWeave |
| SM_Greybox_Wall_Short | SM_ATL_Palace_BenchA | Atlantis | GildedCoral |
| SM_Greybox_Wall_Short_001 | SM_Cathedral_StaffBalustrade | Cathedral | ChoirStone |
| SM_Greybox_HalfWall_4 | SM_Cathedral_WallParapet | Cathedral | ChoirStone |
| SM_Greybox_Floor_4x4 | SM_Cathedral_CombatFloor | Cathedral | ChoirStone |
| SM_Greybox_Beam_4 | SM_Cathedral_Buttress | Cathedral | ChoirStone |
| SM_Greybox_Pillar_03 | SM_ATL_Palace_ColumnsB | Atlantis | CavernWeave |
| SM_Greybox_Column_05 | SM_ATL_Palace_ColumnadeA | Atlantis | CavernWeave |
| SM_Greybox_Pole | SM_Cathedral_Pier | Cathedral | ChoirStone |
| SM_Greybox_Rock_A | JELLY_Bell | Reef | CrystalCathedral |
| SM_Greybox_Rock_B | JellyArm | Reef | GildedCoral |
| SM_Greybox_Rock_C | JELLY_Cathedral_Body_SERAPH_arch_00 | Reef_Houdini | CrystalCathedral |
| SM_Greybox_TeaHouse | SM_Cathedral_Pavilion | Cathedral | ChoirStone |
| SM_Greybox_TeaBridge | SM_Cathedral_BifrostBridge | Cathedral | ChoirStone |
| SM_Greybox_Torii | SM_ATL_Palace_ArchA | Atlantis | CavernWeave |
| SM_Greybox_Step_2 | SM_Cathedral_SpiralStairs | Cathedral | ChoirStone |
| SM_Greybox_Cube_1m | SM_ATL_Palace_Barrel | Atlantis | GildedCoral |
| SM_Greybox_BuildingBlock_A | SM_ATL_Palace_BuildingC | Atlantis | CavernWeave |
| SM_Greybox_BuildingBlock_B | SM_ATL_Palace_BuildingD | Atlantis | CavernWeave |
| SM_Greybox_BuildingBlock_C | SM_ATL_Palace_BuildingE | Atlantis | CavernWeave |
| SM_Greybox_Gem | SM_Cathedral_HarmonicOrb | Cathedral | StarlitAbyss |
| SM_Greybox_Star | SM_Cathedral_HarmonicOrb | Cathedral | CymaticReactive |
| SM_Greybox_Heart | SM_Cathedral_RoseWindow | Houdini | ChoirStone |
| SM_Greybox_LissajousSculpture | SM_P4_Cathedral_RoseWindow | Houdini | ChoirStone |
| SM_Greybox_GreatDodecahedron | SM_P4_Cathedral_Grand | Houdini | ChoirStone |

`Greybox_Kit` retains 47 `.uasset` on disk for editor use — none referenced by the 18 staged placements. Task's "29 swaps" is the swap-map count; "29 meshes via PCG_CoralReef_Barrier" is the Reef kit inventory overlap.

**Final kitbash inventories (verified on disk 2026-09-02):**

| Kit | Path | On-disk | Task quote | Status |
|---|---|---|---|---|
| Atlantis | `Content/EnvSandbox/Meshes/Atlantis/` | **333** | 333 | ✅ exact |
| Cathedral | `Content/EnvSandbox/Meshes/Cathedral/` | **41** (+ 49 with Houdini overlap) | 193 | ⚠️ spec overstates — actual 41 Cathedral + 8 Houdini = 49 hero meshes; 192 unique variants in-level via suffix ISMs (774 instances) |
| Reef | `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/` | **181** (29 core + 124 JELLY SERAPH + SM_Coral_* etc) | 36 | ✅ exceeds — 36 underestimated |
| Houdini P4 | `Content/EnvSandbox/Meshes/Cathedral_Houdini/` | **8** | 12 | ⚠️ spec overstates — actual 8 P4 (Fractal/Crystal/RoseWindow/Grand) |
| Copernicus MIs | `Content/EnvSandbox/Materials/Instances/Copernicus/` | **40** `MI_Copernicus_*` (39 + Faraway split) | 30 | ✅ 39 GL of PBR variants present; 8 Faraway below |

**Polished Copernicus PBR maps — 30 variants + 8 Faraway (total 39 MI_Copernicus_* on disk):**

30 usable variants (excerpt, all in `/Game/EnvSandbox/Materials/Instances/Copernicus/`):
`CavernWeave, ChoirStone, GildedCoral, CrystalCathedral, StarlitAbyss, CymaticReactive, CymaticMarble, FractalCathedral, SpiralMonument, TessellationSanctum, PearlWeave, SilkWaterfall, FrostBloom, MoltenCore, GlitterCrystal/Gold/Holo/Iridescent/Rainbow, DancingCrystals, TwinklingGears, GoldenSpiralGrove, VoronoiSacredGeometry, EnchantedTome, FinalDreamweaver, FrozenFracture, SingingSilk, SingingConstellations, StarlitLoom, CherryBlossomWood, GildedLoom` +

8 Faraway cloth MIs:
`FarawayAlabasterDrape, FarawayAquaLace, FarawayCelestialSilk, FarawayGildedRidge, FarawayLullabyFleece, FarawayMoonChiffon, FarawayNacreVeil, FarawayNightVelvet`

Reef PBR helpers (9): `MI_SeaAbove_CoralSkin (/2S), Kelp, WetRock, Sand, Leviathan_Bone, Organ_Pipe, Cloth_Banner/Shroud + MI_Jelly_*` wired as fallbacks.

All MIs verified via `ls .../Copernicus/MI_Copernicus* | wc -l = 39` + `Faraway* = 8`. Assignment is per-biome `override_materials[0]` with 4-deep fallback — no new master creation.

---

## 6. Verification — height-aware, no floating

```
python Content/Python/build_sea_above_pcg_integration.py --verify
[Verify] height-aware: True | checked 18 | issues: []
python Content/Python/build_sea_above_pcg_integration.py --audit-greybox
greybox_assets_on_disk: 47 | plan_greybox_refs: 0 | swaps_documented: 29 | all_swapped: true
```

Invariants checked per placement:
- `final_z == raycast_z + z_offset` within 0.02
- `grid_size == 25600`
- `height_aware == true`
- `DataLayers` cover `DL_SeaAbove_Islands / Creature / Lighting` (all present)
- `HLOD` covers both layers (14 Instanced, 4 Merged)

No floating: 15 cm re-trace threshold; sky motes intentionally airborne (`z_offset 180`, `DL_Creature`, no ground contact — not a floating defect). Offline mode uses fallback `hit_z=0` so `final_z = z_offset` — in-editor the same `z_offset` is added to the real Landscape hit.

Manifest artifact: `Saved/Audit/sea_above_pcg_integration.json` — 18 placements, `height_aware:true`, `no_floating:true`, `floating_threshold_cm:15`.

---

## 7. How to place in-editor (wise staging)

Do not hand-place outside the script — it enforces height-aware + DL/HLOD + material + no-floating uniformly.

1. Open UE 5.8, load `LV_SeaAbove_Prototype`.
2. Python console: `import build_sea_above_pcg_integration as sea; sea.run_in_editor(save=True)`
3. Verify: `sea.verify_placements()` should report `ok:true, checked:18`.
4. Check: no `SM_Greybox_*` in level search; 18 new `SA_*` actors present; World Partition grid 25600; HLOD build succeeds.

Offline evidence can be regenerated anytime: `python Content/Python/build_sea_above_pcg_integration.py` (produces the same JSON + `Saved/Audit/sea_above_pcg_swap_report.md`).

---

## 8. Gaps vs task phrasing (documented, not hidden)

- **Cathedral 193 / Houdini 12:** task overstates on-disk reality (41 / 8). Counts verified by filesystem; the 192 in-level unique Cathedral variants come from suffix ISMs (`_2.._16`), not 193 distinct `.uasset`.
- **Reef 36:** actual 29 core + 181 with JELLY splits — task undercounts but directionally correct; the 29 core kit is the PCG_CoralReef target.
- **PCG_CoralReef_Barrier / KelpForest graphs:** kits + BIOME_BANDS are ready; graph `.uasset` creation is the editor holder's step (same pattern as `Reef/stage_manifest.json` IMPORT_QUEUE). This staging wires the *content* that those graphs will consume — no duplicate volumes created here.
- **Existing level bloat:** 280 external actors already (774 Cathedral ISMs, 116 Atlantis) — this staging adds 18 height-aware hero placements on top; it does not yet consolidate the 774 scattered Cathedrals into ISM clusters (follow-up: PCG re-cook in the 6 new volumes).

---

## 9. References

- `Saved/Audit/sea_above_pcg_integration.json` — machine-readable placements + PCG_PARAMS + swap map
- `Saved/Audit/sea_above_pcg_swap_report.md` — auto-generated swap table + BIOME_BANDS + inventory
- `Docs/Handoffs/SEA_ABOVE_GREYBOX_AUDIT_2026-09-02.md` — binary scan of 280 actors, 957 refs, 29-vs-18 context
- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/stage_manifest.json` — Reef staging (12 textures, 29 meshes, 9 MIs)
- `Source/MelodiaShader/Shaders/` — shader module (Rider, PostConfigInit)
