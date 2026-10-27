# RECEIPT — Faraway Mother dressing + water + materials (2026-10-27 evening)

Level: `L_FarawayMother_Blockout` (saved). All editor work via one Monolith lane.

## What changed (owner's 6-item list)
1. **4-biome cymatic dressing generated + visually verified.** 4,026 instances from
   `focus_authoring_fields.npz` + canonical `chladni_field` recompute; z-traced in-editor.
   Biomes: WeaveRidge (900 crystal tips), LaceCanopy (1,400 dwarf-sakura canopies),
   FrillValley (1,226 flowers/bushes), ResonantSeamWay (500 pearls). Route corridor excluded.
   Evidence: `Saved/Audit/Shots/dress_basin_to_couture.png`, `dress_village_court.png`,
   `dress_valley_2km.png` (pink fabric boulders + pearls read well).
2. **Artist-friendly control.** Combined graph replaced by 4 per-biome graphs
   (`PCG_FarawayDress_<Biome>_20261027`) on 4 actors (`Dress_<Biome>`, folder
   `FarawayMother/System04_Dressing`). Each biome is independently toggleable; generated ISM
   components are individually selectable/mesh-swappable per biome. Tunables (enable, density,
   scale, weighted mesh list) live in `Saved/Audit/tmp/dress_config.json`; rebuild via
   `Saved/Audit/tmp/rebuild_dress_split.py` (rerunnable, deterministic stride, seed 3900).
   Counts after rebuild: 900 / 1400 / 1226 / 500 — matches design.
3. **Infinity Nikki research brief** → `Saved/Audit/NIKKI_RESEARCH_BRIEF_20261027.md`.
   Key params adopted: pastel color-first family kept; sparse jewelry-scatter density
   (do-not-carpet); sky-reflective water; sparkle pass recommended next for pearl/crystal MIs.
4. **Water → oceanology hero.** 19 broken water slots (BLK_Waterfall A/B, rep'ed to
   `MI_Oceanology_Melodia_Hero` — `MI_BLK_Waterfall`'s parent was the engine BasicShape
   default). Level-wide audit: `Saved/Audit/tmp/water_audit.json`.
5. **Dead-material HDA fix.** 13 slots on `houdini_default_material` repointed:
   `HDA_Faraway_Village_Foundations_LIVE_20261026` → `MI_Village_chiffon`;
   `INTAKE_HDA_TerracedIsland_000..011` → `MI_Faraway_SilkMountain_Lilac`.
   NOTE: these are editor-side overrides; a recook rebuilds them — durable fix must set
   materials inside the HDAs (open item).
6. **Route proof.** `Saved/Audit/tmp/route_check.json`: 237/237 samples grounded across the
   6 legs of `LD_Faraway_PrimaryValley`; only foreign capsule hits are the cathedral HDA
   itself at the route's destination end (expected arrival contact). LD camera captures:
   `Saved/Audit/Shots/ld_CAM_FarawayLD_*.png` (cameras untouched).

## Also done earlier today
- Stale Terra `_20` frame removed (11 splines deleted from level).
- Canonical frame verdict recorded (hero landscape HDA + AlmostGate + village + cathedral).

## Open for next session
- Durable HDA-internal material assignment (item 5 note).
- Canopy proxy readability: LaceCanopy reads as white blossom clusters at distance (see
  BasinReveal shot) — looks intentional, but swap to sphere+emit fallback if owner dislikes.
- Iridescence/sparkle pass on pearl + crystal MIs per Nikki brief.
- Re-shoot canopy closeup after fog tuning (today's closeups were fogged out).
