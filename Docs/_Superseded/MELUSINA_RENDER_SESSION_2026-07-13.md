# Melusina render session — 2026-07-13

**Host file:** `KitbashExport/Melodia_Portfolio_Stage_v10.blend`  
**Engine:** EEVEE (do not switch)  
**World:** `W_Melodia_FadeDayNight` — Value node **Night Mix** (0=day, 1=night), default **~0.72**  
**Cloth preset:** `stable_wardrobe` — dual-island Pin on `Melusina_Skirt`, shawl Collision removed, gravity ~0.18–0.2

## After-nap quick start

1. Open Stage **v9**. Confirm EEVEE + `W_Melodia_FadeDayNight`.
2. Run pre-flight below (2 minutes).
3. Scrub cloth settle **1→24**, then park on a calm frame.
4. F12 beauty → name with the dated scheme.
5. Drop PNG into `my-site-clean/generated/assets/character/`.
6. Run remount scout (optional):  
   `python Tools/remount_melusina_plates.py --scan`
7. When ready to wire site:  
   `python Tools/remount_melusina_plates.py --apply`  
   then refresh passport Capture to the new beauty file.

## Pre-flight checklist

- [ ] `Studio_FloorCard` Z untouched (~-0.2935)
- [ ] Active cam: `Cam_Beauty` (or Macro / Low as needed)
- [ ] Legacy accordion skirt `hide_render` / `hide_viewport` on; Cloth mods muted
- [ ] Cloth warm-up: scrub frames **1–24** (`stable_wardrobe`, gravity ~0.2, Pin holds both skirt islands)
- [ ] Hair Strand.004 weights OK (0 unweighted)
- [ ] Hat/boot maps under `Imports/MelusinaTextures` (no ACTUALCOMPILED)
- [ ] Eyes: keep **your** closing iris wiring — do not global-swap front/back sets mid-shoot
- [ ] `FX_Hero` **render off** for beauty (sparks/veil/ribbon live but quiet via coll hide_render)
- [ ] `Melusina_WaterFX` **render off** unless splash plate (FLIP paused — prefer HairDrip)
- [ ] `Melusina_HairDrip` **on** only for tip-drip plates (`setup_melusina_liquifeel_hair_drip.py`)
- [ ] `Set_Diorama` opt-in only
- [ ] FloorCard Z pin ≈ -0.2935

## Shot toggles

| Plate | Cam | Night Mix | WaterFX | GP Scene4 | Notes |
|-------|-----|-----------|---------|-----------|-------|
| Beauty Nikki | `Cam_Beauty` | ~0.72 | off | off | Quiet FX_Hero — **first plate to remount** |
| Jewelry glam | `Cam_Beauty` | ~0.65–0.8 | off | off | `Lights_Jewelry` |
| Face / iris | `Cam_Macro` | ~0.7 | off | off | Confirm iris front/back on your closing setup |
| Profile front | `Cam_Beauty` / turn | ~0.72 | off | off | Honest “Front · Nikki” — no bangs plate |
| Splash / tip drip | `Cam_Macro` / Beauty | any | HairDrip on | off | `Melusina_HairDrip` LiquiFeel tips; WaterFX FLIP still off |
| Flourish line art | Beauty | ~0.8 | off | **on** | Toggle `FX_Grease_Scene4` |

## Scrub windows

| System | Frames |
|--------|--------|
| Idle NLA | 0–178 |
| Sparkle pulse | 1–240 |
| FLIP splash | 1–96 tip-drip (or 1–240 splash hero) |
| Cloth settle | **1–24** before still (`stable_wardrobe`) |

## Output naming

Prefer: `melusina_<shot>_<yyyymmdd>_<nn>.png`  

| Shot key | Example |
|----------|---------|
| beauty_nikki | `melusina_beauty_nikki_20260713_01.png` |
| jewelry | `melusina_beauty_jewelry_20260713_01.png` |
| front_nikki | `melusina_front_nikki_20260713_01.png` |
| low_nikki | `melusina_low_nikki_20260713_01.png` |
| water_splash | `melusina_water_splash_20260713_01.png` |
| glam_audvis | `melusina_glam_audvis_20260713_01.png` |

Drop folder: `BS_GodFile/my-site-clean/generated/assets/character/`

Do **not** remount solid mauve `melusina_*_001.png` blanks. Do **not** shoot or remount “bangs” plates.

## Supply checklist (you still provide)

| # | Deliverable | Status gate |
|---|-------------|-------------|
| 1 | Beauty Nikki dated EEVEE still | Blocks hero remount |
| 2 | Jewelry glam three-quarter (if Jul 12 isn’t keeper) | Optional if existing jewelry pack keeps |
| 3 | Low / splash / glam AudVis | Only when real (replace mauve `*_001`) |
| 4 | Short caption per plate | Beyond Beauty / Jewelry / Front |
| 5 | `FIGMA_API_TOKEN` | Only if PostToFigma tonight |

## Remount path (after files exist)

1. Entropy-check PNGs (`Tools/remount_melusina_plates.py --scan`).
2. Wire stage / home / hub thumbs to dated paths (script `--apply`, or hand-edit).
3. Refresh passport Capture + stats:  
   Blender: `exec` `Tools/setup` path via `melodia_asset_passport.emit_melusina_stage_passport(...)`  
   or re-run remount tool with `--passport`.
4. Keep Mauve `*_001` unwired forever unless overwritten by real content.

## Risk watch list

| Risk | Mitigation |
|------|------------|
| Cloth drop / EEVEE slowdown | Settle scrub 1–24; dual-island Pin; mute Cloth mods if stills glitch |
| Shawl burst | Never add Collision back on `Melusina_Shawl` |
| WaterFX noise on beauty | Keep WaterFX collection render off |
| Double Melusina / dress | Never enable Scene4 body/dress imports |
| GP clutter | Keep `FX_Grease_Scene4` opt-in |
| Iris guessing war | Do not auto-rewire eyes mid-shoot |
| Night Mix wrong | Dial Value node before F12 |
| Floor contact wrong | Never move FloorCard |
| Site remount of blanks | Entropy check; refuse solid-color plates |

## Related audits / tools

- `Saved/Audit/melusina_cloth_stable_2026-07-13.json` — wardrobe Pin / shawl
- `Saved/Audit/workingmelusinascene4_harvest_2026-07-13.json`
- `Saved/Audit/melusina_finalize_review_2026-07-13.json`
- `Saved/Audit/melusina_fade_daynight_sky_2026-07-13.json`
- `Tools/setup_melusina_clothes_soft_physics.py` — `stable_wardrobe`
- `Tools/remount_melusina_plates.py` — scan / apply / passport
- `Docs/MELUSINA_SESSION_LOG_2026-07-13.md`
