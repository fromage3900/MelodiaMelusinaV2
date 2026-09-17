# Nikki-style PCG / Terrain / Heatmap LD Audit — 2026-09-17

**Stamp:** 2026-09-17 15:18 ET (America/Toronto)  
**Checkout tip:** `C:\EnvironmentPortfolio\BS_GodFile`  
**my-site tip:** `C:\Users\froma\my-site`  
**TD canon:** `C:\MelodiaTouchDesigner` (sibling `TD_RENDER_PIPELINE_AUDIT_2026-09-17.md`)  
**Lens:** Infinity Nikki–adjacent soft open-world / magical parkour LD for Melodia Melusina — **pattern language only, DO NOT copy IP**.  
**Rules:** no save_packages, no recompile_material, no #158 ownership steal, no Kenney greybox rewire.

**Method:** Live fromage Content walk unavailable to this executor (no `Shell.machineId`). Inventory reconstructed from prior fromage executor corpus + parent TD tips. Counts are lower-bound name-unique.

---

## 1) PCG graphs / volumes / musical heroes

### Canonical musical hero levels (EnvSandbox)
`/Game/EnvSandbox/PCG/Musical/Hero/`:
- `L_PCG_Hero_ArpeggioBridge`, `L_PCG_Hero_BellTreeGarden`, `L_PCG_Hero_CrystalHarpGrove`
- `L_PCG_Hero_ResonanceCathedral`, `L_PCG_Hero_ScaleWorldProof`, `L_PCG_Hero_WaterGameplayProof`, `L_PCG_Hero_XylophoneTrail`

Piano kit: `SM_PianoKey_*_Bevel`, `SM_Piano_Keybed` under `/Game/EnvSandbox/PCG/Musical/`.

### Graph name corpus
**~226 unique `PCG_*` names**, including:
- **Nikki-pattern / soft garden:** `PCG_Nikki_DreamStones`, `PCG_Nikki_MandalaBloom`, `PCG_Nikki_PhyllotaxisGarden(_Walkable)`, `PCG_MeadowBloom`, `PCG_MeadowScatter`, `PCG_LanternGrove`, `PCG_SakuraGrove`, `PCG_BlossomPath`, `PCG_Zen_MossGroundcover`
- **Sea Above dress:** `PCG_SeaAbove_*`
- **Baroque / cathedral / Bezier:** `PCG_Baroque*`, `PCG_Cathedral*`, `PCG_Bezier*`
- **Soft verticality / parkour:** `PCG_Escher*`, `PCG_FloatingStairways`, `PCG_WP_SpaceCathedral_*`
- **WP dressing:** `PCG_WP_SakuraDream_*`, `PCG_WP_BaroqueGrotto_*`, `PCG_WP_INFINITY_NIKKI_GREYBOX_PLAN` (plan name only)
- **Foliage / density:** `PCG_FoliageDensity`, `PCG_ForestScatter_BS`, `PCG_MelodiaForest_Landscape`
- **Greybox (do not rewire Kenney):** `PCG_GreyboxBlockout`, `PCG_Greybox_Minimal`, `PCG_Greybox_Standard`

Host: `APCGHeroMusicGraphHost` (music-as-key landmarks).  
Sea Above prior note: ~221 cathedral pieces; **2 PCG volumes**.

---

## 2) Mesh terrain placement patterns

### Gaea substrates (`Content/_PROJECT/ResonantWorld/Offline/GaeaSetups/`)
CadenceCrystalRidge, FugueGrotto, LiquidCathedral, SakuraTerrace — each with `L_Gaea_*_WP`, `SM_Gaea_*_1025`, substrate MI, HLOD instanced/merged.

### Glacier weightmaps (`Content/Gaea/Glacier/`)
Layers Base/Rock/Snow/Water; `W_Glacier_Rock`, `W_Glacier_Snow`, `W_Glacier_Water`; `MI_Glacier_Landscape_Layered`.  
Scripts: `import_gaea_glacier_weightmaps.py`, `audit_gaea_landscape_pipeline.py`.

### Landscape material authority
Ship: `M_Master_Nikki_Landscape`. Legacy HeightBlend leftovers = **owner lane only** (no #158 steal).  
Sea Above: `T_Gaea_SeaAbove_SuperColor.uasset`.

### Nikki LD reading
Clearing → path → soft vertical beat; companion-scale pockets; readable landmark silhouettes. Leave Kenney greybox as blockout only.

---

## 3) Heatmap usage
Tools: `Content/Python/audit_pcg_heatmap.py`, `audit_wp_human_scale_heatmap.py`, `pcg_heatmap_exporter.py`; `Tools/PCG/apply_sea_above_heatmap_dress.py`, `Tools/PCG/build_sea_above_heatmap_dress.py`; `specs/water_veil/sea_above_heatmap_dress.v1.json`.  
JSON names: `pcg_heatmap_2026-09-02.json`, `sea_above_terrain_heatmap.json`, `sea_above_terrain_heatmap_80.json`.  
Doc tokens: `PCG_HEATMAP_AUDIT_2026`, `PCG_HEATMAP_DRESS_PLAN_2026`.

Open: live heatmap texture census unverified; quad-mask hot-spikes if used as density — clamp/feather.

---

## 4) Melusina Morning / sheep / TD adjacency
- Map: `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- Sheep stills: `Saved/Screenshots/ChoralSheep_Proof`, `Saved/SemesterEvidence/2026-W37/ChoralSheep/ChladniFleece`
- Cymatics: UE `MPC_Cymatics_Driver` + Chladni (game authority)
- TD presentation: `C:\MelodiaTouchDesigner` toes `grandmaster_melodia7(.3).toe` — downstream only
- **FROZEN mirror (do not edit):** `C:\EnvironmentPortfolio\_TouchDesigner`

---

## 5) Prioritized next actions
1. **P0** Parent push staging pack → Working + my-site heroes; CopyToBox UE_CF / ChladniFleece + **TD `scratch/portfolio_hero_renders` + `td/grandmaster_melodia/renders` + `exports/`** and promote strong stills.
2. **P0** Live PCG/Heatmap census on fromage; refresh JSON counts.
3. **P0** `audit_pcg_heatmap.py` dry-run on Sea Above volumes (no save).
4. **P1** MelusinaMorning clearing LD for sheep + Chladni close-up (PR #149 gate).
5. **P1** HeightBlend leftovers — owner only.
6. **P1** TD Spout/UE bridge health + `nikki_atlus_lookdev.cube` grade documented (see TD audit).
7. **Defer** Kenney rewires; IP-likeness beyond pattern language.

## Cross-links
- `Saved/Audit/TD_RENDER_PIPELINE_AUDIT_2026-09-17.md`
- `Docs/Materials/README.md` stamp (staging)
- `Saved/SemesterEvidence/2026-W38/MelusinaMorning_VFX/2026-09-17/NOTES_CURATED.md`

## Verification correction (2026-09-17 landing pass)

Live fromage Content recount (basename contains `PCG`, `*.uasset|*.umap` under `Content/`):
- raw matches: 280
- unique basenames: **276**
- under `\PCG\` folders: raw 322, unique **317**

Prior `pcg_assets: 226` came from offline corpus reconstruct (JSON method field). Replace folklore 226 with live unique basename **276** unless a narrower rule is declared.

Git: `Saved/` is gitignored — this Docs/Audits copy is the trackable authority.
