# Source Control Commit Plan — 2026-08-31

**Generated**: 2026-08-31T06:00:00Z  
**Source**: Saved/Audit/source_control_triage.json (1883 entries)  
**Branch**: main

---

## 1. COMMIT — Batch A: Core Production Changes

These are intentional, tracked production assets and tooling. Group into a single commit.

| # | Path | Status | Notes |
|---|------|--------|-------|
| 1 | `Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset` | M | Character BP |
| 2 | `Content/MelodiaIntegration/Blueprints/BP_Starskiff_MK2.uasset` | ?? | Vehicle BP |
| 3 | `Content/MelodiaIntegration/Blueprints/Opening/BP_KaleidoNaveArrivalTrigger.uasset` | M | Opening trigger |
| 4 | `Content/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig.uasset` | M | Integration config |
| 5 | `Content/MelodiaIntegration/Maps/MelodiaIntegrationMap.umap` | M | Main map |
| 6 | `Content/Melodia/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` | M | HUD widget |
| 7 | `Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset` | M | Anim BP |
| 8 | `Content/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair.uasset` | M | Water hair BP |
| 9 | `Content/Melodia/Characters/Melusina/Materials/MI_Melusina_SKIRT_003.uasset` | M | Skirt MI |
| 10 | `Content/Melodia/Characters/Melusina/Materials/MI_Melusina_skirtpanel_002.uasset` | M | Skirt MI |
| 11 | `Content/Melodia/Characters/Melusina/Materials/MI_Melusina_Dress_Shorewake.uasset` | ?? | New dress MI |
| 12 | `Content/Melodia/Characters/Melusina/Physics/DA_Melusina_HairCollisionLimits.uasset` | M | Physics |
| 13 | `Content/Melodia/Characters/Melusina/Physics/DA_Melusina_SkirtCollisionLimits.uasset` | M | Physics |
| 14 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_BaseColor.uasset` | ?? | Dress texture |
| 15 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Emission.uasset` | ?? | Dress texture |
| 16 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Normal.uasset` | ?? | Dress texture |
| 17 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_BaseColor.uasset` | ?? | Vehicle texture |
| 18 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_Normal.uasset` | ?? | Vehicle texture |
| 19 | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_Starskiff_Hull_Roughness.uasset` | ?? | Vehicle texture |

**Commit message**: `chore: integration BPs, dress textures, starskiff hull, anim/HUD/physics updates`

---

## 2. COMMIT — Batch B: Python Tooling

New Content/Python scripts. Standalone commit.

| # | Path | Status | Notes |
|---|------|--------|-------|
| 1 | `Content/Python/convert_arch_to_toon.py` | ?? | Arch-to-toon converter |
| 2 | `Content/Python/expand_cosmo_master.py` | ?? | Cosmo master expansion |
| 3 | `Content/Python/materialize_glitter_polished.py` | ?? | Glitter materializer |
| 4 | `Content/Python/materialize_seaabove_reef_shadowdream.py` | ?? | Reef materializer |

**Commit message**: `feat: add materialize_python scripts for arch-to-toon, glitter, reef`

---

## 3. COMMIT — Batch C: Docs/Plans

New planning docs. Standalone commit.

| # | Path | Status | Notes |
|---|------|--------|-------|
| 1 | `Docs/ECHO/campaign_05_ingest_report_2026-08-30.json` | ?? | ECHO report |
| 2 | `Docs/Plans/COSMO_MASTER_EXPANSION_2026-08-30.md` | ?? | Cosmo plan |
| 3 | `Docs/Plans/MATERIAL_HEALTH_AND_CONSOLIDATION_PLAN_2026-08-30.md` | ?? | Material plan |
| 4 | `Docs/Production/QWEN_DAEMON_PIPELINE_2026-08-30.md` | ?? | Daemon pipeline doc |

**Commit message**: `docs: add campaign_05 report, cosmo expansion, material health, qwen daemon pipeline`

---

## 4. COMMIT — Batch D: Hermes Skill

| # | Path | Status | Notes |
|---|------|--------|-------|
| 1 | `.hermes/skills/qwen-daemon/SKILL.md` | ?? | Qwen daemon skill |

**Commit message**: `feat: add qwen-daemon skill`

---

## 5. COMMIT — Batch E: Material Masters

EnvSandbox master material updates.

| # | Path | Status | Notes |
|---|------|--------|-------|
| 1 | `Content/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro.uasset` | M | Triplanar function |
| 2 | `Content/EnvSandbox/Materials/Masters/M_Bookshelf_Standard.uasset` | M | Bookshelf master |
| 3 | `Content/EnvSandbox/Materials/Masters/M_Master_Nikki.uasset` | M | Nikki master |
| 4 | `Content/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape.uasset` | M | Nikki landscape |
| 5 | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend.uasset` | M | Toon height blend |
| 6 | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset` | M | Toon universal |
| 7 | `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha.uasset` | M | Toon alpha |
| 8 | `Content/EnvSandbox/Materials/Instances/Atlantis/MI_BrickStoneCleanTrimB.uasset` | M | Atlantis MI |
| 9 | `Content/EnvSandbox/Materials/Instances/Atlantis/MI_WaterClean.uasset` | M | Water MI |
| 10 | `Content/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CliffGrass.uasset` | M | Cliff grass |

**Commit message**: `chore: update material masters (Nikki, Toon, Bookshelf) + Atlantis/Landscape MIs`

---

## 6. GITIGNORE — Add to `.gitignore`

These directories are large generated/binary exports or plugin content that should never be tracked.

```
# Exports (generated)
Exports/
*.blend
*.fbx
*.glb

# HoudiniEngine plugin content (installed)
Plugins/HoudiniEngine/Content/

# Surreal sweep (generated concepts, renders, textures)
surreal_sweep/
surreal_sweep_wave2/

# TouchDesigner import cache
TDImportCache/

# Windows crash dumps
.windows*.txt
```

---

## 7. REVIEW — Manual triage before committing

These are root-level scripts and unknown files that need human review.

| Path | Status | Action Needed |
|------|--------|---------------|
| `.windows.txt` | ?? | Add to .gitignore (Windows crash dump) |
| `.windows2.txt` | ?? | Add to .gitignore |
| `.windows3.txt` | ?? | Add to .gitignore |
| `gen_concepts.py` | ?? | Review: is this a needed root-level script? Move to `Tools/` or `.gitignore` |
| `gen_posters.py` | ?? | Review: same as above |
| `surreal_render.py` | ?? | Review: same as above |
| `surreal_wardrobe_cops.py` | ?? | Review: same as above |
| `harp_flute_lyre_guides.md` | ?? | Low-risk doc, can commit or .gitignore |
| `research_harp_bow_refs.md` | ?? | Low-risk doc |

**Recommendation**: Add `.windows*.txt` to .gitignore. Move `gen_concepts.py`, `gen_posters.py`, `surreal_render.py`, `surreal_wardrobe_cops.py` to `Tools/` or a `scripts/` folder. Commit the two `.md` guides.

---

## 8. Summary Counts

- **Total untracked/modified**: 1883
- **Batch A (Integration/Characters)**: 19 files
- **Batch B (Python tooling)**: 4 files
- **Batch C (Docs)**: 4 files
- **Batch D (Hermes skill)**: 1 file
- **Batch E (Materials)**: 10 files
- **Gitignore additions**: 6 rules
- **Review required**: 8 files
- **Skipped (surreal sweep)**: ~1700 files (all gitignored)

Total committed across all batches: **38 files** (manageable, reviewable).