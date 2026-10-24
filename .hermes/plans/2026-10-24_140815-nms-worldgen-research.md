# Research — No Man's Sky procedural workflows, mapped onto Melodia world-gen (2026-10-24)

**Trigger:** owner asked to research NMS procedural workflows and review existing parallel
docs/plans, in the context of converging the Houdini work into procedural systems for a
Melodia Melusina universe. Companion to the World Compiler terrain-stage work committed
`08a8dd0d6` (house HDA binding + planetary lab fold).

## 1. What No Man's Sky actually does (cited)

- **Deterministic seed cascade.** A single 64-bit seed per star drives everything: star
  position/class -> planetary system -> planet features -> terrain -> biome -> flora/fauna.
  The founding seed was a developer's phone number. Visit the same coordinates -> identical
  world, for any player. (Wikipedia "Development of No Man's Sky"; TechTimes 2026-08-10)
- **Terrain = fBm + domain warping.** Layered Perlin/Simplex noise (fractal Brownian motion).
  NMS goes further with *domain warping* — its "uber noise" — sampling noise at coordinates
  displaced by another noise field, plus ridge filters and sparing real-elevation (DEM)
  blending. This is what gives caves/overhangs and the twisted, tectonic look.
  (dev.to/kartikay; github dandrino/terrain-erosion-3-ways)
- **Flora = L-systems.** Grammar rewrite (axiom -> production rules -> turtle-graphics moves),
  coupled with SpeedTree for variety. (Wikipedia; NMS Fandom "Procedural generation";
  generalistprogrammer.com)
- **Fauna = part library.** Interchangeable body parts scaled and recolored by seed;
  behaviours derived from bone scale (gait, voice pitch). (NMS Fandom; Grant Duncan)
- **Biome rules.** Temperature/humidity/elevation decide palette + spawn; a custom colour
  palette matches flora/fauna to terrain and atmosphere. Determinism != human predictability.

## 2. What Melodia already has — three stacked layers

- **World Compiler (offline, deterministic).** A recipe IS an NMS-style seed cascade:
  identity -> place -> field -> species -> palette -> signal, with **per-chunk sub-seeding**
  (`stable_seed` per chunk, `shared_border_signature` for chunk edges) = NMS's "infinite tiled
  chunks from one seed." Byte-reproducible. Live for Melusina's Morning + Faraway Mother.
- **UE PCG (runtime scatter).** `.hermes/plans/2026-09-24_184500-pcg-convergence-plan.md`:
  L0 primitives / L1 data (`PDA_Vegetation` DAs, `PCGExMeshCollection`) / L2 recipes / L3
  hosts (PCGVolume, Blueprint, World Compiler manifest). MassiveBiome scatter + PCGEx layout
  = NMS "biome rules + part-library scatter" at runtime.
- **Houdini HDAs (DCC authoring).** `Docs/Art/FARAWAY_MOTHER_PROCEDURAL_INVENTORY_2026-10-17.md`
  maps terrain/silk/island/cathedral/house kits; now recipe-wired (this session).

## 3. NMS technique -> Melodia analog -> status

| NMS technique | Melodia analog | Status |
|---|---|---|
| Seed cascade + chunk streaming | World Compiler identity + chunk manifest | LIVE / proven |
| Biome rules (temp/humidity/elev -> palette) | palette bands + chladni + species dressing | LIVE / proven |
| Fauna part-library (scale/recolor) | species meshes + variants + scale_range | LIVE / proven |
| Flora L-systems | `build_dream_flora.py` + GN builders | direction exists; no single canonical builder |
| Terrain fBm + domain warping | `Content/Python/planetary_field.py` = single-scale sin/cos | GAP (deliberately minimal) |

## 4. Verdict

The architecture already IS an NMS-style deterministic procedural universe — we converged on
the same design independently, so NMS is a reference, not a migration. The one place NMS is
meaningfully richer is **terrain density**: fBm octaves + domain warping + ridge filters.
`planetary_field.py` (this session) is the minimal faithful extract of the old lab, so it reads
flat/periodic next to NMS terrain.

## 5. Chosen next step (bounded, no new system)

Add fBm (multiple octaves) + domain warping to `planetary_field.py` as a **v2 field**, sharing
the v1 mask vocabulary and the same compiler stage. `version` selects v1 (default, byte-faithful
to the lab) or v2; still fully seeded and deterministic. Highest-leverage NMS import; lands
directly in the compiler stage. Do NOT spawn a second terrain generator — extend the one.
