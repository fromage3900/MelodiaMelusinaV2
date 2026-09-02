# Sea Above — Mesh Assembly Review + Atlantis Kitbash Plan — 2026-08-29

Companion to `SEA_ABOVE_SECOND_OCEAN_LAYOUT_AND_CAMERA_PLAN_2026-08-29.md` (perception rules,
camera, second-ocean geometry). This one is the **asset inventory and the placement plan**.

---

## 1. Last night's authored meshes — and the headline

**36 mesh assets + 9 material instances + 3 VDB volumes were authored on 2026-08-28/29.
Zero of them are placed in `LV_SeaAbove_Prototype`.**

The only mesh content in the level is `SeaAbove_Island_01_Keel`, which is a Megascans
`SM_MassiveSandstoneCliff_03` — not part of last night's work. Everything below is built,
materialled, and sitting unused.

### Reef kit — `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/`

| Group | Assets | Material | Placed |
|---|---|---|---|
| Coral | `SM_Coral_Staghorn`, `_Table`, `_TubeSponges`, `_Fan`, `_Brain`, `_ReefCluster` | `MI_SeaAbove_CoralSkin` / `_CoralSkin_2S` (Fan needs 2-sided) | ✗ |
| Clutter | `SM_Clutter_PebbleSet`, `_Starfish`, `_SpiralShell`, `_SeaWeed` | `MI_SeaAbove_Sand` / `_CoralSkin` | ✗ |
| Kelp | `SM_Kelp_Tall`, `_Mid`, `_Cluster` | `MI_SeaAbove_Kelp` (2-sided, KelpSway WPO) | ✗ |
| Islands | `SM_Island_A`, `_B`, `_C` (r ≈ 6/4/8 m domes with hanging drips) | `MI_SeaAbove_WetRock` | ✗ |
| Rocks | `SM_RockChunk_M`, `_L` | `MI_SeaAbove_WetRock` | ✗ |
| Flora | `SM_Flora_Chime`, `_Fern`, `_Reed` | `MI_SeaAbove_Kelp` | ✗ |
| Cloth (skeletal + physics assets) | `SM_Banner`, `SM_Shroud` | `MI_SeaAbove_Cloth_Banner` / `_Cloth_Shroud` | ✗ |
| Jellyfish | `JELLY_Bell` (skeletal, morphs `PulseContract`/`PulseExpand`/`SurrealLurch`), `JELLY_Arms` (8 ribbons ≈ 320 m each), `JellyArm_001..007`, `JellyVeil` | `MI_Jelly_Bell` / `MI_Jelly_Arms` | ✗ |
| Terrain | `SM_SeaAbove_LiquidCathedral_257` | `MI_SeaAbove_LiquidCathedral_Substrate` | (mesh-partition) |
| Wardrobe | `SK_ShorewakeDress` | `MI_Melusina_Dress_Shorewake` (assigned 2026-08-29 evening; was auto-import `Material_001`) | ✗ |
| Volumes | `VOL_GhostFog`, `VOL_GodRays`, `VOL_NebulaVeil` (.vdb + .uasset) | — | ✗ |

### Still not imported

`SM_Leviathan.obj` and `SM_DrownedOrgan.obj` still have no `.uasset` (mesh imports remain).
Their six textures WERE imported 2026-08-29 evening (commit `2c201fe3`) with correct flags, and
their material instances exist and are waiting: `MI_SeaAbove_Leviathan_Bone`,
`MI_SeaAbove_Organ_Pipe`. This supersedes `SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29` §6.

---

## 2. The Atlantis kit

`Content/EnvSandbox/Meshes/Atlantis/` — **333 meshes**, 424 textures, 83 material instances.
KitBash3D `ATL`, single set: **BldgLgPalace_A**. A drowned-palace kit, which is exactly the
register the bible asks for.

| Structural | Count | Set dressing | Count | Organic | Count |
|---|---|---|---|---|---|
| Columns | 24 | Planter | 23 | Shrubs | 24 |
| Building | 16 | Bench / Benches | 19 / 8 | Tree | 19 |
| Guardrail | 10 | Stool | 15 | IvyHanging | 13 |
| Arch / Arches | 9 / 2 | Vase / Vases / DecorativeVase | 11 / 5 / 4 | TreeTop | 10 |
| DoorLeft / DoorRight | 8 / 8 | Table | 10 | TreeBottom | 7 |
| Base / BaseColumns | 7 / 3 | Barrels / BarrelRack / Barrel | 4 / 4 / 1 | IvyWall | 3 |
| Stairs / Steps | 6 / 3 | Torch | 5 | | |
| Roof / RoofTiles | 5 / 1 | Ornaments | 5 | | |
| Niche | 5 | Drain | 5 | | |
| Pergola | 4 | Banner | 4 | | |
| Dome | 3 | Chair | 3 | | |
| Floor | 3 | Basket | 2 | | |
| Fountain | 3 | Harp / GrapesStand / HayStack | 1 each | | |
| Columnade | 2 | | | | |
| Cornice | 1 | | | | |

### It covers four of the bible's five required kits

The design bible §01 lists the required environment kits for Sea Above. Mapping:

| Required kit | Source |
|---|---|
| coastal ruins | Atlantis `Building` / `Arch` / `Columns` / `Roof` / `Cornice` / `Base` / `Stairs` |
| inverted wreck set | Atlantis structural pieces gravity-flipped, plus `IvyHanging` (13 pieces already authored to hang), `Banner`, `Torch` |
| gravity-safe shrine markers | Atlantis `Niche` / `Fountain` / `Torch` / `Ornaments` |
| floating debris / fish schools | Atlantis `Vase` / `Barrel` / `Basket` / `Stool` + `SM_Clutter_*` |
| membrane traversal kit | **not Atlantis** — `JELLY_Bell` + `M_SeaAbove_Membrane_Prototype` |

The level title is *"The Inverted Pelagic Cathedral."* A palace kit hung upside down beneath a
false sea is the literal reading of that title, and `IvyHanging` means the kit already ships
pieces authored for the inverted orientation.

---

## 3. The constraint that governs every placement

From the layout plan §5, the veto rule:

> **Nothing may be visible touching both the real ocean and the false ocean in the same frame.**

Atlantis architecture is the single biggest violation risk in the whole level. A drowned colonnade
rising from the seabed, through the water surface, into the air is *exactly* the measuring stick
that collapses the second-ocean illusion — it hands the player a known-height object spanning both
surfaces and lets them solve the depth in one glance.

So placement is banded, and **nothing crosses a band boundary**:

| Band | Z range | Contents |
|---|---|---|
| **A — Above the real ocean** | Z > +55 | Landscape, islands, reef above waterline, full Atlantis ruins. A waterline here is fine — it is the *real* ocean's waterline, which is honest. |
| **B — The gap** | +55 → −5000 | **EMPTY.** Water only. No geometry, no debris, no columns, no kelp tall enough to reach. This emptiness *is* the illusion. |
| **C — Below the false ocean** | Z < −5000 | The inverted cathedral. Atlantis rotated 180°, hanging. Read dimly through the false ocean. |

Band B being empty is not a stylistic preference — it is the mechanism. Every other decision in
this document is negotiable; that one is not.

Corollary: **kelp height is capped.** `SM_Kelp_Tall` is a 2 m ribbon, so it is safe anywhere in
Band A. Do not scale kelp or coral up into Band B to "fill" the water column.

---

## 4. Assembly by level beat

Following the bible's progression (A → E). Beats D and E are later work.

### A — Calm littoral (Band A, near the player start)
Landscape + `SM_Island_A/B/C` + `SM_RockChunk_M/L` on `MI_SeaAbove_WetRock`; reef floor from
`SM_Coral_*` and `SM_Clutter_*`; `SM_Kelp_*` in the shallows; `SM_Flora_Fern/Reed/Chime` at the
tideline. Atlantis enters here only as **fragments** — half-buried `Base`, a toppled `Columns`,
one `Cornice` in the sand. Ruin, not architecture. Teach the anomaly softly, per the bible.

### B — Split-horizon coast (the hero vista, Shots A–C)
The Atlantis `Columnade` / `Arch` / `Guardrail` pieces do their real job here: **framing**. Stand a
colonnade at the overlook so the second horizon is seen *through* a repeating vertical rhythm —
columns give the eye a foreground scale reference that is unambiguously in Band A, which
paradoxically makes the false ocean *less* measurable, because the player anchors scale to the near
architecture and then has nothing to anchor to in the distance.

`Torch` and `Banner` (and `SM_Banner`, the skeletal cloth) go here — they read wind, and wind that
does not match the water's motion is a cheap, strong anomaly cue.

### C — Hanging wreck field (Band C)
The inverted cathedral. Atlantis structural pieces rotated 180° about X or Y, hung beneath the
false ocean, with `IvyHanging` trailing *upward* toward it. Debris (`Vase`, `Barrel`, `Basket`,
`Stool`) suspended in contradictory gravity states, per the bible's beat C. Density falls off fast
with distance — attenuation kills it, so only the near cluster needs to exist.

### D — Bell membrane region
`JELLY_Bell` (skeletal, morph-driven) + `JELLY_Arms`. Sits with the Bell re-seat from the layout
plan §4.3. Not this pass.

---

## 5. Order of work

| # | Step | Why here |
|---|---|---|
| 1 | Confirm the landscape's real bounds and sea-level intersection | Every placement is relative to where land meets water. Nothing can be placed sensibly before this. |
| 2 | Verify `SeaAbove_FalseOceanPlane_Prototype` and the hero-camera fix survived the map transition | Both were unsaved when the world closed — see §6. |
| 3 | Beat A: reef + islands + rock + kelp + flora, on the landscape | Largest visual return, zero illusion risk (all Band A). |
| 4 | Beat B: Atlantis colonnade / arch framing at the overlook | The hero shot is the gate; frame it before dressing it. |
| 5 | Beat A dressing: Atlantis ruin fragments, half-buried | Cheap, and it establishes the ruin vocabulary. |
| 6 | Beat C: inverted Atlantis cluster in Band C | Needs the false ocean confirmed and the absorption tuned first. |
| 7 | Import `SM_Leviathan` + `SM_DrownedOrgan` + 6 textures | Currently the only hard asset gap. |
| 8 | Place `VOL_GhostFog` / `VOL_GodRays` / `VOL_NebulaVeil` | Atmosphere last — it should respond to the composition, not lead it. |

Steps 3–5 are all Band A and carry no risk to the second-ocean illusion, so they can proceed while
the absorption/depth question from the layout plan is still open.

---

## 6. Open / at risk

- **The world closed with unsaved changes.** `SeaAbove_FalseOceanPlane_Prototype` (spawned this
  session) and the `CINE_SeaAbove_HeroReveal_Prototype` transform fix were both unsaved when the
  editor world went to `None`. Re-verify both before assembly; re-create if lost (spec is in the
  layout plan §4 and §6.2).
- `SK_ShorewakeDress` is on `Material_001`, a raw auto-import material. Needs a real assignment.
- `SM_Banner` / `SM_Shroud` were moved off the `MI_SeaAbove_Kelp` placeholder onto
  `MI_SeaAbove_Cloth_Banner` / `_Cloth_Shroud` at 01:37 — verify that stuck.
- See §7 — the Atlantis readiness audit is now done, and the kit is **not** placement-ready.
- The two `MI_SeaAbove_*_Oceanology` instances remain read-only on disk (closeout §5.6).

---

## 7. Atlantis readiness audit — measured 2026-08-29

All 333 static meshes loaded and read in-editor. Raw rows: `Saved/Audit/sea_above/atlantis_mesh_audit.json`.

| Property | Result | Verdict |
|---|---|---|
| Nanite enabled | **0 / 333** | **Blocker for mass placement** |
| LOD count | **1** on every mesh — no LOD chain | **Blocker** — no distance fallback and no Nanite either |
| Simple collision | **0 / 333** — no collision primitives anywhere | Blocker for anything walkable |
| UV channels | 1 (UV0 only) | see below |
| `LightMapCoordinateIndex` | **1** — points at a UV channel that does not exist | Harmless here: `r.AllowStaticLighting = 0`, the project is fully dynamic (Lumen). Do not "fix" it. |
| Material slots | 1,213 total; median 3.6, **max 21 on a single mesh** | Draw-call risk |
| Triangles | **9,676,792 total**; median 8,018; **max 1,106,869 (`ShrubsA`)** | With no Nanite and no LODs, this is full cost at every distance |

### What this means

Placing this kit as-is puts up to 9.7 M triangles on screen with **no LODs and no Nanite** — every
piece renders at full density regardless of distance, and a single dressed courtyard could carry
several hundred draw calls from the material slots alone.

The fix is cheap and it is the right one: **enable Nanite across the kit.** These are rigid static
architectural pieces, which is the exact case Nanite is built for, and it removes the missing-LOD
problem at the same time (Nanite does its own clustering). The foliage pieces — `ShrubsA` at 1.1 M
tris and the `Tree*` family — need a second look, because Nanite + masked foliage materials has real
caveats; those may be better served by conventional LODs or by being swapped for the project's own
foliage.

Collision must be generated for anything the player can reach. Band C (the inverted cathedral,
below the false ocean) is pure background and can stay collisionless.

**Recommended order:** enable Nanite on the non-foliage pieces → generate simple collision only on
the pieces that get placed in Band A → then dress. Do not mass-place before the first step.

### Note on the audit's cost

Reading these properties required loading all 333 meshes, which forced a first-time static-mesh +
distance-field + mesh-card DDC build (~4 minutes, editor peaked around 16 GB). That build was going
to be needed before placement regardless, so it is paid forward rather than wasted — but future bulk
audits should batch the loads rather than doing the whole kit in one pass.
