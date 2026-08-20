# Handoff — Material Pipeline AAA Plan Execution (2026-08-14)

**Pick up:** `Saved/Audit/{material_folder_reorg,sdf_move_pass2,rhythm_materials,nikki_features,nikki_feature_shows,dead_mi_deletion,neutral_map_routing,flat_mi_consolidation}_2026-08-14.json` · `Docs/ENVIRONMENT_MATERIAL_LAYOUT.md` · `Docs/Reconstruction/MATERIAL_SYSTEM_REBUILD_2026-08-14.md`

**Editor:** one UnrealEditor (verify `Get-Process UnrealEditor`), Monolith :9316. This session executed the approved grand plan (phases 1–5 of 7).

---

## 1. Research & authority

- **4 parallel explore subagents** studied: (a) full material folder tree + 1,284 material assets + name collisions (colormap ×590, triple-mirrored trees), (b) duplicate detection (24 runtime MI dups, 1,511 short-name keys, 718 mesh root/nested pairs, zero byte-identical textures inside `Textures\`), (c) mesh→material assignment (762/764 families lack local MIs, 295 colormap-only, 468 no-MI-anywhere, 357 `_Loose` MIs), (d) master/function deep-read (241 params, 27 groups vs 21 organizer vs stale 14; LayerC 6-map duplicate; 3 parallax impls; 4 iridescence paths; 80 unused presets; overhaul Stages A–E).
- **AWS Bedrock:** `aws login` refreshed (root, account 322037002075) but **API invoke is blocked at the account level for ALL models** ("Operation not allowed" — the undocumented model-access use-case form; documented in the 08-13 handoff). Console playground works; next step is an AWS support ticket. Local research was used instead.
- Folder layout contract written: `Docs/ENVIRONMENT_MATERIAL_LAYOUT.md`.

## 2. Folder hierarchy reorg (redirector-safe)

- **53 experimental `M_SDF_*` masters → `Masters/SDF/`** — rename_loaded_asset after clearing LFS read-only bit; verified **0 broken parents** across 173 SDF instances.
- **10 landscape quarantine/work masters** (`*_20260729`, `_BACKUP_`, `_QUARANTINE_`, …) → `_Scratch/`.
- `Masters/` root: 125 → 62 production assets.
- Reorg script: `Content/Python/reorg_material_folders.py` (disk-iteration pattern — `list_assets` iteration breaks rename loops; chmod-before-load is required for LFS).

## 3. New material instances

- **Rhythm battle-surface family (new):** `Instances/Rhythm/` — `MI_Rhythm_Floor_Dream`, `_Floor_Stone`, `_Note_Highlight`, `_Arena_Neon` (audio-reactive), `_Podium_Hero`. Parents `M_RhythmSurface_Pulse` / `M_AudioReactive_BaseMaster` (Harmonix-clock driven). Script: `create_rhythm_materials.py`.
- **Nikki showcase instances (new):** 7 in `Instances/NikkiHero/` proving each new feature gate (`MI_Nikki_Show_RibbonTrim/PearlSheen/Watercolor/GlitterHalo/StickerEdge/PetalShadow/SquishDoll`). Script: `create_nikki_feature_shows.py`.

## 4. Nikki family expansion — the centerpiece

**7 new unique `MF_Nikki*` functions** (Custom HLSL, built by `expand_nikki_features.py`, tagged `NikkiFeat:`):

| Function | Trick |
|---|---|
| `MF_NikkiSDFRibbon` | world-space SDF band ribbon hugging silhouettes (distance falloff + curvature) |
| `MF_NikkiPearlSheen` | dual-layer pearlescent iridescence (thin-film cosine ×2 + ColorRamp3) |
| `MF_NikkiDreamWatercolor` | watercolor bleed in shadow (noise hue rotation + pooling mask) |
| `MF_NikkiGlitterHalo` | world-aligned hash glitter + fresnel halo, time-twinkle (no noise tex) |
| `MF_NikkiStickerEdge` | anime sticker edge-light (banded Fwidth edge + pastel rim) |
| `MF_NikkiSquishWPO` | gentle breathing WPO (sin·dot·world × fresnel soft bob) |
| `MF_NikkiPetalShadow` | blooming SDF petal shadow field |

- **28 new scalars + 7 new gates** added to `M_Master_Nikki` and `M_Master_Nikki_Landscape`, group `04 | Nikki Cute` / `05 | Shadow Dream` / `06 | Kawaii Squish`.
- **All new gates default-OFF** (kawaii baseline Pastel+Twinkle stays ON).
- **Both masters compile clean** (PS 292 / 307; no cycles).
- Feature chain reads the **pastel switch output**, never the ShadowDream switch (cycle trap). WPO routes MF output → StaticSwitch → material property (direct MF→property crashes the editor — two crashes hit before the fix).
- Original surgery re-ran after a cleanup mishap deleted the core chain (tag bug); `expand_nikki_masters.py` restored both masters (verified compiling).

## 5. T3D pipeline + reconstruction

- `Docs/Reconstruction/MATERIAL_SYSTEM_REBUILD_2026-08-14.md` — exact ordered script list to rebuild the whole surface.
- `Docs/T3D_Patterns/patterns/nikki_feature_block.md` — the feature block as a reusable pattern + traps.
- `Docs/T3D_Patterns/patterns/README.md` — material patterns supplement.
- **T3D baseline re-exported** (`verify_baseline.py --update`): 3 drifted masters accepted (Nikki surgery + Universal/Nikki polish), `M_Master_SDF_Toon` path fixed to `Masters/SDF/` → **55/55 clean, 0 failed**.

## 6. Editor stability incidents (this session)

1. Nikki surgery crashed the editor twice (MF→property connection + graph cycle) — fixed, then clean.
2. A cleanup deleted the original Nikki chain (broad `NikkiX:` tag match) — restored via `expand_nikki_masters.py`.
3. LFS read-only blocks renames — chmod-before-load is mandatory.

## 7. Still open (next session)

- **Phase 6/7 of plan:** final full-mesh read-back audit, `material_family_manifest_full.py` capture, git commit (owner-requested at session end), and the AWS support ticket for Bedrock model access.
- Triage of the 24 runtime duplicate short names (NikkiHero/NikkiIntegrated/Water v10) — owner sign-off on canonical per name.
- 718 root/nested mesh pairs — reference-graph decision (owner).
- The 80 Universal presets remain unwired to meshes (documented; next routing pass).
