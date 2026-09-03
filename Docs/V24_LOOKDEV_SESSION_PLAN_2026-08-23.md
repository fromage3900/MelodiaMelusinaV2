# V24 Lookdev Session Plan — Melusina Relink Recovery

**Created:** 2026-08-23
**Supersedes:** `v23_grandmaster_lookdev_b15e17ff.plan.md` (Cursor plan, Aug 16)
**Status:** Relink COMPLETE and render-verified. Ready for lookdev work.

---

## What changed since the v23 plan

The old plan assumed a live "fat in memory" Blender GUI was the grandmaster and
that disk was a 723 KB stub. That premise is dead:

- Lookdev PID 41736 held ~18 GB in RAM, went **Not Responding**, had no MCP
  listener, and was never saved. That unsaved work is **gone**.
- The Aug 16 15:18 on-disk save **survived** at 73,581,972 bytes, six copies on
  the **G:** drive (not C:, which is why earlier searches missed it).
- `Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend` — the library v23 linked
  against — is **absent from every local drive**.

**New premise: disk is the grandmaster. There is no live GUI to protect.**

---

## Evidence ledger

### V23 archive copies (G:, all verified)

| File | Bytes | SHA256 |
|---|---|---|
| `v23_Lookdev_grandmaster_20260816.blend` | 73,581,972 | `afb99a1cce…78e49c` |
| `..._effects_lock_20260816.blend` | 73,581,972 | `afb99a1cce…78e49c` |
| `..._73MB_pre_tiny.blend` | 73,581,972 | `afb99a1cce…78e49c` |
| `..._nikki-math_TINY.blend` | 73,581,972 | `afb99a1cce…78e49c` |
| `..._PRE_nikki-math.blend` | 73,581,972 | `afb99a1cce…78e49c` |
| `..._effects_lock_20260816.blend1` | 73,581,972 | `b75cb50bc4…50c149` |

Five are byte-identical; the `.blend1` is a distinct autosave.
Location: `G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\`

### The relink

- **Working file:** `G:\EnvironmentPortfolio\BS_GodFile\Exports\PortfolioStages\Melodia_Portfolio_Stage_v24_Lookdev_RELINK.blend`
- **Library repointed:** `//Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend` (missing)
  → `G:\...\Saved\Audit\Melodia_Portfolio_Stage_v22_pre_nikki_genshin_2026-08-13.blend` (2,377,544,382 bytes)
- Candidate chosen because it is the same lineage and within 4 KB of the
  recorded v22_FINAL size, and it contains **all four** datablocks v23 needs.

| Metric | Before relink | After relink |
|---|---|---|
| Total objects | 43 | **129** |
| `Asset_melusina` objects | 0 (empty) | **29** |
| `character_rig` bones | — | **1,124** |
| Melusina verts | 0 | **86,096** |
| `FX_Grease_Scene4` | 0 | **7** grease pencil |
| `FX_Hero` | 0 | **22** |
| Render-visible | — | **87** |
| Evaluated meshes / verts | — | **34 / 137,495** |
| Materials / node groups / images | 8 / 53 / 9 | **71 / 333 / 75** |

All 11 local collections verified intact object-for-object (`local_all_ok: true`):
Cameras 8, FLIPFluids 2, FLIPMeshes 5, FX_NikkiBokeh 11, Lights 5,
Lights_Jewelry 1, Lights_Nikki 1, Lights_Silhouette 1, Melusina_HairDrip 3,
Melusina_WaterFX 3, Studio 4.

### File size drop is expected, not loss

73.5 MB → 694 KB. The lost bytes were **local copies of data now resolved
through the library**. Object count went *up* 43→129 and every named collection
retained its contents. Verified, not assumed.

### Proof render

`G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\v24_relink_proof\v24_relink_proof_beauty.png`
(940,292 bytes, 960×960, Cam_Beauty, frame 71, EEVEE 24 samples)

Visual confirmation: Melusina present with lavender locs, purple top hat,
frilled layered dress, chunky boots, silver waist chain, magical energy around
the head. No pink/missing textures, no black shapes, no empty frame.

**Defect found in the render:** heavy white bloom blowing out the torso and face,
plus large out-of-focus bokeh discs obscuring the subject. This is a
lookdev-tunable issue (`FX_NikkiBokeh` + bloom intensity), first task below.

### Texture resolution

13 of 15 unresolved images were found and packed by
`Tools/fix_v24_textures.py` (SHAWL ×6, bow ×5, frontpanel ×2) from
`G:\MelodiaMelusina\MelusinaFinalRig\`.

**Honest caveat:** the pack did **not persist** into the working file. All 15
unresolved images are **library-owned** (`library: …pre_nikki_genshin…`), so
they can only be repaired inside the library file, not the linking scene.
The proof render shows the outfit reading correctly, so these are very likely
unused duplicate slots (`.001`/`.002` suffixes) rather than active maps.
`m_shawl_BaseColor.png` and `m_sleeve_Normal.png` are absent from all search
roots entirely.

---

## Protocol for this session

- **Never write to** `Saved/Audit/*.blend` — those are the archive. Work only in
  `Exports/PortfolioStages/Melodia_Portfolio_Stage_v24_Lookdev_RELINK.blend`.
- **Never write to** the library `…v22_pre_nikki_genshin_2026-08-13.blend`
  unless deliberately repairing library textures, and only after copying it.
- The old plan's "never launch a second Blender / one GUI only" rule is
  **retired** — there is no fat GUI to lose. Headless `--background` is now the
  safe default and is how every step above was verified.
- Re-verify with `Tools/relink_v23_lookdev.py` reporting and the verify script
  before claiming any gate.

---

## Task queue

### 1. Fix the bloom/bokeh blowout  *(blocks all beauty stills)*
The proof render is unusable as a portfolio frame. Reduce bloom intensity and
pull `FX_NikkiBokeh` discs/orbs off the subject line, or move them behind the
character. Re-render frame 71 from Cam_Beauty and compare.

### 2. Repair library textures (optional, deferred)
Copy the library, resolve the 15 library-owned image paths inside that copy,
repoint v24 at it. Only worth doing if a close-up reveals the SHAWL/bow maps
are actually in use. Two files (`m_shawl_BaseColor`, `m_sleeve_Normal`) are
lost and would need re-authoring or substitution.

### 3. Populate the three still-empty collections
`Asset_sirmelodious`, `Review_Queue`, `Set_Diorama` are empty (0 objects) and
are **not** linked — they were marker collections in the original build script.
The library contains `Asset_sirmelodious_util`, `Review_Queue`, and
`Set_Diorama`. Link those in if the shotdeck needs them.

### 4. Shoot the cutscene shotdeck
`deploy/surreal_arch/shotdecks/melusina_cutscene_staging.json` defines 8 shots
over frames 40–104. All 8 named cameras exist and are verified present.
Note: the deck references a 104-frame cine sim; scene frame range is currently
1–250.

| Shot | Camera | Frame |
|---|---|---|
| establish_world | Cam_Turntable.001 | 40 |
| reveal_profile | Cam_Back | 55 |
| water_rise | Cam_Low | 65 |
| dialogue_medium | Cam_Beauty | 71 |
| macro_emotion | Cam_Macro | 80 |
| full_crown | Cam_Front | 91 |
| song_release | Cam_Turntable | 100 |
| bow_finale | Cam_Beauty | 104 |

### 5. FLIP water-hair bake
`FF_MelusinaHair_Domain` / `FF_MelusinaHair_Drip` are present, and
`FLIPMeshes` has all 5 outputs (fluid_surface + 4 whitewater). Re-verify the
tip domain before baking; the old plan flagged tip Z ≈ 0.74–1.86 as needing
re-check.

### 6. AWS Glacier restore (parallel, unblocked by nothing here)
`aws login` requires interactive browser sign-in — owner action required.
Manifest: `Saved/Audit/stage_v22_glacier_backup.json`

```
bucket: melodia-archive-322037002075   region: ca-central-1
key:    melodia/stage/20260815/Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend
bytes:  2,380,043,974
sha256: f2a5a8dd93fefada1a3d296e34926d6586fb09de56a78d7a1b9fa5ae0ee3d41f
class:  DEEP_ARCHIVE  (Standard restore ~12h, Bulk ~48h)
```

That 2.38 GB object is **larger than any local v22** and dated Aug 15 — the same
day as the missing v22_FINAL. It is the best candidate for the true original.
Restoring it would let the link point at real v22_FINAL lineage instead of the
Aug 13 stand-in.

---

## Scripts produced

| Script | Purpose |
|---|---|
| `Tools/relink_v23_lookdev.py` | Repoints the broken library, reloads, gates on non-empty Asset_melusina, saves |
| `Tools/fix_v24_textures.py` | Indexes Melusina texture roots, resolves + packs missing images |
| `Tools/MelodiaProceduralStudio/build_melusina_asset.py` | Builds standalone `Melusina_Asset.blend` from the ARP FBX |

### Side deliverable: standalone Melusina asset

`Tools/MelodiaProceduralStudio/Assets/Melusina_Asset.blend` — 21,944,557 bytes
Built from `G:\MelusinaRigFinalSeparate\SK_MelusinaRigARP.fbx` (33 MB).

```
armature:  root, 432 bones
meshes:    22        verts: 122,119      materials: 38
height:    2.2789 units
bounds:    min [-0.9744, -0.443, 0.0]  max [0.9744, 0.443, 2.2789]
```

Feet pinned to z=0, centered on XY, so placement is a pure translate.
Missing: `DPM2.004_BaseColor.png` (absent from all drives — that material
renders untextured). `m_hatruffle_BaseColor.png` packed (14.7 MB).

This is the asset for dropping Melusina into the MIDI-generated scenes
(`scene_128BPMarpeggiomelody*`, terrain 64 × 11 × 6 units — her 2.28 height
reads well against 6 units of terrain relief).
