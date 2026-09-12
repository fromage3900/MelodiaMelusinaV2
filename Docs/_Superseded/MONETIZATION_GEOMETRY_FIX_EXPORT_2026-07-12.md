# Monetization geometry — fix-up & export list

**Updated:** 2026-07-16 (Melodia Studio / GN review queue synced; review WIP folders retired)  

## Editable GN collections (authoring)

Spawn live Geometry Nodes (modifiers kept) into the stage:

```text
Tools/spawn_editable_ornament_gn.py
  → OrnamentGN_Editable   (7 gothic fix-list)
  → MusicalGN_Editable    (10 musical kitbash)
```

Melodia Studio → **Sculpt Monetization** shows these collections. KitbashExport flat FBX SSOT is untouched until you apply + export.

### Melodia Studio / GN sync — 2026-07-16

Live Blender 5.1 now has the deploy-synced Melodia GN polish pass:
- Music builders, sheet rail, ornament builders, `label_tree`, and `try_apply_melodia_gn` route first.
- 39/39 registered Melodia GN builders are gold/works in `Saved/Audit/melodia_gn_builder_catalog.md`.
- `ARCH` and registered `CASTLE_*` routes are wired through Melodia GN; `MEL_arch`, `MEL_portico`, and `MEL_gazebo` were fixed/tightened.
- Melodia Studio carousel has **Solo Object** (`surreal_arch.solo_object`) for local-view isolate.
- Melodia Studio has **Ivy (Bagapie)** (`surreal_arch.ivy_scatter`) with Blender 5.1 socket rebind.

Deferred backlog: `FILIGREE_*` monolith rewrites remain planned but not required for the current export queue unless the artist chooses to promote a filigree generator into a sellable mesh.

---

## Package SSOT (flat — do not nest)

```text
KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx          (gothic 15)
KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx   (musical 10)
```

WIP / HandRemake / OrnamentSculptReview staging folders are **retired** — author in `MusicalGN_Editable` / `OrnamentGN_Editable` instead.
**Stage:** `KitbashExport/Melodia_Portfolio_Stage_v4.blend`  
**Policy:** Melodia-owned only. Copy → `Products/_Staging/` — never move/delete originals. Keep `store_live: false` until sell ZIP + 6 screenshots.

**WIP hierarchy (copy buckets; packaging SSOT stays flat):**
```text
KitbashExport/OrnamentMusic_WIP/
  Gothic/{P0_Fix, P1_Heroes, P2_Detail}
  Musical/{HandRemake, Tokens, Polish}
Products/_Staging/OrnamentSculptReview_20260712/  (same buckets)
```
Sync: `python Tools/organize_ornament_hierarchy.py`

---

## Revenue blockers (do these first)

| # | Gate | Status |
|---|------|--------|
| 1 | Sculpt / retopo / UV beauty pass on **SKU #1 gothic 15** | Stand-ins exist; stage copies mostly **NO_UV / NO_MAT** |
| 2 | Re-export FBX → `KitbashExport/OrnamentalMeshes/` | 15/15 files present; treat as **pre-beauty** |
| 3 | 6 store screenshots → `Products/OrnamentKitbash/marketing/screenshots/` | **0/6** |
| 4 | `package_ornament_kitbash.py --zip` from current KitbashExport | Preview ZIP ≠ final |
| 5 | Gumroad purchasable + flip `store_live` | Blocked by 1–4 |

**Not monetizing:** Melusina character/rig/hair, Melodia rhythm game, JRPG template, Magicians Library, JRO / third-party ornaments.

## Review Queue / smoke-test sync

Use these as soft checklist items before final FBX/package work:
- Open Melodia Studio in Blender 5.1 and confirm the GN stack uses the **Melodia Studio** tab.
- Build or route-check: `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, ornament builders, `ARCH`, and one representative `CASTLE_*`.
- Confirm the review controls work without hard-locking the stage: Review Queue Prev / Solo / Next, Solo Object, and Ivy (Bagapie).
- Keep all stage review operations soft: no agent `save_mainfile`, no Melusina material/world edits, no Review_Queue collection hard locks.

---

## SKU #1 — Ornament Kitbash (15) — fix priority

**Export SSOT (flat):** `KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx`  
**WIP buckets:** `KitbashExport/OrnamentMusic_WIP/Gothic/{P0_Fix,P1_Heroes,P2_Detail}/`  
**Sculpt grid:** `Products/_Staging/OrnamentSculptReview_20260712/Gothic/`  
**Target mats:** `M_Orn_Base` + `M_Orn_Trim`  
**UE path:** `/Game/EnvSandbox/Meshes/Ornament/`

### P0 — fix before any sell ZIP (broken / buyer-risk)

| Mesh | FBX KB | Live tris (stage) | Issue | Fix |
|------|-------:|------------------:|-------|-----|
| `SM_Orn_TorusKnot` | 163 | **0 faces** (curve shell) | **BROKEN** — not a mesh | Remesh/convert to solid kitbash; UV; Base/Trim |
| `SM_Orn_FiligreeRing` | 1869 | ~97k | **HIGH_POLY** + no UV/mat on stage | Decimate/retopo to ~5–12k; UV; Base/Trim |
| `SM_Orn_CrownMolding` | 974 | — | Heavy FBX; verify clean manifold | Cap density; UV strip; export unit scale |

### P1 — hero sculpt / UV (store screenshots + Gumroad heroes)

| Mesh | FBX KB | Stage tris | Flags | Work |
|------|-------:|-----------:|-------|------|
| `SM_Orn_RoseWindow_8Petal` | 295 | ~15.7k | NO_UV, NO_MAT | Hero #1 — polish petals/tracery, UV, mats |
| `SM_Orn_VaultRibs` | 633 | ~3.0k | NO_UV, NO_MAT | Hero #2 — boss flower detail, UV |
| `SM_Orn_OculusFrame` | 126 | ~5.7k | NO_UV, NO_MAT | Hero #3 |
| `SM_Orn_SpiralStaircase` | 220 | ~13.6k | NO_UV, NO_MAT | Hero #4 — step bevels, UV |

### P2 — Lissajous showpieces (detail SKU selling points)

| Mesh | FBX KB | Stage tris | Work |
|------|-------:|-----------:|------|
| `SM_Orn_WovenRing` | 258 | ~13.6k | Retopo if needed; UV; Base/Trim |
| `SM_Orn_RosetteMedallion` | 247 | ~12.8k | UV; Base/Trim |
| `SM_Orn_GothicTracery` | 257 | ~13.3k | UV; Base/Trim |
| `SM_Orn_PendantFinial` | 87 | ~4.8k | UV; Base/Trim |

### P3 — modular details (ship after P0–P2)

| Mesh | FBX KB | Stage tris | Work |
|------|-------:|-----------:|------|
| `SM_Orn_DoorArchway` | 108 | ~4.6k | UV; Base/Trim |
| `SM_Orn_ColumnCapital` | 87 | ~4.8k | UV; Base/Trim |
| `SM_Orn_QuatrefoilArch` | 208 | ~10.0k | UV; Base/Trim |
| `SM_Orn_CorbelBracket` | 179 | ~0.8k | Confirm not duplicate of crown; UV |
| `SM_Orn_TorusKnot` | — | — | After P0 remesh |

**Per-mesh checklist (all 15):** apply scale → manifold → UV → Base/Trim slots → FBX (Y-up / UE) → overwrite KitbashExport → mirror `Products/OrnamentKitbash/FBX/`.

---

## SKU #1b — Musical Ornament Kitbash (10) — sibling (7 + 3 Melody Tokens)

**Export SSOT (flat):** `KitbashExport/MusicalOrnamentalMeshes/`  
**WIP buckets:** `KitbashExport/OrnamentMusic_WIP/Musical/{HandRemake,Tokens,Polish}/`  
**Stage collection:** `MusicalOrnaments_Review`  
**Product:** `Products/MusicalOrnamentKitbash/` (`store_live: false`)  
**Stage assist:** Melodia Studio → Stage → **Sculpt Monetization** (or Starlight pie → **Sculpt Fix**)

| Priority | Mesh | Notes | Fix |
|----------|------|-------|-----|
| **HandRemake** | `SM_Orn_TrebleClef` | Your lane — do **not** auto-regen | Sculpt / retopo → overwrite flat SSOT |
| **HandRemake** | `SM_Orn_MusicalCorner` | Your lane — do **not** auto-regen | Lean export → overwrite |
| **Tokens** | `SM_Orn_MelodyToken_01` | Placeholder medallion | Replace with beauty mesh |
| **Tokens** | `SM_Orn_MelodyToken_02` | Placeholder | Same |
| **Tokens** | `SM_Orn_MelodyToken_03` | Placeholder | Same |
| Polish | `SM_Orn_SheetMusicRail` | OK density | Beauty polish |
| Polish | `SM_Orn_MusicalDivider` / `NoteBeam` / `NoteHead` / `PearlJewel` | OK | Light polish |

Work only in **HandRemake** + **Tokens** for mesh finals. Placeholder FBX already in KitbashExport + product FBX + staging. Overwrite when your finals land.

---

## Sculpt Monetization isolate set (viewport)

Shown only when preset `sculpt_monetization` is applied:

- Gothic P0/P1: TorusKnot, FiligreeRing, CrownMolding, RoseWindow, VaultRibs, OculusFrame, SpiralStaircase  
- Musical: TrebleClef, MusicalCorner  
- Tokens: MelodyToken_01/02/03 (+ legacy `MelodyToken` if present)

Everything else (Melusina, diorama, wardrobe, water FX, starlight regen) is hidden.

---

## Export pipeline (when beauty-ready)

```text
Sculpt review blend / stage
  → KitbashExport/OrnamentalMeshes/          (SKU #1)
  → KitbashExport/MusicalOrnamentalMeshes/   (SKU #1b)
  → python Content/Python/package_ornament_kitbash.py --zip
  → UE import (optional beauty shots)
  → 6 screenshots → marketing/screenshots/
  → Gumroad → store_live true + site catalog sync
```

Cockpit: `Docs/BLENDER_MELODIA_COCKPIT.md`  
Watch/import: `Content/Python/watch_ornament_export_and_package.py`  
Pipeline: `Tools/run_ornament_kitbash_pipeline.ps1`

---

## Soft-list after SKU #1 (do not block ornaments)

| Order | SKU | Geometry note |
|------:|-----|---------------|
| 2 | Stylized Props Mini ($9) | Lean ZIP ~17.6 MB ready; **Brick2 low retopo pending**; highs excluded |
| 3 | Zundy Modular | Stage from `G:\ZUNDYMONSKITCHEN` |
| 4 | Stylized Cross Prop | Packaged zip on G:\ |
| 5 | Enchanted Forest | Existing pack |
| 6 | Gothic Arch / Lancet | EnvSandbox greybox arches |
| 7 | Greybox Blockout (47) | `SM_Greybox_*` |
| 8 | Melodia House Modular | Curated `_PROJECT` allowlist |
| — | Fantasy Weapons Mini | Optional F:\ staging |

---

## Explicitly out of export list

- Melusina body / hair / elixir / water FX  
- `Surreal_Regen_Starlight` zen graph instances (portfolio stage only)  
- Wardrobe outfit meshes  
- `_lib_*` kit library fragments without UV (dev refs)  
- Magicians Library, JRO, Japanese alphas, Kenney

---

## Suggested work order (today → ship)

1. Open stage → Melodia Studio → **Sculpt Monetization** (isolates fix set)  
2. **Fix TorusKnot** + **decimate FiligreeRing** + Crown density (Filigree still heavy on disk — sculpt, no auto-regen)  
3. UV + Base/Trim on **4 gothic heroes**  
4. Hand-remake **TrebleClef** + **MusicalCorner** in WIP `Musical/HandRemake/` → overwrite flat SSOT  
5. Replace **Melody Token 01–03** placeholders in WIP `Musical/Tokens/` → overwrite KitbashExport musical FBX  
6. Re-export gothic KitbashExport  
7. Capture **6** store screenshots  
8. `package_ornament_kitbash.py --zip` + musical package → Gumroad → `store_live`
