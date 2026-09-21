# Brooch material-ID + UV / texel-density / UDIM architecture

2026-09-17 · STATUS: M1 LANDED (per-part material IDs in the builder + genome, verified by rebuild);
U1-U4 designed below and next in the build order. Same laws as the grandmaster plan: one geometry
authority (the builder), presets set values on builder-owned materials only, derived passes never
touch the live parametric object.

## 1. Material IDs — the per-part table

Goal: masks that a texture artist can address individually (enamel / engraving / wear / roughness
regions), without forking the material authority. The builder creates/updates these; the presets
(horizon-2 P2) only set values on them.

| ID | parts | why a separate mask | falls back to |
|---|---|---|---|
| `MID_Metal_Petal` | crown + inner whorl petals | the enamel/engraving canvas; biggest surface | `MID_Petal` |
| `MID_Metal_Dome` | dome boss + boss cap | brushed-vs-polished separation on the heart | `MID_Petal` |
| `MID_Metal_Body` | plate, step, collar, pave seats | structural metal; matte/brushed family | `MID_Petal` |
| `MID_Metal_Setting` | bezel ring, gem cups, socket rim/cup, claws | stone-setting masks + bright-cut/engraving | `MID_Petal` |
| `MID_Metal_Chain` | dangle chain links (tori) | different wear scale + polish; tiny islands | `MID_Petal` |
| `MID_Metal_Pin` | pin assembly (stem/hinge/clasp/jaws) | hidden-side material (steel/nickel) | (its own, existing) |
| `MID_Bead_Pearl` | centre pearl, accent pearls, dangle drops | pearl SSS + soft sheen | `MID_Bead` |
| `MID_Bead_Pave` | pave micro-beads (up to 128) | micro roughness/dirt masks | `MID_Bead` |
| `MID_Gem_<Element>` | gems (created in-tree per element) | unchanged gala scheme | — |
| `MID_Sparkle` | sparkle instances | unchanged (unlit) | — |

Reserved (NOT created yet, no consumer): `MID_Enamel` (inlay cells via Inset Face), `MID_Glint`
(deliberately left to the sparkle system).

**Laws.**
1. Copy-on-first-use: a genome naming an ID that does not exist in the file gets a copy of the
   fallback material, so every existing genome builds byte-identical until a preset differentiates.
2. Never overwrite an existing material — the builder only creates what is missing.
3. **Cast ON collapses the metal split**: the SDF voxel weld loses face material assignment, so the
   cast branch carries `MID_Metal_Petal` alone. This is why cast is a finishing pass, not a
   pipeline stage; the UV pass runs with cast OFF.
4. Genome block: `materials{petal, bead, pin}` stays for back-compat; new keys
   `metal_petal / metal_dome / metal_body / metal_setting / metal_chain / bead_pearl / bead_pave`
   are optional and fall back. Gala genomes adopt the split with a two-line genome edit when wanted.
5. `per_mat` in `BUILD_REPORT_V10.txt` is the live verification: it must print the new IDs with
   plausible dims per part.

## 2. UV / texel density / UDIM — the derived UV pass

**Architecture (mirrors the cast-bake precedent):** the live object keeps the cheap parametric path
(`Auto UV` OFF). A separate tool — `Tools/brooch_uv_pass.py` — consumes the builder's output and
writes a static deliverable object `FlowerBrooch_UV` (+ report). Paint/export happens on the
deliverable, never on the live GN stack. One writer per surface stays intact.

Pipeline stages:

    U1  apply + separate   evaluate the hero stack, apply to a static copy, separate by material ID
    U2  per-ID unwrap      policy per ID (below), seams placed where physically plausible only
    U3  pack per ID        pack_islands per ID (margin 0.5% of tile, rotation allowed, no overlap)
    U4  TD + UDIM          scale each ID's islands to the piece TD target, place into its UDIM tile
    U5  rejoin + report    rejoin to one mesh, write TD/island/occupancy report, gates below

**Per-ID unwrap policy**

| ID | method | seams |
|---|---|---|
| Metal_Petal | angle-based / SLIM | back midline of each petal + rim tail; never the front face |
| Metal_Dome | spherical (pole at the boss top) | hidden under the cap |
| Metal_Body | cylindrical/radial from the centre | plate under-edge + rear |
| Metal_Setting | angle-based after face split | inside the cups |
| Metal_Chain | per-link cylindrical | link joint (hidden when assembled) |
| Metal_Pin | angle-based | hidden side (rear) |
| Bead_Pearl | spherical per pearl | pole at the drill hole |
| Bead_Pave | spherical, atlas-packed | pole down |
| Gem_* | per-facet islands (cut-aware) | facet edges (deliberate) |

**Texel density law.** TD target per piece (`td_px_cm`, default **512 px/cm** at 4K = 0.0195 px per
µm of metal surface; hero 60 mm). Required UV area per ID = (3D area in cm²) × TD². Island scale is
set per ID so measured TD lands within ±10% of target; the pass reports min/avg/max TD per ID. A
piece whose metal group needs more than `tiles_metal` tiles (default 2 at 4K) must either raise the
tile budget or lower TD — decided by the report, never by eye.

**UDIM map (per piece, stable numbers, never renumbered once shipped):**

    1001  metal: petal + dome + body + setting + pin
    1002  chain
    1003  pearls: pearl + pave
    1004  gems
    1011+ next piece / next texture family

**Gates (the pass fails loudly, not silently):**
1. zero overlapping islands within a tile; margin uniform per ID;
2. no island crosses a tile border;
3. measured TD within ±10% of target for every ID (min must clear 0.9×);
4. UV-area vs 3D-area ratio per ID = 1.0 ± 0.1% (catches lost faces);
5. report: island count, occupancy %, TD table, tiles used — numeric, checked into the report file;
6. determinism: same input → same UV hash (pack seed fixed).

## 3. Interaction with the rest of the system

- Cast bake: cast ON collapses IDs (section 1 law 3) — UV deliverables are always built cast OFF.
- Sparkles/outline: not UV'd (unlit instances; toon shell gets a flat fill).
- The dangle object is UV'd as part of the deliverable (its chains are ID `MID_Metal_Chain`, drops
  `MID_Bead_Pearl`) — the pass evaluates body + dangles together.
- UE/wardrobe export stays parked; the deliverable + report is the artifact the export step will
  consume when the hook opens.
- Presets (horizon-2 P2) address IDs by name; the JSON rows gain per-ID keys
  (`metal_petal{...}`, `bead_pearl{...}`, ...) with role fallbacks so old rows keep working.

## 4. Order

    M1  material IDs in the builder + genome (fallbacks, copy-on-first-use)          <- LANDED
    U1  brooch_uv_pass.py stage A: apply + separate + per-ID unwrap + pack
    U2  TD equalization + UDIM placement + rejoin
    U3  report + gates wired into the run (numbers before renders)
    U4  DeepPaint/texture pass on the deliverable (per-ID masks), preset rows v2
