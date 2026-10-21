# Poitou × Melusina's Morning — House / Terrain / World Convergence

**Date:** 2026-10-20 · **Discovery:** `POITOU_START_HERE`, `POITOU_CONVERGENCE`, `Poitou`, `Marais Poitevin`, `Melusina's Morning`, `roof ribbon`  
**Entry:** [POITOU_START_HERE.md](../../POITOU_START_HERE.md)  
**Type:** executable creative convergence plan, **not a new status authority or engine**. Status remains in [CURRENT_STATE.md](../../CURRENT_STATE.md).  
**Objective:** one coherent, artist-approved and playable P0 opening environment. Protect completed generators; converge, stage, verify, capture.

> **Companion experience score:** [Poitou P0 Golden Walk (M00–M09)](POITOU_P0_GOLDEN_WALK_2026-10-21.md). This specifies the *bounded playable exploration route*; this document retains artistic / terrain / house convergence ownership. Preserve the separate existing First Dream golden-run contract.

## 0. Locked creative identity (the central decision)

**Poitou** is the new fictional art-direction name for the existing **Melusina's Morning** opening area, regionally rooted in **Poitou / Marais Poitevin (Venise Verte)**. Regionalism defines land, water, human craft, ecology and local atmosphere; **Melusina's own house keeps its established extravagant fantasy identity**. A French region does **not** mean every building becomes generic Haussmann/Parisian.

The original house silhouette is binding:
- round, asymmetrical **Borromini-inspired concave → convex entry → concave** façade; convex welcoming center, softer curved shoulders;
- **three overlapping scalloped/whale-back ribbon roof masses** (main, wing, porch), curled eaves, end lift, blue–lavender iridescent **overlapping shell shingles**, small decorated dormers;
- pearl-blush plaster, opalescent aqua/rose glass, ivory carved shells, delicate warm gold/brass, lavender fabric, warm honey-window light;
- deliberate **right-side Listening Tower**, curved/crescent stair and porch, shell-cap cresting, Rocaille C/S curves, fine pearls and restrained musical ornament;
- round resonant salon, music/prayer nook, kitchen/pantry, curved stair, writing/sleeping loft, lookout and acoustic gather/guide/release flow.

**Keep fantasy spectacle concentrated in the house and selective hero moments.** Poitou's context uses lower-saturation weathered Poitou limestone, flat barges, soft water, pollarded ash, grasses, duckweed, canals, moss, vernacular bridges and modest village architecture.

**Desired hero shot:** dawn canal approach → jetty/landing → shallow raised stone terrace → distinctive ribbon roofs peeking through ash trees; water reflection and gentle cymatic response introduce fantasy. One recognizable environmental identity, not seven unrelated biomes.

### Original design authority / evidence

These Sept 2–3 design packets were recovered from Git history, preserved verbatim as **historical concept / implementation memory**, not current builder-status claims:
- [House design master](../References/MelusinasHouse/OriginalDesign/melusinashouseplan_2026-09-02.md) — 13.2m × 9.8m working footprint, 3.42m wall baseline, 0.65m façade wave, 2.55m main roof rise, 0.28×0.36m shingle module / 40% overlap (artist-adjustable, not measured Poitou architecture);
- [House GN asset-family packet](../References/MelusinasHouse/OriginalDesign/MELUSINAS_HOUSE_GN_ASSET_FAMILY_IMPLEMENTATION_2026-09-03.md);
- [House rooms and acoustic plan](../References/MelusinasHouse/OriginalDesign/MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md);
- [Visual reference-board index](../References/MelusinasHouse/README.md). Full-resolution owner concept boards also exist in the originating ChatGPT artwork library.

**Rule:** original concept boards constrain style; [current Melodia House GN entry](../../MELUSINA_HOUSE_GN_START_HERE.md) and live source code constrain implementation. Historical `GN_MH_*` labels describe possible scene wrappers, not registered product IDs.

## 1. Existing system ownership — do not replace

| Layer | Canonical owner / interface | Preserve |
|---|---|---|
| World identity & provenance | [World Atlas](../WorldAtlas/README.md), `specs/world_atlas.v1.json` | `world_id: melusinas_morning` and UE path `/Game/Melodia/Levels/Opening/L_MelusinaMorning`; add display alias only with an explicit follow-up, no bulk rename |
| Game and save/narrative runtime | [World Building SSOT](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md); QuillScript/C++/JRPG | No new save, quest, combat, beat clock or gameplay-brain system |
| World planning | [Universe Foundry contract](../Production/UNIVERSE_FOUNDRY_CONTRACT.md) | Orchestration/mission planning; do not turn it into another generator |
| Deterministic compilation | [World Compiler contract](../WorldGen/WORLD_COMPILER_CONTRACT.md), [runbook](../WorldGen/WORLD_COMPILER_SESSION_RUNBOOK.md), `Tools/world_compiler.py`, `Tools/world_compiler_ue_driver.py`, `recipes/` | Existing `world_recipe.v1`, bundle, point-row schema and level anchor; compile CLI, consume in editor |
| Terrain authoring → UE | [Terrain handoff contract](../WorldGen/TERRAIN_HANDOFF_CONTRACT.md), `Tools/terrain_handoff.py`, [Mesh Terrain spec](../WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md) | `melodia.terrain_handoff.v1`, **UE 5.8 Mesh Terrain**, scale **100cm/m**, `classic_landscape_used=false`; do not silently create a fourth incompatible terrain lane |
| Houdini semantic fields | [Field Atlas Foundry plan](../Houdini/FoundryDay_2026-09-24/04_FOUNDRY_FIELD_ATLAS.md), `specs/houdini_foundry/field_atlas_channels.v1.json` | Reuse existing masks / manifest vocabulary; proposed HDA is **not** proof of shipped tool |
| House and procedural assets | [Melusina House GN](../../MELUSINA_HOUSE_GN_START_HERE.md), `deploy/surreal_arch/melodia_gn/`, `presets.py` | `MEL_mh_*` builders and verified `GN_PARIS_*` variants; wrappers only if scene composition requires them |
| Historical house production | [House final / Paris→Nikki plan](../../HOUSE_GN_FINAL_PLAN_2026-09-18.md), [Maison Impossible](../Production/MAISON_IMPOSSIBLE_2026-09-20.md) | Paris/Escher families are a *library*, not the Poitou art style; select only compatible curves, openings, trims, terraces and stone |
| UE world construction | existing World Compiler UE consumer, PCG graphs, material masters, Niagara/MPC writer contracts | No duplicate actor spawner, PCG framework, shader/MPC authority or live compile side channel |
| Heavy creative assets | Perforce / live UE / local Houdini & Blender WIP | Git source cannot prove local binary art exists or that a package was saved; audit each authority before claiming landings |

## 2. Current truth and unknowns — read before assigning work

At planning time, Git `main` head was `0c8c714` (Oct 16). **Verified on `main`:**
- `MEL_mh_foundation_*`, `MEL_mh_roof_ribbon`, `MEL_mh_opening_family`, `MEL_mh6_room_shell`, `MEL_melusina_house_round_interior` source and prior headless proof references; **do not rebuild**. Roof ribbon and Parisian variants are **owner-reported already finished**. Live scene fit and visual approval remain separate evidence.
- Parisian GN implementation files (e.g. `paris_wall_detail.py`, `paris_mansard.py`, `paris_common.py`, `paris_daynight_facade.py`) and [Maison Impossible brand record](../Production/MAISON_IMPOSSIBLE_2026-09-20.md); not all are appropriate to deploy in Poitou.
- `L_MelusinaMorning` World Atlas source and scoped World Compiler/PCG proof. **Do not** equate that with a Poitou terrain/world rebuild already landed.

**Not verified in searchable `main` as of this audit:** files explicitly named `Poitou`, `Poitou` or `Marais`; the new DEM/Houdini geometry, its precise coordinate contract, Grok agent staging and latest in-editor scene may be local, Perforce-owned or in unmerged work. **Do not discard, overwrite, or remake them.** First audit owner machine and agent lanes. A search miss is not a broken pipeline.

### Required input ledger (Luna owns; audit before mutation)

| Artifact to locate | Expected evidence | If missing on Git main |
|---|---|---|
| Two uploaded Marais Poitevin reference boards (environment + terrain) | original file locations, attribution/license, palette and visual annotations | Ask owner/Grok for exact source path; do not pretend Git contains them |
| Geospatial heightfield + source DEM | extent, sample grid, source URL/license, projected CRS, vertical datum (`NGF-IGN69` on preview), water datum, reprojection, XYZ min/max, geo-to-UE transform | Preserve local/Perforce producer and hashes; do not resample from screenshots |
| Grok Houdini graph and staged assets | HDA/hip path, node/parm manifest, cooks, output locations, checksums, owner and dirty-status | Reconcile one-way after source-of-truth check; never make a rival grandmaster |
| Existing house assembly, GN scripts and roof/shingle assets | blend name, source builder IDs, registered presets, visual screenshots, UE asset paths | Reuse; only isolated missing *composition* wrappers proposed |
| Parisian asset variants | real builder ID, module, preset, geometry screenshot, suitability | Curate, do not run entire Maison Impossible pack blindly |
| Current `L_MelusinaMorning` map and active local/Perforce assets | editor level, external actor changes, PCG graph identity, dirty package count | Leave original map alone until verified; Poitou remains a display alias |
| World recipe / compiled bundle / masks | `recipe_id`, stable seed, `place.level`, hash, terrain handoff, point schema | Extend valid existing recipe only with additive scoped change |

Ledger each item `FOUND / MISSING / STAGED / VERIFIED`, plus owner, exact path, SHA/hash, last cook, review image and next action. Never mark artist-approved from a successful headless test alone.

## 3. Luna — bounded **art direction + physical assembly**

**L0 · Discovery (read-only).** Inventory both local and Git/Perforce Poitou lanes, existing Melusina House / Paris builders, reference boards and actual map actors. Identify duplicates and proven/unknown items; make a one-page **reuse matrix**. Do not search six months of unrelated docs.

**L1 · Freeze the silhouette.** Start with the existing Foundation Master / roof ribbon / scallop distributor or authored house assembly (inspect before composing). Preserve three overlapping curled roofs, pink center volume, round stained glass, right tower, porch and asymmetrical wall rhythm. Produce **clay front / side / 3⁄4** shots before decorating. No new roof systems.

**L2 · Ground the house in Poitou.** Use the already authored Poitou terrain; identify safe elevated pocket near canal; fit a small, art-directed terrace and limestone landing/jetty, accessible path/bridge and one flat barque. Keep actual wetland water/edge mask legible. Do not pretend original sea-cliff house foundation can sit untouched on flat marsh: adapt *the interface to the land*, not its silhouette. Preserve walkable bank and navigation clearance.

**L3 · Regional dressing only where it helps.** Pollarded ash tree avenue, duckweed channels, damp moss, meadows, low bridges, limewashed/limestone vernacular background, canal reflections. Select an existing Parisian/Gothic module only when its scale and motifs strengthen the house; avoid transplanting a Haussmann street.

**L4 · One controlled color/lighting score.** House = blush, pearlescent blue/lavender, aqua glass, warm gold, warm interior glow; terrain = near-black greens, neutral limestone, muted water and mist. Cinematic dawn, layered trees, water reflections, subtle cymatic ripples under the established music/FX writer. **No replacement master materials** without demonstrated incompatibility.

**L5 · Hand to owner.** Provide `composition_clay_front.png`, `composition_clay_3q.png`, `composition_dawn_beauty.png`, a labeled overhead composition frame, registry/asset ledger, exact unresolved issues. House should be recognizable as Melusina's from a distant silhouette **without** relying on glow/ornament.

**Luna stop condition:** one composition + one look + clear handoff; no multiplayer orchestration, no new procedural framework, no unapproved live-editor saves.

## 4. Sol — **only** difficult technical integration

**S0 · Start after Luna's ledger.** Receive exact repro steps and ownership for a blocker. Reproduce before patching; reserve a single writer to the relevant app/worktree.

**S1 · Geographic-to-engine transform.** Confirm the DEM **horizontal projected CRS and units** (do not infer EPSG from axis labels), `NGF-IGN69` source vertical reference, source extents, height resolution, target waterline, datum conversion, transform origin, map scale and non-destructive reimport. Distinguish raw DEM values from photo-estimated berm height (reference diagram `0.3–1m` is explicitly illustrative). Bake bank/wetland/meadow/path/heritage masks with the current Houdini pipeline; prefer existing Field Atlas vocabulary, do not claim an unbuilt HDA is shipped.

**S2 · Terrain contract.** Produce or map a valid unified `melodia.terrain_handoff.v1` sibling via `Tools/terrain_handoff.py`; verify Mesh Terrain 5.8 import, **100 cm/m**, proper `/Game/` namespace, `classic_landscape_used=false` and consumer readiness. No classic Landscape fallback without explicit owner design decision.

**S3 · Compile and compose.** Preserve current `world_recipe.v1`, existing morning `recipe_id` and seed unless owner explicitly changes them. World Compiler CLI generates a deterministic bundle; existing UE consumer/PCG composes it in `L_MelusinaMorning`. Limit edits to proven missing adapters/placement/clearance defects; keep C++ / Blueprint / PCG / MPC / QuillScript authorities unchanged.

**S4 · PIE + restart proof.** Confirm actual player traversal along canal → landing → house, collision and water edges, PCG regeneration identity, house materials/LOD/perf, compiled bundle hash/determinism, no unintended duplicate actors, no unexplained dirty packages, map survives save/reopen where authorized. Record screenshots and `PASS/FAIL/NOT_RUN` per gate. Prefer existing proof and QA scripts.

**Sol stop condition:** a specific measured integration blocker resolved with tests and before/after evidence; not a broad rebuild or concept redesign.

## 5. Acceptance gates — do these in order

| Gate | Who | Observable pass |
|---|---|---|
| G0 inventory | Luna | exact Poitou producer/inputs found or honestly marked missing; builder IDs and authored assets classified `reuse`, `adapt`, or `needs proof` |
| G1 shape identity | Luna / owner | clay silhouette visibly reads *the original* scalloped-roof round Rococo house (3 views), scaled against person/path |
| G2 place identity | Luna / owner | reference-consistent marsh channels, flat terrain, raised banks, barque and Poitou limestone; house's base transition logical |
| G3 material identity | Luna / owner | fantasy house stands apart from restrained local environment; no Paris/Haussmann takeover |
| G4 schema/compile | Sol | valid terrain handoff; existing recipe and bundle schemas still validate; deterministic rebuild; no new status/runtime authority |
| G5 editor runtime | Sol | known map package, World Compiler/PCG coexist, collision/traversal, no duplicate writer, save/reopen proof at explicitly recorded evidence rung |
| G6 P0 final | owner | one dawn hero frame + one approachable playable establishing moment accepted; then freeze scope |

Any missing evidence stays `NOT_RUN` — **do not mark whole Poitou "done"** on the strength of existing morning/roof code.

## 6. Safe work and version-control discipline

- **No destructive substitution:** do not replace current Poitou Houdini graph, house WIP, UE package, masks, presets or house design docs from an archive. Copy/branch before transformations.
- **No new architecture:** no second World Compiler, Universe Foundry, runtime rhythm writer, material-master stack, Houdini terrain intake schema or house GN registry. Existing `MEL_mh_*`, `GN_PARIS_*`, world schemas and published recipes keep meaning/IDs.
- **Provenance:** original visual boards and Wikimedia terrain/historical maps need credited sources/licenses in their existing reference manifest (e.g. local `TERRAIN_SOURCES.md`, verify path); don't delete attribution.
- **External owners:** Perforce/Unreal binary packages and local Hython projects do not become Git-owned just because the plan references them. Avoid bulk binary commits/LFS costs; capture hashes and paths.
- **One editor / one writer:** follow [World Compiler runbook](../WorldGen/WORLD_COMPILER_SESSION_RUNBOOK.md) and Blender cockpit; no background agent saving the live portfolio blend or UE editor-owned package.
- **Status and evidence:** `CURRENT_STATE.md` is the single repository status document; update only after real proof. World Atlas evidence rungs are `SOURCE_PRESENT → SOURCE_BUILT → LIVE_PROVEN → RESTART_PROVEN → PACKAGED_PROVEN → PORTFOLIO_APPROVED`. This plan must **not** inflate the evidence rung.
- **Scope:** no character redesign, no unrelated Paris/Brutalist catalog work, no new gameplay features. P0 opening and house first.

## 7. Copy-paste execution prompts

### Luna — initial bounded session

> Read `POITOU_START_HERE.md` and its canonical convergence plan. First perform the G0 **read-only audit** across the latest Grok/Poitou local terrain/Houdini staging, Perforce-owned UE scene, existing Melusina House `MEL_mh_*` GN assets and completed `GN_PARIS_*` variants. Restore the original round-Baroque house design identity from the preserved Sept 2–3 packets as **visual constraints only**. Do not rebuild ribbon roofs, tiles, or Paris systems. Then compose a single recognizable house-on-canal Poitou hero scene with clay front/3q and dusk/dawn palette proof; report reuse matrix, source paths and blockers. No destructive writes, new world schema or owner-editor save.

### Sol — only when given a technical blocker

> Read `POITOU_START_HERE.md` and the G0 ledger from Luna. Solve **one** reproducible blocker from G4/G5 in the established Houdini terrain → `melodia.terrain_handoff.v1` → World Compiler CLI → UE 5.8 Mesh Terrain/PCG pipeline. Keep `melusinas_morning`, `L_MelusinaMorning`, recipe schemas, seeds and single-writer ownership intact. Return exact code paths, before/after hashes, test command outputs and PIE evidence; do not redesign the house or make another compiler/generator.

## 8. First P0 handoff/checkpoint

**Next action:** Luna posts G0 inventory + three clay screenshots. Owner chooses the strongest canal-facing staging. Only then hand Sol specific issues. **Deliver one showcase-quality scene, not a new ecosystem.**
