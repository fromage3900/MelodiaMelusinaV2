# Resonant Blooms — visual + geometry-node expansion plan (execute)

Owner direction (2026-10-11): expanded procedural GN trees, flower research, more headless
work. Extends the just-landed v0.1 (branch `landing/blooms-v0.1`, commit `bf4772f50`) and the
crude existing `build_stylized_tree_group`. Every lane proves itself HEADLESS first — a
registry PASS means nothing until a `--factory-startup` construction + render pass clears.

Source of truth for contracts: skill `melodia-gn-builder-workflow` + `deploy/surreal_arch/melodia_gn/core.py`.
Golden-angle math authority: `deploy/surreal_arch/melodia_gn/phyllotaxis.py` — never re-author 137.5077°.

## Lane 0 — harden the loop (do first, ~30 min)

The v0.1 pack script runs Blender foreground and blocks; make expansion iterable overnight.

1. Wrap the two existing entry points into one headless proof harness, `Tools/bloom_pipeline/bloom_proof.py`,
   modelled on `Tools/wardrobe_pipeline/gn52_proof.py`:
   - `--factory-startup`; **delete the 2 m default cube explicitly** (it fills the camera).
   - Build every tree via `GROUP_BUILDERS[name]()`; purge `bpy.data.node_groups` before each
     rebuild (a cached tree re-proves the OLD one).
   - Purge the CACHED MODULE, not just `sys.path`: `del sys.modules[m] for m == pkg or pkg.*`,
     re-import, `assert pkg.__file__.startswith(REPO)` or crash (AppData autoloads a stale copy).
   - Assert: every tree exists, zero link failures, output fed, `to_mesh()` verts > 0 per stage.
   - Gate link TYPES: flag any link where exactly one side is GEOMETRY (cross-domain links
     evaluate EMPTY with no error). Reference gate: `horn_dangl_proof.py` G6.
2. Workbench side/top previews per species/stage (already in `bloom_preview.py`) — keep as the
   "look" gate. EEVEE is dead in `--background` (blank frame); **Cycles CPU** is the render path.
3. Wire a preset-socket audit: every `BUILDERS_PRESETS` key must be a real input socket, or it
   fails red.

**Done when:** `python bloom_proof.py` exits 0 and prints a per-species vert/face census for
bud/half/full × 3 seeds. This becomes the regression gate for every lane below.

## Lane 1 — real procedural TREES (the crude `build_stylized_tree_group` → true generators)

`build_stylized_tree_group` is a placeholder (cylinder trunk + 3 icosphere clumps). Build two
real tree builders in a new module `deploy/surreal_arch/melodia_gn/trees.py`, registered via
`register_builder` (returns a bare `tree`, never the triple — a triple drags in unused Music sockets).

1. **MEL_tree_trunk** — recursive branching skeleton:
   - Start: `Curve Line` (or `Curve Spiral`) for the leader; drive depth by an Int dial `Depth` (3–5).
   - Each level: `Resample Curve` (COUNT mode) → `Instance on Points` a rotated/tapered child branch
     → `Realize Instances` (MANDATORY — a Points/Instances domain reads 0 through `to_mesh()`).
   - Branch angle + length falloff per level are float dials; compute placement in PYTHON where a
     value is constant (a socket chain is only as good as every link's dial reading).
   - Trunk taper: `Set Curve Radius` per level, then sweep with `Curve to Mesh` (radius via the
     **`Scale`** input — there is no `Radius` input on `CurveToMesh` in 5.2; profile circle carries radius).
2. **MEL_tree_foliage** — canopy on the branch tips:
   - `Curve to Points` (Count) at branch ends → distribute leaf instances (reuse a `_petal`-style
     leaf mesh or the blooms petal). Per-point `Random Value` Seed + Rotation for variation.
   - Optional phyllotaxis clustering of leaves on branch segments via `phyllotaxis.py` builders.
3. Keep it FBX-bakeable: `trees_bake.py` (mirror of `bake_bloom_kit.py`) bakes LOD0/1 + seasonal
   variants to FBX. GN procedural-time (wind via SceneTime) does NOT survive FBX — bake a static
   canopy, animate wind in UE.

**Trap pre-read (each cost a real round):** Merge by Distance needs Realize Instances first;
Set Material per-branch BEFORE the Join (one Set Material at output overwrites all); an unlinked
Geometry input is a SILENT empty, not an error (assert every node's geometry input is linked);
Join Geometry's Geometry is a multi-socket (link each part).

## Lane 2 — flower research → more species

Research FIRST (per eyewear-GN lesson: a variant that duplicates an existing shape wastes a slot).
Reference: `EXTENDING.md` roadmap. Candidate species, in value order — camellia, ranunculus,
lotus, lily, tulip. For each: pull 2–3 botanical references (petal count, whorl structure, open
form), map to the existing `SPECIES` dict schema (`counts`, `r`, `z`, `s`, `c`, `o`, `t0`, `petal`),
then add a `build_bloom_x` + a `PRODUCT` row. Nothing else needed (per the architecture contract).

Ship order (each independently sellable + proof-gated):
1. **Rose bowl fix** (top of roadmap, known v0.1 weakness): per-whorl petal shape (2nd/3rd petal
   dict) + curved calyx + inner "spiral heart" of 3 rolled petals. Render side AND top — the
   silhouette is set by per-whorl r/z + petal bend/recurve + c/o tilts, and widening petals
   made it worse before (trumpet + flat lid). Two nudge→verify passes max, then ask the owner.
2. **Peony gap close** (known v0.1 weakness): add inner whorls / raise petal overlap so full-open
   stops showing background through inter-petal gaps.
3. **Musical Mode input** — expose a `Mode`/scale dial that picks per-whorl petal counts + tilts
   from scale degrees (Lydian = lifted, Dorian = relaxed); optional `Root Pitch` → size ∝ sqrt(f_ref/f).
4. **2–3 new species** from research.

## Lane 3 — composition + headless bake scale-out

1. **Bouquet / field scatter group** — `Distribute Points on Faces` over a ground surface, instance
   flowers with per-point random Growth + Seed. Per-species branch with its own Seed + Density dials
   (a single Switch collapses to one variant — build one Distribute+Instance branch per species, then Join).
   NOTE: Distribute POISSON emits ZERO points when Density Max is any linked field — use RANDOM.
2. **Wind** — vertex bend via `sin(time + GrowthCol.B)`, gn SceneTime. Bake-time/portfolio only
   (GN time does not survive FBX; UE does wind).
3. **LODs** — lower `_petal` grid `Vertices X/Y` for distant flowers (peony is 22k tris).
4. **Presets** — colour ramps per species (blush, crimson, white, yellow, lavender) as extra materials.

## Standing gates (every lane)

- Neutrality: every new dial defaults so dial-defaults-eval == base-eval (`wardrobe_proof.py` pattern).
  A "neutral-feeling" 1.0 default is a latent mesh-bloat bug.
- Headless construction PASS before any GUI time. Registry PASS is not construction.
- Mirror to live addon dir after every change:
  `cp deploy/surreal_arch/melodia_gn/<file> "%APPDATA%/Blender Foundation/Blender/5.2/scripts/addons/surreal_arch/melodia_gn/"` then `cmp` to confirm byte-identical.
- **Look at the renders** — numbers alone hid several real bugs in v0.1. Verify by reading the PNG
  back and sampling bands, never by eyeballing a thumbnail or byte size (blank charcoal frames pass a byte check).
- Commit in bounded lane; integrator lands. Do not push/open PRs as a worker.

## Deliverables / exit criteria

1. `Tools/bloom_pipeline/bloom_proof.py` — green regression gate for all species/stages.
2. `trees.py` — MEL_tree_trunk + MEL_tree_foliage, registered + headless-proven + baked to FBX.
3. Rose bowl + peony gap closed, verified by side+top renders, owner-eyed.
4. +2–3 species (research-grounded), each with presets, in the pack zip.
5. Bouquet/field scatter + LOD + wind(portfolio) lanes proven headless.
6. Pack regenerated (`pack_bloom_generator.py`) → refreshed `ResonantBlooms_v0.2.zip`, docs updated.

## Not in scope (do not drift)

No second world compiler / scatter framework / material master. No EEVEE headless renders. No new
landscapes. No Perforce submit. No touching `Config/`, `Content/Materials/MF_MeshBlend_*`,
`.gitignore`, `run_verify.ps1`. Stay on blooms/trees; park side-fixes unless asked.
