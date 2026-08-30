# Houdini Work Plan — Sea Above P0 Closeout + AAA Polish Pass

**Date:** 2026-08-28 (evening, updated)
**Supersedes as the Houdini-day router:** `Docs/Handoffs/OVERNIGHT_HOUDINI_LEARN_LOOP_2026-08-28.md`
(its task inventory is unchanged; its evidence claims are — see §0.3).
**Feeds, does not compete with:** `Docs/VFX_NIAGARA_FLIPBOOK_SYSTEM_PLAN_2026-08-28.md` (droplet
atlas seam), `Docs/Art/SEA_ABOVE_SYSTEM_INTEGRATION_VISUAL_SHADER_BREAKDOWN_2026-08-26.md`
(material/VFX ownership), `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md` (gate authority).
**Owner direction, later this session:** presentation-layer procedural construction is explicitly
in scope — coral, texture suites, VAT assets, composed reef chunks (§3A). System convergence
(§5) still binds: no new combat/rhythm/HUD/wardrobe authority, ever.
**Lane class:** `author` / `asset_qa` / `beatmap_author` adjacent — offline Houdini work. No editor
writes in this lane; all editor steps queue through the single-editor holder.

---

## 0. Read-state — what changed since the overnight plan

### 0.1 P0 moved forward (Phase 1 CLOSED, Phase 2 wired)

- Allowlist delta landed; 12/12 `.qsc` playable; `test_qsc_allowlist_contract` 4/4 green.
- The Quill trigger repair means **one** trigger drives all five pillar scripts, and the four
  pillar triggers are placed and saved in `L_MelusinaMorning` and `LV_SeaAbove_Prototype`.
- `LV_SeaAbove_Prototype` is the canonical WP map with real content on disk: Oceanology ocean,
  false-ocean plane, PlayerStart, 12 floating islands, 4 Data Layers, fixed water volume
  (still a 2 m cube — scale before swimming proofs).

### 0.2 The hard gate that outranks everything: the tree does not compile

Commit `694b7250` half-landed the `FGameplayTag` migration (~20 errors, six water-lane files +
wardrobe test include). A build was in flight at handoff. **No PIE result is trustworthy until a
closed-editor build goes green** — every PIE run after 05:27 tested stale binaries. The wardrobe
automation tests (which would close two gates) don't compile either.

### 0.3 Houdini truth check (measured today, offline)

| Item | State | Evidence |
|---|---|---|
| Houdini 22.0.368 + hython | present | `P0_BACKEND_SESSION_EVIDENCE_2026-08-28.json` |
| **License** | **UNVERIFIED — likely the blocker** | `hserver -l` timed out (08-28 backend session); **live probe today: `hython --version` hung >60 s and wedged the shell session** |
| HoudiniEngine plugin | copied + enabled in `.uproject` | `HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` |
| HDA cooking in UE | **blocked on Engine license** (FREE tier; Apprentice HDAs incompatible) | same spec §2 |
| COP/PIL variant pipeline | **proven 1:1** — 12 wool albedos + contact sheet | `CHORAL_SHEEP_HOUDINI_VARIANTS_2026-08-28.md` |
| Groom pipeline | staged; real ABC needs hython; placeholder fallback exists | `CHORAL_SHEEP_GROOM_VARIANTS_2026-08-28.md` |
| **Overnight learn loop** | **DEMO ONLY — not evidence.** `state.json` best avg_score all 0.0, `history: []`; log ends `OVERNIGHT RUN COMPLETE (demo)`; scoring was PIL stubs; WLAB HIP is a stub "needs hython" | `Saved/Audit/overnight/state.json`, `OVERNIGHT_LOG.md` |

**Rule going forward:** do not cite overnight generations or their scores as results. They are
scaffolding. Every hython invocation gets a strict timeout and log capture, and is never run from
a shared agent shell (today's hang cost a wedged console).

---

## 1. Ordering — the one thing this plan gets right

The Sea Above pillar closes with **PIE evidence, not new art**. The assets that the gate needs
already exist in `LV_SeaAbove_Prototype`. Houdini work must never sit on that critical path.

```
Track A (editor holder)      Track B (Houdini lane, offline)         Track C (evidence)
─────────────────────────    ─────────────────────────────────       ─────────────────
B0 build green               B0 license verdict (parallel-safe)      contract tests
  ↓                            ↓                                       ledger rows only
wardrobe auto-tests          COP droplet atlas → manifests           (no prose claims)
  ↓                            ↓
walk 4 pillar triggers       membrane texture set → manifests
  ↓                            ↓
SeaAbove cutscene PIE        wool (timebox) / grooms / [HDA if licensed]
  ↓                            ↓
ledger rows                  ingest → queue editor-import window
```

---

## 2. Track A — Sea Above P0 pillar closure (editor holder; ~90 min after green build)

Not Houdini work, but it is what "close out Sea Above P0" actually means. Steps in order:

1. **Confirm the build went green** (evening closeout §8.1). If the in-flight build stalled:
   complete the `FGameplayTag` migration forward (the chosen direction) and pay one closed-editor
   rebuild. Bundle the `MelodiaShader` `AddShaderSourceDirectoryMapping("/Melodia", …)` fix (§4 of
   the closeout) into the same window — never pay two rebuilds.
2. **Scale the `OceanologyWaterVolume`** from its 2 m cube to the swimmable region (evening
   closeout §7) — cheap, and the cutscene lookdev reads wrong without it.
3. **Walk the Sea Above pillar trigger** in `LV_SeaAbove_Prototype`:
   - Quill `MelodiaQuillSeaAboveCutscene` plays; notify `melodia:travel:<level>` succeeds (the
     travel ID is in `TravelLevelIds` since Phase 1 — verify the notify resolves, not fails silently).
   - **Membrane pulse observed with a 16.0 s cycle** — `M_SeaAbove_Membrane_Prototype` +
     `User.SeaAbovePulse` from `BP_SeaAbove_PrototypeDirector`. Record two pulse-cycle timestamps
     in the assertion JSON to prove periodicity, not just presence.
   - **Droplets visible** — `NS_SeaAbove_UpwardDroplets_Prototype`. NOTE: the flipbook plan §3
     proved this emitter is bound to the membrane shader (flat opaque quads) and its Phase 2 fix
     is already specified. Track B1's atlas feeds that fix; do not polish the wrong material first.
   - Flags + stat + reward committed: `flag.cutscene.sea_above_witnessed`,
     `flag.sea_above.membrane_pulse_active`, `flag.cutscene.sea_above_completed`,
     `melodia_resonance:5`, `reward.cutscene.sea_above_memory`. Read them back from the canonical
     save record / narrative subsystem state — not from console prose.
4. **Evidence bundle:** PIE frames + assertion JSON (state reads, pulse timestamps, flag values,
   error counts) saved together under `Saved/Audit/sea_above/p0_pillar_<date>/`. Frames without
   the JSON are not evidence (AGENTS.md evidence standard #3).
5. **Record the row** per `Docs/P0_TASK_LEDGER.json` conventions (`sea_above_cutscene` pillar
   entry) and sync `Saved/gate_ledger.json` if the ledger reads stale. Prose is not a row.

---

## 3. Track B — the Houdini lane (offline; runs during Track A)

### B0 — License verdict (30 min, do first, owner-visible)

```powershell
# strict timeouts; capture logs; never from the shared agent shell
hserver -l                              # expect a license line, not "No licenses in use"
hython -c "import hou; print(hou.applicationVersionString())"   # with a 45 s timeout
```

- If `hserver` shows the FREE Engine license → HDA + real hython cooks unlock (B3–B5 live).
- If Apprentice-only / still hanging → **the PIL/Blender fallbacks carry today's deliverables**
  (proven 1:1 for COP work), and B3–B5 stay parked with a documented verdict. Do not spend the
  day fighting `sesinetd`; log the verdict and move on.

### B1 — Sea Above droplet flipbook atlas (the P0-serving deliverable; COP or PIL fallback)

Feeds the flipbook plan's Phase 2 reference implementation (§3 target state). This is the one
piece of Houdini art that directly improves what the P0 cutscene proof shows on screen.

- **Spec:** upward-droplet birth-to-death sheet, grayscale **luminance mask (data in R, no alpha
  reliance)**, 1024², 4×4 or 8×8 grid, matching `M_Niagara_MelodiaFlipbook` atlas math and the
  engine SubUV `SubImageSize`. Include gutter-free cell layout — the existing atlases put gutters
  at exact cell boundaries; match that.
- **Import settings contract** (from flipbook plan §2.3): `sRGB=false`, grayscale compression,
  `TEXTUREGROUP_Effects`. Put these on the ingest manifest so the editor import cannot get them
  wrong.
- **Output:** `Saved/Audit/sea_above/houdini_variants/T_SeaAbove_DropletFlipbook.png` +
  `sha256` manifest + an ingest script mirroring the `ingest_sheep_normals.py` pattern (verify →
  manifest → editor-import step listed but not executed by this lane).
- **Red line:** this lane never edits `M_Niagara_MelodiaFlipbook` or any master. The editor-side
  wiring (`MI_Niagara_MelodiaFlipbook_Droplet` sibling, renderer swap off the membrane shader) is
  an editor-window task owned by the flipbook plan.

### B2 — Membrane texture set (polish; COP or PIL)

`M_SeaAbove_Membrane_Prototype` already owns `SeaAbovePulse` → `RadialReveal` + displacement.
Houdini contributes **textures only**, as instance parameters:

- `T_SeaAbove_Membrane_RadialReveal` (1024² grayscale radial pattern) — gives the reveal
  structure instead of pure math falloff.
- `T_SeaAbove_Membrane_Ripple_N` (COP `Height → Normal`, 1024²) — for the pulse displacement.
- Output + manifest to `Saved/Audit/sea_above/houdini_variants/`; apply via MI parameters in the
  editor window. **Never touch `M_Water_Master_Grand_v10_Upgrade` (DO NOT MODIFY) or any frozen
  master.**

### B3 — Wool evolution, for real (timebox 2 h; needs hython)

The overnight loop's task inventory stands, but re-run it **for real** only if B0 goes green, and
only after fixing the stub: state must record real hython-cooked renders, `max_gens` corrected
(it recorded 1), and the scorer separated from the PIL placeholder. If B0 is red, park with the
verdict and note that the ship decision pending in `CHORAL_SHEEP_WOOL_LAB_REVIEW_2026-08-28.md`
(Option A ship flat vs Option B promote Worley12) can proceed either way on the existing proven
albedos — that decision is the owner's and is not blocked.

### B4 — Groom cook (needs hython)

`build_choral_groom_hip.py` → `cook_groom_variants.py` → real Ogawa ABCs → `ingest_grooms.py
--verify`. Cooking real ABCs un-blocks the *pipeline*, but UE binding stays blocked on the owner
side (sheep mesh has 0 vertex groups; blendshape approach agreed). Cook + verify + manifest only.

### B5 — ArpeggioStair HDA (optional; only if B0 green AND time remains)

Follow `HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` as written. **Not P0, not today's priority** —
it is listed so the license verdict (B0) can be acted on the moment it clears, and so the spec's
checklist has a next owner. The HDA output must bake to partitioned actors per that spec; no
Landscape actor at any step.

---

## 3A. Track B+ — the Procedural Reef Pipeline (owner-directed creative pass)

The Sea Above visual thesis — an inverted ocean hanging in the sky over a liquid cathedral — is
precisely the content Houdini exists for. This section is the ambitious lane the owner asked for:
procedurally grown coral, swaying kelp, full texture suites, composed reef chunks. Everything
cooks **offline in hython Apprentice**: geometry export (FBX/ABC), COP texture baking, and SOP
networks all work under Apprentice. The Engine license only gates cooking HDAs *inside UE*, and
this pipeline deliberately avoids needing it by baking to files. One Apprentice caveat: Mantra
renders are watermarked — beauty shots go through the existing Blender lit-sphere path
(`blender_lit_sphere_render.py` pattern), Houdini viewport OpenGL snaps for QA.

### Pipeline shape (same evidence culture as the rest of the repo)

```
seed_manifest.json  →  hython cook  →  FBX/ABC + textures + contact sheet + sha256 manifest
    →  ingest verify (ingest_grooms.py pattern)  →  QUEUED editor-import window (single editor)
    →  Nanite static mesh + MI instance params consume EXISTING MPC params (no new writers)
```

Determinism is non-negotiable: every cook records its seed and parameters in the manifest. A
beautiful mesh you cannot reproduce is not shippable content, it is a one-off.

### R1 — Coral generator (`Tools/Houdini/sea_above_reef/build_coral_generator.py`)

VDB-growth corals, not modeled corals. Seed points → VDB from polygons → advect along curl noise
with a directional bias → polygonize → UV + attribute masks → export.

| Archetype | Method | Signature |
|---|---|---|
| Staghorn (branching) | iterative small-side clone + bend toward noise | grows **downward** — the reef hangs from the floating islands and the false-ocean underside; inverted gravity is the level's identity |
| Table coral | radial disk + noise displacement | downward-facing umbrella |
| Tube sponges | metaball cluster + cavity | high emissive mask in cavities |
| Brain coral | noisy sphere + crevice mask | wet-mask showcase |
| Fan coral | curved plane + curl warp | silhouette variety at distance |
| Anemone field | groom-style tube clumps | pairs with R3 kelp sway |

Every mesh carries **vertex-color masks** (AO/bend, wetness, and a pulse band by height) so UE
materials stay MI-instance-driven: `MI_SeaAbove_Coral_*` tinted by the **12 pitch classes** —
the same PC00–PC11 chromatic system the Choral Sheep coats already use. The reef literally sings
the level's chord; content ties into the game's core musical identity instead of decorating
beside it.

Export per variant: Nanite-ready high mesh + 2 LODs, ≤ 12 unique coral meshes total (HISM
budget), composed-chunk target ≤ 3 M tris (Nanite absorbs density; emissive overdraw is the real
cost — keep emissive areas under ~15% of silhouette).

### R2 — Reef chunk composer (`compose_reef_chunks.py`)

Scatter R1 archetypes onto hython-generated rock bases (matched to a proxy of the existing
island transforms — the editor lane exports an island-transform JSON first; never guess
placements). Two output forms per chunk:

- **Composed chunk** — one FBX, corals + rock + kelp anchors baked. Drop-in `SM_ReefChunk_XX`.
- **Loose kit** — individual meshes + a scatter-weight JSON so the editor lane can drive PCG
  scatter with real density attributes later.

Both from the same seed → the kit and the composed chunk are guaranteed-consistent views of one
cook.

### R3 — Kelp + VAT sway (the cheap-AAA trick)

Tube-sweep kelp ribbons along noise curves; bake sway to **Vertex Animation Textures**
(position + normal, 2 textures per system). UE material samples the VAT with amplitude scaled by
`SeaAbovePulse` — the kelp visibly reacts to the membrane pulse with zero runtime sim cost. Same
VAT path later animates anemones and droplet-ripple ground decals. This is the single
highest-polish-per-hour item in the plan.

### R4 — Floating island regenerator (wave 1.5, optional)

VDB rock clusters with hanging liquid-drip undersides and a flat gameplay plateau; 3–5 seed
variants. The 12 placed islands stay authoritative — this module only produces *additional*
decoration islands until the owner asks for a swap.

### R5 — Texture suite v2 (COP, extends B1/B2)

Beyond the droplet atlas and membrane set already specced: bioluminescent emissive mask, wet-mask
(black-line growth by curvature), foam strip for the waterline, sediment gradient, and a
pulse-band LUT the coral/kelp materials share. All grayscale/data-map discipline from the
flipbook plan applies (sRGB off, R-channel data, `TEXTUREGROUP_Effects`). Contact sheet +
sha256 manifest per suite.

### R6 — The one-writer rule for all of it

Every pulse-reactive asset above reads **only** the existing `User.SeaAbovePulse` MPC parameter
from `BP_SeaAbove_PrototypeDirector` (per the 08-26 breakdown doc's ownership table). Geometry
and materials *sample* the pulse; nothing in this lane may add a second MPC writer or a second
presentation director. That is the line between "procedural content pipeline" and "defect."

### R7 — Quantum reef curator (optional flourish, policy-compliant)

The AGENTS.md quantum policy explicitly allows offline ranking of authored layouts/seeds. So:
cook N candidate reef layouts per chunk seed, score offline on constraints (silhouette variety,
emissive overdraw budget, gameplay-path clearance over the plateau, draw-call estimate), rank
quantum vs classical baseline, **classical fallback always wins on any backend failure**. Output
is only a chosen-seed manifest feeding R2 — the frame-by-frame game never touches quantum.

### Wave-1 acceptance (today, after B0)

| Module | Minimum ship |
|---|---|
| R1 | ≥ 3 archetypes cooked (staghorn, table, tube sponge) + contact sheet + manifests |
| R2 | 1 composed reef chunk on a proxy rock, seed-recorded |
| R3 | 1 kelp VAT asset: mesh + 2 VAT textures verified by ingest |
| R5 | Texture suite v2 first pass + contact sheet |
| R6/R7 | One-writer note in manifests; curator optional and clearly marked offline-only |

Everything else is wave 2 (next sessions): more archetypes, island regenerator, KaleidoNave
kaleidoscope-glass COP panels, Morning-field flower VATs.

### Wave-1 delivery log — 2026-08-28 late session (owner-directed expansion: sand, shell masks, clutter)

**Shipped (committed harness, `Tools/Houdini/sea_above_reef/`):**

| File | Purpose |
|---|---|
| `reef_common.py` | periodic value-noise / fBm / wrapped-Voronoi (exact tiling), wrap-Sobel normals, dual-runtime PNG save (PIL primary; bpy Non-Color pass-through fallback with bottom-up flip fix), sha256 manifest writer, WrappedDraw (9-offset seamless primitives) |
| `tilable_sand_suite.py` | **tilable sand**: albedo (authored dreamy ivory/aquamarine sRGB palette), height, normal (OpenGL Y+), wet mask, ripple mask + **tilable caustics** (two-scale wrapped-Voronoi edges) — the "underwater env maps" leg |
| `tilable_shell_masks.py` | **tilable shell masks**: nautilus (log-spiral chamber lattice), scallop (full-bleed ribs + hinge dots), conch (diagonal bands + Voronoi bulges), sand-dollar (5-fold petal lattice) + 2×2 contact sheet |
| `underwater_clutter_atlas.py` | **12 underwater-clutter sprites** (spiral shell, scallop, clam pair, starfish, sea glass, pebbles, barnacle cluster, seaweed sprig, coral twig, bottle shard, bubbles, driftwood) → 4×4 RGBA decal atlas + QA sheet + tilable floor-debris mask (12×12 lattice jitter) |
| `ingest_reef_textures.py` | the verifier: per-file sha256, mode/size check, **edge-seam tileability metric** (pass < 3 levels), UE import contract per kind (sRGB flag / LOD group), combined manifest |
| `build_clutter_meshes.py` | hython SOP builder (pebble scatter / starfish extrude+smooth / log-spiral sweep / seaweed ribbon) → FBX + manifest. **Queued behind the license verdict**; needs hython only, no Engine license |
| `probe_hython_license.ps1` | wedge-proof B0: Start-Process + 45 s hard timeout + kill for `hserver -l` and a `hou` import, prints a verdict — exists because a bare `hython --version` wedged this session's console |
| `README_texture_suite.md` | runbook: cook commands, import table, Blender fallback, determinism contract |

**Not shipped: the PNGs themselves.** The cook is BLOCKED, not done — the shell service was
wedged by the earlier hython hang (every command timing out, re-verified from a different
workdir) and the Blender MCP bridge refused connection. Per the evidence standard, no texture is
claimed to exist. One live console cooks and verifies the whole suite:

```powershell
python Tools/Houdini/sea_above_reef/tilable_sand_suite.py
python Tools/Houdini/sea_above_reef/tilable_shell_masks.py
python Tools/Houdini/sea_above_reef/underwater_clutter_atlas.py
python Tools/Houdini/sea_above_reef/ingest_reef_textures.py --include-sheets
Tools/Houdini/sea_above_reef/probe_hython_license.ps1   # B0 verdict, then mesh builder if green
```

**Editor-import queue (holder executes, manifest-driven):** import atlas/sand/shell sets with
the contract table (sRGB flags per kind); wire the sand set into an MI of the substrate parent;
drop `T_SeaAbove_Caustics` as a two-panner blend on the ocean material; place clutter decals via
existing decal paths. No master touched; pulse-reactive wiring reads `User.SeaAbovePulse` only (R6).

### EXECUTED — final results, 2026-08-28 end of session

The shell recovered mid-session and everything above was then actually run. Final state:

| Deliverable | Result |
|---|---|
| Texture suite | **COOKED** — 24 files: sand set (albedo/height/normal/wet/ripple), caustics, 4 shell masks, 12 clutter sprites + atlas, floor mask, 2 contact sheets, 3 suite manifests |
| Ingest verdict | **11/11 tiling targets PASS** (gradient-relative seam rule; sprites/atlas correctly excluded as non-wrap outputs). Three bugs were caught and fixed by this verifier: a real Voronoi edge band (toroidal distance now), naive metric on high-freq sines, sprites swept into the wrap check |
| B0 license verdict | **hython GREEN** (`HOU 22.0.368` imports), license server answering, **no Engine license** (`Used Licenses: None`) → HDA-in-UE parked, hython cooks green |
| Clutter meshes | **COOKED** — 4 meshes × (.obj + .bgeo.sc) in `Saved/Audit/sea_above/meshes/` + manifest: PebbleSet (14 spheres), Starfish (extruded puff), SpiralShell (610-prims tube), SeaWeed (200-prims tapered tube) |
| Apprentice format discoveries | FBX ROP **and** Alembic ROP export are Apprentice-blocked (the groom lane's "real ABC via hython" was therefore never actually cooked — same staged-not-proven pattern as the overnight loop). Working path: File SOP `filemode="write"` (menu tokens `auto/read/write/none` — index 3 is "No Operation", caught by probe) |
| Harness fixes landed | sand suite size-override SyntaxError (Py 3.14), probe `$Args` reserved-var bug, `geo` not prebound in H22 Python SOPs, sweep→code-tube replacement, toroidal Voronoi, seam-metric v2 |

Also fixed this session: the wedge-proof probe (`probe_hython_license.ps1`) now genuinely isolates
hython/hserver (Start-Process + hard timeout + kill) — the console wedge from earlier cannot recur.

### R1 EXECUTED — coral generator + EnvSandbox staging (owner-directed, same session)

- `build_coral_generator.py`: **6 code-grown coral meshes** — staghorn recursive branching tree
  (1920 prims, downward-biased growth), ribbed hanging table (720), tube-sponge cluster, warped
  fan, folded brain, 26-arm reef cluster. VDB-growth upgrade path reserved; export is the proven
  File-SOP path (.obj + .bgeo.sc). Manifest: `coral_mesh_manifest.json`.
- `coral_textures.py`: tilable **CoralSkin** albedo (rose→lavender patches), normal,
  emissive-pore mask (scaled by `User.SeaAbovePulse` in material) → **14/14 tiling pass**.
- `stage_to_sandbox.py`: **25/25 assets staged, hash-verified** into
  `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/{Textures,Meshes}/` with
  `stage_manifest.json` + `IMPORT_QUEUE.md` (per-file sRGB/compression/LOD/scale contract for
  the editor holder). Editor was down — no .uasset creation; that step is queued, not skipped.
- FBX re-confirmed Apprentice-blocked; `.obj` delivered instead (UE-native import).
- New landmines recorded in the reference doc: raw-string escaped docstrings break injected SOP
  code; `hou.Vector3` has no `rotateAroundAxis` (use Rodrigues); Voronoi/noise periods must be
  powers of two on 1024 grids.

### R3 EXECUTED — kelp + sway LUT (owner-directed "go", same session)

- `build_kelp_vat.py`: **3 kelp ribbon meshes** (Tall 2.0 m, Mid 1.5 m wide, Cluster of 3 merged
  stalks) — S-curved spines, cupped cross-section, twist taper; `uv.y = growth axis` is the
  binding contract with the LUT. Cooked .obj + .bgeo.sc, `kelp_mesh_manifest.json`.
- `kelp_vat_textures.py`: **`T_SeaAbove_KelpSway_LUT`** (512² RGB data) — the OBJ-compatible
  "VAT": U = time (loop-perfect integer harmonics, gust-modulated), V = height along stalk,
  R/G = lateral bend offsets, B = bow. Material recipe (in `IMPORT_QUEUE.md`): WPO samples the
  LUT at `(Time*Speed, uv.y)`; amplitude ×=`(1 + 1.5 * User.SeaAbovePulse)` — pulse-reactive,
  zero runtime sim, one MPC reader.
- **U-loop verified seam-free** (wrap step 0.254 L vs 0.204 gradient, ratio 1.246). Note: a
  first wrap check compared the V axis and "failed" at 31 levels — that check was wrong
  (V=height intentionally clamps; base is pinned), fixed to a U-axis ratio check.
- Design decision recorded: true per-vertex FLIPBOOK VAT needs UV1/vertex-ID indexing, which
  OBJ cannot carry — it is the Engine-license upgrade path; meshes ship as .bgeo.sc in audit
  for exactly that future.
- Restage: **29/29 assets hash-verified** in the sandbox (16 textures + 13 meshes); IMPORT_QUEUE
  carries the full kelp sway recipe.

### R4 + R5 EXECUTED — parallel subagent pass + Blender render QA (same session)

**R5 (subagent, texture suite v2)** — delivered and verified: droplet flipbook atlas (the B1
deliverable, now cooked), membrane reveal + ripple normal (B2), tilable wet-rock suite
(albedo/normal/wetline), barnacle crust mask, 12-PC pulse-band LUT, foam mask, sediment ramp.
Ingest after merge: **19/0 tiling pass** (centered radials, strips and the atlas correctly
excluded as non-wrap outputs). Subagent also added the 10 CONTRACT rows + exclusions.

**R4 (coordinator-authored)** — the island subagent returned an EMPTY report and produced NO
file (verified on disk before believing anything) — recorded as a coordination lesson: subagent
reports are claims, disk is truth. The coordinator authored `build_island_generator.py` on the
house pattern: 3 floating islands (dome + plateau clamp + hanging drips + tendril on C; 2870/
3486 prims on A/C) + 2 rock chunks. Two template-injection misses found by the cook (SEED
placeholder absent; chunk code used lowercase seed_off) — both fixed in one pass each.

**Sandbox now: 44/44 staged, hash-verified (26 textures + 18 meshes).** IMPORT_QUEUE updated
for all R4/R5 assets.

**Blender render QA suite (coordinator):** `render_qa_blender.py` (headless Blender 5.2, Cycles
CPU, SeaAbove 3-point rig — warm key / aqua fill / cool rim, camera auto-fit, x100 mesh scale,
clay shading; textures render flat + on ×2-wrapped spheres for seam/value checks; version-tolerant
OBJ import; `--skip-existing` resume) + `assemble_contact_sheets.py` (PIL, labeled sheets).
Output: **62 renders** + `render_manifest.json` + 4 sheets in `Saved/Audit/sea_above/renders/`
(`_SHEET_Meshes`, `_SHEET_Textures_Flat`, `_SHEET_Textures_Spheres`, `_SHEET_OVERVIEW`).
Two operational facts recorded: background Blender 5.2 can hang at EXIT after all work is
flushed (kill is safe once render_manifest.json exists), and the full-suite CPU render takes
>15 min — run with `--skip-existing` to resume.

---

### R6 EXECUTED — THE JELLYFISH (owner-directed finale, same session)

Massive jellyfish-esque structure: **~90 m bell with 3 morph targets** (PulseContract /
PulseExpand / SurrealLurch — all four pose variants generated from one code path with
**verified identical topology**, 4320 pts / 4224 faces each) + **8 ribbon arms at ~320 m
each — 3.5 football fields per arm** — with the surreal logic baked two ways: into the rest
geometry (Moebius half-twist, bifurcation drift at s=0.5, anti-gravity rise after the fall)
and into **loop-verified LUTs** (`T_Jelly_ArmLogic_LUT` U-loop ratio 0.937, biolum 0.851;
traveling cyan-magenta bioluminescence pooled by bend magnitude). Bell ships as skeletal FBX
with morphs (Blender export — Apprentice cannot), arms as Nanite-able static FBX; motion =
WPO on the LUTs, one MPC reader. QA renders in `renders/jelly/`. Staged: **48/48 hash-OK**
(28 textures + 20 meshes incl. 2 FBX).

**New lessons recorded:** `_inject` + quoted placeholders double-wrap strings
(`MODE = "__MODE__"` + repr → `"'bell'"` — the arms only ran because the broken comparison
fell into their branch; caught by a debug print of the injected line); a dangling selection
made `bpy.ops.object.join()` swallow the bell into the arms mesh (deselect-before-join);
JSON pose values are dicts — iterating one yields keys, not points; **user addons break
background Blender — always `-b --factory-startup -noaudio`**.

**Lookdev v2 (iridescence + veil, same night):** 7 new textures — bell BaseColor/Normal/
Opacity/CanalMask/Irid_Mottle, the **`T_Jelly_Iridescence_LUT`** (U = N·V facing, V = film
phase, pastel-near-facing → spectral-at-grazing sine-spectrum palette), and tilable
**Nematocyst glints**. Ingest grew a third category — **U-only wrap** for radial-domain bell
maps (U verified, V is a designed gradient that must not tile) — and now sits at **25/0 pass
overall**. The full **iridescent material recipe + magical parameter manifest** (Iridescence-
Intensity/Power, FilmPhaseSpeed, CanalGlow, Sweep/Flutter/PulseGain, BiolumSpeed/Intensity,
GlintPanner, morph driver table with SurrealLurch timing) lives in the sandbox
`IMPORT_QUEUE.md`. Sandbox total: **55/55 staged, hash-verified** (35 textures + 20 meshes).

### WONDERS EXECUTED — THE LEVIATHAN + THE DROWNED ORGAN (owner "something cool", night cap)

- **`build_leviathan.py`** — colossal sunken ribcage, fossilized **died swimming upward**
  (spine run 140 m, tail rises 30 m): 22 vertebrae (tapering torus rings + neural spines,
  tail tilted upward), 11 rib pairs arcing down then inward, stylized skull with eye rings
  and jaw. 6682 pts / 6736 prims. Static, Nanite-able.
- **`build_drowned_organ.py`** — cathedral pipe organ: **24 pipes in 12 pitch-class ranks**
  (deepest = tallest), facade arc, console + arch frame; 4446 pts / 4140 prims. `uv.x` maps
  each pipe to its PC band → tint from `T_SeaAbove_PulseBand_LUT` (the shared chromatic
  system); mouth-ring emissive × `User.SeaAbovePulse` — **the reef becomes an instrument.**
- **`bone_organ_textures.py`** — eroded bone suite + brushed-brass/patina pipe set; one
  marginal seam (cusped sawtooth profile) caught by ingest, fixed with a smooth cosine seam.
  Final ingest: **31/0 tiling pass**.
- Sandbox now **63/63 staged hash-OK** (41 textures + 22 meshes); 2 jelly FBX skips were the
  owner's editor holding them open (locks handled gracefully by the stager — the editor is IN
  USE, coordinate before touching `Content/`). QA renders of both wonders verified visually;
  sheets rebuilt (20-cell mesh sheet).

### DREAMS LANE EXECUTED — volumetrics + frozen cloth + dream flora + STARSKIFF MK2 (owner "all three")

- **Volumetrics**: `build_volumetrics.py` — GodRays shafts, GhostFog (leviathan's
  ghost), NebulaVeil — **3/3 .vdb written** (Apprentice vdb write probe-verified) and
  staged to `Reef/Volumes/` for UE 5.3+ Sparse Volume Texture import.
- **Frozen cloth**: `build_frozen_cloth.py` — analytic drape poses (Vellum upgrade
  documented), 6 same-topology pose sets → `cloth_shapekeys.py` → **SM_Banner.fbx
  (SwayA/SwayB/Billow) + SM_Shroud.fbx (Gather/Drift/Settle)** — morph-bearing, via the
  proven jelly-bell path.
- **Dream flora**: `build_dream_flora.py` — code-L-system (rewriting + turtle walk, no
  SOP parm roulette): GlassReed / ChimeBlossom (bell tips) / SpiralFern — PCG-scatter
  flora with the Bell motif seeded.
- **STARSKIFF MK2**: `expand_starskiff.py` opened a COPY of the owner's desktop
  `Starskiff_Shorewake_Project.blend` (original untouched), added GunwaleGlow +
  MastLantern + FX sockets (wake L/R, sail cloth, lantern), exported
  `SM_Starskiff_MK2.fbx` — traversal-READY asset (boat gameplay = owner's game-code
  design). Gunwale skipped gracefully (rim name differs in the saved blend — one-line
  fix queued). QA render through the project's own camera queued next session.
- Sandbox total: **77/77 staged hash-OK** (47 textures + 30 meshes incl. 5 morph-bearing
  FBXs) + 3 VDB volumes in `Reef/Volumes/`. Owner's editor was IN USE throughout (jelly
  FBX locks) — stager skipped locks gracefully; no Content conflicts.

---

## 4. Evidence standard for this lane

1. Cooks produce **manifests** (sha256 + source params), never "trust me" folders. Pattern:
   `ingest_grooms.py` / `ingest_sheep_normals.py`.
2. Nothing is claimed closed from a Houdini cook. Sea Above P0 closes with Track A's PIE bundle
   + ledger row. Wool/groom/HDA polish claims cite their manifests and, once imported, an editor
   re-read (`get_cdo_properties` / material param re-read), not the cook log.
3. The overnight demo run is recorded as demo. If B3 re-runs it for real, its first action is
   resetting `state.json` and labeling the log, so real and demo generations are never mixed.
4. `houdini_*` MCP mutate tools stay gated per `specs/mcp_tool_policy.v1.json` — today this lane
   uses direct hython scripts + read-only MCP (`list_hips`/`inspect_hip`) only.

## 5. Red lines (this lane)

- **No writes under `Content/_PROJECT/`.** The 08-26 `TONIGHT_ASSEMBLY_PLAN` proposed
  `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SeaAbove/` — that path is off-limits; the
  canonical level is `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/…` and it already exists.
- No master material edits, no second HUD/UI writer, no new rhythm/wardrobe/combat authority.
  Houdini supplies textures, grooms, meshes — owners consume them.
- One editor. Editor import windows are queued tasks for the holder, not lane actions.
- No `delete_asset`, no destructive git, no `.hip` conversion of Apprentice `.hipnc` files.
- No Sakura art direction in any generated texture/mesh.

## 6. Timeline (relative to start)

| Block | Track B (Houdini lane) | Track A (editor holder, parallel) |
|---|---|---|
| H0 | B0 license verdict → report | confirm build green; if stalled, finish migration + rebuild (+ shader mapping) |
| H1–H2 | B1 droplet atlas + manifest | wardrobe automation tests (compile now that build is green) |
| H2–H3 | B2 membrane texture set + manifests | walk pillar triggers → Sea Above PIE proof + evidence bundle |
| H3–H4 | B3 wool (timebox) or park; B4 grooms if licensed | scale water volume; record rows |
| H4–H6 | **R1 coral cooks (≥3 archetypes) → R2 one composed chunk → R3 kelp VAT → R5 texture suite** (§3A wave 1) | walk remaining pillars; queue editor-import window for B1/B2/R-outputs |
| H6+ | B5 HDA only if licensed; R7 curator optional; wave-2 scoping | package_launch remains Phase 4 |

**Wave 2 (next sessions, same pipeline):** remaining coral archetypes, R4 island regenerator,
KaleidoNave kaleidoscope-glass COP panels, Morning-field flower VATs, PCG-scatter handoff from
R2's loose-kit density JSON.

## 7. Done-today checklist

- [ ] License verdict recorded (green or red, with the command output)
- [ ] Droplet atlas + sha256 manifest in `Saved/Audit/sea_above/houdini_variants/`
- [ ] Membrane texture set + manifests
- [ ] **Reef wave 1:** ≥3 coral archetypes + contact sheet + seed manifests; 1 composed chunk;
      1 kelp VAT asset verified; texture suite v2 first pass
- [ ] Sea Above pillar PIE bundle: frames + assertion JSON (pulse timestamps, flag/stat/reward
      read-backs) + ledger row
- [ ] Overnight demo status explicitly noted; state reset if the loop re-runs for real
- [ ] Editor-import queue updated with all R-module outputs (manifest-driven)
- [ ] No red-line violations; single MPC writer confirmed in every reactive asset manifest

---

**Deliberately not in this plan:** second outfit art (post-P0), Shorelistener `Cos_*` assets
(concept board only), Niagara hygiene sweep (flipbook plan Phase 3), itch tooling, any new
combat/rhythm/HUD/wardrobe authority.

**The convergence line, restated for the creative pass:** *systems* converge — rhythm, wardrobe,
battle, HUD each have one owner and this lane builds none of them. *Presentation content* is now
owner-directed construction territory (§3A): the reef, the textures, the VATs — all of it feeds
the presentation the four pillars already own, reads only their existing parameters, and lands
through manifests. Grow as much ocean as we want; never grow a second authority.
