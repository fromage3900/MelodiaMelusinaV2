# Material Library Audit — Post-Migration Sweep

Run **after** you finish manually copying Melodia materials into `/Game/EnvSandbox/Materials/`.  
Designed for **one afternoon** (~3–4 hours). Goal: rewire **EnvSandbox portfolio materials** to `/Game/EnvSandbox/...` paths — **not** to purge legacy source assets.

**Related:** [`MATERIAL_MIGRATION.md`](MATERIAL_MIGRATION.md) (schema), [`TOON_MIGRATION_RUNBOOK.md`](TOON_MIGRATION_RUNBOOK.md) (batch workflow).

### Retention policy — `Content/_PROJECT/`

**Retain `Content/_PROJECT/` permanently.** This folder (~1800+ Melodia legacy assets) is your source work and personal material library. The audit never schedules its deletion, archival removal from the project, or automated cleanup.

- **Audit goal:** portfolio instances and masters under `/Game/EnvSandbox/Materials/` should reference `/Game/EnvSandbox/...` when ready — not `/Game/_PROJECT/...`.
- **Triplicate textures are OK short-term** (same stem in `SDF/Textures/`, `Content/Textures/`, and `_PROJECT/04_Materials/Textures/`). Prefer EnvSandbox copies for assignable portfolio surfaces; leave `_PROJECT` copies in place.
- **Do not delete** any files under `Content/_PROJECT/` as part of this audit or migration workflow.

**Automation:** `Content/Python/audit_material_library.py` (inventory + dead-ref scan) · `Content/Python/fix_migration_redirectors.py` (redirectors)

---

## When to run

| Trigger | Action |
|---------|--------|
| Last robocopy / manual copy batch landed | Run audit script → fix redirectors → re-run |
| Before a portfolio demo / git milestone | Phases 1–7 + spot viewport; confirm zero `_PROJECT` refs in EnvSandbox materials |
| After adding Impressionist or environment instances | Phase 6 naming + parent check only |

---

## Current snapshot (2026-06-19 — mid-migration)

Baseline from `audit_material_library.py` before your send-over completes:

| Metric | Count | Notes |
|--------|------:|-------|
| EnvSandbox Materials uassets | 56 | 47 material-like + 9 textures |
| Orphan textures (portfolio path) | **5** | `Marble_1/3/5/6/9` — copied to `SDF/Textures/` but masters still sample `_PROJECT` paths |
| EnvSandbox refs still on `_PROJECT` paths | **25+ edges** | Copied Melodia masters + instances embed `/Game/_PROJECT/04_Materials/...` — rewire to `/Game/EnvSandbox/...` |
| Dead function refs | **14** | 11 copied SDF masters → missing `/Game/Art/Materials/.../MF_MeshBlend_Activator_Index` |
| Duplicate names (within Materials) | 0 | — |
| Triplicate storage | **9 textures** | Same stem in `SDF/Textures/`, `Content/Textures/`, `_PROJECT/04_Materials/Textures/` |
| On-disk libraries | 1800 + 460 | `Content/_PROJECT/` (**permanent** source library), `Content/Textures/` (staging — may dedupe after rewire) |

Full JSON: `Saved/Audit/material_library_audit.json`

---

## Phases (run in order)

### Phase 1 — Inventory (~20 min)

1. **Tools → Execute Python Script** (or Output Log):
   ```
   python "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_material_library.py"
   ```
2. In editor (optional, adds redirector list): same script via `py "..."`.
3. Content Browser → `/Game/EnvSandbox/Materials` → enable **Show Redirectors**.
4. Note counts: textures, masters, instances, redirectors, `_PROJECT` ref edges.

**Exit:** JSON report saved; you have a before/after baseline.

---

### Phase 2 — Dead texture purge (~45 min)

**Goal:** Every material samples textures under `/Game/EnvSandbox/Materials/SDF/Textures/` (or documented exception).

#### Checklist — `SDF/Textures/`

- [ ] List orphans from audit (`orphan_textures` in JSON).
- [ ] For each copied Melodia master still pointing at `_PROJECT/.../Textures/...`:
  - Open material → find texture sample nodes → retarget to portfolio path.
  - Or run **Reference Viewer** on the `_PROJECT` texture → **Migrate Asset** to `SDF/Textures/<Category>/`.
- [ ] Delete portfolio orphans only after **zero** incoming `_PROJECT` refs remain for that stem (orphans under `SDF/Textures/` only — never delete `_PROJECT` source textures).
- [ ] `_PROJECT` assets may remain on disk indefinitely; rewiring EnvSandbox refs does not require removing them.

#### Checklist — `Textures/` (legacy root)

- [ ] `Content/Textures/` (460 uassets) is **not** in schema — treat as staging.
- [ ] After rewiring, move or delete duplicates already present under `SDF/Textures/`.
- [ ] Keep CC0 surfaces in `Content/Surfaces_CC0/` — out of scope unless wired into a master.

**Defer (do not purge):** textures referenced only by deferred Melodia game/VFX masters you have not ported.

---

### Phase 3 — Redirector fix (~15 min)

1. ```
   py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_migration_redirectors.py"
   ```
2. If script warns (no API): Content Browser → Filters → **Show Redirectors** (or Miscellaneous → Redirectors) → right-click redirector → **Fixup** → **Save All**. See [UE58_REDIRECTOR_CLEANUP.md](UE58_REDIRECTOR_CLEANUP.md). Do **not** search for the old “Fix Up Redirectors in Folder” label — it is not in UE 5.8.
3. Re-run `audit_material_library.py` — `melodia_path_refs` inside Materials should trend to **0**.
4. Spot-check: open `MI_SDF_Gothic_RoseGold`, `M_SDF_TrueParallax` — no pink texture slots.

**Exit:** Zero redirectors under Materials; no `/Game/_PROJECT/` strings in EnvSandbox materials (grep or audit script).

---

### Phase 4 — Duplicate merge (~30 min)

| Situation | Action |
|-----------|--------|
| Same stem in `SDF/Textures/` + `_PROJECT/.../Textures/` | Keep both; rewire EnvSandbox materials to portfolio copy; leave `_PROJECT` copy in place |
| Same stem in `SDF/Textures/` + `Content/Textures/` | Keep `SDF/Textures/`; delete root `Content/Textures/` copy after rewire |
| Same stem in two portfolio subfolders | Merge into schema path; fix redirector |
| Visually identical, different names | Pick one `T_*` name; instance overrides for tint/scale |

**Tooling:** Reference Viewer → **Manage Dependencies** → see who uses each texture.

---

### Phase 5 — Naming compliance (~30 min)

Schema: [`MATERIAL_MIGRATION.md`](MATERIAL_MIGRATION.md) § Folder & naming.

| Folder | Prefix / pattern | Audit |
|--------|-------------------|-------|
| `Masters/` | `M_*` | No `MI_` in Masters |
| `SDF/Instances/` | `MI_Toon_SDF_*` or `MI_SDF_*` | No bare `M_SDF_*_Inst` left as primary assignable |
| `SDF/Textures/` | `T_*` or Melodia procedural names (`Marble_7_-_512x512`) | Prefer `T_` on next pass |
| `Instances/Environment/` | `MI_*` | No Melodia codenames |
| `Instances/Stylized/` | `MI_*` | — |
| `Functions/` | `MF_*` | — |
| `ToonProfiles/` | `TP_*` | — |
| `Impressionist/` | `M_Master_Impressionist_*`, `MI_Impressionist_*` | Documented extension; keep subtree self-contained |
| `PostProcess/` | `M_PP_*` | — |

- [ ] Rename or duplicate-and-replace (with redirector fix) any stragglers.
- [ ] Remove Melodia game names (`Musical`, `BeatSync`, character codenames) unless intentionally renamed.

---

### Phase 6 — Toon / Substrate compliance (~45 min)

Per master in `Masters/` and `Impressionist/Masters/`:

- [ ] Shading model: **Substrate Toon BSDF** → **Front Material** (not legacy Base Color-only root).
- [ ] Toon Profile assigned (`TP_*` under `ToonProfiles/`).
- [ ] Material compiles (no red nodes; no missing MooaToon custom nodes).
- [ ] Viewport: assign to `_Template` `Floor_0` + one vertical mesh — 2–3 readable shadow steps.

**Documented exceptions:** copied Melodia SDF masters awaiting Strategy C conversion may still be Default Lit / MooaToon until batch 3 — list them in commit notes, not as permanent exceptions.

---

### Phase 7 — Instance parent validation (~20 min)

- [ ] Every `MI_*` parent is an asset in `Masters/` (or documented style-local master under `Environments/<Style>/Materials/`).
- [ ] `MI_Toon_SDF_*` parents → `M_Toon_SDF`.
- [ ] `MI_SDF_*` parents → correct batch-2 master (`M_SDF_FiligreeRim`, etc.).
- [ ] No instance parent still pointing at `/Game/_PROJECT/...`.
- [ ] Scalar overrides only on instances — no unique graph logic trapped in instances.

---

### Phase 8 — MeshBlend compat (~20 min)

- [ ] `MF_MeshBlend_Activator_Index_0/1` in `Functions/` compile.
- [ ] If `MF_MeshBlend_Activator_Index` missing: copy from Melodia `G:\Melodia\Content\Art\Materials\Master\Materials\` into `Functions/` **or** rewire subgraph to portfolio `MF_*`.
- [ ] Test `M_HybridStone_SDF`, `M_SDF_HybridStone` on a mesh with activator — blend weights respond.

---

### Phase 9 — Final reference graph (~15 min)

1. Re-run `audit_material_library.py`.
2. Editor: **Reference Viewer** on `/Game/EnvSandbox/Materials` root — no external refs to `_PROJECT`, `Melodia`, or `Content/Textures/`.
3. **Size Map** (optional): confirm no multi-MB orphaned textures under Materials.
4. `Content/_PROJECT/` stays in the project — confirm portfolio materials load without depending on `_PROJECT` paths (see defer rules).

---

## Folder checklists (quick pass)

### `Masters/`

- [ ] Count matches migration batch log (~18 portfolio + copied Melodia until converted).
- [ ] Each master compiles; Toon or documented defer.
- [ ] Zero `_PROJECT` texture paths.
- [ ] Hybrid masters: MeshBlend function resolves.

### `SDF/`

**Instances/** — assignable surfaces only; parents valid.  
**Textures/** — all referenced; no orphans after rewire; no third copy in `Content/Textures/`.

### `Impressionist/`

- [ ] Self-contained subtree (`Masters/`, `Instances/`, uses `TP_Impressionist_*`).
- [ ] No accidental parent to copied MooaToon master.

### `Instances/` (`Environment/`, `Stylized/`)

- [ ] Folders exist; populate during batches 4–7.
- [ ] Empty folders OK at audit time.

### `Textures/` (schema)

Only `SDF/Textures/` (+ per-style overrides under `Environments/...` if added later).

---

## Automation vs manual

| Step | Script / tool |
|------|----------------|
| Inventory, orphans, dead refs, `_PROJECT` grep | `audit_material_library.py` |
| Redirectors | `fix_migration_redirectors.py` or **Fix Up Redirectors in Folder** |
| Melodia source inventory (read-only) | `scan_melodia_materials.py` on `G:\Melodia\Content` |
| Per-asset dependency graph | Editor **Reference Viewer** |
| Broken texture compile errors | Output Log after **Apply** in Material Editor |
| Batch Toon setup (not audit) | `setup_sdf_materials.py`, `setup_impressionist_materials.py` |

---

## Acceptance criteria (sign-off)

- [ ] `audit_material_library.py`: `missing_texture_refs` = **0**, `melodia_path_refs` in EnvSandbox = **0**
- [ ] `orphan_textures` = **0** (or each listed as intentional with owner master)
- [ ] Zero redirectors under `/Game/EnvSandbox/Materials`
- [ ] All portfolio masters on **Substrate Toon** or explicit defer list in `MATERIAL_MIGRATION.md`
- [ ] Naming matches schema (§ Phase 5)
- [ ] `_Template` viewport pass: no pink materials on test meshes
- [ ] EnvSandbox materials load with zero `_PROJECT` path dependencies (`Content/_PROJECT/` remains on disk)

---

## Defer rules — delete vs keep (EnvSandbox scope only)

| Asset / folder | Verdict |
|----------------|---------|
| `Content/_PROJECT/` | **Keep permanently** — source work / legacy library; never auto-delete or remove from project via this audit |
| `Content/Textures/` duplicate of `SDF/Textures/` | **Delete** duplicate under `Content/Textures/` after EnvSandbox rewire (not `_PROJECT`) |
| Orphan texture in `SDF/Textures/` (never referenced) | **Delete** or **Archive** to `_Dev/MelodiaMigration/Textures/` |
| Copied Melodia master superseded by `M_Toon_SDF` / batch-2 master | **Delete** EnvSandbox copy after instance parents retargeted |
| `ML_*` material layers, dev/test Melodia assets | **Do not copy** into EnvSandbox; if present there, **Delete** |
| `M_SDF_Musical`, underwater, math-art SDF | **Defer** — do not audit for portfolio |
| `MF_MeshBlend_*` with missing parent | **Fix** (copy source MF) — do not delete until rewired |
| `Impressionist/` subtree | **Keep** — parallel style system |
| `Surfaces_CC0/`, `UltraDynamicSky/`, template packs | **Keep** — not part of EnvSandbox material schema |
| Triplicate marble/perlin/voronoi (portfolio + `_PROJECT` + `Textures/`) | **OK short-term** — portfolio uses `SDF/Textures/`; `_PROJECT` copies stay |

---

## Recommended first pass (after your migration send-over)

1. Run `audit_material_library.py` → save JSON baseline.
2. `fix_migration_redirectors.py` + manual redirector fix.
3. Rewire **top 5 texture offenders** on copied masters (`Marble_7`, `Perlin_1`, `Voronoi_2`, `Voronoi_11`, `Marble_3`) from `_PROJECT` paths to `SDF/Textures/`.
4. Copy `MF_MeshBlend_Activator_Index` from Melodia into `Functions/`; fix 11 hybrid master refs.
5. Viewport smoke test on `_Template`.
6. Re-run audit — confirm `melodia_path_refs` dropped.
7. Schedule full Phase 1–9 sweep to finish EnvSandbox path rewiring (`_PROJECT` library stays on disk).

---

## Melodia cross-check — patterns to avoid copying

Common dead-weight texture sources in `G:\Melodia\Content` (do not robocopy blindly):

| Pattern | Risk |
|---------|------|
| `04_Materials/MATERIALLAYERS/` (`ML_*`) | Layer stacks; not portable to Substrate Toon |
| `Dev/`, `TestBench`, `*Test*` | Dev-only; breaks compile when MooaToon nodes missing |
| `*Musical*`, `*Music_*`, `*Beat*`, `*Vinyl*`, `*Staff*` | Game-specific; defer per migration doc |
| `*Temp*`, `*WIP*`, `*Scratch*` | ~100+ texture-name hits; discard |
| `*_OLD`, `/old/` paths | Superseded duplicates |
| `Underwater/`, Mandelbrot/Julia SDF textures | Tier B defer |
| `MPC_Melodia_Palette` | Parameter collection — rebuild as portfolio MPC if needed |
| `Cosmo/`, `water/` masters' texture sets | Only copy if actively porting those masters |
| `Grainy_*`, `Swirl_*` | Often chained in Melodia masters — copy **only** if target master uses them |

**Rule of thumb:** copy textures **with** the master you are converting in the same session; run audit immediately after.

---

*Last updated: 2026-06-19 — `_PROJECT` permanent retention policy; baseline from `audit_material_library.py` mid-migration*
