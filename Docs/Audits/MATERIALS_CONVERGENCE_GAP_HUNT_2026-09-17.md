# Materials convergence gap hunt ΓÇö 2026-09-17

**Owner:** Fromage ┬╖ **Executor:** Melodia study bot (inventory only)  
**Machine (target):** fromage `6402dab1-6635-4abb-8220-27a07354b444`  
**Repo tip (owner):** `C:\EnvironmentPortfolio\BS_GodFile` (MelodiaMelusinaV2)  
**Stamp:** 2026-09-17 ~19:41 EDT (America/Toronto)  
**Mode:** **Inventory + plan only** ΓÇö **0 converts**, **0 proof batches**, **no** Monolith `save_packages` / `recompile_material`  
**Monolith:** **not used** (`http://127.0.0.1:9316` connection refused on executor box; no Monolith MCP on this surface)

---

## 1. Scope + treatment bar + method

### Scope

Project-wide hunt for remaining packs/folders whose `MI_*` (or stock `M_*` masters used as instances) still sit on **stock / imported / marketplace parents** and lack:

1. **Melodia / Custom_MS pipeline master** retarget, and  
2. **Chladni love** (pitch/emissive cymatics wiring via sheep-coat pattern params + `MPC_Cymatics_Driver`), not parent-retarget alone.

**Out of this pass's conversion lane:** Megascans + Brushify Floating Islands (New Bot **IN_PROGRESS**). Do not collide.

### Treatment bar (convergence)

| Bar | Requirement |
|-----|-------------|
| **1) Retarget** | Imported MIs ΓåÆ Melodia / Custom pipeline masters ΓÇö **not** stock Quixel / MSPresets-material / marketplace parents |
| **2) Chladni love** | Pitch/emissive cymatics wiring (sheep-coat pattern / `MPC_Cymatics` bus) ΓÇö **not** parent-retarget only |

**Custom_MS authority targets** (from New Bot Megascans/Brushify playbook):

```
/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault
/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage
  (+ NoOpacity, NoWPO, NoOpacityNoWPO variants)
```

**Chladni reference (sheep coat):**  
`/Game/Melodia/Companions/ChoralSheep/Materials/MI_ChoralSheep_Body_Chladni_C` ┬╖ pattern `T_Chladni_C_ROOT` ┬╖ bus `/Game/Melodia/Cymatics/MPC_Cymatics_Driver`  
Params: `ChladniIntensity`, `ChladniEmissiveStrength`, `ChladniSheenStrength`, `HarmonizeActive`, `BeatAccent`, `Cymatic_ModeN/M`, pearl/lilac vectors, `ChladniPatternTexture`.  
Env guidance: subtle emissive (intensity ~0.15ΓÇô0.35; emissive ~0.2ΓÇô0.8) ΓÇö **do not destroy PBR albedo**.

If Custom_MS lacks Chladni slots ΓåÆ **wrapper path** under `/Game/Melodia/Materials/Env/Chladni/` (document; do not graph-surgery / recompile).

### Method (this pass)

| Step | Result |
|------|--------|
| Disk scan `Content/**/MI_*.uasset` on fromage | **Blocked** ΓÇö executor has no MachineShell / CopyToBox to `6402dab1-ΓÇª` |
| Git `main` Content tree walk (GitHub MCP) | Pack roots + git-tracked MI clusters counted |
| `Docs/SOURCES_MATRIX.md` | Maps local-only packs (Megascans, Brushify, Custom, Library, ΓÇª) not all present on git tip |
| `Docs/Materials/LABEL_MAP_2026-09-09.md` + Package A / closeout receipts | EXCLUDE Melodia-wired + LEGACY/QUARANTINE stamps |
| New Bot receipt `IMPORT_MATS_MEGASCANS_BRUSHIFY_CHLADNI_2026-09-17.md` | Owner disk counts Megascans ~237 / Brushify ~111; New Bot lane ownership |
| Monolith parent histogram | **Not run** ΓÇö Monolith unavailable on executor |

**Confidence:** Pack existence + git-tracked MI counts = **high**. Live parent class (still stock Quixel vs already Universal/Custom_MS) = **hypothesis until fromage census**. Counts marked `git` vs `owner-disk` vs `unknown-live`.

---

## 2. EXCLUDE list

### 2A. New Bot IN_PROGRESS ΓÇö do not convert / do not steal

| Pack | Approx MI | Notes |
|------|-----------|-------|
| **Megascans** (`Content/Megascans`) | ~**237** `MI_*` (owner disk) | Custom_MS + Chladni ΓÇö New Bot playbook/receipt 2026-09-17; live batch **blocked** on their surface too |
| **Brushify Floating Islands** (`Content/Brushify - Floating Islands/ΓÇª`) | ~**111** `MI_*` + ~19 `M_*` (owner disk) | Pipeline + Chladni; landscape **defer**; Greybox dupes ΓåÆ prefer primary |

### 2B. Already Melodia-wired / SHIP (LABEL_MAP + receipts) ΓÇö do not re-convert

| Family / asset | Soft path / pattern | Why excluded |
|----------------|---------------------|--------------|
| Sheep coats / Chladni fleece | `M_Chorus_Wool_Master`, `MI_ChoralSheep_Body*`, `MI_ChoralSheep_Body_Chladni_C` | Chladni **authority** |
| SurrealFabric flipbook lookdev | `M_SurrealFabric_Flipbook`, `MI_SurrealFabric_CelestialSilk` / `CymaticPulse` / `BrassPatina` | Melodia master + lookdev (Ctrl+S owed) |
| Nikki healthy landscape | `M_Master_Nikki_Landscape` + **9** Nikki MIs; `MI_NikkiIntegrated_*`; `MI_Landscape_NikkiDream` | Landscape SHIP |
| Melodia/_PROJECT VFX Flipbook + Static_Glint | `M_Niagara_MelodiaFlipbook`, `MI_Niagara_Melodia_Static_Glint` | VFX SHIP (twin redirect still owed on depends_on) |
| Sheep VFX consumers | `MI_NS_ChoralSheep_WoolMote`, `BeatStar` | Melodia/_PROJECT parents |
| Oceanology Melodia | `M_Water_Oceanology_Melodia`, `MI_Oceanology_Melodia_Hero` | Ocean SHIP |
| SDF SHIP masters / instances | `M_Master_SDF_Toon`, `M_Toon_SDF`, `M_SDF_OrnamentLayer`, `M_SDF_GildedFiligree` | Blessed SDF |
| Universal toon spine | `M_Master_Toon_Universal` (+ Batch 4 Cymatic_* present) | Melodia env spine (Chladni param exposure still pack-dependent) |
| Clean-env stubs | `MI_Melodia_Stub_Toon`, `MI_Melodia_Stub_Fabric` | Lookdev stubs ΓÇö not marketplace gaps |
| Cymatics bus | `MPC_Cymatics_Driver` | Shared bus SHIP |
| HeightBlend / false ocean / Enhanced SDF | LABEL_MAP **LEGACY** / **QUARANTINE** | Owned stamps (#158 HeightBlend; do not steal) ΓÇö not Custom_MS queue |
| Kenney greybox blockout | PCG / Kenney rewire bans in audits | **Do not rewire** as convergence |
| UltraDynamicSky system mats | `Content/UltraDynamicSky/Materials/**` | Sky/weather system ΓÇö leave stock; not surface Chladni |
| ArtOfShader / IMPERFECTER PP | Post-process packs | Not env surface convergence |
| MetaSound `MSPresets` | SOURCES_MATRIX = audio chain | **Not** Quixel material MSPresets |

Discover more EXCLUDES from: `Docs/Materials/LABEL_MAP_2026-09-09.md`, `Saved/Audit/PACKAGE_A_*`, `MATERIALS_CLEAN_LOOP_FOLDIN_*`, `IMPORT_MATS_MEGASCANS_BRUSHIFY_CHLADNI_*`, `Docs/SOURCES_MATRIX.md`.

---

## 3. Ranked gap queue

| Pack name | Approx MI count | Current parent pattern (hypothesized / known) | Suggested Melodia/Custom master | Chladni readiness | Priority |
|-----------|-----------------|-----------------------------------------------|----------------------------------|-------------------|----------|
| **KitBash3D Atlantis** (`EnvSandbox/Materials/Instances/Atlantis` + `PBR_Auto/MI_KB3D_ATL_*`) | **~83** git Atlantis folder + **~28** KB3D_ATL twins in PBR_Auto (overlap likely) | Stock KitBash / Atlantis masters **or** already Universal (PBR_Auto name) ΓÇö **live parent census owed** | Surface ΓåÆ `M_MS_CustomDefault`; foliage/cards ΓåÆ CustomFoliage / Universal; fabric ΓåÆ Universal or SurrealFabric case-by-case | Rock/stone/wood: **needs wrapper** if Custom_MS lacks slots; fabric: soft emissive only | **P0** |
| **KitBash Enchanted Vehicles** (`Content/KitBash_EnchantedVehicles`) | **~22** git `M_KB3D_ECV_*` (masters, not MI_*) | Stock KitBash3D marketplace masters | Create Melodia MIs on `M_MS_CustomDefault` / Universal; mesh slot retarget later | Fabric/gold/wood: wrapper likely; skip plastic/cable | **P0** |
| **BlingVol3** (`Instances/BlingVol3` + PBR_Auto `MI_T_Bling_*` / `MI_bling_surface_vol3_*`) | **~15** dedicated + **~15ΓÇô30** PBR_Auto bling/rhinestone (dedupe owed) | Marketplace bling masters **or** Universal | `M_MS_CustomDefault` or Universal metallic path | **High Chladni fit** (emissive sparkle) ΓÇö slots? else wrapper | **P0** |
| **Quixel leftovers outside Megascans tree** | **unknown-live** (local `Custom` / stray Quixel / material MSPresets if present) | Stock Quixel / VT / RealityScan | Same as Megascans ΓåÆ Custom_MS | Same AΓåÆB Chladni strategy | **P1** (census first; do not steal Megascans tree) |
| **Greybox_Kit Brushify twins** | **unknown-live** (owner note: dupes under Greybox) | Brushify / Greybox copies | Prefer primary Brushify pack; twin = note-only | Defer Chladni to primary | **P1** collision ΓÇö wait New Bot |
| **Magician's Library** (SOURCES: `EnvSandbox/Library/Migrated/MagiciansLibrary`, `magicianlabatory`, `Library`) | **unknown-live** (migrated pack; git tip may omit) | Coreb marketplace masters | Custom_MS / Universal after census | Prop surfaces: wrapper | **P1** |
| **EnvSandbox PBR_Auto mixed bulk** (non-KB3D / non-bling Melodia-named MIs) | **~80+** remaining in folder after marketplace slices | Many already Universal (pipeline name) | Leave if Melodia parent; only retarget proven stock | Chladni only if hero surface | **P2** (parent histogram first) |
| **GrandWater / false ocean** (`Instances/Water` GrandWater + v7/v9/v10) | **~9+** GrandWater + version folders | LEGACY false ocean authorities | ΓåÆ `M_Water_Oceanology_Melodia` (not Custom_MS) | Water cymatics = Oceanology/Melodia path ΓÇö **not** sheep Chladni pattern | **P2** (water lane; LABEL_MAP) |
| **HeightBlend leftovers** | **27** live (fold-in 1745) | `M_Master_Toon_Landscape_HeightBlend` | ΓåÆ Nikki landscape (#158 owns) | Landscape: special; not Custom_MS Chladni | **P2** ΓÇö **do not steal #158** |
| **Kenney RetroFantasyKit** | **~7** git | Kenney / Universal | Leave / archive bare names (existing org scripts) | Skip Chladni | **P3** ΓÇö greybox ban |
| **UltraDynamicSky** | system Weather/MF tree (few MI surface) | UDS masters | **Leave stock** | N/A | **P3** / EXCLUDE system |
| **Surfaces_CC0 / SurrealRocks / Alphas_Sparkles** (SOURCES pending/verified) | **unknown-live** | Mixed CC0 / stock | Universal or Custom_MS if PBR | Optional soft Chladni | **P3** after census |
| **TurnBasedJRPGTemplate / NPCs marketplace** | character/UI ΓÇö out of env surface | Template | Character Melodia masters | Character Chladni separate | **P3** env-out |

---

## 4. Top 5 next packs AFTER Megascans / Brushify

Explicit queue for whoever picks up **after** New Bot finishes Megascans + Brushify non-landscape:

| Rank | Pack | Approx count | Why next | First live action |
|------|------|--------------|----------|-------------------|
| **1** | **KitBash3D Atlantis** (`/Game/EnvSandbox/Materials/Instances/Atlantis` + `ΓÇª/PBR_Auto/MI_KB3D_ATL_*`) | ~**83** + ~**28** twin names | Largest git-tracked marketplace kitbash surface corpus; rock/cliff Chladni candidates | Parent histogram ΓåÆ Custom_MS vs Universal split ΓåÆ 10 MI proof **only after** Megascans proof path proven |
| **2** | **KitBash Enchanted Vehicles** (`/Game/KitBash_EnchantedVehicles`) | ~**22** `M_KB3D_ECV_*` | Stock masters still at pack root; provenance pending in SOURCES | Inventory mesh slots; author Melodia MIs (no mass convert until parent schema known) |
| **3** | **BlingVol3** | ~**15ΓÇô45** (dedupe) | Emissive/sparkle = natural Chladni love | Probe parent + Chladni slots; tiny 3-MI lookdev only if safe |
| **4** | **Quixel leftovers outside Megascans** | census | Same Custom_MS spine as Megascans without colliding New Bot tree | PowerShell: find `MI_*.uasset` under Quixel/Custom/MS material presets **excluding** `Content\Megascans` |
| **5** | **Magician's Library migrated** | census | Marketplace props still in EnvSandbox/Library paths | Disk count + parent histogram; prefer Universal for props if already Nikki-adjacent |

**Honorable mention (not Top 5):** Greybox Brushify twins ΓÇö track for collision only; prefer primary Brushify.

---

## 5. Open risks / collisions

| Risk | Detail | Mitigation |
|------|--------|------------|
| **New Bot Megascans/Brushify lane** | Concurrent Custom_MS + Chladni work | This hunt **excludes**; no proof batch this pass |
| **Greybox Brushify dupes** | Twin trees confuse counts / double-convert | Prefer `/Game/Brushify - Floating Islands/...`; Greybox = note-only |
| **Custom_MS lacks Chladni slots** | Likely (New Bot ┬º11) | Probe params; use Melodia env wrapper ΓÇö **no** `recompile_material` |
| **PBR_Auto false security** | Folder name Γëá Melodia parent | Live `get_material_properties` / parent histogram required |
| **Atlantis vs KB3D_ATL twins** | Duplicate instance trees | Pick one authority folder; archive twin after redirect |
| **#158 HeightBlend** | 27 LEGACY MIs | Do not steal; not Custom_MS queue |
| **False ocean GrandWater** | Water LEGACY | Route to Oceanology Melodia ΓÇö separate from Chladni surface |
| **Kenney / greybox bans** | Audits forbid Kenney greybox rewire | Leave P3 |
| **Local-only Content** | Megascans/Brushify/Custom often **not** on git `main` tip | Fromage disk census is SSOT for counts |
| **Executor surface** | No MachineShell / Monolith on study box | Docs + git inventory only; parent CopyToBox for `Saved/Audit` |

---

## 6. Convert this pass?

**None.** Prefer inventory only. No tiny proof batch ΓÇö would collide with New Bot Megascans/Brushify lanes and cannot verify parents without Monolith.

---

## 7. Fromage live census recipe (when MachineShell + Monolith up)

```powershell
$root = 'C:\EnvironmentPortfolio\BS_GodFile\Content'
# Already owned (note only):
(Get-ChildItem "$root\Megascans" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue).Count
(Get-ChildItem "$root\Brushify - Floating Islands" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue).Count
# Gap candidates:
(Get-ChildItem "$root\KitBash_EnchantedVehicles" -Recurse -Filter 'M_*.uasset' -EA SilentlyContinue).Count
(Get-ChildItem "$root\EnvSandbox\Materials\Instances\Atlantis" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue).Count
(Get-ChildItem "$root\EnvSandbox\Materials\Instances\BlingVol3" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue).Count
(Get-ChildItem "$root\Greybox_Kit" -Recurse -Directory -Filter '*Brushify*' -EA SilentlyContinue | ForEach-Object {
  [pscustomobject]@{ Path=$_.FullName; MI=(Get-ChildItem $_.FullName -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue).Count }
})
# Quixel leftovers outside Megascans:
Get-ChildItem $root -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue |
  Where-Object { $_.FullName -match 'Quixel|MSPresets|Megascans' -and $_.FullName -notmatch '\\Megascans\\' } |
  Group-Object { Split-Path (Split-Path $_.FullName) } | Sort-Object Count -Desc
```

Monolith (read-only): parent histogram for Atlantis, KitBash ECV, BlingVol3; `get_material_parameters` on `M_MS_CustomDefault` for Chladni slot presence.

---

## 8. Deliverable paths

| Role | Path |
|------|------|
| Owner disk (CopyToBox target) | `C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md` |
| Trackable docs | `Docs/Audits/MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md` |
| Box staging | `/workspace/materials-convergence-gap/Saved/Audit/` + `Docs/Audits/` |

---

## 9. Related receipts

- `Saved/Audit/IMPORT_MATS_MEGASCANS_BRUSHIFY_CHLADNI_2026-09-17.md` (New Bot lane)  
- `Docs/Materials/LABEL_MAP_2026-09-09.md`  
- `Docs/SOURCES_MATRIX.md`  
- `Docs/Audits/PACKAGE_A_MATERIALS_ORG_2026-09-17.md`  
- `Docs/Pipeline/MATERIAL_PIPELINE.md` (Universal spine Γëá Custom_MS overwrite spine)

---

**End of gap hunt ΓÇö inventory only.**
