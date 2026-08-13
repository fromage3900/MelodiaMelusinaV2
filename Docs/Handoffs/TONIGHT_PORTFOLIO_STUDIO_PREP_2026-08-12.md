# Tonight — portfolio renders, Melodia Studio, P0 levels, water-hair cache

**Date:** 2026-08-12 evening  
**Mode:** closed-editor inventory + plan. Live 5.2 still required for bake/smoke.  
**Cockpit:** [`Docs/BLENDER_MELODIA_COCKPIT.md`](../BLENDER_MELODIA_COCKPIT.md)  
**GN quality:** [`deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-12.md`](../../deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-12.md) (P0 presets landed; this file is the cine/UE tonight board)  
**Handpainted inventory:** [`Saved/Audit/handpainted_texture_inventory_2026-08-12.md`](../../Saved/Audit/handpainted_texture_inventory_2026-08-12.md) (1208 channel-suffix hits). Passport `Textures: 0` means Komikaze stills, **not** “you have no maps.”

Locks: do not reopen rhythm/Quill. One Unreal editor. Do not save v22 without `MELODIA_ALLOW_STAGE_SAVE=1`.

---

## Order of work tonight

1. **Blender 5.2 restart** (not Sync & Reload on crashed leftover). N → BlenderMCP → Connect **9876**. Health `12/12` / `165`. Smoke-apply one P0 preset (`MEL_effect_magic` LIQUID).
2. **Melusina beauty plate on v22** (`melodia_stage_shot.py --preset beauty --lights nikki --subject melusina`). Hair pin stays `Water (Advance).001`.
3. **Hero props for UE import** — owner maps are ZenTrim + tileables, not Magicians lantern albedos. See handpainted inventory.
4. **Four P0 levels** — placement + missing meshes only; no gameplay rewrite.
5. **Water-hair for UE** — three layers. Flip Fluids cache is **empty**; rebake is cine-only.

---

## Four P0 levels (First 20 Minutes)

Live route (Dreamstate is **not** a standalone map):

| # | Level | Role | Tonight polish |
|---|--------|------|----------------|
| 1 | `/Game/Melodia/Levels/Opening/L_MelusinaMorning` | Bedroom / Sir intro | Confirm `SK_Melusina` + `SK_MelusinaHair` + `ABP_Melusina_WaterHair`. Do not use Content-root stale `L_MelusinaMorning`. |
| 2 | `/Game/EnvSandbox/Environments/L_KaleidoNave` | Traversal (merged Dreamstate) | Cathedral kit FBX already in `KitbashExport/CathedralKit/`. Place ornaments; do not resurrect `L_Melodia_Dreamstate`. |
| 3 | `/Game/ZenForestTest` | First JRPG encounter | Owner look = `ZenTrim_Base4K` (already on `SM_SM_StreetLamp_fbm`). Magicians `SM_Lantern` + `T_Lantern_*` is marketplace fallback, not your handpaint. Torii greybox is live. |
| 4 | Roguelike rooms (`/Game/Melodia/Roguelike/Rooms/*`; Grove as stand-in) | Expedition close | Ornament kitbash already at `/Game/EnvSandbox/Meshes/Ornament/`. No new Set Dressing GN. |

Owner A1 (battle path Morning → KaleidoNave) still holds the UE editor when it is open.

---

## Handpainted maps (channel hunt, 2026-08-12)

Indexer: `Tools/inventory_handpainted_textures.py`. JSON: `Saved/Audit/handpainted_texture_inventory_2026-08-12.json`. **1208 hits.** No copies (G: nearly full). `F:\Library` missing.

| Class | Count | What it is |
|-------|------:|------------|
| character | 611 | `shirttextured.spp` (1.4 GB), head/shirt `.spp`, `Imports/MelusinaTextures/*.png` (173 files), `T_Melusina_*` / `T_MelusinaC_*` already in UE |
| other_hero | 440 | Greybox `.fbm` sidecars and misc channel maps (not the three SKU names) |
| tileable | 86 | `G:\MelodiaMelusina\MELUSINATILEABLE TEXTURES\` — brick, floral brick, crystal, grass, cobble, soil, bark; house `hybtrimsheet.spp` |
| trimsheet | 61 | `/Game/Textures/ZenTrim_*` 4K (Base4K, Flowers, Wet, Cracked…) plus copies inside Greybox `.fbm` |
| substance_source | 8 | Foliage `substance001.spp`, `HeartTiles.spp`, `pea.spp` |
| prop_token | 2 | `G:\MelodiaMelusina\melodsytoken.spp` (564 MB) |
| prop_cross / lantern / wand | **0** | No files named lantern/wand/cross/kasuga with channel suffixes on G: or Content |

**Correction:** Komikaze passport `Textures: 0` is the still, not the library. Your handpaint lives as Melusina clothes/body, ZenTrim, and `MELUSINATILEABLE TEXTURES`. The three hero props do **not** have their own `*_BaseColor` sets on disk; they should wear **ZenTrim** (StreetLamp `.fbm` already has `ZenTrim_Base4K_BaseColor`) or a tileable (floral brick / crystal), not Magicians `T_Lantern_*`.

`ACTUALCOMPILEDMELUSINATEXTURES` is **not** on G: tonight; staged PNGs are already under `Imports/MelusinaTextures/`.

---

## Hero assets located

Komikaze plates are **shader stills**. Owner albedo is ZenTrim / tileables / Melusina `T_MelusinaC_*`, not those PNGs.

### StylizedCrossProp

| Kind | Path / fact |
|------|-------------|
| Plates | `generated/assets/cross/cross_komikaze_*.png` |
| Handpaint | **No** `cross_*_BaseColor`. Wire `G:\MelodiaMelusina\MELUSINATILEABLE TEXTURES\bricks\floralbrickgreayscale\Untitled material\Untitled material_BaseColor.png` or `/Game/Textures/ZenTrim_Base4K_BaseColor` |
| Catalog target | `StylizedCrossProp_FBX.fbx` — missing from `Products/_Staging` |
| Live UE mesh | **None.** `T_Hatch_Cross` is a hatch pattern, not the vow cross |
| Import plan | Lean FBX from v22 + **your** ZenTrim/floral brick MI. Do not use hatch |

### ZenLantern

| Kind | Path / fact |
|------|-------------|
| Plates | `generated/assets/props/zenlantern_komikaze_*.png` |
| Handpaint | **No** lantern-named maps. Closest owner set: `Content/Greybox_Kit/SM_SM_StreetLamp_fbm/ZenTrim_Base4K_BaseColor.uasset` |
| Passport | 8.2M tris, Komikaze still (`Textures: 0` = no packed albedo in that render) |
| Live UE | Magicians `SM_Lantern` + `T_Lantern_*` = **marketplace**, not yours |
| Import plan | Studio `ZEN_LANTERN` low mesh or StreetLamp greybox + **ZenTrim_Base4K**. Keep Magicians only as silhouette fallback |

### StylizedMagicalWand

| Kind | Path / fact |
|------|-------------|
| Plates | `generated/assets/props/magical_wand_komikaze_*.png` |
| Handpaint | **No** `wand_*_BaseColor`. Mesh `SM_Retopo_wand.fbx` (87 KB) has no sibling `.fbm` maps |
| Live UE mesh | `/Game/EnvSandbox/Greybox_Kit/SM_Retopo_wand` |
| Import plan | Already imported. Assign **ZenTrim** (or a small unique MI from tileable crystal/hearts) — do not wait on a missing wand albedo pack |

---

## Flip Fluids studied (Blender) vs Niagara Fluids (UE)

These are **different solvers**. Do not mix names.

| System | What it is | Hair? |
|--------|------------|-------|
| **Blender Flip Fluids** addon `flip_fluids_addon` | Domain / inflow / obstacle. Cache = `.bobj` under `KitbashExport/flip_cache_melusina_waterhair/` | Tip **droplets** + optional cine `fluid_surface` only |
| **LiquiFeel** | Elixir glass + `Melusina_HairDrip` proxies | Never replace strands |
| **UE Niagara** `/Game/Melodia/VFX/Melusina_WaterFX` | Specs in `specs/niagara_presets/melusina_waterfx*.json` | Gameplay drip/mist |
| **UE Water V10 / Niagara Fluids 2D–3D FLIP** | World water body (`L_WaterV10_NativeValidation`) | **Not hair** |

### Why the Blender sim “didn’t work on hair” (already diagnosed)

Domain bbox sat at world Z ~2.7–4.8 while tips are ~0.7–1.9; drip emitter outside domain; `Melusina_WaterFX` `hide_render=True`; cache had **0** `.bobj`; drip was `TYPE_FLUID` without inflow. Tool: `Tools/tune_melusina_hair_drip.py` (cache dir, res 72, frames 1–96).

**Tonight’s cache on disk:** `KitbashExport/flip_cache_melusina_waterhair/` contains `flipstats.data` + logs only — **zero `.bobj`**. Historical 1–240 bake was emptied 2026-07-14. Logs name Stage **v7**. Rebake must happen on **v22**.

Objects (do not hide-render the look hair): `FF_MelusinaHair_Domain`, `FF_MelusinaHair_Drip`, `FF_MelusinaHair_Sheet`, `fluid_surface`. Beauty stills hide the FF objects (`setup_melusina_master_studio.py`).

---

## How to get water-hair fluid renders cached for UE

**Hair is already water in-engine** via `SK_MelusinaHair` + `MI_Melusina_WaterHair` + `ABP_Melusina_WaterHair`. That is the gameplay body. Flip Fluids does **not** replace it.

```text
Layer A  LOOK (always)     SK_MelusinaHair + MI_Melusina_WaterHair
                           Blender pin: Water (Advance).001 on Hair Strand.*
Layer B  DRIP (gameplay)   Niagara Melusina_WaterFX  (no .bobj, no Alembic)
Layer C  CINE CACHE        Flip Fluids bake → Alembic fluid_surface
                           → UE Geometry Cache on a cine actor only
```

### Layer C procedure (next live 5.2, then UE when editor free)

1. v22: confirm `FF_MelusinaHair_*` exist. Run `tune_melusina_hair_drip.py` so domain covers tips. Sheet off for “little drip”; sheet on only for a cascade hero.
2. Flip Fluid → Bake frames **1–96** @ res **72** (or 80) into `KitbashExport/flip_cache_melusina_waterhair/`. Expect `.bobj` count ≈ frame count. Do not bake 240 until 96 is good.
3. Export **`fluid_surface`** Alembic (`Exports/MelusinaWaterHair/GC_MelusinaHairFlip_v22.abc`), UVs on, world scale cm. Parent/constraint to `hair_root` / head in Blender before export if the surface should follow the head.
4. UE: Import Alembic as **Geometry Cache**. New cine actor (not `SK_MelusinaHair`). Material: water/toon MI, not a second skeletal hair. Socket to head. Play cache in sequencer / montage.
5. Optional cheaper runtime: VAT from the same ABC — only if cine cache is too heavy. Do **not** run Flip Fluids or Niagara 3D FLIP as the hair solver.

**Non-goals:** replacing `Water (Advance).001`; putting FLIP meshes under `FX_Hero`; using Water V10 Niagara Fluids as hair; treating `T_Hatch_Cross` as the vow cross.

---

## Melodia Studio tonight (closed-editor already done)

- Addon synced to 5.2 AppData. P0: 24 builders / 73 looks. Naming audit 165/165.
- Smoke in GUI: GN Stack 12 sections; apply `MEL_effect_magic` / `MEL_filigree_spiral` / `MEL_castle_assembler` presets.
- Optional lantern: Studio `ZEN_LANTERN` low mesh → FBX for ZenForest if Magicians lantern silhouette is wrong.
- B2 website plate dry-run still open (`stage_publish.py`, git push off).

---

## Continuation (20:40 ET) — for the next agent

**Handoff:** [`TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md`](TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md)

Closed-editor work is done. Live gates:

| Blocker | Why |
|---------|-----|
| UnrealEditor PID 38184 | A1 holds. Do not `--apply` ZenTrim or import Cathedral until released. |
| Blender MCP down | Owner restarts 5.2. Then tune → bake → alembic helper. |
| Cathedral 41 FBX | Not in Content. Import when A idle. |
| `MI_ZenTrim_Base4K` | Missing; script creates it on `--apply`. |
| Cross mesh | Still missing. Never `T_Hatch_Cross`. |

D1 harness now tries `/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI` first.
