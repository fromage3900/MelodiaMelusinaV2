# WP PCG Greybox Plan: Infinity Nikki Lens

## Purpose

This is the greybox contract for the four World Partition pillar levels. PCG
should establish a readable traversal spine, a few legible destination moments,
and safe dressing zones before high-detail set dressing begins. The player must
always be able to answer three questions: where am I going, what can I walk on,
and what is worth looking at.

The plan follows the strongest open-world lessons visible in Infinity Nikki:
exploration and platforming are primary verbs, outfit abilities should reveal
new traversal possibilities, and landmarks carry the story of the world rather
than being buried under decoration. These are design translations for this
project, not claims about Infold's internal tools.

## Production Rules

- Greybox graphs use the live-tested library first. Experimental `*Ex`, room,
  and gravity graphs remain optional dressing passes until their inputs are
  explicitly authored.
- Reserve a continuous primary route at least 450 cm wide for Melusina's
  420 cm/s movement. Use 700 cm at encounter approaches, camera reveals, and
  NPC gathering pockets.
- Keep a 350 cm clear radius around landmarks, encounter triggers, NPCs,
  player starts, jump/landing spaces, and camera hero lines.
- Apply a 250 cm exclusion band along the primary route and a 150 cm band on
  secondary paths. PCG scatter must consume these masks before density is
  increased.
- Use three density bands: route 0-0.15, destination 0.25-0.45, background
  0.55-0.75. Never solve visual richness by filling the route band.
- Place tall silhouettes at route turns and horizon breaks, not at random
  intervals. Every major vista gets one dominant landmark, two supporting
  forms, and a quiet foreground frame.
- Keep hero, collision, and PCG ownership separate: terrain/blockout owns
  walkability; PCG owns dressing; set dressing owns authored focal assets.

## Pillar Assignments

### SakuraDream: blossom promenade

**Aesthetic:** warm spring meadow, shrine-garden rhythm, soft pink/green
contrast, gentle discovery.

**Greybox spine:** `PCG_GreyboxBlockout` plus `PCG_MeadowFalloff`.

**Best candidates:** `PCG_BlossomPath`, `PCG_SakuraGrove`,
`PCG_Sakura_PetalDrift`, `PCG_MeadowBloom`.

**Layout:** one readable blossom path from arrival to shrine; a pond or meadow
rest pocket off the route; one elevated shrine reveal visible from the first
turn. Keep petal drift and grove dressing outside the path mask.

**Set-dress handoff:** torii/shrine hero, two bridge variants, low blossom
clusters, NPC social pocket, and one optional photography overlook.

### SpaceCathedral: celestial nave and sky bridges

**Aesthetic:** cool cosmic cathedral, vertical awe, controlled impossibility,
clear silhouettes against a deep sky.

**Greybox spine:** `PCG_RockScatter`, `PCG_GardenRuins` using the WP mesh-
sampled variants.

**Best candidates:** `PCG_FloatingStairways`, `PCG_PenroseShrine`,
`PCG_BridgeArchipelago`. `PCG_CathedralNave`, `PCG_EscherDecks`, and the
generic greybox graphs remain reference candidates but were empty in the
current WP volume context; they are excluded until their input contract is
fixed.

**Layout:** a grounded nave route first, then two optional sky-bridge loops.
Every gravity/height change needs a visible landing and a return route. Keep
the central aisle clean so the player can read the cathedral scale immediately.

**Set-dress handoff:** nave landmark, bridge rails, constellation panels,
landing platforms, low-risk photo overlook, and a clear ability-gated shortcut.

**Avoid in greybox:** `PCG_EscherRelativityRoom`, `PCG_EscherRecursiveRoom`,
and other room/gravity experiments until their authored inputs and recovery
routes are tested.

### BaroqueGrotto: ruin garden into wet cavern

**Aesthetic:** romantic overgrown ruin, dark-to-luminous progression, moss,
stone, and one high-contrast magical interior.

**Greybox spine:** `PCG_BaroqueRuins`, `PCG_Cloister`.

**Best candidates:** `PCG_BaroqueColonnade`, `PCG_OvergrownRuins`,
`PCG_GardenRuins`, `PCG_RockScatter`, `PCG_WallMoss`, `PCG_WallLichen`.

**Layout:** broad ruin approach, compressed colonnade, then a luminous grotto
chamber. Use the transition as pacing: the player should see the warm exit
before entering the dark space. Wall ivy/lichen must respect door, camera, and
NPC exclusion masks.

**Set-dress handoff:** entry arch, broken columns, wet rock framing, luminous
crystal destination, safe rest pocket, and a readable combat clearing.

### CosmicOrrery: orbit garden and observatory

**Aesthetic:** midnight observatory, orbital motion, sparse luminous props,
quiet negative space around the hero view.

**Greybox spine:** `PCG_EscherDecks` plus `PCG_FloatingStairways`.

**Best candidates:** `PCG_PenroseShrine`, `PCG_BridgeArchipelago`,
`PCG_LanternGrove`, `PCG_GardenRuins`, then the dedicated
`PCG_Cosmic_OrbitScatter` only after an isolated generation test.

**Layout:** a grounded garden ring, one observatory destination, and an orbit
loop that reads as optional rather than mandatory. Keep the central sky view
open; orbital scatter belongs on the perimeter and in controlled bands.

**Set-dress handoff:** orrery hero, low lantern grove, star-map panels,
perimeter ruins, two readable landing points, and a quiet photo platform.

## Walkability / Heatmap Pass

For each level, author or verify these masks before generating detail:

1. `WP_PrimaryRoute`: arrival to destination, 450-700 cm wide.
2. `WP_SecondaryRoutes`: loops and NPC/collection branches, 300-450 cm wide.
3. `WP_Landings`: 700 cm clear circles at jumps, bridges, and vertical reveals.
4. `WP_EncounterClear`: 900 cm clear circles around combat triggers.
5. `WP_LandmarkClear`: 350 cm clear radius around authored focal assets.
6. `WP_NoScatter`: union of the above plus camera sightline masks.

Heatmap review gates:

- **Green:** route has continuous ground/nav support and no PCG points in the
  exclusion mask.
- **Amber:** density touches the route edge, sightline, or landing margin;
  reduce density before set dressing.
- **Red:** route is blocked, a landing lacks a return path, or a landmark is
  occluded from its intended approach; do not dress the level yet.

The existing `pcg_heatmap_exporter.py` is the editor capture path. The existing
`audit_pcg_heatmap.py` is a presentation fallback, not authoritative spatial
proof; it synthesizes density when the audit contains no point coordinates.

The current verified density handoff is generated with:

```powershell
python Content/Python/generate_wp_setdress_handoff.py
```

It writes one JSON contract and one SVG density plate per pillar under
`Saved/Audit/WP_SetDress/`. These plates show relative PCG density and route
clearance rules for manual set dressing. They do not claim navmesh reachability
or capsule clearance; those remain explicit in-editor gates before a graph is
approved for playtest.

The structural greybox spine is authored with:

```powershell
py Content/Python/setup_wp_human_scale_blockout.py
```

This creates an intentionally plain 300 cm corridor with 240 cm clear height,
then a 1200 x 900 cm destination hall at 360 cm clear height. Actors are tagged
`WP_PrimaryRoute`, `WP_NoScatter`, `WP_LandmarkClear`, or `WP_EncounterClear` so
the heatmap and set-dressing passes have explicit semantic anchors. Evidence is
written to `Saved/Audit/wp_human_scale_blockout.json`.

The WP graph chain is now `VolumeSampler -> DataFromActor(PCG_Exclude) ->
Difference -> Transform -> Spawner`. This makes the heatmap mask a spatial
input to the graph while preserving populated output; the older point-tag
filter path was rejected because it culled the entire stream in UE 5.8.

The actual procedural corridor rails are placed with:

```powershell
py Content/Python/build_pcg_human_scale_corridor.py
py Content/Python/setup_wp_human_scale_pcg_rails.py
```

The two rail volumes sit at `X=-165` and `X=+165`, `Z=120`, and generate
one-metre grid points through the level spine. Their 30 cm greybox walls leave
300 cm of clear player lane and 240 cm of clear vertical space. Evidence is
written to `Saved/Audit/wp_human_scale_pcg_rails.json`.

The first editor navigation probe is stored at
`Saved/Audit/wp_navigation_probe.json`. It currently reports no nav projection
at the sampled PCG centers, so the four levels are **not yet walkability-green**.
Each level does contain a `NavMeshBoundsVolume`; the remaining investigation is
whether the greybox terrain has usable collision and whether Recast is actually
building tiles inside those bounds. Repair terrain collision or navigation build
settings, then rerun `Content/Python/audit_wp_navigation.py` before approving
route dressing.

`repair_wp_terrain_collision.py` now restores the terrain actor contract for
all four pillars: each `Terrain_<Pillar>` actor references its authored mesh
and uses `QueryAndPhysics` / `BlockAll`. A direct UE 5.8 probe verified a
three-point, 1,200 cm SakuraDream route after a settled full nav build. The
same settled per-level probe now also verifies SpaceCathedral (1,600 cm),
BaroqueGrotto (1,600 cm), and CosmicOrrery (400 cm). The probe must use the
projected terrain endpoints; raw flat-Z endpoints can report false negatives on
the generated terrain. WP reloads can still discard Recast tiles, so rebuild
navigation after loading a pillar before sampling it.

The 250 cm primary-route width gate now passes on all four sampled spines:

| Pillar | Sampled route | Minimum measured width | Result |
|---|---:|---:|---|
| SakuraDream | 1,200 cm | 771.6 cm | Pass |
| SpaceCathedral | 1,600 cm | 1,000 cm | Pass |
| BaroqueGrotto | 1,600 cm | 1,000 cm | Pass |
| CosmicOrrery | 400 cm | 1,000 cm | Pass |

The authoritative settled nav route record is
`Saved/Audit/wp_navigation_verified_routes.json`; all four routes pass there.
Use `record_wp_nav_current.py` after loading and building a single WP level
when refreshing this evidence. This avoids the false-zero caused by unloading
Recast tiles while iterating through multiple World Partition maps.

CosmicOrrery's earlier scene census undercounted its streamed PCG actors. A
fresh explicit pillar verification now sees all 3 volumes populated with
3,063 instances, and the streamed scene census sees 3 PCG volumes and 3
terrain/static-mesh actors. Regenerate the handoff after any future PCG rebuild
so its density plate reflects the latest verified counts.

## Execution Order

1. Run `setup_wp_pillar_levels.py --pillar <name> --verify` and confirm the
   selected graph paths exist.
2. Generate only the greybox spine graphs in one level at a time.
3. Export the top-down heatmap and collision/nav report.
4. Walk the route with Melusina and mark blocked edges, camera occlusion, and
   unclear destinations.
5. Freeze route/exclusion masks.
6. Add secondary dressing graphs, then authored set dressing.
7. Run the level-specific hero capture only after the route remains readable.

Do not batch-generate all four levels in one editor session; the existing PCG
catalog documents async generation and memory pressure when many dense graphs
are generated together.

## References

- Project graph catalog: `Docs/PCG_CATALOG.md`
- WP builder: `Content/Python/setup_wp_pillar_levels.py`
- WP audit: `Content/Python/audit_wp_levels.py`
- Heatmap capture: `Content/Python/pcg_heatmap_exporter.py`
- Official Infinity Nikki open-world context: https://infinitynikki.infoldgames.com/en/news/442
- Apple/Infold open-world design discussion: https://developer.apple.com/news/?id=9mgkwjnm
- Unreal/Infold technical interview: https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-an-open-world-for-a-stylish-adventure/
