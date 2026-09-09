# Universal Wardrobe Studio — AAA Pipeline Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Turn `Melusina_Wardrobe_Studio_v1.blend` into a versioned, proof-gated pipeline that generates new outfits procedurally (GN builders), tests them against audio reactivity in-studio, and ships them to UE — with Chladni cymatics as the pattern authority and simulation split between Blender (interactive) and Vellum (offline hero bakes).

**Architecture:** One mannequin (the recovered `Retopo_Melusina_002`), one GN garment kit registered in the existing `melodia_gn` registry, one audio contract (Universal Musical Influence + `audio_amplitude` attribute), one proof harness that gates every builder headlessly before anything reaches the GUI. Seasons and variants are presets, never tree copies. UE's `MelodiaWardrobeSubsystem` stays the gameplay authority; Blender is authoring/bake lane only.

**Tech Stack:** Blender 5.2 LTS only (never 4.5), Geometry Nodes + `GeometryNodeSampleSoundFrequencies`, existing `deploy/surreal_arch/melodia_gn/` registry, melodia-cymatic-eigenmode solver (Chladni), Blender cloth + `garment_xpbd_drape.py` (fit tests), Houdini Vellum via melodia-fabric-cops-pipeline (hero bakes only), EEVEE for review renders.

---

## Verdicts on the two open questions (decided up front)

**Chladni — YES, integrate.** It becomes the *pattern authority* for fabric surfaces: the
eigenmode solver (m,n modes) bakes cymatic displacement/mask maps, and the audio band
*selects* which eigenmode drives a piece. This is offline selection (quantum-style: pick
the pattern before play), not frame-by-frame simulation — consistent with project doctrine.

**Vellum — YES, but as the offline hero-bake lane only.** In-studio fit tests use
Blender-native cloth + the existing `garment_xpbd_drape.py` GN builder (fast iterate
loop, same window as modeling). Vellum (Houdini COPs pipeline, already present in the
toolchain) is reserved for final drape bakes on pieces that need film-grade fold
detail, cached to Alembic and imported. Making Vellum the in-loop tester would break
the generate→test cadence; making it forbidden would waste a present tool. Bake lane it is.

---

## Current context (what exists, verified 2026-09-05/06)

- Studio file: `Saved/Audit/melusina_lookdev/Melusina_Wardrobe_Studio_v1.blend`
  (v22 Zen rebuild, EEVEE TAA 64, 878 objects, 163/165 textures resolved,
  `WARDROBE_Pieces` / `WARDROBE_StudioSet` / `WARDROBE_FX` collections created)
- Inventory manifest: `Saved/Audit/melusina_lookdev/WARDROBE_INVENTORY_20260905.json`
  (11 pieces catalogued with materials)
- Recovered textures: `Saved/Audit/melusina_lookdev/Textures_Recovered/` (28 files, local — G: is off-limits for live reads)
- GN registry: `deploy/surreal_arch/melodia_gn/` — `core.py` (registry, presets, Universal
  Musical Influence), `garment_loom.py`, `garment_xpbd_drape.py`, `garment_tension_folds.py`,
  `garment_audio_drape.py`, `starskiff_hull.py`, `starskiff_biomech.py`
- Proven 5.2 audio pattern: Sound socket via `_add_sound_param`, band math (Low/High Hz),
  `GeometryNodeSampleSoundFrequencies`, silent-zero fallback, `audio_amplitude` store —
  encoded in skill `melodia-gn-builder-workflow`
- Proven 5.2 traps (encoded in same skill): NaN from POWER(negative)/SQRT(negative),
  MeshLine per-step offset, Realize Instances required at tree tail, neutral-at-zero dials,
  proof harness must purge cached trees, headless interface-default edits don't re-sync modifiers
- Headless proof pattern: `Tools/wardrobe_pipeline/gn52_proof.py` (background + `--factory-startup`)
- Sync law: repo `deploy/surreal_arch/melodia_gn/` → `%APPDATA%/Blender Foundation/Blender/5.2/scripts/addons/surreal_arch/melodia_gn/` via `cp` + `cmp`
- MCP bridge: live session on TCP 127.0.0.1:9876 (`Tools/blender_mcp_client.py`) — one bridge, serialize all live-session work through it

---

## Phase 1 — Foundations (hygiene before features)

### Task 1.1: Studio file skeleton lock
**Files:** `Melusina_Wardrobe_Studio_v1.blend` (in-session via MCP)
- Verify `WARDROBE_Pieces` contains all 11 inventoried pieces; anything not a garment
  stays in `Set_Diorama`/`Characters`. Move nothing by hand — script it:
  `python Tools/blender_mcp_client.py execute_code --file <script>` reading
  `WARDROBE_INVENTORY_20260905.json` as the source of truth.
- Add `WARDROBE_Archive` collection (for superseded piece versions — nothing deleted, ever).
**Verify:** object count before == after (only parenting/membership changed).

### Task 1.2: Naming + versioning convention (write the doc)
**Files:** Create `Saved/Audit/melusina_lookdev/WARDROBE_PIPELINE.md`
- Pieces: `W_mel_<piece>_v<NN>` (e.g. `W_mel_shawl_v03`). Builders: `MEL_garm_*`.
- Textures: `T_<piece>_<map>.png` under `Saved/Audit/melusina_lookdev/Textures/<piece>/`.
- Rule: G: drive is never a live dependency; anything referenced must live under
  `melusina_lookdev/` on C: first (the 50-minute relink lesson).
**Verify:** doc exists; every existing piece renamed or aliased in the manifest.

### Task 1.3: Master material library (instances only)
**Files:** in-studio; manifest row in `WARDROBE_INVENTORY_*.json`
- One master per fabric family (velvet, silk, brass trim, painted wood — reuse the
  v22 `SBW_MELUSINA.*` node groups as the masters). All pieces get `MI_` instances.
- Texture sets stay OPEN: never wire an old piece's maps onto a newer mesh.
**Verify:** material count grows by instances only; no duplicated node trees.

---

## Phase 2 — GN Garment Kit (the generator)

### Task 2.1: `wardrobe_kit.py` builder module
**Files:** Create `deploy/surreal_arch/melodia_gn/wardrobe_kit.py`
- Builders: `MEL_garm_drape_base` (fit-over-mannequin shell with thickness), 
  `MEL_garm_trim_lattice` (brass/jewel trim instancing, rivet pitch 6×d — biomech rules),
  `MEL_garm_layer_stack` (join N shells with gasket gap 0.004).
- Every builder auto-receives Universal Musical Influence (registry handles it — never
  call `add_music_influence_params` manually).
- **Every dial is neutral-at-zero.** Reuse the proven multiply wiring; defaults 0.0.
- Register via `register_builder()`, 3 presets each in `BUILDERS_PRESETS`.
**Verify (headless, before GUI):** extend proof per Task 3.1; zero GUI time until red→green.

### Task 2.2: Chladni pattern layer (`chladni_layers.py`)
**Files:** Create `deploy/surreal_arch/melodia_gn/chladni_layers.py`; 
Reference skill `melodia-cymatic-eigenmode` for the physics solver (read skill first;
its solver output format is the contract).
- `MEL_garm_chladni_layer`: displacement/mask layer driven by baked eigenmode maps.
- Inputs: `Eigenmode Map` (image), `Mode Weight`, `Audio Band Select` (Low/High Hz),
  `Cymatic Amplitude`, `Seed`.
- Audio band *selects* the eigenmode (offline choice), amplitude rides `Musical Amplitude`.
- Bake contract: store `chladni_psi` + `audio_amplitude` named attributes (POINT domain)
  for Substance/UE handoff.
- Traps pre-encoded: no POWER on negatives, MAXIMUM-guard radicals, Math CLAMP node
  doesn't exist in 5.x (use ShaderNodeClamp).
**Verify:** headless build + attribute presence assert.

### Task 2.3: Sync + registry hygiene
**Files:** repo ↔ addons dir
- `cp` changed modules to `%APPDATA%/.../surreal_arch/melodia_gn/`, `cmp` byte-identical.
- Preset-socket audit: every `BUILDERS_PRESETS` key must be a real interface socket
  (fail red in proof).

---

## Phase 3 — Proof harness (the AAA gate)

### Task 3.1: `wardrobe_proof.py`
**Files:** Create `Tools/wardrobe_pipeline/wardrobe_proof.py` (extend `gn52_proof.py` pattern)
- Headless, `--background --factory-startup`, opens a *test* mannequin file (not the studio).
- For every registered `MEL_garm_*` builder: purge cached tree → build → assert
  nodes/links > 0 → wire to test mesh → evaluate via `bpy.data.meshes.new_from_object` →
  assert verts > 0 and bounds sane (no NaN: bbox finite, dims within [0.1×, 10×] of mannequin).
- **Neutrality assert:** all dials at default ⇒ output bounds == input bounds (±noise epsilon).
- **Audio assert:** `audio_amplitude` attribute exists on output geometry.
- **Preset assert:** every preset key is a real socket.
- Exit non-zero on any failure (CI-able later).
**Verify:** run green on existing builders (loom, xpbd_drape, hull) before new ones.

### Task 3.2: Render smoke
**Files:** Create `Tools/wardrobe_pipeline/wardrobe_render_smoke.py`
- EEVEE turntable (36 frames, 256px) + JSON manifest (object counts, material slots,
  missing-texture count) saved next to frames. PNG without JSON is not evidence.
**Verify:** manifest `missing_textures == 0` for shipped pieces.

---

## Phase 4 — Fit + motion test loop (in-studio)

### Task 4.1: XPBD fit test
- `garment_xpbd_drape.py` builder on the test piece → drape over `Retopo_Melusina_002`
  in the live session via MCP (Path A modifier inputs for per-piece tweaks).
- Collision: mannequin gets a `COLLISION` modifier; self-intersections read as fit failures.
**Verify:** drape converges (no exploding verts over 120 frames); capture contact sheet.

### Task 4.2: Audio-reactive preview
- Wire `MEL_garm_chladni_layer` + hull-audio pattern to the piece; drive with a loaded
  sound (the studio has `audvis_global_settings` already — reuse, don't duplicate).
- Preview only; bake-time rendering of the same setup for lookdev.
**Verify:** amplitude attribute animates; viewport shows displacement following the track.

---

## Phase 5 — Vellum hero-bake lane (offline, optional per piece)

### Task 5.1: Vellum bake contract
**Files:** `Saved/Audit/melusina_lookdev/VELLUM_BAKE_CONTRACT.md`
- Input: exported mannequin + piece (Alembic). Output: Alembic vertex cache + baked
  cymatic/audio attributes. Read skill `melodia-fabric-cops-pipeline` before any Houdini work.
- Import back into studio as cache (never re-sim in Blender — one sim authority per piece).
**Verify:** roundtrip — cached piece re-attaches to mannequin at frame 1 exactly.

---

## Phase 6 — Export to UE (respect the authority line)

### Task 6.1: Export pass
- FBX/USD per piece + baked textures; naming per convention; manifest row per export.
- UE side: `MelodiaWardrobeSubsystem` remains the only gameplay authority — exports land
  as assets, not logic. Follow `melusina-blender-handkeyed-import` skill conventions.
**Verify:** UE import log shows zero missing textures; subsystem sees the new piece rows.

---

## Order of execution
1 → 2.1 → 3.1 (proof green) → 2.2 → 2.3 → 3.2 → 4.1 → 4.2 → 5.1 → 6.1
Proof harness (3.1) lands *before* the Chladni layer so every new builder is born gated.

## Risks / tradeoffs / open questions
- **Blender 5.2 API churn** — every builder headless-proofs before GUI time (non-negotiable).
- **G: drive latency** — all live-referenced assets local on C:; G: is copy-source only.
- **.blend bloat** — studio stays ~2.4GB; per-piece working files stay lean (external
  textures, pack only ship candidates).
- **Vellum availability/version** — Houdini is present in the toolchain; confirm license
  seat + version before Task 5.1 (open question for owner).
- **Audio runtime authority** — Unreal owns rhythm; Blender audio layers are authoring/
  bake preview. Any temptation to "ship" Blender audio reactivity into UE is a doctrine break.
- **One bridge** — all live-session mutations serialize through MCP 9876; no second writer.
