# GOAL — Massive World biome spawner live in Melusina's Morning (2026-09-24)

**Bounded:** today. One Massive-driven biome volume live in `L_MelusinaMorning`, skinned with Melodia assets, PIE-proven and saved. Supersedes the G1–G6 staging order in `2026-09-24_173839-massive-world-pcg-port.md` for this run.
**Owner:** license paid (entry staged by owner in `Docs/CREDITS.md`); owner OK to integrate live in Morning (2026-09-24).
**Ground truth (live read 2026-09-24):** Morning is World Partition, 226 actors, **no Landscape**; ground is `StaticMeshActor`s plus `Morning_SheepDell_Lake` (Oceanology). So the pack's landscape tools (river, lake, cliff, RVT road, stamps) are out; the biome/vegetation spawner is in, projected onto static-mesh ground.

## Steps

### M1 — Stage the pack in place (no second editor)
- Extract `Content/Massive/**` from the archive into `BS_GodFile/Content/Massive/` — the vendor's own `/Game/Massive` path, so references stay valid and future Fab updates drop in over it. `Content/*` is gitignored, so the whole pack stays out of git until M6 picks the subset.
- UE 5.8 loads 5.5 assets forward. No bulk loading: the demo map (53 MB, ~600 MB textures) is not opened.
- **Gate:** the Asset Registry sees the pack; the kept PCG graphs (`MassiveShared/PCG/*`, `MassiveWorld/PCG/PCG_Biome_3_0`, `Functions/*`) and `DA_DemoVegetation` load with zero errors in the log.

### M2 — Melodia biome data
- `DA_Melodia_MorningBiome` duplicated from `DA_DemoVegetation`, re-pointed to Melodia meshes only: `GenericFlower`/`GenericFlowerTall` (existing meadow MIs), rainbow SpeedTree B0–B6, the existing rock set. Materials stay MIs of existing masters. No new masters.
- Lives in `/Game/Melodia/PCG/MassiveBiome/`.
- **Gate:** the DA has zero references into `/Game/Massive/**` render assets.

### M3 — Static-mesh ground adapter
- `PCG_Melodia_MassiveBiome` in `/Game/Melodia/PCG/MassiveBiome/`: samples the volume, projects onto static-mesh ground (world ray hit / surface sampling of ground actors — no landscape), then runs the pack's spawner subgraph (`PCG_Spawner` / `PCG_VegetationTransform`, slope/fertility functions) with `DA_Melodia_MorningBiome`.
- The vendor graphs are called, not edited.
- **Gate:** generates in the editor on a small test volume with Melodia meshes only; PCG graph errors = 0.

### M4 — Live in Morning (additive only)
- Add one `PCGVolume` `Massive_Biome_Meadow` over Morning's meadow ground, graph `PCG_Melodia_MassiveBiome`, generate on load. Existing 13 PCG components untouched.
- **Gate:** instances land on the ground (no floaters, none in the lake); lit PIE proof on Morning (four views); save the level; verify `__ExternalActors__` mtimes moved (WP save trap).

### M5 — Record
- `CURRENT_STATE.md` entry; audit JSON + stills in `Saved/Audit/massive_morning_20260924/`.

### M6 — Commit (owner OK per commit)
- Commit the Melodia assets, the Morning external actor, and the vendor subset the Melodia graph hard-references (force-add from `/Game/Massive/`), checked by reference viewer: no committed asset references an uncommitted one. Docs/CREDITS entry present.

## Not in this goal
River/lake/cliff/road/stamps (need a landscape; roads also need `r.VirtualTextures` in protected `DefaultEngine.ini`); `PCG_RuntimeBiome`; the Morning audit findings (greybox rocks, coral field, dead volumes) — owner decisions; the pack's controller/game mode, textures, demo map.
