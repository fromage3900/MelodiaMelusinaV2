# Sea Above — Foliage, Exploration & Quest-Place Extension Plan (2026-09-03)

Extends SEA_ABOVE_FINAL_EXECUTION_PLAN (steps A-D) with the living layer:
foliage dressing, explorable areas, and physical homes for the already-authored
quest beats. Everything below is prep — editor is down (crash 19:25, no data
loss; restart before applying).

## What already exists (verified)

**Foliage authorities:**
- SpeedTree master PRESENT: `Content/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.uasset`
  — AGENTS.md names SpeedTree the core plant authority. Extend it, don't bypass.
- Megascans 3D_Plants: 74 presets on disk (AlexandraPalm, BeechFern, BostonFern,
  CustomMoss, CloverVarieties, ...) — the photoreal foliage tier for islands.
- L-system flora generators (hython, buildable): `build_dream_flora.py`
  (SM_Flora_GlassReed, ChimeBlossom, SpiralFern) — the toon-form flora.
- Reef kit: SM_Flora_Chime/Fern/Reed, SM_Kelp_* (already partially used).
- Proven ecosystem generator: `Tools/PCG/build_faraway_mother_pcg_ecosystem.py`
  (4-biome, tension-field, deterministic manifest -> apply pattern).

**Quest/narrative hooks (already authored, need locations):**
- `Content/MelodiaIntegration/Narrative/Shorewake/MelodiaQuillShorewake.qsc`:
  "Take the Shorewake Weave... board the Starskiff... anchored at the OVERLOOK
  MOORING" — names a destination not yet built/aesthetically dressed.
- `MelodiaQuillSeaAboveCutscene.qsc` — travel hook via `melodia:travel:`.
- 14 authored .qsc beats total; hooks: `encounter.shorelistener.reveal`,
  `reward.wardrobe.shorewake_veil`, `quest.p0_sea_above.veil_sung`,
  `flag.sea_above.starskiff_ready` (allowlisted notify verbs only).
- PlayerStart(0,0,13175) -> Quill(-910,500,13145) -> MusicKey(0,-950) ->
  Dock(-5099,5821,6270) is the playable loop.

## The three new layers

### L1. Foliage dressing (islands + palace environs)
- **Island flora** (Z > 13,455 cells, 909 grid cells above sea): Megascans
  3D_Plants on the photoreal tier — palms/ferns/brush on island slopes, density
  by phi falloff from the loop, height-aware raycast snap (BS_GodFile #2).
- **Palace environs**: enhance the existing 29 SM_ATL kitbash with SpeedTree
  trees + reef-kit SM_Flora_Chime/Fern along the walkway ribbon (path-adjacent,
  under the XylophoneTrail corridor).
- **Underwater foliage already in** (kelp/coral 136 pts) — no duplication.

### L2. Exploration areas (places to be)
Three destinations mapped to the story the qsc already tells:
1. **Overlook Mooring** (story-named: "anchored at the overlook mooring") —
   the Starskiff's dock platform + vista. Propose: dress the -5099,5821 area as
   a proper overlook (rocks, flora, a view axis to the silhouette ring).
2. **Shorewake Balcony** ("the high balcony... the tide in the sky") — a raised
   island-to-sea platform at a golden radius ~8k, Quill beat -> music-key
   resonance node, view back to the palace.
3. **Drowned Cathedral Tiers** (already exist: 24 music nodes at -45.3k/-14.6k)
   — the vertical mystery; the 12 jelly halo + garden beat already seed it.
   These become the "descend" beat of exploration, with the veil hooks
   (`quest.p0_sea_above.veil_sung`) firing there on resonance.

### L3. Quest placement (hooks get homes)
- Map each authored notify to a physical trigger:
  | Notify | Home |
  |---|---|
  | Shorewake weave grant | Quill beat at balcony (L2.2) |
  | starskiff_ready flag | Overlook mooring (L2.1) |
  | veil_sung flag | Cathedral tier resonance |
  | shorelistener.reveal encounter | ReefGarden edge ~2k from palace |
- Do NOT author new .qsc without the allowlist; reuse the 14 existing beats.
  Trigger placement is a level-actor concern (triggers), not new narrative.

## Asset rules (bind)
- SpeedTree = tree authority; Megascans 3D_Plants = photoreal bushes/ferns;
  L-system flora = toon-form flora. No new masters; AAA tier only.
- No new landscape; CanonicalLandscape only. Height-aware everywhere.
- Keep the loop walkable: foliage density by phi falloff, clear the ribbon.

## Next actions (after editor restart)
1. `Tools/PCG/build_sea_above_foliage.py` — island-foliage manifest from
   sea_above_layers.npz (Z>13455 cells), Megascans 3D_Plants + SpeedTree mesh
   refs, phi decay, height-aware. **DONE (prep)** — manifest
   `specs/water_veil/sea_above_foliage.v1.json` generated + verified: 86 pts
   (IslandFoliage 64 / BalconyFlora 12 / MooringDress 10), all in bounds.
   Full-map layers rebuilt at `Saved/Audit/sea_above_layers_full.npz` (3650
   above-sea cells).
2. **Apply-lane flag (editor decision):** the loop neighborhood (±13k) is 100%
   submerged — BalconyFlora/MooringDress points raycast to the DEEP canyon
   floor (-8k), not the waterline. The apply harness needs a waterline-snap
   mode for these two zones (snap Z to sea surface 13455 + clearance), or they
   must be placed on verified floating structures. IslandFoliage is safe
   (raycasts to real island land).
3. Verify the two destination sites by disk-level bounds (Overlook Mooring area,
   golden-radius balcony) and confirm they're inside the landscape.
4. Editor lane: apply foliage manifest (with waterline-snap for balcony/mooring),
   dress mooring/balcony, place trigger actors for the existing qsc beats.
   Reload-verify.
5. Record gate rows: `sea_above_foliage`, `sea_above_exploration`.

## Evidence
- Layers: `Saved/Audit/sea_above_layers.npz`; quest hooks: qsc files above;
  foliage assets: registry census (SpeedTree master, 74 Megascans plants,
  SM_Flora_* on disk). All verified before writing this plan.