# Melusina Nikki plate + Genshin FACE/BODY — 2026-08-13

Git-tracked copy of the Blender 5.2 pass. `Saved/` is hook-blocked; Cam_Beauty PNG stays in the website sibling (7.8 MB). Light Map G is the small PNG next to this file. Do not commit v22 (~2.38 GB), the sidecar blend, the 209 MB ABC, or Flip `.bobj`.

Live Blender **5.2 GUI only** (v22). No second Blender. No Flip bake/rebake. No Unreal. No `nikki_mat_apply` on character. `MELUSINA_SHADER_AGENT_STOP` was **absent**.

## Plate (website sibling)

**Cam_Beauty Nikki still:**

`C:\EnvironmentPortfolio\my-site-clean\generated\melusina_cam_beauty_nikki_2026-08-13.png` (7,839,106 bytes)

Also:

- `C:\EnvironmentPortfolio\my-site-clean\generated\assets\character\melusina_stage_beauty.png` (same bytes; `melodia_stage_shot.py` default)
- `G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_cam_beauty_nikki_2026-08-13.png`
- `G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_nikki_beauty_2026-08-13.png`

Taken on live v22 via `melodia_stage_shot.py --preset beauty --lights nikki --subject melusina` (imported in-session; hair-protect monkeypatched so Flip glam stayed hidden). Engine `BLENDER_EEVEE`, frame 240. `Review_Queue` `hide_render` during the plate.

## Track 1 — Nikki beauty / Lights parent

| Item | Result |
|------|--------|
| `beauty_clean` | Applied. `deploy/surreal_arch/stage_visibility.py` now lists parent **`Lights`** in `beauty_clean` on-set (loaded addon still needed a live unhide). |
| Lights parent | Unhid `Lights`. Lamps live there: KeyWarm / RimPink / GoldKick / FillCool. `Lights_Nikki` is an empty marker. |
| Nikki recipe | KeyWarm **900**, RimPink **550**, FillCool **280**, GoldKick **140**. **`L_FillCool` was missing — created** AREA at (0.4, 2.8, 2.2). Extra `L_RimPink.001` hide_render. |
| Flip glam | Domain cube `hide_render`. `fluid_surface` shown (FLIPMeshes). Mesh strands Flip **obstacle** + `hide_render`. Hair PRO curves `hide_render`. **No bake / no rebake.** Cache still 480 `.bobj` 1–240. |
| Water (Advance).001 | **Restored** onto `Hair Strand.004/.007/.010` (was `.002`). No `nikki_mat_apply`. Also assigned onto `fluid_surface` as hair-body look. |
| SHAWL.001 | Hybrid **intact** (`Linear Gradient (Halftone).007`). Not rewritten. |
| Simply Cloth | `SimplyCloth` + `SimplyPin` on shawl/skirt/sleeve under `character_grp_rig`. `show_render=False` for the still (no 1–240 cloth sim). Wardrobe_* collections empty. |
| Swingy SHP | **Skipped** — no `SHP_Armature (Hair Strand.*)` companions. `character_rig.bSwSimulate` already True. |
| LiquiFeel | `melusina_ElixirGlass` only. HairDrip + FX_Hero hide_render. Not on strands. |
| Floor | `Studio_FloorCard` Z ≈ **-0.2935 LOCKED** (measured -0.293479). Not moved. |
| Flip note | During render: Flip `'Action' has no attribute 'fcurves'` + lock-interface warning. Plate still wrote. Cache globules sit **below scalp** (max Z ≈ 1.015 vs head.x Z ≈ 1.442) — plate reads bald; do not rebake. `FLIPFluids` collection was hide_render during the still (surface is in `FLIPMeshes`). |

## Track 2 — Genshin FACE/BODY only

| Map | Landed |
|-----|--------|
| Head proxy | `Genshin_HeadProxy` UV sphere at `head.x` (-0.003, -0.159, 1.442), hide_render. |
| Custom normals | Data Transfer `GenshinHeadNormals`, Projected Face Interpolated, mix **0.32** `Melusina.001` / **0.38** `simply_coll`. Auto Smooth / Weighted Normal. |
| Vertex colour `Col` | R = outline thickness, G = z-offset on simply_coll, Melusina.001, shawl/skirt/sleeve/panels/gloves/bow. |
| Light Map G | [`Melusina_Genshin_LightMap.png`](Melusina_Genshin_LightMap.png) Non-Color (sRGB off). G = shadow-threshold cheat (undersides, collarbone, sleeves). Parked as **unused** TEX_IMAGE on Lane A mats (Principled/roughness/metallic **not** rewritten). SimpleBake_Props `selected_lightmap=True`, `lightmap_apply_colman=False`. **Cycles SimpleBake operator not run** (would switch engine / block). |
| UV1 | Copied from UVMap on `Melusina.001` + `simply_coll`. Face SDF full angular bake **P1 skipped**. |
| Forbidden | **No** Data Transfer on `fluid_surface` or Hair Strand* / Hair PRO curves. |
| ARP | **Did not** Apply All Transforms on `character_rig`. |
| `Melusina.001` | Not in View Layer — `shade_smooth` failed; Data Transfer modifier still added. Live body is `simply_coll`. |

## Save / dirty

- Sidecar (copy of on-disk pre-persist v22): `G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\Melodia_Portfolio_Stage_v22_pre_nikki_genshin_2026-08-13.blend`.
- **Saved** v22 2026-08-13 ~16:36 ET with `MELODIA_ALLOW_STAGE_SAVE=1` inside Blender (`2380026019` bytes). Dirty **false** after save. Maps confirmed live (HeadProxy, Col, Data Transfer, UV1, Light Map, SimplyCloth, L_FillCool).
- Plate PNG is on disk independently of the blend save.

## Skipped

- Flip start / rebake
- `nikki_mat_apply` on Melusina/hair
- Swingy on missing SHP companions
- Simply Cloth simulation during the still
- Full Genshin ramp LUT rewrite
- Face SDF angular bake
- Apply All Transforms on `character_rig`
- Second Blender / Unreal / Live Link
