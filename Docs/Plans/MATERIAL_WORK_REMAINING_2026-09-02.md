# Material Work — Remaining & Incomplete (2026-09-02)

**Verified against:** `Saved/Audit/_mi_no_tex_144_classified.json`, `Saved/Audit/pbr_full_scan_2026-08-30.json`, `ART_DIRECTOR_REVIEW.md`, commit messages

---

## 1. Quantified Gaps

| Metric | Value |
|---|---|
| Total PBR textures | 3,343 |
| Distinct stems | 1,446 |
| Complete PBR stems (all channels) | 210 |
| Orphaned complete stems (no MI) | 144 |
| Material Instances (total) | 1,654 |
| Melusina-specific orphans | 19 |

---

## 2. Orphaned PBR Stems (144 — no Material Instance)

These have full texture suites on disk but **no MI to use them**. They're inert.

**Breakdown:**

| Category | Count | Examples |
|---|---|---|
| Melusina hero materials | 19 | T_Melusina_BaroqueAquatic_MosaicTile, T_Melusina_CathedralPearl_MarbleTile, T_Melusina_EtherealVeil_StarlightChantilly, T_Melusina_IridescentSiren_ScaleTessellation, T_Melusina_MoonlitHarbor_WaterRippleParquet, T_Melusina_PorcelainMusicBox_KintsugiLapis, T_Melusina_SakuraLullaby_SilkOrganza, T_Melusina_WatercolourWave_Parquet, etc. |
| Instrument materials | 7+ | T_Cello, T_Crystal, T_Note, T_Stem1, T_Stembell, T_Treble |
| Landscape/Terrain | 1 | T_LandscapeGrayscale, T_Leafcool |
| Misc environment | 117+ | Rhinestones, bling, various CC0 kits |

**Fix:** For each stem that should be shippable, create an MI on the appropriate master (usually `M_Master_Toon_Universal` or `M_Master_Toon_Universal_Alpha`).

---

## 3. Material Instances Missing Textures

From `_mi_no_tex_144_classified.json` — these MIs exist but reference **no textures on disk**. They render as flat/grey.

| Count | Status |
|---|---|
| 94 | Suite present on disk (textures exist, MI may not reference them) |
| 0 | Missing suite entirely |

**Note:** The audit classified these as "orphan stems" not "orphan MIs." The MIs may exist but have broken texture references. Need to verify per-MI.

---

## 4. Remaining Work from Recent Commits

### From `agent_work_log_2026-08-29`:
- [ ] `SM_Leviathan.obj` / `SM_DrownedOrgan.obj` mesh imports (MIs waiting)
- [ ] `MI_Melusina_WaterHair` creation on `M_Water_Master_Grand_v7` + `SK_MelusinaHair` slot fix (prior claim wrong — MI does not exist)
- [ ] `SK_Melusina_V2_Shirt` outline slot
- [ ] Ocean visual pass + `Toon_Weight` dial + `DA_Color_AnimeLightBlue` / `DA_Foam_Stylized` application
- [ ] Banner/Shroud fabric master; Madoka/Itto wiring mirror onto HeightBlend; SDF lane consumer decision

### From `ART_DIRECTOR_REVIEW.md`:
- [ ] `pipeline/handoff/portfolio_package.json` has 5 of 7 sections empty (assets, materials, renders, scene identity, stats)
- [ ] Material preview grid — no `previews_manifest.json`, `materials` array empty
- [ ] Breakdown plates — no `Portfolio_Breakdown` tagged actors
- [ ] Stats manifest — no triangle/draw-call producer
- [ ] CC0 kit swap never landed (torii, trees, bridge, lantern) — scene delivers placeholders
- [ ] Second environment family (Venetian canal, Moorish courtyard, or Sci-Fi deck) to prove breadth
- [ ] Video/GIF — 10–15s flythrough or petal drift loop
- [ ] Pond + `MI_GrandWater_SakuraPond` undocumented visually

### From P1 Cymatics promotion:
- [ ] 22 new Copernicus variants need Monolith Phase A live import (CymaticOrchid + Faraway* + Melodia* + MoonlitMoss/PrismaticObsidian/RoyalVelvetBrocade/SingingDune/WeepingWillow)
- [ ] World Field Bus cymatic publishers need PIE verification
- [ ] Cymatics P1 promotion gate (owner review)

### From earlier closeout sessions:
- [ ] Nikki glow wiring (committed butHeightBlend master was read-only — may need re-verification)
- [ ] `MI_Melusina_Dress_Shorewake` assigned to `SK_ShorewakeDress` slot 0 (committed, verify in PIE)
- [ ] `T_Leviathan_Bone_*` + `T_Organ_Pipe_*` imported (committed, verify)
- [ ] `MI_SeaAbove_Leviathan_Bone` + `MI_SeaAbove_Organ_Pipe` created (committed, verify)

---

## 5. Master Material Health

| Master | Status | Notes |
|---|---|---|
| `M_Master_Toon_Universal` | ✅ 18 texture slots, 12+ param groups, Substrate Toon | Verify 30 MI scalars actually bind (klein_veil_import.py:94 skips unknown silently) |
| `M_Master_Toon_Universal_Alpha` | ✅ Used for garment layers | 10 layers materialized, read-back 10/10 |
| `M_Master_Toon_Landscape_HeightBlend` | ⚠️ BeatPulse + AudioEmissiveStrength added | Verify in PIE — read-only crash earlier |
| `M_Water_Master_Grand_v7` | ❌ MI_Melusina_WaterHair does not exist | Create + assign to hair slot |
| `M_Master_Melusina_Costume` | ❌ Does not exist | 3 MI specs reference this parent |
| `M_Master_FarawayMother_Fabric` | ❌ Does not exist | 3 MI specs reference this parent |
| `M_Master_Starskiff_Rigid` | ❌ Does not exist | 1 MI spec references this parent |
| `M_Master_Simple_Universal` | ⚠️ Node count drift (25→26) | Re-freeze baseline |
| Banner/Shroud fabric master | ❌ Not created | Referenced in P2 spec |

---

## 6. Priority Order

### Tier 1 — Shipping blockers (do first)
1. **Create 19 Melusina MIs** — hero materials with full PBR suites, no MI = invisible
2. **Fix MI_Melusina_WaterHair** — hair renders grey without it
3. **Verify M_Master_Toon_Universal params** — 10 scalars may be silently skipped
4. **Create 3 missing parent masters** — Melusina_Costume, FarawayMother_Fabric, Starskiff_Rigid

### Tier 2 — Visual polish (do before portfolio)
5. **Ocean visual pass** — water is a differentiator, currently flat
6. **Banner/Shroud fabric master** — P2 progression gate
7. **CC0 kit swap** — replace placeholders (torii, trees, bridge, lantern)
8. **Second environment family** — prove breadth beyond Sakura

### Tier 3 — Portfolio (do when visuals are final)
9. **Material preview grid** — 13–14 `MI_Show_*` thumbnails
10. **Breakdown plates** — `Portfolio_Breakdown` tagged actors
11. **Stats manifest** — triangle/draw-call producer
12. **Video/GIF** — 10–15s flythrough

---

*Evidence: 144 orphaned stems from Saved/Audit/_mi_no_tex_144_classified.json, 1654 MIs from pbr_full_scan_2026-08-30.json, ART_DIRECTOR_REVIEW.md §3.*