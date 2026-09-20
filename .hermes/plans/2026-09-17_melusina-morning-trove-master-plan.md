# MELUSINA'S MORNING — THE TROVE MASTER PLAN (draft v1, 2026-09-17)

> **For Hermes:** this is the spine. Three sections are held open (`[[REVIEW: …]]`) until the
> three delegated reviews land: UE 5.8 engine truth, the Houdini↔PCG bridge, and the
> inventory/design brief. Do not close the plan before those are merged.
> Level of record: `/Game/Melodia/Levels/Opening/L_MelusinaMorning`.

---

## 0. The thesis — how a Nikki master would actually build this

A master does not decorate a room. A master builds a **curiosity engine**:

1. **A handful of authored, photographable "wow" compositions.** Nikki's open world is not
   uniformly beautiful — it is a chain of 20-40 hand-built moments that the procedural layer
   connects. Players remember the moments, not the density.
2. **A procedural envelope that makes the world feel endless.** The envelope is what lets the
   player believe the field continues past the camera. Its job is *credibility*, not detail.
3. **One living signal.** Everything breathes on the same music. Nikki couples cloth, wind,
   water and light into one readable pulse; the world feels alive because it is *synchronised*,
   not because it is animated.
4. **Exploration verbs as content.** In Nikki the outfit *is* the traversal kit. Melodia already
   has that seam (wardrobe Glide/Dash/Swim hooks, proven). The trove must reward the verbs the
   player owns, not the ones we wish they owned.
5. **Collectibles as breadcrumbs with a destination.** Motes on furniture tops, not motes in
   space. Every collectible should pull the player onto a surface we designed.

Applied to Melusina's Morning, the division of labour is:

```text
HOUDINI  = the pattern composer + the baker
           (Chladni eigenmodes, phyllotaxis, erosion, ribbons, point fields, Copernicus maps)
UE PCG   = the placement authority
           (spatial rules, density, culling, instancing, runtime generation)
MATERIALS= the signal readers
           (toon master Cymatic_* parameters -> emissive / iridescence / UV distortion)
PYTHON   = the pipeline glue + the proof harness
           (manifests, apply, reload proof, ledgers)
GAMEPLAY = the reasons to walk there
           (Quill triggers, Choral Sheep, wardrobe hooks, Dawnmotes, travel volume)
```

The rule that keeps it honest: **Houdini never places, PCG never invents, materials never write.**
Each layer owns one thing and reads the others.

---

## 1. The five signature moments (the trove)

| # | Moment | The shot | Systems it spends |
|---|---|---|---|
| 1 | **The Rainbow Bloom** — seven radial cymatic bands ringing the sheep-dell pond, each band a different Chladni mode, breathing on the beat | low dolly from the waterline, bands arcing to the rim | 7 × `MI_RainbowPetal_*`, toon master Cymatic_*, one PCG graph, one HISM per band |
| 2 | **The Listening Dell** — the amphitheater (bowl floor z −646, rim walk z +175) played as an instrument | wide from the rim looking down into the bowl | the live `PCG_Hero_ArpeggioBridge` (24 steps) + `PCG_Hero_BellTreeGarden` (36 nodes), rim-stone notes, choir stone |
| 3 | **The Wardrobe Threshold** — the wake-up corner as a photo-mode stage | over-the-shoulder from the bed, Sir's perch in frame | `Morning_Bed`, frozen PPV stack, ink V7.1, wardrobe hooks, `FX_Morning_Bed_PollenSparkle` |
| 4 | **The Climb** — vertical route bed → shelf → wardrobe-top → arch, with Dawnmotes as breadcrumbs | look-up framing from the floor | 7 Dawnmotes, `SM_Greybox_Wall_Window` ledges, wardrobe Glide as the reward at the top |
| 5 | **The Waterline Secret** — the pond edge at low angle: ghost lotus, crystal anemone polyps, water glint, the Slip of the Sky | macro, near-waterline | SurrealFlora bodies (ghost lotus 29 parts, siren kelp 59, crystal anemone 341 polyps), `FX_Morning_WaterGlint`, native `OceanologyLake` |

Non-negotiables from the owner's standing rules: **no new landscapes**, **height-aware placement
mandatory**, **delete greybox/proxy on sight**, **one writer per surface**, **single editor holder**.

---

## 2. Where Morning actually stands (evidence, not memory)

**Verified live on 2026-09-16/17** (all receipts in `Saved/Audit/`, study:
`melusina_bedroom_study_2026-09-16.json`):

- 241 actors. Shell is still Greybox_Kit (`SM_room_2`, `SM_wallhi_006`, 2 × `SM_Greybox_Wall_Window`,
  8 × `SM_classic_arch_20`), 19 greybox meshes total.
- The dell is the real work so far: **71 house-kit scatter actors** at true ground
  (`morning_house_dell.v2.json`), native `OceanologyLake`, ChoirStone pond bed, moonlit cobble
  terrace (real hython COP bake, 8 maps), 7 Niagara, 6 PointLights + Spot.
- **Navigation: added this session** — `NavMeshBoundsVolume` @ (−20, 1020, −300) extent
  (1950, 2193, 956), RecastNavMesh 60 tiles, saved. Route map: room strip z −586, dell band
  z −646, bed platform z −506.
- **Two dead route legs the nav pass exposed:** the exit volume (350, −670, −145) is 314uu
  off-mesh, and `Morning_QuillTrigger_P0` floats **728uu above** the dell floor. No path from
  P0 → exit, and `sheep → exit` is unreachable.
- The bed top is a walkable island ~1–1.4m above the surrounding floor with no link (fine for
  a bed, but it means every bed-anchored agent path is partial).
- **PCG:** 3 volumes; `PCG_Hero_ArpeggioBridge` (82 instances) and `PCG_Hero_BellTreeGarden`
  (27) generate; `PCG_Morning_MemoryDressing` contributes nothing.
  `PCG_MelusinaHouse_MorningDell` was rebuilt this session to **21 nodes / 14 edges** with the
  seven band payloads (mesh + per-band MI) and **now saves** — it previously could not save at
  all. Its missing hop is the branch→Output pin (not wireable from Python; see §3).
- **562 rainbow petals** were built and verified in-session and are the design of record for
  moment #1, but they did not persist (ISM created via `new_object` does not serialise) and the
  husks were removed. `rainbow_bloom_manifest.json` holds the numbers:
  R20 O68 Y75 G69 B86 I109 V135.
- PIE stills from 2026-09-16: 1 black frame, later frames with the camera inside bedding, and a
  Lumen exposure warning (−5.4 outside the safe range). Owner's eyes are the gate.

---

## 3. [[REVIEW: UE 5.8 ENGINE TRUTH]] — pending

To be filled from the engine-source review (`Saved/Audit/ue58_pcg_source_reference.md`).
Questions it must close before any Act 2 work:

- Why `add_edge` into `DefaultInputNode`/`DefaultOutputNode` silently no-ops from Python, and
  what the supported path is (editor pin drag only? a C++ entry point? a different graph shape?).
- Which 5.8 node classes can load external point data (Houdini CSV/JSON/point cloud) and what
  their exact settings are.
- The spatial controls that matter: point bounds/extents, `unbounded`, steepness, surface
  sampler parameters, bounds-based culling — i.e. the supported way to guarantee "never floats,
  never intersects vertical geometry, never blocks the route".
- Runtime generation options in 5.8 (`PCGComponentGenerationTrigger`, `PCGCompute`/GPU module)
  and whether the trove can generate on load inside budget.

---

## 4. [[REVIEW: HOUDINI ↔ PCG BRIDGE]] — pending

To be filled from `Saved/Audit/houdini_pcg_bridge_reference.md`. Contract to be frozen here:

```text
hython  -> point field (position, rotation, scale, band id, chladni mode, density)
        -> Copernicus maps (mode-indexed emissive / iridescence / normal)
        -> UE import -> MIs -> PCG payload -> generation -> proof
```

Open questions it must answer: the exact exporter for point data, the exact 5.8 loader node,
whether Houdini Engine cooks live in UE or stays an offline baker in this project (current
evidence says offline bakes imported as textures/meshes — confirm), and the PDG/TOP story if any.

---

## 5. [[REVIEW: INVENTORY + DESIGN BRIEF]] — pending

To be filled from `Saved/Audit/morning_trove_inventory.md`: the unrealised troves worth spending
(333 Atlantis meshes, 36 reef kit meshes, SurrealFlora bodies, CrystalTip variants, Niagara
library), the live-vs-hollow PCG gallery, and the 8–12 distilled Nikki design principles plus
the 10 highest-value things Morning does not yet have.

---

## 6. The acts (order of execution, each with a gate)

### Act 0 — close the loose ends (30 min, before anything new)
1. Owner drags the 7 spawner pins into the Output node in the PCG graph editor; Hermes then
   generates and reload-proves the count.
2. Delete the hollow twin `PCG_RainbowBloom_Test` (engine delete refused; needs a Content Browser
   right-click).
3. Repair the two dead route legs: lift the exit volume onto the mesh, drop the P0 trigger pad
   onto the dell floor, rebuild nav, re-prove with `morning_nav_route_proof` shape.
**Gate:** graph generates > 0 instances and survives a reload; the three nav paths return connected.

### Act 1 — Houdini authors the pattern (the trove's intellect)
1. Chladni band field: 7 concentric bands, each with its own mode (n,m), emitted as a point field
   with attributes `band`, `mode`, `density`, `scale`, `rot`.
2. A **migration** parameter: the band boundaries (and/or hue offset) drift slowly over the track,
   so the carpet rearranges rather than just pulsing.
3. Copernicus bakes per-mode maps (emissive/iridescence/normal) at 1–4K.
**Gate:** point field + 7 map sets on disk, with a bake receipt; a render of the field as points.

### Act 2 — PCG places it (the trove's body)
1. One graph, seven bands, all spatial rules from §3 switched on.
2. Hero-clearance mask around bed → the photo path; navmesh-clearance filter so scatter never
   blocks a proven route (the GAP-09 defect class, closed here).
3. One HISM per band; Nanite on the petal mesh; no per-instance lights.
**Gate:** manifest == apply == reload == commit; instance counts per band; PIE frame with the field.

### Act 3 — the signal (the trove's life)
1. Band MIs read the canonical palette (emissive scale, iridescence shift, UV distortion) —
   read-only, one writer stands.
2. Optional: rim stones (Listening Dell) ring on accent; dust motes rise on the beat.
**Gate:** a capture where the field visibly changes with the music, plus a grep proving no second
palette writer.

### Act 4 — the reasons to walk (the trove's pull)
1. Dawnmote breadcrumbs on *predicted* furniture tops (`predict_player_paths` / raycast survey).
2. Photo-mode pass: three hero framings measured with sightline analysis; verify the ink stack
   does not eat the petals.
3. The Climb: verify the glide reward actually lands (playtest, not a probe).
**Gate:** owner's eyes at the portfolio camera; a documented framing sheet.

### Act 5 — prove and publish
1. Full capture pass, ledger rows, `CURRENT_STATE.md` update in the same change.
2. A 60–90s capture for the reel + the Humber deliverable framing.

---

## 7. Rules this plan will not break

- One editor holder. No parallel MCP writer. Editor reads are cheap; every write is proved.
- No new landscape. Houdini dresses the existing floor; it never replaces terrain.
- One audio writer (`UMelodiaAudioReactivePresentationSubsystem`); `MelodiaCymaticsSubsystem`
  stays read-only; materials read, never write.
- Hero clearance beats density: the bed, the wake path and the photo framings stay clean.
- Greybox leaves as it is replaced, not after.
- Every claim carries a receipt path; "generated: true" with 0 instances is a defect, not a result.
- Never touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python.
- Houdini/Blender run headless (`--factory-startup`), never a GUI launched by an agent.

---

## 8. Open owner decisions

1. Scale of the trove: 5 moments as above, or a subset to protect the Choral Sheep lane?
2. Does the rainbow field live **around the pond** (current design, sheep-adjacent) or does it
   also thread through the room? (Different PCG volumes, different density story.)
3. Vendor water: native `OceanologyLake` stands, or the vendor BP lane revisited?
4. Is the greybox shell replaced this semester (Blender GN `GN_MH_ROOM_02_BedroomShell`) or does
   the trove ship on the greybox first, then re-dress?
