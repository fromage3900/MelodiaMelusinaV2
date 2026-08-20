# Toon Migration Runbook — Melodia → BS_GodFile (UE 5.8)

Systematic playbook for converting **all portfolio-relevant** Melodia materials to **stock UE 5.8 Substrate Toon** in `BS_GodFile`. Use this instead of ad-hoc robocopy.

**Companion docs:** `MATERIAL_MIGRATION.md` (folder schema, batch log), `SANDBOX_LONGTERM_PLAN.md` (architecture rules).

**Legacy library:** `Content/_PROJECT/` stays in the project permanently — never delete or archive as part of this runbook. Deprecation steps below apply only to superseded copies under `/Game/EnvSandbox/Materials/`, not `_PROJECT`.

**Inventory tool:** `Content/Python/scan_melodia_materials.py` — re-run after Melodia changes.

*Last inventory scan: 2026-06-19*

---

## Executive summary

| Metric | Count |
|--------|------:|
| Melodia material-like assets (`M_/MI_/ML_/MF_/MPC_`) | **517** |
| Melodia textures (`T_` or under `Textures/`) | **174** |
| Portfolio-relevant masters (excludes defer) | **~107** |
| Already in `/Game/EnvSandbox/Materials/` | **47** on disk |
| **Remaining portfolio work** | **~95 masters + ~80 instances/MIs** |
| Defer (game/VFX/dev/layers/UI) | **46** + Tier B/C SDF |

**Done so far**

| Batch | What | Count |
|-------|------|------:|
| Batch 1a | Robocopy Melodia SDF masters + textures + 2 MFs | 16 M + 9 T + 2 MF |
| Batch 1b | `setup_sdf_materials.py` — Substrate Toon proxy master + instances + profiles | 1 M + 5 MI + 4 TP |
| Batch 2 | UnrealMCP fancy SDF masters (portfolio originals) | 5 M + 5 MI |

**Critical gap:** 12 copied Melodia SDF masters are still **Melodia graphs** (MooaToon / Default Lit output). Batch 2 created **new** toon masters but did not retarget the copies. Conversion is the main work ahead.

---

## 1. Full remaining inventory

### 1.1 Counts by category (Melodia `G:\Melodia\Content`)

| Category | Total | M | MI | ML | MF | Notes |
|----------|------:|--:|---:|---:|---:|-------|
| **SDF (Tier A env)** | 40 | 30 | 10 | — | — | Gothic/baroque/cathedral kit |
| **SDF underwater (Tier B)** | 9 | 9 | — | — | — | Defer until underwater style |
| **SDF math-art (Tier B)** | 5 | 5 | — | — | — | Demo/reference only |
| **Environment** | 186 | 145 | 21 | — | 16 | Stone, trim, oil paint, hybrid |
| **Landscape** | 12 | 5 | 7 | — | — | Height/layer blend |
| **Foliage** | 5 | 3 | 1 | — | 1 | Grass, gold leaf |
| **Stylized / MooaToon** | 56 | 49 | 4 | — | 3 | → `M_Master_Toon` family |
| **Character** | 4 | 4 | — | — | — | Defer (no characters in portfolio) |
| **Post-process** | 7 | 3 | — | — | 4 | Outline + grade (skip ArtOfShader dupes) |
| **UI** | 3 | 3 | — | — | — | Defer |
| **Defer — material layers** | 26 | — | — | 26 | — | MooaToon `ML_*`; rebuild as `MF_*` if needed |
| **Defer — game/rhythm** | 14 | 9 | 5 | — | — | Musical motifs, audio-reactive |
| **Defer — VFX/combat** | 2 | 2 | — | — | — | Orbs, portals |
| **Defer — dev** | 1 | 1 | — | — | — | Test bench |
| **Other** | 147 | 40 | 45 | — | 59 | Mixed; filter per batch |

### 1.2 Migration status — SDF Tier A (29 masters)

| Status | Assets |
|--------|--------|
| **Toon built (batch 1b)** | `M_Toon_SDF`, `MI_Toon_SDF_{Wall,Floor,Accent,Rim,Ornamental}` |
| **Toon built (batch 2 MCP — 2026-06-19)** | `M_SDF_{ReliefPanel,FiligreeRim,GothicTracery,HybridStone,ParallaxPulse}` + 5 `MI_SDF_*` |
| **Copied, needs toon conversion (Strategy C)** | `M_SDF_TrueParallax`, `GildedStucco`, `GildedFiligree`, `Baroque`, `OrnamentLayer`, `OrnamentLayer_Enhanced`, `GothicArchitecture`, `GothicArchitecture_Enhanced`, `RoseWindow`, `RayMarch_Gothic`, `M_HybridStone_SDF`, `M_SDF_TrueParallax_Inst` |
| **Not yet copied — Tier A remaining (17)** | `M_SDF_BaroqueColumn`, `CathedralVault`, `CrystallineSpire`, `EscherGeometry_Enhanced`, `FlyingButtress`, `GildedAltar`, `GothicRoseWindow`, `Grass_Field`, `InfinityMirror`, `MengerSponge`, `MetalShards`, `Mobius_Strip`, `Penrose_Staircase`, `SierpinskiTetrahedron`, `StarburstGem`, `M_HybridLandscape_MooaToonSDF`, `M_HybridWater_SDF_Inst` |

### 1.3 Tier rules

| Tier | Rule | Action |
|------|------|--------|
| **A** | Baroque/gothic environment, cathedral kit, hybrid stone/water/grass | Migrate in batches 3–5 |
| **B** | Underwater SDF (9), math-art SDF (5), niche stylized | Defer until style needs them |
| **C** | Musical/rhythm (`M_SDF_Musical*`, `MI_Music_*`, `M_MusicalSDF_*`), combat VFX, dev/test, `ML_*` layers, UI | **Do not migrate** |

---

## 2. Systematic toon conversion pipeline

### Phase 0 — Prerequisites (once per machine)

1. **Engine:** UE 5.8 stock, `r.Substrate=True`, `r.Substrate.ProjectGBufferFormat=0` in `Config/DefaultEngine.ini`; restart editor.
2. **Plugins:** Python Editor Script Plugin, UnrealMCP (`Plugins/UnrealMCP`), PCG optional.
3. **Redirector hygiene:** After every robocopy batch, run:
   ```text
   py "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_migration_redirectors.py"
   ```
   If API missing → see [UE58_REDIRECTOR_CLEANUP.md](UE58_REDIRECTOR_CLEANUP.md): Filters → Show Redirectors → **Fixup**, or `py Content/Python/fix_migration_redirectors.py`. (The old “Fix Up Redirectors in Folder” label is not in UE 5.8.) → Save All.
4. **Master templates** (create before large instance work):
   - `M_Master_Toon` — opaque surfaces (stone, wood, fabric, trim)
   - `M_Master_Toon_SDF` — alias/evolution of `M_Toon_SDF` with texture-ramp hookup
   - `M_Master_Toon_Transparent` — glass/stained glass
   - `M_Master_Foliage` — two-sided vegetation
   - `M_Master_Landscape` — layer blend (later)
   - Toon Profiles: extend `TP_{Default,Stucco,Gold,Ornamental}` → add `TP_Stone`, `TP_Wood`, `TP_Glass`, `TP_Foliage`

### Phase 1 — Portfolio master templates

**Goal:** ≤6 masters cover 90% of instances.

| Master | Source inspiration (Melodia) | Output |
|--------|---------------------------|--------|
| `M_Master_Toon` | `M_Stone_*_Toon`, `M_Wood_Toon`, `M_Fabric_Toon`, `M_MooaToon_Master` | Substrate Toon BSDF ← albedo/tint + normal + roughness scalar |
| `M_Master_Toon_SDF` | `M_Toon_SDF` + batch 2 MCP masters | World/texture SDF bands → Toon BSDF |
| `M_Master_Toon_Transparent` | `M_Glass_Refract_Toon`, `M_LF_StainedGlass` | Toon BSDF + opacity |
| `M_Master_Foliage` | `M_Vegetation_Grass_Toon`, `M_MooaToon_GoldLeaf` | Two-sided + wind scalar (no gameplay) |

Build `M_Master_Toon` first via `setup_sdf_materials.py` pattern or MCP; **wire Substrate Toon BSDF → Front Material manually** (see blockers).

### Phase 2 — Batch copy (robocopy)

**Never copy whole `04_Materials`.** Copy per batch into schema paths:

```powershell
# Example: Batch 3 cathedral SDF pack
$src = "G:\Melodia\Content\_PROJECT\04_Materials\SDF"
$dst = "C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Materials\Masters"
robocopy $src $dst M_SDF_CathedralVault.uasset M_SDF_FlyingButtress.uasset /NFL /NDL
# Textures referenced by those masters — copy to SDF/Textures/<Category>/
```

After copy: open project → run `fix_migration_redirectors.py` → fix broken texture paths in Content Browser.

### Phase 3 — Toon retarget strategies

| Strategy | When | Steps | MCP vs manual |
|----------|------|-------|---------------|
| **A — Instance-only** | Parent already Substrate Toon (`M_Master_Toon*`) | Duplicate Melodia `MI_*` → set parent to portfolio master → copy scalar/vector params → assign `TP_*` on instance | 90% MCP (`create_material_instance`) |
| **B — Graph rebuild** | Batch 2-style fancy surfaces (noise/Voronoi/marble) | MCP: `create_material_asset` → expressions → connect color chain → **manual** Toon BSDF + Front Material → `create_material_instance` | 70% MCP / 30% manual Toon pin |
| **C — Raymarch SDF keep** | Copied Melodia `M_SDF_*` with raymarch/custom nodes | Open graph → delete MooaToon output node → insert `SubstrateToonBSDF` fed by existing color → connect **Front Material** → recompile | 10% MCP / 90% manual |

**Strategy C workflow (per copied master):**

1. Open `M_SDF_*` in Material Editor.
2. Find final color output (before old MooaToon / Default Lit root).
3. Add `Substrate Toon BSDF`, assign `TP_*`.
4. Connect color → BaseColor/DiffuseColor; connect BSDF → **Front Material**.
5. Remove broken MooaToon custom nodes if compile errors (keep math).
6. Save → assign to `_Template` test mesh → viewport orbit.

### Phase 4 — Validation checklist (every batch)

- [ ] All new assets under `/Game/EnvSandbox/Materials/` (no stray `/Game/Materials/`)
- [ ] Zero redirectors in folder (script or manual fix)
- [ ] Each master compiles (no red nodes; no MooaToon missing)
- [ ] Viewport: `_Template` — test on `Floor_0` + one vertical mesh + one curved mesh
- [ ] Toon ramps readable (2–3 discrete shadow steps, gold spec band on accents)
- [ ] MeshBlend: if hybrid master, test with `MF_MeshBlend_Activator_*` activator
- [ ] Git: commit batch as one milestone (materials + doc update only)

### Phase 5 — Deprecation (EnvSandbox copies only)

1. Hide (editor) or delete **EnvSandbox** copied Melodia masters once portfolio toon replacement validates — not assets under `Content/_PROJECT/`.
2. Remove references to `M_MooaToon_*`, Default Lit-only masters from `_Template` and environment maps.
3. Do **not** install MooaToon plugin in BS_GodFile.

---

## 3. Batch schedule

Estimates assume one focused session (~2–4 h) per batch.

### Batch 3 — Tier A SDF completion (recommended next)

| Item | Count | Strategy | MCP / manual |
|------|------:|----------|--------------|
| Convert 12 already-copied SDF masters to Toon | 12 | C | 10% / 90% |
| Robocopy + convert high-priority missing | 6 | C | 5 masters manual-heavy |
| New instances tuning Gothic/Rose | 6–8 MI | A | MCP instances |

**Priority missing masters:** `CathedralVault`, `FlyingButtress`, `BaroqueColumn`, `GildedAltar`, `Grass_Field`, `GothicRoseWindow`.

**Skip in batch 3:** math-art, underwater, Tier C musical.

### Batch 4 — `M_Master_Toon` environment pack

| Item | Count | Strategy | MCP / manual |
|------|------:|----------|--------------|
| Build `M_Master_Toon` + 4 TP variants | 1 M + 4 TP | B + manual Toon | 50% / 50% |
| Surface masters → instances | ~12 MI | A | 90% MCP |
| Key Melodia sources | `M_Stone_{Rough,Smooth}_Toon`, `M_Wood_Toon`, `M_Fabric_Toon`, `M_Leather_Toon`, `M_OilPainting_Gold_Baroque`, `M_MooaToon_Marble_Veined_v2`, `M_CathedralFloor_Textured` | | |

### Batch 5 — Landscape + hybrid + foliage

| Item | Count | Strategy | MCP / manual |
|------|------:|----------|--------------|
| `M_Master_Landscape` + layer infos | 1 M | Manual + MCP layer tools | 40% / 60% |
| Hybrid landscape/water SDF | 2 M | C | Manual |
| Foliage master + grass instance | 2 M + 2 MI | B/A | Mixed |
| Sources | `M_HybridLandscape_MooaToonSDF`, `M_HybridWater_SDF_Inst`, `M_Landscape_HeightBlend`, `M_Vegetation_Grass_Toon` | | |

### Batch 6 — Glass + trim + post-process

| Item | Count | Strategy |
|------|------:|----------|
| Stained glass / refract | 2 M | B + transparent master |
| Trim/concrete instances | 4–6 MI | A |
| `M_PP_ToonOutline` | 1 M | MCP expressions + manual output |

### Batch 7+ — Stylized MooaToon facades (optional)

Convert selected `M_MooaToon_Facade_*`, `Veins_*`, `Halftone_Universal` into **`MI_*` on `M_Master_Toon_SDF`** — only if a portfolio style needs that look. Otherwise defer.

### Defer indefinitely

- Tier B underwater (9) + math (5)
- Tier C game (14) + VFX (2) + dev (1) + UI (3) + ML layers (26)
- ArtOfShader pack — **already in BS_GodFile**; do not re-migrate from Melodia
- Character materials (4)

---

## 4. Automation tooling

### 4.1 Scripts (BS_GodFile `Content/Python/`)

| Script | Purpose | When |
|--------|---------|------|
| `setup_sdf_materials.py` | Batch 1 toon master + 5 SDF instances + TP profiles | Re-run safe; rebuilds batch 1 |
| `fix_migration_redirectors.py` | Fix redirectors under `/Game/EnvSandbox/Materials` | **After every robocopy** |
| `scan_melodia_materials.py` | Regenerate inventory counts | Before planning next batch |
| `setup_template.py` | `_Template` level + PPV hooks | Once; add outline MI after batch 6 |

### 4.2 UnrealMCP batch pattern

Typical MCP sequence per new master (Strategy B):

```text
1. create_material_asset(name, path="/Game/EnvSandbox/Materials/Masters/")
2. add_material_expression × N  (VectorParameter, TextureSample, Multiply, Lerp, …)
3. connect_material_expressions (wire color chain)
4. [MANUAL] Substrate Toon BSDF → Front Material in editor
5. recompile_material
6. create_material_instance(name, parent_material, scalar_parameters, vector_parameters)
```

**MCP tools:** `create_material_asset`, `add_material_expression`, `connect_material_expressions`, `connect_to_material_output`, `create_material_instance`, `recompile_material`, `get_material_graph`.

**Known limit:** `connect_to_material_output` lists legacy pins only (`BaseColor`, `Roughness`, …) — **not `Front Material`**. Substrate Toon root requires manual wiring or Python (`setup_sdf_materials.py` `_connect_front_material` pattern).

### 4.3 Optional: bulk parent retarget commandlet

For many `MI_*` whose parent is already toon:

```python
# Future: Content/Python/retarget_material_instances.py
# For each MI in manifest: set_material_instance_parent(mi, new_master)
# Copy parameters by name intersection; log mismatches
```

Use when Batch 4 creates `M_Master_Toon` and you have 20+ Melodia instances to reparent.

### 4.4 Monolith vs UnrealMCP-only

| Tool | Install when | Skip when |
|------|--------------|-----------|
| **UnrealMCP** (installed) | Default for material creation, instances, graph reads | — |
| **Monolith** (`G:\Melodia\Plugins\Monolith`) | Need bulk asset ops, 1300+ actions, advanced graph surgery at scale | Batch 1–5 manageable with UnrealMCP + Python |

**Recommendation:** Stay UnrealMCP-only through Batch 5. Evaluate Monolith if Batch 7 stylized conversion becomes bottleneck.

---

## 5. Daily workflow

```text
1. Open BS_GodFile.uproject (UE 5.8)
2. Pull latest / confirm clean Content/EnvSandbox/Materials
3. Run batch robocopy (if copying new Melodia uassets)
4. py fix_migration_redirectors.py
5. MCP or manual: build/convert batch masters (Strategy A/B/C)
6. py setup_sdf_materials.py  (only if rebuilding batch 1 templates)
7. Viewport test in _Template — Floor_0 + wall mesh
8. Update batch table in MATERIAL_MIGRATION.md
9. Git commit milestone
```

**Session target:** 1 batch phase per day (3–6 masters converted + validated).

---

## 6. Blockers & mitigations

| Blocker | Impact | Mitigation |
|---------|--------|------------|
| **Substrate Toon via MCP** | Cannot auto-connect Front Material | Manual pin in editor; copy pattern from `setup_sdf_materials.py` |
| **Redirector paths** | Pink materials after robocopy | Always run `fix_migration_redirectors.py`; fix texture paths to `SDF/Textures/` |
| **MooaToon custom nodes** | Compile failures on copied graphs | Strategy C: bypass/delete custom nodes; keep math |
| **Raymarch SDF complexity** | Full parity expensive | Accept proxy bands (batch 1/2) first; true SDF textures later |
| **MeshBlend** | Hybrid stone needs activator MFs | Already copied `MF_MeshBlend_Activator_*`; test per hybrid master |

---

## 7. Success criteria

Migration is **complete for portfolio v1** when:

- All Tier A SDF have Substrate Toon output (proxy or converted raymarch)
- `M_Master_Toon` covers stone/wood/fabric/leather/trim with ≤15 instances
- `_Template` uses only `/Game/EnvSandbox/Materials/**` assets
- Zero MooaToon plugin references
- One baroque environment styled end-to-end with migrated materials

---

*Maintained with `scan_melodia_materials.py`. Update batch tables in `MATERIAL_MIGRATION.md` after each batch.*
